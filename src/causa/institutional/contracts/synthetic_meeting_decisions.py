from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.meeting_decisions import (
    MeetingDecisionsConstraintSet,
    MeetingDecisionsEvaluation,
    MeetingDecisionsEvidenceMappingResult,
    build_meeting_decisions_constraint_set,
    evaluate_meeting_decisions_constraints,
    map_reviewed_meeting_decisions_evidence,
)
from causa.institutional.contracts.meeting_decisions_evaluation import (
    MeetingDecisionsBenchmarkReport,
    MeetingDecisionsRedTeamReport,
    run_meeting_decisions_benchmark_suite,
    run_meeting_decisions_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticMeetingDecisionsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: MeetingDecisionsEvidenceMappingResult
    constraint_set: MeetingDecisionsConstraintSet
    reviewed_evaluation: MeetingDecisionsEvaluation
    benchmark_report: MeetingDecisionsBenchmarkReport
    red_team_report: MeetingDecisionsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticMeetingDecisionsEvaluationArtifact":
        expected_set = build_meeting_decisions_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_meeting_decisions_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Meeting-decisions evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_meeting_decisions_evaluation_artifact() -> (
    SyntheticMeetingDecisionsEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().meeting_decisions_evidence
    mapping = map_reviewed_meeting_decisions_evidence(evidence)
    constraint_set = build_meeting_decisions_constraint_set(mapping)
    return SyntheticMeetingDecisionsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка решений собраний по статьям 181.1–181.5 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_meeting_decisions_constraints(constraint_set, mapping.facts),
        benchmark_report=run_meeting_decisions_benchmark_suite(),
        red_team_report=run_meeting_decisions_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
