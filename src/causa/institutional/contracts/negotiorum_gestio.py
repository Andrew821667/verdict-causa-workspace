from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


NEGOTIORUM_GESTIO_EVIDENCE_SCHEMA_VERSION = "contracts.negotiorum-gestio-evidence.v0"
NEGOTIORUM_GESTIO_MAPPING_VERSION = "contracts-reviewed-negotiorum-gestio-to-facts-v0"
NEGOTIORUM_GESTIO_MODEL_VERSION = "contracts-negotiorum-gestio-articles-980-989-v0"


class NegotiorumGestioEvidencePredicate(str, Enum):
    # Условия действий в чужом интересе (статья 980 ГК РФ).
    ACTION_IN_ANOTHER_INTEREST_PERFORMED = "action_in_another_interest_performed"
    ACTION_CONDITIONS_BREACHED = "action_conditions_breached"
    # Уведомление заинтересованного лица (статья 981 ГК РФ).
    INTERESTED_PERSON_NOTICE_NOT_GIVEN = "interested_person_notice_not_given"
    NOTICE_WAITING_DUTY_BREACHED = "notice_waiting_duty_breached"
    # Одобрение и неодобрение действий (статьи 982 и 983 ГК РФ).
    APPROVAL_EFFECTS_NOT_APPLIED = "approval_effects_not_applied"
    DISAPPROVED_ACTION_CONTINUED = "disapproved_action_continued"
    # Возмещение убытков и вознаграждение (статьи 984 и 985 ГК РФ).
    NECESSARY_EXPENSES_NOT_REIMBURSED = "necessary_expenses_not_reimbursed"
    REMUNERATION_RULES_BREACHED = "remuneration_rules_breached"
    # Последствия сделки, неосновательное обогащение и отчёт (статьи 986–989 ГК РФ).
    TRANSACTION_CONSEQUENCES_TRANSFER_BREACHED = "transaction_consequences_transfer_breached"
    GESTOR_REPORTING_DUTY_BREACHED = "gestor_reporting_duty_breached"


REQUIRED_NEGOTIORUM_GESTIO_PREDICATES = frozenset(NegotiorumGestioEvidencePredicate)


class NegotiorumGestioEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: NegotiorumGestioEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedNegotiorumGestioEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = NEGOTIORUM_GESTIO_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[NegotiorumGestioEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedNegotiorumGestioEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Negotiorum-gestio evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Negotiorum-gestio evidence contains duplicate legal source refs.")
        return self


class NegotiorumGestioFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action_in_another_interest_performed: bool
    action_conditions_breached: bool
    interested_person_notice_not_given: bool
    notice_waiting_duty_breached: bool
    approval_effects_not_applied: bool
    disapproved_action_continued: bool
    necessary_expenses_not_reimbursed: bool
    remuneration_rules_breached: bool
    transaction_consequences_transfer_breached: bool
    gestor_reporting_duty_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "NegotiorumGestioFactSet":
        if self.notice_waiting_duty_breached and not self.interested_person_notice_not_given:
            raise ValueError(
                "Нарушение обязанности выждать решение заинтересованного лица относится только к "
                "случаю, когда нарушение уведомления этого лица установлено."
            )
        if self.remuneration_rules_breached and not self.action_in_another_interest_performed:
            raise ValueError(
                "Нарушение правил о вознаграждении относится только к действиям в чужом интересе "
                "без поручения."
            )
        return self


class NegotiorumGestioFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class NegotiorumGestioEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: NegotiorumGestioFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[NegotiorumGestioFactProvenance] = Field(default_factory=list)


class NegotiorumGestioConstraintSet(BaseModel):
    id: str
    model_version: str = NEGOTIORUM_GESTIO_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class NegotiorumGestioEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    negotiorum_gestio_qualified: bool
    action_conditions_duty_breached: bool
    notice_duty_breached: bool
    waiting_duty_breached: bool
    approval_effects_breached: bool
    disapproval_effects_breached: bool
    expenses_reimbursement_breached: bool
    remuneration_duty_breached: bool
    transaction_consequences_breached: bool
    reporting_duty_breached: bool
    requires_human_negotiorum_gestio_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_negotiorum_gestio_evidence(
    evidence: ReviewedNegotiorumGestioEvidence,
) -> NegotiorumGestioEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Negotiorum-gestio evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Negotiorum-gestio evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_NEGOTIORUM_GESTIO_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed negotiorum-gestio evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_NEGOTIORUM_GESTIO_PREDICATES
    }
    return NegotiorumGestioEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=NEGOTIORUM_GESTIO_MAPPING_VERSION,
        facts=NegotiorumGestioFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            NegotiorumGestioFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_NEGOTIORUM_GESTIO_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_negotiorum_gestio_constraint_set(
    mapping: NegotiorumGestioEvidenceMappingResult,
) -> NegotiorumGestioConstraintSet:
    return NegotiorumGestioConstraintSet(
        id=f"negotiorum-gestio-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "negotiorum_gestio_qualified == action_in_another_interest_performed",
            "action_conditions_duty_breached == negotiorum_gestio_qualified AND action_conditions_breached",
            "notice_duty_breached == negotiorum_gestio_qualified AND interested_person_notice_not_given",
            "waiting_duty_breached == negotiorum_gestio_qualified AND interested_person_notice_not_given AND notice_waiting_duty_breached",
            "approval_effects_breached == negotiorum_gestio_qualified AND approval_effects_not_applied",
            "disapproval_effects_breached == negotiorum_gestio_qualified AND disapproved_action_continued",
            "expenses_reimbursement_breached == negotiorum_gestio_qualified AND necessary_expenses_not_reimbursed",
            "remuneration_duty_breached == negotiorum_gestio_qualified AND remuneration_rules_breached",
            "transaction_consequences_breached == negotiorum_gestio_qualified AND transaction_consequences_transfer_breached",
            "reporting_duty_breached == negotiorum_gestio_qualified AND gestor_reporting_duty_breached",
            "requires_human_negotiorum_gestio_assessment == action_conditions_duty_breached OR notice_duty_breached OR approval_effects_breached OR disapproval_effects_breached OR expenses_reimbursement_breached OR remuneration_duty_breached OR transaction_consequences_breached OR reporting_duty_breached",
        ],
    )


