from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.contract_concept import (
    ContractConceptConstraintSet,
    ContractConceptEvaluation,
    ContractConceptEvidenceMappingResult,
    build_contract_concept_constraint_set,
    evaluate_contract_concept_constraints,
    map_reviewed_contract_concept_evidence,
)
from causa.institutional.contracts.contract_concept_evaluation import (
    ContractConceptBenchmarkReport,
    ContractConceptRedTeamReport,
    run_contract_concept_benchmark_suite,
    run_contract_concept_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticContractConceptEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ContractConceptEvidenceMappingResult
    constraint_set: ContractConceptConstraintSet
    reviewed_evaluation: ContractConceptEvaluation
    benchmark_report: ContractConceptBenchmarkReport
    red_team_report: ContractConceptRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticContractConceptEvaluationArtifact":
        expected_set = build_contract_concept_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_contract_concept_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Contract-concept evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_contract_concept_evaluation_artifact() -> (
    SyntheticContractConceptEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().contract_concept_evidence
    mapping = map_reviewed_contract_concept_evidence(evidence)
    constraint_set = build_contract_concept_constraint_set(mapping)
    return SyntheticContractConceptEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка понятия договора и применимых к нему правил по "
            "статье 420 ГК РФ. В демонстрационном деле спор ведут две организации по "
            "договору поставки: акт отвечает понятию договора, правила главы 9 и общие "
            "положения об обязательствах применяются, вытеснения не заявлено. Не "
            "устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_contract_concept_constraints(constraint_set, mapping.facts),
        benchmark_report=run_contract_concept_benchmark_suite(),
        red_team_report=run_contract_concept_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95825/"],
    )
