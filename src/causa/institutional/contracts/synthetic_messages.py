from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.messages import (
    MessagesConstraintSet,
    MessagesEvaluation,
    MessagesEvidenceMappingResult,
    build_messages_constraint_set,
    evaluate_messages_constraints,
    map_reviewed_messages_evidence,
)
from causa.institutional.contracts.messages_evaluation import (
    MessagesBenchmarkReport,
    MessagesRedTeamReport,
    run_messages_benchmark_suite,
    run_messages_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticMessagesEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: MessagesEvidenceMappingResult
    constraint_set: MessagesConstraintSet
    reviewed_evaluation: MessagesEvaluation
    benchmark_report: MessagesBenchmarkReport
    red_team_report: MessagesRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticMessagesEvaluationArtifact":
        expected_set = build_messages_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_messages_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Messages evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_messages_evaluation_artifact() -> SyntheticMessagesEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().messages_evidence
    mapping = map_reviewed_messages_evidence(evidence)
    constraint_set = build_messages_constraint_set(mapping)
    return SyntheticMessagesEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка юридически значимых сообщений по статье 165.1 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_messages_constraints(constraint_set, mapping.facts),
        benchmark_report=run_messages_benchmark_suite(),
        red_team_report=run_messages_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
