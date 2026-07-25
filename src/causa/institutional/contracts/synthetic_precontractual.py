from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.precontractual import (
    PrecontractualConstraintSet,
    PrecontractualEvaluation,
    PrecontractualEvidenceMappingResult,
    build_precontractual_constraint_set,
    evaluate_precontractual_constraints,
    map_reviewed_precontractual_evidence,
)
from causa.institutional.contracts.precontractual_evaluation import (
    PrecontractualBenchmarkReport,
    PrecontractualRedTeamReport,
    run_precontractual_benchmark_suite,
    run_precontractual_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticPrecontractualEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: PrecontractualEvidenceMappingResult
    constraint_set: PrecontractualConstraintSet
    reviewed_evaluation: PrecontractualEvaluation
    benchmark_report: PrecontractualBenchmarkReport
    red_team_report: PrecontractualRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticPrecontractualEvaluationArtifact":
        expected_set = build_precontractual_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_precontractual_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Precontractual evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_precontractual_evaluation_artifact() -> (
    SyntheticPrecontractualEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().precontractual_evidence
    mapping = map_reviewed_precontractual_evidence(evidence)
    constraint_set = build_precontractual_constraint_set(mapping)
    return SyntheticPrecontractualEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о преддоговорной ответственности по статье 434.1 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_precontractual_constraints(constraint_set, mapping.facts),
        benchmark_report=run_precontractual_benchmark_suite(),
        red_team_report=run_precontractual_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
