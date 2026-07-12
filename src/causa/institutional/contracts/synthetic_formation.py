from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.formation import (
    FormationConstraintSet,
    FormationEvaluation,
    FormationEvidenceMappingResult,
    build_formation_constraint_set,
    evaluate_formation_constraints,
    map_reviewed_formation_evidence,
)
from causa.institutional.contracts.formation_evaluation import (
    FormationBenchmarkReport,
    FormationRedTeamReport,
    run_formation_benchmark_suite,
    run_formation_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticFormationEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: FormationEvidenceMappingResult
    constraint_set: FormationConstraintSet
    reviewed_evaluation: FormationEvaluation
    benchmark_report: FormationBenchmarkReport
    red_team_report: FormationRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticFormationEvaluationArtifact":
        expected_set = build_formation_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_formation_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Formation evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_formation_evaluation_artifact() -> SyntheticFormationEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().formation_evidence
    mapping = map_reviewed_formation_evidence(evidence)
    constraint_set = build_formation_constraint_set(mapping)
    return SyntheticFormationEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка формальных предпосылок заключения договора. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_formation_constraints(constraint_set, mapping.facts),
        benchmark_report=run_formation_benchmark_suite(),
        red_team_report=run_formation_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
            "https://vsrf.ru/documents/own/27540/",
        ],
    )
