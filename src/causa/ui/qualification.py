"""Автоматическая квалификация дела: какой кластер система определила сама.

## Что здесь происходит

Оператор загружает материалы и не обязан знать, каким институтом ГК РФ его спор
описывается. Квалификацию определяет система: у 62 институтов есть предикат
квалификации (`*_qualified`), и сработавшие предикаты и есть кластер дела.

## Почему здесь нет процента уверенности

Проценту неоткуда взяться. Предикат квалификации — булев вывод решателя из
проверенных фактов, а не оценка правдоподобия; приписать ему «уверенность 0.82»
значило бы выдать выдуманное число за измеренное. Это ровно тот дефект, который
интерфейс обязан не допускать: предложенное не должно выглядеть установленным.

Вместо числа состояние квалификации выражено тем, что действительно вычислимо:

`SINGLE`
    В своей группе сработал ровно один предикат — конкуренции нет.

`COMPETING`
    В группе сработало несколько. Это не ошибка: дело может быть одновременно
    поставкой и куплей-продажей, потому что специальные правила поставки
    надстроены над общими. Но оператор обязан это видеть.

`NEEDS_HUMAN`
    Институт сам поднял флаг `requires_human_*`. Квалификация состоялась, но
    институт просит человека, и интерфейс не имеет права это скрыть.

## Чего здесь нет

Квалификация не переопределяется оператором молча. Замечание оператора о
квалификации — отдельное действие (`causa.ui.remarks`), оно фиксируется как
уточнение по делу либо как сигнал обучения, но не переписывает вывод модели.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.layer_connectivity import (
    LAYER_CONNECTIVITY_AUDIT,
    ConnectivityVerdict,
)
from causa.institutional.contracts.practice_coverage import (
    INSTITUTE_ARTICLE_RANGES,
    article_sort_key,
    institutes_for_article,
    uncovered_domain_ru,
)
from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult
from causa.ui.institute_titles import INSTITUTE_TITLES_RU

QUALIFICATION_VERSION = "ui-qualification-v0"

#: Предикаты, которые содержат «qualified», но кластер дела не определяют.
#:
#: Список ведётся явно и с причиной: молчаливое исключение предиката неотличимо
#: от того, что его забыли.
NOT_A_CLUSTER_PREDICATE_RU: dict[str, str] = {
    "force_majeure_qualified": (
        "вывод о свойствах обстоятельства (статья 401 ГК РФ), а не о том, "
        "каким договорным типом описывается спор"
    ),
}


#: Специальный тип → общий тип, правила которого он вытесняет.
#:
#: Это структура части второй ГК РФ, а не эвристика интерфейса: поставка —
#: вид купли-продажи (статья 506), прокат — вид аренды (статья 626), бытовой
#: подряд — вид подряда (статья 730). Без этой связи конкуренция квалификаций
#: выглядела бы противоречием, хотя она и есть нормальное устройство кодекса.
#: Розничная купля-продажа и поставка для государственных нужд отсюда убраны.
#: У них нет предиката квалификации: ни `retail_sale_qualified`, ни
#: `state_supply_qualified` в модели не существует, поэтому вытеснять они
#: никогда ничего не могли, и обе записи были мёртвым кодом. Вернуть их сюда
#: следует вместе с предикатом, а не раньше; тест это охраняет.
SPECIALISATION: dict[str, str] = {
    "supply": "sale",
    "contractation": "sale",
    "energy_supply": "sale",
    "real_estate_sale": "sale",
    "enterprise_sale": "sale",
    "rental": "lease",
    "vehicle_lease": "lease",
    "building_lease": "lease",
    "enterprise_lease": "building_lease",
    "leasing": "lease",
    "residential_lease": "lease",
    "consumer_work": "work_contract",
    "construction_contract": "work_contract",
    "design_work": "work_contract",
    "state_work": "work_contract",
    "research_work": "work_contract",
    "warehouse_storage": "storage",
    "special_storage": "storage",
    "insurance_settlement": "insurance",
    "commercial_credit": "loan",
    "credit": "loan",
    "factoring": "loan",
}


class CaseScope(str, Enum):
    """Относится ли дело к тому, что система вообще умеет разбирать."""

    #: Сработал хотя бы один предикат квалификации.
    IN_SCOPE = "in_scope"
    #: Заявленные по делу статьи не покрыты ни одним институтом.
    OUT_OF_SCOPE_SUSPECTED = "out_of_scope_suspected"
    #: Ничего не сработало, а статьи не заявлены: судить не о чем.
    UNDETERMINED = "undetermined"


SCOPE_LABELS_RU = {
    CaseScope.IN_SCOPE: "дело относится к смоделированной области",
    CaseScope.OUT_OF_SCOPE_SUSPECTED: "дело, похоже, вне смоделированной области",
    CaseScope.UNDETERMINED: "область дела не определена",
}


class QualificationCertainty(str, Enum):
    SINGLE = "single"
    COMPETING = "competing"
    NEEDS_HUMAN = "needs_human"


CERTAINTY_LABELS_RU = {
    QualificationCertainty.SINGLE: "единственная квалификация в своей группе",
    QualificationCertainty.COMPETING: "конкурирует с другой квалификацией",
    QualificationCertainty.NEEDS_HUMAN: "институт запросил проверку человеком",
}


class ClusterGroup(str, Enum):
    SPECIAL_TYPE = "special_type"
    GENERAL_PART = "general_part"


GROUP_LABELS_RU = {
    ClusterGroup.SPECIAL_TYPE: "специальный договорный тип",
    ClusterGroup.GENERAL_PART: "общая часть",
}


class ClusterCandidate(BaseModel):
    """Один сработавший кластер — то, что оператор видит в окне квалификации."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    institute: str
    title_ru: str
    predicate: str
    group: ClusterGroup
    group_ru: str
    articles_ru: str
    certainty: QualificationCertainty
    certainty_ru: str
    basis_ru: str
    #: Общий тип, чьи правила этот институт вытесняет как специальные.
    specialises: str | None = None
    #: Истина, если в этом же деле сработал более специальный тип.
    displaced_by_special_rule: bool = False


