from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.forwarding import (
    ForwardingConstraintSet,
    ForwardingEvaluation,
    ForwardingEvidenceMappingResult,
    build_forwarding_constraint_set,
    evaluate_forwarding_constraints,
    map_reviewed_forwarding_evidence,
)
from causa.institutional.contracts.forwarding_evaluation import (
    ForwardingBenchmarkReport,
    ForwardingRedTeamReport,
    run_forwarding_benchmark_suite,
    run_forwarding_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticForwardingEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ForwardingEvidenceMappingResult
    constraint_set: ForwardingConstraintSet
    reviewed_evaluation: ForwardingEvaluation
    benchmark_report: ForwardingBenchmarkReport
    red_team_report: ForwardingRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticForwardingEvaluationArtifact":
        expected_set = build_forwarding_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_forwarding_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Forwarding evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_forwarding_evaluation_artifact() -> SyntheticForwardingEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().forwarding_evidence
    mapping = map_reviewed_forwarding_evidence(evidence)
    constraint_set = build_forwarding_constraint_set(mapping)
    return SyntheticForwardingEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о транспортной экспедиции по статьям 801–806 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_forwarding_constraints(constraint_set, mapping.facts),
        benchmark_report=run_forwarding_benchmark_suite(),
        red_team_report=run_forwarding_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
