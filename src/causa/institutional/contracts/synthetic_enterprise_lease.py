from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.enterprise_lease import (
    EnterpriseLeaseConstraintSet,
    EnterpriseLeaseEvaluation,
    EnterpriseLeaseEvidenceMappingResult,
    build_enterprise_lease_constraint_set,
    evaluate_enterprise_lease_constraints,
    map_reviewed_enterprise_lease_evidence,
)
from causa.institutional.contracts.enterprise_lease_evaluation import (
    EnterpriseLeaseBenchmarkReport,
    EnterpriseLeaseRedTeamReport,
    run_enterprise_lease_benchmark_suite,
    run_enterprise_lease_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticEnterpriseLeaseEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: EnterpriseLeaseEvidenceMappingResult
    constraint_set: EnterpriseLeaseConstraintSet
    reviewed_evaluation: EnterpriseLeaseEvaluation
    benchmark_report: EnterpriseLeaseBenchmarkReport
    red_team_report: EnterpriseLeaseRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticEnterpriseLeaseEvaluationArtifact":
        expected_set = build_enterprise_lease_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_enterprise_lease_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Enterprise-lease evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_enterprise_lease_evaluation_artifact() -> (
    SyntheticEnterpriseLeaseEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().enterprise_lease_evidence
    mapping = map_reviewed_enterprise_lease_evidence(evidence)
    constraint_set = build_enterprise_lease_constraint_set(mapping)
    return SyntheticEnterpriseLeaseEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил об аренде предприятий по статьям 656–664 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_enterprise_lease_constraints(constraint_set, mapping.facts),
        benchmark_report=run_enterprise_lease_benchmark_suite(),
        red_team_report=run_enterprise_lease_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
