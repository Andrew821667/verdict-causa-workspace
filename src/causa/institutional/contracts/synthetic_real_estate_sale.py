from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.real_estate_sale import (
    RealEstateSaleConstraintSet,
    RealEstateSaleEvaluation,
    RealEstateSaleEvidenceMappingResult,
    build_real_estate_sale_constraint_set,
    evaluate_real_estate_sale_constraints,
    map_reviewed_real_estate_sale_evidence,
)
from causa.institutional.contracts.real_estate_sale_evaluation import (
    RealEstateSaleBenchmarkReport,
    RealEstateSaleRedTeamReport,
    run_real_estate_sale_benchmark_suite,
    run_real_estate_sale_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticRealEstateSaleEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: RealEstateSaleEvidenceMappingResult
    constraint_set: RealEstateSaleConstraintSet
    reviewed_evaluation: RealEstateSaleEvaluation
    benchmark_report: RealEstateSaleBenchmarkReport
    red_team_report: RealEstateSaleRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticRealEstateSaleEvaluationArtifact":
        expected_set = build_real_estate_sale_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_real_estate_sale_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Real estate sale evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_real_estate_sale_evaluation_artifact() -> (
    SyntheticRealEstateSaleEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().real_estate_sale_evidence
    mapping = map_reviewed_real_estate_sale_evidence(evidence)
    constraint_set = build_real_estate_sale_constraint_set(mapping)
    return SyntheticRealEstateSaleEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о продаже недвижимости по статьям 549–558 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_real_estate_sale_constraints(constraint_set, mapping.facts),
        benchmark_report=run_real_estate_sale_benchmark_suite(),
        red_team_report=run_real_estate_sale_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
