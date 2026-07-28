from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


BUILDING_LEASE_EVIDENCE_SCHEMA_VERSION = "contracts.building-lease-evidence.v0"
BUILDING_LEASE_MAPPING_VERSION = "contracts-reviewed-building-lease-to-facts-v0"
BUILDING_LEASE_MODEL_VERSION = "contracts-building-lease-articles-650-655-v0"


class BuildingLeaseEvidencePredicate(str, Enum):
    # Понятие, форма и регистрация (статьи 650 и 651 ГК РФ).
    BUILDING_LEASED_FOR_TEMPORARY_USE = "building_leased_for_temporary_use"
    SINGLE_WRITTEN_DOCUMENT_MISSING = "single_written_document_missing"
    LEASE_TERM_AT_LEAST_ONE_YEAR = "lease_term_at_least_one_year"
    STATE_REGISTRATION_MISSING = "state_registration_missing"
    # Права на земельный участок (статьи 652 и 653 ГК РФ).
    LAND_RIGHTS_NOT_TRANSFERRED = "land_rights_not_transferred"
    LAND_OWNERSHIP_CHANGED = "land_ownership_changed"
    LAND_USE_RIGHT_DENIED_AFTER_CHANGE = "land_use_right_denied_after_change"
    # Арендная плата, передача и возврат (статьи 654 и 655 ГК РФ).
    AGREED_RENT_AMOUNT_MISSING = "agreed_rent_amount_missing"
    TRANSFER_DEED_MISSING = "transfer_deed_missing"
    RETURN_DEED_MISSING = "return_deed_missing"


REQUIRED_BUILDING_LEASE_PREDICATES = frozenset(BuildingLeaseEvidencePredicate)


class BuildingLeaseEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: BuildingLeaseEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedBuildingLeaseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = BUILDING_LEASE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[BuildingLeaseEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedBuildingLeaseEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Building-lease evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Building-lease evidence contains duplicate legal source refs.")
        return self


class BuildingLeaseFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    building_leased_for_temporary_use: bool
    single_written_document_missing: bool
    lease_term_at_least_one_year: bool
    state_registration_missing: bool
    land_rights_not_transferred: bool
    land_ownership_changed: bool
    land_use_right_denied_after_change: bool
    agreed_rent_amount_missing: bool
    transfer_deed_missing: bool
    return_deed_missing: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "BuildingLeaseFactSet":
        if self.land_use_right_denied_after_change and not self.land_ownership_changed:
            raise ValueError(
                "Отказ в сохранении права пользования участком относится только к случаю "
                "перехода права собственности на земельный участок."
            )
        return self


class BuildingLeaseFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class BuildingLeaseEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: BuildingLeaseFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[BuildingLeaseFactProvenance] = Field(default_factory=list)


class BuildingLeaseConstraintSet(BaseModel):
    id: str
    model_version: str = BUILDING_LEASE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class BuildingLeaseEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    building_lease_qualified: bool
    form_defect_makes_void: bool
    registration_required_and_missing: bool
    land_rights_not_conveyed: bool
    land_use_right_preserved: bool
    rent_term_not_agreed: bool
    transfer_not_documented: bool
    return_not_documented: bool
    requires_human_building_lease_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_building_lease_evidence(
    evidence: ReviewedBuildingLeaseEvidence,
) -> BuildingLeaseEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Building-lease evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Building-lease evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_BUILDING_LEASE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed building-lease evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_BUILDING_LEASE_PREDICATES
    }
    return BuildingLeaseEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=BUILDING_LEASE_MAPPING_VERSION,
        facts=BuildingLeaseFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            BuildingLeaseFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_BUILDING_LEASE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_building_lease_constraint_set(
    mapping: BuildingLeaseEvidenceMappingResult,
) -> BuildingLeaseConstraintSet:
    return BuildingLeaseConstraintSet(
        id=f"building-lease-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "building_lease_qualified == building_leased_for_temporary_use",
            "form_defect_makes_void == building_lease_qualified AND single_written_document_missing",
            "registration_required_and_missing == building_lease_qualified AND lease_term_at_least_one_year AND state_registration_missing",
            "land_rights_not_conveyed == building_lease_qualified AND land_rights_not_transferred",
            "land_use_right_preserved == building_lease_qualified AND land_ownership_changed AND land_use_right_denied_after_change",
            "rent_term_not_agreed == building_lease_qualified AND agreed_rent_amount_missing",
            "transfer_not_documented == building_lease_qualified AND transfer_deed_missing",
            "return_not_documented == building_lease_qualified AND return_deed_missing",
            "requires_human_building_lease_assessment == form_defect_makes_void OR registration_required_and_missing OR land_rights_not_conveyed OR land_use_right_preserved OR rent_term_not_agreed OR transfer_not_documented OR return_not_documented",
        ],
    )


