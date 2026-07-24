from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


TEMPORAL_EFFECT_EVIDENCE_SCHEMA_VERSION = "contracts.temporal-effect-evidence.v0"
TEMPORAL_EFFECT_MAPPING_VERSION = "contracts-reviewed-temporal-effect-to-facts-v0"
TEMPORAL_EFFECT_MODEL_VERSION = "contracts-temporal-effect-articles-425-433-v0"


class TemporalEffectEvidencePredicate(str, Enum):
    # Момент заключения договора (статья 433 ГК РФ).
    ACCEPTANCE_RECEIVED_BY_OFFEROR = "acceptance_received_by_offeror"
    CONTRACT_REQUIRES_PROPERTY_DELIVERY = "contract_requires_property_delivery"
    PROPERTY_DELIVERED = "property_delivered"
    CONTRACT_REQUIRES_STATE_REGISTRATION = "contract_requires_state_registration"
    STATE_REGISTRATION_COMPLETED = "state_registration_completed"
    # Действие договора во времени (статья 425 ГК РФ).
    EFFECTIVENESS_DEFERRED_BY_TERMS = "effectiveness_deferred_by_terms"
    DEFERRED_EFFECTIVENESS_CONDITION_MET = "deferred_effectiveness_condition_met"
    RETROACTIVE_APPLICATION_AGREED = "retroactive_application_agreed"
    PRIOR_RELATIONS_EXIST = "prior_relations_exist"
    TERM_END_DEFINED = "term_end_defined"
    TERM_END_REACHED = "term_end_reached"
    TERMS_PROVIDE_OBLIGATIONS_END_ON_TERM = "terms_provide_obligations_end_on_term"
    PERFORMANCE_COMPLETED = "performance_completed"
    BREACH_COMMITTED_DURING_TERM = "breach_committed_during_term"


REQUIRED_TEMPORAL_EFFECT_PREDICATES = frozenset(TemporalEffectEvidencePredicate)


class TemporalEffectEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: TemporalEffectEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedTemporalEffectEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = TEMPORAL_EFFECT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[TemporalEffectEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedTemporalEffectEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Temporal-effect evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Temporal-effect evidence contains duplicate legal source refs.")
        return self


class TemporalEffectFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    acceptance_received_by_offeror: bool
    contract_requires_property_delivery: bool
    property_delivered: bool
    contract_requires_state_registration: bool
    state_registration_completed: bool
    effectiveness_deferred_by_terms: bool
    deferred_effectiveness_condition_met: bool
    retroactive_application_agreed: bool
    prior_relations_exist: bool
    term_end_defined: bool
    term_end_reached: bool
    terms_provide_obligations_end_on_term: bool
    performance_completed: bool
    breach_committed_during_term: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "TemporalEffectFactSet":
        if self.deferred_effectiveness_condition_met and not self.effectiveness_deferred_by_terms:
            raise ValueError("Deferred-effectiveness condition requires deferred effectiveness.")
        if self.state_registration_completed and not self.contract_requires_state_registration:
            raise ValueError("State registration cannot be completed when it is not required.")
        if self.term_end_reached and not self.term_end_defined:
            raise ValueError("Term end cannot be reached when no term end is defined.")
        return self


class TemporalEffectFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class TemporalEffectEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: TemporalEffectFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[TemporalEffectFactProvenance] = Field(default_factory=list)


class TemporalEffectConstraintSet(BaseModel):
    id: str
    model_version: str = TEMPORAL_EFFECT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class TemporalEffectEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    conclusion_moment_established: bool
    contract_in_force: bool
    retroactive_effect_applies: bool
    term_expired: bool
    future_obligations_discharged_by_term_end: bool
    liability_preserved_after_term: bool
    registration_pending: bool
    deferred_effect_pending: bool
    requires_human_temporal_effect_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_temporal_effect_evidence(
    evidence: ReviewedTemporalEffectEvidence,
) -> TemporalEffectEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Temporal-effect evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Temporal-effect evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_TEMPORAL_EFFECT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed temporal-effect evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_TEMPORAL_EFFECT_PREDICATES
    }
    return TemporalEffectEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=TEMPORAL_EFFECT_MAPPING_VERSION,
        facts=TemporalEffectFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            TemporalEffectFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_TEMPORAL_EFFECT_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_temporal_effect_constraint_set(
    mapping: TemporalEffectEvidenceMappingResult,
) -> TemporalEffectConstraintSet:
    return TemporalEffectConstraintSet(
        id=f"temporal-effect-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "conclusion_moment_established == acceptance_received_by_offeror AND (NOT contract_requires_property_delivery OR property_delivered) AND (NOT contract_requires_state_registration OR state_registration_completed)",
            "contract_in_force == conclusion_moment_established AND (NOT effectiveness_deferred_by_terms OR deferred_effectiveness_condition_met)",
            "retroactive_effect_applies == contract_in_force AND retroactive_application_agreed AND prior_relations_exist",
            "term_expired == term_end_defined AND term_end_reached",
            "future_obligations_discharged_by_term_end == term_expired AND terms_provide_obligations_end_on_term AND NOT performance_completed",
            "liability_preserved_after_term == term_expired AND breach_committed_during_term",
            "registration_pending == contract_requires_state_registration AND NOT state_registration_completed",
            "deferred_effect_pending == effectiveness_deferred_by_terms AND NOT deferred_effectiveness_condition_met",
            "requires_human_temporal_effect_assessment == registration_pending OR deferred_effect_pending OR (retroactive_application_agreed AND NOT prior_relations_exist)",
        ],
    )


