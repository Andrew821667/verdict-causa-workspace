from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


LOAN_EVIDENCE_SCHEMA_VERSION = "contracts.loan-evidence.v0"
LOAN_MAPPING_VERSION = "contracts-reviewed-loan-to-facts-v0"
LOAN_MODEL_VERSION = "contracts-loan-articles-807-818-v0"


class LoanEvidencePredicate(str, Enum):
    # Понятие займа и форма договора (статьи 807 и 808 ГК РФ).
    MONEY_OR_FUNGIBLES_TRANSFERRED_FOR_RETURN = "money_or_fungibles_transferred_for_return"
    WRITTEN_FORM_REQUIRED_BUT_MISSING = "written_form_required_but_missing"
    # Проценты по договору займа (статья 809 ГК РФ).
    INTEREST_TERMS_NOT_COMPLIANT = "interest_terms_not_compliant"
    USURIOUS_INTEREST_RATE = "usurious_interest_rate"
    # Возврат суммы займа и просрочка (статьи 810 и 811 ГК РФ).
    REPAYMENT_DEADLINE_BREACHED = "repayment_deadline_breached"
    LATE_PAYMENT_INTEREST_NOT_ACCRUED = "late_payment_interest_not_accrued"
    # Оспаривание по безденежности и утрата обеспечения (статьи 812 и 813 ГК РФ).
    LOAN_CHALLENGED_AS_UNFUNDED = "loan_challenged_as_unfunded"
    SECURITY_LOST_OR_DETERIORATED = "security_lost_or_deteriorated"
    # Целевой заём и новация долга (статьи 814 и 818 ГК РФ).
    TARGETED_LOAN_MISUSED_OR_CONTROL_OBSTRUCTED = "targeted_loan_misused_or_control_obstructed"
    NOVATION_INTO_LOAN_REQUIREMENTS_BREACHED = "novation_into_loan_requirements_breached"


REQUIRED_LOAN_PREDICATES = frozenset(LoanEvidencePredicate)


class LoanEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: LoanEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedLoanEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = LOAN_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[LoanEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedLoanEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Loan evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Loan evidence contains duplicate legal source refs.")
        return self


class LoanFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    money_or_fungibles_transferred_for_return: bool
    written_form_required_but_missing: bool
    interest_terms_not_compliant: bool
    usurious_interest_rate: bool
    repayment_deadline_breached: bool
    late_payment_interest_not_accrued: bool
    loan_challenged_as_unfunded: bool
    security_lost_or_deteriorated: bool
    targeted_loan_misused_or_control_obstructed: bool
    novation_into_loan_requirements_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "LoanFactSet":
        if self.late_payment_interest_not_accrued and not self.repayment_deadline_breached:
            raise ValueError(
                "Неначисление процентов за просрочку относится только к случаю, когда нарушение "
                "срока возврата суммы займа установлено."
            )
        if self.written_form_required_but_missing and not (
            self.money_or_fungibles_transferred_for_return
        ):
            raise ValueError("Несоблюдение письменной формы относится только к договору займа.")
        return self


class LoanFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class LoanEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: LoanFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[LoanFactProvenance] = Field(default_factory=list)


class LoanConstraintSet(BaseModel):
    id: str
    model_version: str = LOAN_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class LoanEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    loan_qualified: bool
    written_form_requirement_breached: bool
    interest_rules_breached: bool
    usurious_interest_reducible: bool
    repayment_duty_breached: bool
    late_payment_interest_due: bool
    unfunded_loan_challenge_available: bool
    early_repayment_demand_available: bool
    targeted_loan_control_breached: bool
    novation_requirements_breached: bool
    requires_human_loan_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_loan_evidence(evidence: ReviewedLoanEvidence) -> LoanEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Loan evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Loan evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(predicate.value for predicate in REQUIRED_LOAN_PREDICATES - assertions.keys())
    if missing:
        raise ValueError(
            "Reviewed loan evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_LOAN_PREDICATES
    }
    return LoanEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=LOAN_MAPPING_VERSION,
        facts=LoanFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            LoanFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_LOAN_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_loan_constraint_set(mapping: LoanEvidenceMappingResult) -> LoanConstraintSet:
    return LoanConstraintSet(
        id=f"loan-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "loan_qualified == money_or_fungibles_transferred_for_return",
            "written_form_requirement_breached == loan_qualified AND written_form_required_but_missing",
            "interest_rules_breached == loan_qualified AND interest_terms_not_compliant",
            "usurious_interest_reducible == loan_qualified AND usurious_interest_rate",
            "repayment_duty_breached == loan_qualified AND repayment_deadline_breached",
            "late_payment_interest_due == loan_qualified AND repayment_deadline_breached AND late_payment_interest_not_accrued",
            "unfunded_loan_challenge_available == loan_qualified AND loan_challenged_as_unfunded",
            "early_repayment_demand_available == loan_qualified AND security_lost_or_deteriorated",
            "targeted_loan_control_breached == loan_qualified AND targeted_loan_misused_or_control_obstructed",
            "novation_requirements_breached == loan_qualified AND novation_into_loan_requirements_breached",
            "requires_human_loan_assessment == written_form_requirement_breached OR interest_rules_breached OR usurious_interest_reducible OR repayment_duty_breached OR unfunded_loan_challenge_available OR early_repayment_demand_available OR targeted_loan_control_breached OR novation_requirements_breached",
        ],
    )


