from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


RESIDENTIAL_LEASE_EVIDENCE_SCHEMA_VERSION = "contracts.residential-lease-evidence.v0"
RESIDENTIAL_LEASE_MAPPING_VERSION = "contracts-reviewed-residential-lease-to-facts-v0"
RESIDENTIAL_LEASE_MODEL_VERSION = "contracts-residential-lease-articles-671-688-v0"


class ResidentialLeaseEvidencePredicate(str, Enum):
    # Понятие, форма и срок найма (статьи 671, 673, 674 и 683 ГК РФ).
    DWELLING_PROVIDED_FOR_RESIDENCE_FOR_FEE = "dwelling_provided_for_residence_for_fee"
    WRITTEN_FORM_MISSING = "written_form_missing"
    DWELLING_NOT_ISOLATED_OR_UNFIT = "dwelling_not_isolated_or_unfit"
    SHORT_TERM_LEASE_UP_TO_ONE_YEAR = "short_term_lease_up_to_one_year"
    # Обязанности сторон и плата (статьи 676, 678 и 682 ГК РФ).
    LESSOR_FAILED_OPERATION_DUTIES = "lessor_failed_operation_duties"
    TENANT_BREACHED_USE_OR_PAYMENT = "tenant_breached_use_or_payment"
    RENT_UNILATERALLY_CHANGED = "rent_unilaterally_changed"
    # Преимущественное право и расторжение (статьи 684, 687 и 688 ГК РФ).
    RENEWAL_OFFER_NOT_MADE_BEFORE_EXPIRY = "renewal_offer_not_made_before_expiry"
    LESSOR_TERMINATED_WITHOUT_COURT = "lessor_terminated_without_court"
    TENANT_DENIED_REMEDY_PERIOD = "tenant_denied_remedy_period"


REQUIRED_RESIDENTIAL_LEASE_PREDICATES = frozenset(ResidentialLeaseEvidencePredicate)


class ResidentialLeaseEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ResidentialLeaseEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedResidentialLeaseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = RESIDENTIAL_LEASE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ResidentialLeaseEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedResidentialLeaseEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Residential-lease evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Residential-lease evidence contains duplicate legal source refs.")
        return self


class ResidentialLeaseFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dwelling_provided_for_residence_for_fee: bool
    written_form_missing: bool
    dwelling_not_isolated_or_unfit: bool
    short_term_lease_up_to_one_year: bool
    lessor_failed_operation_duties: bool
    tenant_breached_use_or_payment: bool
    rent_unilaterally_changed: bool
    renewal_offer_not_made_before_expiry: bool
    lessor_terminated_without_court: bool
    tenant_denied_remedy_period: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ResidentialLeaseFactSet":
        if self.renewal_offer_not_made_before_expiry and self.short_term_lease_up_to_one_year:
            raise ValueError(
                "Правила о преимущественном праве нанимателя на заключение договора на новый "
                "срок не применяются к краткосрочному найму до одного года."
            )
        if self.tenant_denied_remedy_period and not self.tenant_breached_use_or_payment:
            raise ValueError(
                "Отказ в предоставлении срока для устранения нарушения относится только к "
                "случаю нарушения нанимателем условий пользования или оплаты."
            )
        return self


class ResidentialLeaseFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ResidentialLeaseEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ResidentialLeaseFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ResidentialLeaseFactProvenance] = Field(default_factory=list)


