from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.tort_general import (
    TortGeneralConstraintSet,
    TortGeneralEvaluation,
    TortGeneralEvidenceMappingResult,
    build_tort_general_constraint_set,
    evaluate_tort_general_constraints,
    map_reviewed_tort_general_evidence,
)
from causa.institutional.contracts.tort_general_evaluation import (
    TortGeneralBenchmarkReport,
    TortGeneralRedTeamReport,
    run_tort_general_benchmark_suite,
    run_tort_general_red_team_suite,
)


class SyntheticTortGeneralEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: TortGeneralEvidenceMappingResult
    constraint_set: TortGeneralConstraintSet
    reviewed_evaluation: TortGeneralEvaluation
    benchmark_report: TortGeneralBenchmarkReport
    red_team_report: TortGeneralRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticTortGeneralEvaluationArtifact":
        expected_set = build_tort_general_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_tort_general_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Tort-general evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_tort_general_evaluation_artifact() -> SyntheticTortGeneralEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().tort_general_evidence
    mapping = map_reviewed_tort_general_evidence(evidence)
    constraint_set = build_tort_general_constraint_set(mapping)
    return SyntheticTortGeneralEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка общих правил о возмещении вреда по статьям 1064–1083 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_tort_general_constraints(constraint_set, mapping.facts),
        benchmark_report=run_tort_general_benchmark_suite(),
        red_team_report=run_tort_general_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
