from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.insurance import (
    InsuranceConstraintSet,
    InsuranceEvaluation,
    InsuranceEvidenceMappingResult,
    build_insurance_constraint_set,
    evaluate_insurance_constraints,
    map_reviewed_insurance_evidence,
)
from causa.institutional.contracts.insurance_evaluation import (
    InsuranceBenchmarkReport,
    InsuranceRedTeamReport,
    run_insurance_benchmark_suite,
    run_insurance_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticInsuranceEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: InsuranceEvidenceMappingResult
    constraint_set: InsuranceConstraintSet
    reviewed_evaluation: InsuranceEvaluation
    benchmark_report: InsuranceBenchmarkReport
    red_team_report: InsuranceRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticInsuranceEvaluationArtifact":
        expected_set = build_insurance_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_insurance_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Insurance evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_insurance_evaluation_artifact() -> SyntheticInsuranceEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().insurance_evidence
    mapping = map_reviewed_insurance_evidence(evidence)
    constraint_set = build_insurance_constraint_set(mapping)
    return SyntheticInsuranceEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка общих положений о страховании и договоре страхования по "
            "статьям 927–943 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_insurance_constraints(constraint_set, mapping.facts),
        benchmark_report=run_insurance_benchmark_suite(),
        red_team_report=run_insurance_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
