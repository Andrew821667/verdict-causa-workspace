from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.carriage import (
    CarriageConstraintSet,
    CarriageEvaluation,
    CarriageEvidenceMappingResult,
    build_carriage_constraint_set,
    evaluate_carriage_constraints,
    map_reviewed_carriage_evidence,
)
from causa.institutional.contracts.carriage_evaluation import (
    CarriageBenchmarkReport,
    CarriageRedTeamReport,
    run_carriage_benchmark_suite,
    run_carriage_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticCarriageEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: CarriageEvidenceMappingResult
    constraint_set: CarriageConstraintSet
    reviewed_evaluation: CarriageEvaluation
    benchmark_report: CarriageBenchmarkReport
    red_team_report: CarriageRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticCarriageEvaluationArtifact":
        expected_set = build_carriage_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_carriage_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Carriage evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_carriage_evaluation_artifact() -> SyntheticCarriageEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().carriage_evidence
    mapping = map_reviewed_carriage_evidence(evidence)
    constraint_set = build_carriage_constraint_set(mapping)
    return SyntheticCarriageEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка общих положений о перевозке по статьям 784–800 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_carriage_constraints(constraint_set, mapping.facts),
        benchmark_report=run_carriage_benchmark_suite(),
        red_team_report=run_carriage_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
