from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


TRUST_MANAGEMENT_EVIDENCE_SCHEMA_VERSION = "contracts.trust-management-evidence.v0"
TRUST_MANAGEMENT_MAPPING_VERSION = "contracts-reviewed-trust-management-to-facts-v0"
TRUST_MANAGEMENT_MODEL_VERSION = "contracts-trust-management-articles-1012-1026-v0"


class TrustManagementEvidencePredicate(str, Enum):
    # Договор доверительного управления и объект управления (статьи 1012 и 1013 ГК РФ).
    TRUST_MANAGEMENT_CONTRACT_CONCLUDED = "trust_management_contract_concluded"
    TRUST_PROPERTY_SCOPE_BREACHED = "trust_property_scope_breached"
    # Доверительный управляющий (статья 1015 ГК РФ).
    TRUSTEE_STATUS_INVALID = "trustee_status_invalid"
    # Существенные условия и форма договора (статьи 1016 и 1017 ГК РФ).
    ESSENTIAL_TERMS_OR_FORM_BREACHED = "essential_terms_or_form_breached"
    FORM_INVALIDITY_NOT_APPLIED = "form_invalidity_not_applied"
    # Обособление имущества и передача обременённого имущества (статьи 1018 и 1019 ГК РФ).
    PROPERTY_SEPARATION_BREACHED = "property_separation_breached"
    ENCUMBERED_PROPERTY_NOTICE_BREACHED = "encumbered_property_notice_breached"
    # Права, обязанности и ответственность управляющего (статьи 1020–1022 ГК РФ).
    TRUSTEE_RIGHTS_AND_REPORT_BREACHED = "trustee_rights_and_report_breached"
    TRUSTEE_LIABILITY_RULES_BREACHED = "trustee_liability_rules_breached"
    # Вознаграждение и прекращение договора (статьи 1023, 1024 и 1026 ГК РФ).
    REMUNERATION_OR_TERMINATION_RULES_BREACHED = "remuneration_or_termination_rules_breached"


REQUIRED_TRUST_MANAGEMENT_PREDICATES = frozenset(TrustManagementEvidencePredicate)


class TrustManagementEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: TrustManagementEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedTrustManagementEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = TRUST_MANAGEMENT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[TrustManagementEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedTrustManagementEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Trust-management evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Trust-management evidence contains duplicate legal source refs.")
        return self


class TrustManagementFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    trust_management_contract_concluded: bool
    trust_property_scope_breached: bool
    trustee_status_invalid: bool
    essential_terms_or_form_breached: bool
    form_invalidity_not_applied: bool
    property_separation_breached: bool
    encumbered_property_notice_breached: bool
    trustee_rights_and_report_breached: bool
    trustee_liability_rules_breached: bool
    remuneration_or_termination_rules_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "TrustManagementFactSet":
        if self.form_invalidity_not_applied and not self.essential_terms_or_form_breached:
            raise ValueError(
                "Неприменение последствий несоблюдения формы относится только к случаю, когда "
                "нарушение существенных условий или формы договора установлено."
            )
        if self.trust_property_scope_breached and not self.trust_management_contract_concluded:
            raise ValueError(
                "Нарушение состава объекта доверительного управления относится только к договору "
                "доверительного управления имуществом."
            )
        return self


class TrustManagementFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class TrustManagementEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: TrustManagementFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[TrustManagementFactProvenance] = Field(default_factory=list)


class TrustManagementConstraintSet(BaseModel):
    id: str
    model_version: str = TRUST_MANAGEMENT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class TrustManagementEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    trust_management_qualified: bool
    property_scope_duty_breached: bool
    trustee_status_duty_breached: bool
    essential_terms_duty_breached: bool
    form_invalidity_breached: bool
    property_separation_duty_breached: bool
    encumbered_property_duty_breached: bool
    trustee_rights_duty_breached: bool
    trustee_liability_duty_breached: bool
    remuneration_and_termination_duty_breached: bool
    requires_human_trust_management_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_trust_management_evidence(
    evidence: ReviewedTrustManagementEvidence,
) -> TrustManagementEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Trust-management evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Trust-management evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_TRUST_MANAGEMENT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed trust-management evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_TRUST_MANAGEMENT_PREDICATES
    }
    return TrustManagementEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=TRUST_MANAGEMENT_MAPPING_VERSION,
        facts=TrustManagementFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            TrustManagementFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_TRUST_MANAGEMENT_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_trust_management_constraint_set(
    mapping: TrustManagementEvidenceMappingResult,
) -> TrustManagementConstraintSet:
    return TrustManagementConstraintSet(
        id=f"trust-management-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "trust_management_qualified == trust_management_contract_concluded",
            "property_scope_duty_breached == trust_management_qualified AND trust_property_scope_breached",
            "trustee_status_duty_breached == trust_management_qualified AND trustee_status_invalid",
            "essential_terms_duty_breached == trust_management_qualified AND essential_terms_or_form_breached",
            "form_invalidity_breached == trust_management_qualified AND essential_terms_or_form_breached AND form_invalidity_not_applied",
            "property_separation_duty_breached == trust_management_qualified AND property_separation_breached",
            "encumbered_property_duty_breached == trust_management_qualified AND encumbered_property_notice_breached",
            "trustee_rights_duty_breached == trust_management_qualified AND trustee_rights_and_report_breached",
            "trustee_liability_duty_breached == trust_management_qualified AND trustee_liability_rules_breached",
            "remuneration_and_termination_duty_breached == trust_management_qualified AND remuneration_or_termination_rules_breached",
            "requires_human_trust_management_assessment == property_scope_duty_breached OR trustee_status_duty_breached OR essential_terms_duty_breached OR property_separation_duty_breached OR encumbered_property_duty_breached OR trustee_rights_duty_breached OR trustee_liability_duty_breached OR remuneration_and_termination_duty_breached",
        ],
    )


