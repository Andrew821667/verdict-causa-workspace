from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.agency import (
    AgencyConstraintSet,
    AgencyEvaluation,
    AgencyEvidenceMappingResult,
    build_agency_constraint_set,
    evaluate_agency_constraints,
    map_reviewed_agency_evidence,
)
from causa.institutional.contracts.agency_evaluation import (
    AgencyBenchmarkReport,
    AgencyRedTeamReport,
    run_agency_benchmark_suite,
    run_agency_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticAgencyEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: AgencyEvidenceMappingResult
    constraint_set: AgencyConstraintSet
    reviewed_evaluation: AgencyEvaluation
    benchmark_report: AgencyBenchmarkReport
    red_team_report: AgencyRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticAgencyEvaluationArtifact":
        expected_set = build_agency_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_agency_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Agency evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_agency_evaluation_artifact() -> SyntheticAgencyEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().agency_evidence
    mapping = map_reviewed_agency_evidence(evidence)
    constraint_set = build_agency_constraint_set(mapping)
    return SyntheticAgencyEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил об агентировании по статьям 1005–1011 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_agency_constraints(constraint_set, mapping.facts),
        benchmark_report=run_agency_benchmark_suite(),
        red_team_report=run_agency_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
