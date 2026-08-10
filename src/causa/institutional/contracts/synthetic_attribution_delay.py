from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.attribution_delay import (
    AttributionDelayConstraintSet,
    AttributionDelayEvaluation,
    AttributionDelayEvidenceMappingResult,
    build_attribution_delay_constraint_set,
    evaluate_attribution_delay_constraints,
    map_reviewed_attribution_delay_evidence,
)
from causa.institutional.contracts.attribution_delay_evaluation import (
    AttributionDelayBenchmarkReport,
    AttributionDelayRedTeamReport,
    run_attribution_delay_benchmark_suite,
    run_attribution_delay_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticAttributionDelayEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: AttributionDelayEvidenceMappingResult
    constraint_set: AttributionDelayConstraintSet
    reviewed_evaluation: AttributionDelayEvaluation
    benchmark_report: AttributionDelayBenchmarkReport
    red_team_report: AttributionDelayRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticAttributionDelayEvaluationArtifact":
        expected_set = build_attribution_delay_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_attribution_delay_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Attribution and delay evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_attribution_delay_evaluation_artifact() -> (
    SyntheticAttributionDelayEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().attribution_delay_evidence
    mapping = map_reviewed_attribution_delay_evidence(evidence)
    constraint_set = build_attribution_delay_constraint_set(mapping)
    return SyntheticAttributionDelayEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка возложения ответственности и просрочки сторон по "
            "статьям 402–406 ГК РФ. Не устанавливает судебный факт и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_attribution_delay_constraints(constraint_set, mapping.facts),
        benchmark_report=run_attribution_delay_benchmark_suite(),
        red_team_report=run_attribution_delay_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
