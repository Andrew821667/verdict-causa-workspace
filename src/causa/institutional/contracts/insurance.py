from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


INSURANCE_EVIDENCE_SCHEMA_VERSION = "contracts.insurance-evidence.v0"
INSURANCE_MAPPING_VERSION = "contracts-reviewed-insurance-to-facts-v0"
INSURANCE_MODEL_VERSION = "contracts-insurance-articles-927-943-v0"


class InsuranceEvidencePredicate(str, Enum):
    # Договор страхования и страховщик (статьи 927 и 938 ГК РФ).
    INSURANCE_CONTRACT_CONCLUDED = "insurance_contract_concluded"
    INSURER_NOT_ENTITLED_TO_ACT = "insurer_not_entitled_to_act"
    # Страховой интерес (статьи 928 и 930 ГК РФ).
    INSURED_INTEREST_ABSENT_OR_UNLAWFUL = "insured_interest_absent_or_unlawful"
    # Форма договора и его существенные условия (статьи 940 и 942 ГК РФ).
    INSURANCE_WRITTEN_FORM_NOT_OBSERVED = "insurance_written_form_not_observed"
    ESSENTIAL_TERMS_NOT_AGREED = "essential_terms_not_agreed"
    INSURANCE_RULES_APPLICATION_BREACHED = "insurance_rules_application_breached"
    # Имущественное и личное страхование (статьи 929–934 ГК РФ).
    PROPERTY_INSURANCE_SCOPE_BREACHED = "property_insurance_scope_breached"
    PERSONAL_INSURANCE_SCOPE_BREACHED = "personal_insurance_scope_breached"
    # Выгодоприобретатель и обязательное страхование (статьи 935–939 ГК РФ).
    BENEFICIARY_RIGHTS_DISREGARDED = "beneficiary_rights_disregarded"
    COMPULSORY_INSURANCE_DUTY_BREACHED = "compulsory_insurance_duty_breached"


REQUIRED_INSURANCE_PREDICATES = frozenset(InsuranceEvidencePredicate)


class InsuranceEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: InsuranceEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedInsuranceEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = INSURANCE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[InsuranceEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedInsuranceEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Insurance evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Insurance evidence contains duplicate legal source refs.")
        return self


class InsuranceFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    insurance_contract_concluded: bool
    insurer_not_entitled_to_act: bool
    insured_interest_absent_or_unlawful: bool
    insurance_written_form_not_observed: bool
    essential_terms_not_agreed: bool
    insurance_rules_application_breached: bool
    property_insurance_scope_breached: bool
    personal_insurance_scope_breached: bool
    beneficiary_rights_disregarded: bool
    compulsory_insurance_duty_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "InsuranceFactSet":
        if self.insurance_rules_application_breached and not self.essential_terms_not_agreed:
            raise ValueError(
                "Нарушение применения правил страхования относится только к случаю, когда "
                "несогласование существенных условий в самом договоре установлено."
            )
        if self.insurance_written_form_not_observed and not self.insurance_contract_concluded:
            raise ValueError(
                "Несоблюдение письменной формы относится только к договору страхования."
            )
        return self


class InsuranceFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class InsuranceEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: InsuranceFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[InsuranceFactProvenance] = Field(default_factory=list)


class InsuranceConstraintSet(BaseModel):
    id: str
    model_version: str = INSURANCE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class InsuranceEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    insurance_qualified: bool
    insurer_status_invalid: bool
    insured_interest_invalid: bool
    insurance_form_void: bool
    essential_terms_duty_breached: bool
    insurance_rules_duty_breached: bool
    property_insurance_duty_breached: bool
    personal_insurance_duty_breached: bool
    beneficiary_rights_breached: bool
    compulsory_insurance_breached: bool
    requires_human_insurance_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_insurance_evidence(
    evidence: ReviewedInsuranceEvidence,
) -> InsuranceEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Insurance evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Insurance evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_INSURANCE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed insurance evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_INSURANCE_PREDICATES
    }
    return InsuranceEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=INSURANCE_MAPPING_VERSION,
        facts=InsuranceFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            InsuranceFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_INSURANCE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_insurance_constraint_set(
    mapping: InsuranceEvidenceMappingResult,
) -> InsuranceConstraintSet:
    return InsuranceConstraintSet(
        id=f"insurance-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "insurance_qualified == insurance_contract_concluded",
            "insurer_status_invalid == insurance_qualified AND insurer_not_entitled_to_act",
            "insured_interest_invalid == insurance_qualified AND insured_interest_absent_or_unlawful",
            "insurance_form_void == insurance_qualified AND insurance_written_form_not_observed",
            "essential_terms_duty_breached == insurance_qualified AND essential_terms_not_agreed",
            "insurance_rules_duty_breached == insurance_qualified AND essential_terms_not_agreed AND insurance_rules_application_breached",
            "property_insurance_duty_breached == insurance_qualified AND property_insurance_scope_breached",
            "personal_insurance_duty_breached == insurance_qualified AND personal_insurance_scope_breached",
            "beneficiary_rights_breached == insurance_qualified AND beneficiary_rights_disregarded",
            "compulsory_insurance_breached == insurance_qualified AND compulsory_insurance_duty_breached",
            "requires_human_insurance_assessment == insurer_status_invalid OR insured_interest_invalid OR insurance_form_void OR essential_terms_duty_breached OR property_insurance_duty_breached OR personal_insurance_duty_breached OR beneficiary_rights_breached OR compulsory_insurance_breached",
        ],
    )


