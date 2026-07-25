from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.general_obligations import (
    GeneralObligationsConstraintSet,
    GeneralObligationsEvaluation,
    GeneralObligationsEvidenceMappingResult,
    build_general_obligations_constraint_set,
    evaluate_general_obligations_constraints,
    map_reviewed_general_obligations_evidence,
)
from causa.institutional.contracts.general_obligations_evaluation import (
    GeneralObligationsBenchmarkReport,
    GeneralObligationsRedTeamReport,
    run_general_obligations_benchmark_suite,
    run_general_obligations_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticGeneralObligationsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: GeneralObligationsEvidenceMappingResult
    constraint_set: GeneralObligationsConstraintSet
    reviewed_evaluation: GeneralObligationsEvaluation
    benchmark_report: GeneralObligationsBenchmarkReport
    red_team_report: GeneralObligationsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticGeneralObligationsEvaluationArtifact":
        expected_set = build_general_obligations_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_general_obligations_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "General obligations evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_general_obligations_evaluation_artifact() -> (
    SyntheticGeneralObligationsEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().general_obligations_evidence
    mapping = map_reviewed_general_obligations_evidence(evidence)
    constraint_set = build_general_obligations_constraint_set(mapping)
    return SyntheticGeneralObligationsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка общих положений об обязательствах по статьям "
            "307–308.3 ГК РФ. Не устанавливает судебный факт и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_general_obligations_constraints(constraint_set, mapping.facts),
        benchmark_report=run_general_obligations_benchmark_suite(),
        red_team_report=run_general_obligations_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
