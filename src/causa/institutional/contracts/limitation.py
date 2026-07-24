from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


LIMITATION_EVIDENCE_SCHEMA_VERSION = "contracts.limitation-evidence.v0"
LIMITATION_MAPPING_VERSION = "contracts-reviewed-limitation-to-facts-v0"
LIMITATION_MODEL_VERSION = "contracts-limitation-articles-195-208-v0"


class LimitationEvidencePredicate(str, Enum):
    # Предмет и начало течения (статьи 195, 200, 208 ГК РФ).
    CLAIM_SUBJECT_TO_LIMITATION = "claim_subject_to_limitation"
    RIGHT_VIOLATION_AND_DEFENDANT_KNOWN = "right_violation_and_defendant_known"
    FIXED_PERFORMANCE_TERM_EXPIRED = "fixed_performance_term_expired"
    # Общий и специальный срок, объективный предел (статьи 196, 197 ГК РФ).
    GENERAL_THREE_YEAR_TERM_ELAPSED = "general_three_year_term_elapsed"
    SPECIAL_TERM_APPLIES = "special_term_applies"
    SPECIAL_TERM_ELAPSED = "special_term_elapsed"
    OBJECTIVE_TEN_YEAR_LIMIT_EXCEEDED = "objective_ten_year_limit_exceeded"
    # Приостановление, перерыв и период судебной защиты (статьи 202, 203, 204 ГК РФ).
    SUSPENSION_GROUND_IN_FINAL_SIX_MONTHS = "suspension_ground_in_final_six_months"
    DEBTOR_ACKNOWLEDGED_DEBT = "debtor_acknowledged_debt"
    JUDICIAL_PROTECTION_PERIOD_ONGOING = "judicial_protection_period_ongoing"
    # Заявление стороны, восстановление, дополнительные требования (статьи 199, 205, 207 ГК РФ).
    LIMITATION_PLEADED_BY_PARTY_BEFORE_JUDGMENT = "limitation_pleaded_by_party_before_judgment"
    CLAIMANT_IS_INDIVIDUAL_WITH_VALID_EXCUSE = "claimant_is_individual_with_valid_excuse"
    IS_ADDITIONAL_CLAIM = "is_additional_claim"
    MAIN_CLAIM_TIME_BARRED = "main_claim_time_barred"


REQUIRED_LIMITATION_PREDICATES = frozenset(LimitationEvidencePredicate)


class LimitationEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: LimitationEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedLimitationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = LIMITATION_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[LimitationEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedLimitationEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Limitation evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Limitation evidence contains duplicate legal source refs.")
        return self


class LimitationFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_subject_to_limitation: bool
    right_violation_and_defendant_known: bool
    fixed_performance_term_expired: bool
    general_three_year_term_elapsed: bool
    special_term_applies: bool
    special_term_elapsed: bool
    objective_ten_year_limit_exceeded: bool
    suspension_ground_in_final_six_months: bool
    debtor_acknowledged_debt: bool
    judicial_protection_period_ongoing: bool
    limitation_pleaded_by_party_before_judgment: bool
    claimant_is_individual_with_valid_excuse: bool
    is_additional_claim: bool
    main_claim_time_barred: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "LimitationFactSet":
        if self.special_term_elapsed and not self.special_term_applies:
            raise ValueError("Special limitation term cannot elapse when it does not apply.")
        if self.main_claim_time_barred and not self.is_additional_claim:
            raise ValueError("Main-claim bar is recorded only for an additional claim.")
        return self


class LimitationFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class LimitationEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: LimitationFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[LimitationFactProvenance] = Field(default_factory=list)


class LimitationConstraintSet(BaseModel):
    id: str
    model_version: str = LIMITATION_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class LimitationEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    limitation_period_started: bool
    basic_term_elapsed: bool
    limitation_running_paused: bool
    limitation_period_expired: bool
    objective_limit_barred: bool
    limitation_reset_by_acknowledgement: bool
    limitation_suspended: bool
    limitation_defense_available: bool
    limitation_restorable: bool
    additional_claim_barred_with_main: bool
    claim_not_subject_to_limitation: bool
    requires_human_limitation_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_limitation_evidence(
    evidence: ReviewedLimitationEvidence,
) -> LimitationEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Limitation evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Limitation evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_LIMITATION_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed limitation evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_LIMITATION_PREDICATES
    }
    return LimitationEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=LIMITATION_MAPPING_VERSION,
        facts=LimitationFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            LimitationFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_LIMITATION_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_limitation_constraint_set(
    mapping: LimitationEvidenceMappingResult,
) -> LimitationConstraintSet:
    return LimitationConstraintSet(
        id=f"limitation-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "limitation_period_started == right_violation_and_defendant_known OR fixed_performance_term_expired",
            "basic_term_elapsed == (special_term_applies AND special_term_elapsed) OR (NOT special_term_applies AND general_three_year_term_elapsed)",
            "limitation_running_paused == suspension_ground_in_final_six_months OR debtor_acknowledged_debt OR judicial_protection_period_ongoing",
            "limitation_period_expired == claim_subject_to_limitation AND limitation_period_started AND ((basic_term_elapsed AND NOT limitation_running_paused) OR objective_ten_year_limit_exceeded)",
            "objective_limit_barred == claim_subject_to_limitation AND objective_ten_year_limit_exceeded",
            "limitation_reset_by_acknowledgement == debtor_acknowledged_debt",
            "limitation_suspended == suspension_ground_in_final_six_months",
            "limitation_defense_available == limitation_period_expired AND limitation_pleaded_by_party_before_judgment",
            "limitation_restorable == limitation_period_expired AND claimant_is_individual_with_valid_excuse",
            "additional_claim_barred_with_main == is_additional_claim AND main_claim_time_barred",
            "claim_not_subject_to_limitation == NOT claim_subject_to_limitation",
            "requires_human_limitation_assessment == limitation_restorable OR (limitation_period_expired AND NOT limitation_pleaded_by_party_before_judgment)",
        ],
    )


