from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.public_promise import (
    PublicPromiseConstraintSet,
    PublicPromiseEvaluation,
    PublicPromiseEvidenceMappingResult,
    build_public_promise_constraint_set,
    evaluate_public_promise_constraints,
    map_reviewed_public_promise_evidence,
)
from causa.institutional.contracts.public_promise_evaluation import (
    PublicPromiseBenchmarkReport,
    PublicPromiseRedTeamReport,
    run_public_promise_benchmark_suite,
    run_public_promise_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticPublicPromiseEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: PublicPromiseEvidenceMappingResult
    constraint_set: PublicPromiseConstraintSet
    reviewed_evaluation: PublicPromiseEvaluation
    benchmark_report: PublicPromiseBenchmarkReport
    red_team_report: PublicPromiseRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticPublicPromiseEvaluationArtifact":
        expected_set = build_public_promise_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_public_promise_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Public-promise evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_public_promise_evaluation_artifact() -> (
    SyntheticPublicPromiseEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().public_promise_evidence
    mapping = map_reviewed_public_promise_evidence(evidence)
    constraint_set = build_public_promise_constraint_set(mapping)
    return SyntheticPublicPromiseEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о публичном обещании награды и публичном конкурсе по "
            "статьям 1055–1061 ГК РФ. Не устанавливает судебный факт и не является юридической "
            "консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_public_promise_constraints(constraint_set, mapping.facts),
        benchmark_report=run_public_promise_benchmark_suite(),
        red_team_report=run_public_promise_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
