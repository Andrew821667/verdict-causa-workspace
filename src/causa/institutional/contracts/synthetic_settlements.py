from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.settlements import (
    SettlementsConstraintSet,
    SettlementsEvaluation,
    SettlementsEvidenceMappingResult,
    build_settlements_constraint_set,
    evaluate_settlements_constraints,
    map_reviewed_settlements_evidence,
)
from causa.institutional.contracts.settlements_evaluation import (
    SettlementsBenchmarkReport,
    SettlementsRedTeamReport,
    run_settlements_benchmark_suite,
    run_settlements_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticSettlementsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: SettlementsEvidenceMappingResult
    constraint_set: SettlementsConstraintSet
    reviewed_evaluation: SettlementsEvaluation
    benchmark_report: SettlementsBenchmarkReport
    red_team_report: SettlementsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticSettlementsEvaluationArtifact":
        expected_set = build_settlements_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_settlements_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Settlements evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_settlements_evaluation_artifact() -> SyntheticSettlementsEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().settlements_evidence
    mapping = map_reviewed_settlements_evidence(evidence)
    constraint_set = build_settlements_constraint_set(mapping)
    return SyntheticSettlementsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о расчётах по статьям 861–885 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_settlements_constraints(constraint_set, mapping.facts),
        benchmark_report=run_settlements_benchmark_suite(),
        red_team_report=run_settlements_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
