from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.obligation_dynamics import (
    ObligationDynamicsConstraintSet,
    ObligationDynamicsEvaluation,
    ObligationDynamicsEvidenceMappingResult,
    build_obligation_dynamics_constraint_set,
    evaluate_obligation_dynamics_constraints,
    map_reviewed_obligation_dynamics_evidence,
)
from causa.institutional.contracts.obligation_dynamics_evaluation import (
    ObligationDynamicsBenchmarkReport,
    ObligationDynamicsRedTeamReport,
    run_obligation_dynamics_benchmark_suite,
    run_obligation_dynamics_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticObligationDynamicsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ObligationDynamicsEvidenceMappingResult
    constraint_set: ObligationDynamicsConstraintSet
    reviewed_evaluation: ObligationDynamicsEvaluation
    benchmark_report: ObligationDynamicsBenchmarkReport
    red_team_report: ObligationDynamicsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticObligationDynamicsEvaluationArtifact":
        expected_set = build_obligation_dynamics_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_obligation_dynamics_constraints(
            expected_set,
            self.reviewed_mapping.facts,
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Obligation-dynamics evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_obligation_dynamics_evaluation_artifact() -> (
    SyntheticObligationDynamicsEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().obligation_dynamics_evidence
    mapping = map_reviewed_obligation_dynamics_evidence(evidence)
    constraint_set = build_obligation_dynamics_constraint_set(mapping)
    return SyntheticObligationDynamicsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка перемены лиц и прекращения обязательств. "
            "Не устанавливает судебный результат и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_obligation_dynamics_constraints(
            constraint_set,
            mapping.facts,
        ),
        benchmark_report=run_obligation_dynamics_benchmark_suite(),
        red_team_report=run_obligation_dynamics_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
            "https://vsrf.ru/documents/own/26276/",
            "https://www.vsrf.ru/documents/own/29023/",
        ],
    )
