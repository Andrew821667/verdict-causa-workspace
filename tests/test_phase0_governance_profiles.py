from causa.governance.candidate_types import CandidateType
from causa.governance.pipeline import GovernanceStage
from causa.governance.profiles import GOVERNANCE_PROFILES, get_governance_profile


def test_every_candidate_type_has_governance_profile() -> None:
    assert set(GOVERNANCE_PROFILES) == set(CandidateType)


def test_meta_principle_requires_cross_review_and_sandbox() -> None:
    profile = get_governance_profile(CandidateType.META_PRINCIPLE)

    assert profile.requires_cross_review is True
    assert profile.requires_sandbox is True
    assert GovernanceStage.RED_TEAM_CHECK in profile.required_stages


def test_gap_heuristic_has_lightweight_profile() -> None:
    profile = get_governance_profile(CandidateType.GAP_HEURISTIC)

    assert profile.requires_cross_review is False
    assert profile.requires_sandbox is False
    assert GovernanceStage.EXPERT_REVIEW in profile.required_stages
