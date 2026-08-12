"""Карта разбора: от материалов до итога, вместе с разрывами.

## Что показывает карта

Узлы четырёх видов и рёбра между ними:

`SOURCE`
    Проверенный источник права, на котором держится разбор.

`EVIDENCE`
    Проверенный набор фактов по делу — то, что оператор загрузил и что прошло
    проверку.

`INSTITUTE`
    Институт, который в этом деле что-то сказал. Институт, промолчавший по
    этому делу, на карту не попадает: рисовать 90 пустых узлов — значит
    спрятать те несколько, которые сработали.

`LAYER`
    Слой общих положений — узел, в котором выводы институтов превращаются в
    судьбу требования.

## Разрывы

Ребро от института к слою существует, только если институт действительно питает
слой (`LAYER_FED_BY`). Если институт по делу сработал, а связи нет, карта
показывает **разрыв** и подставляет причину из аудита связности: либо это
решение (специальный тип, средства защиты, стадия заключения, дублирование),
либо открытый долг связности.

Разрыв не прячется. Институт, чей вывод никуда не идёт, не влияет на то, что
прочитает юрист, — и оператор обязан это видеть на карте, а не узнавать из
спецификации.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.layer_connectivity import (
    LAYER_CONNECTIVITY_AUDIT,
    VERDICT_LABELS_RU,
    ConnectivityVerdict,
)
from causa.institutional.contracts.real_case_pipeline import LAYER_FED_BY
from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisRequest,
    ReviewedContractAnalysisResult,
)
from causa.translation_pipeline import build_translation_assertions
from causa.ui.institute_titles import INSTITUTE_TITLES_RU
from causa.ui.reasoning import CONCLUSION_SPINE

CASE_MAP_VERSION = "ui-case-map-v0"

_LAYER_INSTITUTES = ("general_effects", "general_consistency")

_IGNORED_EVALUATION_FIELDS = frozenset(
    {"constraint_set_id", "satisfiable", "reasons_ru", "warnings_ru"}
)


class NodeKind(str, Enum):
    SOURCE = "source"
    EVIDENCE = "evidence"
    INSTITUTE = "institute"
    LAYER = "layer"


NODE_KIND_LABELS_RU = {
    NodeKind.SOURCE: "источник права",
    NodeKind.EVIDENCE: "проверенные факты",
    NodeKind.INSTITUTE: "институт",
    NodeKind.LAYER: "итоговые выводы",
}


class MapNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    kind: NodeKind
    kind_ru: str
    title_ru: str
    detail_ru: str = ""
    needs_human: bool = False


class MapEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    target: str
    #: Ложь означает разрыв: вывод не доходит до цели.
    connected: bool
    reason_ru: str = ""
    #: Истина только для разрывов из категории «открытый долг связности».
    open_debt: bool = False


class CaseMap(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = CASE_MAP_VERSION
    nodes: list[MapNode] = Field(default_factory=list)
    edges: list[MapEdge] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)

    @property
    def breaks(self) -> list[MapEdge]:
        return [edge for edge in self.edges if not edge.connected]


def _spine_sources(
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
) -> list[str]:
    """Источники, на которых держится линия вывода.

    В `source_ids` попадают все проверенные артефакты дела — их около трёхсот, и
    все они на карте не нужны: карта тогда состоит из источников, а не из
    разбора. На карту идут те, на которые ссылаются звенья линии вывода;
    остальные пересчитаны в примечании, а не забыты.
    """
    codes = {code for code, _ in CONCLUSION_SPINE}
    referenced: set[str] = set()
    for assertion in build_translation_assertions(request, result):
        if assertion.code in codes:
            referenced.update(assertion.source_refs)
    return sorted(referenced)


def _spoke(evaluation) -> bool:
    """Сказал ли институт что-нибудь по этому делу."""
    for name in type(evaluation).model_fields:
        if name in _IGNORED_EVALUATION_FIELDS:
            continue
        if getattr(evaluation, name) is True:
            return True
    return False


def _needs_human(evaluation) -> bool:
    return any(
        name.startswith("requires_human_") and getattr(evaluation, name) is True
        for name in type(evaluation).model_fields
    )


def _true_fields(evaluation) -> list[str]:
    return [
        name
        for name in type(evaluation).model_fields
        if name not in _IGNORED_EVALUATION_FIELDS and getattr(evaluation, name) is True
    ]


def build_case_map(
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
) -> CaseMap:
    """Собрать карту разбора одного дела."""
    nodes: list[MapNode] = []
    edges: list[MapEdge] = []

    evidence_id = "evidence:case"
    nodes.append(
        MapNode(
            id=evidence_id,
            kind=NodeKind.EVIDENCE,
            kind_ru=NODE_KIND_LABELS_RU[NodeKind.EVIDENCE],
            title_ru="Проверенные факты дела",
            # Перечислять здесь всех проверяющих бессмысленно: их девяносто, и
            # список превращает узел в стену текста. Важно их число.
            detail_ru=(f"дело {request.case_id}; проверяющих: {len(result.reviewer_ids)}"),
        )
    )
    for source_id in _spine_sources(request, result):
        nodes.append(
            MapNode(
                id=f"source:{source_id}",
                kind=NodeKind.SOURCE,
                kind_ru=NODE_KIND_LABELS_RU[NodeKind.SOURCE],
                title_ru=source_id,
                detail_ru="источник, признанный применимым и действующим",
            )
        )
        edges.append(
            MapEdge(
                source=f"source:{source_id}",
                target=evidence_id,
                connected=True,
                reason_ru="факты сопоставлены с нормой этого источника",
            )
        )

    layer_id = "layer:general_effects"
    nodes.append(
        MapNode(
            id=layer_id,
            kind=NodeKind.LAYER,
            kind_ru=NODE_KIND_LABELS_RU[NodeKind.LAYER],
            title_ru=INSTITUTE_TITLES_RU["general_effects"],
            detail_ru="судьба требования из договора",
            needs_human=result.general_effects_evaluation.requires_human_general_effects_assessment,
        )
    )

    for field_name in ReviewedContractAnalysisResult.model_fields:
        if not field_name.endswith("_evaluation"):
            continue
        institute = field_name[: -len("_evaluation")]
        if institute in _LAYER_INSTITUTES:
            continue
        evaluation = getattr(result, field_name)
        if not _spoke(evaluation):
            continue
        node_id = f"institute:{institute}"
        nodes.append(
            MapNode(
                id=node_id,
                kind=NodeKind.INSTITUTE,
                kind_ru=NODE_KIND_LABELS_RU[NodeKind.INSTITUTE],
                title_ru=INSTITUTE_TITLES_RU[institute],
                detail_ru="выводы: " + ", ".join(_true_fields(evaluation)),
                needs_human=_needs_human(evaluation),
            )
        )
        edges.append(
            MapEdge(
                source=evidence_id,
                target=node_id,
                connected=True,
                reason_ru="факты дела разобраны этим институтом",
            )
        )
        if institute in LAYER_FED_BY:
            edges.append(
                MapEdge(
                    source=node_id,
                    target=layer_id,
                    connected=True,
                    reason_ru="вывод института входит в слой общих положений",
                )
            )
            continue
        audit = LAYER_CONNECTIVITY_AUDIT.get(institute)
        if audit is None:
            edges.append(
                MapEdge(
                    source=node_id,
                    target=layer_id,
                    connected=False,
                    reason_ru="связи нет и причина не записана — это дефект аудита",
                    open_debt=True,
                )
            )
            continue
        verdict, reason = audit
        edges.append(
            MapEdge(
                source=node_id,
                target=layer_id,
                connected=False,
                reason_ru=f"{VERDICT_LABELS_RU[verdict]}: {reason}",
                open_debt=verdict is ConnectivityVerdict.SHOULD_BE_WIRED,
            )
        )

    shown_sources = sum(1 for node in nodes if node.kind is NodeKind.SOURCE)
    notes: list[str] = [
        f"На карте {shown_sources} источников из {len(result.source_ids)} проверенных "
        "артефактов дела: показаны те, на которые ссылается линия вывода."
    ]
    debts = [edge for edge in edges if edge.open_debt]
    if debts:
        titles = ", ".join(INSTITUTE_TITLES_RU[edge.source.split(":", 1)[1]] for edge in debts)
        notes.append(
            "По этому делу сработали институты, чей вывод не доходит до итога и "
            f"обоснования этому нет: {titles}. Это открытый долг связности."
        )
    silent = [edge for edge in edges if not edge.connected and not edge.open_debt]
    if silent:
        notes.append(
            f"Разрывов с записанной причиной: {len(silent)}. Вывод института "
            "относится к его собственным правилам и в итог не переносится."
        )
    return CaseMap(nodes=nodes, edges=edges, notes_ru=notes)
