from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.storage import (
    StorageConstraintSet,
    StorageEvaluation,
    StorageEvidenceMappingResult,
    build_storage_constraint_set,
    evaluate_storage_constraints,
    map_reviewed_storage_evidence,
)
from causa.institutional.contracts.storage_evaluation import (
    StorageBenchmarkReport,
    StorageRedTeamReport,
    run_storage_benchmark_suite,
    run_storage_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticStorageEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: StorageEvidenceMappingResult
    constraint_set: StorageConstraintSet
    reviewed_evaluation: StorageEvaluation
    benchmark_report: StorageBenchmarkReport
    red_team_report: StorageRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticStorageEvaluationArtifact":
        expected_set = build_storage_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_storage_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Storage evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_storage_evaluation_artifact() -> SyntheticStorageEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().storage_evidence
    mapping = map_reviewed_storage_evidence(evidence)
    constraint_set = build_storage_constraint_set(mapping)
    return SyntheticStorageEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка общих положений о хранении по статьям 886–906 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_storage_constraints(constraint_set, mapping.facts),
        benchmark_report=run_storage_benchmark_suite(),
        red_team_report=run_storage_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
