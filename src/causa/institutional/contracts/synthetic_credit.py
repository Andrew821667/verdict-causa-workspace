from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.credit import (
    CreditConstraintSet,
    CreditEvaluation,
    CreditEvidenceMappingResult,
    build_credit_constraint_set,
    evaluate_credit_constraints,
    map_reviewed_credit_evidence,
)
from causa.institutional.contracts.credit_evaluation import (
    CreditBenchmarkReport,
    CreditRedTeamReport,
    run_credit_benchmark_suite,
    run_credit_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticCreditEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: CreditEvidenceMappingResult
    constraint_set: CreditConstraintSet
    reviewed_evaluation: CreditEvaluation
    benchmark_report: CreditBenchmarkReport
    red_team_report: CreditRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticCreditEvaluationArtifact":
        expected_set = build_credit_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_credit_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Credit evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_credit_evaluation_artifact() -> SyntheticCreditEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().credit_evidence
    mapping = map_reviewed_credit_evidence(evidence)
    constraint_set = build_credit_constraint_set(mapping)
    return SyntheticCreditEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о кредите по статьям 819–821.1 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_credit_constraints(constraint_set, mapping.facts),
        benchmark_report=run_credit_benchmark_suite(),
        red_team_report=run_credit_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
