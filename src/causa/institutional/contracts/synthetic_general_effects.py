from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.general_effects import (
    GeneralEffectsConstraintSet,
    GeneralEffectsEvaluation,
    GeneralEffectsInputs,
    build_general_effects_constraint_set,
    evaluate_general_effects_constraints,
)
from causa.institutional.contracts.general_effects_evaluation import (
    GeneralEffectsBenchmarkReport,
    GeneralEffectsRedTeamReport,
    run_general_effects_benchmark_suite,
    run_general_effects_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
)


class SyntheticGeneralEffectsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    derived_inputs: GeneralEffectsInputs
    constraint_set: GeneralEffectsConstraintSet
    derived_evaluation: GeneralEffectsEvaluation
    benchmark_report: GeneralEffectsBenchmarkReport
    red_team_report: GeneralEffectsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticGeneralEffectsEvaluationArtifact":
        expected_set = build_general_effects_constraint_set(
            self.derived_inputs, self.constraint_set.id.split(":", 1)[-1]
        )
        expected_evaluation = evaluate_general_effects_constraints(
            expected_set, self.derived_inputs
        )
        if self.constraint_set != expected_set or self.derived_evaluation != expected_evaluation:
            raise ValueError("General-effects evaluation is not reproducible from derived inputs.")
        return self


def build_synthetic_general_effects_evaluation_artifact() -> (
    SyntheticGeneralEffectsEvaluationArtifact
):
    result = build_synthetic_supply_analysis_artifact().result
    return SyntheticGeneralEffectsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка применения общих положений ГК РФ (статьи 167, 199 и 432) к "
            "выводам специальных институтов. Входы слоя выводятся из результатов якорных "
            "моделей общей части, а не утверждаются рецензентом. Не устанавливает судебный "
            "факт и не является юридической консультацией."
        ),
        derived_inputs=result.general_effects_inputs,
        constraint_set=result.general_effects_constraint_set,
        derived_evaluation=result.general_effects_evaluation,
        benchmark_report=run_general_effects_benchmark_suite(),
        red_team_report=run_general_effects_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95820/",
            "https://government.ru/docs/all/95825/",
        ],
    )
