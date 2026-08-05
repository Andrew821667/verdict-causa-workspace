from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.negotiorum_gestio import (
    NegotiorumGestioConstraintSet,
    NegotiorumGestioEvaluation,
    NegotiorumGestioEvidenceMappingResult,
    build_negotiorum_gestio_constraint_set,
    evaluate_negotiorum_gestio_constraints,
    map_reviewed_negotiorum_gestio_evidence,
)
from causa.institutional.contracts.negotiorum_gestio_evaluation import (
    NegotiorumGestioBenchmarkReport,
    NegotiorumGestioRedTeamReport,
    run_negotiorum_gestio_benchmark_suite,
    run_negotiorum_gestio_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticNegotiorumGestioEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: NegotiorumGestioEvidenceMappingResult
    constraint_set: NegotiorumGestioConstraintSet
    reviewed_evaluation: NegotiorumGestioEvaluation
    benchmark_report: NegotiorumGestioBenchmarkReport
    red_team_report: NegotiorumGestioRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticNegotiorumGestioEvaluationArtifact":
        expected_set = build_negotiorum_gestio_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_negotiorum_gestio_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Negotiorum-gestio evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_negotiorum_gestio_evaluation_artifact() -> (
    SyntheticNegotiorumGestioEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().negotiorum_gestio_evidence
    mapping = map_reviewed_negotiorum_gestio_evidence(evidence)
    constraint_set = build_negotiorum_gestio_constraint_set(mapping)
    return SyntheticNegotiorumGestioEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о действиях в чужом интересе без поручения по "
            "статьям 980–989 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_negotiorum_gestio_constraints(constraint_set, mapping.facts),
        benchmark_report=run_negotiorum_gestio_benchmark_suite(),
        red_team_report=run_negotiorum_gestio_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
