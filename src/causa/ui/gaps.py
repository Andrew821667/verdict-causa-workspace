"""Очередь типизированных пробелов: чего системе не хватает и что это меняет.

## Откуда берутся пробелы

Пробел не выдумывается интерфейсом. Он берётся из того, что конвейер уже
вычислил, и каждый тип имеет собственный источник:

`DECISIVE_FACT`
    Материальный контрфактический сценарий. Библиотека правовых операторов
    задаёт вопрос («изменится ли вывод, если исполнение считать совершенным в
    срок?»), решатель отвечает, какие выводы при этом переворачиваются, а
    оператор несёт список доказательств, которыми этот факт закрывается. Это и
    есть типизированный пробел: вопрос, цена ответа и способ закрыть.

`HUMAN_REVIEW`
    Институт поднял флаг `requires_human_*`. Система дошла до границы своей
    компетенции и говорит об этом. Флаг — ответ, а не сбой, и он обязан стать
    задачей оператору, а не строкой в логе.

`NOT_EXPLORED`
    Оператор пропущен: не выполнены предпосылки либо исчерпан бюджет
    контрфактов. Непроверенное не должно выглядеть проверенным.

`FOUND_BY_SWEEP`
    Факт, который переворачивает вывод, но не входит ни в один из семи
    операторов библиотеки. Найден однофакторным обходом
    (`causa.reasoning.sensitivity`), а не выбран из списка.

    Разница не техническая. Библиотека спрашивает то, что кто-то заранее
    написал; обход спрашивает обо всём. Три факта из тринадцати в библиотеку не
    входят вовсе, и это три главных возражения ответчика: «обязанности не
    было», «я исполнил», «у меня есть возражение против платежа». Первое
    переворачивает вывод почти в половине возможных конфигураций дела, и до
    обхода система не задавала его никогда.

## Почему пробел несёт цену

Пробел без последствия — это просьба донести документ «на всякий случай». Здесь
у каждого пробела записано, какие именно выводы изменятся, если факт
установить. Оператор видит не «не хватает данных», а «от этого зависит вывод о
нарушении обязательства».

## Что означает пометка «блокирует вывод»

Раньше — ничего. Она ставилась по признаку «сценарий входит в список
критических», а этот список по построению **совпадал** со списком материальных
сценариев, из которых пробелы и собираются. То есть пометка стояла у каждого
пробела всегда, а охраняющий её тест проверял тавтологию.

Теперь она означает проверяемое: факт меняет судьбу требования, а не
подробность о нём. Судьбу решают три вывода — возникает ли вопрос о нарушении,
доступно ли требование убытков, перекрыто ли требование давностью
(`DECISIVE_OUTCOMES`). Пробел, который переворачивает только доказательственную
подробность внутри уже возникшего вопроса, блокирующим не считается.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.legal_operators import build_contract_legal_operator_library
from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult
from causa.reasoning.sensitivity import DECISIVE_OUTCOMES, sweep_obligation_facts
from causa.ui.documents import DERIVED_FACTS_RU, ClosureKind
from causa.ui.institute_titles import INSTITUTE_TITLES_RU

GAP_QUEUE_VERSION = "ui-gap-queue-v0"


class GapKind(str, Enum):
    DECISIVE_FACT = "decisive_fact"
    HUMAN_REVIEW = "human_review"
    NOT_EXPLORED = "not_explored"
    FOUND_BY_SWEEP = "found_by_sweep"


GAP_KIND_LABELS_RU = {
    GapKind.DECISIVE_FACT: "факт, от которого зависит вывод",
    GapKind.HUMAN_REVIEW: "система остановилась и просит человека",
    GapKind.NOT_EXPLORED: "вопрос не проверялся",
    GapKind.FOUND_BY_SWEEP: "факт найден обходом, а не выбран из списка",
}


class TypedGap(BaseModel):
    """Один пробел в очереди оператора."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    kind: GapKind
    kind_ru: str
    question_ru: str
    #: Что изменится в выводах, если пробел закрыть. Пусто для `HUMAN_REVIEW`.
    consequence_ru: list[str] = Field(default_factory=list)
    #: Чем пробел закрывается: документы и доказательства.
    closes_with_ru: list[str] = Field(default_factory=list)
    institute: str | None = None
    institute_ru: str | None = None
    blocking: bool = False
    #: Как пробел закрывается: утверждением о факте, датой или никак.
    closure_kind: ClosureKind | None = None
    #: Какие факты станут какими, если оператор подтвердит их документом.
    fact_updates: dict[str, bool] = Field(default_factory=dict)


