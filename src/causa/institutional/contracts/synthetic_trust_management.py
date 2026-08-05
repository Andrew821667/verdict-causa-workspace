from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.trust_management import (
    TrustManagementConstraintSet,
    TrustManagementEvaluation,
    TrustManagementEvidenceMappingResult,
    build_trust_management_constraint_set,
    evaluate_trust_management_constraints,
    map_reviewed_trust_management_evidence,
)
from causa.institutional.contracts.trust_management_evaluation import (
    TrustManagementBenchmarkReport,
    TrustManagementRedTeamReport,
    run_trust_management_benchmark_suite,
    run_trust_management_red_team_suite,
)


class SyntheticTrustManagementEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: TrustManagementEvidenceMappingResult
    constraint_set: TrustManagementConstraintSet
    reviewed_evaluation: TrustManagementEvaluation
    benchmark_report: TrustManagementBenchmarkReport
    red_team_report: TrustManagementRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticTrustManagementEvaluationArtifact":
        expected_set = build_trust_management_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_trust_management_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Trust-management evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_trust_management_evaluation_artifact() -> (
    SyntheticTrustManagementEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().trust_management_evidence
    mapping = map_reviewed_trust_management_evidence(evidence)
    constraint_set = build_trust_management_constraint_set(mapping)
    return SyntheticTrustManagementEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о доверительном управлении имуществом по "
            "статьям 1012–1026 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_trust_management_constraints(constraint_set, mapping.facts),
        benchmark_report=run_trust_management_benchmark_suite(),
        red_team_report=run_trust_management_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
