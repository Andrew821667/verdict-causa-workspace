from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.representations import (
    RepresentationsConstraintSet,
    RepresentationsEvaluation,
    RepresentationsEvidenceMappingResult,
    build_representations_constraint_set,
    evaluate_representations_constraints,
    map_reviewed_representations_evidence,
)
from causa.institutional.contracts.representations_evaluation import (
    RepresentationsBenchmarkReport,
    RepresentationsRedTeamReport,
    run_representations_benchmark_suite,
    run_representations_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticRepresentationsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: RepresentationsEvidenceMappingResult
    constraint_set: RepresentationsConstraintSet
    reviewed_evaluation: RepresentationsEvaluation
    benchmark_report: RepresentationsBenchmarkReport
    red_team_report: RepresentationsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticRepresentationsEvaluationArtifact":
        expected_set = build_representations_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_representations_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Representations evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_representations_evaluation_artifact() -> (
    SyntheticRepresentationsEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().representations_evidence
    mapping = map_reviewed_representations_evidence(evidence)
    constraint_set = build_representations_constraint_set(mapping)
    return SyntheticRepresentationsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о заверениях об обстоятельствах по статье 431.2 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_representations_constraints(constraint_set, mapping.facts),
        benchmark_report=run_representations_benchmark_suite(),
        red_team_report=run_representations_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
