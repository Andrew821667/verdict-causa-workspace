from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.freedom import (
    FreedomConstraintSet,
    FreedomEvaluation,
    FreedomEvidenceMappingResult,
    build_freedom_constraint_set,
    evaluate_freedom_constraints,
    map_reviewed_freedom_evidence,
)
from causa.institutional.contracts.freedom_evaluation import (
    FreedomBenchmarkReport,
    FreedomRedTeamReport,
    run_freedom_benchmark_suite,
    run_freedom_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticFreedomEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: FreedomEvidenceMappingResult
    constraint_set: FreedomConstraintSet
    reviewed_evaluation: FreedomEvaluation
    benchmark_report: FreedomBenchmarkReport
    red_team_report: FreedomRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticFreedomEvaluationArtifact":
        expected_set = build_freedom_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_freedom_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Freedom evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_freedom_evaluation_artifact() -> SyntheticFreedomEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().freedom_evidence
    mapping = map_reviewed_freedom_evidence(evidence)
    constraint_set = build_freedom_constraint_set(mapping)
    return SyntheticFreedomEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о свободе договора, его соответствии закону и "
            "определении цены по статьям 421–424 ГК РФ. Не устанавливает судебный факт и "
            "не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_freedom_constraints(constraint_set, mapping.facts),
        benchmark_report=run_freedom_benchmark_suite(),
        red_team_report=run_freedom_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
