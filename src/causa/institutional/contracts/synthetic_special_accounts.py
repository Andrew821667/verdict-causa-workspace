from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.special_accounts import (
    SpecialAccountsConstraintSet,
    SpecialAccountsEvaluation,
    SpecialAccountsEvidenceMappingResult,
    build_special_accounts_constraint_set,
    evaluate_special_accounts_constraints,
    map_reviewed_special_accounts_evidence,
)
from causa.institutional.contracts.special_accounts_evaluation import (
    SpecialAccountsBenchmarkReport,
    SpecialAccountsRedTeamReport,
    run_special_accounts_benchmark_suite,
    run_special_accounts_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticSpecialAccountsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: SpecialAccountsEvidenceMappingResult
    constraint_set: SpecialAccountsConstraintSet
    reviewed_evaluation: SpecialAccountsEvaluation
    benchmark_report: SpecialAccountsBenchmarkReport
    red_team_report: SpecialAccountsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticSpecialAccountsEvaluationArtifact":
        expected_set = build_special_accounts_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_special_accounts_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Special-accounts evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_special_accounts_evaluation_artifact() -> (
    SyntheticSpecialAccountsEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().special_accounts_evidence
    mapping = map_reviewed_special_accounts_evidence(evidence)
    constraint_set = build_special_accounts_constraint_set(mapping)
    return SyntheticSpecialAccountsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка специальных видов банковских счетов по статьям "
            "860.1–860.15 ГК РФ. Не устанавливает судебный факт и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_special_accounts_constraints(constraint_set, mapping.facts),
        benchmark_report=run_special_accounts_benchmark_suite(),
        red_team_report=run_special_accounts_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
