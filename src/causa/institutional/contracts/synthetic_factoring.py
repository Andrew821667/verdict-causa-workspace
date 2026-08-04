from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.factoring import (
    FactoringConstraintSet,
    FactoringEvaluation,
    FactoringEvidenceMappingResult,
    build_factoring_constraint_set,
    evaluate_factoring_constraints,
    map_reviewed_factoring_evidence,
)
from causa.institutional.contracts.factoring_evaluation import (
    FactoringBenchmarkReport,
    FactoringRedTeamReport,
    run_factoring_benchmark_suite,
    run_factoring_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticFactoringEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: FactoringEvidenceMappingResult
    constraint_set: FactoringConstraintSet
    reviewed_evaluation: FactoringEvaluation
    benchmark_report: FactoringBenchmarkReport
    red_team_report: FactoringRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticFactoringEvaluationArtifact":
        expected_set = build_factoring_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_factoring_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Factoring evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_factoring_evaluation_artifact() -> SyntheticFactoringEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().factoring_evidence
    mapping = map_reviewed_factoring_evidence(evidence)
    constraint_set = build_factoring_constraint_set(mapping)
    return SyntheticFactoringEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о финансировании под уступку денежного требования по "
            "статьям 824–833 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_factoring_constraints(constraint_set, mapping.facts),
        benchmark_report=run_factoring_benchmark_suite(),
        red_team_report=run_factoring_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