class ResidentialLeaseConstraintSet(BaseModel):
    id: str
    model_version: str = RESIDENTIAL_LEASE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ResidentialLeaseEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    residential_lease_qualified: bool
    form_requirement_violated: bool
    object_not_suitable_for_residence: bool
    lessor_operation_duties_breached: bool
    tenant_breach_established: bool
    unilateral_rent_change_invalid: bool
    renewal_priority_right_breached: bool
    extrajudicial_termination_invalid: bool
    remedy_period_wrongly_denied: bool
    requires_human_residential_lease_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_residential_lease_evidence(
    evidence: ReviewedResidentialLeaseEvidence,
) -> ResidentialLeaseEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Residential-lease evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Residential-lease evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_RESIDENTIAL_LEASE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed residential-lease evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_RESIDENTIAL_LEASE_PREDICATES
    }
    return ResidentialLeaseEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=RESIDENTIAL_LEASE_MAPPING_VERSION,
        facts=ResidentialLeaseFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ResidentialLeaseFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_RESIDENTIAL_LEASE_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_residential_lease_constraint_set(
    mapping: ResidentialLeaseEvidenceMappingResult,
) -> ResidentialLeaseConstraintSet:
    return ResidentialLeaseConstraintSet(
        id=f"residential-lease-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "residential_lease_qualified == dwelling_provided_for_residence_for_fee",
            "form_requirement_violated == residential_lease_qualified AND written_form_missing",
            "object_not_suitable_for_residence == residential_lease_qualified AND dwelling_not_isolated_or_unfit",
            "lessor_operation_duties_breached == residential_lease_qualified AND lessor_failed_operation_duties",
            "tenant_breach_established == residential_lease_qualified AND tenant_breached_use_or_payment",
            "unilateral_rent_change_invalid == residential_lease_qualified AND rent_unilaterally_changed",
            "renewal_priority_right_breached == residential_lease_qualified AND renewal_offer_not_made_before_expiry",
            "extrajudicial_termination_invalid == residential_lease_qualified AND lessor_terminated_without_court",
            "remedy_period_wrongly_denied == residential_lease_qualified AND tenant_breached_use_or_payment AND tenant_denied_remedy_period",
            "requires_human_residential_lease_assessment == form_requirement_violated OR object_not_suitable_for_residence OR lessor_operation_duties_breached OR tenant_breach_established OR unilateral_rent_change_invalid OR renewal_priority_right_breached OR extrajudicial_termination_invalid OR remedy_period_wrongly_denied",
        ],
    )