class GapQueue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = GAP_QUEUE_VERSION
    gaps: list[TypedGap] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)

    @property
    def blocking_count(self) -> int:
        return sum(1 for gap in self.gaps if gap.blocking)


def _outcome_phrase(delta) -> str:
    became = "станет «да»" if delta.after else "станет «нет»"
    return f"{delta.field_label_ru}: {became}"


def _decisive_fact_gaps(result: ReviewedContractAnalysisResult) -> list[TypedGap]:
    report = result.counterfactual_sensitivity
    if report is None:
        return []
    library = {
        operator.id: operator for operator in build_contract_legal_operator_library().operators
    }
    gaps: list[TypedGap] = []
    for scenario in report.scenarios:
        if not scenario.material:
            continue
        operator = library.get(scenario.operator_id)
        fact_updates = {delta.field_name: delta.after for delta in scenario.fact_deltas}
        # Пропуск срока не утверждается, а вычисляется из дат, поэтому такой
        # пробел закрывается датой из документа, а не галочкой.
        derived = [field for field in fact_updates if field in DERIVED_FACTS_RU]
        closure_kind = ClosureKind.SUPPLIED_DATE if derived else ClosureKind.ASSERTED_FACT
        gaps.append(
            TypedGap(
                id=f"gap:decisive:{scenario.operator_code.value}",
                kind=GapKind.DECISIVE_FACT,
                kind_ru=GAP_KIND_LABELS_RU[GapKind.DECISIVE_FACT],
                question_ru=scenario.legal_question_ru,
                consequence_ru=[_outcome_phrase(delta) for delta in scenario.outcome_deltas],
                closes_with_ru=list(operator.required_evidence_ru) if operator else [],
                institute="constraint",
                institute_ru=INSTITUTE_TITLES_RU["constraint"],
                blocking=any(
                    delta.field_name in DECISIVE_OUTCOMES for delta in scenario.outcome_deltas
                ),
                closure_kind=closure_kind,
                fact_updates={} if derived else fact_updates,
            )
        )
    return gaps


def _human_review_gaps(result: ReviewedContractAnalysisResult) -> list[TypedGap]:
    gaps: list[TypedGap] = []
    for field_name in ReviewedContractAnalysisResult.model_fields:
        if not field_name.endswith("_evaluation"):
            continue
        institute = field_name[: -len("_evaluation")]
        evaluation = getattr(result, field_name)
        for name in type(evaluation).model_fields:
            if not name.startswith("requires_human_"):
                continue
            if getattr(evaluation, name) is not True:
                continue
            title = INSTITUTE_TITLES_RU[institute]
            gaps.append(
                TypedGap(
                    id=f"gap:human:{institute}:{name}",
                    kind=GapKind.HUMAN_REVIEW,
                    kind_ru=GAP_KIND_LABELS_RU[GapKind.HUMAN_REVIEW],
                    question_ru=(
                        f"«{title}»: модель дошла до границы своей компетенции и "
                        "просит юридическую оценку человека."
                    ),
                    closes_with_ru=[
                        "решение оператора с обоснованием, зафиксированное в деле",
                    ],
                    institute=institute,
                    institute_ru=title,
                    blocking=True,
                )
            )
    return gaps


