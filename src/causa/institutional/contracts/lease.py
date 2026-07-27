from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


LEASE_EVIDENCE_SCHEMA_VERSION = "contracts.lease-evidence.v0"
LEASE_MAPPING_VERSION = "contracts-reviewed-lease-to-facts-v0"
LEASE_MODEL_VERSION = "contracts-lease-articles-606-625-v0"


class LeaseEvidencePredicate(str, Enum):
    # Понятие и объекты аренды (статьи 606 и 607 ГК РФ).
    PROPERTY_LEASED_FOR_TEMPORARY_USE = "property_leased_for_temporary_use"
    LEASE_OBJECT_NOT_IDENTIFIABLE = "lease_object_not_identifiable"
    # Форма, срок и предоставление имущества (статьи 609, 611, 612 и 613 ГК РФ).
    LEASE_FORM_OR_REGISTRATION_MISSING = "lease_form_or_registration_missing"
    LEASED_PROPERTY_DEFECTIVE_OR_INCOMPLETE = "leased_property_defective_or_incomplete"
    THIRD_PARTY_RIGHTS_NOT_DISCLOSED = "third_party_rights_not_disclosed"
    # Пользование, содержание и расторжение (статьи 615, 616 и 619 ГК РФ).
    SUBLEASE_WITHOUT_LESSOR_CONSENT = "sublease_without_lessor_consent"
    LESSOR_FAILED_CAPITAL_REPAIR = "lessor_failed_capital_repair"
    TENANT_MATERIALLY_BREACHED = "tenant_materially_breached"
    # Преимущественное право и улучшения (статьи 621 и 623 ГК РФ).
    TENANT_SEEKS_RENEWAL_WITH_PRIORITY = "tenant_seeks_renewal_with_priority"
    INSEPARABLE_IMPROVEMENTS_WITH_CONSENT = "inseparable_improvements_with_consent"


REQUIRED_LEASE_PREDICATES = frozenset(LeaseEvidencePredicate)


class LeaseEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: LeaseEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedLeaseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = LEASE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[LeaseEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedLeaseEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Lease evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Lease evidence contains duplicate legal source refs.")
        return self


class LeaseFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    property_leased_for_temporary_use: bool
    lease_object_not_identifiable: bool
    lease_form_or_registration_missing: bool
    leased_property_defective_or_incomplete: bool
    third_party_rights_not_disclosed: bool
    sublease_without_lessor_consent: bool
    lessor_failed_capital_repair: bool
    tenant_materially_breached: bool
    tenant_seeks_renewal_with_priority: bool
    inseparable_improvements_with_consent: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "LeaseFactSet":
        if self.tenant_seeks_renewal_with_priority and self.tenant_materially_breached:
            raise ValueError(
                "Существенное нарушение обязанностей арендатором исключает преимущественное "
                "право на заключение договора на новый срок."
            )
        if self.tenant_seeks_renewal_with_priority and self.lease_object_not_identifiable:
            raise ValueError(
                "Преимущественное право на новый срок предполагает согласованный предмет "
                "договора аренды."
            )
        if self.inseparable_improvements_with_consent and self.lease_object_not_identifiable:
            raise ValueError(
                "Возмещение стоимости неотделимых улучшений предполагает согласованный предмет "
                "договора аренды."
            )
        return self


class LeaseFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class LeaseEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: LeaseFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[LeaseFactProvenance] = Field(default_factory=list)


class LeaseConstraintSet(BaseModel):
    id: str
    model_version: str = LEASE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class LeaseEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    lease_qualified: bool
    object_terms_not_agreed: bool
    form_requirement_violated: bool
    lessor_liable_for_defects: bool
    undisclosed_third_party_rights: bool
    unauthorized_sublease: bool
    lessor_neglected_capital_repair: bool
    lessor_may_terminate_for_breach: bool
    tenant_has_priority_renewal: bool
    tenant_improvement_compensation_due: bool
    requires_human_lease_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_lease_evidence(
    evidence: ReviewedLeaseEvidence,
) -> LeaseEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Lease evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Lease evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(predicate.value for predicate in REQUIRED_LEASE_PREDICATES - assertions.keys())
    if missing:
        raise ValueError(
            "Reviewed lease evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_LEASE_PREDICATES
    }
    return LeaseEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=LEASE_MAPPING_VERSION,
        facts=LeaseFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            LeaseFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_LEASE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_lease_constraint_set(
    mapping: LeaseEvidenceMappingResult,
) -> LeaseConstraintSet:
    return LeaseConstraintSet(
        id=f"lease-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "lease_qualified == property_leased_for_temporary_use",
            "object_terms_not_agreed == lease_qualified AND lease_object_not_identifiable",
            "form_requirement_violated == lease_qualified AND lease_form_or_registration_missing",
            "lessor_liable_for_defects == lease_qualified AND leased_property_defective_or_incomplete",
            "undisclosed_third_party_rights == lease_qualified AND third_party_rights_not_disclosed",
            "unauthorized_sublease == lease_qualified AND sublease_without_lessor_consent",
            "lessor_neglected_capital_repair == lease_qualified AND lessor_failed_capital_repair",
            "lessor_may_terminate_for_breach == lease_qualified AND tenant_materially_breached",
            "tenant_has_priority_renewal == lease_qualified AND tenant_seeks_renewal_with_priority",
            "tenant_improvement_compensation_due == lease_qualified AND inseparable_improvements_with_consent",
            "requires_human_lease_assessment == object_terms_not_agreed OR form_requirement_violated OR lessor_liable_for_defects OR undisclosed_third_party_rights OR unauthorized_sublease OR lessor_neglected_capital_repair OR lessor_may_terminate_for_breach OR tenant_improvement_compensation_due",
        ],
    )


