from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.franchise import (
    FranchiseConstraintSet,
    FranchiseEvaluation,
    FranchiseEvidenceMappingResult,
    build_franchise_constraint_set,
    evaluate_franchise_constraints,
    map_reviewed_franchise_evidence,
)
from causa.institutional.contracts.franchise_evaluation import (
    FranchiseBenchmarkReport,
    FranchiseRedTeamReport,
    run_franchise_benchmark_suite,
    run_franchise_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticFranchiseEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: FranchiseEvidenceMappingResult
    constraint_set: FranchiseConstraintSet
    reviewed_evaluation: FranchiseEvaluation
    benchmark_report: FranchiseBenchmarkReport
    red_team_report: FranchiseRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticFranchiseEvaluationArtifact":
        expected_set = build_franchise_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_franchise_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Franchise evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_franchise_evaluation_artifact() -> SyntheticFranchiseEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().franchise_evidence
    mapping = map_reviewed_franchise_evidence(evidence)
    constraint_set = build_franchise_constraint_set(mapping)
    return SyntheticFranchiseEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о коммерческой концессии по статьям 1027–1040 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_franchise_constraints(constraint_set, mapping.facts),
        benchmark_report=run_franchise_benchmark_suite(),
        red_team_report=run_franchise_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
