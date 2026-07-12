from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.security import (
    SecurityConstraintSet,
    SecurityEvaluation,
    SecurityEvidenceMappingResult,
    build_security_constraint_set,
    evaluate_security_constraints,
    map_reviewed_security_evidence,
)
from causa.institutional.contracts.security_evaluation import (
    SecurityBenchmarkReport,
    SecurityRedTeamReport,
    run_security_benchmark_suite,
    run_security_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticSecurityEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: SecurityEvidenceMappingResult
    constraint_set: SecurityConstraintSet
    reviewed_evaluation: SecurityEvaluation
    benchmark_report: SecurityBenchmarkReport
    red_team_report: SecurityRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticSecurityEvaluationArtifact":
        expected_set = build_security_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_security_constraints(
            expected_set,
            self.reviewed_mapping.facts,
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Security evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_security_evaluation_artifact() -> SyntheticSecurityEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().security_evidence
    mapping = map_reviewed_security_evidence(evidence)
    constraint_set = build_security_constraint_set(mapping)
    return SyntheticSecurityEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка способов обеспечения исполнения обязательств. "
            "Не устанавливает судебный результат и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_security_constraints(
            constraint_set,
            mapping.facts,
        ),
        benchmark_report=run_security_benchmark_suite(),
        red_team_report=run_security_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
            "https://vsrf.ru/documents/own/8524/",
            "https://www.vsrf.ru/documents/own/29544/",
            "https://www.vsrf.ru/documents/own/32601/",
        ],
    )