def _not_explored_gaps(result: ReviewedContractAnalysisResult) -> list[TypedGap]:
    report = result.counterfactual_sensitivity
    if report is None:
        return []
    gaps = [
        TypedGap(
            id=f"gap:not-explored:{skipped.operator_id.rsplit(':', 1)[-1]}",
            kind=GapKind.NOT_EXPLORED,
            kind_ru=GAP_KIND_LABELS_RU[GapKind.NOT_EXPLORED],
            question_ru=skipped.reason_ru,
            closes_with_ru=[],
            blocking=False,
        )
        for skipped in report.skipped_operators
    ]
    if report.budget_exhausted:
        gaps.append(
            TypedGap(
                id="gap:not-explored:budget",
                kind=GapKind.NOT_EXPLORED,
                kind_ru=GAP_KIND_LABELS_RU[GapKind.NOT_EXPLORED],
                question_ru=(
                    "Бюджет контрфактического анализа исчерпан: часть вопросов не "
                    "проверялась, и о них ничего не известно."
                ),
                closes_with_ru=["повышение бюджета в политике, если это допускает риск-тир"],
                blocking=False,
            )
        )
    return gaps


def _library_covered_facts() -> set[str]:
    """Факты, о которых библиотека операторов вообще умеет спрашивать."""
    return {
        field
        for operator in build_contract_legal_operator_library().operators
        for field in operator.fact_patch
    }


def _swept_fact_gaps(result: ReviewedContractAnalysisResult) -> list[TypedGap]:
    """Факты, переворачивающие вывод, о которых библиотека не спрашивает.

    Формулировка вопроса здесь собрана из подписи факта, а не написана юристом,
    и об этом сказано в самом пробеле. Выдавать сгенерированную фразу за
    юридический вопрос нельзя: у операторов библиотеки есть и формулировка, и
    перечень доказательств, а здесь — только измерение.
    """
    covered = _library_covered_facts()
    gaps: list[TypedGap] = []
    for sensitivity in sweep_obligation_facts(result):
        if sensitivity.fact in covered:
            continue
        gaps.append(
            TypedGap(
                id=f"gap:sweep:{sensitivity.fact}",
                kind=GapKind.FOUND_BY_SWEEP,
                kind_ru=GAP_KIND_LABELS_RU[GapKind.FOUND_BY_SWEEP],
                question_ru=sensitivity.question_ru,
                consequence_ru=[flip.line_ru for flip in sensitivity.flips],
                closes_with_ru=[
                    "документ, подтверждающий или опровергающий этот факт",
                    "формулировка вопроса здесь собрана системой: юридической "
                    "постановки для него в библиотеке операторов нет",
                ],
                institute="constraint",
                institute_ru=INSTITUTE_TITLES_RU["constraint"],
                blocking=sensitivity.decisive,
                closure_kind=(
                    ClosureKind.SUPPLIED_DATE
                    if sensitivity.fact in DERIVED_FACTS_RU
                    else ClosureKind.ASSERTED_FACT
                ),
                fact_updates=(
                    {}
                    if sensitivity.fact in DERIVED_FACTS_RU
                    else {sensitivity.fact: sensitivity.to_value}
                ),
            )
        )
    return gaps


def build_gap_queue(result: ReviewedContractAnalysisResult) -> GapQueue:
    """Собрать очередь пробелов по делу."""
    gaps = [
        *_human_review_gaps(result),
        *_decisive_fact_gaps(result),
        *_swept_fact_gaps(result),
        *_not_explored_gaps(result),
    ]
    notes: list[str] = []
    if not gaps:
        notes.append(
            "Очередь пуста: ни один вопрос не меняет вывода и ни один институт "
            "не запросил человека. Это утверждение о деле, а не отсутствие проверки."
        )
    blocking = sum(1 for gap in gaps if gap.blocking)
    if blocking:
        notes.append(
            f"Пробелов, меняющих вывод: {blocking}. Пока они открыты, вывод по "
            "делу нельзя считать окончательным."
        )
    return GapQueue(gaps=gaps, notes_ru=notes)
