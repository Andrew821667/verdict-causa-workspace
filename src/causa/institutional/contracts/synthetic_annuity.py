from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.annuity import (
    AnnuityConstraintSet,
    AnnuityEvaluation,
    AnnuityEvidenceMappingResult,
    build_annuity_constraint_set,
    evaluate_annuity_constraints,
    map_reviewed_annuity_evidence,
)
from causa.institutional.contracts.annuity_evaluation import (
    AnnuityBenchmarkReport,
    AnnuityRedTeamReport,
    run_annuity_benchmark_suite,
    run_annuity_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticAnnuityEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: AnnuityEvidenceMappingResult
    constraint_set: AnnuityConstraintSet
    reviewed_evaluation: AnnuityEvaluation
    benchmark_report: AnnuityBenchmarkReport
    red_team_report: AnnuityRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticAnnuityEvaluationArtifact":
        expected_set = build_annuity_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_annuity_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Annuity evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_annuity_evaluation_artifact() -> SyntheticAnnuityEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().annuity_evidence
    mapping = map_reviewed_annuity_evidence(evidence)
    constraint_set = build_annuity_constraint_set(mapping)
    return SyntheticAnnuityEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о ренте и пожизненном содержании с иждивением по "
            "статьям 583–605 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_annuity_constraints(constraint_set, mapping.facts),
        benchmark_report=run_annuity_benchmark_suite(),
        red_team_report=run_annuity_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