def evaluate_trust_management_constraints(
    constraint_set: TrustManagementConstraintSet,
    facts: TrustManagementFactSet,
) -> TrustManagementEvaluation:
    variables = {field_name: Bool(field_name) for field_name in TrustManagementFactSet.model_fields}
    trust_management_qualified = Bool("trust_management_qualified")
    property_scope_duty_breached = Bool("property_scope_duty_breached")
    trustee_status_duty_breached = Bool("trustee_status_duty_breached")
    essential_terms_duty_breached = Bool("essential_terms_duty_breached")
    form_invalidity_breached = Bool("form_invalidity_breached")
    property_separation_duty_breached = Bool("property_separation_duty_breached")
    encumbered_property_duty_breached = Bool("encumbered_property_duty_breached")
    trustee_rights_duty_breached = Bool("trustee_rights_duty_breached")
    trustee_liability_duty_breached = Bool("trustee_liability_duty_breached")
    remuneration_and_termination_duty_breached = Bool("remuneration_and_termination_duty_breached")
    requires_human_trust_management_assessment = Bool("requires_human_trust_management_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(trust_management_qualified == variables["trust_management_contract_concluded"])
    solver.add(
        property_scope_duty_breached
        == And(trust_management_qualified, variables["trust_property_scope_breached"])
    )
    solver.add(
        trustee_status_duty_breached
        == And(trust_management_qualified, variables["trustee_status_invalid"])
    )
    solver.add(
        essential_terms_duty_breached
        == And(trust_management_qualified, variables["essential_terms_or_form_breached"])
    )
    solver.add(
        form_invalidity_breached
        == And(
            trust_management_qualified,
            variables["essential_terms_or_form_breached"],
            variables["form_invalidity_not_applied"],
        )
    )
    solver.add(
        property_separation_duty_breached
        == And(trust_management_qualified, variables["property_separation_breached"])
    )
    solver.add(
        encumbered_property_duty_breached
        == And(trust_management_qualified, variables["encumbered_property_notice_breached"])
    )
    solver.add(
        trustee_rights_duty_breached
        == And(trust_management_qualified, variables["trustee_rights_and_report_breached"])
    )
    solver.add(
        trustee_liability_duty_breached
        == And(trust_management_qualified, variables["trustee_liability_rules_breached"])
    )
    solver.add(
        remuneration_and_termination_duty_breached
        == And(
            trust_management_qualified,
            variables["remuneration_or_termination_rules_breached"],
        )
    )
    solver.add(
        requires_human_trust_management_assessment
        == Or(
            property_scope_duty_breached,
            trustee_status_duty_breached,
            essential_terms_duty_breached,
            property_separation_duty_breached,
            encumbered_property_duty_breached,
            trustee_rights_duty_breached,
            trustee_liability_duty_breached,
            remuneration_and_termination_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return TrustManagementEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            trust_management_qualified=False,
            property_scope_duty_breached=False,
            trustee_status_duty_breached=False,
            essential_terms_duty_breached=False,
            form_invalidity_breached=False,
            property_separation_duty_breached=False,
            encumbered_property_duty_breached=False,
            trustee_rights_duty_breached=False,
            trustee_liability_duty_breached=False,
            remuneration_and_termination_duty_breached=False,
            requires_human_trust_management_assessment=True,
            reasons_ru=["Набор фактов о доверительном управлении имуществом противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор доверительного управления имуществом: учредитель "
            "управления передаёт доверительному управляющему на определённый срок имущество в "
            "доверительное управление, а управляющий обязуется осуществлять управление этим "
            "имуществом в интересах учредителя управления или указанного им лица "
            "(статья 1012 ГК РФ)."
            if truth(trust_management_qualified)
            else "Отношения не квалифицированы как договор доверительного управления имуществом."
        ),
    ]
    if truth(property_scope_duty_breached):
        reasons_ru.append(
            "Объектами доверительного управления могут быть предприятия и другие имущественные "
            "комплексы, отдельные объекты недвижимости, ценные бумаги, права, удостоверенные "
            "бездокументарными ценными бумагами, исключительные права и иное имущество; "
            "имущество, находящееся в хозяйственном ведении или оперативном управлении, "
            "объектом управления быть не может (статья 1013 ГК РФ)."
        )
    if truth(trustee_status_duty_breached):
        reasons_ru.append(
            "Доверительным управляющим может быть индивидуальный предприниматель или "
            "коммерческая организация, за исключением унитарного предприятия; имущество не "
            "подлежит передаче в доверительное управление государственному органу или органу "
            "местного самоуправления (статья 1015 ГК РФ)."
        )
    if truth(essential_terms_duty_breached):
        reasons_ru.append(
            "В договоре доверительного управления должны быть указаны состав передаваемого "
            "имущества, наименование учредителя управления или выгодоприобретателя, размер и "
            "форма вознаграждения управляющего и срок действия договора; договор заключается в "
            "письменной форме, а передача недвижимости подлежит государственной регистрации "
            "(статьи 1016 и 1017 ГК РФ)."
        )
    if truth(form_invalidity_breached):
        reasons_ru.append(
            "Несоблюдение формы договора доверительного управления имуществом или требования о "
            "государственной регистрации передачи недвижимого имущества влечёт "
            "недействительность договора (статья 1017 ГК РФ)."
        )
    if truth(property_separation_duty_breached):
        reasons_ru.append(
            "Имущество, переданное в доверительное управление, обособляется от другого имущества "
            "учредителя управления и от имущества управляющего, отражается у управляющего на "
            "отдельном балансе, и по нему ведётся самостоятельный учёт с открытием отдельного "
            "банковского счёта (статья 1018 ГК РФ)."
        )
    if truth(encumbered_property_duty_breached):
        reasons_ru.append(
            "Передача в доверительное управление имущества, обременённого залогом, допускается с "
            "предупреждением управляющего об обременении; при отсутствии такого предупреждения "
            "управляющий вправе требовать расторжения договора и уплаты вознаграждения "
            "(статья 1019 ГК РФ)."
        )
    if truth(trustee_rights_duty_breached):
        reasons_ru.append(
            "Доверительный управляющий осуществляет в пределах, предусмотренных законом и "
            "договором, правомочия собственника, обязан представлять учредителю управления и "
            "выгодоприобретателю отчёт о своей деятельности и по общему правилу осуществляет "
            "управление лично (статьи 1020 и 1021 ГК РФ)."
        )
    if truth(trustee_liability_duty_breached):
        reasons_ru.append(
            "Доверительный управляющий, не проявивший при управлении имуществом должной "
            "заботливости об интересах выгодоприобретателя или учредителя управления, возмещает "
            "упущенную выгоду и убытки, если не докажет наличие предусмотренных законом "
            "обстоятельств (статья 1022 ГК РФ)."
        )
    if truth(remuneration_and_termination_duty_breached):
        reasons_ru.append(
            "Доверительный управляющий имеет право на вознаграждение и возмещение необходимых "
            "расходов за счёт доходов от использования имущества, а прекращение договора "
            "доверительного управления подчиняется правилам статей 1023, 1024 и 1026 ГК РФ."
        )
    return TrustManagementEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        trust_management_qualified=truth(trust_management_qualified),
        property_scope_duty_breached=truth(property_scope_duty_breached),
        trustee_status_duty_breached=truth(trustee_status_duty_breached),
        essential_terms_duty_breached=truth(essential_terms_duty_breached),
        form_invalidity_breached=truth(form_invalidity_breached),
        property_separation_duty_breached=truth(property_separation_duty_breached),
        encumbered_property_duty_breached=truth(encumbered_property_duty_breached),
        trustee_rights_duty_breached=truth(trustee_rights_duty_breached),
        trustee_liability_duty_breached=truth(trustee_liability_duty_breached),
        remuneration_and_termination_duty_breached=truth(
            remuneration_and_termination_duty_breached
        ),
        requires_human_trust_management_assessment=truth(
            requires_human_trust_management_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о доверительном управлении имуществом и "
            "не заменяет судебную оценку.",
            "Состав переданного имущества, должная заботливость управляющего и обоснованность "
            "расходов оцениваются экспертом и судом (статьи 1013, 1022 и 1023 ГК РФ).",
        ],
    )
