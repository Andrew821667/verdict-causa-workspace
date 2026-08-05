from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.partnership import (
    PartnershipConstraintSet,
    PartnershipEvaluation,
    PartnershipEvidenceMappingResult,
    build_partnership_constraint_set,
    evaluate_partnership_constraints,
    map_reviewed_partnership_evidence,
)
from causa.institutional.contracts.partnership_evaluation import (
    PartnershipBenchmarkReport,
    PartnershipRedTeamReport,
    run_partnership_benchmark_suite,
    run_partnership_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticPartnershipEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: PartnershipEvidenceMappingResult
    constraint_set: PartnershipConstraintSet
    reviewed_evaluation: PartnershipEvaluation
    benchmark_report: PartnershipBenchmarkReport
    red_team_report: PartnershipRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticPartnershipEvaluationArtifact":
        expected_set = build_partnership_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_partnership_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Partnership evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_partnership_evaluation_artifact() -> SyntheticPartnershipEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().partnership_evidence
    mapping = map_reviewed_partnership_evidence(evidence)
    constraint_set = build_partnership_constraint_set(mapping)
    return SyntheticPartnershipEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о простом товариществе по статьям 1041–1054 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_partnership_constraints(constraint_set, mapping.facts),
        benchmark_report=run_partnership_benchmark_suite(),
        red_team_report=run_partnership_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
