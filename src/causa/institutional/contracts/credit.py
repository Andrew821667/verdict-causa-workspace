from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


CREDIT_EVIDENCE_SCHEMA_VERSION = "contracts.credit-evidence.v0"
CREDIT_MAPPING_VERSION = "contracts-reviewed-credit-to-facts-v0"
CREDIT_MODEL_VERSION = "contracts-credit-articles-819-821-1-v0"


class CreditEvidencePredicate(str, Enum):
    # Понятие кредитного договора и его стороны (статья 819 ГК РФ).
    CREDIT_PROVIDED_FOR_RETURN_WITH_INTEREST = "credit_provided_for_return_with_interest"
    LENDER_NOT_A_CREDIT_ORGANISATION = "lender_not_a_credit_organisation"
    INTEREST_OR_OTHER_PAYMENTS_TERMS_BREACHED = "interest_or_other_payments_terms_breached"
    CONSUMER_CREDIT_RULES_APPLICABLE = "consumer_credit_rules_applicable"
    # Форма кредитного договора (статья 820 ГК РФ).
    WRITTEN_FORM_MISSING = "written_form_missing"
    # Отказ от предоставления и получения кредита (статья 821 ГК РФ).
    LENDER_REFUSED_WITHOUT_INSOLVENCY_GROUNDS = "lender_refused_without_insolvency_grounds"
    BORROWER_NOTICE_OF_REFUSAL_NOT_GIVEN_IN_TIME = "borrower_notice_of_refusal_not_given_in_time"
    TARGETED_CREDIT_MISUSED = "targeted_credit_misused"
    # Требование досрочного возврата кредита (статья 821.1 ГК РФ).
    EARLY_REPAYMENT_DEMANDED_WITHOUT_GROUNDS = "early_repayment_demanded_without_grounds"
    EARLY_REPAYMENT_FROM_CITIZEN_WITHOUT_STATUTORY_GROUND = (
        "early_repayment_from_citizen_without_statutory_ground"
    )


REQUIRED_CREDIT_PREDICATES = frozenset(CreditEvidencePredicate)


class CreditEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: CreditEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCreditEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CREDIT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CreditEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedCreditEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Credit evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Credit evidence contains duplicate legal source refs.")
        return self


class CreditFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    credit_provided_for_return_with_interest: bool
    lender_not_a_credit_organisation: bool
    interest_or_other_payments_terms_breached: bool
    consumer_credit_rules_applicable: bool
    written_form_missing: bool
    lender_refused_without_insolvency_grounds: bool
    borrower_notice_of_refusal_not_given_in_time: bool
    targeted_credit_misused: bool
    early_repayment_demanded_without_grounds: bool
    early_repayment_from_citizen_without_statutory_ground: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "CreditFactSet":
        if self.early_repayment_from_citizen_without_statutory_ground and not (
            self.early_repayment_demanded_without_grounds
        ):
            raise ValueError(
                "Требование досрочного возврата от гражданина вне установленных законом случаев "
                "относится только к случаю, когда требование досрочного возврата без оснований "
                "установлено."
            )
        if self.written_form_missing and not self.credit_provided_for_return_with_interest:
            raise ValueError(
                "Несоблюдение письменной формы относится только к кредитному договору."
            )
        return self


class CreditFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class CreditEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: CreditFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[CreditFactProvenance] = Field(default_factory=list)


