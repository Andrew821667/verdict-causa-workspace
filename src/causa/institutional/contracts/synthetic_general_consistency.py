from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.general_consistency import (
    GeneralConsistencyConstraintSet,
    GeneralConsistencyEvaluation,
    GeneralConsistencyInputs,
    build_general_consistency_constraint_set,
    evaluate_general_consistency_constraints,
)
from causa.institutional.contracts.general_consistency_evaluation import (
    GeneralConsistencyBenchmarkReport,
    GeneralConsistencyRedTeamReport,
    run_general_consistency_benchmark_suite,
    run_general_consistency_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
)


class SyntheticGeneralConsistencyArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    inputs: GeneralConsistencyInputs
    constraint_set: GeneralConsistencyConstraintSet
    evaluation: GeneralConsistencyEvaluation
    benchmark_report: GeneralConsistencyBenchmarkReport
    red_team_report: GeneralConsistencyRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticGeneralConsistencyArtifact":
        expected_set = build_general_consistency_constraint_set(
            self.inputs, self.constraint_set.id.split(":", 1)[1]
        )
        expected_evaluation = evaluate_general_consistency_constraints(expected_set, self.inputs)
        if self.constraint_set != expected_set or self.evaluation != expected_evaluation:
            raise ValueError("Consistency evaluation is not reproducible from its inputs.")
        return self


def build_synthetic_general_consistency_artifact() -> SyntheticGeneralConsistencyArtifact:
    result = build_synthetic_supply_analysis_artifact().result
    return SyntheticGeneralConsistencyArtifact(
        disclaimer_ru=(
            "Синтетическая сверка проверенных фактов между институтами пакета. Слой называет "
            "расхождение в описаниях одного и того же обстоятельства и не выбирает, какая "
            "версия верна. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        inputs=result.general_consistency_inputs,
        constraint_set=result.general_consistency_constraint_set,
        evaluation=result.general_consistency_evaluation,
        benchmark_report=run_general_consistency_benchmark_suite(),
        red_team_report=run_general_consistency_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