def evaluate_residential_lease_constraints(
    constraint_set: ResidentialLeaseConstraintSet,
    facts: ResidentialLeaseFactSet,
) -> ResidentialLeaseEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in ResidentialLeaseFactSet.model_fields
    }
    residential_lease_qualified = Bool("residential_lease_qualified")
    form_requirement_violated = Bool("form_requirement_violated")
    object_not_suitable_for_residence = Bool("object_not_suitable_for_residence")
    lessor_operation_duties_breached = Bool("lessor_operation_duties_breached")
    tenant_breach_established = Bool("tenant_breach_established")
    unilateral_rent_change_invalid = Bool("unilateral_rent_change_invalid")
    renewal_priority_right_breached = Bool("renewal_priority_right_breached")
    extrajudicial_termination_invalid = Bool("extrajudicial_termination_invalid")
    remedy_period_wrongly_denied = Bool("remedy_period_wrongly_denied")
    requires_human_residential_lease_assessment = Bool(
        "requires_human_residential_lease_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(residential_lease_qualified == variables["dwelling_provided_for_residence_for_fee"])
    solver.add(
        form_requirement_violated
        == And(residential_lease_qualified, variables["written_form_missing"])
    )
    solver.add(
        object_not_suitable_for_residence
        == And(residential_lease_qualified, variables["dwelling_not_isolated_or_unfit"])
    )
    solver.add(
        lessor_operation_duties_breached
        == And(residential_lease_qualified, variables["lessor_failed_operation_duties"])
    )
    solver.add(
        tenant_breach_established
        == And(residential_lease_qualified, variables["tenant_breached_use_or_payment"])
    )
    solver.add(
        unilateral_rent_change_invalid
        == And(residential_lease_qualified, variables["rent_unilaterally_changed"])
    )
    solver.add(
        renewal_priority_right_breached
        == And(residential_lease_qualified, variables["renewal_offer_not_made_before_expiry"])
    )
    solver.add(
        extrajudicial_termination_invalid
        == And(residential_lease_qualified, variables["lessor_terminated_without_court"])
    )
    solver.add(
        remedy_period_wrongly_denied
        == And(
            residential_lease_qualified,
            variables["tenant_breached_use_or_payment"],
            variables["tenant_denied_remedy_period"],
        )
    )
    solver.add(
        requires_human_residential_lease_assessment
        == Or(
            form_requirement_violated,
            object_not_suitable_for_residence,
            lessor_operation_duties_breached,
            tenant_breach_established,
            unilateral_rent_change_invalid,
            renewal_priority_right_breached,
            extrajudicial_termination_invalid,
            remedy_period_wrongly_denied,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ResidentialLeaseEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            residential_lease_qualified=False,
            form_requirement_violated=False,
            object_not_suitable_for_residence=False,
            lessor_operation_duties_breached=False,
            tenant_breach_established=False,
            unilateral_rent_change_invalid=False,
            renewal_priority_right_breached=False,
            extrajudicial_termination_invalid=False,
            remedy_period_wrongly_denied=False,
            requires_human_residential_lease_assessment=True,
            reasons_ru=["Набор фактов о найме жилого помещения противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как наём жилого помещения: собственник или управомоченное "
            "им лицо обязуется предоставить нанимателю жилое помещение за плату во владение и "
            "пользование для проживания в нём (статья 671 ГК РФ)."
            if truth(residential_lease_qualified)
            else "Отношения не квалифицированы как наём жилого помещения."
        ),
    ]
    if truth(form_requirement_violated):
        reasons_ru.append(
            "Договор найма жилого помещения заключается в письменной форме (статья 674 ГК РФ)."
        )
    if truth(object_not_suitable_for_residence):
        reasons_ru.append(
            "Объектом договора найма может быть изолированное жилое помещение, пригодное для "
            "постоянного проживания; заявленный объект этому требованию не отвечает "
            "(статья 673 ГК РФ)."
        )
    if truth(lessor_operation_duties_breached):
        reasons_ru.append(
            "Наймодатель обязан осуществлять надлежащую эксплуатацию жилого дома, обеспечивать "
            "проведение ремонта общего имущества и предоставление коммунальных услуг "
            "(статья 676 ГК РФ)."
        )
    if truth(tenant_breach_established):
        reasons_ru.append(
            "Наниматель обязан использовать жилое помещение только для проживания, обеспечивать "
            "его сохранность и своевременно вносить плату; нарушение этих обязанностей "
            "установлено (статьи 678 и 687 ГК РФ)."
        )
    if truth(unilateral_rent_change_invalid):
        reasons_ru.append(
            "Одностороннее изменение размера платы за жилое помещение не допускается, за "
            "исключением случаев, предусмотренных законом или договором (статья 682 ГК РФ)."
        )
    if truth(renewal_priority_right_breached):
        reasons_ru.append(
            "Не позднее чем за три месяца до истечения срока найма наймодатель обязан предложить "
            "нанимателю заключить договор на тех же или иных условиях либо предупредить об "
            "отказе от продления; иначе договор считается продлённым на прежних условиях "
            "(статья 684 ГК РФ)."
        )
    if truth(extrajudicial_termination_invalid):
        reasons_ru.append(
            "Расторжение договора найма жилого помещения по требованию наймодателя допускается "
            "только в судебном порядке (статьи 687 и 688 ГК РФ)."
        )
    if truth(remedy_period_wrongly_denied):
        reasons_ru.append(
            "При расторжении по требованию наймодателя суд может предоставить нанимателю срок "
            "для устранения нарушения; отказ в предоставлении такого срока подлежит проверке "
            "(статья 687 ГК РФ)."
        )
    return ResidentialLeaseEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        residential_lease_qualified=truth(residential_lease_qualified),
        form_requirement_violated=truth(form_requirement_violated),
        object_not_suitable_for_residence=truth(object_not_suitable_for_residence),
        lessor_operation_duties_breached=truth(lessor_operation_duties_breached),
        tenant_breach_established=truth(tenant_breach_established),
        unilateral_rent_change_invalid=truth(unilateral_rent_change_invalid),
        renewal_priority_right_breached=truth(renewal_priority_right_breached),
        extrajudicial_termination_invalid=truth(extrajudicial_termination_invalid),
        remedy_period_wrongly_denied=truth(remedy_period_wrongly_denied),
        requires_human_residential_lease_assessment=truth(
            requires_human_residential_lease_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о найме жилого помещения и не заменяет "
            "судебную оценку.",
            "Размер платы, пригодность помещения, существенность нарушения и достаточность срока "
            "для его устранения оцениваются экспертом и судом (статьи 673, 682 и 687 ГК РФ).",
        ],
    )