class CreditConstraintSet(BaseModel):
    id: str
    model_version: str = CREDIT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class CreditEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    credit_qualified: bool
    lender_status_invalid: bool
    interest_or_payment_terms_breached: bool
    consumer_credit_regime_applies: bool
    written_form_nullity: bool
    lender_refusal_unjustified: bool
    borrower_refusal_notice_breached: bool
    targeted_credit_control_breached: bool
    early_repayment_demand_unjustified: bool
    citizen_early_repayment_restriction_breached: bool
    requires_human_credit_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_credit_evidence(evidence: ReviewedCreditEvidence) -> CreditEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Credit evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Credit evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_CREDIT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed credit evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_CREDIT_PREDICATES
    }
    return CreditEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CREDIT_MAPPING_VERSION,
        facts=CreditFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            CreditFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_CREDIT_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_credit_constraint_set(mapping: CreditEvidenceMappingResult) -> CreditConstraintSet:
    return CreditConstraintSet(
        id=f"credit-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "credit_qualified == credit_provided_for_return_with_interest",
            "lender_status_invalid == credit_qualified AND lender_not_a_credit_organisation",
            "interest_or_payment_terms_breached == credit_qualified AND interest_or_other_payments_terms_breached",
            "consumer_credit_regime_applies == credit_qualified AND consumer_credit_rules_applicable",
            "written_form_nullity == credit_qualified AND written_form_missing",
            "lender_refusal_unjustified == credit_qualified AND lender_refused_without_insolvency_grounds",
            "borrower_refusal_notice_breached == credit_qualified AND borrower_notice_of_refusal_not_given_in_time",
            "targeted_credit_control_breached == credit_qualified AND targeted_credit_misused",
            "early_repayment_demand_unjustified == credit_qualified AND early_repayment_demanded_without_grounds",
            "citizen_early_repayment_restriction_breached == credit_qualified AND early_repayment_demanded_without_grounds AND early_repayment_from_citizen_without_statutory_ground",
            "requires_human_credit_assessment == lender_status_invalid OR interest_or_payment_terms_breached OR consumer_credit_regime_applies OR written_form_nullity OR lender_refusal_unjustified OR borrower_refusal_notice_breached OR targeted_credit_control_breached OR early_repayment_demand_unjustified",
        ],
    )


