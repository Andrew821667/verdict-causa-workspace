from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.performance_remedies import (
    PerformanceRemediesConstraintSet,
    PerformanceRemediesEvaluation,
    PerformanceRemediesEvidenceMappingResult,
    build_performance_remedies_constraint_set,
    evaluate_performance_remedies_constraints,
    map_reviewed_performance_remedies_evidence,
)
from causa.institutional.contracts.performance_remedies_evaluation import (
    PerformanceRemediesBenchmarkReport,
    PerformanceRemediesRedTeamReport,
    run_performance_remedies_benchmark_suite,
    run_performance_remedies_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticPerformanceRemediesEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: PerformanceRemediesEvidenceMappingResult
    constraint_set: PerformanceRemediesConstraintSet
    reviewed_evaluation: PerformanceRemediesEvaluation
    benchmark_report: PerformanceRemediesBenchmarkReport
    red_team_report: PerformanceRemediesRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticPerformanceRemediesEvaluationArtifact":
        expected_set = build_performance_remedies_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_performance_remedies_constraints(
            expected_set,
            self.reviewed_mapping.facts,
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Performance-remedies evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_performance_remedies_evaluation_artifact() -> (
    SyntheticPerformanceRemediesEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().performance_remedies_evidence
    mapping = map_reviewed_performance_remedies_evidence(evidence)
    constraint_set = build_performance_remedies_constraint_set(mapping)
    return SyntheticPerformanceRemediesEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка исполнения обязательств и средств защиты. "
            "Не рассчитывает суммы, не устанавливает судебный результат и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_performance_remedies_constraints(
            constraint_set,
            mapping.facts,
        ),
        benchmark_report=run_performance_remedies_benchmark_suite(),
        red_team_report=run_performance_remedies_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
            "https://vsrf.ru/documents/own/8524/",
            "https://www.vsrf.ru/documents/own/8478/",
        ],
    )
