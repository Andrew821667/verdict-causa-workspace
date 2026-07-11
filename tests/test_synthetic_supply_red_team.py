import json
from pathlib import Path

from causa.evaluation import RedTeamSuiteReport
from causa.institutional.contracts.red_team import SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
from causa.institutional.contracts.red_team_runner import (
    DEFAULT_SUPPLY_CANDIDATE_GUARDRAIL,
    run_red_team_scenario,
    run_synthetic_supply_red_team_suite,
)
from causa.phase0.pipeline import build_phase0_readiness_report


def test_synthetic_supply_red_team_suite_has_initial_coverage() -> None:
    scenario_ids = {scenario.id for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS}

    assert len(SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS) >= 10
    assert {
        "redteam-ignore-valid-excuse",
        "redteam-erase-payment-duty",
        "redteam-defects-collapse",
        "redteam-penalty-erasure",
        "redteam-hallucinated-source",
        "redteam-temporal-overreach",
        "redteam-special-contract-overrides-statute",
        "redteam-expired-statute-over-current-case-law",
        "redteam-infer-defect-without-confirmed-performance",
        "redteam-ignore-payment-defense",
    } <= scenario_ids


def test_default_guardrail_blocks_current_red_team_suite() -> None:
    report = run_synthetic_supply_red_team_suite()

    assert report.total == len(SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS)
    assert report.unblocked == 0
    assert report.block_rate == 1.0


def test_missing_guardrail_fragment_leaves_attack_unblocked() -> None:
    scenario = next(
        scenario
        for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
        if scenario.id == "redteam-erase-payment-duty"
    )
    weak_guardrail = (
        DEFAULT_SUPPLY_CANDIDATE_GUARDRAIL.replace("Payment", "Billing").replace(
            "payment", "billing"
        )
    )
    result = run_red_team_scenario(scenario, weak_guardrail)

    assert result.blocked is False
    assert any("payment" in reason for reason in result.reasons)


def test_exported_synthetic_supply_red_team_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/synthetic_supply_red_team_report.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    report = RedTeamSuiteReport.model_validate(data)

    assert report.id == "synthetic-supply-red-team-suite-v0"
    assert report.total >= 6
    assert report.unblocked == 0


def test_readiness_report_references_red_team_suite() -> None:
    report = build_phase0_readiness_report()
    evaluation_item = next(item for item in report.items if item.id == "ws8-evaluation-red-team")

    assert "synthetic-supply-red-team-suite-v0" in evaluation_item.evidence_refs
