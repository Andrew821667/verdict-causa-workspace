from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


VEHICLE_LEASE_EVIDENCE_SCHEMA_VERSION = "contracts.vehicle-lease-evidence.v0"
VEHICLE_LEASE_MAPPING_VERSION = "contracts-reviewed-vehicle-lease-to-facts-v0"
VEHICLE_LEASE_MODEL_VERSION = "contracts-vehicle-lease-articles-632-649-v0"


class VehicleLeaseEvidencePredicate(str, Enum):
    # Понятие, вид и форма (статьи 632, 633, 642 и 643 ГК РФ).
    VEHICLE_LEASED_FOR_TEMPORARY_USE = "vehicle_leased_for_temporary_use"
    LEASE_WITH_CREW = "lease_with_crew"
    WRITTEN_FORM_MISSING = "written_form_missing"
    RENEWAL_OR_PRIORITY_RIGHT_CLAIMED = "renewal_or_priority_right_claimed"
    # Содержание, экипаж и расходы (статьи 634–636, 644–646 ГК РФ).
    MAINTENANCE_OR_REPAIR_NEGLECTED = "maintenance_or_repair_neglected"
    CREW_SERVICE_NOT_PROVIDED = "crew_service_not_provided"
    OPERATING_COSTS_MISALLOCATED = "operating_costs_misallocated"
    # Страхование, субаренда и ответственность (статьи 637, 638, 640, 646–648 ГК РФ).
    INSURANCE_OBLIGATION_BREACHED = "insurance_obligation_breached"
    SUBLEASE_WRONGLY_RESTRICTED = "sublease_wrongly_restricted"
    THIRD_PARTY_HARM_LIABILITY_MISASSIGNED = "third_party_harm_liability_misassigned"


REQUIRED_VEHICLE_LEASE_PREDICATES = frozenset(VehicleLeaseEvidencePredicate)


class VehicleLeaseEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: VehicleLeaseEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedVehicleLeaseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = VEHICLE_LEASE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[VehicleLeaseEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedVehicleLeaseEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Vehicle-lease evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Vehicle-lease evidence contains duplicate legal source refs.")
        return self


class VehicleLeaseFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    vehicle_leased_for_temporary_use: bool
    lease_with_crew: bool
    written_form_missing: bool
    renewal_or_priority_right_claimed: bool
    maintenance_or_repair_neglected: bool
    crew_service_not_provided: bool
    operating_costs_misallocated: bool
    insurance_obligation_breached: bool
    sublease_wrongly_restricted: bool
    third_party_harm_liability_misassigned: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "VehicleLeaseFactSet":
        if self.crew_service_not_provided and not self.lease_with_crew:
            raise ValueError(
                "Неоказание услуг экипажа относится только к аренде транспортного средства с "
                "экипажем."
            )
        return self


class VehicleLeaseFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class VehicleLeaseEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: VehicleLeaseFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[VehicleLeaseFactProvenance] = Field(default_factory=list)


class VehicleLeaseConstraintSet(BaseModel):
    id: str
    model_version: str = VEHICLE_LEASE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class VehicleLeaseEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    vehicle_lease_qualified: bool
    form_requirement_violated: bool
    renewal_right_not_available: bool
    maintenance_duty_breached: bool
    crew_service_shortfall: bool
    operating_cost_misallocation: bool
    insurance_duty_breached: bool
    sublease_restriction_invalid: bool
    third_party_liability_misassigned: bool
    requires_human_vehicle_lease_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_vehicle_lease_evidence(
    evidence: ReviewedVehicleLeaseEvidence,
) -> VehicleLeaseEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Vehicle-lease evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Vehicle-lease evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_VEHICLE_LEASE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed vehicle-lease evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_VEHICLE_LEASE_PREDICATES
    }
    return VehicleLeaseEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=VEHICLE_LEASE_MAPPING_VERSION,
        facts=VehicleLeaseFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            VehicleLeaseFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_VEHICLE_LEASE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_vehicle_lease_constraint_set(
    mapping: VehicleLeaseEvidenceMappingResult,
) -> VehicleLeaseConstraintSet:
    return VehicleLeaseConstraintSet(
        id=f"vehicle-lease-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "vehicle_lease_qualified == vehicle_leased_for_temporary_use",
            "form_requirement_violated == vehicle_lease_qualified AND written_form_missing",
            "renewal_right_not_available == vehicle_lease_qualified AND renewal_or_priority_right_claimed",
            "maintenance_duty_breached == vehicle_lease_qualified AND maintenance_or_repair_neglected",
            "crew_service_shortfall == vehicle_lease_qualified AND lease_with_crew AND crew_service_not_provided",
            "operating_cost_misallocation == vehicle_lease_qualified AND operating_costs_misallocated",
            "insurance_duty_breached == vehicle_lease_qualified AND insurance_obligation_breached",
            "sublease_restriction_invalid == vehicle_lease_qualified AND sublease_wrongly_restricted",
            "third_party_liability_misassigned == vehicle_lease_qualified AND third_party_harm_liability_misassigned",
            "requires_human_vehicle_lease_assessment == form_requirement_violated OR renewal_right_not_available OR maintenance_duty_breached OR crew_service_shortfall OR operating_cost_misallocation OR insurance_duty_breached OR sublease_restriction_invalid OR third_party_liability_misassigned",
        ],
    )


