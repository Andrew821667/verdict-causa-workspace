from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.residential_lease import (
    ResidentialLeaseConstraintSet,
    ResidentialLeaseEvaluation,
    ResidentialLeaseEvidenceMappingResult,
    build_residential_lease_constraint_set,
    evaluate_residential_lease_constraints,
    map_reviewed_residential_lease_evidence,
)
from causa.institutional.contracts.residential_lease_evaluation import (
    ResidentialLeaseBenchmarkReport,
    ResidentialLeaseRedTeamReport,
    run_residential_lease_benchmark_suite,
    run_residential_lease_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticResidentialLeaseEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ResidentialLeaseEvidenceMappingResult
    constraint_set: ResidentialLeaseConstraintSet
    reviewed_evaluation: ResidentialLeaseEvaluation
    benchmark_report: ResidentialLeaseBenchmarkReport
    red_team_report: ResidentialLeaseRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticResidentialLeaseEvaluationArtifact":
        expected_set = build_residential_lease_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_residential_lease_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Residential-lease evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_residential_lease_evaluation_artifact() -> (
    SyntheticResidentialLeaseEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().residential_lease_evidence
    mapping = map_reviewed_residential_lease_evidence(evidence)
    constraint_set = build_residential_lease_constraint_set(mapping)
    return SyntheticResidentialLeaseEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о найме жилого помещения по статьям 671–688 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_residential_lease_constraints(constraint_set, mapping.facts),
        benchmark_report=run_residential_lease_benchmark_suite(),
        red_team_report=run_residential_lease_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
