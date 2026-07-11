from causa.institutional.contracts.counterfactual_evaluation import (
    SyntheticCounterfactualEvaluationArtifact,
    run_counterfactual_benchmark_suite,
    run_counterfactual_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
)


def build_synthetic_counterfactual_evaluation_artifact(
) -> SyntheticCounterfactualEvaluationArtifact:
    analysis = build_synthetic_supply_analysis_artifact()
    return SyntheticCounterfactualEvaluationArtifact(
        sensitivity_report=analysis.result.counterfactual_sensitivity,
        benchmark_report=run_counterfactual_benchmark_suite(),
        red_team_report=run_counterfactual_red_team_suite(),
    )