def evaluate_building_lease_constraints(
    constraint_set: BuildingLeaseConstraintSet,
    facts: BuildingLeaseFactSet,
) -> BuildingLeaseEvaluation:
    variables = {field_name: Bool(field_name) for field_name in BuildingLeaseFactSet.model_fields}
    building_lease_qualified = Bool("building_lease_qualified")
    form_defect_makes_void = Bool("form_defect_makes_void")
    registration_required_and_missing = Bool("registration_required_and_missing")
    land_rights_not_conveyed = Bool("land_rights_not_conveyed")
    land_use_right_preserved = Bool("land_use_right_preserved")
    rent_term_not_agreed = Bool("rent_term_not_agreed")
    transfer_not_documented = Bool("transfer_not_documented")
    return_not_documented = Bool("return_not_documented")
    requires_human_building_lease_assessment = Bool("requires_human_building_lease_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(building_lease_qualified == variables["building_leased_for_temporary_use"])
    solver.add(
        form_defect_makes_void
        == And(building_lease_qualified, variables["single_written_document_missing"])
    )
    solver.add(
        registration_required_and_missing
        == And(
            building_lease_qualified,
            variables["lease_term_at_least_one_year"],
            variables["state_registration_missing"],
        )
    )
    solver.add(
        land_rights_not_conveyed
        == And(building_lease_qualified, variables["land_rights_not_transferred"])
    )
    solver.add(
        land_use_right_preserved
        == And(
            building_lease_qualified,
            variables["land_ownership_changed"],
            variables["land_use_right_denied_after_change"],
        )
    )
    solver.add(
        rent_term_not_agreed
        == And(building_lease_qualified, variables["agreed_rent_amount_missing"])
    )
    solver.add(
        transfer_not_documented == And(building_lease_qualified, variables["transfer_deed_missing"])
    )
    solver.add(
        return_not_documented == And(building_lease_qualified, variables["return_deed_missing"])
    )
    solver.add(
        requires_human_building_lease_assessment
        == Or(
            form_defect_makes_void,
            registration_required_and_missing,
            land_rights_not_conveyed,
            land_use_right_preserved,
            rent_term_not_agreed,
            transfer_not_documented,
            return_not_documented,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return BuildingLeaseEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            building_lease_qualified=False,
            form_defect_makes_void=False,
            registration_required_and_missing=False,
            land_rights_not_conveyed=False,
            land_use_right_preserved=False,
            rent_term_not_agreed=False,
            transfer_not_documented=False,
            return_not_documented=False,
            requires_human_building_lease_assessment=True,
            reasons_ru=["Набор фактов об аренде здания или сооружения противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как аренда здания или сооружения: арендодатель обязуется "
            "передать арендатору во временное владение и пользование здание или сооружение "
            "(статья 650 ГК РФ)."
            if truth(building_lease_qualified)
            else "Отношения не квалифицированы как аренда здания или сооружения."
        ),
    ]
    if truth(form_defect_makes_void):
        reasons_ru.append(
            "Договор аренды здания или сооружения заключается в письменной форме путём "
            "составления одного документа, подписанного сторонами; несоблюдение формы влечёт "
            "недействительность договора (статья 651 ГК РФ)."
        )
    if truth(registration_required_and_missing):
        reasons_ru.append(
            "Договор аренды здания или сооружения, заключённый на срок не менее года, подлежит "
            "государственной регистрации и считается заключённым с момента такой регистрации "
            "(статья 651 ГК РФ)."
        )
    if truth(land_rights_not_conveyed):
        reasons_ru.append(
            "Одновременно с передачей прав владения и пользования зданием или сооружением "
            "арендатору передаются права на ту часть земельного участка, которая занята "
            "недвижимостью и необходима для её использования (статья 652 ГК РФ)."
        )
    if truth(land_use_right_preserved):
        reasons_ru.append(
            "При переходе права собственности на земельный участок к другому лицу за арендатором "
            "здания или сооружения сохраняется право пользования частью участка на прежних "
            "условиях (статья 653 ГК РФ)."
        )
    if truth(rent_term_not_agreed):
        reasons_ru.append(
            "Условие о размере арендной платы является существенным: при его отсутствии договор "
            "аренды здания или сооружения считается незаключённым, а правила определения цены по "
            "сравнимым обстоятельствам не применяются (статья 654 ГК РФ)."
        )
    if truth(transfer_not_documented):
        reasons_ru.append(
            "Передача здания или сооружения осуществляется по передаточному акту или иному "
            "документу о передаче, подписанному сторонами; уклонение от подписания считается "
            "отказом от исполнения обязанности (статья 655 ГК РФ)."
        )
    if truth(return_not_documented):
        reasons_ru.append(
            "При прекращении договора здание или сооружение возвращается арендодателю по "
            "передаточному акту или иному документу о передаче (статья 655 ГК РФ)."
        )
    return BuildingLeaseEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        building_lease_qualified=truth(building_lease_qualified),
        form_defect_makes_void=truth(form_defect_makes_void),
        registration_required_and_missing=truth(registration_required_and_missing),
        land_rights_not_conveyed=truth(land_rights_not_conveyed),
        land_use_right_preserved=truth(land_use_right_preserved),
        rent_term_not_agreed=truth(rent_term_not_agreed),
        transfer_not_documented=truth(transfer_not_documented),
        return_not_documented=truth(return_not_documented),
        requires_human_building_lease_assessment=truth(requires_human_building_lease_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила об аренде зданий и сооружений и не "
            "заменяет судебную оценку.",
            "Размер арендной платы, состав передаваемых прав на земельный участок и последствия "
            "уклонения от подписания акта оцениваются экспертом и судом (статьи 652, 654 и 655 "
            "ГК РФ).",
        ],
    )
