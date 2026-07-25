from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.adhesion import (
    AdhesionConstraintSet,
    AdhesionEvaluation,
    AdhesionEvidenceMappingResult,
    build_adhesion_constraint_set,
    evaluate_adhesion_constraints,
    map_reviewed_adhesion_evidence,
)
from causa.institutional.contracts.adhesion_evaluation import (
    AdhesionBenchmarkReport,
    AdhesionRedTeamReport,
    run_adhesion_benchmark_suite,
    run_adhesion_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticAdhesionEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: AdhesionEvidenceMappingResult
    constraint_set: AdhesionConstraintSet
    reviewed_evaluation: AdhesionEvaluation
    benchmark_report: AdhesionBenchmarkReport
    red_team_report: AdhesionRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticAdhesionEvaluationArtifact":
        expected_set = build_adhesion_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_adhesion_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Adhesion evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_adhesion_evaluation_artifact() -> SyntheticAdhesionEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().adhesion_evidence
    mapping = map_reviewed_adhesion_evidence(evidence)
    constraint_set = build_adhesion_constraint_set(mapping)
    return SyntheticAdhesionEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о договоре присоединения по статье 428 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_adhesion_constraints(constraint_set, mapping.facts),
        benchmark_report=run_adhesion_benchmark_suite(),
        red_team_report=run_adhesion_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
