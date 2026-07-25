from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


ADHESION_EVIDENCE_SCHEMA_VERSION = "contracts.adhesion-evidence.v0"
ADHESION_MAPPING_VERSION = "contracts-reviewed-adhesion-to-facts-v0"
ADHESION_MODEL_VERSION = "contracts-adhesion-article-428-v0"


class AdhesionEvidencePredicate(str, Enum):
    # Признаки договора присоединения и режим (пункты 1 и 3 статьи 428 ГК РФ).
    ADHESION_CONTRACT = "adhesion_contract"
    UNEQUAL_BARGAINING_POWER = "unequal_bargaining_power"
    TERMS_INDIVIDUALLY_NEGOTIATED = "terms_individually_negotiated"
    # Основания для изменения или расторжения (пункт 2 статьи 428 ГК РФ).
    DEPRIVES_USUAL_RIGHTS = "deprives_usual_rights"
    EXCLUDES_OR_LIMITS_OTHER_PARTY_LIABILITY = "excludes_or_limits_other_party_liability"
    MANIFESTLY_ONEROUS_TERMS = "manifestly_onerous_terms"
    # Ограничение для предпринимателя и заявленное требование (пункт 2 статьи 428 ГК РФ).
    ADHERING_PARTY_BUSINESS_ACTOR = "adhering_party_business_actor"
    ADHERING_PARTY_KNEW_TERMS = "adhering_party_knew_terms"
    MODIFICATION_OR_TERMINATION_DEMANDED = "modification_or_termination_demanded"


REQUIRED_ADHESION_PREDICATES = frozenset(AdhesionEvidencePredicate)


class AdhesionEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: AdhesionEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedAdhesionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = ADHESION_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[AdhesionEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedAdhesionEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Adhesion evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Adhesion evidence contains duplicate legal source refs.")
        return self


class AdhesionFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    adhesion_contract: bool
    unequal_bargaining_power: bool
    terms_individually_negotiated: bool
    deprives_usual_rights: bool
    excludes_or_limits_other_party_liability: bool
    manifestly_onerous_terms: bool
    adhering_party_business_actor: bool
    adhering_party_knew_terms: bool
    modification_or_termination_demanded: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "AdhesionFactSet":
        if self.adhesion_contract and self.terms_individually_negotiated:
            raise ValueError(
                "Договор присоединения исключает индивидуальное согласование его условий."
            )
        if self.adhering_party_knew_terms and not self.adhering_party_business_actor:
            raise ValueError(
                "Знание условий учитывается только для присоединившейся стороны — предпринимателя."
            )
        return self


class AdhesionFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class AdhesionEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: AdhesionFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[AdhesionFactProvenance] = Field(default_factory=list)


class AdhesionConstraintSet(BaseModel):
    id: str
    model_version: str = ADHESION_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class AdhesionEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    adhesion_regime_applies: bool
    grounds_for_relief_present: bool
    business_actor_bar: bool
    relief_available: bool
    requires_human_adhesion_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_adhesion_evidence(
    evidence: ReviewedAdhesionEvidence,
) -> AdhesionEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Adhesion evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Adhesion evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_ADHESION_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed adhesion evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_ADHESION_PREDICATES
    }
    return AdhesionEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=ADHESION_MAPPING_VERSION,
        facts=AdhesionFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            AdhesionFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_ADHESION_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_adhesion_constraint_set(
    mapping: AdhesionEvidenceMappingResult,
) -> AdhesionConstraintSet:
    return AdhesionConstraintSet(
        id=f"adhesion-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "adhesion_regime_applies == (adhesion_contract OR unequal_bargaining_power) AND NOT terms_individually_negotiated",
            "grounds_for_relief_present == deprives_usual_rights OR excludes_or_limits_other_party_liability OR manifestly_onerous_terms",
            "business_actor_bar == adhesion_regime_applies AND adhering_party_business_actor AND adhering_party_knew_terms",
            "relief_available == adhesion_regime_applies AND grounds_for_relief_present AND modification_or_termination_demanded AND NOT business_actor_bar",
            "requires_human_adhesion_assessment == relief_available OR (adhesion_regime_applies AND grounds_for_relief_present AND business_actor_bar)",
        ],
    )


def evaluate_adhesion_constraints(
    constraint_set: AdhesionConstraintSet,
    facts: AdhesionFactSet,
) -> AdhesionEvaluation:
    variables = {field_name: Bool(field_name) for field_name in AdhesionFactSet.model_fields}
    adhesion_regime_applies = Bool("adhesion_regime_applies")
    grounds_for_relief_present = Bool("grounds_for_relief_present")
    business_actor_bar = Bool("business_actor_bar")
    relief_available = Bool("relief_available")
    requires_human_adhesion_assessment = Bool("requires_human_adhesion_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        adhesion_regime_applies
        == And(
            Or(variables["adhesion_contract"], variables["unequal_bargaining_power"]),
            Not(variables["terms_individually_negotiated"]),
        )
    )
    solver.add(
        grounds_for_relief_present
        == Or(
            variables["deprives_usual_rights"],
            variables["excludes_or_limits_other_party_liability"],
            variables["manifestly_onerous_terms"],
        )
    )
    solver.add(
        business_actor_bar
        == And(
            adhesion_regime_applies,
            variables["adhering_party_business_actor"],
            variables["adhering_party_knew_terms"],
        )
    )
    solver.add(
        relief_available
        == And(
            adhesion_regime_applies,
            grounds_for_relief_present,
            variables["modification_or_termination_demanded"],
            Not(business_actor_bar),
        )
    )
    solver.add(
        requires_human_adhesion_assessment
        == Or(
            relief_available,
            And(adhesion_regime_applies, grounds_for_relief_present, business_actor_bar),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return AdhesionEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            adhesion_regime_applies=False,
            grounds_for_relief_present=False,
            business_actor_bar=False,
            relief_available=False,
            requires_human_adhesion_assessment=True,
            reasons_ru=["Набор фактов о договоре присоединения противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор подчинён режиму договора присоединения (статья 428 ГК РФ)."
            if truth(adhesion_regime_applies)
            else "Режим договора присоединения к договору не применяется."
        ),
    ]
    if truth(relief_available):
        reasons_ru.append(
            "Присоединившаяся сторона вправе требовать изменения или расторжения "
            "договора (пункт 2 статьи 428 ГК РФ)."
        )
    elif truth(business_actor_bar):
        reasons_ru.append(
            "Присоединившаяся при осуществлении предпринимательской деятельности "
            "сторона, знавшая условия, не вправе требовать изменения или расторжения "
            "по пункту 2 статьи 428 ГК РФ."
        )
    return AdhesionEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        adhesion_regime_applies=truth(adhesion_regime_applies),
        grounds_for_relief_present=truth(grounds_for_relief_present),
        business_actor_bar=truth(business_actor_bar),
        relief_available=truth(relief_available),
        requires_human_adhesion_assessment=truth(requires_human_adhesion_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о договоре присоединения и "
            "не заменяет судебную оценку.",
            "Обременительность условий и неравенство переговорных возможностей "
            "оцениваются экспертом и судом.",
        ],
    )
