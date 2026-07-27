from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.lease import (
    LeaseConstraintSet,
    LeaseEvaluation,
    LeaseEvidenceMappingResult,
    build_lease_constraint_set,
    evaluate_lease_constraints,
    map_reviewed_lease_evidence,
)
from causa.institutional.contracts.lease_evaluation import (
    LeaseBenchmarkReport,
    LeaseRedTeamReport,
    run_lease_benchmark_suite,
    run_lease_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticLeaseEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: LeaseEvidenceMappingResult
    constraint_set: LeaseConstraintSet
    reviewed_evaluation: LeaseEvaluation
    benchmark_report: LeaseBenchmarkReport
    red_team_report: LeaseRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticLeaseEvaluationArtifact":
        expected_set = build_lease_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_lease_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Lease evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_lease_evaluation_artifact() -> SyntheticLeaseEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().lease_evidence
    mapping = map_reviewed_lease_evidence(evidence)
    constraint_set = build_lease_constraint_set(mapping)
    return SyntheticLeaseEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка общих положений об аренде по статьям 606–625 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_lease_constraints(constraint_set, mapping.facts),
        benchmark_report=run_lease_benchmark_suite(),
        red_team_report=run_lease_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
