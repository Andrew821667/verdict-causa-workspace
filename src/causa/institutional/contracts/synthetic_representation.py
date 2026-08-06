from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.representation import (
    RepresentationConstraintSet,
    RepresentationEvaluation,
    RepresentationEvidenceMappingResult,
    build_representation_constraint_set,
    evaluate_representation_constraints,
    map_reviewed_representation_evidence,
)
from causa.institutional.contracts.representation_evaluation import (
    RepresentationBenchmarkReport,
    RepresentationRedTeamReport,
    run_representation_benchmark_suite,
    run_representation_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticRepresentationEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: RepresentationEvidenceMappingResult
    constraint_set: RepresentationConstraintSet
    reviewed_evaluation: RepresentationEvaluation
    benchmark_report: RepresentationBenchmarkReport
    red_team_report: RepresentationRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticRepresentationEvaluationArtifact":
        expected_set = build_representation_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_representation_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Representation evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_representation_evaluation_artifact() -> (
    SyntheticRepresentationEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().representation_evidence
    mapping = map_reviewed_representation_evidence(evidence)
    constraint_set = build_representation_constraint_set(mapping)
    return SyntheticRepresentationEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о представительстве и доверенности по "
            "статьям 182–189 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_representation_constraints(constraint_set, mapping.facts),
        benchmark_report=run_representation_benchmark_suite(),
        red_team_report=run_representation_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95820/",
        ],
    )