class CaseQualification(BaseModel):
    """Квалификация дела целиком: что сработало и что с этим делать."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = QUALIFICATION_VERSION
    candidates: list[ClusterCandidate] = Field(default_factory=list)
    primary: ClusterCandidate | None = None
    competing: bool = False
    #: Относится ли дело к тому, что система умеет разбирать.
    scope: CaseScope = CaseScope.UNDETERMINED
    #: Статьи, заявленные по делу и не покрытые ни одним институтом.
    uncovered_articles: list[str] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


def _article_range_ru(institute: str) -> str:
    ranges = INSTITUTE_ARTICLE_RANGES.get(institute)
    if not ranges:
        return "статьи не сопоставлены"
    parts = [first if first == last else f"{first}–{last}" for first, last in ranges]
    return "статьи " + ", ".join(parts) + " ГК РФ"


def _group_of(institute: str) -> ClusterGroup:
    entry = LAYER_CONNECTIVITY_AUDIT.get(institute)
    if entry is not None and entry[0] is ConnectivityVerdict.SPECIAL_TYPE:
        return ClusterGroup.SPECIAL_TYPE
    return ClusterGroup.GENERAL_PART


def qualification_predicates() -> dict[str, str]:
    """Институт → имя его предиката квалификации.

    Набор выводится из модели результата, а не перечисляется вручную: новый
    институт с предикатом квалификации попадает в квалификацию сам. Исключения
    ведутся в `NOT_A_CLUSTER_PREDICATE_RU` и обязаны нести причину.
    """
    found: dict[str, str] = {}
    for field_name, field in ReviewedContractAnalysisResult.model_fields.items():
        if not field_name.endswith("_evaluation"):
            continue
        institute = field_name[: -len("_evaluation")]
        predicates = [
            name
            for name in getattr(field.annotation, "model_fields", {})
            if name.endswith("_qualified") and name not in NOT_A_CLUSTER_PREDICATE_RU
        ]
        if len(predicates) == 1:
            found[institute] = predicates[0]
        elif len(predicates) > 1:
            # Несколько предикатов в одном институте — самостоятельные
            # квалификации (товарный и коммерческий кредит), каждая своя строка.
            for index, predicate in enumerate(sorted(predicates)):
                key = institute if index == 0 else f"{institute}:{predicate}"
                found[key] = predicate
    return found


def _human_review_flag(evaluation) -> bool:
    for name in getattr(type(evaluation), "model_fields", {}):
        if name.startswith("requires_human_") and getattr(evaluation, name) is True:
            return True
    return False


def build_case_qualification(
    result: ReviewedContractAnalysisResult,
    claimed_articles: list[str] | None = None,
) -> CaseQualification:
    """Собрать квалификацию дела из сработавших предикатов.

    `claimed_articles` — статьи ГК, на которые ссылается само дело. Они нужны
    ровно для одного: отличить «материалов не хватает» от «это не моя отрасль».
    Без них система молчала о разнице, а вердикт заполнял молчание неправдой —
    по делу о наследстве утверждал, что договор недействителен.
    """
    raw: list[tuple[str, str, ClusterGroup, bool]] = []
    for key, predicate in qualification_predicates().items():
        institute = key.split(":", 1)[0]
        evaluation = getattr(result, f"{institute}_evaluation")
        if getattr(evaluation, predicate) is not True:
            continue
        raw.append((institute, predicate, _group_of(institute), _human_review_flag(evaluation)))

    present = {institute for institute, _, _, _ in raw}
    displaced: set[str] = set()
    for institute in present:
        parent = SPECIALISATION.get(institute)
        while parent is not None:
            if parent in present:
                displaced.add(parent)
            parent = SPECIALISATION.get(parent)

    # Конкуренция считается только среди невытесненных: пара «поставка и
    # купля-продажа» разрешена статьёй 506, а не оставлена оператору.
    unresolved: dict[ClusterGroup, int] = {}
    for institute, _, group, _ in raw:
        if institute not in displaced:
            unresolved[group] = unresolved.get(group, 0) + 1

    candidates: list[ClusterCandidate] = []
    for institute, predicate, group, needs_human in sorted(raw):
        if needs_human:
            certainty = QualificationCertainty.NEEDS_HUMAN
        elif institute not in displaced and unresolved.get(group, 0) > 1:
            certainty = QualificationCertainty.COMPETING
        else:
            certainty = QualificationCertainty.SINGLE
        candidates.append(
            ClusterCandidate(
                institute=institute,
                title_ru=INSTITUTE_TITLES_RU[institute],
                predicate=predicate,
                group=group,
                group_ru=GROUP_LABELS_RU[group],
                articles_ru=_article_range_ru(institute),
                certainty=certainty,
                certainty_ru=CERTAINTY_LABELS_RU[certainty],
                basis_ru=(
                    f"предикат `{predicate}` истинен по проверенным фактам дела; "
                    f"{_article_range_ru(institute)}"
                ),
                specialises=SPECIALISATION.get(institute),
                displaced_by_special_rule=institute in displaced,
            )
        )

    special = [
        c
        for c in candidates
        if c.group is ClusterGroup.SPECIAL_TYPE and not c.displaced_by_special_rule
    ]
    if len(special) == 1:
        primary = special[0]
    elif special:
        primary = None
    else:
        remaining = [c for c in candidates if not c.displaced_by_special_rule]
        primary = remaining[0] if len(remaining) == 1 else None

    uncovered = sorted(
        {article for article in (claimed_articles or []) if not institutes_for_article(article)},
        key=article_sort_key,
    )
    if candidates:
        scope = CaseScope.IN_SCOPE
    elif uncovered:
        scope = CaseScope.OUT_OF_SCOPE_SUSPECTED
    else:
        scope = CaseScope.UNDETERMINED

    notes: list[str] = []
    if scope is CaseScope.OUT_OF_SCOPE_SUSPECTED:
        domains = sorted({uncovered_domain_ru(article) for article in uncovered})
        notes.append(
            "Заявленные по делу статьи не покрыты ни одним институтом: "
            + ", ".join(uncovered)
            + ". "
            + " ".join(domains)
            + " Это не нехватка материалов, а граница компетенции системы."
        )
    elif uncovered:
        # Квалификация состоялась, но дело ссылается и на то, чего в модели нет.
        # Молчать об этом нельзя: разбор будет верным лишь в своей части.
        notes.append(
            "Часть заявленных по делу статей не покрыта ни одним институтом: "
            + ", ".join(uncovered)
            + ". Разбор относится только к покрытой части спора."
        )
    elif not candidates:
        notes.append(
            "Ни один предикат квалификации не сработал. Статьи по делу не "
            "заявлены, поэтому нельзя сказать, чего не хватает — материалов "
            "или самого института. Это ответ, а не сбой."
        )
    if displaced:
        pairs = ", ".join(
            f"{INSTITUTE_TITLES_RU[child]} вытесняет правила «{INSTITUTE_TITLES_RU[parent]}»"
            for child, parent in sorted(SPECIALISATION.items())
            if child in present and parent in displaced
        )
        notes.append(
            "Сработало несколько типов, и это устройство кодекса, а не "
            f"противоречие: {pairs}. Общие правила продолжают применяться в "
            "части, не изменённой специальными."
        )
    if len(special) > 1:
        notes.append(
            "Несколько специальных типов не сводятся друг к другу. Выбор "
            "квалификации остаётся за оператором: система его не делает."
        )
    if any(c.certainty is QualificationCertainty.NEEDS_HUMAN for c in candidates):
        notes.append(
            "Институт поднял флаг проверки человеком: квалификация состоялась, "
            "но её нельзя показывать как окончательную."
        )
    return CaseQualification(
        candidates=candidates,
        primary=primary,
        competing=any(count > 1 for count in unresolved.values()),
        scope=scope,
        uncovered_articles=uncovered,
        notes_ru=notes,
    )
