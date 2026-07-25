from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.retail_sale import (
    RetailSaleConstraintSet,
    RetailSaleEvaluation,
    RetailSaleEvidenceMappingResult,
    build_retail_sale_constraint_set,
    evaluate_retail_sale_constraints,
    map_reviewed_retail_sale_evidence,
)
from causa.institutional.contracts.retail_sale_evaluation import (
    RetailSaleBenchmarkReport,
    RetailSaleRedTeamReport,
    run_retail_sale_benchmark_suite,
    run_retail_sale_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticRetailSaleEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: RetailSaleEvidenceMappingResult
    constraint_set: RetailSaleConstraintSet
    reviewed_evaluation: RetailSaleEvaluation
    benchmark_report: RetailSaleBenchmarkReport
    red_team_report: RetailSaleRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticRetailSaleEvaluationArtifact":
        expected_set = build_retail_sale_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_retail_sale_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Retail sale evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_retail_sale_evaluation_artifact() -> SyntheticRetailSaleEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().retail_sale_evidence
    mapping = map_reviewed_retail_sale_evidence(evidence)
    constraint_set = build_retail_sale_constraint_set(mapping)
    return SyntheticRetailSaleEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о розничной купле-продаже по статьям "
            "492–505 ГК РФ. Не устанавливает судебный факт и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_retail_sale_constraints(constraint_set, mapping.facts),
        benchmark_report=run_retail_sale_benchmark_suite(),
        red_team_report=run_retail_sale_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
