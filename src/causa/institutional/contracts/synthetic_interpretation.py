from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.interpretation import (
    InterpretationConstraintSet,
    InterpretationEvaluation,
    InterpretationEvidenceMappingResult,
    build_interpretation_constraint_set,
    evaluate_interpretation_constraints,
    map_reviewed_interpretation_evidence,
)
from causa.institutional.contracts.interpretation_evaluation import (
    InterpretationBenchmarkReport,
    InterpretationRedTeamReport,
    run_interpretation_benchmark_suite,
    run_interpretation_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticInterpretationEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: InterpretationEvidenceMappingResult
    constraint_set: InterpretationConstraintSet
    reviewed_evaluation: InterpretationEvaluation
    benchmark_report: InterpretationBenchmarkReport
    red_team_report: InterpretationRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticInterpretationEvaluationArtifact":
        expected_set = build_interpretation_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_interpretation_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Interpretation evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_interpretation_evaluation_artifact() -> (
    SyntheticInterpretationEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().interpretation_evidence
    mapping = map_reviewed_interpretation_evidence(evidence)
    constraint_set = build_interpretation_constraint_set(mapping)
    return SyntheticInterpretationEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил толкования договора по статье 431 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_interpretation_constraints(constraint_set, mapping.facts),
        benchmark_report=run_interpretation_benchmark_suite(),
        red_team_report=run_interpretation_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