def evaluate_lease_constraints(
    constraint_set: LeaseConstraintSet,
    facts: LeaseFactSet,
) -> LeaseEvaluation:
    variables = {field_name: Bool(field_name) for field_name in LeaseFactSet.model_fields}
    lease_qualified = Bool("lease_qualified")
    object_terms_not_agreed = Bool("object_terms_not_agreed")
    form_requirement_violated = Bool("form_requirement_violated")
    lessor_liable_for_defects = Bool("lessor_liable_for_defects")
    undisclosed_third_party_rights = Bool("undisclosed_third_party_rights")
    unauthorized_sublease = Bool("unauthorized_sublease")
    lessor_neglected_capital_repair = Bool("lessor_neglected_capital_repair")
    lessor_may_terminate_for_breach = Bool("lessor_may_terminate_for_breach")
    tenant_has_priority_renewal = Bool("tenant_has_priority_renewal")
    tenant_improvement_compensation_due = Bool("tenant_improvement_compensation_due")
    requires_human_lease_assessment = Bool("requires_human_lease_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(lease_qualified == variables["property_leased_for_temporary_use"])
    solver.add(
        object_terms_not_agreed == And(lease_qualified, variables["lease_object_not_identifiable"])
    )
    solver.add(
        form_requirement_violated
        == And(lease_qualified, variables["lease_form_or_registration_missing"])
    )
    solver.add(
        lessor_liable_for_defects
        == And(lease_qualified, variables["leased_property_defective_or_incomplete"])
    )
    solver.add(
        undisclosed_third_party_rights
        == And(lease_qualified, variables["third_party_rights_not_disclosed"])
    )
    solver.add(
        unauthorized_sublease == And(lease_qualified, variables["sublease_without_lessor_consent"])
    )
    solver.add(
        lessor_neglected_capital_repair
        == And(lease_qualified, variables["lessor_failed_capital_repair"])
    )
    solver.add(
        lessor_may_terminate_for_breach
        == And(lease_qualified, variables["tenant_materially_breached"])
    )
    solver.add(
        tenant_has_priority_renewal
        == And(lease_qualified, variables["tenant_seeks_renewal_with_priority"])
    )
    solver.add(
        tenant_improvement_compensation_due
        == And(lease_qualified, variables["inseparable_improvements_with_consent"])
    )
    solver.add(
        requires_human_lease_assessment
        == Or(
            object_terms_not_agreed,
            form_requirement_violated,
            lessor_liable_for_defects,
            undisclosed_third_party_rights,
            unauthorized_sublease,
            lessor_neglected_capital_repair,
            lessor_may_terminate_for_breach,
            tenant_improvement_compensation_due,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return LeaseEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            lease_qualified=False,
            object_terms_not_agreed=False,
            form_requirement_violated=False,
            lessor_liable_for_defects=False,
            undisclosed_third_party_rights=False,
            unauthorized_sublease=False,
            lessor_neglected_capital_repair=False,
            lessor_may_terminate_for_breach=False,
            tenant_has_priority_renewal=False,
            tenant_improvement_compensation_due=False,
            requires_human_lease_assessment=True,
            reasons_ru=["Набор фактов об аренде противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как аренда: арендодатель обязуется предоставить арендатору "
            "имущество за плату во временное владение и пользование (статья 606 ГК РФ)."
            if truth(lease_qualified)
            else "Отношения не квалифицированы как договор аренды."
        ),
    ]
    if truth(object_terms_not_agreed):
        reasons_ru.append(
            "В договоре отсутствуют данные, позволяющие определённо установить передаваемое в "
            "аренду имущество: условие об объекте не согласовано, договор не считается "
            "заключённым (статья 607 ГК РФ)."
        )
    if truth(form_requirement_violated):
        reasons_ru.append(
            "Не соблюдены требования к письменной форме или государственной регистрации договора "
            "аренды (статья 609 ГК РФ)."
        )
    if truth(lessor_liable_for_defects):
        reasons_ru.append(
            "Арендодатель предоставил имущество не в надлежащем состоянии, без принадлежностей и "
            "документов либо с недостатками и отвечает за них (статьи 611 и 612 ГК РФ)."
        )
    if truth(undisclosed_third_party_rights):
        reasons_ru.append(
            "Арендодатель не предупредил арендатора о правах третьих лиц на сдаваемое в аренду "
            "имущество; такие права сохраняются, а арендатор вправе требовать уменьшения платы "
            "или расторжения (статья 613 ГК РФ)."
        )
    if truth(unauthorized_sublease):
        reasons_ru.append(
            "Сдача имущества в субаренду произведена без согласия арендодателя, что недопустимо "
            "(статья 615 ГК РФ)."
        )
    if truth(lessor_neglected_capital_repair):
        reasons_ru.append(
            "Арендодатель не производит капитальный ремонт, отнесённый к его обязанностям; "
            "арендатор вправе применить установленные способы защиты (статья 616 ГК РФ)."
        )
    if truth(lessor_may_terminate_for_breach):
        reasons_ru.append(
            "При существенном нарушении арендатором условий договора или назначения имущества "
            "арендодатель вправе требовать досрочного расторжения договора (статья 619 ГК РФ)."
        )
    if truth(tenant_has_priority_renewal):
        reasons_ru.append(
            "Надлежаще исполнявший обязанности арендатор имеет при прочих равных условиях "
            "преимущественное право на заключение договора аренды на новый срок (статья 621 "
            "ГК РФ)."
        )
    if truth(tenant_improvement_compensation_due):
        reasons_ru.append(
            "Стоимость неотделимых улучшений, произведённых арендатором с согласия арендодателя, "
            "подлежит возмещению после прекращения договора, если иное не предусмотрено "
            "(статья 623 ГК РФ)."
        )
    return LeaseEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        lease_qualified=truth(lease_qualified),
        object_terms_not_agreed=truth(object_terms_not_agreed),
        form_requirement_violated=truth(form_requirement_violated),
        lessor_liable_for_defects=truth(lessor_liable_for_defects),
        undisclosed_third_party_rights=truth(undisclosed_third_party_rights),
        unauthorized_sublease=truth(unauthorized_sublease),
        lessor_neglected_capital_repair=truth(lessor_neglected_capital_repair),
        lessor_may_terminate_for_breach=truth(lessor_may_terminate_for_breach),
        tenant_has_priority_renewal=truth(tenant_has_priority_renewal),
        tenant_improvement_compensation_due=truth(tenant_improvement_compensation_due),
        requires_human_lease_assessment=truth(requires_human_lease_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные общие положения об аренде и не заменяет судебную "
            "оценку.",
            "Размер арендной платы, существенность нарушения и стоимость улучшений оцениваются "
            "экспертом и судом (статьи 614, 619 и 623 ГК РФ).",
        ],
    )
