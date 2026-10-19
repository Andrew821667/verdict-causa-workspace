from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.citizen_release import (
    CitizenReleaseConstraintSet,
    CitizenReleaseEvaluation,
    CitizenReleaseEvidenceMappingResult,
    build_citizen_release_constraint_set,
    evaluate_citizen_release_constraints,
    map_reviewed_citizen_release_evidence,
)
from causa.institutional.contracts.citizen_release_evaluation import (
    CitizenReleaseBenchmarkReport,
    CitizenReleaseRedTeamReport,
    run_citizen_release_benchmark_suite,
    run_citizen_release_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticCitizenReleaseEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: CitizenReleaseEvidenceMappingResult
    constraint_set: CitizenReleaseConstraintSet
    reviewed_evaluation: CitizenReleaseEvaluation
    benchmark_report: CitizenReleaseBenchmarkReport
    red_team_report: CitizenReleaseRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticCitizenReleaseEvaluationArtifact":
        expected_set = build_citizen_release_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_citizen_release_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Citizen-release evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_citizen_release_evaluation_artifact() -> (
    SyntheticCitizenReleaseEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().citizen_release_evidence
    mapping = map_reviewed_citizen_release_evidence(evidence)
    constraint_set = build_citizen_release_constraint_set(mapping)
    return SyntheticCitizenReleaseEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка освобождения гражданина от обязательств по статье "
            "213.28 закона 127-ФЗ. В демонстрационном деле спор о поставке ведут две "
            "организации, гражданин банкротом не признавался, и институт молчит: это и "
            "есть ожидаемый результат для такого дела. Не устанавливает судебный факт и "
            "не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_citizen_release_constraints(constraint_set, mapping.facts),
        benchmark_report=run_citizen_release_benchmark_suite(),
        red_team_report=run_citizen_release_red_team_suite(),
        source_urls=["http://pravo.gov.ru/proxy/ips/?docbody=&nd=102078527"],
    )
