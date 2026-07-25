from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.option import (
    OptionConstraintSet,
    OptionEvaluation,
    OptionEvidenceMappingResult,
    build_option_constraint_set,
    evaluate_option_constraints,
    map_reviewed_option_evidence,
)
from causa.institutional.contracts.option_evaluation import (
    OptionBenchmarkReport,
    OptionRedTeamReport,
    run_option_benchmark_suite,
    run_option_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticOptionEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: OptionEvidenceMappingResult
    constraint_set: OptionConstraintSet
    reviewed_evaluation: OptionEvaluation
    benchmark_report: OptionBenchmarkReport
    red_team_report: OptionRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticOptionEvaluationArtifact":
        expected_set = build_option_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_option_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Option evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_option_evaluation_artifact() -> SyntheticOptionEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().option_evidence
    mapping = map_reviewed_option_evidence(evidence)
    constraint_set = build_option_constraint_set(mapping)
    return SyntheticOptionEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил об опционе на заключение договора и опционном "
            "договоре по статьям 429.2 и 429.3 ГК РФ. Не устанавливает судебный факт и "
            "не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_option_constraints(constraint_set, mapping.facts),
        benchmark_report=run_option_benchmark_suite(),
        red_team_report=run_option_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
