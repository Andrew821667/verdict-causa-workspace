from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.terms import (
    TermsConstraintSet,
    TermsEvaluation,
    TermsEvidenceMappingResult,
    build_terms_constraint_set,
    evaluate_terms_constraints,
    map_reviewed_terms_evidence,
)
from causa.institutional.contracts.terms_evaluation import (
    TermsBenchmarkReport,
    TermsRedTeamReport,
    run_terms_benchmark_suite,
    run_terms_red_team_suite,
)


class SyntheticTermsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: TermsEvidenceMappingResult
    constraint_set: TermsConstraintSet
    reviewed_evaluation: TermsEvaluation
    benchmark_report: TermsBenchmarkReport
    red_team_report: TermsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticTermsEvaluationArtifact":
        expected_set = build_terms_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_terms_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Terms evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_terms_evaluation_artifact() -> SyntheticTermsEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().terms_evidence
    mapping = map_reviewed_terms_evidence(evidence)
    constraint_set = build_terms_constraint_set(mapping)
    return SyntheticTermsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил об исчислении сроков по статьям 190–194 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_terms_constraints(constraint_set, mapping.facts),
        benchmark_report=run_terms_benchmark_suite(),
        red_team_report=run_terms_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
