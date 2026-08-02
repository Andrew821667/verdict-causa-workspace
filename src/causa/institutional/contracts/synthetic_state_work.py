from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.state_work import (
    StateWorkConstraintSet,
    StateWorkEvaluation,
    StateWorkEvidenceMappingResult,
    build_state_work_constraint_set,
    evaluate_state_work_constraints,
    map_reviewed_state_work_evidence,
)
from causa.institutional.contracts.state_work_evaluation import (
    StateWorkBenchmarkReport,
    StateWorkRedTeamReport,
    run_state_work_benchmark_suite,
    run_state_work_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticStateWorkEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: StateWorkEvidenceMappingResult
    constraint_set: StateWorkConstraintSet
    reviewed_evaluation: StateWorkEvaluation
    benchmark_report: StateWorkBenchmarkReport
    red_team_report: StateWorkRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticStateWorkEvaluationArtifact":
        expected_set = build_state_work_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_state_work_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("State-work evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_state_work_evaluation_artifact() -> SyntheticStateWorkEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().state_work_evidence
    mapping = map_reviewed_state_work_evidence(evidence)
    constraint_set = build_state_work_constraint_set(mapping)
    return SyntheticStateWorkEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о подрядных работах для государственных и "
            "муниципальных нужд по статьям 763–768 ГК РФ. Не устанавливает судебный факт и не "
            "является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_state_work_constraints(constraint_set, mapping.facts),
        benchmark_report=run_state_work_benchmark_suite(),
        red_team_report=run_state_work_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
