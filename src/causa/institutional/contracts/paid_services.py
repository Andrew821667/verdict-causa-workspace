from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PAID_SERVICES_EVIDENCE_SCHEMA_VERSION = "contracts.paid-services-evidence.v0"
PAID_SERVICES_MAPPING_VERSION = "contracts-reviewed-paid-services-to-facts-v0"
PAID_SERVICES_MODEL_VERSION = "contracts-paid-services-articles-779-783-1-v0"


class PaidServicesEvidencePredicate(str, Enum):
    # Понятие возмездного оказания услуг и его границы (статья 779 ГК РФ).
    SERVICES_RENDERED_FOR_FEE_BY_ASSIGNMENT = "services_rendered_for_fee_by_assignment"
    CONTRACT_COVERED_BY_SPECIAL_CHAPTER = "contract_covered_by_special_chapter"
    # Личное исполнение и оплата услуг (статьи 780 и 781 ГК РФ).
    THIRD_PARTY_PERFORMED_WITHOUT_CONTRACT_PERMISSION = (
        "third_party_performed_without_contract_permission"
    )
    PAYMENT_TERMS_OR_DEADLINE_BREACHED = "payment_terms_or_deadline_breached"
    IMPOSSIBILITY_CAUSED_BY_CUSTOMER = "impossibility_caused_by_customer"
    IMPOSSIBILITY_WITHOUT_PARTY_FAULT = "impossibility_without_party_fault"
    ACTUAL_EXPENSES_NOT_REIMBURSED = "actual_expenses_not_reimbursed"
    # Односторонний отказ от договора (статья 782 ГК РФ).
    CUSTOMER_WITHDREW_WITHOUT_COVERING_EXPENSES = "customer_withdrew_without_covering_expenses"
    PERFORMER_WITHDREW_WITHOUT_FULL_COMPENSATION = "performer_withdrew_without_full_compensation"
    # Особенности услуг связи (статья 783.1 ГК РФ).
    COMMUNICATION_SUSPENSION_RULES_BREACHED = "communication_suspension_rules_breached"


REQUIRED_PAID_SERVICES_PREDICATES = frozenset(PaidServicesEvidencePredicate)


class PaidServicesEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: PaidServicesEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedPaidServicesEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PAID_SERVICES_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[PaidServicesEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedPaidServicesEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Paid-services evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Paid-services evidence contains duplicate legal source refs.")
        return self


class PaidServicesFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    services_rendered_for_fee_by_assignment: bool
    contract_covered_by_special_chapter: bool
    third_party_performed_without_contract_permission: bool
    payment_terms_or_deadline_breached: bool
    impossibility_caused_by_customer: bool
    impossibility_without_party_fault: bool
    actual_expenses_not_reimbursed: bool
    customer_withdrew_without_covering_expenses: bool
    performer_withdrew_without_full_compensation: bool
    communication_suspension_rules_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "PaidServicesFactSet":
        if self.actual_expenses_not_reimbursed and not self.impossibility_without_party_fault:
            raise ValueError(
                "Невозмещение фактически понесённых расходов относится только к случаю, когда "
                "невозможность исполнения по обстоятельствам, за которые ни одна из сторон не "
                "отвечает, установлена."
            )
        if self.impossibility_caused_by_customer and self.impossibility_without_party_fault:
            raise ValueError(
                "Невозможность исполнения по вине заказчика и невозможность по обстоятельствам, "
                "за которые ни одна из сторон не отвечает, исключают друг друга."
            )
        return self


class PaidServicesFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class PaidServicesEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: PaidServicesFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[PaidServicesFactProvenance] = Field(default_factory=list)


class PaidServicesConstraintSet(BaseModel):
    id: str
    model_version: str = PAID_SERVICES_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class PaidServicesEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    paid_services_qualified: bool
    special_chapter_exclusion_applies: bool
    personal_performance_duty_breached: bool
    payment_duty_breached: bool
    customer_fault_full_payment_due: bool
    no_fault_impossibility_established: bool
    actual_expenses_reimbursement_due: bool
    customer_withdrawal_expenses_due: bool
    performer_withdrawal_compensation_due: bool
    communication_suspension_breached: bool
    requires_human_paid_services_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_paid_services_evidence(
    evidence: ReviewedPaidServicesEvidence,
) -> PaidServicesEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Paid-services evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Paid-services evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_PAID_SERVICES_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed paid-services evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_PAID_SERVICES_PREDICATES
    }
    return PaidServicesEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PAID_SERVICES_MAPPING_VERSION,
        facts=PaidServicesFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            PaidServicesFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_PAID_SERVICES_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_paid_services_constraint_set(
    mapping: PaidServicesEvidenceMappingResult,
) -> PaidServicesConstraintSet:
    return PaidServicesConstraintSet(
        id=f"paid-services-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "paid_services_qualified == services_rendered_for_fee_by_assignment",
            "special_chapter_exclusion_applies == paid_services_qualified AND contract_covered_by_special_chapter",
            "personal_performance_duty_breached == paid_services_qualified AND third_party_performed_without_contract_permission",
            "payment_duty_breached == paid_services_qualified AND payment_terms_or_deadline_breached",
            "customer_fault_full_payment_due == paid_services_qualified AND impossibility_caused_by_customer",
            "no_fault_impossibility_established == paid_services_qualified AND impossibility_without_party_fault",
            "actual_expenses_reimbursement_due == paid_services_qualified AND impossibility_without_party_fault AND actual_expenses_not_reimbursed",
            "customer_withdrawal_expenses_due == paid_services_qualified AND customer_withdrew_without_covering_expenses",
            "performer_withdrawal_compensation_due == paid_services_qualified AND performer_withdrew_without_full_compensation",
            "communication_suspension_breached == paid_services_qualified AND communication_suspension_rules_breached",
            "requires_human_paid_services_assessment == special_chapter_exclusion_applies OR personal_performance_duty_breached OR payment_duty_breached OR customer_fault_full_payment_due OR no_fault_impossibility_established OR customer_withdrawal_expenses_due OR performer_withdrawal_compensation_due OR communication_suspension_breached",
        ],
    )


