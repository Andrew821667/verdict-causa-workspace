from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


ANNUITY_EVIDENCE_SCHEMA_VERSION = "contracts.annuity-evidence.v0"
ANNUITY_MAPPING_VERSION = "contracts-reviewed-annuity-to-facts-v0"
ANNUITY_MODEL_VERSION = "contracts-annuity-articles-583-605-v0"


class AnnuityEvidencePredicate(str, Enum):
    # Понятие, форма и обеспечение ренты (статьи 583, 584, 587 и 588 ГК РФ).
    PROPERTY_TRANSFERRED_FOR_PERIODIC_RENT = "property_transferred_for_periodic_rent"
    NOTARIZATION_MISSING = "notarization_missing"
    RENT_SECURITY_MISSING = "rent_security_missing"
    RENT_PAYMENT_OVERDUE = "rent_payment_overdue"
    # Постоянная рента и выкуп (статьи 589, 592 и 593 ГК РФ).
    PERMANENT_RENT = "permanent_rent"
    PAYER_WAIVED_REDEMPTION_RIGHT = "payer_waived_redemption_right"
    RECIPIENT_REDEMPTION_GROUND_PRESENT = "recipient_redemption_ground_present"
    # Пожизненная рента и пожизненное содержание с иждивением (статьи 596, 599, 601, 604 и 605).
    LIFE_ANNUITY_OR_MAINTENANCE = "life_annuity_or_maintenance"
    PAYER_MATERIALLY_BREACHED = "payer_materially_breached"
    MAINTENANCE_PROPERTY_ENCUMBERED_WITHOUT_CONSENT = (
        "maintenance_property_encumbered_without_consent"
    )


REQUIRED_ANNUITY_PREDICATES = frozenset(AnnuityEvidencePredicate)


class AnnuityEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: AnnuityEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedAnnuityEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = ANNUITY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[AnnuityEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedAnnuityEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Annuity evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Annuity evidence contains duplicate legal source refs.")
        return self


class AnnuityFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    property_transferred_for_periodic_rent: bool
    notarization_missing: bool
    rent_security_missing: bool
    rent_payment_overdue: bool
    permanent_rent: bool
    payer_waived_redemption_right: bool
    recipient_redemption_ground_present: bool
    life_annuity_or_maintenance: bool
    payer_materially_breached: bool
    maintenance_property_encumbered_without_consent: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "AnnuityFactSet":
        if self.permanent_rent and self.life_annuity_or_maintenance:
            raise ValueError("Рента не может быть одновременно постоянной и пожизненной.")
        if self.payer_waived_redemption_right and not self.permanent_rent:
            raise ValueError("Отказ от права выкупа относится только к постоянной ренте.")
        if (
            self.maintenance_property_encumbered_without_consent
            and not self.life_annuity_or_maintenance
        ):
            raise ValueError(
                "Обременение имущества без согласия получателя относится только к пожизненному "
                "содержанию с иждивением."
            )
        return self


class AnnuityFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class AnnuityEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: AnnuityFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[AnnuityFactProvenance] = Field(default_factory=list)


class AnnuityConstraintSet(BaseModel):
    id: str
    model_version: str = ANNUITY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class AnnuityEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    annuity_qualified: bool
    form_defect_makes_void: bool
    rent_security_not_provided: bool
    overdue_interest_due: bool
    redemption_waiver_void: bool
    recipient_may_demand_redemption: bool
    recipient_may_terminate_life_annuity: bool
    unauthorized_maintenance_encumbrance: bool
    requires_human_annuity_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_annuity_evidence(
    evidence: ReviewedAnnuityEvidence,
) -> AnnuityEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Annuity evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Annuity evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_ANNUITY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed annuity evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_ANNUITY_PREDICATES
    }
    return AnnuityEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=ANNUITY_MAPPING_VERSION,
        facts=AnnuityFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            AnnuityFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_ANNUITY_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_annuity_constraint_set(
    mapping: AnnuityEvidenceMappingResult,
) -> AnnuityConstraintSet:
    return AnnuityConstraintSet(
        id=f"annuity-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "annuity_qualified == property_transferred_for_periodic_rent",
            "form_defect_makes_void == annuity_qualified AND notarization_missing",
            "rent_security_not_provided == annuity_qualified AND rent_security_missing",
            "overdue_interest_due == annuity_qualified AND rent_payment_overdue",
            "redemption_waiver_void == annuity_qualified AND permanent_rent AND payer_waived_redemption_right",
            "recipient_may_demand_redemption == annuity_qualified AND permanent_rent AND recipient_redemption_ground_present",
            "recipient_may_terminate_life_annuity == annuity_qualified AND life_annuity_or_maintenance AND payer_materially_breached",
            "unauthorized_maintenance_encumbrance == annuity_qualified AND life_annuity_or_maintenance AND maintenance_property_encumbered_without_consent",
            "requires_human_annuity_assessment == form_defect_makes_void OR rent_security_not_provided OR overdue_interest_due OR redemption_waiver_void OR recipient_may_demand_redemption OR recipient_may_terminate_life_annuity OR unauthorized_maintenance_encumbrance",
        ],
    )


