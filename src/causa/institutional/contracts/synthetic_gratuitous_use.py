from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.gratuitous_use import (
    GratuitousUseConstraintSet,
    GratuitousUseEvaluation,
    GratuitousUseEvidenceMappingResult,
    build_gratuitous_use_constraint_set,
    evaluate_gratuitous_use_constraints,
    map_reviewed_gratuitous_use_evidence,
)
from causa.institutional.contracts.gratuitous_use_evaluation import (
    GratuitousUseBenchmarkReport,
    GratuitousUseRedTeamReport,
    run_gratuitous_use_benchmark_suite,
    run_gratuitous_use_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticGratuitousUseEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: GratuitousUseEvidenceMappingResult
    constraint_set: GratuitousUseConstraintSet
    reviewed_evaluation: GratuitousUseEvaluation
    benchmark_report: GratuitousUseBenchmarkReport
    red_team_report: GratuitousUseRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticGratuitousUseEvaluationArtifact":
        expected_set = build_gratuitous_use_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_gratuitous_use_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Gratuitous-use evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_gratuitous_use_evaluation_artifact() -> (
    SyntheticGratuitousUseEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().gratuitous_use_evidence
    mapping = map_reviewed_gratuitous_use_evidence(evidence)
    constraint_set = build_gratuitous_use_constraint_set(mapping)
    return SyntheticGratuitousUseEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о безвозмездном пользовании (ссуде) по статьям "
            "689–701 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_gratuitous_use_constraints(constraint_set, mapping.facts),
        benchmark_report=run_gratuitous_use_benchmark_suite(),
        red_team_report=run_gratuitous_use_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
