from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.supply import (
    SupplyConstraintSet,
    SupplyEvaluation,
    SupplyEvidenceMappingResult,
    build_supply_constraint_set,
    evaluate_supply_constraints,
    map_reviewed_supply_evidence,
)
from causa.institutional.contracts.supply_evaluation import (
    SupplyBenchmarkReport,
    SupplyRedTeamReport,
    run_supply_benchmark_suite,
    run_supply_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticSupplyEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: SupplyEvidenceMappingResult
    constraint_set: SupplyConstraintSet
    reviewed_evaluation: SupplyEvaluation
    benchmark_report: SupplyBenchmarkReport
    red_team_report: SupplyRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticSupplyEvaluationArtifact":
        expected_set = build_supply_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_supply_constraints(
            expected_set,
            self.reviewed_mapping.facts,
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Supply evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_supply_evaluation_artifact() -> SyntheticSupplyEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().supply_evidence
    mapping = map_reviewed_supply_evidence(evidence)
    constraint_set = build_supply_constraint_set(mapping)
    return SyntheticSupplyEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка специальных правил договора поставки. "
            "Не устанавливает судебный результат, не рассчитывает суммы и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_supply_constraints(constraint_set, mapping.facts),
        benchmark_report=run_supply_benchmark_suite(),
        red_team_report=run_supply_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/96096/",
            "https://www.consultant.ru/document/cons_doc_LAW_17621/",
            "https://vsrf.ru/lk/practice/stor_pdf_ec/1655326",
        ],
    )
