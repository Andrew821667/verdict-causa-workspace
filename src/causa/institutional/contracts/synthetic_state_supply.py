from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.state_supply import (
    StateSupplyConstraintSet,
    StateSupplyEvaluation,
    StateSupplyEvidenceMappingResult,
    build_state_supply_constraint_set,
    evaluate_state_supply_constraints,
    map_reviewed_state_supply_evidence,
)
from causa.institutional.contracts.state_supply_evaluation import (
    StateSupplyBenchmarkReport,
    StateSupplyRedTeamReport,
    run_state_supply_benchmark_suite,
    run_state_supply_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticStateSupplyEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: StateSupplyEvidenceMappingResult
    constraint_set: StateSupplyConstraintSet
    reviewed_evaluation: StateSupplyEvaluation
    benchmark_report: StateSupplyBenchmarkReport
    red_team_report: StateSupplyRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticStateSupplyEvaluationArtifact":
        expected_set = build_state_supply_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_state_supply_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("State supply evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_state_supply_evaluation_artifact() -> SyntheticStateSupplyEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().state_supply_evidence
    mapping = map_reviewed_state_supply_evidence(evidence)
    constraint_set = build_state_supply_constraint_set(mapping)
    return SyntheticStateSupplyEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о поставке товаров для государственных и "
            "муниципальных нужд по статьям 525–534 ГК РФ. Не устанавливает судебный факт "
            "и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_state_supply_constraints(constraint_set, mapping.facts),
        benchmark_report=run_state_supply_benchmark_suite(),
        red_team_report=run_state_supply_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
