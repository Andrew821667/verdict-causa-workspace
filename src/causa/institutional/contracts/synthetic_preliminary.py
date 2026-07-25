from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.preliminary import (
    PreliminaryConstraintSet,
    PreliminaryEvaluation,
    PreliminaryEvidenceMappingResult,
    build_preliminary_constraint_set,
    evaluate_preliminary_constraints,
    map_reviewed_preliminary_evidence,
)
from causa.institutional.contracts.preliminary_evaluation import (
    PreliminaryBenchmarkReport,
    PreliminaryRedTeamReport,
    run_preliminary_benchmark_suite,
    run_preliminary_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticPreliminaryEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: PreliminaryEvidenceMappingResult
    constraint_set: PreliminaryConstraintSet
    reviewed_evaluation: PreliminaryEvaluation
    benchmark_report: PreliminaryBenchmarkReport
    red_team_report: PreliminaryRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticPreliminaryEvaluationArtifact":
        expected_set = build_preliminary_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_preliminary_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Preliminary evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_preliminary_evaluation_artifact() -> SyntheticPreliminaryEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().preliminary_evidence
    mapping = map_reviewed_preliminary_evidence(evidence)
    constraint_set = build_preliminary_constraint_set(mapping)
    return SyntheticPreliminaryEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о предварительном договоре по статье 429 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_preliminary_constraints(constraint_set, mapping.facts),
        benchmark_report=run_preliminary_benchmark_suite(),
        red_team_report=run_preliminary_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
