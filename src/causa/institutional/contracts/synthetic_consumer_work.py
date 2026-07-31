from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.consumer_work import (
    ConsumerWorkConstraintSet,
    ConsumerWorkEvaluation,
    ConsumerWorkEvidenceMappingResult,
    build_consumer_work_constraint_set,
    evaluate_consumer_work_constraints,
    map_reviewed_consumer_work_evidence,
)
from causa.institutional.contracts.consumer_work_evaluation import (
    ConsumerWorkBenchmarkReport,
    ConsumerWorkRedTeamReport,
    run_consumer_work_benchmark_suite,
    run_consumer_work_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticConsumerWorkEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ConsumerWorkEvidenceMappingResult
    constraint_set: ConsumerWorkConstraintSet
    reviewed_evaluation: ConsumerWorkEvaluation
    benchmark_report: ConsumerWorkBenchmarkReport
    red_team_report: ConsumerWorkRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticConsumerWorkEvaluationArtifact":
        expected_set = build_consumer_work_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_consumer_work_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Consumer-work evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_consumer_work_evaluation_artifact() -> SyntheticConsumerWorkEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().consumer_work_evidence
    mapping = map_reviewed_consumer_work_evidence(evidence)
    constraint_set = build_consumer_work_constraint_set(mapping)
    return SyntheticConsumerWorkEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о бытовом подряде по статьям 730–739 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_consumer_work_constraints(constraint_set, mapping.facts),
        benchmark_report=run_consumer_work_benchmark_suite(),
        red_team_report=run_consumer_work_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