def evaluate_insurance_constraints(
    constraint_set: InsuranceConstraintSet,
    facts: InsuranceFactSet,
) -> InsuranceEvaluation:
    variables = {field_name: Bool(field_name) for field_name in InsuranceFactSet.model_fields}
    insurance_qualified = Bool("insurance_qualified")
    insurer_status_invalid = Bool("insurer_status_invalid")
    insured_interest_invalid = Bool("insured_interest_invalid")
    insurance_form_void = Bool("insurance_form_void")
    essential_terms_duty_breached = Bool("essential_terms_duty_breached")
    insurance_rules_duty_breached = Bool("insurance_rules_duty_breached")
    property_insurance_duty_breached = Bool("property_insurance_duty_breached")
    personal_insurance_duty_breached = Bool("personal_insurance_duty_breached")
    beneficiary_rights_breached = Bool("beneficiary_rights_breached")
    compulsory_insurance_breached = Bool("compulsory_insurance_breached")
    requires_human_insurance_assessment = Bool("requires_human_insurance_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(insurance_qualified == variables["insurance_contract_concluded"])
    solver.add(
        insurer_status_invalid == And(insurance_qualified, variables["insurer_not_entitled_to_act"])
    )
    solver.add(
        insured_interest_invalid
        == And(insurance_qualified, variables["insured_interest_absent_or_unlawful"])
    )
    solver.add(
        insurance_form_void
        == And(insurance_qualified, variables["insurance_written_form_not_observed"])
    )
    solver.add(
        essential_terms_duty_breached
        == And(insurance_qualified, variables["essential_terms_not_agreed"])
    )
    solver.add(
        insurance_rules_duty_breached
        == And(
            insurance_qualified,
            variables["essential_terms_not_agreed"],
            variables["insurance_rules_application_breached"],
        )
    )
    solver.add(
        property_insurance_duty_breached
        == And(insurance_qualified, variables["property_insurance_scope_breached"])
    )
    solver.add(
        personal_insurance_duty_breached
        == And(insurance_qualified, variables["personal_insurance_scope_breached"])
    )
    solver.add(
        beneficiary_rights_breached
        == And(insurance_qualified, variables["beneficiary_rights_disregarded"])
    )
    solver.add(
        compulsory_insurance_breached
        == And(insurance_qualified, variables["compulsory_insurance_duty_breached"])
    )
    solver.add(
        requires_human_insurance_assessment
        == Or(
            insurer_status_invalid,
            insured_interest_invalid,
            insurance_form_void,
            essential_terms_duty_breached,
            property_insurance_duty_breached,
            personal_insurance_duty_breached,
            beneficiary_rights_breached,
            compulsory_insurance_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return InsuranceEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            insurance_qualified=False,
            insurer_status_invalid=False,
            insured_interest_invalid=False,
            insurance_form_void=False,
            essential_terms_duty_breached=False,
            insurance_rules_duty_breached=False,
            property_insurance_duty_breached=False,
            personal_insurance_duty_breached=False,
            beneficiary_rights_breached=False,
            compulsory_insurance_breached=False,
            requires_human_insurance_assessment=True,
            reasons_ru=["Набор фактов о страховании противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор страхования: страхование имущества и иных "
            "имущественных интересов либо страхование жизни, здоровья и других личных интересов "
            "осуществляется на основании договора имущественного или личного страхования "
            "(статьи 927, 929 и 934 ГК РФ)."
            if truth(insurance_qualified)
            else "Отношения не квалифицированы как договор страхования."
        ),
    ]
    if truth(insurer_status_invalid):
        reasons_ru.append(
            "В качестве страховщиков могут выступать юридические лица, имеющие разрешения "
            "(лицензии) на осуществление страхования соответствующего вида "
            "(статья 938 ГК РФ)."
        )
    if truth(insured_interest_invalid):
        reasons_ru.append(
            "Страхование противоправных интересов, а также убытков от участия в играх и расходов "
            "по освобождению заложников не допускается; договор страхования имущества в пользу "
            "лица, не имеющего интереса в сохранении застрахованного имущества, недействителен "
            "(статьи 928 и 930 ГК РФ)."
        )
    if truth(insurance_form_void):
        reasons_ru.append(
            "Договор страхования должен быть заключён в письменной форме; несоблюдение письменной "
            "формы влечёт недействительность договора, кроме договора обязательного "
            "государственного страхования (статья 940 ГК РФ)."
        )
    if truth(essential_terms_duty_breached):
        reasons_ru.append(
            "Между страхователем и страховщиком должно быть достигнуто соглашение об "
            "определённом имуществе либо ином имущественном интересе или о застрахованном лице, "
            "о характере страхового случая, о размере страховой суммы и о сроке действия договора "
            "(статья 942 ГК РФ)."
        )
    if truth(insurance_rules_duty_breached):
        reasons_ru.append(
            "Условия договора страхования могут быть определены в правилах страхования; они "
            "обязательны для страхователя, если в договоре прямо указано на их применение и сами "
            "правила изложены в договоре либо приложены к нему (статья 943 ГК РФ)."
        )
    if truth(property_insurance_duty_breached):
        reasons_ru.append(
            "По договору имущественного страхования могут быть застрахованы риск утраты, "
            "недостачи или повреждения имущества, риск ответственности по обязательствам из "
            "причинения вреда или по договору и предпринимательский риск в пределах, "
            "предусмотренных законом (статьи 929 и 931–933 ГК РФ)."
        )
    if truth(personal_insurance_duty_breached):
        reasons_ru.append(
            "По договору личного страхования страховщик обязуется выплатить страховую сумму в "
            "случае причинения вреда жизни или здоровью застрахованного лица, достижения им "
            "определённого возраста или наступления иного предусмотренного события "
            "(статья 934 ГК РФ)."
        )
    if truth(beneficiary_rights_breached):
        reasons_ru.append(
            "Права и обязанности выгодоприобретателя, освобождение страховщика от исполнения и "
            "порядок замены выгодоприобретателя определяются правилами статей 939 и 956 ГК РФ."
        )
    if truth(compulsory_insurance_breached):
        reasons_ru.append(
            "Обязанность страховать жизнь, здоровье или имущество других лиц либо свою "
            "гражданскую ответственность может быть возложена законом; последствия неисполнения "
            "этой обязанности определяются статьями 935–937 ГК РФ."
        )
    return InsuranceEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        insurance_qualified=truth(insurance_qualified),
        insurer_status_invalid=truth(insurer_status_invalid),
        insured_interest_invalid=truth(insured_interest_invalid),
        insurance_form_void=truth(insurance_form_void),
        essential_terms_duty_breached=truth(essential_terms_duty_breached),
        insurance_rules_duty_breached=truth(insurance_rules_duty_breached),
        property_insurance_duty_breached=truth(property_insurance_duty_breached),
        personal_insurance_duty_breached=truth(personal_insurance_duty_breached),
        beneficiary_rights_breached=truth(beneficiary_rights_breached),
        compulsory_insurance_breached=truth(compulsory_insurance_breached),
        requires_human_insurance_assessment=truth(requires_human_insurance_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только общие положения о страховании и договоре страхования и не "
            "заменяет судебную оценку.",
            "Наличие страхового интереса, характер страхового случая и содержание правил "
            "страхования оцениваются экспертом и судом (статьи 930, 942 и 943 ГК РФ).",
        ],
    )
