from pydantic import BaseModel, Field

from causa.governance.candidate_types import CandidateType
from causa.governance.pipeline import GovernanceStage


class GovernanceProfile(BaseModel):
    candidate_type: CandidateType
    required_stages: list[GovernanceStage] = Field(default_factory=list)
    requires_sandbox: bool = False
    requires_cross_review: bool = False
    expiration_days: int | None = None


GOVERNANCE_PROFILES: dict[CandidateType, GovernanceProfile] = {
    CandidateType.META_PRINCIPLE: GovernanceProfile(
        candidate_type=CandidateType.META_PRINCIPLE,
        required_stages=[
            GovernanceStage.TYPE_CLASSIFICATION,
            GovernanceStage.FORMAL_CHECK,
            GovernanceStage.SOURCE_CHECK,
            GovernanceStage.BENCHMARK_CHECK,
            GovernanceStage.RED_TEAM_CHECK,
            GovernanceStage.EXPERT_REVIEW,
            GovernanceStage.CROSS_REVIEW,
            GovernanceStage.SANDBOX,
        ],
        requires_sandbox=True,
        requires_cross_review=True,
        expiration_days=540,
    ),
    CandidateType.CALIBRATION_RULE: GovernanceProfile(
        candidate_type=CandidateType.CALIBRATION_RULE,
        required_stages=[
            GovernanceStage.TYPE_CLASSIFICATION,
            GovernanceStage.BENCHMARK_CHECK,
            GovernanceStage.EXPERT_REVIEW,
        ],
        expiration_days=365,
    ),
    CandidateType.GAP_HEURISTIC: GovernanceProfile(
        candidate_type=CandidateType.GAP_HEURISTIC,
        required_stages=[
            GovernanceStage.TYPE_CLASSIFICATION,
            GovernanceStage.EXPERT_REVIEW,
        ],
        expiration_days=365,
    ),
    CandidateType.CONFLICT_RESOLUTION_PATTERN: GovernanceProfile(
        candidate_type=CandidateType.CONFLICT_RESOLUTION_PATTERN,
        required_stages=[
            GovernanceStage.TYPE_CLASSIFICATION,
            GovernanceStage.FORMAL_CHECK,
            GovernanceStage.SOURCE_CHECK,
            GovernanceStage.BENCHMARK_CHECK,
            GovernanceStage.RED_TEAM_CHECK,
            GovernanceStage.EXPERT_REVIEW,
            GovernanceStage.SANDBOX,
        ],
        requires_sandbox=True,
        expiration_days=540,
    ),
    CandidateType.COUNTERFACTUAL_SENSITIVITY_PATTERN: GovernanceProfile(
        candidate_type=CandidateType.COUNTERFACTUAL_SENSITIVITY_PATTERN,
        required_stages=[
            GovernanceStage.TYPE_CLASSIFICATION,
            GovernanceStage.BENCHMARK_CHECK,
            GovernanceStage.EXPERT_REVIEW,
        ],
        expiration_days=365,
    ),
    CandidateType.ARGUMENT_TEMPLATE: GovernanceProfile(
        candidate_type=CandidateType.ARGUMENT_TEMPLATE,
        required_stages=[
            GovernanceStage.TYPE_CLASSIFICATION,
            GovernanceStage.RED_TEAM_CHECK,
            GovernanceStage.EXPERT_REVIEW,
        ],
        expiration_days=365,
    ),
    CandidateType.TRANSLATION_PATTERN: GovernanceProfile(
        candidate_type=CandidateType.TRANSLATION_PATTERN,
        required_stages=[
            GovernanceStage.TYPE_CLASSIFICATION,
            GovernanceStage.BENCHMARK_CHECK,
            GovernanceStage.EXPERT_REVIEW,
        ],
        expiration_days=365,
    ),
}


def get_governance_profile(candidate_type: CandidateType) -> GovernanceProfile:
    return GOVERNANCE_PROFILES[candidate_type]