def evaluate_paid_services_constraints(
    constraint_set: PaidServicesConstraintSet,
    facts: PaidServicesFactSet,
) -> PaidServicesEvaluation:
    variables = {field_name: Bool(field_name) for field_name in PaidServicesFactSet.model_fields}
    paid_services_qualified = Bool("paid_services_qualified")
    special_chapter_exclusion_applies = Bool("special_chapter_exclusion_applies")
    personal_performance_duty_breached = Bool("personal_performance_duty_breached")
    payment_duty_breached = Bool("payment_duty_breached")
    customer_fault_full_payment_due = Bool("customer_fault_full_payment_due")
    no_fault_impossibility_established = Bool("no_fault_impossibility_established")
    actual_expenses_reimbursement_due = Bool("actual_expenses_reimbursement_due")
    customer_withdrawal_expenses_due = Bool("customer_withdrawal_expenses_due")
    performer_withdrawal_compensation_due = Bool("performer_withdrawal_compensation_due")
    communication_suspension_breached = Bool("communication_suspension_breached")
    requires_human_paid_services_assessment = Bool("requires_human_paid_services_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(paid_services_qualified == variables["services_rendered_for_fee_by_assignment"])
    solver.add(
        special_chapter_exclusion_applies
        == And(paid_services_qualified, variables["contract_covered_by_special_chapter"])
    )
    solver.add(
        personal_performance_duty_breached
        == And(
            paid_services_qualified,
            variables["third_party_performed_without_contract_permission"],
        )
    )
    solver.add(
        payment_duty_breached
        == And(paid_services_qualified, variables["payment_terms_or_deadline_breached"])
    )
    solver.add(
        customer_fault_full_payment_due
        == And(paid_services_qualified, variables["impossibility_caused_by_customer"])
    )
    solver.add(
        no_fault_impossibility_established
        == And(paid_services_qualified, variables["impossibility_without_party_fault"])
    )
    solver.add(
        actual_expenses_reimbursement_due
        == And(
            paid_services_qualified,
            variables["impossibility_without_party_fault"],
            variables["actual_expenses_not_reimbursed"],
        )
    )
    solver.add(
        customer_withdrawal_expenses_due
        == And(paid_services_qualified, variables["customer_withdrew_without_covering_expenses"])
    )
    solver.add(
        performer_withdrawal_compensation_due
        == And(paid_services_qualified, variables["performer_withdrew_without_full_compensation"])
    )
    solver.add(
        communication_suspension_breached
        == And(paid_services_qualified, variables["communication_suspension_rules_breached"])
    )
    solver.add(
        requires_human_paid_services_assessment
        == Or(
            special_chapter_exclusion_applies,
            personal_performance_duty_breached,
            payment_duty_breached,
            customer_fault_full_payment_due,
            no_fault_impossibility_established,
            customer_withdrawal_expenses_due,
            performer_withdrawal_compensation_due,
            communication_suspension_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return PaidServicesEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            paid_services_qualified=False,
            special_chapter_exclusion_applies=False,
            personal_performance_duty_breached=False,
            payment_duty_breached=False,
            customer_fault_full_payment_due=False,
            no_fault_impossibility_established=False,
            actual_expenses_reimbursement_due=False,
            customer_withdrawal_expenses_due=False,
            performer_withdrawal_compensation_due=False,
            communication_suspension_breached=False,
            requires_human_paid_services_assessment=True,
            reasons_ru=["Набор фактов о возмездном оказании услуг противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как возмездное оказание услуг: исполнитель обязуется по "
            "заданию заказчика оказать услуги — совершить определённые действия или осуществить "
            "определённую деятельность, а заказчик обязуется оплатить эти услуги "
            "(статья 779 ГК РФ)."
            if truth(paid_services_qualified)
            else "Отношения не квалифицированы как договор возмездного оказания услуг."
        ),
    ]
    if truth(special_chapter_exclusion_applies):
        reasons_ru.append(
            "Услуги оказываются по договору, предусмотренному отдельной главой Кодекса, поэтому "
            "правила о возмездном оказании услуг к таким отношениям не применяются "
            "(статья 779 ГК РФ)."
        )
    if truth(personal_performance_duty_breached):
        reasons_ru.append(
            "Исполнитель обязан оказать услуги лично, если иное не предусмотрено договором "
            "(статья 780 ГК РФ)."
        )
    if truth(payment_duty_breached):
        reasons_ru.append(
            "Заказчик обязан оплатить оказанные ему услуги в сроки и в порядке, которые указаны в "
            "договоре возмездного оказания услуг (статья 781 ГК РФ)."
        )
    if truth(customer_fault_full_payment_due):
        reasons_ru.append(
            "Невозможность исполнения возникла по вине заказчика: услуги подлежат оплате в полном "
            "объёме, если иное не предусмотрено законом или договором (статья 781 ГК РФ)."
        )
    if truth(no_fault_impossibility_established):
        reasons_ru.append(
            "Невозможность исполнения возникла по обстоятельствам, за которые ни одна из сторон "
            "не отвечает, что влечёт особые правила расчётов (статья 781 ГК РФ)."
        )
    if truth(actual_expenses_reimbursement_due):
        reasons_ru.append(
            "Заказчик обязан возместить исполнителю фактически понесённые им расходы, если иное "
            "не предусмотрено законом или договором (статья 781 ГК РФ)."
        )
    if truth(customer_withdrawal_expenses_due):
        reasons_ru.append(
            "Заказчик вправе отказаться от исполнения договора при условии оплаты исполнителю "
            "фактически понесённых им расходов (статья 782 ГК РФ)."
        )
    if truth(performer_withdrawal_compensation_due):
        reasons_ru.append(
            "Исполнитель вправе отказаться от исполнения обязательств по договору лишь при "
            "условии полного возмещения заказчику убытков (статья 782 ГК РФ)."
        )
    if truth(communication_suspension_breached):
        reasons_ru.append(
            "Приостановление или ограничение оказания услуг связи допускается только в случаях и "
            "порядке, установленных законом и договором (статья 783.1 ГК РФ)."
        )
    return PaidServicesEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        paid_services_qualified=truth(paid_services_qualified),
        special_chapter_exclusion_applies=truth(special_chapter_exclusion_applies),
        personal_performance_duty_breached=truth(personal_performance_duty_breached),
        payment_duty_breached=truth(payment_duty_breached),
        customer_fault_full_payment_due=truth(customer_fault_full_payment_due),
        no_fault_impossibility_established=truth(no_fault_impossibility_established),
        actual_expenses_reimbursement_due=truth(actual_expenses_reimbursement_due),
        customer_withdrawal_expenses_due=truth(customer_withdrawal_expenses_due),
        performer_withdrawal_compensation_due=truth(performer_withdrawal_compensation_due),
        communication_suspension_breached=truth(communication_suspension_breached),
        requires_human_paid_services_assessment=truth(requires_human_paid_services_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о возмездном оказании услуг и не заменяет "
            "судебную оценку.",
            "Качество оказанных услуг, наличие вины стороны и размер фактически понесённых "
            "расходов оцениваются экспертом и судом (статьи 781 и 782 ГК РФ).",
        ],
    )
