from causa.governance.candidate_types import CandidateType
from causa.governance.failure_taxonomy import FailureType
from causa.management.policies import CasePolicy
from causa.management.risk_tiers import RiskTier
from causa.management.sla_modes import SLAMode


def test_candidate_type_taxonomy_contains_meta_principle() -> None:
    assert CandidateType.META_PRINCIPLE.value == "meta_principle"


def test_failure_taxonomy_contains_translation_distortion() -> None:
    assert FailureType.TRANSLATION_DISTORTION.value == "translation_distortion"


def test_case_policy_binds_mode_and_risk_tier() -> None:
    policy = CasePolicy(mode=SLAMode.STANDARD, risk_tier=RiskTier.T3_DRAFT_LETTER)
    assert policy.mode == SLAMode.STANDARD
    assert policy.risk_tier == RiskTier.T3_DRAFT_LETTER
