"""Схема правоотношения: кто кому что должен и чем это кончилось.

## Зачем схема, если есть карта

Карта разбора (`causa.ui.case_map`) отвечает на вопрос об устройстве системы:
какой институт сработал и доходит ли его вывод до итога. Это карта **работы
машины**.

Схема отвечает на вопрос юриста: какое правоотношение связывает стороны, что с
ним произошло и к какому результату это привело. Одно другое не заменяет:
по карте связности нельзя понять дело, по схеме правоотношения нельзя понять,
почему вывод института не дошёл до итога.

## Почему стороны называются ролями, а не именами

Имён сторон во входах модели нет — там тринадцать фактов обязательства и три
даты. Подставить «ООО „Ромашка“» неоткуда, а придумать значило бы нарисовать
дело, которого система не видела. Поэтому на схеме роли: должник по спорному
обязательству и кредитор. Роль — это то, что из фактов действительно следует.

## Почему связь может быть «не установлена»

Схема рисует и то, чего в деле нет: денежное обязательство, требование
убытков. Пустое место на схеме читается как «этого в деле не заявляли», и это
полезнее, чем схема, на которой видно только заявленное: юрист сразу видит, где
дело не достроено.

## Итог — цепочка, а не ярлык

Результат показан как последовательность условий, каждое из которых либо
достигнуто, либо нет: обязательство → срок → освобождение → нарушение →
средство защиты → судебная защита. Обрыв цепочки виден в том месте, где он
произошёл, а не сводится к красному кружку в конце.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult
from causa.ui.qualification import CaseQualification
from causa.ui.verdict import CaseVerdict

RELATION_SCHEME_VERSION = "ui-relation-scheme-v0"

DEBTOR = "debtor"
CREDITOR = "creditor"


class LinkState(str, Enum):
    #: Связь установлена и исполняется нормально.
    PERFORMED = "performed"
    #: Связь установлена, но нарушена.
    BREACHED = "breached"
    #: Связь установлена, о нарушении речи нет.
    ESTABLISHED = "established"
    #: Такой связи в деле не заявлено.
    ABSENT = "absent"


LINK_STATE_LABELS_RU = {
    LinkState.PERFORMED: "исполнено",
    LinkState.BREACHED: "нарушено",
    LinkState.ESTABLISHED: "установлено",
    LinkState.ABSENT: "не заявлено",
}


class SchemeParty(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title_ru: str
    role_ru: str


class SchemeLink(BaseModel):
    """Одна правовая связь между сторонами."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    source: str
    target: str
    title_ru: str
    state: LinkState
    state_ru: str
    detail_ru: str = ""
    articles_ru: str = ""


