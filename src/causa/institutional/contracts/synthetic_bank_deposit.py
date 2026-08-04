from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.bank_deposit import (
    BankDepositConstraintSet,
    BankDepositEvaluation,
    BankDepositEvidenceMappingResult,
    build_bank_deposit_constraint_set,
    evaluate_bank_deposit_constraints,
    map_reviewed_bank_deposit_evidence,
)
from causa.institutional.contracts.bank_deposit_evaluation import (
    BankDepositBenchmarkReport,
    BankDepositRedTeamReport,
    run_bank_deposit_benchmark_suite,
    run_bank_deposit_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticBankDepositEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: BankDepositEvidenceMappingResult
    constraint_set: BankDepositConstraintSet
    reviewed_evaluation: BankDepositEvaluation
    benchmark_report: BankDepositBenchmarkReport
    red_team_report: BankDepositRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticBankDepositEvaluationArtifact":
        expected_set = build_bank_deposit_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_bank_deposit_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Bank-deposit evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_bank_deposit_evaluation_artifact() -> SyntheticBankDepositEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().bank_deposit_evidence
    mapping = map_reviewed_bank_deposit_evidence(evidence)
    constraint_set = build_bank_deposit_constraint_set(mapping)
    return SyntheticBankDepositEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о банковском вкладе по статьям 834–844 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_bank_deposit_constraints(constraint_set, mapping.facts),
        benchmark_report=run_bank_deposit_benchmark_suite(),
        red_team_report=run_bank_deposit_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
