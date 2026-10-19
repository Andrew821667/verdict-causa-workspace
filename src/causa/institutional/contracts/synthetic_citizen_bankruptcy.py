from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.citizen_bankruptcy import (
    CitizenBankruptcyConstraintSet,
    CitizenBankruptcyEvaluation,
    CitizenBankruptcyEvidenceMappingResult,
    build_citizen_bankruptcy_constraint_set,
    evaluate_citizen_bankruptcy_constraints,
    map_reviewed_citizen_bankruptcy_evidence,
)
from causa.institutional.contracts.citizen_bankruptcy_evaluation import (
    CitizenBankruptcyBenchmarkReport,
    CitizenBankruptcyRedTeamReport,
    run_citizen_bankruptcy_benchmark_suite,
    run_citizen_bankruptcy_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticCitizenBankruptcyEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: CitizenBankruptcyEvidenceMappingResult
    constraint_set: CitizenBankruptcyConstraintSet
    reviewed_evaluation: CitizenBankruptcyEvaluation
    benchmark_report: CitizenBankruptcyBenchmarkReport
    red_team_report: CitizenBankruptcyRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticCitizenBankruptcyEvaluationArtifact":
        expected_set = build_citizen_bankruptcy_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_citizen_bankruptcy_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Citizen-bankruptcy evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_citizen_bankruptcy_evaluation_artifact() -> (
    SyntheticCitizenBankruptcyEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().citizen_bankruptcy_evidence
    mapping = map_reviewed_citizen_bankruptcy_evidence(evidence)
    constraint_set = build_citizen_bankruptcy_constraint_set(mapping)
    return SyntheticCitizenBankruptcyEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка несостоятельности (банкротства) гражданина по "
            "статье 25 ГК РФ. В демонстрационном деле спор о поставке ведут две "
            "организации, должник гражданином не является, и институт молчит: это и "
            "есть ожидаемый результат для такого дела. Не устанавливает судебный факт "
            "и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_citizen_bankruptcy_constraints(constraint_set, mapping.facts),
        benchmark_report=run_citizen_bankruptcy_benchmark_suite(),
        red_team_report=run_citizen_bankruptcy_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95825/"],
    )
