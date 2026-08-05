from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.product_liability import (
    ProductLiabilityConstraintSet,
    ProductLiabilityEvaluation,
    ProductLiabilityEvidenceMappingResult,
    build_product_liability_constraint_set,
    evaluate_product_liability_constraints,
    map_reviewed_product_liability_evidence,
)
from causa.institutional.contracts.product_liability_evaluation import (
    ProductLiabilityBenchmarkReport,
    ProductLiabilityRedTeamReport,
    run_product_liability_benchmark_suite,
    run_product_liability_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticProductLiabilityEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ProductLiabilityEvidenceMappingResult
    constraint_set: ProductLiabilityConstraintSet
    reviewed_evaluation: ProductLiabilityEvaluation
    benchmark_report: ProductLiabilityBenchmarkReport
    red_team_report: ProductLiabilityRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticProductLiabilityEvaluationArtifact":
        expected_set = build_product_liability_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_product_liability_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Product-liability evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_product_liability_evaluation_artifact() -> (
    SyntheticProductLiabilityEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().product_liability_evidence
    mapping = map_reviewed_product_liability_evidence(evidence)
    constraint_set = build_product_liability_constraint_set(mapping)
    return SyntheticProductLiabilityEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о возмещении вреда, причинённого вследствие "
            "недостатков товаров, работ или услуг, по статьям 1095–1098 ГК РФ. Не устанавливает "
            "судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_product_liability_constraints(constraint_set, mapping.facts),
        benchmark_report=run_product_liability_benchmark_suite(),
        red_team_report=run_product_liability_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
