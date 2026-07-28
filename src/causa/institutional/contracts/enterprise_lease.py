from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


ENTERPRISE_LEASE_EVIDENCE_SCHEMA_VERSION = "contracts.enterprise-lease-evidence.v0"
ENTERPRISE_LEASE_MAPPING_VERSION = "contracts-reviewed-enterprise-lease-to-facts-v0"
ENTERPRISE_LEASE_MODEL_VERSION = "contracts-enterprise-lease-articles-656-664-v0"


class EnterpriseLeaseEvidencePredicate(str, Enum):
    # Понятие, форма и регистрация (статьи 656 и 658 ГК РФ).
    ENTERPRISE_LEASED_AS_COMPLEX = "enterprise_leased_as_complex"
    SINGLE_WRITTEN_DOCUMENT_MISSING = "single_written_document_missing"
    STATE_REGISTRATION_MISSING = "state_registration_missing"
    # Права кредиторов по долгам предприятия (статья 657 ГК РФ).
    CREDITORS_NOT_NOTIFIED = "creditors_not_notified"
    DEBT_TRANSFERRED_WITHOUT_CREDITOR_CONSENT = "debt_transferred_without_creditor_consent"
    # Передача предприятия и подготовка (статья 659 ГК РФ).
    TRANSFER_DEED_MISSING = "transfer_deed_missing"
    LESSOR_FAILED_TRANSFER_PREPARATION = "lessor_failed_transfer_preparation"
    # Пользование, содержание и возврат (статьи 660, 661 и 664 ГК РФ).
    TENANT_DISPOSAL_RIGHT_WRONGLY_RESTRICTED = "tenant_disposal_right_wrongly_restricted"
    MAINTENANCE_OR_REPAIR_NEGLECTED = "maintenance_or_repair_neglected"
    RETURN_PREPARATION_NEGLECTED = "return_preparation_neglected"


REQUIRED_ENTERPRISE_LEASE_PREDICATES = frozenset(EnterpriseLeaseEvidencePredicate)


class EnterpriseLeaseEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: EnterpriseLeaseEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedEnterpriseLeaseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = ENTERPRISE_LEASE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[EnterpriseLeaseEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedEnterpriseLeaseEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Enterprise-lease evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Enterprise-lease evidence contains duplicate legal source refs.")
        return self


class EnterpriseLeaseFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    enterprise_leased_as_complex: bool
    single_written_document_missing: bool
    state_registration_missing: bool
    creditors_not_notified: bool
    debt_transferred_without_creditor_consent: bool
    transfer_deed_missing: bool
    lessor_failed_transfer_preparation: bool
    tenant_disposal_right_wrongly_restricted: bool
    maintenance_or_repair_neglected: bool
    return_preparation_neglected: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "EnterpriseLeaseFactSet":
        if self.debt_transferred_without_creditor_consent and not self.enterprise_leased_as_complex:
            raise ValueError(
                "Перевод долгов без согласия кредитора относится только к аренде предприятия "
                "как имущественного комплекса."
            )
        return self


class EnterpriseLeaseFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class EnterpriseLeaseEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: EnterpriseLeaseFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[EnterpriseLeaseFactProvenance] = Field(default_factory=list)


class EnterpriseLeaseConstraintSet(BaseModel):
    id: str
    model_version: str = ENTERPRISE_LEASE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class EnterpriseLeaseEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    enterprise_lease_qualified: bool
    form_defect_makes_void: bool
    registration_required_and_missing: bool
    creditor_notice_not_given: bool
    creditor_consent_missing_for_debt: bool
    transfer_not_documented: bool
    transfer_preparation_breached: bool
    disposal_right_wrongly_restricted: bool
    maintenance_duty_breached: bool
    return_preparation_breached: bool
    requires_human_enterprise_lease_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_enterprise_lease_evidence(
    evidence: ReviewedEnterpriseLeaseEvidence,
) -> EnterpriseLeaseEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Enterprise-lease evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Enterprise-lease evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_ENTERPRISE_LEASE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed enterprise-lease evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_ENTERPRISE_LEASE_PREDICATES
    }
    return EnterpriseLeaseEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=ENTERPRISE_LEASE_MAPPING_VERSION,
        facts=EnterpriseLeaseFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            EnterpriseLeaseFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_ENTERPRISE_LEASE_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_enterprise_lease_constraint_set(
    mapping: EnterpriseLeaseEvidenceMappingResult,
) -> EnterpriseLeaseConstraintSet:
    return EnterpriseLeaseConstraintSet(
        id=f"enterprise-lease-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "enterprise_lease_qualified == enterprise_leased_as_complex",
            "form_defect_makes_void == enterprise_lease_qualified AND single_written_document_missing",
            "registration_required_and_missing == enterprise_lease_qualified AND state_registration_missing",
            "creditor_notice_not_given == enterprise_lease_qualified AND creditors_not_notified",
            "creditor_consent_missing_for_debt == enterprise_lease_qualified AND debt_transferred_without_creditor_consent",
            "transfer_not_documented == enterprise_lease_qualified AND transfer_deed_missing",
            "transfer_preparation_breached == enterprise_lease_qualified AND lessor_failed_transfer_preparation",
            "disposal_right_wrongly_restricted == enterprise_lease_qualified AND tenant_disposal_right_wrongly_restricted",
            "maintenance_duty_breached == enterprise_lease_qualified AND maintenance_or_repair_neglected",
            "return_preparation_breached == enterprise_lease_qualified AND return_preparation_neglected",
            "requires_human_enterprise_lease_assessment == form_defect_makes_void OR registration_required_and_missing OR creditor_notice_not_given OR creditor_consent_missing_for_debt OR transfer_not_documented OR transfer_preparation_breached OR disposal_right_wrongly_restricted OR maintenance_duty_breached OR return_preparation_breached",
        ],
    )


