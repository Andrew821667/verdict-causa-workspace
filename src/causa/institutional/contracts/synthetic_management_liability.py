from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.management_liability import (
    ManagementLiabilityConstraintSet,
    ManagementLiabilityEvaluation,
    ManagementLiabilityEvidenceMappingResult,
    build_management_liability_constraint_set,
    evaluate_management_liability_constraints,
    map_reviewed_management_liability_evidence,
)
from causa.institutional.contracts.management_liability_evaluation import (
    ManagementLiabilityBenchmarkReport,
    ManagementLiabilityRedTeamReport,
    run_management_liability_benchmark_suite,
    run_management_liability_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticManagementLiabilityEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ManagementLiabilityEvidenceMappingResult
    constraint_set: ManagementLiabilityConstraintSet
    reviewed_evaluation: ManagementLiabilityEvaluation
    benchmark_report: ManagementLiabilityBenchmarkReport
    red_team_report: ManagementLiabilityRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticManagementLiabilityEvaluationArtifact":
        expected_set = build_management_liability_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_management_liability_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Management-liability evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_management_liability_evaluation_artifact() -> (
    SyntheticManagementLiabilityEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().management_liability_evidence
    mapping = map_reviewed_management_liability_evidence(evidence)
    constraint_set = build_management_liability_constraint_set(mapping)
    return SyntheticManagementLiabilityEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка ответственности управляющих лиц юридического лица "
            "по статье 53.1 ГК РФ. В демонстрационном деле о поставке требований к "
            "директору или контролирующему лицу нет, поэтому все признаки ложны и "
            "институт молчит: это и есть ожидаемый результат для такого дела. Не "
            "устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_management_liability_constraints(
            constraint_set, mapping.facts
        ),
        benchmark_report=run_management_liability_benchmark_suite(),
        red_team_report=run_management_liability_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
