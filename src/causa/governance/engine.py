from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causa.governance.candidate_types import CandidateType
from causa.governance.pipeline import GovernanceStage
from causa.governance.profiles import get_governance_profile
from causa.localization.ru import (
    CANDIDATE_TYPE_LABELS_RU,
    GOVERNANCE_STAGE_LABELS_RU,
    LOCALE_RU,
    label_ru,
)


GOVERNANCE_ENGINE_VERSION = "governance-engine-v0"


class GovernanceDecisionOutcome(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class GovernanceStageDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    sequence: int = Field(ge=1)
    candidate_id: str
    from_stage: GovernanceStage
    from_stage_label_ru: str
    to_stage: GovernanceStage
    to_stage_label_ru: str
    outcome: GovernanceDecisionOutcome
    actor_id: str
    decided_at: datetime
    reasons_ru: tuple[str, ...] = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    policy_version: str


class CandidateActivationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    candidate_id: str
    candidate_version: str
    activated_at: datetime
    expires_at: datetime | None = None
    actor_id: str
    policy_version: str
    decision_id: str


class SandboxEvaluationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    candidate_id: str
    started_at: datetime
    completed_at: datetime
    evaluator_id: str
    isolation_scope_ru: str
    scenario_count: int = Field(ge=1)
    failed_scenario_count: int = Field(ge=0)
    passed: bool
    reasons_ru: tuple[str, ...] = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_result_counts(self) -> "SandboxEvaluationRecord":
        if self.failed_scenario_count > self.scenario_count:
            raise ValueError("Число проваленных сценариев превышает общее число сценариев.")
        if self.passed and self.failed_scenario_count:
            raise ValueError("Успешная песочница не может содержать проваленные сценарии.")
        if not self.passed and not self.failed_scenario_count:
            raise ValueError("Неуспешная песочница должна содержать проваленный сценарий.")
        if self.completed_at < self.started_at:
            raise ValueError("Песочница не может завершиться раньше начала.")
        return self


class RevalidationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    candidate_id: str
    candidate_version: str
    due_at: datetime | None
    completed_at: datetime
    reviewer_id: str
    passed: bool
    next_due_at: datetime | None = None
    reasons_ru: tuple[str, ...] = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    decision_id: str


class RollbackRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    candidate_id: str
    rolled_back_candidate_version: str
    restored_candidate_version: str | None = None
    rolled_back_at: datetime
    actor_id: str
    reasons_ru: tuple[str, ...] = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    decision_id: str


class GovernanceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    candidate_id: str
    candidate_type: CandidateType
    candidate_type_label_ru: str
    locale: str = LOCALE_RU
    engine_version: str = GOVERNANCE_ENGINE_VERSION
    policy_version: str
    current_stage: GovernanceStage = GovernanceStage.PROPOSED
    current_stage_label_ru: str = GOVERNANCE_STAGE_LABELS_RU[GovernanceStage.PROPOSED.value]
    created_at: datetime
    decisions: list[GovernanceStageDecision] = Field(default_factory=list)
    activations: list[CandidateActivationRecord] = Field(default_factory=list)
    sandbox_evaluations: list[SandboxEvaluationRecord] = Field(default_factory=list)
    revalidations: list[RevalidationRecord] = Field(default_factory=list)
    rollbacks: list[RollbackRecord] = Field(default_factory=list)
    active_candidate_version: str | None = None
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_audit_history(self) -> "GovernanceRecord":
        expected_label = label_ru(self.current_stage, GOVERNANCE_STAGE_LABELS_RU)
        if self.current_stage_label_ru != expected_label:
            raise ValueError("Русская метка не соответствует текущей governance-стадии.")
        previous_stage = GovernanceStage.PROPOSED
        previous_time = self.created_at
        for expected_sequence, decision in enumerate(self.decisions, start=1):
            if decision.sequence != expected_sequence:
                raise ValueError("Нарушена последовательность governance-решений.")
            if decision.candidate_id != self.candidate_id:
                raise ValueError("Governance-решение относится к другому кандидату.")
            if decision.policy_version != self.policy_version:
                raise ValueError("Governance-решение использует другую версию политики.")
            if decision.from_stage != previous_stage:
                raise ValueError("Нарушена цепочка стадий governance-решений.")
            if decision.decided_at < previous_time:
                raise ValueError("Нарушена хронология governance-решений.")
            if decision.from_stage_label_ru != _stage_label(decision.from_stage):
                raise ValueError("Русская метка исходной стадии governance-решения неверна.")
            if decision.to_stage_label_ru != _stage_label(decision.to_stage):
                raise ValueError("Русская метка следующей стадии governance-решения неверна.")
            previous_stage = decision.to_stage
            previous_time = decision.decided_at
        if self.decisions and self.decisions[-1].to_stage != self.current_stage:
            raise ValueError("Текущая стадия не соответствует последнему governance-решению.")
        if self.current_stage in {GovernanceStage.ACTIVE, GovernanceStage.REVALIDATION}:
            if self.active_candidate_version is None:
                raise ValueError("Для активной стадии требуется версия кандидата.")
        if self.current_stage in {GovernanceStage.REJECTED, GovernanceStage.ROLLED_BACK}:
            if self.active_candidate_version is not None:
                raise ValueError("Терминальная стадия не может содержать активную версию.")
        return self


class GovernanceLifecycleArtifact(BaseModel):
    id: str
    locale: str = LOCALE_RU
    engine_version: str = GOVERNANCE_ENGINE_VERSION
    title_ru: str
    summary_ru: list[str] = Field(default_factory=list)
    records: list[GovernanceRecord] = Field(default_factory=list)


def create_governance_record(
    *,
    candidate_id: str,
    candidate_type: CandidateType,
    policy_version: str,
    created_at: datetime,
) -> GovernanceRecord:
    return GovernanceRecord(
        id=f"governance-record:{candidate_id}",
        candidate_id=candidate_id,
        candidate_type=candidate_type,
        candidate_type_label_ru=label_ru(candidate_type, CANDIDATE_TYPE_LABELS_RU),
        policy_version=policy_version,
        created_at=created_at,
    )


def _stage_label(stage: GovernanceStage) -> str:
    return label_ru(stage, GOVERNANCE_STAGE_LABELS_RU)


def _next_required_stage(record: GovernanceRecord) -> GovernanceStage:
    profile = get_governance_profile(record.candidate_type)
    if record.current_stage == GovernanceStage.PROPOSED:
        return profile.required_stages[0]
    try:
        current_index = profile.required_stages.index(record.current_stage)
    except ValueError as error:
        raise ValueError(
            f"Стадия {_stage_label(record.current_stage)} не входит в профиль кандидата."
        ) from error
    if current_index + 1 < len(profile.required_stages):
        return profile.required_stages[current_index + 1]
    return GovernanceStage.ACTIVE


def _build_decision(
    record: GovernanceRecord,
    *,
    to_stage: GovernanceStage,
    outcome: GovernanceDecisionOutcome,
    actor_id: str,
    decided_at: datetime,
    reasons_ru: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> GovernanceStageDecision:
    sequence = len(record.decisions) + 1
    return GovernanceStageDecision(
        id=f"governance-decision:{record.candidate_id}:{sequence}",
        sequence=sequence,
        candidate_id=record.candidate_id,
        from_stage=record.current_stage,
        from_stage_label_ru=_stage_label(record.current_stage),
        to_stage=to_stage,
        to_stage_label_ru=_stage_label(to_stage),
        outcome=outcome,
        actor_id=actor_id,
        decided_at=decided_at,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
        policy_version=record.policy_version,
    )


def _require_chronological_time(record: GovernanceRecord, event_at: datetime) -> None:
    latest_at = record.decisions[-1].decided_at if record.decisions else record.created_at
    if event_at < latest_at:
        raise ValueError("Новое governance-событие не может предшествовать журналу решений.")


def _expiration_at(record: GovernanceRecord, activated_at: datetime) -> datetime | None:
    expiration_days = get_governance_profile(record.candidate_type).expiration_days
    if expiration_days is None:
        return None
    return activated_at + timedelta(days=expiration_days)


def _apply_decision(
    record: GovernanceRecord,
    decision: GovernanceStageDecision,
) -> GovernanceRecord:
    activations = list(record.activations)
    active_candidate_version = record.active_candidate_version
    expires_at = record.expires_at
    if decision.to_stage == GovernanceStage.ACTIVE and record.current_stage != GovernanceStage.REVALIDATION:
        version_number = len(activations) + 1
        active_candidate_version = f"{record.candidate_id}@{version_number}"
        expires_at = _expiration_at(record, decision.decided_at)
        activations.append(
            CandidateActivationRecord(
                id=f"activation:{record.candidate_id}:{version_number}",
                candidate_id=record.candidate_id,
                candidate_version=active_candidate_version,
                activated_at=decision.decided_at,
                expires_at=expires_at,
                actor_id=decision.actor_id,
                policy_version=record.policy_version,
                decision_id=decision.id,
            )
        )
    if decision.to_stage in {GovernanceStage.REJECTED, GovernanceStage.ROLLED_BACK}:
        expires_at = None
        active_candidate_version = None

    return record.model_copy(
        update={
            "current_stage": decision.to_stage,
            "current_stage_label_ru": decision.to_stage_label_ru,
            "decisions": [*record.decisions, decision],
            "activations": activations,
            "active_candidate_version": active_candidate_version,
            "expires_at": expires_at,
        }
    )


def submit_stage_decision(
    record: GovernanceRecord,
    *,
    expected_stage: GovernanceStage,
    passed: bool,
    actor_id: str,
    decided_at: datetime,
    reasons_ru: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> GovernanceRecord:
    _require_chronological_time(record, decided_at)
    if record.current_stage != expected_stage:
        raise ValueError(
            "Стадия изменилась: ожидалась «"
            f"{_stage_label(expected_stage)}», текущая — «{record.current_stage_label_ru}»."
        )
    if record.current_stage in {GovernanceStage.REJECTED, GovernanceStage.ROLLED_BACK}:
        raise ValueError("Терминальная governance-запись не допускает новых переходов.")
    if record.current_stage == GovernanceStage.ACTIVE:
        raise ValueError("Для активного кандидата используйте повторную валидацию или откат.")
    if record.current_stage == GovernanceStage.REVALIDATION:
        raise ValueError("Для этой стадии используйте завершение повторной валидации.")
    if record.current_stage == GovernanceStage.SANDBOX:
        raise ValueError("Для этой стадии используйте завершение проверки в песочнице.")

    to_stage = _next_required_stage(record) if passed else GovernanceStage.REJECTED
    outcome = (
        GovernanceDecisionOutcome.APPROVED
        if passed
        else GovernanceDecisionOutcome.REJECTED
    )
    decision = _build_decision(
        record,
        to_stage=to_stage,
        outcome=outcome,
        actor_id=actor_id,
        decided_at=decided_at,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
    )
    return _apply_decision(record, decision)


def complete_sandbox(
    record: GovernanceRecord,
    sandbox: SandboxEvaluationRecord,
) -> GovernanceRecord:
    if record.current_stage != GovernanceStage.SANDBOX:
        raise ValueError("Проверку в песочнице можно завершить только на стадии sandbox.")
    if sandbox.candidate_id != record.candidate_id:
        raise ValueError("Запись песочницы относится к другому кандидату.")
    _require_chronological_time(record, sandbox.started_at)
    to_stage = GovernanceStage.ACTIVE if sandbox.passed else GovernanceStage.REJECTED
    outcome = (
        GovernanceDecisionOutcome.APPROVED
        if sandbox.passed
        else GovernanceDecisionOutcome.REJECTED
    )
    decision = _build_decision(
        record,
        to_stage=to_stage,
        outcome=outcome,
        actor_id=sandbox.evaluator_id,
        decided_at=sandbox.completed_at,
        reasons_ru=sandbox.reasons_ru,
        evidence_refs=sandbox.evidence_refs,
    )
    updated = _apply_decision(record, decision)
    return updated.model_copy(
        update={
            "sandbox_evaluations": [*record.sandbox_evaluations, sandbox],
        }
    )


def start_revalidation(
    record: GovernanceRecord,
    *,
    actor_id: str,
    started_at: datetime,
    reasons_ru: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> GovernanceRecord:
    _require_chronological_time(record, started_at)
    if record.current_stage != GovernanceStage.ACTIVE:
        raise ValueError("Повторная валидация доступна только для активного кандидата.")
    decision = _build_decision(
        record,
        to_stage=GovernanceStage.REVALIDATION,
        outcome=GovernanceDecisionOutcome.APPROVED,
        actor_id=actor_id,
        decided_at=started_at,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
    )
    return _apply_decision(record, decision)


def complete_revalidation(
    record: GovernanceRecord,
    *,
    passed: bool,
    reviewer_id: str,
    completed_at: datetime,
    reasons_ru: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> GovernanceRecord:
    _require_chronological_time(record, completed_at)
    if record.current_stage != GovernanceStage.REVALIDATION:
        raise ValueError("Завершить повторную валидацию можно только на соответствующей стадии.")
    if record.active_candidate_version is None:
        raise ValueError("У кандидата отсутствует активная версия для повторной валидации.")

    to_stage = GovernanceStage.ACTIVE if passed else GovernanceStage.ROLLED_BACK
    outcome = (
        GovernanceDecisionOutcome.APPROVED
        if passed
        else GovernanceDecisionOutcome.ROLLED_BACK
    )
    decision = _build_decision(
        record,
        to_stage=to_stage,
        outcome=outcome,
        actor_id=reviewer_id,
        decided_at=completed_at,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
    )
    updated = _apply_decision(record, decision)
    next_due_at = _expiration_at(record, completed_at) if passed else None
    revalidation = RevalidationRecord(
        id=f"revalidation:{record.candidate_id}:{len(record.revalidations) + 1}",
        candidate_id=record.candidate_id,
        candidate_version=record.active_candidate_version,
        due_at=record.expires_at,
        completed_at=completed_at,
        reviewer_id=reviewer_id,
        passed=passed,
        next_due_at=next_due_at,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
        decision_id=decision.id,
    )
    update: dict[str, object] = {
        "revalidations": [*record.revalidations, revalidation],
        "expires_at": next_due_at,
    }
    if not passed:
        rollback = RollbackRecord(
            id=f"rollback:{record.candidate_id}:{len(record.rollbacks) + 1}",
            candidate_id=record.candidate_id,
            rolled_back_candidate_version=record.active_candidate_version,
            rolled_back_at=completed_at,
            actor_id=reviewer_id,
            reasons_ru=reasons_ru,
            evidence_refs=evidence_refs,
            decision_id=decision.id,
        )
        update["rollbacks"] = [*record.rollbacks, rollback]
    return updated.model_copy(update=update)


def rollback_candidate(
    record: GovernanceRecord,
    *,
    actor_id: str,
    rolled_back_at: datetime,
    reasons_ru: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    restored_candidate_version: str | None = None,
) -> GovernanceRecord:
    _require_chronological_time(record, rolled_back_at)
    if record.current_stage not in {GovernanceStage.ACTIVE, GovernanceStage.REVALIDATION}:
        raise ValueError("Откат доступен только для активного или повторно проверяемого кандидата.")
    if record.active_candidate_version is None:
        raise ValueError("У кандидата отсутствует активная версия для отката.")
    decision = _build_decision(
        record,
        to_stage=GovernanceStage.ROLLED_BACK,
        outcome=GovernanceDecisionOutcome.ROLLED_BACK,
        actor_id=actor_id,
        decided_at=rolled_back_at,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
    )
    updated = _apply_decision(record, decision)
    rollback = RollbackRecord(
        id=f"rollback:{record.candidate_id}:{len(record.rollbacks) + 1}",
        candidate_id=record.candidate_id,
        rolled_back_candidate_version=record.active_candidate_version,
        restored_candidate_version=restored_candidate_version,
        rolled_back_at=rolled_back_at,
        actor_id=actor_id,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
        decision_id=decision.id,
    )
    return updated.model_copy(update={"rollbacks": [*record.rollbacks, rollback]})