def evaluate_credit_constraints(
    constraint_set: CreditConstraintSet,
    facts: CreditFactSet,
) -> CreditEvaluation:
    variables = {field_name: Bool(field_name) for field_name in CreditFactSet.model_fields}
    credit_qualified = Bool("credit_qualified")
    lender_status_invalid = Bool("lender_status_invalid")
    interest_or_payment_terms_breached = Bool("interest_or_payment_terms_breached")
    consumer_credit_regime_applies = Bool("consumer_credit_regime_applies")
    written_form_nullity = Bool("written_form_nullity")
    lender_refusal_unjustified = Bool("lender_refusal_unjustified")
    borrower_refusal_notice_breached = Bool("borrower_refusal_notice_breached")
    targeted_credit_control_breached = Bool("targeted_credit_control_breached")
    early_repayment_demand_unjustified = Bool("early_repayment_demand_unjustified")
    citizen_early_repayment_restriction_breached = Bool(
        "citizen_early_repayment_restriction_breached"
    )
    requires_human_credit_assessment = Bool("requires_human_credit_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(credit_qualified == variables["credit_provided_for_return_with_interest"])
    solver.add(
        lender_status_invalid
        == And(credit_qualified, variables["lender_not_a_credit_organisation"])
    )
    solver.add(
        interest_or_payment_terms_breached
        == And(credit_qualified, variables["interest_or_other_payments_terms_breached"])
    )
    solver.add(
        consumer_credit_regime_applies
        == And(credit_qualified, variables["consumer_credit_rules_applicable"])
    )
    solver.add(written_form_nullity == And(credit_qualified, variables["written_form_missing"]))
    solver.add(
        lender_refusal_unjustified
        == And(credit_qualified, variables["lender_refused_without_insolvency_grounds"])
    )
    solver.add(
        borrower_refusal_notice_breached
        == And(credit_qualified, variables["borrower_notice_of_refusal_not_given_in_time"])
    )
    solver.add(
        targeted_credit_control_breached
        == And(credit_qualified, variables["targeted_credit_misused"])
    )
    solver.add(
        early_repayment_demand_unjustified
        == And(credit_qualified, variables["early_repayment_demanded_without_grounds"])
    )
    solver.add(
        citizen_early_repayment_restriction_breached
        == And(
            credit_qualified,
            variables["early_repayment_demanded_without_grounds"],
            variables["early_repayment_from_citizen_without_statutory_ground"],
        )
    )
    solver.add(
        requires_human_credit_assessment
        == Or(
            lender_status_invalid,
            interest_or_payment_terms_breached,
            consumer_credit_regime_applies,
            written_form_nullity,
            lender_refusal_unjustified,
            borrower_refusal_notice_breached,
            targeted_credit_control_breached,
            early_repayment_demand_unjustified,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return CreditEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            credit_qualified=False,
            lender_status_invalid=False,
            interest_or_payment_terms_breached=False,
            consumer_credit_regime_applies=False,
            written_form_nullity=False,
            lender_refusal_unjustified=False,
            borrower_refusal_notice_breached=False,
            targeted_credit_control_breached=False,
            early_repayment_demand_unjustified=False,
            citizen_early_repayment_restriction_breached=False,
            requires_human_credit_assessment=True,
            reasons_ru=["Набор фактов о кредитном договоре противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как кредитный: денежные средства предоставлены заёмщику в "
            "размере и на условиях договора, а заёмщик обязуется возвратить полученную сумму, "
            "уплатить проценты и предусмотренные договором иные платежи (статья 819 ГК РФ)."
            if truth(credit_qualified)
            else "Отношения не квалифицированы как кредитный договор."
        ),
    ]
    if truth(lender_status_invalid):
        reasons_ru.append(
            "Кредитором по кредитному договору выступают банк или иная кредитная организация; "
            "предоставление средств иным лицом не образует кредитного договора "
            "(статья 819 ГК РФ)."
        )
    if truth(interest_or_payment_terms_breached):
        reasons_ru.append(
            "Нарушены условия договора о размере и порядке уплаты процентов за пользование "
            "кредитом либо иных предусмотренных договором платежей (статья 819 ГК РФ)."
        )
    if truth(consumer_credit_regime_applies):
        reasons_ru.append(
            "Заёмщиком является гражданин, а кредит предоставлен для целей, не связанных с "
            "предпринимательской деятельностью: к отношениям применяются правила о "
            "потребительском кредите (статья 819 ГК РФ)."
        )
    if truth(written_form_nullity):
        reasons_ru.append(
            "Кредитный договор должен быть заключён в письменной форме; несоблюдение письменной "
            "формы влечёт ничтожность договора (статья 820 ГК РФ)."
        )
    if truth(lender_refusal_unjustified):
        reasons_ru.append(
            "Кредитор вправе отказаться от предоставления кредита полностью или частично лишь при "
            "наличии обстоятельств, очевидно свидетельствующих о том, что сумма не будет "
            "возвращена в срок (статья 821 ГК РФ)."
        )
    if truth(borrower_refusal_notice_breached):
        reasons_ru.append(
            "Заёмщик вправе отказаться от получения кредита, уведомив кредитора до установленного "
            "договором срока предоставления, если иное не предусмотрено законом или договором "
            "(статья 821 ГК РФ)."
        )
    if truth(targeted_credit_control_breached):
        reasons_ru.append(
            "При нарушении заёмщиком обязанности целевого использования кредита кредитор вправе "
            "отказаться от дальнейшего кредитования по договору (статья 821 ГК РФ)."
        )
    if truth(early_repayment_demand_unjustified):
        reasons_ru.append(
            "Кредитор вправе требовать досрочного возврата кредита только в случаях, "
            "предусмотренных Кодексом, другими законами или договором (статья 821.1 ГК РФ)."
        )
    if truth(citizen_early_repayment_restriction_breached):
        reasons_ru.append(
            "От заёмщика-гражданина, получившего кредит для личных нужд, досрочный возврат может "
            "быть потребован только в случаях, предусмотренных законом (статья 821.1 ГК РФ)."
        )
    return CreditEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        credit_qualified=truth(credit_qualified),
        lender_status_invalid=truth(lender_status_invalid),
        interest_or_payment_terms_breached=truth(interest_or_payment_terms_breached),
        consumer_credit_regime_applies=truth(consumer_credit_regime_applies),
        written_form_nullity=truth(written_form_nullity),
        lender_refusal_unjustified=truth(lender_refusal_unjustified),
        borrower_refusal_notice_breached=truth(borrower_refusal_notice_breached),
        targeted_credit_control_breached=truth(targeted_credit_control_breached),
        early_repayment_demand_unjustified=truth(early_repayment_demand_unjustified),
        citizen_early_repayment_restriction_breached=truth(
            citizen_early_repayment_restriction_breached
        ),
        requires_human_credit_assessment=truth(requires_human_credit_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила ГК РФ о кредите и не заменяет судебную "
            "оценку.",
            "Достаточность обстоятельств, свидетельствующих о невозврате, применимость закона о "
            "потребительском кредите и основания досрочного возврата оцениваются экспертом и "
            "судом (статьи 819, 821 и 821.1 ГК РФ).",
        ],
    )