def evaluate_negotiorum_gestio_constraints(
    constraint_set: NegotiorumGestioConstraintSet,
    facts: NegotiorumGestioFactSet,
) -> NegotiorumGestioEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in NegotiorumGestioFactSet.model_fields
    }
    negotiorum_gestio_qualified = Bool("negotiorum_gestio_qualified")
    action_conditions_duty_breached = Bool("action_conditions_duty_breached")
    notice_duty_breached = Bool("notice_duty_breached")
    waiting_duty_breached = Bool("waiting_duty_breached")
    approval_effects_breached = Bool("approval_effects_breached")
    disapproval_effects_breached = Bool("disapproval_effects_breached")
    expenses_reimbursement_breached = Bool("expenses_reimbursement_breached")
    remuneration_duty_breached = Bool("remuneration_duty_breached")
    transaction_consequences_breached = Bool("transaction_consequences_breached")
    reporting_duty_breached = Bool("reporting_duty_breached")
    requires_human_negotiorum_gestio_assessment = Bool(
        "requires_human_negotiorum_gestio_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(negotiorum_gestio_qualified == variables["action_in_another_interest_performed"])
    solver.add(
        action_conditions_duty_breached
        == And(negotiorum_gestio_qualified, variables["action_conditions_breached"])
    )
    solver.add(
        notice_duty_breached
        == And(negotiorum_gestio_qualified, variables["interested_person_notice_not_given"])
    )
    solver.add(
        waiting_duty_breached
        == And(
            negotiorum_gestio_qualified,
            variables["interested_person_notice_not_given"],
            variables["notice_waiting_duty_breached"],
        )
    )
    solver.add(
        approval_effects_breached
        == And(negotiorum_gestio_qualified, variables["approval_effects_not_applied"])
    )
    solver.add(
        disapproval_effects_breached
        == And(negotiorum_gestio_qualified, variables["disapproved_action_continued"])
    )
    solver.add(
        expenses_reimbursement_breached
        == And(negotiorum_gestio_qualified, variables["necessary_expenses_not_reimbursed"])
    )
    solver.add(
        remuneration_duty_breached
        == And(negotiorum_gestio_qualified, variables["remuneration_rules_breached"])
    )
    solver.add(
        transaction_consequences_breached
        == And(
            negotiorum_gestio_qualified,
            variables["transaction_consequences_transfer_breached"],
        )
    )
    solver.add(
        reporting_duty_breached
        == And(negotiorum_gestio_qualified, variables["gestor_reporting_duty_breached"])
    )
    solver.add(
        requires_human_negotiorum_gestio_assessment
        == Or(
            action_conditions_duty_breached,
            notice_duty_breached,
            approval_effects_breached,
            disapproval_effects_breached,
            expenses_reimbursement_breached,
            remuneration_duty_breached,
            transaction_consequences_breached,
            reporting_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return NegotiorumGestioEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            negotiorum_gestio_qualified=False,
            action_conditions_duty_breached=False,
            notice_duty_breached=False,
            waiting_duty_breached=False,
            approval_effects_breached=False,
            disapproval_effects_breached=False,
            expenses_reimbursement_breached=False,
            remuneration_duty_breached=False,
            transaction_consequences_breached=False,
            reporting_duty_breached=False,
            requires_human_negotiorum_gestio_assessment=True,
            reasons_ru=["Набор фактов о действиях в чужом интересе противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Установлены действия в чужом интересе без поручения: действия без поручения, иного "
            "указания или заранее обещанного согласия заинтересованного лица совершены в целях "
            "предотвращения вреда его личности или имуществу, исполнения его обязательства или в "
            "его иных непротивоправных интересах (статья 980 ГК РФ)."
            if truth(negotiorum_gestio_qualified)
            else "Действия в чужом интересе без поручения не установлены."
        ),
    ]
    if truth(action_conditions_duty_breached):
        reasons_ru.append(
            "Действия в чужом интересе должны совершаться исходя из очевидной выгоды или пользы "
            "и действительных или вероятных намерений заинтересованного лица и с необходимой по "
            "обстоятельствам дела заботливостью и осмотрительностью (статья 980 ГК РФ)."
        )
    if truth(notice_duty_breached):
        reasons_ru.append(
            "Лицо, действующее в чужом интересе, обязано при первой возможности сообщить об этом "
            "заинтересованному лицу (статья 981 ГК РФ)."
        )
    if truth(waiting_duty_breached):
        reasons_ru.append(
            "После сообщения заинтересованному лицу необходимо выждать в течение разумного срока "
            "его решение об одобрении или о неодобрении предпринимаемых действий, если такое "
            "ожидание не влечёт серьёзного ущерба (статья 981 ГК РФ)."
        )
    if truth(approval_effects_breached):
        reasons_ru.append(
            "Если лицо, в интересе которого предпринимаются действия, одобрит их, к отношениям "
            "сторон в дальнейшем применяются правила о договоре поручения или ином договоре, "
            "соответствующем характеру предпринятых действий (статья 982 ГК РФ)."
        )
    if truth(disapproval_effects_breached):
        reasons_ru.append(
            "Действия в чужом интересе, совершённые после того, как тому, кто их совершает, стало "
            "известно о неодобрении их заинтересованным лицом, не влекут для последнего "
            "обязанностей ни в отношении совершившего эти действия, ни в отношении третьих лиц "
            "(статья 983 ГК РФ)."
        )
    if truth(expenses_reimbursement_breached):
        reasons_ru.append(
            "Необходимые расходы и иной реальный ущерб, понесённые лицом, действовавшим в чужом "
            "интересе, подлежат возмещению заинтересованным лицом, за исключением расходов, "
            "вызванных действиями после неодобрения (статья 984 ГК РФ)."
        )
    if truth(remuneration_duty_breached):
        reasons_ru.append(
            "Лицо, действия которого в чужом интересе привели к положительному для "
            "заинтересованного лица результату, имеет право на вознаграждение, если оно "
            "предусмотрено законом, соглашением или обычаями делового оборота "
            "(статья 985 ГК РФ)."
        )
    if truth(transaction_consequences_breached):
        reasons_ru.append(
            "Обязанности по сделке, заключённой в чужом интересе, переходят к лицу, в интересах "
            "которого она совершена, при условии одобрения им этой сделки и отсутствия возражений "
            "другой стороны (статья 986 ГК РФ)."
        )
    if truth(reporting_duty_breached):
        reasons_ru.append(
            "Лицо, действовавшее в чужом интересе, обязано представить заинтересованному лицу "
            "отчёт с указанием полученных доходов и понесённых расходов и иных убытков "
            "(статья 989 ГК РФ)."
        )
    return NegotiorumGestioEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        negotiorum_gestio_qualified=truth(negotiorum_gestio_qualified),
        action_conditions_duty_breached=truth(action_conditions_duty_breached),
        notice_duty_breached=truth(notice_duty_breached),
        waiting_duty_breached=truth(waiting_duty_breached),
        approval_effects_breached=truth(approval_effects_breached),
        disapproval_effects_breached=truth(disapproval_effects_breached),
        expenses_reimbursement_breached=truth(expenses_reimbursement_breached),
        remuneration_duty_breached=truth(remuneration_duty_breached),
        transaction_consequences_breached=truth(transaction_consequences_breached),
        reporting_duty_breached=truth(reporting_duty_breached),
        requires_human_negotiorum_gestio_assessment=truth(
            requires_human_negotiorum_gestio_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о действиях в чужом интересе без "
            "поручения и не заменяет судебную оценку.",
            "Очевидность выгоды, действительные намерения заинтересованного лица и необходимость "
            "понесённых расходов оцениваются экспертом и судом (статьи 980 и 984 ГК РФ).",
        ],
    )
