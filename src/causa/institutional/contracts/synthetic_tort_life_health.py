from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.tort_life_health import (
    TortLifeHealthConstraintSet,
    TortLifeHealthEvaluation,
    TortLifeHealthEvidenceMappingResult,
    build_tort_life_health_constraint_set,
    evaluate_tort_life_health_constraints,
    map_reviewed_tort_life_health_evidence,
)
from causa.institutional.contracts.tort_life_health_evaluation import (
    TortLifeHealthBenchmarkReport,
    TortLifeHealthRedTeamReport,
    run_tort_life_health_benchmark_suite,
    run_tort_life_health_red_team_suite,
)


class SyntheticTortLifeHealthEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: TortLifeHealthEvidenceMappingResult
    constraint_set: TortLifeHealthConstraintSet
    reviewed_evaluation: TortLifeHealthEvaluation
    benchmark_report: TortLifeHealthBenchmarkReport
    red_team_report: TortLifeHealthRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticTortLifeHealthEvaluationArtifact":
        expected_set = build_tort_life_health_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_tort_life_health_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Tort-life-health evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_tort_life_health_evaluation_artifact() -> (
    SyntheticTortLifeHealthEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().tort_life_health_evidence
    mapping = map_reviewed_tort_life_health_evidence(evidence)
    constraint_set = build_tort_life_health_constraint_set(mapping)
    return SyntheticTortLifeHealthEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о возмещении вреда, причинённого жизни или здоровью "
            "гражданина, по статьям 1084–1094 ГК РФ. Не устанавливает судебный факт и не "
            "является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_tort_life_health_constraints(constraint_set, mapping.facts),
        benchmark_report=run_tort_life_health_benchmark_suite(),
        red_team_report=run_tort_life_health_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
