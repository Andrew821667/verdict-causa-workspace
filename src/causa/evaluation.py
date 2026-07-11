from pydantic import BaseModel, Field

from causa.governance.failure_taxonomy import FailureType


class BenchmarkTask(BaseModel):
    id: str
    title: str
    institutional_package_id: str
    expected_source_refs: list[str] = Field(default_factory=list)
    authority_candidate_source_refs: list[str] = Field(default_factory=list)
    expected_authority_winner: str | None = None
    expected_authority_rules: list[str] = Field(default_factory=list)
    expected_failure_types: list[FailureType] = Field(default_factory=list)
    facts: dict[str, bool] = Field(default_factory=dict)
    temporal_facts: dict[str, str] = Field(default_factory=dict)
    expected_source_applicability: dict[str, bool] = Field(default_factory=dict)
    expected_breach_issue: bool | None = None
    expected_late_performance_issue: bool | None = None
    expected_defect_issue: bool | None = None
    expected_payment_default_issue: bool | None = None
    expected_damages_remedy_available: bool | None = None
    expected_causation_evidence_gap: bool | None = None
    expected_limitation_bar: bool | None = None
    required_warning_fragments: list[str] = Field(default_factory=list)


class BenchmarkTaskResult(BaseModel):
    task_id: str
    passed: bool
    breach_issue: bool | None = None
    late_performance_issue: bool | None = None
    defect_issue: bool | None = None
    payment_default_issue: bool | None = None
    damages_remedy_available: bool | None = None
    causation_evidence_gap: bool | None = None
    limitation_bar: bool | None = None
    source_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    temporal_reasons: list[str] = Field(default_factory=list)
    source_applicability_reasons: list[str] = Field(default_factory=list)
    authority_winner: str | None = None
    authority_reasons: list[str] = Field(default_factory=list)
    authority_rules: list[str] = Field(default_factory=list)
    authority_excluded_source_refs: list[str] = Field(default_factory=list)


class BenchmarkSuiteReport(BaseModel):
    id: str
    institutional_package_id: str
    total: int
    passed: int
    failed: int
    results: list[BenchmarkTaskResult] = Field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total


class PracticeUtilityObservation(BaseModel):
    id: str
    task_id: str
    time_to_useful_draft_minutes: float = Field(ge=0)
    accepted_argument_count: int = Field(ge=0)
    human_correction_count: int = Field(ge=0)
    reviewer_usefulness_rating: float = Field(ge=1, le=5)
    formally_smart_but_practically_useless: bool = False
    notes: list[str] = Field(default_factory=list)


class PracticeUtilityReport(BaseModel):
    id: str
    institutional_package_id: str
    baseline_kind: str
    total_observations: int
    average_time_to_useful_draft_minutes: float
    total_accepted_argument_count: int
    total_human_correction_count: int
    average_reviewer_usefulness_rating: float
    formally_smart_but_practically_useless_count: int
    observations: list[PracticeUtilityObservation] = Field(default_factory=list)


class RedTeamScenario(BaseModel):
    id: str
    title: str
    institutional_package_id: str
    unacceptable_outcome: str
    target_failure_type: FailureType
    attack_vector: str = ""
    required_guardrail_fragments: list[str] = Field(default_factory=list)
    attack_facts: dict[str, bool] = Field(default_factory=dict)
    unacceptable_constraint_field: str | None = None
    unacceptable_constraint_value: bool | None = None
    authority_candidate_source_refs: list[str] = Field(default_factory=list)
    authority_evaluation_date: str | None = None
    unacceptable_authority_winner: str | None = None
    attack_source_ref: str | None = None


class AdversarialAttackAttempt(BaseModel):
    id: str
    technique: str
    requested_outcome: str
    observed_outcome: str
    blocked: bool
    reasons: list[str] = Field(default_factory=list)


class GeneratedAdversarialAttack(BaseModel):
    id: str
    scenario_id: str
    generator_id: str
    generator_kind: str
    prompt: str
    attack_text: str
    requires_human_review: bool = True


class RedTeamScenarioResult(BaseModel):
    scenario_id: str
    blocked: bool
    target_failure_type: FailureType
    reasons: list[str] = Field(default_factory=list)
    reconstructed_attack: str | None = None
    adversarial_attempts: list[AdversarialAttackAttempt] = Field(default_factory=list)
    generated_attack: GeneratedAdversarialAttack | None = None


class RedTeamSuiteReport(BaseModel):
    id: str
    institutional_package_id: str
    total: int
    blocked: int
    unblocked: int
    results: list[RedTeamScenarioResult] = Field(default_factory=list)

    @property
    def block_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.blocked / self.total


class IncidentRecord(BaseModel):
    id: str
    failure_type: FailureType
    description: str
    trace_id: str | None = None
