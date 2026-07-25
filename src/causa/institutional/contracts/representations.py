from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


REPRESENTATIONS_EVIDENCE_SCHEMA_VERSION = "contracts.representations-evidence.v0"
REPRESENTATIONS_MAPPING_VERSION = "contracts-reviewed-representations-to-facts-v0"
REPRESENTATIONS_MODEL_VERSION = "contracts-representations-article-431-2-v0"


class RepresentationsEvidencePredicate(str, Enum):
    # Недостоверное заверение, имеющее значение (пункт 1 статьи 431.2 ГК РФ).
    REPRESENTATION_GIVEN = "representation_given"
    REPRESENTATION_MATERIAL = "representation_material"
    REPRESENTATION_FALSE = "representation_false"
    RELIANCE_BY_OTHER_PARTY = "reliance_by_other_party"
    # Основание ответственности и контекст (пункты 1 и 4 статьи 431.2 ГК РФ).
    GIVEN_IN_BUSINESS_OR_CORPORATE_CONTEXT = "given_in_business_or_corporate_context"
    REPRESENTOR_KNEW_OR_SHOULD_HAVE_KNOWN = "representor_knew_or_should_have_known"
    DAMAGES_OR_PENALTY_CLAIMED = "damages_or_penalty_claimed"
    # Существенность и обман (пункты 2 и 3 статьи 431.2 ГК РФ).
    REPRESENTATION_SIGNIFICANT = "representation_significant"
    DECEPTION_BY_FALSE_REPRESENTATION = "deception_by_false_representation"


REQUIRED_REPRESENTATIONS_PREDICATES = frozenset(RepresentationsEvidencePredicate)


class RepresentationsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: RepresentationsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedRepresentationsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = REPRESENTATIONS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[RepresentationsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedRepresentationsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Representations evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Representations evidence contains duplicate legal source refs.")
        return self


class RepresentationsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    representation_given: bool
    representation_material: bool
    representation_false: bool
    reliance_by_other_party: bool
    given_in_business_or_corporate_context: bool
    representor_knew_or_should_have_known: bool
    damages_or_penalty_claimed: bool
    representation_significant: bool
    deception_by_false_representation: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "RepresentationsFactSet":
        if self.representation_material and not self.representation_given:
            raise ValueError("Значение заверения невозможно без данного заверения.")
        if self.representation_false and not self.representation_given:
            raise ValueError("Недостоверность заверения невозможна без данного заверения.")
        if self.reliance_by_other_party and not self.representation_given:
            raise ValueError("Доверие к заверению невозможно без данного заверения.")
        if self.representation_significant and not self.representation_material:
            raise ValueError(
                "Существенное значение заверения предполагает его значение для договора."
            )
        if self.deception_by_false_representation and not self.representation_false:
            raise ValueError("Обман заверением невозможен без недостоверного заверения.")
        return self


class RepresentationsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class RepresentationsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: RepresentationsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[RepresentationsFactProvenance] = Field(default_factory=list)


class RepresentationsConstraintSet(BaseModel):
    id: str
    model_version: str = REPRESENTATIONS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class RepresentationsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    material_false_representation: bool
    liability_basis_present: bool
    damages_or_penalty_available: bool
    right_to_rescind: bool
    avoidance_for_deception_available: bool
    requires_human_representations_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_representations_evidence(
    evidence: ReviewedRepresentationsEvidence,
) -> RepresentationsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Representations evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Representations evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_REPRESENTATIONS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed representations evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_REPRESENTATIONS_PREDICATES
    }
    return RepresentationsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=REPRESENTATIONS_MAPPING_VERSION,
        facts=RepresentationsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            RepresentationsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_REPRESENTATIONS_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_representations_constraint_set(
    mapping: RepresentationsEvidenceMappingResult,
) -> RepresentationsConstraintSet:
    return RepresentationsConstraintSet(
        id=f"representations-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "material_false_representation == representation_given AND representation_material AND representation_false",
            "liability_basis_present == material_false_representation AND reliance_by_other_party AND (given_in_business_or_corporate_context OR representor_knew_or_should_have_known)",
            "damages_or_penalty_available == liability_basis_present AND damages_or_penalty_claimed",
            "right_to_rescind == liability_basis_present AND representation_significant",
            "avoidance_for_deception_available == material_false_representation AND reliance_by_other_party AND deception_by_false_representation",
            "requires_human_representations_assessment == liability_basis_present OR avoidance_for_deception_available",
        ],
    )


