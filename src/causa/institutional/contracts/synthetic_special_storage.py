from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.special_storage import (
    SpecialStorageConstraintSet,
    SpecialStorageEvaluation,
    SpecialStorageEvidenceMappingResult,
    build_special_storage_constraint_set,
    evaluate_special_storage_constraints,
    map_reviewed_special_storage_evidence,
)
from causa.institutional.contracts.special_storage_evaluation import (
    SpecialStorageBenchmarkReport,
    SpecialStorageRedTeamReport,
    run_special_storage_benchmark_suite,
    run_special_storage_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticSpecialStorageEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: SpecialStorageEvidenceMappingResult
    constraint_set: SpecialStorageConstraintSet
    reviewed_evaluation: SpecialStorageEvaluation
    benchmark_report: SpecialStorageBenchmarkReport
    red_team_report: SpecialStorageRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticSpecialStorageEvaluationArtifact":
        expected_set = build_special_storage_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_special_storage_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Special-storage evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_special_storage_evaluation_artifact() -> (
    SyntheticSpecialStorageEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().special_storage_evidence
    mapping = map_reviewed_special_storage_evidence(evidence)
    constraint_set = build_special_storage_constraint_set(mapping)
    return SyntheticSpecialStorageEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о специальных видах хранения по статьям 919–926 "
            "ГК РФ. Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_special_storage_constraints(constraint_set, mapping.facts),
        benchmark_report=run_special_storage_benchmark_suite(),
        red_team_report=run_special_storage_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
