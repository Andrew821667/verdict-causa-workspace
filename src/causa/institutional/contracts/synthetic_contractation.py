from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.contractation import (
    ContractationConstraintSet,
    ContractationEvaluation,
    ContractationEvidenceMappingResult,
    build_contractation_constraint_set,
    evaluate_contractation_constraints,
    map_reviewed_contractation_evidence,
)
from causa.institutional.contracts.contractation_evaluation import (
    ContractationBenchmarkReport,
    ContractationRedTeamReport,
    run_contractation_benchmark_suite,
    run_contractation_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticContractationEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ContractationEvidenceMappingResult
    constraint_set: ContractationConstraintSet
    reviewed_evaluation: ContractationEvaluation
    benchmark_report: ContractationBenchmarkReport
    red_team_report: ContractationRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticContractationEvaluationArtifact":
        expected_set = build_contractation_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_contractation_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Contractation evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_contractation_evaluation_artifact() -> SyntheticContractationEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().contractation_evidence
    mapping = map_reviewed_contractation_evidence(evidence)
    constraint_set = build_contractation_constraint_set(mapping)
    return SyntheticContractationEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о контрактации по статьям 535–538 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_contractation_constraints(constraint_set, mapping.facts),
        benchmark_report=run_contractation_benchmark_suite(),
        red_team_report=run_contractation_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
