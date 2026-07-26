from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.barter import (
    BarterConstraintSet,
    BarterEvaluation,
    BarterEvidenceMappingResult,
    build_barter_constraint_set,
    evaluate_barter_constraints,
    map_reviewed_barter_evidence,
)
from causa.institutional.contracts.barter_evaluation import (
    BarterBenchmarkReport,
    BarterRedTeamReport,
    run_barter_benchmark_suite,
    run_barter_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticBarterEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: BarterEvidenceMappingResult
    constraint_set: BarterConstraintSet
    reviewed_evaluation: BarterEvaluation
    benchmark_report: BarterBenchmarkReport
    red_team_report: BarterRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticBarterEvaluationArtifact":
        expected_set = build_barter_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_barter_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Barter evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_barter_evaluation_artifact() -> SyntheticBarterEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().barter_evidence
    mapping = map_reviewed_barter_evidence(evidence)
    constraint_set = build_barter_constraint_set(mapping)
    return SyntheticBarterEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о мене по статьям 567–571 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_barter_constraints(constraint_set, mapping.facts),
        benchmark_report=run_barter_benchmark_suite(),
        red_team_report=run_barter_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
