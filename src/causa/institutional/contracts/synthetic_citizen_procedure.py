from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.citizen_procedure import (
    CitizenProcedureConstraintSet,
    CitizenProcedureEvaluation,
    CitizenProcedureEvidenceMappingResult,
    build_citizen_procedure_constraint_set,
    evaluate_citizen_procedure_constraints,
    map_reviewed_citizen_procedure_evidence,
)
from causa.institutional.contracts.citizen_procedure_evaluation import (
    CitizenProcedureBenchmarkReport,
    CitizenProcedureRedTeamReport,
    run_citizen_procedure_benchmark_suite,
    run_citizen_procedure_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticCitizenProcedureEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: CitizenProcedureEvidenceMappingResult
    constraint_set: CitizenProcedureConstraintSet
    reviewed_evaluation: CitizenProcedureEvaluation
    benchmark_report: CitizenProcedureBenchmarkReport
    red_team_report: CitizenProcedureRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticCitizenProcedureEvaluationArtifact":
        expected_set = build_citizen_procedure_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_citizen_procedure_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Citizen-procedure evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_citizen_procedure_evaluation_artifact() -> (
    SyntheticCitizenProcedureEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().citizen_procedure_evidence
    mapping = map_reviewed_citizen_procedure_evidence(evidence)
    constraint_set = build_citizen_procedure_constraint_set(mapping)
    return SyntheticCitizenProcedureEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка обоснованности заявления о признании гражданина "
            "банкротом и выбора процедуры по статьям 213.2, 213.6 и 213.13 закона 127-ФЗ. В "
            "демонстрационном деле спор о поставке ведут две организации, заявления о "
            "признании гражданина банкротом никто не подавал, и институт молчит: это и есть "
            "ожидаемый результат для такого дела. Не устанавливает судебный факт и не "
            "является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_citizen_procedure_constraints(constraint_set, mapping.facts),
        benchmark_report=run_citizen_procedure_benchmark_suite(),
        red_team_report=run_citizen_procedure_red_team_suite(),
        source_urls=["http://pravo.gov.ru/proxy/ips/?docbody=&nd=102078527"],
    )
