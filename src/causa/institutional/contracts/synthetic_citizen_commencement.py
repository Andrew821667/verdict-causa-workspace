from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.citizen_commencement import (
    CitizenCommencementConstraintSet,
    CitizenCommencementEvaluation,
    CitizenCommencementEvidenceMappingResult,
    build_citizen_commencement_constraint_set,
    evaluate_citizen_commencement_constraints,
    map_reviewed_citizen_commencement_evidence,
)
from causa.institutional.contracts.citizen_commencement_evaluation import (
    CitizenCommencementBenchmarkReport,
    CitizenCommencementRedTeamReport,
    run_citizen_commencement_benchmark_suite,
    run_citizen_commencement_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticCitizenCommencementEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: CitizenCommencementEvidenceMappingResult
    constraint_set: CitizenCommencementConstraintSet
    reviewed_evaluation: CitizenCommencementEvaluation
    benchmark_report: CitizenCommencementBenchmarkReport
    red_team_report: CitizenCommencementRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticCitizenCommencementEvaluationArtifact":
        expected_set = build_citizen_commencement_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_citizen_commencement_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Citizen-commencement evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_citizen_commencement_evaluation_artifact() -> (
    SyntheticCitizenCommencementEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().citizen_commencement_evidence
    mapping = map_reviewed_citizen_commencement_evidence(evidence)
    constraint_set = build_citizen_commencement_constraint_set(mapping)
    return SyntheticCitizenCommencementEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка возбуждения дела о банкротстве гражданина по статьям "
            "213.3–213.5 закона 127-ФЗ. В демонстрационном деле спор о поставке ведут две "
            "организации, заявления о признании гражданина банкротом никто не подавал, и "
            "институт молчит: это и есть ожидаемый результат для такого дела. Не "
            "устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_citizen_commencement_constraints(
            constraint_set, mapping.facts
        ),
        benchmark_report=run_citizen_commencement_benchmark_suite(),
        red_team_report=run_citizen_commencement_red_team_suite(),
        source_urls=["http://pravo.gov.ru/proxy/ips/?docbody=&nd=102078527"],
    )
