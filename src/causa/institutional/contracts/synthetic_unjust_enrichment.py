from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.unjust_enrichment import (
    UnjustEnrichmentConstraintSet,
    UnjustEnrichmentEvaluation,
    UnjustEnrichmentEvidenceMappingResult,
    build_unjust_enrichment_constraint_set,
    evaluate_unjust_enrichment_constraints,
    map_reviewed_unjust_enrichment_evidence,
)
from causa.institutional.contracts.unjust_enrichment_evaluation import (
    UnjustEnrichmentBenchmarkReport,
    UnjustEnrichmentRedTeamReport,
    run_unjust_enrichment_benchmark_suite,
    run_unjust_enrichment_red_team_suite,
)


class SyntheticUnjustEnrichmentEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: UnjustEnrichmentEvidenceMappingResult
    constraint_set: UnjustEnrichmentConstraintSet
    reviewed_evaluation: UnjustEnrichmentEvaluation
    benchmark_report: UnjustEnrichmentBenchmarkReport
    red_team_report: UnjustEnrichmentRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticUnjustEnrichmentEvaluationArtifact":
        expected_set = build_unjust_enrichment_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_unjust_enrichment_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Unjust-enrichment evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_unjust_enrichment_evaluation_artifact() -> (
    SyntheticUnjustEnrichmentEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().unjust_enrichment_evidence
    mapping = map_reviewed_unjust_enrichment_evidence(evidence)
    constraint_set = build_unjust_enrichment_constraint_set(mapping)
    return SyntheticUnjustEnrichmentEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил об обязательствах вследствие неосновательного "
            "обогащения по статьям 1102–1109 ГК РФ. Не устанавливает судебный факт и не "
            "является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_unjust_enrichment_constraints(constraint_set, mapping.facts),
        benchmark_report=run_unjust_enrichment_benchmark_suite(),
        red_team_report=run_unjust_enrichment_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
