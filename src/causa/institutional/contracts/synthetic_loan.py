from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.loan import (
    LoanConstraintSet,
    LoanEvaluation,
    LoanEvidenceMappingResult,
    build_loan_constraint_set,
    evaluate_loan_constraints,
    map_reviewed_loan_evidence,
)
from causa.institutional.contracts.loan_evaluation import (
    LoanBenchmarkReport,
    LoanRedTeamReport,
    run_loan_benchmark_suite,
    run_loan_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticLoanEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: LoanEvidenceMappingResult
    constraint_set: LoanConstraintSet
    reviewed_evaluation: LoanEvaluation
    benchmark_report: LoanBenchmarkReport
    red_team_report: LoanRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticLoanEvaluationArtifact":
        expected_set = build_loan_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_loan_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Loan evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_loan_evaluation_artifact() -> SyntheticLoanEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().loan_evidence
    mapping = map_reviewed_loan_evidence(evidence)
    constraint_set = build_loan_constraint_set(mapping)
    return SyntheticLoanEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о займе по статьям 807–818 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_loan_constraints(constraint_set, mapping.facts),
        benchmark_report=run_loan_benchmark_suite(),
        red_team_report=run_loan_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
