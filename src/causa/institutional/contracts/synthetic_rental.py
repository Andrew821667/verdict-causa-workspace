from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.rental import (
    RentalConstraintSet,
    RentalEvaluation,
    RentalEvidenceMappingResult,
    build_rental_constraint_set,
    evaluate_rental_constraints,
    map_reviewed_rental_evidence,
)
from causa.institutional.contracts.rental_evaluation import (
    RentalBenchmarkReport,
    RentalRedTeamReport,
    run_rental_benchmark_suite,
    run_rental_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticRentalEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: RentalEvidenceMappingResult
    constraint_set: RentalConstraintSet
    reviewed_evaluation: RentalEvaluation
    benchmark_report: RentalBenchmarkReport
    red_team_report: RentalRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticRentalEvaluationArtifact":
        expected_set = build_rental_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_rental_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Rental evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_rental_evaluation_artifact() -> SyntheticRentalEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().rental_evidence
    mapping = map_reviewed_rental_evidence(evidence)
    constraint_set = build_rental_constraint_set(mapping)
    return SyntheticRentalEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о прокате по статьям 626–631 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_rental_constraints(constraint_set, mapping.facts),
        benchmark_report=run_rental_benchmark_suite(),
        red_team_report=run_rental_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