def evaluate_temporal_effect_constraints(
    constraint_set: TemporalEffectConstraintSet,
    facts: TemporalEffectFactSet,
) -> TemporalEffectEvaluation:
    variables = {field_name: Bool(field_name) for field_name in TemporalEffectFactSet.model_fields}
    conclusion_moment_established = Bool("conclusion_moment_established")
    contract_in_force = Bool("contract_in_force")
    retroactive_effect_applies = Bool("retroactive_effect_applies")
    term_expired = Bool("term_expired")
    future_obligations_discharged_by_term_end = Bool("future_obligations_discharged_by_term_end")
    liability_preserved_after_term = Bool("liability_preserved_after_term")
    registration_pending = Bool("registration_pending")
    deferred_effect_pending = Bool("deferred_effect_pending")
    requires_human_temporal_effect_assessment = Bool("requires_human_temporal_effect_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        conclusion_moment_established
        == And(
            variables["acceptance_received_by_offeror"],
            Or(
                Not(variables["contract_requires_property_delivery"]),
                variables["property_delivered"],
            ),
            Or(
                Not(variables["contract_requires_state_registration"]),
                variables["state_registration_completed"],
            ),
        )
    )
    solver.add(
        contract_in_force
        == And(
            conclusion_moment_established,
            Or(
                Not(variables["effectiveness_deferred_by_terms"]),
                variables["deferred_effectiveness_condition_met"],
            ),
        )
    )
    solver.add(
        retroactive_effect_applies
        == And(
            contract_in_force,
            variables["retroactive_application_agreed"],
            variables["prior_relations_exist"],
        )
    )
    solver.add(term_expired == And(variables["term_end_defined"], variables["term_end_reached"]))
    solver.add(
        future_obligations_discharged_by_term_end
        == And(
            term_expired,
            variables["terms_provide_obligations_end_on_term"],
            Not(variables["performance_completed"]),
        )
    )
    solver.add(
        liability_preserved_after_term
        == And(term_expired, variables["breach_committed_during_term"])
    )
    solver.add(
        registration_pending
        == And(
            variables["contract_requires_state_registration"],
            Not(variables["state_registration_completed"]),
        )
    )
    solver.add(
        deferred_effect_pending
        == And(
            variables["effectiveness_deferred_by_terms"],
            Not(variables["deferred_effectiveness_condition_met"]),
        )
    )
    solver.add(
        requires_human_temporal_effect_assessment
        == Or(
            registration_pending,
            deferred_effect_pending,
            And(
                variables["retroactive_application_agreed"],
                Not(variables["prior_relations_exist"]),
            ),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return TemporalEffectEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            conclusion_moment_established=False,
            contract_in_force=False,
            retroactive_effect_applies=False,
            term_expired=False,
            future_obligations_discharged_by_term_end=False,
            liability_preserved_after_term=False,
            registration_pending=False,
            deferred_effect_pending=False,
            requires_human_temporal_effect_assessment=True,
            reasons_ru=["Набор фактов о действии договора во времени противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    in_force = truth(contract_in_force)
    reasons_ru = [
        (
            "Момент заключения договора установлен по правилам статьи 433 ГК РФ."
            if truth(conclusion_moment_established)
            else "Момент заключения договора по статье 433 ГК РФ не установлен."
        ),
        (
            "Договор вступил в силу и обязателен для сторон."
            if in_force
            else "Вступление договора в силу не подтверждено."
        ),
    ]
    if truth(retroactive_effect_applies):
        reasons_ru.append(
            "Условия договора распространены на отношения, возникшие до его заключения."
        )
    if truth(term_expired):
        reasons_ru.append("Срок действия договора истек.")
    if truth(future_obligations_discharged_by_term_end):
        reasons_ru.append("Окончание срока действия прекращает неисполненные обязательства сторон.")
    if truth(liability_preserved_after_term):
        reasons_ru.append(
            "Окончание срока действия не освобождает от ответственности за допущенное нарушение."
        )
    if truth(registration_pending):
        reasons_ru.append("Договор подлежит государственной регистрации, которая не завершена.")
    if truth(deferred_effect_pending):
        reasons_ru.append("Отлагательное условие вступления договора в силу не наступило.")
    return TemporalEffectEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        conclusion_moment_established=truth(conclusion_moment_established),
        contract_in_force=in_force,
        retroactive_effect_applies=truth(retroactive_effect_applies),
        term_expired=truth(term_expired),
        future_obligations_discharged_by_term_end=truth(future_obligations_discharged_by_term_end),
        liability_preserved_after_term=truth(liability_preserved_after_term),
        registration_pending=truth(registration_pending),
        deferred_effect_pending=truth(deferred_effect_pending),
        requires_human_temporal_effect_assessment=truth(requires_human_temporal_effect_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила действия договора во времени и не заменяет судебную оценку.",
            "Момент заключения, срок действия и последствия его истечения оцениваются экспертом.",
        ],
    )
