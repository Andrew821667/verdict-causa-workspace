from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.temporal_effect import (
    TemporalEffectConstraintSet,
    TemporalEffectEvaluation,
    TemporalEffectEvidenceMappingResult,
    build_temporal_effect_constraint_set,
    evaluate_temporal_effect_constraints,
    map_reviewed_temporal_effect_evidence,
)
from causa.institutional.contracts.temporal_effect_evaluation import (
    TemporalEffectBenchmarkReport,
    TemporalEffectRedTeamReport,
    run_temporal_effect_benchmark_suite,
    run_temporal_effect_red_team_suite,
)


class SyntheticTemporalEffectEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: TemporalEffectEvidenceMappingResult
    constraint_set: TemporalEffectConstraintSet
    reviewed_evaluation: TemporalEffectEvaluation
    benchmark_report: TemporalEffectBenchmarkReport
    red_team_report: TemporalEffectRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticTemporalEffectEvaluationArtifact":
        expected_set = build_temporal_effect_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_temporal_effect_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Temporal-effect evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_temporal_effect_evaluation_artifact() -> (
    SyntheticTemporalEffectEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().temporal_effect_evidence
    mapping = map_reviewed_temporal_effect_evidence(evidence)
    constraint_set = build_temporal_effect_constraint_set(mapping)
    return SyntheticTemporalEffectEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил действия договора во времени по статьям 425 "
            "и 433 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_temporal_effect_constraints(constraint_set, mapping.facts),
        benchmark_report=run_temporal_effect_benchmark_suite(),
        red_team_report=run_temporal_effect_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