def evaluate_loan_constraints(
    constraint_set: LoanConstraintSet,
    facts: LoanFactSet,
) -> LoanEvaluation:
    variables = {field_name: Bool(field_name) for field_name in LoanFactSet.model_fields}
    loan_qualified = Bool("loan_qualified")
    written_form_requirement_breached = Bool("written_form_requirement_breached")
    interest_rules_breached = Bool("interest_rules_breached")
    usurious_interest_reducible = Bool("usurious_interest_reducible")
    repayment_duty_breached = Bool("repayment_duty_breached")
    late_payment_interest_due = Bool("late_payment_interest_due")
    unfunded_loan_challenge_available = Bool("unfunded_loan_challenge_available")
    early_repayment_demand_available = Bool("early_repayment_demand_available")
    targeted_loan_control_breached = Bool("targeted_loan_control_breached")
    novation_requirements_breached = Bool("novation_requirements_breached")
    requires_human_loan_assessment = Bool("requires_human_loan_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(loan_qualified == variables["money_or_fungibles_transferred_for_return"])
    solver.add(
        written_form_requirement_breached
        == And(loan_qualified, variables["written_form_required_but_missing"])
    )
    solver.add(
        interest_rules_breached == And(loan_qualified, variables["interest_terms_not_compliant"])
    )
    solver.add(
        usurious_interest_reducible == And(loan_qualified, variables["usurious_interest_rate"])
    )
    solver.add(
        repayment_duty_breached == And(loan_qualified, variables["repayment_deadline_breached"])
    )
    solver.add(
        late_payment_interest_due
        == And(
            loan_qualified,
            variables["repayment_deadline_breached"],
            variables["late_payment_interest_not_accrued"],
        )
    )
    solver.add(
        unfunded_loan_challenge_available
        == And(loan_qualified, variables["loan_challenged_as_unfunded"])
    )
    solver.add(
        early_repayment_demand_available
        == And(loan_qualified, variables["security_lost_or_deteriorated"])
    )
    solver.add(
        targeted_loan_control_breached
        == And(loan_qualified, variables["targeted_loan_misused_or_control_obstructed"])
    )
    solver.add(
        novation_requirements_breached
        == And(loan_qualified, variables["novation_into_loan_requirements_breached"])
    )
    solver.add(
        requires_human_loan_assessment
        == Or(
            written_form_requirement_breached,
            interest_rules_breached,
            usurious_interest_reducible,
            repayment_duty_breached,
            unfunded_loan_challenge_available,
            early_repayment_demand_available,
            targeted_loan_control_breached,
            novation_requirements_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return LoanEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            loan_qualified=False,
            written_form_requirement_breached=False,
            interest_rules_breached=False,
            usurious_interest_reducible=False,
            repayment_duty_breached=False,
            late_payment_interest_due=False,
            unfunded_loan_challenge_available=False,
            early_repayment_demand_available=False,
            targeted_loan_control_breached=False,
            novation_requirements_breached=False,
            requires_human_loan_assessment=True,
            reasons_ru=["Набор фактов о займе противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как заём: займодавец передаёт в собственность заёмщику "
            "деньги или другие вещи, определённые родовыми признаками, а заёмщик обязуется "
            "возвратить такую же сумму денег или равное количество полученных вещей того же рода "
            "и качества (статья 807 ГК РФ)."
            if truth(loan_qualified)
            else "Отношения не квалифицированы как договор займа."
        ),
    ]
    if truth(written_form_requirement_breached):
        reasons_ru.append(
            "Договор займа между гражданами заключается в письменной форме, если его сумма "
            "превышает установленный законом предел, а если займодавцем является юридическое "
            "лицо — независимо от суммы (статья 808 ГК РФ)."
        )
    if truth(interest_rules_breached):
        reasons_ru.append(
            "Проценты за пользование займом начислены с нарушением правил об их размере и порядке "
            "уплаты либо вопреки установленным законом случаям беспроцентного займа "
            "(статья 809 ГК РФ)."
        )
    if truth(usurious_interest_reducible):
        reasons_ru.append(
            "Размер процентов по договору займа с гражданином в два и более раза превышает "
            "обычно взимаемые в подобных случаях проценты и является чрезмерно обременительным; "
            "суд вправе уменьшить его до обычно взимаемого размера (статья 809 ГК РФ)."
        )
    if truth(repayment_duty_breached):
        reasons_ru.append(
            "Заёмщик обязан возвратить займодавцу полученную сумму займа в срок и в порядке, "
            "которые предусмотрены договором (статья 810 ГК РФ)."
        )
    if truth(late_payment_interest_due):
        reasons_ru.append(
            "При нарушении срока возврата на невозвращённую сумму подлежат уплате проценты, "
            "предусмотренные правилами об ответственности за неисполнение денежного "
            "обязательства, независимо от процентов за пользование займом (статья 811 ГК РФ)."
        )
    if truth(unfunded_loan_challenge_available):
        reasons_ru.append(
            "Заёмщик вправе оспаривать договор займа по безденежности, доказывая, что деньги или "
            "другие вещи в действительности не получены им или получены в меньшем количестве "
            "(статья 812 ГК РФ)."
        )
    if truth(early_repayment_demand_available):
        reasons_ru.append(
            "При невыполнении заёмщиком обязанностей по обеспечению возврата займа либо при "
            "утрате обеспечения по обстоятельствам, за которые займодавец не отвечает, займодавец "
            "вправе потребовать досрочного возврата займа и уплаты причитающихся процентов "
            "(статья 813 ГК РФ)."
        )
    if truth(targeted_loan_control_breached):
        reasons_ru.append(
            "Целевой заём использован не в соответствии с определённой договором целью либо "
            "заёмщик не обеспечил займодавцу возможность контроля за использованием суммы займа "
            "(статья 814 ГК РФ)."
        )
    if truth(novation_requirements_breached):
        reasons_ru.append(
            "Замена долга, возникшего из купли-продажи, аренды или иного основания, заёмным "
            "обязательством совершается с соблюдением требований о новации и формы договора "
            "займа (статья 818 ГК РФ)."
        )
    return LoanEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        loan_qualified=truth(loan_qualified),
        written_form_requirement_breached=truth(written_form_requirement_breached),
        interest_rules_breached=truth(interest_rules_breached),
        usurious_interest_reducible=truth(usurious_interest_reducible),
        repayment_duty_breached=truth(repayment_duty_breached),
        late_payment_interest_due=truth(late_payment_interest_due),
        unfunded_loan_challenge_available=truth(unfunded_loan_challenge_available),
        early_repayment_demand_available=truth(early_repayment_demand_available),
        targeted_loan_control_breached=truth(targeted_loan_control_breached),
        novation_requirements_breached=truth(novation_requirements_breached),
        requires_human_loan_assessment=truth(requires_human_loan_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о займе и не заменяет судебную оценку.",
            "Обычно взимаемый размер процентов, обременительность условий и достаточность "
            "доказательств безденежности оцениваются экспертом и судом (статьи 809 и 812 "
            "ГК РФ).",
        ],
    )
