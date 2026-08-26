from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.escrow_deposit import (
    EscrowDepositConstraintSet,
    EscrowDepositEvaluation,
    EscrowDepositEvidenceMappingResult,
    build_escrow_deposit_constraint_set,
    evaluate_escrow_deposit_constraints,
    map_reviewed_escrow_deposit_evidence,
)
from causa.institutional.contracts.escrow_deposit_evaluation import (
    EscrowDepositBenchmarkReport,
    EscrowDepositRedTeamReport,
    run_escrow_deposit_benchmark_suite,
    run_escrow_deposit_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticEscrowDepositEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: EscrowDepositEvidenceMappingResult
    constraint_set: EscrowDepositConstraintSet
    reviewed_evaluation: EscrowDepositEvaluation
    benchmark_report: EscrowDepositBenchmarkReport
    red_team_report: EscrowDepositRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticEscrowDepositEvaluationArtifact":
        expected_set = build_escrow_deposit_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_escrow_deposit_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Escrow-deposit evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_escrow_deposit_evaluation_artifact() -> (
    SyntheticEscrowDepositEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().escrow_deposit_evidence
    mapping = map_reviewed_escrow_deposit_evidence(evidence)
    constraint_set = build_escrow_deposit_constraint_set(mapping)
    return SyntheticEscrowDepositEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка условного депонирования (эскроу) по статьям "
            "926.1–926.8 ГК РФ. Не устанавливает судебный факт и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_escrow_deposit_constraints(constraint_set, mapping.facts),
        benchmark_report=run_escrow_deposit_benchmark_suite(),
        red_team_report=run_escrow_deposit_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
