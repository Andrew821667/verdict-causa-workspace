from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.civil_principles import (
    CivilPrinciplesConstraintSet,
    CivilPrinciplesEvaluation,
    CivilPrinciplesEvidenceMappingResult,
    build_civil_principles_constraint_set,
    evaluate_civil_principles_constraints,
    map_reviewed_civil_principles_evidence,
)
from causa.institutional.contracts.civil_principles_evaluation import (
    CivilPrinciplesBenchmarkReport,
    CivilPrinciplesRedTeamReport,
    run_civil_principles_benchmark_suite,
    run_civil_principles_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticCivilPrinciplesEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: CivilPrinciplesEvidenceMappingResult
    constraint_set: CivilPrinciplesConstraintSet
    reviewed_evaluation: CivilPrinciplesEvaluation
    benchmark_report: CivilPrinciplesBenchmarkReport
    red_team_report: CivilPrinciplesRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticCivilPrinciplesEvaluationArtifact":
        expected_set = build_civil_principles_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_civil_principles_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Property-rights evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_civil_principles_evaluation_artifact() -> (
    SyntheticCivilPrinciplesEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().civil_principles_evidence
    mapping = map_reviewed_civil_principles_evidence(evidence)
    constraint_set = build_civil_principles_constraint_set(mapping)
    return SyntheticCivilPrinciplesEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка основных начал гражданского законодательства и "
            "правил о защите гражданских прав по статьям 1–16.1 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_civil_principles_constraints(constraint_set, mapping.facts),
        benchmark_report=run_civil_principles_benchmark_suite(),
        red_team_report=run_civil_principles_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
