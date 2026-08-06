from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.objects import (
    ObjectsConstraintSet,
    ObjectsEvaluation,
    ObjectsEvidenceMappingResult,
    build_objects_constraint_set,
    evaluate_objects_constraints,
    map_reviewed_objects_evidence,
)
from causa.institutional.contracts.objects_evaluation import (
    ObjectsBenchmarkReport,
    ObjectsRedTeamReport,
    run_objects_benchmark_suite,
    run_objects_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticObjectsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ObjectsEvidenceMappingResult
    constraint_set: ObjectsConstraintSet
    reviewed_evaluation: ObjectsEvaluation
    benchmark_report: ObjectsBenchmarkReport
    red_team_report: ObjectsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticObjectsEvaluationArtifact":
        expected_set = build_objects_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_objects_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Objects evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_objects_evaluation_artifact() -> SyntheticObjectsEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().objects_evidence
    mapping = map_reviewed_objects_evidence(evidence)
    constraint_set = build_objects_constraint_set(mapping)
    return SyntheticObjectsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка объектов гражданских прав, их оборотоспособности и "
            "нематериальных благ по статьям 128–152 ГК РФ. Не устанавливает судебный факт и "
            "не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_objects_constraints(constraint_set, mapping.facts),
        benchmark_report=run_objects_benchmark_suite(),
        red_team_report=run_objects_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
