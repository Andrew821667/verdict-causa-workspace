from pydantic import BaseModel

from causa.management.risk_tiers import RiskTier
from causa.management.sla_modes import SLAMode


class ReviewRequirement(BaseModel):
    human_review: bool
    cross_review: bool = False
    replayable_trace: bool = True
    complete_provenance: bool = True


class PolicyMatrixEntry(BaseModel):
    mode: SLAMode
    risk_tier: RiskTier
    max_agent_passes: int
    allow_candidate_principles: bool
    require_red_team: bool
    review: ReviewRequirement


def build_policy_matrix_entry(mode: SLAMode, risk_tier: RiskTier) -> PolicyMatrixEntry:
    high_risk = risk_tier in {
        RiskTier.T4_PROCEDURAL_DRAFT,
        RiskTier.T5_HIGH_STAKES_RECOMMENDATION,
        RiskTier.T6_READY_TO_FILE_DOCUMENT,
    }
    deep_mode = mode in {SLAMode.DEEP, SLAMode.RESEARCH}

    return PolicyMatrixEntry(
        mode=mode,
        risk_tier=risk_tier,
        max_agent_passes={
            SLAMode.DRAFT: 1,
            SLAMode.STANDARD: 3,
            SLAMode.DEEP: 6,
            SLAMode.RESEARCH: 10,
        }[mode],
        allow_candidate_principles=not high_risk or deep_mode,
        require_red_team=high_risk or deep_mode,
        review=ReviewRequirement(
            human_review=high_risk,
            cross_review=risk_tier
            in {
                RiskTier.T5_HIGH_STAKES_RECOMMENDATION,
                RiskTier.T6_READY_TO_FILE_DOCUMENT,
            },
            replayable_trace=True,
            complete_provenance=high_risk,
        ),
    )
