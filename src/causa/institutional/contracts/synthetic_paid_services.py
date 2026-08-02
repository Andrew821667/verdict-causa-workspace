from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.paid_services import (
    PaidServicesConstraintSet,
    PaidServicesEvaluation,
    PaidServicesEvidenceMappingResult,
    build_paid_services_constraint_set,
    evaluate_paid_services_constraints,
    map_reviewed_paid_services_evidence,
)
from causa.institutional.contracts.paid_services_evaluation import (
    PaidServicesBenchmarkReport,
    PaidServicesRedTeamReport,
    run_paid_services_benchmark_suite,
    run_paid_services_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticPaidServicesEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: PaidServicesEvidenceMappingResult
    constraint_set: PaidServicesConstraintSet
    reviewed_evaluation: PaidServicesEvaluation
    benchmark_report: PaidServicesBenchmarkReport
    red_team_report: PaidServicesRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticPaidServicesEvaluationArtifact":
        expected_set = build_paid_services_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_paid_services_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Paid-services evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_paid_services_evaluation_artifact() -> SyntheticPaidServicesEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().paid_services_evidence
    mapping = map_reviewed_paid_services_evidence(evidence)
    constraint_set = build_paid_services_constraint_set(mapping)
    return SyntheticPaidServicesEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о возмездном оказании услуг по статьям 779–783.1 "
            "ГК РФ. Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_paid_services_constraints(constraint_set, mapping.facts),
        benchmark_report=run_paid_services_benchmark_suite(),
        red_team_report=run_paid_services_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
