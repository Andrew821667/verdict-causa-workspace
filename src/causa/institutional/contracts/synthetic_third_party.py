from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.third_party import (
    ThirdPartyConstraintSet,
    ThirdPartyEvaluation,
    ThirdPartyEvidenceMappingResult,
    build_third_party_constraint_set,
    evaluate_third_party_constraints,
    map_reviewed_third_party_evidence,
)
from causa.institutional.contracts.third_party_evaluation import (
    ThirdPartyBenchmarkReport,
    ThirdPartyRedTeamReport,
    run_third_party_benchmark_suite,
    run_third_party_red_team_suite,
)


class SyntheticThirdPartyEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ThirdPartyEvidenceMappingResult
    constraint_set: ThirdPartyConstraintSet
    reviewed_evaluation: ThirdPartyEvaluation
    benchmark_report: ThirdPartyBenchmarkReport
    red_team_report: ThirdPartyRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticThirdPartyEvaluationArtifact":
        expected_set = build_third_party_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_third_party_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Third-party evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_third_party_evaluation_artifact() -> SyntheticThirdPartyEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().third_party_evidence
    mapping = map_reviewed_third_party_evidence(evidence)
    constraint_set = build_third_party_constraint_set(mapping)
    return SyntheticThirdPartyEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о договоре в пользу третьего лица по статье 430 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_third_party_constraints(constraint_set, mapping.facts),
        benchmark_report=run_third_party_benchmark_suite(),
        red_team_report=run_third_party_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
