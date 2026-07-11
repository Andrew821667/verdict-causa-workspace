from datetime import date

from causa.evaluation import (
    PilotDataOrigin,
    PilotTaskCategory,
    PrivacySafePilotUtilityObservation,
    PrivacySafePilotUtilityReport,
)
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST


SYNTHETIC_PRIVACY_SAFE_PILOT_UTILITY_OBSERVATIONS = [
    PrivacySafePilotUtilityObservation(
        id="pilot-00000001",
        task_category=PilotTaskCategory.SUPPLY_DELIVERY,
        collection_date=date(2026, 7, 11),
        data_origin=PilotDataOrigin.SYNTHETIC_SCHEMA_DEMO,
        privacy_reviewed=True,
        consent_recorded=True,
        time_to_useful_draft_minutes=20,
        accepted_argument_count=1,
        human_correction_count=1,
        reviewer_usefulness_rating=4,
    ),
    PrivacySafePilotUtilityObservation(
        id="pilot-00000002",
        task_category=PilotTaskCategory.AUTHORITY,
        collection_date=date(2026, 7, 11),
        data_origin=PilotDataOrigin.SYNTHETIC_SCHEMA_DEMO,
        privacy_reviewed=True,
        consent_recorded=True,
        time_to_useful_draft_minutes=28,
        accepted_argument_count=0,
        human_correction_count=2,
        reviewer_usefulness_rating=2.5,
        formally_smart_but_practically_useless=True,
    ),
]


def build_privacy_safe_pilot_utility_report(
    observations: list[PrivacySafePilotUtilityObservation] | None = None,
) -> PrivacySafePilotUtilityReport:
    selected_observations = (
        SYNTHETIC_PRIVACY_SAFE_PILOT_UTILITY_OBSERVATIONS
        if observations is None
        else observations
    )
    total_observations = len(selected_observations)
    total_time_to_useful_draft = sum(
        observation.time_to_useful_draft_minutes for observation in selected_observations
    )
    total_accepted_argument_count = sum(
        observation.accepted_argument_count for observation in selected_observations
    )
    total_human_correction_count = sum(
        observation.human_correction_count for observation in selected_observations
    )
    total_reviewer_usefulness_rating = sum(
        observation.reviewer_usefulness_rating for observation in selected_observations
    )
    formally_smart_but_practically_useless_count = sum(
        observation.formally_smart_but_practically_useless
        for observation in selected_observations
    )

    return PrivacySafePilotUtilityReport(
        id="synthetic-privacy-safe-pilot-utility-report-v0",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        data_origin=PilotDataOrigin.SYNTHETIC_SCHEMA_DEMO,
        schema_version="privacy-safe-pilot-utility.v0",
        total_observations=total_observations,
        average_time_to_useful_draft_minutes=(
            total_time_to_useful_draft / total_observations if total_observations else 0.0
        ),
        total_accepted_argument_count=total_accepted_argument_count,
        total_human_correction_count=total_human_correction_count,
        average_reviewer_usefulness_rating=(
            total_reviewer_usefulness_rating / total_observations
            if total_observations
            else 0.0
        ),
        formally_smart_but_practically_useless_count=(
            formally_smart_but_practically_useless_count
        ),
        observations=selected_observations,
    )
