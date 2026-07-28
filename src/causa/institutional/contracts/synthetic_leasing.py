from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.leasing import (
    LeasingConstraintSet,
    LeasingEvaluation,
    LeasingEvidenceMappingResult,
    build_leasing_constraint_set,
    evaluate_leasing_constraints,
    map_reviewed_leasing_evidence,
)
from causa.institutional.contracts.leasing_evaluation import (
    LeasingBenchmarkReport,
    LeasingRedTeamReport,
    run_leasing_benchmark_suite,
    run_leasing_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticLeasingEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: LeasingEvidenceMappingResult
    constraint_set: LeasingConstraintSet
    reviewed_evaluation: LeasingEvaluation
    benchmark_report: LeasingBenchmarkReport
    red_team_report: LeasingRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticLeasingEvaluationArtifact":
        expected_set = build_leasing_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_leasing_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Leasing evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_leasing_evaluation_artifact() -> SyntheticLeasingEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().leasing_evidence
    mapping = map_reviewed_leasing_evidence(evidence)
    constraint_set = build_leasing_constraint_set(mapping)
    return SyntheticLeasingEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о финансовой аренде (лизинге) по статьям 665–670 "
            "ГК РФ. Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_leasing_constraints(constraint_set, mapping.facts),
        benchmark_report=run_leasing_benchmark_suite(),
        red_team_report=run_leasing_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
