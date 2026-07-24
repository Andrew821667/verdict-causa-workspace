from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.form import (
    FormConstraintSet,
    FormEvaluation,
    FormEvidenceMappingResult,
    build_form_constraint_set,
    evaluate_form_constraints,
    map_reviewed_form_evidence,
)
from causa.institutional.contracts.form_evaluation import (
    FormBenchmarkReport,
    FormRedTeamReport,
    run_form_benchmark_suite,
    run_form_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticFormEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: FormEvidenceMappingResult
    constraint_set: FormConstraintSet
    reviewed_evaluation: FormEvaluation
    benchmark_report: FormBenchmarkReport
    red_team_report: FormRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticFormEvaluationArtifact":
        expected_set = build_form_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_form_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Form evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_form_evaluation_artifact() -> SyntheticFormEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().form_evidence
    mapping = map_reviewed_form_evidence(evidence)
    constraint_set = build_form_constraint_set(mapping)
    return SyntheticFormEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о форме сделки по статьям 158–165 и 434 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_form_constraints(constraint_set, mapping.facts),
        benchmark_report=run_form_benchmark_suite(),
        red_team_report=run_form_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
