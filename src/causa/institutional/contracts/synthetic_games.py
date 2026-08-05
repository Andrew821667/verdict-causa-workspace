from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.games import (
    GamesConstraintSet,
    GamesEvaluation,
    GamesEvidenceMappingResult,
    build_games_constraint_set,
    evaluate_games_constraints,
    map_reviewed_games_evidence,
)
from causa.institutional.contracts.games_evaluation import (
    GamesBenchmarkReport,
    GamesRedTeamReport,
    run_games_benchmark_suite,
    run_games_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticGamesEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: GamesEvidenceMappingResult
    constraint_set: GamesConstraintSet
    reviewed_evaluation: GamesEvaluation
    benchmark_report: GamesBenchmarkReport
    red_team_report: GamesRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticGamesEvaluationArtifact":
        expected_set = build_games_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_games_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Games evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_games_evaluation_artifact() -> SyntheticGamesEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().games_evidence
    mapping = map_reviewed_games_evidence(evidence)
    constraint_set = build_games_constraint_set(mapping)
    return SyntheticGamesEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о проведении игр и пари по статьям 1062–1063 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_games_constraints(constraint_set, mapping.facts),
        benchmark_report=run_games_benchmark_suite(),
        red_team_report=run_games_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