class SchemeStage(BaseModel):
    """Одно условие в цепочке от факта к результату."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title_ru: str
    reached: bool
    detail_ru: str = ""


class RelationScheme(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = RELATION_SCHEME_VERSION
    parties: list[SchemeParty] = Field(default_factory=list)
    links: list[SchemeLink] = Field(default_factory=list)
    #: Цепочка условий от обязательства до итога.
    stages: list[SchemeStage] = Field(default_factory=list)
    #: Итоговый вывод — тот же, что в вердикте: два разных ответа недопустимы.
    outcome_ru: str = ""
    outcome_detail_ru: str = ""
    notes_ru: list[str] = Field(default_factory=list)

    @property
    def broke_at(self) -> SchemeStage | None:
        """Первое условие, которое не достигнуто. Здесь цепочка и обрывается."""
        return next((stage for stage in self.stages if not stage.reached), None)


def _obligation_link(
    result: ReviewedContractAnalysisResult,
    qualification: CaseQualification,
) -> SchemeLink:
    facts = result.evidence_mapping.facts
    constraint = result.constraint_evaluation
    primary = qualification.primary
    if not facts.duty_exists:
        state = LinkState.ABSENT
        detail = "существование обязательства по делу не установлено"
    elif constraint.late_performance_issue or constraint.defect_issue:
        state = LinkState.BREACHED
        detail = (
            "срок исполнения пропущен"
            if constraint.late_performance_issue
            else "исполнение отступает от условий обязательства"
        )
    elif facts.performance_completed:
        state = LinkState.PERFORMED
        detail = "обязательство исполнено, притязаний по нему не заявлено"
    else:
        state = LinkState.ESTABLISHED
        detail = "обязательство существует, нарушение не установлено"
    return SchemeLink(
        id="link:performance",
        source=DEBTOR,
        target=CREDITOR,
        title_ru="Обязанность исполнить в натуре",
        state=state,
        state_ru=LINK_STATE_LABELS_RU[state],
        detail_ru=detail,
        articles_ru=primary.articles_ru if primary is not None else "",
    )


def _payment_link(result: ReviewedContractAnalysisResult) -> SchemeLink:
    facts = result.evidence_mapping.facts
    constraint = result.constraint_evaluation
    if not facts.payment_duty_exists:
        state = LinkState.ABSENT
        detail = "денежное обязательство по делу не заявлено"
    elif constraint.payment_default_issue:
        state = LinkState.BREACHED
        detail = "платёж в срок не произведён"
    elif facts.payment_due:
        state = LinkState.ESTABLISHED
        detail = "срок платежа наступил, просрочка не установлена"
    else:
        state = LinkState.ESTABLISHED
        detail = "денежное обязательство существует, срок платежа не наступил"
    return SchemeLink(
        id="link:payment",
        source=CREDITOR,
        target=DEBTOR,
        title_ru="Встречная обязанность оплатить",
        state=state,
        state_ru=LINK_STATE_LABELS_RU[state],
        detail_ru=detail,
        articles_ru="статьи 309–328 ГК РФ",
    )


def _liability_link(result: ReviewedContractAnalysisResult) -> SchemeLink:
    constraint = result.constraint_evaluation
    if not constraint.breach_issue:
        state = LinkState.ABSENT
        detail = "вопрос об ответственности не возникает: нарушение не установлено"
    elif constraint.damages_remedy_available:
        state = LinkState.ESTABLISHED
        detail = "предпосылки требования о возмещении убытков подтверждены"
    else:
        state = LinkState.ESTABLISHED
        detail = (
            "нарушение установлено, но предпосылки требования убытков подтверждены не полностью"
        )
    return SchemeLink(
        id="link:liability",
        source=DEBTOR,
        target=CREDITOR,
        title_ru="Охранительное притязание из нарушения",
        state=state,
        state_ru=LINK_STATE_LABELS_RU[state],
        detail_ru=detail,
        articles_ru="статьи 393–406.1 и 401 ГК РФ",
    )


def build_relation_scheme(
    result: ReviewedContractAnalysisResult,
    qualification: CaseQualification,
    verdict: CaseVerdict,
) -> RelationScheme:
    """Собрать схему правоотношения и цепочку до итога."""
    facts = result.evidence_mapping.facts
    constraint = result.constraint_evaluation
    layer = result.general_effects_evaluation

    parties = [
        SchemeParty(
            id=DEBTOR,
            title_ru="Должник",
            role_ru="сторона спорного обязательства, от которой требуют исполнения",
        ),
        SchemeParty(
            id=CREDITOR,
            title_ru="Кредитор",
            role_ru="сторона, которая вправе требовать исполнения",
        ),
    ]

    links = [
        _obligation_link(result, qualification),
        _payment_link(result),
        _liability_link(result),
    ]

    stages = [
        SchemeStage(
            id="stage:contract",
            title_ru="Договор действует как основание требования",
            reached=layer.contract_legally_effective,
            detail_ru=(
                "договор заключён, действителен и не порочен по форме"
                if layer.contract_legally_effective
                else "договор не действует: спор решается судьбой сделки, а не сроками"
            ),
        ),
        SchemeStage(
            id="stage:duty",
            title_ru="Обязательство существует",
            reached=facts.duty_exists,
            detail_ru=(
                "обязанность должника подтверждена"
                if facts.duty_exists
                else "обязанность должника не подтверждена"
            ),
        ),
        SchemeStage(
            id="stage:due",
            title_ru="Срок исполнения пропущен",
            reached=facts.due_date_missed,
            detail_ru=(
                "пропуск срока вычислен из согласованной даты и даты исполнения"
                if facts.due_date_missed
                else "пропуск срока не установлен"
            ),
        ),
        SchemeStage(
            id="stage:exemption",
            title_ru="Основание освобождения не подтверждено",
            reached=not facts.valid_exception_applies,
            detail_ru=(
                "обстоятельство, освобождающее от ответственности, не установлено"
                if not facts.valid_exception_applies
                else "установлено обстоятельство, освобождающее должника"
            ),
        ),
        SchemeStage(
            id="stage:breach",
            title_ru="Вопрос о нарушении возникает",
            reached=constraint.breach_issue,
            detail_ru=(
                "предпосылки нарушения подтверждены"
                if constraint.breach_issue
                else "предпосылки нарушения не подтверждены"
            ),
        ),
        SchemeStage(
            id="stage:remedy",
            title_ru="Средство защиты доступно",
            reached=constraint.damages_remedy_available,
            detail_ru=(
                "предпосылки требования убытков подтверждены"
                if constraint.damages_remedy_available
                else "подтверждены не все предпосылки требования убытков"
            ),
        ),
        SchemeStage(
            id="stage:protection",
            title_ru="Судебная защита доступна",
            reached=layer.judicial_protection_available,
            detail_ru=(
                "исковая давность и пределы осуществления прав требование не перекрывают"
                if layer.judicial_protection_available
                else "требование перекрыто давностью либо пределами осуществления прав"
            ),
        ),
    ]

    notes = [
        "Стороны названы ролями: имён сторон во входах модели нет, и "
        "подставлять их системе неоткуда.",
        "Связь, помеченная «не заявлено», означает, что этого в деле не "
        "утверждали, а не что этого не было.",
    ]

    return RelationScheme(
        parties=parties,
        links=links,
        stages=stages,
        outcome_ru=verdict.headline_ru,
        outcome_detail_ru=verdict.detail_ru,
        notes_ru=notes,
    )
