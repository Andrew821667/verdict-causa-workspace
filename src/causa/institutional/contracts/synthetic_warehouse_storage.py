from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.warehouse_storage import (
    WarehouseStorageConstraintSet,
    WarehouseStorageEvaluation,
    WarehouseStorageEvidenceMappingResult,
    build_warehouse_storage_constraint_set,
    evaluate_warehouse_storage_constraints,
    map_reviewed_warehouse_storage_evidence,
)
from causa.institutional.contracts.warehouse_storage_evaluation import (
    WarehouseStorageBenchmarkReport,
    WarehouseStorageRedTeamReport,
    run_warehouse_storage_benchmark_suite,
    run_warehouse_storage_red_team_suite,
)


class SyntheticWarehouseStorageEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: WarehouseStorageEvidenceMappingResult
    constraint_set: WarehouseStorageConstraintSet
    reviewed_evaluation: WarehouseStorageEvaluation
    benchmark_report: WarehouseStorageBenchmarkReport
    red_team_report: WarehouseStorageRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticWarehouseStorageEvaluationArtifact":
        expected_set = build_warehouse_storage_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_warehouse_storage_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Warehouse-storage evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_warehouse_storage_evaluation_artifact() -> (
    SyntheticWarehouseStorageEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().warehouse_storage_evidence
    mapping = map_reviewed_warehouse_storage_evidence(evidence)
    constraint_set = build_warehouse_storage_constraint_set(mapping)
    return SyntheticWarehouseStorageEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о хранении на товарном складе по статьям 907–918 "
            "ГК РФ. Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_warehouse_storage_constraints(constraint_set, mapping.facts),
        benchmark_report=run_warehouse_storage_benchmark_suite(),
        red_team_report=run_warehouse_storage_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
