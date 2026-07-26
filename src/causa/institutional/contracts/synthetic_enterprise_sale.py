from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.enterprise_sale import (
    EnterpriseSaleConstraintSet,
    EnterpriseSaleEvaluation,
    EnterpriseSaleEvidenceMappingResult,
    build_enterprise_sale_constraint_set,
    evaluate_enterprise_sale_constraints,
    map_reviewed_enterprise_sale_evidence,
)
from causa.institutional.contracts.enterprise_sale_evaluation import (
    EnterpriseSaleBenchmarkReport,
    EnterpriseSaleRedTeamReport,
    run_enterprise_sale_benchmark_suite,
    run_enterprise_sale_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticEnterpriseSaleEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: EnterpriseSaleEvidenceMappingResult
    constraint_set: EnterpriseSaleConstraintSet
    reviewed_evaluation: EnterpriseSaleEvaluation
    benchmark_report: EnterpriseSaleBenchmarkReport
    red_team_report: EnterpriseSaleRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticEnterpriseSaleEvaluationArtifact":
        expected_set = build_enterprise_sale_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_enterprise_sale_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Enterprise sale evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_enterprise_sale_evaluation_artifact() -> (
    SyntheticEnterpriseSaleEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().enterprise_sale_evidence
    mapping = map_reviewed_enterprise_sale_evidence(evidence)
    constraint_set = build_enterprise_sale_constraint_set(mapping)
    return SyntheticEnterpriseSaleEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о продаже предприятия по статьям 559–566 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_enterprise_sale_constraints(constraint_set, mapping.facts),
        benchmark_report=run_enterprise_sale_benchmark_suite(),
        red_team_report=run_enterprise_sale_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
