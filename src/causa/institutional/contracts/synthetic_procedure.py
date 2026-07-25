from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.procedure import (
    ProcedureConstraintSet,
    ProcedureEvaluation,
    ProcedureEvidenceMappingResult,
    build_procedure_constraint_set,
    evaluate_procedure_constraints,
    map_reviewed_procedure_evidence,
)
from causa.institutional.contracts.procedure_evaluation import (
    ProcedureBenchmarkReport,
    ProcedureRedTeamReport,
    run_procedure_benchmark_suite,
    run_procedure_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticProcedureEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ProcedureEvidenceMappingResult
    constraint_set: ProcedureConstraintSet
    reviewed_evaluation: ProcedureEvaluation
    benchmark_report: ProcedureBenchmarkReport
    red_team_report: ProcedureRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticProcedureEvaluationArtifact":
        expected_set = build_procedure_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_procedure_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Procedure evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_procedure_evaluation_artifact() -> SyntheticProcedureEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().procedure_evidence
    mapping = map_reviewed_procedure_evidence(evidence)
    constraint_set = build_procedure_constraint_set(mapping)
    return SyntheticProcedureEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о заключении договора в обязательном порядке "
            "и на торгах по статьям 445–449 ГК РФ. Не устанавливает судебный факт и не "
            "является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_procedure_constraints(constraint_set, mapping.facts),
        benchmark_report=run_procedure_benchmark_suite(),
        red_team_report=run_procedure_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
