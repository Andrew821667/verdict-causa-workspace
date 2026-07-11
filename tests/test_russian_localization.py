from causa.governance.candidate_types import CandidateType
from causa.governance.failure_taxonomy import FailureType
from causa.governance.pipeline import GovernanceStage
from causa.localization.ru import (
    CANDIDATE_TYPE_LABELS_RU,
    FAILURE_TYPE_LABELS_RU,
    GOVERNANCE_STAGE_LABELS_RU,
    RISK_TIER_LABELS_RU,
    SLA_MODE_LABELS_RU,
)
from causa.management.risk_tiers import RiskTier
from causa.management.sla_modes import SLAMode
from causa.institutional.contracts.red_team import SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
from causa.institutional.contracts.synthetic_sources import SYNTHETIC_CONTRACT_SOURCES


def _contains_cyrillic(value: str) -> bool:
    return any("а" <= character.lower() <= "я" for character in value)


def test_russian_labels_cover_all_governance_machine_values() -> None:
    assert set(GOVERNANCE_STAGE_LABELS_RU) == {stage.value for stage in GovernanceStage}
    assert set(CANDIDATE_TYPE_LABELS_RU) == {
        candidate_type.value for candidate_type in CandidateType
    }
    assert set(FAILURE_TYPE_LABELS_RU) == {
        failure_type.value for failure_type in FailureType
    }


def test_russian_labels_cover_all_management_plane_values() -> None:
    assert set(SLA_MODE_LABELS_RU) == {mode.value for mode in SLAMode}
    assert set(RISK_TIER_LABELS_RU) == {risk_tier.value for risk_tier in RiskTier}


def test_formal_and_authority_results_include_russian_reasons() -> None:
    from causa.phase0.demo_trace import build_supply_dispute_demo_trace

    trace = build_supply_dispute_demo_trace()

    assert trace.temporal_evaluation.reasons_ru
    assert trace.source_applicability.reasons_ru
    assert trace.constraint_evaluation.reasons_ru
    assert trace.analysis_result.authority_evaluation.reasons_ru
    assert all(_contains_cyrillic(reason) for reason in trace.constraint_evaluation.reasons_ru)


def test_synthetic_russian_law_materials_are_human_readable_in_russian() -> None:
    assert all(_contains_cyrillic(source.title) for source in SYNTHETIC_CONTRACT_SOURCES)
    assert all(_contains_cyrillic(source.text) for source in SYNTHETIC_CONTRACT_SOURCES)
    assert all(_contains_cyrillic(scenario.title) for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS)
    assert all(
        _contains_cyrillic(scenario.unacceptable_outcome)
        for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
    )
