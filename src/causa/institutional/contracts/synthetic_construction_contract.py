from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.construction_contract import (
    ConstructionContractConstraintSet,
    ConstructionContractEvaluation,
    ConstructionContractEvidenceMappingResult,
    build_construction_contract_constraint_set,
    evaluate_construction_contract_constraints,
    map_reviewed_construction_contract_evidence,
)
from causa.institutional.contracts.construction_contract_evaluation import (
    ConstructionContractBenchmarkReport,
    ConstructionContractRedTeamReport,
    run_construction_contract_benchmark_suite,
    run_construction_contract_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticConstructionContractEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ConstructionContractEvidenceMappingResult
    constraint_set: ConstructionContractConstraintSet
    reviewed_evaluation: ConstructionContractEvaluation
    benchmark_report: ConstructionContractBenchmarkReport
    red_team_report: ConstructionContractRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticConstructionContractEvaluationArtifact":
        expected_set = build_construction_contract_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_construction_contract_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Construction-contract evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_construction_contract_evaluation_artifact() -> (
    SyntheticConstructionContractEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().construction_contract_evidence
    mapping = map_reviewed_construction_contract_evidence(evidence)
    constraint_set = build_construction_contract_constraint_set(mapping)
    return SyntheticConstructionContractEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о строительном подряде по статьям 740–757 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_construction_contract_constraints(
            constraint_set, mapping.facts
        ),
        benchmark_report=run_construction_contract_benchmark_suite(),
        red_team_report=run_construction_contract_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
