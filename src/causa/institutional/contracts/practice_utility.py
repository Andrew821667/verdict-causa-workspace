from causa.evaluation import PracticeUtilityObservation, PracticeUtilityReport
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST


SYNTHETIC_SUPPLY_PRACTICE_UTILITY_OBSERVATIONS = [
    PracticeUtilityObservation(
        id="utility-supply-late-delivery-v0",
        task_id="bench-supply-late-no-excuse",
        time_to_useful_draft_minutes=18,
        accepted_argument_count=2,
        human_correction_count=1,
        reviewer_usefulness_rating=4,
        notes=["Synthetic baseline: reviewer retained the source-grounded delay analysis."],
    ),
    PracticeUtilityObservation(
        id="utility-supply-defect-separation-v0",
        task_id="bench-confirmed-defect-after-timely-performance",
        time_to_useful_draft_minutes=24,
        accepted_argument_count=1,
        human_correction_count=2,
        reviewer_usefulness_rating=3.5,
        notes=["Synthetic baseline: reviewer corrected the scope of the defect remedy."],
    ),
    PracticeUtilityObservation(
        id="utility-supply-authority-trace-v0",
        task_id="bench-statutory-source-prevails-over-contract-specific",
        time_to_useful_draft_minutes=30,
        accepted_argument_count=0,
        human_correction_count=3,
        reviewer_usefulness_rating=2,
        formally_smart_but_practically_useless=True,
        notes=[
            "Synthetic baseline: the authority trace was correct but did not answer the requested remedy question."
        ],
    ),
]


def build_synthetic_supply_practice_utility_report(
    observations: list[PracticeUtilityObservation] | None = None,
) -> PracticeUtilityReport:
    selected_observations = (
        SYNTHETIC_SUPPLY_PRACTICE_UTILITY_OBSERVATIONS
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

    return PracticeUtilityReport(
        id="synthetic-supply-practice-utility-report-v0",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        baseline_kind="synthetic_phase0_baseline",
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
