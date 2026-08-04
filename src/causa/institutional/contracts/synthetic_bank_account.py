from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.bank_account import (
    BankAccountConstraintSet,
    BankAccountEvaluation,
    BankAccountEvidenceMappingResult,
    build_bank_account_constraint_set,
    evaluate_bank_account_constraints,
    map_reviewed_bank_account_evidence,
)
from causa.institutional.contracts.bank_account_evaluation import (
    BankAccountBenchmarkReport,
    BankAccountRedTeamReport,
    run_bank_account_benchmark_suite,
    run_bank_account_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticBankAccountEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: BankAccountEvidenceMappingResult
    constraint_set: BankAccountConstraintSet
    reviewed_evaluation: BankAccountEvaluation
    benchmark_report: BankAccountBenchmarkReport
    red_team_report: BankAccountRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticBankAccountEvaluationArtifact":
        expected_set = build_bank_account_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_bank_account_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Bank-account evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_bank_account_evaluation_artifact() -> SyntheticBankAccountEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().bank_account_evidence
    mapping = map_reviewed_bank_account_evidence(evidence)
    constraint_set = build_bank_account_constraint_set(mapping)
    return SyntheticBankAccountEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о банковском счёте по статьям 845–860 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_bank_account_constraints(constraint_set, mapping.facts),
        benchmark_report=run_bank_account_benchmark_suite(),
        red_team_report=run_bank_account_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
