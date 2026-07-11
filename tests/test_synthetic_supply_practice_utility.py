import json
from pathlib import Path

from causa.evaluation import PracticeUtilityObservation, PracticeUtilityReport
from causa.institutional.contracts.practice_utility import (
    SYNTHETIC_SUPPLY_PRACTICE_UTILITY_OBSERVATIONS,
    build_synthetic_supply_practice_utility_report,
)
from causa.phase0.pipeline import build_phase0_readiness_report


def test_synthetic_supply_practice_utility_report_keeps_quality_separate() -> None:
    report = build_synthetic_supply_practice_utility_report()

    assert report.total_observations == len(SYNTHETIC_SUPPLY_PRACTICE_UTILITY_OBSERVATIONS)
    assert report.baseline_kind == "synthetic_phase0_baseline"
    assert report.total_accepted_argument_count == 3
    assert report.total_human_correction_count == 6
    assert report.average_time_to_useful_draft_minutes == 24.0
    assert report.average_reviewer_usefulness_rating == 3.1666666666666665
    assert report.formally_smart_but_practically_useless_count == 1


def test_practice_utility_report_handles_empty_observations() -> None:
    report = build_synthetic_supply_practice_utility_report(observations=[])

    assert report.total_observations == 0
    assert report.average_time_to_useful_draft_minutes == 0.0
    assert report.average_reviewer_usefulness_rating == 0.0


def test_exported_synthetic_supply_practice_utility_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/synthetic_supply_practice_utility_report.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    report = PracticeUtilityReport.model_validate(data)

    assert report.id == "synthetic-supply-practice-utility-report-v0"
    assert all(
        isinstance(observation, PracticeUtilityObservation)
        for observation in report.observations
    )


def test_readiness_report_references_practice_utility_report() -> None:
    report = build_phase0_readiness_report()
    evaluation_item = next(item for item in report.items if item.id == "ws8-evaluation-red-team")

    assert "synthetic-supply-practice-utility-report-v0" in evaluation_item.evidence_refs