def evaluate_annuity_constraints(
    constraint_set: AnnuityConstraintSet,
    facts: AnnuityFactSet,
) -> AnnuityEvaluation:
    variables = {field_name: Bool(field_name) for field_name in AnnuityFactSet.model_fields}
    annuity_qualified = Bool("annuity_qualified")
    form_defect_makes_void = Bool("form_defect_makes_void")
    rent_security_not_provided = Bool("rent_security_not_provided")
    overdue_interest_due = Bool("overdue_interest_due")
    redemption_waiver_void = Bool("redemption_waiver_void")
    recipient_may_demand_redemption = Bool("recipient_may_demand_redemption")
    recipient_may_terminate_life_annuity = Bool("recipient_may_terminate_life_annuity")
    unauthorized_maintenance_encumbrance = Bool("unauthorized_maintenance_encumbrance")
    requires_human_annuity_assessment = Bool("requires_human_annuity_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(annuity_qualified == variables["property_transferred_for_periodic_rent"])
    solver.add(form_defect_makes_void == And(annuity_qualified, variables["notarization_missing"]))
    solver.add(
        rent_security_not_provided == And(annuity_qualified, variables["rent_security_missing"])
    )
    solver.add(overdue_interest_due == And(annuity_qualified, variables["rent_payment_overdue"]))
    solver.add(
        redemption_waiver_void
        == And(
            annuity_qualified,
            variables["permanent_rent"],
            variables["payer_waived_redemption_right"],
        )
    )
    solver.add(
        recipient_may_demand_redemption
        == And(
            annuity_qualified,
            variables["permanent_rent"],
            variables["recipient_redemption_ground_present"],
        )
    )
    solver.add(
        recipient_may_terminate_life_annuity
        == And(
            annuity_qualified,
            variables["life_annuity_or_maintenance"],
            variables["payer_materially_breached"],
        )
    )
    solver.add(
        unauthorized_maintenance_encumbrance
        == And(
            annuity_qualified,
            variables["life_annuity_or_maintenance"],
            variables["maintenance_property_encumbered_without_consent"],
        )
    )
    solver.add(
        requires_human_annuity_assessment
        == Or(
            form_defect_makes_void,
            rent_security_not_provided,
            overdue_interest_due,
            redemption_waiver_void,
            recipient_may_demand_redemption,
            recipient_may_terminate_life_annuity,
            unauthorized_maintenance_encumbrance,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return AnnuityEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            annuity_qualified=False,
            form_defect_makes_void=False,
            rent_security_not_provided=False,
            overdue_interest_due=False,
            redemption_waiver_void=False,
            recipient_may_demand_redemption=False,
            recipient_may_terminate_life_annuity=False,
            unauthorized_maintenance_encumbrance=False,
            requires_human_annuity_assessment=True,
            reasons_ru=["Набор фактов о ренте противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как рента: получатель ренты передал плательщику имущество "
            "в собственность в обмен на периодические рентные платежи (статья 583 ГК РФ)."
            if truth(annuity_qualified)
            else "Отношения не квалифицированы как договор ренты."
        ),
    ]
    if truth(form_defect_makes_void):
        reasons_ru.append(
            "Несоблюдение нотариальной формы (и государственной регистрации для недвижимости) "
            "влечёт ничтожность договора ренты (статья 584 ГК РФ)."
        )
    if truth(rent_security_not_provided):
        reasons_ru.append(
            "Обеспечение выплаты ренты не предоставлено: получатель приобретает право залога на "
            "недвижимость, а для движимого имущества обеспечение является существенным условием "
            "(статья 587 ГК РФ)."
        )
    if truth(overdue_interest_due):
        reasons_ru.append(
            "За просрочку выплаты ренты плательщик уплачивает получателю проценты, если иное не "
            "установлено договором (статья 588 ГК РФ)."
        )
    if truth(redemption_waiver_void):
        reasons_ru.append(
            "Условие об отказе плательщика постоянной ренты от права её выкупа ничтожно "
            "(статья 592 ГК РФ)."
        )
    if truth(recipient_may_demand_redemption):
        reasons_ru.append(
            "При наличии установленных оснований получатель постоянной ренты вправе требовать "
            "её выкупа плательщиком (статья 593 ГК РФ)."
        )
    if truth(recipient_may_terminate_life_annuity):
        reasons_ru.append(
            "При существенном нарушении плательщиком получатель пожизненной ренты или "
            "пожизненного содержания вправе требовать выкупа или расторжения договора и "
            "возмещения убытков (статьи 599 и 605 ГК РФ)."
        )
    if truth(unauthorized_maintenance_encumbrance):
        reasons_ru.append(
            "Отчуждение или обременение переданной под пожизненное содержание недвижимости без "
            "предварительного согласия получателя ренты недопустимо (статья 604 ГК РФ)."
        )
    return AnnuityEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        annuity_qualified=truth(annuity_qualified),
        form_defect_makes_void=truth(form_defect_makes_void),
        rent_security_not_provided=truth(rent_security_not_provided),
        overdue_interest_due=truth(overdue_interest_due),
        redemption_waiver_void=truth(redemption_waiver_void),
        recipient_may_demand_redemption=truth(recipient_may_demand_redemption),
        recipient_may_terminate_life_annuity=truth(recipient_may_terminate_life_annuity),
        unauthorized_maintenance_encumbrance=truth(unauthorized_maintenance_encumbrance),
        requires_human_annuity_assessment=truth(requires_human_annuity_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о ренте и пожизненном содержании и не "
            "заменяет судебную оценку.",
            "Размер ренты и содержания, выкупная цена и существенность нарушения оцениваются "
            "экспертом и судом (статьи 594, 597 и 602 ГК РФ).",
        ],
    )
