from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.commercial_credit import (
    CommercialCreditConstraintSet,
    CommercialCreditEvaluation,
    CommercialCreditEvidenceMappingResult,
    build_commercial_credit_constraint_set,
    evaluate_commercial_credit_constraints,
    map_reviewed_commercial_credit_evidence,
)
from causa.institutional.contracts.commercial_credit_evaluation import (
    CommercialCreditBenchmarkReport,
    CommercialCreditRedTeamReport,
    run_commercial_credit_benchmark_suite,
    run_commercial_credit_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticCommercialCreditEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: CommercialCreditEvidenceMappingResult
    constraint_set: CommercialCreditConstraintSet
    reviewed_evaluation: CommercialCreditEvaluation
    benchmark_report: CommercialCreditBenchmarkReport
    red_team_report: CommercialCreditRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticCommercialCreditEvaluationArtifact":
        expected_set = build_commercial_credit_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_commercial_credit_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Commercial-credit evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_commercial_credit_evaluation_artifact() -> (
    SyntheticCommercialCreditEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().commercial_credit_evidence
    mapping = map_reviewed_commercial_credit_evidence(evidence)
    constraint_set = build_commercial_credit_constraint_set(mapping)
    return SyntheticCommercialCreditEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о товарном и коммерческом кредите по статьям 822–823 "
            "ГК РФ. Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_commercial_credit_constraints(constraint_set, mapping.facts),
        benchmark_report=run_commercial_credit_benchmark_suite(),
        red_team_report=run_commercial_credit_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
