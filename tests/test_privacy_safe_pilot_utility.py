import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.evaluation import (
    PilotDataOrigin,
    PilotTaskCategory,
    PrivacySafePilotUtilityObservation,
    PrivacySafePilotUtilityReport,
)
from causa.institutional.contracts.pilot_utility import (
    SYNTHETIC_PRIVACY_SAFE_PILOT_UTILITY_OBSERVATIONS,
    build_privacy_safe_pilot_utility_report,
)
from causa.phase0.pipeline import build_phase0_readiness_report


def test_privacy_safe_pilot_report_uses_synthetic_schema_demo() -> None:
    report = build_privacy_safe_pilot_utility_report()

    assert report.data_origin == PilotDataOrigin.SYNTHETIC_SCHEMA_DEMO
    assert report.total_observations == len(SYNTHETIC_PRIVACY_SAFE_PILOT_UTILITY_OBSERVATIONS)
    assert report.average_time_to_useful_draft_minutes == 24.0
    assert report.total_human_correction_count == 3
    assert report.formally_smart_but_practically_useless_count == 1


def test_privacy_safe_pilot_observation_requires_privacy_review() -> None:
    with pytest.raises(ValidationError, match="Privacy review"):
        PrivacySafePilotUtilityObservation(
            id="pilot-abcdef12",
            task_category=PilotTaskCategory.PAYMENT,
            collection_date="2026-07-11",
            data_origin=PilotDataOrigin.SYNTHETIC_SCHEMA_DEMO,
            privacy_reviewed=False,
            consent_recorded=True,
            time_to_useful_draft_minutes=1,
            accepted_argument_count=0,
            human_correction_count=0,
            reviewer_usefulness_rating=1,
        )


def test_privacy_safe_pilot_observation_requires_consent_record() -> None:
    with pytest.raises(ValidationError, match="Consent record"):
        PrivacySafePilotUtilityObservation(
            id="pilot-abcdef12",
            task_category=PilotTaskCategory.PAYMENT,
            collection_date="2026-07-11",
            data_origin=PilotDataOrigin.SYNTHETIC_SCHEMA_DEMO,
            privacy_reviewed=True,
            consent_recorded=False,
            time_to_useful_draft_minutes=1,
            accepted_argument_count=0,
            human_correction_count=0,
            reviewer_usefulness_rating=1,
        )


def test_privacy_safe_pilot_observation_forbids_free_text_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PrivacySafePilotUtilityObservation.model_validate(
            {
                "id": "pilot-abcdef12",
                "task_category": PilotTaskCategory.PAYMENT,
                "collection_date": "2026-07-11",
                "data_origin": PilotDataOrigin.SYNTHETIC_SCHEMA_DEMO,
                "privacy_reviewed": True,
                "consent_recorded": True,
                "time_to_useful_draft_minutes": 1,
                "accepted_argument_count": 0,
                "human_correction_count": 0,
                "reviewer_usefulness_rating": 1,
                "notes": "Potentially identifying text is not allowed.",
            }
        )


def test_exported_privacy_safe_pilot_fixture_is_valid() -> None:
    fixture_path = Path("examples/synthetic_privacy_safe_pilot_utility_report.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    report = PrivacySafePilotUtilityReport.model_validate(data)

    assert report.schema_version == "privacy-safe-pilot-utility.v0"
    assert all(observation.privacy_reviewed for observation in report.observations)


def test_readiness_report_references_privacy_safe_pilot_schema() -> None:
    report = build_phase0_readiness_report()
    evaluation_item = next(item for item in report.items if item.id == "ws8-evaluation-red-team")

    assert "synthetic-privacy-safe-pilot-utility-report-v0" in evaluation_item.evidence_refs
