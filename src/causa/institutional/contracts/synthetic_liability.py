from causa.institutional.contracts.liability_evaluation import (
    SyntheticLiabilityEvaluationArtifact,
    run_liability_benchmark_suite,
    run_liability_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
)


def build_synthetic_liability_evaluation_artifact(
) -> SyntheticLiabilityEvaluationArtifact:
    analysis = build_synthetic_supply_analysis_artifact()
    return SyntheticLiabilityEvaluationArtifact(
        reviewed_mapping=analysis.result.liability_evidence_mapping,
        reviewed_constraint_set=analysis.result.liability_constraint_set,
        reviewed_evaluation=analysis.result.liability_evaluation,
        benchmark_report=run_liability_benchmark_suite(),
        red_team_report=run_liability_red_team_suite(),
    )
