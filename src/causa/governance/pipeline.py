from enum import Enum

from pydantic import BaseModel, Field

from causa.localization.ru import GOVERNANCE_STAGE_LABELS_RU, label_ru


class GovernanceStage(str, Enum):
    PROPOSED = "proposed"
    TYPE_CLASSIFICATION = "type_classification"
    FORMAL_CHECK = "formal_check"
    SOURCE_CHECK = "source_check"
    BENCHMARK_CHECK = "benchmark_check"
    RED_TEAM_CHECK = "red_team_check"
    EXPERT_REVIEW = "expert_review"
    CROSS_REVIEW = "cross_review"
    SANDBOX = "sandbox"
    ACTIVE = "active"
    REVALIDATION = "revalidation"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class GovernanceDecision(BaseModel):
    accepted: bool
    next_stage: GovernanceStage
    next_stage_label_ru: str
    reasons: list[str] = Field(default_factory=list)
    reasons_ru: list[str] = Field(default_factory=list)


def advance_candidate(
    current_stage: GovernanceStage,
    checks_passed: bool,
    reasons: list[str] | None = None,
) -> GovernanceDecision:
    reasons = reasons or []
    if not checks_passed:
        return GovernanceDecision(
            accepted=False,
            next_stage=GovernanceStage.REJECTED,
            next_stage_label_ru=label_ru(
                GovernanceStage.REJECTED, GOVERNANCE_STAGE_LABELS_RU
            ),
            reasons=reasons or ["Required checks failed."],
            reasons_ru=["Обязательные проверки не пройдены."],
        )

    order = list(GovernanceStage)
    index = order.index(current_stage)
    if current_stage in {
        GovernanceStage.ACTIVE,
        GovernanceStage.REJECTED,
        GovernanceStage.ROLLED_BACK,
    }:
        return GovernanceDecision(
            accepted=True,
            next_stage=current_stage,
            next_stage_label_ru=label_ru(current_stage, GOVERNANCE_STAGE_LABELS_RU),
            reasons=["Terminal stage reached."],
            reasons_ru=["Достигнута терминальная стадия."],
        )

    return GovernanceDecision(
        accepted=True,
        next_stage=order[index + 1],
        next_stage_label_ru=label_ru(order[index + 1], GOVERNANCE_STAGE_LABELS_RU),
        reasons=reasons or ["Checks passed."],
        reasons_ru=["Обязательные проверки пройдены."],
    )
