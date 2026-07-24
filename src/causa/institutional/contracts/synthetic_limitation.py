from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.limitation import (
    LimitationConstraintSet,
    LimitationEvaluation,
    LimitationEvidenceMappingResult,
    build_limitation_constraint_set,
    evaluate_limitation_constraints,
    map_reviewed_limitation_evidence,
)
from causa.institutional.contracts.limitation_evaluation import (
    LimitationBenchmarkReport,
    LimitationRedTeamReport,
    run_limitation_benchmark_suite,
    run_limitation_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticLimitationEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: LimitationEvidenceMappingResult
    constraint_set: LimitationConstraintSet
    reviewed_evaluation: LimitationEvaluation
    benchmark_report: LimitationBenchmarkReport
    red_team_report: LimitationRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticLimitationEvaluationArtifact":
        expected_set = build_limitation_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_limitation_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Limitation evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_limitation_evaluation_artifact() -> SyntheticLimitationEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().limitation_evidence
    mapping = map_reviewed_limitation_evidence(evidence)
    constraint_set = build_limitation_constraint_set(mapping)
    return SyntheticLimitationEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил исковой давности по статьям 195–208 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_limitation_constraints(constraint_set, mapping.facts),
        benchmark_report=run_limitation_benchmark_suite(),
        red_team_report=run_limitation_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
