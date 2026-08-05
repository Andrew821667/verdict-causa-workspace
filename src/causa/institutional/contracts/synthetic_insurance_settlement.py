from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.insurance_settlement import (
    InsuranceSettlementConstraintSet,
    InsuranceSettlementEvaluation,
    InsuranceSettlementEvidenceMappingResult,
    build_insurance_settlement_constraint_set,
    evaluate_insurance_settlement_constraints,
    map_reviewed_insurance_settlement_evidence,
)
from causa.institutional.contracts.insurance_settlement_evaluation import (
    InsuranceSettlementBenchmarkReport,
    InsuranceSettlementRedTeamReport,
    run_insurance_settlement_benchmark_suite,
    run_insurance_settlement_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticInsuranceSettlementEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: InsuranceSettlementEvidenceMappingResult
    constraint_set: InsuranceSettlementConstraintSet
    reviewed_evaluation: InsuranceSettlementEvaluation
    benchmark_report: InsuranceSettlementBenchmarkReport
    red_team_report: InsuranceSettlementRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticInsuranceSettlementEvaluationArtifact":
        expected_set = build_insurance_settlement_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_insurance_settlement_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Insurance-settlement evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_insurance_settlement_evaluation_artifact() -> (
    SyntheticInsuranceSettlementEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().insurance_settlement_evidence
    mapping = map_reviewed_insurance_settlement_evidence(evidence)
    constraint_set = build_insurance_settlement_constraint_set(mapping)
    return SyntheticInsuranceSettlementEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил об исполнении страхового обязательства по "
            "статьям 944–970 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_insurance_settlement_constraints(
            constraint_set, mapping.facts
        ),
        benchmark_report=run_insurance_settlement_benchmark_suite(),
        red_team_report=run_insurance_settlement_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
