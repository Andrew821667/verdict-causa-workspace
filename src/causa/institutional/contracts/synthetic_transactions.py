from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.transactions import (
    TransactionsConstraintSet,
    TransactionsEvaluation,
    TransactionsEvidenceMappingResult,
    build_transactions_constraint_set,
    evaluate_transactions_constraints,
    map_reviewed_transactions_evidence,
)
from causa.institutional.contracts.transactions_evaluation import (
    TransactionsBenchmarkReport,
    TransactionsRedTeamReport,
    run_transactions_benchmark_suite,
    run_transactions_red_team_suite,
)


class SyntheticTransactionsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: TransactionsEvidenceMappingResult
    constraint_set: TransactionsConstraintSet
    reviewed_evaluation: TransactionsEvaluation
    benchmark_report: TransactionsBenchmarkReport
    red_team_report: TransactionsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticTransactionsEvaluationArtifact":
        expected_set = build_transactions_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_transactions_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Transactions evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_transactions_evaluation_artifact() -> SyntheticTransactionsEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().transactions_evidence
    mapping = map_reviewed_transactions_evidence(evidence)
    constraint_set = build_transactions_constraint_set(mapping)
    return SyntheticTransactionsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка понятия, видов и условий сделок, а также согласия на их "
            "совершение по статьям 153–157.1 ГК РФ. Не устанавливает судебный факт и не "
            "является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_transactions_constraints(constraint_set, mapping.facts),
        benchmark_report=run_transactions_benchmark_suite(),
        red_team_report=run_transactions_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