def evaluate_representations_constraints(
    constraint_set: RepresentationsConstraintSet,
    facts: RepresentationsFactSet,
) -> RepresentationsEvaluation:
    variables = {field_name: Bool(field_name) for field_name in RepresentationsFactSet.model_fields}
    material_false_representation = Bool("material_false_representation")
    liability_basis_present = Bool("liability_basis_present")
    damages_or_penalty_available = Bool("damages_or_penalty_available")
    right_to_rescind = Bool("right_to_rescind")
    avoidance_for_deception_available = Bool("avoidance_for_deception_available")
    requires_human_representations_assessment = Bool("requires_human_representations_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        material_false_representation
        == And(
            variables["representation_given"],
            variables["representation_material"],
            variables["representation_false"],
        )
    )
    solver.add(
        liability_basis_present
        == And(
            material_false_representation,
            variables["reliance_by_other_party"],
            Or(
                variables["given_in_business_or_corporate_context"],
                variables["representor_knew_or_should_have_known"],
            ),
        )
    )
    solver.add(
        damages_or_penalty_available
        == And(liability_basis_present, variables["damages_or_penalty_claimed"])
    )
    solver.add(
        right_to_rescind == And(liability_basis_present, variables["representation_significant"])
    )
    solver.add(
        avoidance_for_deception_available
        == And(
            material_false_representation,
            variables["reliance_by_other_party"],
            variables["deception_by_false_representation"],
        )
    )
    solver.add(
        requires_human_representations_assessment
        == Or(liability_basis_present, avoidance_for_deception_available)
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return RepresentationsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            material_false_representation=False,
            liability_basis_present=False,
            damages_or_penalty_available=False,
            right_to_rescind=False,
            avoidance_for_deception_available=False,
            requires_human_representations_assessment=True,
            reasons_ru=["Набор фактов о заверениях об обстоятельствах противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Дано недостоверное заверение, имеющее значение для договора "
            "(пункт 1 статьи 431.2 ГК РФ)."
            if truth(material_false_representation)
            else "Недостоверное заверение, имеющее значение для договора, не установлено."
        ),
    ]
    if truth(damages_or_penalty_available):
        reasons_ru.append(
            "Сторона, полагавшаяся на заверение, вправе требовать возмещения убытков или "
            "неустойки независимо от признания договора незаключённым или "
            "недействительным (пункт 1 статьи 431.2 ГК РФ)."
        )
    if truth(right_to_rescind):
        reasons_ru.append(
            "При существенном значении недостоверного заверения сторона вправе "
            "отказаться от договора (пункт 2 статьи 431.2 ГК РФ)."
        )
    if truth(avoidance_for_deception_available):
        reasons_ru.append(
            "Недостоверное заверение может служить основанием для оспаривания договора "
            "как совершённого под влиянием обмана (пункт 3 статьи 431.2, статья 179 ГК РФ)."
        )
    return RepresentationsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        material_false_representation=truth(material_false_representation),
        liability_basis_present=truth(liability_basis_present),
        damages_or_penalty_available=truth(damages_or_penalty_available),
        right_to_rescind=truth(right_to_rescind),
        avoidance_for_deception_available=truth(avoidance_for_deception_available),
        requires_human_representations_assessment=truth(requires_human_representations_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о заверениях об обстоятельствах "
            "и не заменяет судебную оценку.",
            "Существенность заверения, добросовестность сторон и обоснованность доверия "
            "оцениваются экспертом и судом.",
        ],
    )
