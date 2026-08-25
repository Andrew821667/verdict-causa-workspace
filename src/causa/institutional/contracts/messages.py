"""Формальная модель юридически значимых сообщений.

Статья 165.1 ГК РФ: заявления, уведомления, извещения, требования и иные
сообщения, с которыми закон или сделка связывает гражданско-правовые последствия
для другого лица, влекут эти последствия **с момента доставки**. Сообщение
считается доставленным и тогда, когда оно поступило адресату, но по
обстоятельствам, зависящим от него, не было вручено или адресат с ним не
ознакомился.

**Почему институт появился.** Пробел нашёл обход кодекса, а не практика.
Измерение покрытия шло от дел: если суды на статью не ссылались, её отсутствие
никто не замечал. Обход идёт от закона и нашёл статью 165.1 незаявленной ни
одним институтом — при том что она лежит под доброй половиной модели.

В предикатах пакета больше двадцати фактов о доставленном уведомлении: об
отказе от договора (`unilateral_refusal_notice_delivered`), о зачёте
(`set_off_notice_delivered`), о приостановлении встречного исполнения
(`suspension_notice_delivered`), о прощении долга
(`debt_forgiveness_notice_delivered`), о переуступке (`debtor_notified`). Каждый
из них принимал доставку на веру от того, кто заполняет факты, — а правило, по
которому сообщение считается доставленным, не было смоделировано нигде.

**Что даёт модель.** Она разделяет два пути доставки, которые в одном предикате
сливаются:

- `delivered_by_handover` — сообщение вручено адресату или его представителю;
- `delivered_by_addressee_risk` — сообщение не вручено, но считается
  доставленным, потому что поступило адресату и не было получено по
  обстоятельствам, зависящим от него.

Второй путь и есть содержание статьи 165.1. Он требует надлежащего адреса
(пункты 63 и 67 постановления Пленума Верховного Суда РФ от 23 июня 2015 года
№ 25) и возможности достоверно установить отправителя и адресата (пункт 65 того
же постановления) — вручение по первому пути этого не требует: врученное
сообщение доставлено независимо от того, куда его посылали.

**Оговорка об объёме.** Модель отвечает на вопрос об **одном** сообщении — том,
о котором идёт спор. Она не проверяет доставку каждого уведомления, упомянутого
в других институтах: контракт данных даёт один блок доказательств на институт, и
нескольких сообщений в нём не выразить. Связать вывод с двадцатью предикатами
других институтов — открытый вопрос, названный в спецификации.

**Чего модель не делает.** Пункт 2 статьи 165.1 допускает иное правило доставки
— в законе, в условиях сделки, в обычае или в установившейся практике сторон.
Содержание такого правила лежит вне модели: она лишь фиксирует, что общее
правило вытеснено, и поднимает флаг экспертизы.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

MESSAGES_EVIDENCE_SCHEMA_VERSION = "contracts.messages-evidence.v0"
MESSAGES_MAPPING_VERSION = "contracts-reviewed-messages-to-facts-v0"
MESSAGES_MODEL_VERSION = "contracts-messages-article-165-1-v0"


class MessagesEvidencePredicate(str, Enum):
    # Квалификация сообщения как юридически значимого (пункт 1 статьи 165.1).
    MESSAGE_ASSERTED = "message_asserted"
    CONSEQUENCES_ATTACHED_BY_LAW_OR_TRANSACTION = "consequences_attached_by_law_or_transaction"
    # Направление сообщения (пункты 63, 65 и 67 постановления Пленума ВС РФ № 25).
    SENT_TO_STATUTORY_OR_AGREED_ADDRESS = "sent_to_statutory_or_agreed_address"
    SENDER_AND_ADDRESSEE_IDENTIFIABLE = "sender_and_addressee_identifiable"
    FORM_MATCHES_MESSAGE_NATURE = "form_matches_message_nature"
    # Доставка (пункт 1 статьи 165.1).
    HANDED_TO_ADDRESSEE_OR_REPRESENTATIVE = "handed_to_addressee_or_representative"
    ARRIVED_AT_ADDRESSEE = "arrived_at_addressee"
    NON_RECEIPT_DUE_TO_ADDRESSEE = "non_receipt_due_to_addressee"
    # Иное правило доставки (пункт 2 статьи 165.1).
    LAW_SETS_OTHER_DELIVERY_RULE = "law_sets_other_delivery_rule"
    TRANSACTION_SETS_OTHER_DELIVERY_RULE = "transaction_sets_other_delivery_rule"
    CUSTOM_OR_PRACTICE_SETS_OTHER_DELIVERY_RULE = "custom_or_practice_sets_other_delivery_rule"


REQUIRED_MESSAGES_PREDICATES = frozenset(MessagesEvidencePredicate)


class MessagesEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: MessagesEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedMessagesEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = MESSAGES_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[MessagesEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedMessagesEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Messages evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Messages evidence contains duplicate legal source refs.")
        return self


class MessagesFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    message_asserted: bool
    consequences_attached_by_law_or_transaction: bool
    sent_to_statutory_or_agreed_address: bool
    sender_and_addressee_identifiable: bool
    form_matches_message_nature: bool
    handed_to_addressee_or_representative: bool
    arrived_at_addressee: bool
    non_receipt_due_to_addressee: bool
    law_sets_other_delivery_rule: bool
    transaction_sets_other_delivery_rule: bool
    custom_or_practice_sets_other_delivery_rule: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "MessagesFactSet":
        if self.non_receipt_due_to_addressee and not self.arrived_at_addressee:
            raise ValueError(
                "Невручение по обстоятельствам, зависящим от адресата, относится только к "
                "сообщению, которое ему поступило (пункт 1 статьи 165.1 ГК РФ). Не "
                "поступившее сообщение не вручено по обстоятельствам отправителя или "
                "связи, а не адресата."
            )
        if self.handed_to_addressee_or_representative and self.non_receipt_due_to_addressee:
            raise ValueError(
                "Сообщение не может быть одновременно вручённым и невручённым: вручение "
                "и риск неполучения — два разных пути доставки, а не один."
            )
        return self


class MessagesFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class MessagesEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: MessagesFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[MessagesFactProvenance] = Field(default_factory=list)


class MessagesConstraintSet(BaseModel):
    id: str
    model_version: str = MESSAGES_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class MessagesEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    message_qualified: bool
    properly_addressed: bool
    delivered_by_handover: bool
    # Содержание статьи 165.1: сообщение считается доставленным, хотя вручено не было.
    delivered_by_addressee_risk: bool
    default_rule_displaced: bool
    message_delivered: bool
    consequences_effective: bool
    delivery_not_established: bool
    requires_human_message_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_messages_evidence(
    evidence: ReviewedMessagesEvidence,
) -> MessagesEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Messages evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Messages evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_MESSAGES_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed messages evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_MESSAGES_PREDICATES
    }
    return MessagesEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=MESSAGES_MAPPING_VERSION,
        facts=MessagesFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            MessagesFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_MESSAGES_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_messages_constraint_set(
    mapping: MessagesEvidenceMappingResult,
) -> MessagesConstraintSet:
    return MessagesConstraintSet(
        id=f"messages-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "message_qualified == message_asserted AND consequences_attached_by_law_or_transaction",
            "default_rule_displaced == message_qualified AND (law_sets_other_delivery_rule OR transaction_sets_other_delivery_rule OR custom_or_practice_sets_other_delivery_rule)",
            "properly_addressed == message_qualified AND sent_to_statutory_or_agreed_address AND sender_and_addressee_identifiable AND form_matches_message_nature",
            "delivered_by_handover == message_qualified AND handed_to_addressee_or_representative",
            "delivered_by_addressee_risk == properly_addressed AND arrived_at_addressee AND non_receipt_due_to_addressee AND NOT handed_to_addressee_or_representative",
            "message_delivered == (delivered_by_handover OR delivered_by_addressee_risk) AND NOT default_rule_displaced",
            "consequences_effective == message_delivered",
            "delivery_not_established == message_qualified AND NOT message_delivered",
            "requires_human_message_assessment == default_rule_displaced OR delivery_not_established OR delivered_by_addressee_risk",
        ],
    )


def evaluate_messages_constraints(
    constraint_set: MessagesConstraintSet,
    facts: MessagesFactSet,
) -> MessagesEvaluation:
    variables = {field_name: Bool(field_name) for field_name in MessagesFactSet.model_fields}
    message_qualified = Bool("message_qualified")
    properly_addressed = Bool("properly_addressed")
    delivered_by_handover = Bool("delivered_by_handover")
    delivered_by_addressee_risk = Bool("delivered_by_addressee_risk")
    default_rule_displaced = Bool("default_rule_displaced")
    message_delivered = Bool("message_delivered")
    consequences_effective = Bool("consequences_effective")
    delivery_not_established = Bool("delivery_not_established")
    requires_human_message_assessment = Bool("requires_human_message_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        message_qualified
        == And(
            variables["message_asserted"],
            variables["consequences_attached_by_law_or_transaction"],
        )
    )
    solver.add(
        default_rule_displaced
        == And(
            message_qualified,
            Or(
                variables["law_sets_other_delivery_rule"],
                variables["transaction_sets_other_delivery_rule"],
                variables["custom_or_practice_sets_other_delivery_rule"],
            ),
        )
    )
    solver.add(
        properly_addressed
        == And(
            message_qualified,
            variables["sent_to_statutory_or_agreed_address"],
            variables["sender_and_addressee_identifiable"],
            variables["form_matches_message_nature"],
        )
    )
    solver.add(
        delivered_by_handover
        == And(message_qualified, variables["handed_to_addressee_or_representative"])
    )
    solver.add(
        delivered_by_addressee_risk
        == And(
            properly_addressed,
            variables["arrived_at_addressee"],
            variables["non_receipt_due_to_addressee"],
            Not(variables["handed_to_addressee_or_representative"]),
        )
    )
    solver.add(
        message_delivered
        == And(
            Or(delivered_by_handover, delivered_by_addressee_risk),
            Not(default_rule_displaced),
        )
    )
    solver.add(consequences_effective == message_delivered)
    solver.add(delivery_not_established == And(message_qualified, Not(message_delivered)))
    solver.add(
        requires_human_message_assessment
        == Or(default_rule_displaced, delivery_not_established, delivered_by_addressee_risk)
    )

    if solver.check() != sat:
        return MessagesEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            message_qualified=False,
            properly_addressed=False,
            delivered_by_handover=False,
            delivered_by_addressee_risk=False,
            default_rule_displaced=False,
            message_delivered=False,
            consequences_effective=False,
            delivery_not_established=False,
            requires_human_message_assessment=True,
            reasons_ru=["Набор фактов о юридически значимом сообщении противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Заявлено сообщение, с которым закон или сделка связывает гражданско-правовые "
            "последствия для другого лица, — юридически значимое сообщение "
            "(пункт 1 статьи 165.1 ГК РФ)."
            if truth(message_qualified)
            else "Юридически значимое сообщение в деле не заявлено: либо сообщения нет, либо "
            "закон и сделка не связывают с ним последствий для другого лица."
        ),
    ]
    if truth(delivered_by_handover):
        reasons_ru.append(
            "Сообщение вручено адресату или его представителю, поэтому оно доставлено "
            "независимо от того, по какому адресу направлялось (пункт 1 статьи 165.1 ГК РФ)."
        )
    if truth(delivered_by_addressee_risk):
        reasons_ru.append(
            "Сообщение не вручено, но считается доставленным: оно поступило адресату и не "
            "было вручено либо адресат с ним не ознакомился по обстоятельствам, зависящим "
            "от него самого. Риск неполучения несёт адресат (пункт 1 статьи 165.1 ГК РФ, "
            "пункты 63 и 67 постановления Пленума Верховного Суда РФ от 23.06.2015 № 25)."
        )
    if truth(message_qualified) and not truth(properly_addressed):
        reasons_ru.append(
            "Надлежащее направление не подтверждено: сообщение либо послано не по адресу "
            "из реестра, месту жительства или указанному самим адресатом, либо не позволяет "
            "достоверно установить отправителя и адресата, либо направлено в форме, не "
            "соответствующей характеру сообщения (пункты 63, 65 и 67 постановления Пленума "
            "Верховного Суда РФ от 23.06.2015 № 25). Доставка по риску неполучения без "
            "этого не выводится."
        )
    if truth(default_rule_displaced):
        reasons_ru.append(
            "Общее правило доставки вытеснено: иное предусмотрено законом либо условиями "
            "сделки либо следует из обычая или из установившейся во взаимоотношениях "
            "сторон практики (пункт 2 статьи 165.1 ГК РФ). Содержание этого иного правила "
            "модель не разбирает."
        )
    if truth(consequences_effective):
        reasons_ru.append(
            "Гражданско-правовые последствия сообщения наступили для адресата с момента "
            "доставки (пункт 1 статьи 165.1 ГК РФ)."
        )
    if truth(delivery_not_established):
        reasons_ru.append(
            "Доставка не установлена, поэтому последствия сообщения для адресата не "
            "наступили. Это утверждение о доказанности доставки, а не о том, что сообщение "
            "не посылалось."
        )
    return MessagesEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        message_qualified=truth(message_qualified),
        properly_addressed=truth(properly_addressed),
        delivered_by_handover=truth(delivered_by_handover),
        delivered_by_addressee_risk=truth(delivered_by_addressee_risk),
        default_rule_displaced=truth(default_rule_displaced),
        message_delivered=truth(message_delivered),
        consequences_effective=truth(consequences_effective),
        delivery_not_established=truth(delivery_not_established),
        requires_human_message_assessment=truth(requires_human_message_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель отвечает об одном сообщении — том, о котором идёт спор. Доставку "
            "каждого уведомления, упомянутого в других институтах, она не проверяет: "
            "контракт данных даёт один блок доказательств на институт.",
            "Момент доставки модель не определяет: она устанавливает сам факт доставки, а "
            "дату вручения или поступления вносит человек.",
            "Зависимость обстоятельств невручения от адресата — вопрос оценки "
            "доказательств, а не вывода из фактов.",
        ],
    )
