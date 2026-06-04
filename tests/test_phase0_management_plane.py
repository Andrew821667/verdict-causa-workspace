from causa.management.policy_matrix import build_policy_matrix_entry
from causa.management.risk_tiers import RiskTier
from causa.management.sla_modes import SLAMode


def test_low_risk_draft_policy_is_lightweight() -> None:
    policy = build_policy_matrix_entry(SLAMode.DRAFT, RiskTier.T1_REFERENCE)

    assert policy.max_agent_passes == 1
    assert policy.review.human_review is False
    assert policy.require_red_team is False


def test_high_risk_policy_requires_review_and_red_team() -> None:
    policy = build_policy_matrix_entry(
        SLAMode.STANDARD,
        RiskTier.T5_HIGH_STAKES_RECOMMENDATION,
    )

    assert policy.review.human_review is True
    assert policy.review.cross_review is True
    assert policy.require_red_team is True
    assert policy.review.complete_provenance is True


def test_research_mode_allows_more_agent_passes() -> None:
    policy = build_policy_matrix_entry(SLAMode.RESEARCH, RiskTier.T2_INTERNAL_MEMO)

    assert policy.max_agent_passes == 10
    assert policy.require_red_team is True
