from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.framework import (
    FrameworkConstraintSet,
    FrameworkEvaluation,
    FrameworkEvidenceMappingResult,
    build_framework_constraint_set,
    evaluate_framework_constraints,
    map_reviewed_framework_evidence,
)
from causa.institutional.contracts.framework_evaluation import (
    FrameworkBenchmarkReport,
    FrameworkRedTeamReport,
    run_framework_benchmark_suite,
    run_framework_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticFrameworkEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: FrameworkEvidenceMappingResult
    constraint_set: FrameworkConstraintSet
    reviewed_evaluation: FrameworkEvaluation
    benchmark_report: FrameworkBenchmarkReport
    red_team_report: FrameworkRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticFrameworkEvaluationArtifact":
        expected_set = build_framework_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_framework_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Framework evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_framework_evaluation_artifact() -> SyntheticFrameworkEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().framework_evidence
    mapping = map_reviewed_framework_evidence(evidence)
    constraint_set = build_framework_constraint_set(mapping)
    return SyntheticFrameworkEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о рамочном и абонентском договоре по статьям "
            "429.1 и 429.4 ГК РФ. Не устанавливает судебный факт и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_framework_constraints(constraint_set, mapping.facts),
        benchmark_report=run_framework_benchmark_suite(),
        red_team_report=run_framework_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