def evaluate_vehicle_lease_constraints(
    constraint_set: VehicleLeaseConstraintSet,
    facts: VehicleLeaseFactSet,
) -> VehicleLeaseEvaluation:
    variables = {field_name: Bool(field_name) for field_name in VehicleLeaseFactSet.model_fields}
    vehicle_lease_qualified = Bool("vehicle_lease_qualified")
    form_requirement_violated = Bool("form_requirement_violated")
    renewal_right_not_available = Bool("renewal_right_not_available")
    maintenance_duty_breached = Bool("maintenance_duty_breached")
    crew_service_shortfall = Bool("crew_service_shortfall")
    operating_cost_misallocation = Bool("operating_cost_misallocation")
    insurance_duty_breached = Bool("insurance_duty_breached")
    sublease_restriction_invalid = Bool("sublease_restriction_invalid")
    third_party_liability_misassigned = Bool("third_party_liability_misassigned")
    requires_human_vehicle_lease_assessment = Bool("requires_human_vehicle_lease_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(vehicle_lease_qualified == variables["vehicle_leased_for_temporary_use"])
    solver.add(
        form_requirement_violated == And(vehicle_lease_qualified, variables["written_form_missing"])
    )
    solver.add(
        renewal_right_not_available
        == And(vehicle_lease_qualified, variables["renewal_or_priority_right_claimed"])
    )
    solver.add(
        maintenance_duty_breached
        == And(vehicle_lease_qualified, variables["maintenance_or_repair_neglected"])
    )
    solver.add(
        crew_service_shortfall
        == And(
            vehicle_lease_qualified,
            variables["lease_with_crew"],
            variables["crew_service_not_provided"],
        )
    )
    solver.add(
        operating_cost_misallocation
        == And(vehicle_lease_qualified, variables["operating_costs_misallocated"])
    )
    solver.add(
        insurance_duty_breached
        == And(vehicle_lease_qualified, variables["insurance_obligation_breached"])
    )
    solver.add(
        sublease_restriction_invalid
        == And(vehicle_lease_qualified, variables["sublease_wrongly_restricted"])
    )
    solver.add(
        third_party_liability_misassigned
        == And(vehicle_lease_qualified, variables["third_party_harm_liability_misassigned"])
    )
    solver.add(
        requires_human_vehicle_lease_assessment
        == Or(
            form_requirement_violated,
            renewal_right_not_available,
            maintenance_duty_breached,
            crew_service_shortfall,
            operating_cost_misallocation,
            insurance_duty_breached,
            sublease_restriction_invalid,
            third_party_liability_misassigned,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return VehicleLeaseEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            vehicle_lease_qualified=False,
            form_requirement_violated=False,
            renewal_right_not_available=False,
            maintenance_duty_breached=False,
            crew_service_shortfall=False,
            operating_cost_misallocation=False,
            insurance_duty_breached=False,
            sublease_restriction_invalid=False,
            third_party_liability_misassigned=False,
            requires_human_vehicle_lease_assessment=True,
            reasons_ru=["Набор фактов об аренде транспортного средства противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как аренда транспортного средства: арендодатель предоставил "
            "транспортное средство за плату во временное владение и пользование (статьи 632 и 642 "
            "ГК РФ)."
            if truth(vehicle_lease_qualified)
            else "Отношения не квалифицированы как аренда транспортного средства."
        ),
    ]
    if truth(form_requirement_violated):
        reasons_ru.append(
            "Договор аренды транспортного средства заключается в письменной форме независимо от "
            "срока; требование формы нарушено (статьи 633 и 643 ГК РФ)."
        )
    if truth(renewal_right_not_available):
        reasons_ru.append(
            "К аренде транспортного средства не применяются правила о преимущественном праве на "
            "заключение договора на новый срок (статьи 632 и 642 ГК РФ)."
        )
    if truth(maintenance_duty_breached):
        reasons_ru.append(
            "Обязанность по поддержанию надлежащего состояния транспортного средства, включая "
            "текущий и капитальный ремонт, не исполнена: при аренде с экипажем она лежит на "
            "арендодателе, без экипажа — на арендаторе (статьи 634 и 644 ГК РФ)."
        )
    if truth(crew_service_shortfall):
        reasons_ru.append(
            "При аренде с экипажем арендодатель обязан обеспечить управление транспортным "
            "средством и его надлежащую техническую эксплуатацию силами экипажа; услуги экипажа "
            "не предоставлены надлежащим образом (статья 635 ГК РФ)."
        )
    if truth(operating_cost_misallocation):
        reasons_ru.append(
            "Расходы по эксплуатации транспортного средства распределены неверно: коммерческая "
            "эксплуатация при аренде с экипажем и содержание при аренде без экипажа отнесены не "
            "на ту сторону (статьи 636 и 646 ГК РФ)."
        )
    if truth(insurance_duty_breached):
        reasons_ru.append(
            "Обязанность по страхованию транспортного средства и ответственности не исполнена: "
            "при аренде с экипажем она лежит на арендодателе, без экипажа — на арендаторе "
            "(статьи 637 и 646 ГК РФ)."
        )
    if truth(sublease_restriction_invalid):
        reasons_ru.append(
            "Арендатор вправе без согласия арендодателя сдавать транспортное средство в "
            "субаренду, если иное не предусмотрено договором; ограничение неправомерно "
            "(статьи 638 и 647 ГК РФ)."
        )
    if truth(third_party_liability_misassigned):
        reasons_ru.append(
            "Ответственность за вред, причинённый третьим лицам транспортным средством, "
            "распределена неверно: при аренде с экипажем её несёт арендодатель, без экипажа — "
            "арендатор (статьи 640 и 648 ГК РФ)."
        )
    return VehicleLeaseEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        vehicle_lease_qualified=truth(vehicle_lease_qualified),
        form_requirement_violated=truth(form_requirement_violated),
        renewal_right_not_available=truth(renewal_right_not_available),
        maintenance_duty_breached=truth(maintenance_duty_breached),
        crew_service_shortfall=truth(crew_service_shortfall),
        operating_cost_misallocation=truth(operating_cost_misallocation),
        insurance_duty_breached=truth(insurance_duty_breached),
        sublease_restriction_invalid=truth(sublease_restriction_invalid),
        third_party_liability_misassigned=truth(third_party_liability_misassigned),
        requires_human_vehicle_lease_assessment=truth(requires_human_vehicle_lease_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила об аренде транспортных средств и не "
            "заменяет судебную оценку.",
            "Размер платы, распределение конкретных расходов и объём ответственности "
            "оцениваются экспертом и судом (статьи 636, 639 и 648 ГК РФ).",
        ],
    )
