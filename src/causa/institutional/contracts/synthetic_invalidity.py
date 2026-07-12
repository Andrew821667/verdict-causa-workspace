from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.invalidity import (
    InvalidityConstraintSet,
    InvalidityEvaluation,
    InvalidityEvidenceMappingResult,
    build_invalidity_constraint_set,
    evaluate_invalidity_constraints,
    map_reviewed_invalidity_evidence,
)
from causa.institutional.contracts.invalidity_evaluation import (
    InvalidityBenchmarkReport,
    InvalidityRedTeamReport,
    run_invalidity_benchmark_suite,
    run_invalidity_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticInvalidityEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: InvalidityEvidenceMappingResult
    constraint_set: InvalidityConstraintSet
    reviewed_evaluation: InvalidityEvaluation
    benchmark_report: InvalidityBenchmarkReport
    red_team_report: InvalidityRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticInvalidityEvaluationArtifact":
        expected_set = build_invalidity_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_invalidity_constraints(
            expected_set,
            self.reviewed_mapping.facts,
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Invalidity evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_invalidity_evaluation_artifact() -> SyntheticInvalidityEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().invalidity_evidence
    mapping = map_reviewed_invalidity_evidence(evidence)
    constraint_set = build_invalidity_constraint_set(mapping)
    return SyntheticInvalidityEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка недействительности сделки. Не признает сделку "
            "недействительной и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_invalidity_constraints(constraint_set, mapping.facts),
        benchmark_report=run_invalidity_benchmark_suite(),
        red_team_report=run_invalidity_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
            "https://vsrf.ru/documents/own/8435/",
        ],
    )
