from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.gift import (
    GiftConstraintSet,
    GiftEvaluation,
    GiftEvidenceMappingResult,
    build_gift_constraint_set,
    evaluate_gift_constraints,
    map_reviewed_gift_evidence,
)
from causa.institutional.contracts.gift_evaluation import (
    GiftBenchmarkReport,
    GiftRedTeamReport,
    run_gift_benchmark_suite,
    run_gift_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticGiftEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: GiftEvidenceMappingResult
    constraint_set: GiftConstraintSet
    reviewed_evaluation: GiftEvaluation
    benchmark_report: GiftBenchmarkReport
    red_team_report: GiftRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticGiftEvaluationArtifact":
        expected_set = build_gift_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_gift_constraints(expected_set, self.reviewed_mapping.facts)
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Gift evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_gift_evaluation_artifact() -> SyntheticGiftEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().gift_evidence
    mapping = map_reviewed_gift_evidence(evidence)
    constraint_set = build_gift_constraint_set(mapping)
    return SyntheticGiftEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о дарении по статьям 572–582 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_gift_constraints(constraint_set, mapping.facts),
        benchmark_report=run_gift_benchmark_suite(),
        red_team_report=run_gift_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
