from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.sale import (
    SaleConstraintSet,
    SaleEvaluation,
    SaleEvidenceMappingResult,
    build_sale_constraint_set,
    evaluate_sale_constraints,
    map_reviewed_sale_evidence,
)
from causa.institutional.contracts.sale_evaluation import (
    SaleBenchmarkReport,
    SaleRedTeamReport,
    run_sale_benchmark_suite,
    run_sale_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticSaleEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: SaleEvidenceMappingResult
    constraint_set: SaleConstraintSet
    reviewed_evaluation: SaleEvaluation
    benchmark_report: SaleBenchmarkReport
    red_team_report: SaleRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticSaleEvaluationArtifact":
        expected_set = build_sale_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_sale_constraints(
            expected_set,
            self.reviewed_mapping.facts,
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Sale evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_sale_evaluation_artifact() -> SyntheticSaleEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().sale_evidence
    mapping = map_reviewed_sale_evidence(evidence)
    constraint_set = build_sale_constraint_set(mapping)
    return SyntheticSaleEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка общих правил договора купли-продажи. "
            "Не устанавливает судебный результат, не рассчитывает суммы и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_sale_constraints(constraint_set, mapping.facts),
        benchmark_report=run_sale_benchmark_suite(),
        red_team_report=run_sale_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/96096/?page=3",
            "https://www.vsrf.ru/files/27530/",
            "https://www.vsrf.ru/documents/reviews/34051/",
            "https://www.consultant.ru/document/cons_doc_LAW_17621/",
        ],
    )
