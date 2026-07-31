from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.work_contract import (
    WorkContractConstraintSet,
    WorkContractEvaluation,
    WorkContractEvidenceMappingResult,
    build_work_contract_constraint_set,
    evaluate_work_contract_constraints,
    map_reviewed_work_contract_evidence,
)
from causa.institutional.contracts.work_contract_evaluation import (
    WorkContractBenchmarkReport,
    WorkContractRedTeamReport,
    run_work_contract_benchmark_suite,
    run_work_contract_red_team_suite,
)


class SyntheticWorkContractEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: WorkContractEvidenceMappingResult
    constraint_set: WorkContractConstraintSet
    reviewed_evaluation: WorkContractEvaluation
    benchmark_report: WorkContractBenchmarkReport
    red_team_report: WorkContractRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticWorkContractEvaluationArtifact":
        expected_set = build_work_contract_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_work_contract_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Work-contract evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_work_contract_evaluation_artifact() -> SyntheticWorkContractEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().work_contract_evidence
    mapping = map_reviewed_work_contract_evidence(evidence)
    constraint_set = build_work_contract_constraint_set(mapping)
    return SyntheticWorkContractEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка общих положений о подряде по статьям 702–729 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_work_contract_constraints(constraint_set, mapping.facts),
        benchmark_report=run_work_contract_benchmark_suite(),
        red_team_report=run_work_contract_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