def evaluate_limitation_constraints(
    constraint_set: LimitationConstraintSet,
    facts: LimitationFactSet,
) -> LimitationEvaluation:
    variables = {field_name: Bool(field_name) for field_name in LimitationFactSet.model_fields}
    limitation_period_started = Bool("limitation_period_started")
    basic_term_elapsed = Bool("basic_term_elapsed")
    limitation_running_paused = Bool("limitation_running_paused")
    limitation_period_expired = Bool("limitation_period_expired")
    objective_limit_barred = Bool("objective_limit_barred")
    limitation_reset_by_acknowledgement = Bool("limitation_reset_by_acknowledgement")
    limitation_suspended = Bool("limitation_suspended")
    limitation_defense_available = Bool("limitation_defense_available")
    limitation_restorable = Bool("limitation_restorable")
    additional_claim_barred_with_main = Bool("additional_claim_barred_with_main")
    claim_not_subject_to_limitation = Bool("claim_not_subject_to_limitation")
    requires_human_limitation_assessment = Bool("requires_human_limitation_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        limitation_period_started
        == Or(
            variables["right_violation_and_defendant_known"],
            variables["fixed_performance_term_expired"],
        )
    )
    solver.add(
        basic_term_elapsed
        == Or(
            And(variables["special_term_applies"], variables["special_term_elapsed"]),
            And(
                Not(variables["special_term_applies"]),
                variables["general_three_year_term_elapsed"],
            ),
        )
    )
    solver.add(
        limitation_running_paused
        == Or(
            variables["suspension_ground_in_final_six_months"],
            variables["debtor_acknowledged_debt"],
            variables["judicial_protection_period_ongoing"],
        )
    )
    solver.add(
        limitation_period_expired
        == And(
            variables["claim_subject_to_limitation"],
            limitation_period_started,
            Or(
                And(basic_term_elapsed, Not(limitation_running_paused)),
                variables["objective_ten_year_limit_exceeded"],
            ),
        )
    )
    solver.add(
        objective_limit_barred
        == And(
            variables["claim_subject_to_limitation"],
            variables["objective_ten_year_limit_exceeded"],
        )
    )
    solver.add(limitation_reset_by_acknowledgement == variables["debtor_acknowledged_debt"])
    solver.add(limitation_suspended == variables["suspension_ground_in_final_six_months"])
    solver.add(
        limitation_defense_available
        == And(
            limitation_period_expired,
            variables["limitation_pleaded_by_party_before_judgment"],
        )
    )
    solver.add(
        limitation_restorable
        == And(
            limitation_period_expired,
            variables["claimant_is_individual_with_valid_excuse"],
        )
    )
    solver.add(
        additional_claim_barred_with_main
        == And(variables["is_additional_claim"], variables["main_claim_time_barred"])
    )
    solver.add(claim_not_subject_to_limitation == Not(variables["claim_subject_to_limitation"]))
    solver.add(
        requires_human_limitation_assessment
        == Or(
            limitation_restorable,
            And(
                limitation_period_expired,
                Not(variables["limitation_pleaded_by_party_before_judgment"]),
            ),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return LimitationEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            limitation_period_started=False,
            basic_term_elapsed=False,
            limitation_running_paused=False,
            limitation_period_expired=False,
            objective_limit_barred=False,
            limitation_reset_by_acknowledgement=False,
            limitation_suspended=False,
            limitation_defense_available=False,
            limitation_restorable=False,
            additional_claim_barred_with_main=False,
            claim_not_subject_to_limitation=False,
            requires_human_limitation_assessment=True,
            reasons_ru=["Набор фактов об исковой давности противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    expired = truth(limitation_period_expired)
    reasons_ru = [
        (
            "Срок исковой давности истек."
            if expired
            else "Истечение срока исковой давности не подтверждено."
        ),
    ]
    if truth(claim_not_subject_to_limitation):
        reasons_ru.append("На требование исковая давность не распространяется (статья 208 ГК РФ).")
    if truth(limitation_defense_available):
        reasons_ru.append(
            "Истекшая давность заявлена стороной и является основанием к отказу в иске "
            "(статья 199 ГК РФ)."
        )
    elif expired:
        reasons_ru.append(
            "Давность истекла, но сторона не заявила о ее применении до вынесения решения."
        )
    if truth(limitation_reset_by_acknowledgement):
        reasons_ru.append("Признание долга прерывает течение давности (статья 203 ГК РФ).")
    if truth(limitation_suspended):
        reasons_ru.append("Течение давности приостановлено (статья 202 ГК РФ).")
    if truth(objective_limit_barred):
        reasons_ru.append("Превышен предельный десятилетний срок (статья 196 ГК РФ).")
    if truth(limitation_restorable):
        reasons_ru.append(
            "Для гражданина при уважительной причине возможно восстановление срока "
            "(статья 205 ГК РФ)."
        )
    if truth(additional_claim_barred_with_main):
        reasons_ru.append(
            "Давность по дополнительному требованию истекает вместе с главным (статья 207 ГК РФ)."
        )
    return LimitationEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        limitation_period_started=truth(limitation_period_started),
        basic_term_elapsed=truth(basic_term_elapsed),
        limitation_running_paused=truth(limitation_running_paused),
        limitation_period_expired=expired,
        objective_limit_barred=truth(objective_limit_barred),
        limitation_reset_by_acknowledgement=truth(limitation_reset_by_acknowledgement),
        limitation_suspended=truth(limitation_suspended),
        limitation_defense_available=truth(limitation_defense_available),
        limitation_restorable=truth(limitation_restorable),
        additional_claim_barred_with_main=truth(additional_claim_barred_with_main),
        claim_not_subject_to_limitation=truth(claim_not_subject_to_limitation),
        requires_human_limitation_assessment=truth(requires_human_limitation_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила исковой давности и не заменяет судебную оценку.",
            "Момент начала течения, уважительность причин и применение давности судом оцениваются экспертом.",
        ],
    )
