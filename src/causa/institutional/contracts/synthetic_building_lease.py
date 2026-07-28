from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.building_lease import (
    BuildingLeaseConstraintSet,
    BuildingLeaseEvaluation,
    BuildingLeaseEvidenceMappingResult,
    build_building_lease_constraint_set,
    evaluate_building_lease_constraints,
    map_reviewed_building_lease_evidence,
)
from causa.institutional.contracts.building_lease_evaluation import (
    BuildingLeaseBenchmarkReport,
    BuildingLeaseRedTeamReport,
    run_building_lease_benchmark_suite,
    run_building_lease_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticBuildingLeaseEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: BuildingLeaseEvidenceMappingResult
    constraint_set: BuildingLeaseConstraintSet
    reviewed_evaluation: BuildingLeaseEvaluation
    benchmark_report: BuildingLeaseBenchmarkReport
    red_team_report: BuildingLeaseRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticBuildingLeaseEvaluationArtifact":
        expected_set = build_building_lease_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_building_lease_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Building-lease evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_building_lease_evaluation_artifact() -> (
    SyntheticBuildingLeaseEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().building_lease_evidence
    mapping = map_reviewed_building_lease_evidence(evidence)
    constraint_set = build_building_lease_constraint_set(mapping)
    return SyntheticBuildingLeaseEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил об аренде зданий и сооружений по статьям 650–655 "
            "ГК РФ. Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_building_lease_constraints(constraint_set, mapping.facts),
        benchmark_report=run_building_lease_benchmark_suite(),
        red_team_report=run_building_lease_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