def evaluate_enterprise_lease_constraints(
    constraint_set: EnterpriseLeaseConstraintSet,
    facts: EnterpriseLeaseFactSet,
) -> EnterpriseLeaseEvaluation:
    variables = {field_name: Bool(field_name) for field_name in EnterpriseLeaseFactSet.model_fields}
    enterprise_lease_qualified = Bool("enterprise_lease_qualified")
    form_defect_makes_void = Bool("form_defect_makes_void")
    registration_required_and_missing = Bool("registration_required_and_missing")
    creditor_notice_not_given = Bool("creditor_notice_not_given")
    creditor_consent_missing_for_debt = Bool("creditor_consent_missing_for_debt")
    transfer_not_documented = Bool("transfer_not_documented")
    transfer_preparation_breached = Bool("transfer_preparation_breached")
    disposal_right_wrongly_restricted = Bool("disposal_right_wrongly_restricted")
    maintenance_duty_breached = Bool("maintenance_duty_breached")
    return_preparation_breached = Bool("return_preparation_breached")
    requires_human_enterprise_lease_assessment = Bool("requires_human_enterprise_lease_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(enterprise_lease_qualified == variables["enterprise_leased_as_complex"])
    solver.add(
        form_defect_makes_void
        == And(enterprise_lease_qualified, variables["single_written_document_missing"])
    )
    solver.add(
        registration_required_and_missing
        == And(enterprise_lease_qualified, variables["state_registration_missing"])
    )
    solver.add(
        creditor_notice_not_given
        == And(enterprise_lease_qualified, variables["creditors_not_notified"])
    )
    solver.add(
        creditor_consent_missing_for_debt
        == And(
            enterprise_lease_qualified,
            variables["debt_transferred_without_creditor_consent"],
        )
    )
    solver.add(
        transfer_not_documented
        == And(enterprise_lease_qualified, variables["transfer_deed_missing"])
    )
    solver.add(
        transfer_preparation_breached
        == And(enterprise_lease_qualified, variables["lessor_failed_transfer_preparation"])
    )
    solver.add(
        disposal_right_wrongly_restricted
        == And(
            enterprise_lease_qualified,
            variables["tenant_disposal_right_wrongly_restricted"],
        )
    )
    solver.add(
        maintenance_duty_breached
        == And(enterprise_lease_qualified, variables["maintenance_or_repair_neglected"])
    )
    solver.add(
        return_preparation_breached
        == And(enterprise_lease_qualified, variables["return_preparation_neglected"])
    )
    solver.add(
        requires_human_enterprise_lease_assessment
        == Or(
            form_defect_makes_void,
            registration_required_and_missing,
            creditor_notice_not_given,
            creditor_consent_missing_for_debt,
            transfer_not_documented,
            transfer_preparation_breached,
            disposal_right_wrongly_restricted,
            maintenance_duty_breached,
            return_preparation_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return EnterpriseLeaseEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            enterprise_lease_qualified=False,
            form_defect_makes_void=False,
            registration_required_and_missing=False,
            creditor_notice_not_given=False,
            creditor_consent_missing_for_debt=False,
            transfer_not_documented=False,
            transfer_preparation_breached=False,
            disposal_right_wrongly_restricted=False,
            maintenance_duty_breached=False,
            return_preparation_breached=False,
            requires_human_enterprise_lease_assessment=True,
            reasons_ru=["Набор фактов об аренде предприятия противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как аренда предприятия: арендодатель обязуется предоставить "
            "арендатору за плату во временное владение и пользование предприятие в целом как "
            "имущественный комплекс, используемый для предпринимательской деятельности "
            "(статья 656 ГК РФ)."
            if truth(enterprise_lease_qualified)
            else "Отношения не квалифицированы как аренда предприятия."
        ),
    ]
    if truth(form_defect_makes_void):
        reasons_ru.append(
            "Договор аренды предприятия заключается в письменной форме путём составления одного "
            "документа, подписанного сторонами; несоблюдение формы влечёт недействительность "
            "договора (статья 658 ГК РФ)."
        )
    if truth(registration_required_and_missing):
        reasons_ru.append(
            "Договор аренды предприятия подлежит государственной регистрации и считается "
            "заключённым с момента такой регистрации (статья 658 ГК РФ)."
        )
    if truth(creditor_notice_not_given):
        reasons_ru.append(
            "Кредиторы по обязательствам, включённым в состав предприятия, должны быть письменно "
            "уведомлены о передаче предприятия в аренду до его передачи (статья 657 ГК РФ)."
        )
    if truth(creditor_consent_missing_for_debt):
        reasons_ru.append(
            "Перевод на арендатора долгов, включённых в состав предприятия, без согласия "
            "кредитора недопустим; после передачи стороны несут солидарную ответственность по "
            "включённым в состав предприятия долгам, переведённым без согласия кредитора "
            "(статья 657 ГК РФ)."
        )
    if truth(transfer_not_documented):
        reasons_ru.append(
            "Передача предприятия арендатору осуществляется по передаточному акту (статья 659 "
            "ГК РФ)."
        )
    if truth(transfer_preparation_breached):
        reasons_ru.append(
            "Подготовка предприятия к передаче, включая составление и представление на подписание "
            "передаточного акта, является обязанностью арендодателя и осуществляется за его счёт "
            "(статья 659 ГК РФ)."
        )
    if truth(disposal_right_wrongly_restricted):
        reasons_ru.append(
            "Арендатор вправе без согласия арендодателя продавать, обменивать, предоставлять во "
            "временное пользование материальные ценности, входящие в состав имущества "
            "арендованного предприятия, если это не влечёт уменьшения его стоимости и не "
            "нарушает условий договора; ограничение неправомерно (статья 660 ГК РФ)."
        )
    if truth(maintenance_duty_breached):
        reasons_ru.append(
            "Арендатор обязан в течение всего срока действия договора поддерживать предприятие в "
            "надлежащем техническом состоянии, включая его текущий и капитальный ремонт "
            "(статья 661 ГК РФ)."
        )
    if truth(return_preparation_breached):
        reasons_ru.append(
            "При прекращении договора арендованный имущественный комплекс возвращается "
            "арендодателю по передаточному акту; подготовка предприятия к передаче является "
            "обязанностью арендатора и осуществляется за его счёт (статья 664 ГК РФ)."
        )
    return EnterpriseLeaseEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        enterprise_lease_qualified=truth(enterprise_lease_qualified),
        form_defect_makes_void=truth(form_defect_makes_void),
        registration_required_and_missing=truth(registration_required_and_missing),
        creditor_notice_not_given=truth(creditor_notice_not_given),
        creditor_consent_missing_for_debt=truth(creditor_consent_missing_for_debt),
        transfer_not_documented=truth(transfer_not_documented),
        transfer_preparation_breached=truth(transfer_preparation_breached),
        disposal_right_wrongly_restricted=truth(disposal_right_wrongly_restricted),
        maintenance_duty_breached=truth(maintenance_duty_breached),
        return_preparation_breached=truth(return_preparation_breached),
        requires_human_enterprise_lease_assessment=truth(
            requires_human_enterprise_lease_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила об аренде предприятий и не заменяет "
            "судебную оценку.",
            "Состав предприятия, стоимость передаваемых ценностей и объём обязанностей по "
            "содержанию оцениваются экспертом и судом (статьи 656, 660 и 661 ГК РФ).",
        ],
    )
