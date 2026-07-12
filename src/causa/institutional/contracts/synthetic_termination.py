from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.termination import (
    TerminationConstraintSet,
    TerminationEvaluation,
    TerminationEvidenceMappingResult,
    build_termination_constraint_set,
    evaluate_termination_constraints,
    map_reviewed_termination_evidence,
)
from causa.institutional.contracts.termination_evaluation import (
    TerminationBenchmarkReport,
    TerminationRedTeamReport,
    run_termination_benchmark_suite,
    run_termination_red_team_suite,
)


class SyntheticTerminationEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: TerminationEvidenceMappingResult
    constraint_set: TerminationConstraintSet
    reviewed_evaluation: TerminationEvaluation
    benchmark_report: TerminationBenchmarkReport
    red_team_report: TerminationRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticTerminationEvaluationArtifact":
        expected_set = build_termination_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_termination_constraints(
            expected_set,
            self.reviewed_mapping.facts,
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Termination evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_termination_evaluation_artifact() -> SyntheticTerminationEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().termination_evidence
    mapping = map_reviewed_termination_evidence(evidence)
    constraint_set = build_termination_constraint_set(mapping)
    return SyntheticTerminationEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка изменения и расторжения договора. "
            "Не устанавливает судебный результат и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_termination_constraints(
            constraint_set,
            mapping.facts,
        ),
        benchmark_report=run_termination_benchmark_suite(),
        red_team_report=run_termination_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
            "https://vsrf.ru/documents/own/8524/",
            "https://vsrf.ru/documents/own/30139/",
        ],
    )
