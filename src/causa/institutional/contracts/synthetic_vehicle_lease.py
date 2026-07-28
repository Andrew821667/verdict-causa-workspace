from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.vehicle_lease import (
    VehicleLeaseConstraintSet,
    VehicleLeaseEvaluation,
    VehicleLeaseEvidenceMappingResult,
    build_vehicle_lease_constraint_set,
    evaluate_vehicle_lease_constraints,
    map_reviewed_vehicle_lease_evidence,
)
from causa.institutional.contracts.vehicle_lease_evaluation import (
    VehicleLeaseBenchmarkReport,
    VehicleLeaseRedTeamReport,
    run_vehicle_lease_benchmark_suite,
    run_vehicle_lease_red_team_suite,
)


class SyntheticVehicleLeaseEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: VehicleLeaseEvidenceMappingResult
    constraint_set: VehicleLeaseConstraintSet
    reviewed_evaluation: VehicleLeaseEvaluation
    benchmark_report: VehicleLeaseBenchmarkReport
    red_team_report: VehicleLeaseRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticVehicleLeaseEvaluationArtifact":
        expected_set = build_vehicle_lease_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_vehicle_lease_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Vehicle-lease evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_vehicle_lease_evaluation_artifact() -> SyntheticVehicleLeaseEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().vehicle_lease_evidence
    mapping = map_reviewed_vehicle_lease_evidence(evidence)
    constraint_set = build_vehicle_lease_constraint_set(mapping)
    return SyntheticVehicleLeaseEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил об аренде транспортных средств по статьям 632–649 "
            "ГК РФ. Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_vehicle_lease_constraints(constraint_set, mapping.facts),
        benchmark_report=run_vehicle_lease_benchmark_suite(),
        red_team_report=run_vehicle_lease_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
