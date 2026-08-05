from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.commission import (
    CommissionConstraintSet,
    CommissionEvaluation,
    CommissionEvidenceMappingResult,
    build_commission_constraint_set,
    evaluate_commission_constraints,
    map_reviewed_commission_evidence,
)
from causa.institutional.contracts.commission_evaluation import (
    CommissionBenchmarkReport,
    CommissionRedTeamReport,
    run_commission_benchmark_suite,
    run_commission_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticCommissionEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: CommissionEvidenceMappingResult
    constraint_set: CommissionConstraintSet
    reviewed_evaluation: CommissionEvaluation
    benchmark_report: CommissionBenchmarkReport
    red_team_report: CommissionRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticCommissionEvaluationArtifact":
        expected_set = build_commission_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_commission_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Commission evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_commission_evaluation_artifact() -> SyntheticCommissionEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().commission_evidence
    mapping = map_reviewed_commission_evidence(evidence)
    constraint_set = build_commission_constraint_set(mapping)
    return SyntheticCommissionEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о комиссии по статьям 990–1004 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_commission_constraints(constraint_set, mapping.facts),
        benchmark_report=run_commission_benchmark_suite(),
        red_team_report=run_commission_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
