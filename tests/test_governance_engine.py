import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.governance.candidate_types import CandidateType
from causa.governance.engine import (
    GovernanceDecisionOutcome,
    GovernanceLifecycleArtifact,
    GovernanceRecord,
    SandboxEvaluationRecord,
    complete_revalidation,
    complete_sandbox,
    create_governance_record,
    rollback_candidate,
    start_revalidation,
    submit_stage_decision,
)
from causa.governance.pipeline import GovernanceStage
from causa.governance.synthetic_lifecycle import (
    build_synthetic_gap_governance_record,
    build_synthetic_governance_lifecycle_artifact,
    build_synthetic_sandbox_and_rollback_record,
)


CREATED_AT = datetime.fromisoformat("2026-07-11T10:00:00+03:00")


def _new_gap_record():
    return create_governance_record(
        candidate_id="candidate-test-gap",
        candidate_type=CandidateType.GAP_HEURISTIC,
        policy_version="policy-test-v0",
        created_at=CREATED_AT,
    )


def _approve_current(record, minute: int = 1):
    return submit_stage_decision(
        record,
        expected_stage=record.current_stage,
        passed=True,
        actor_id="domain-owner-test",
        decided_at=CREATED_AT + timedelta(minutes=minute),
        reasons_ru=("Обязательная проверка пройдена.",),
        evidence_refs=(f"evidence:{record.current_stage.value}",),
    )


def test_gap_heuristic_follows_profile_and_activates_version() -> None:
    record = _new_gap_record()
    record = _approve_current(record, 1)
    record = _approve_current(record, 2)
    record = _approve_current(record, 3)

    assert [decision.from_stage for decision in record.decisions] == [
        GovernanceStage.PROPOSED,
        GovernanceStage.TYPE_CLASSIFICATION,
        GovernanceStage.EXPERT_REVIEW,
    ]
    assert record.current_stage == GovernanceStage.ACTIVE
    assert record.current_stage_label_ru == "Активно"
    assert record.active_candidate_version == "candidate-test-gap@1"
    assert record.expires_at == CREATED_AT + timedelta(minutes=3, days=365)
    assert record.activations[0].decision_id == record.decisions[-1].id
    assert all(decision.reasons_ru for decision in record.decisions)
    assert all(decision.evidence_refs for decision in record.decisions)


def test_failed_check_rejects_candidate_and_preserves_russian_reason() -> None:
    record = submit_stage_decision(
        _new_gap_record(),
        expected_stage=GovernanceStage.PROPOSED,
        passed=False,
        actor_id="domain-owner-test",
        decided_at=CREATED_AT,
        reasons_ru=("Тип кандидата не подтвержден.",),
        evidence_refs=("classification-report:failed",),
    )

    assert record.current_stage == GovernanceStage.REJECTED
    assert record.decisions[0].outcome == GovernanceDecisionOutcome.REJECTED
    assert record.decisions[0].reasons_ru == ("Тип кандидата не подтвержден.",)

    with pytest.raises(ValueError, match="Терминальная"):
        submit_stage_decision(
            record,
            expected_stage=GovernanceStage.REJECTED,
            passed=True,
            actor_id="domain-owner-test",
            decided_at=CREATED_AT + timedelta(minutes=1),
            reasons_ru=("Повторная попытка.",),
            evidence_refs=("evidence:retry",),
        )


def test_stale_stage_command_is_rejected() -> None:
    record = _approve_current(_new_gap_record())

    with pytest.raises(ValueError, match="Стадия изменилась"):
        submit_stage_decision(
            record,
            expected_stage=GovernanceStage.PROPOSED,
            passed=True,
            actor_id="domain-owner-test",
            decided_at=CREATED_AT + timedelta(minutes=2),
            reasons_ru=("Устаревшее решение.",),
            evidence_refs=("evidence:stale",),
        )


def test_decision_time_cannot_precede_governance_record() -> None:
    with pytest.raises(ValueError, match="не может предшествовать"):
        submit_stage_decision(
            _new_gap_record(),
            expected_stage=GovernanceStage.PROPOSED,
            passed=True,
            actor_id="domain-owner-test",
            decided_at=CREATED_AT - timedelta(minutes=1),
            reasons_ru=("Решение с неверным временем.",),
            evidence_refs=("evidence:invalid-time",),
        )


def test_loaded_governance_history_rejects_broken_sequence() -> None:
    record = build_synthetic_gap_governance_record("candidate-broken-history")
    payload = record.model_dump(mode="json")
    payload["decisions"][1]["sequence"] = 99

    with pytest.raises(ValidationError, match="последовательность"):
        GovernanceRecord.model_validate(payload)


def test_sandbox_cannot_be_bypassed_by_generic_transition() -> None:
    artifact = build_synthetic_governance_lifecycle_artifact()
    rollback_record = artifact.records[1]
    sandbox_decision = next(
        decision
        for decision in rollback_record.decisions
        if decision.from_stage == GovernanceStage.SANDBOX
    )
    record_before_sandbox = rollback_record.model_copy(
        update={
            "current_stage": GovernanceStage.SANDBOX,
            "current_stage_label_ru": "Предактивационная песочница",
            "decisions": [
                decision
                for decision in rollback_record.decisions
                if decision.sequence < sandbox_decision.sequence
            ],
            "activations": [],
            "sandbox_evaluations": [],
            "rollbacks": [],
            "active_candidate_version": None,
        }
    )

    with pytest.raises(ValueError, match="завершение проверки в песочнице"):
        submit_stage_decision(
            record_before_sandbox,
            expected_stage=GovernanceStage.SANDBOX,
            passed=True,
            actor_id="reviewer",
            decided_at=record_before_sandbox.decisions[-1].decided_at + timedelta(minutes=1),
            reasons_ru=("Попытка обхода.",),
            evidence_refs=("evidence:bypass",),
        )


def test_sandbox_record_validates_counts_and_result() -> None:
    with pytest.raises(ValidationError, match="Успешная песочница"):
        SandboxEvaluationRecord(
            id="sandbox-invalid",
            candidate_id="candidate",
            started_at=CREATED_AT,
            completed_at=CREATED_AT + timedelta(minutes=1),
            evaluator_id="reviewer",
            isolation_scope_ru="Синтетические данные.",
            scenario_count=3,
            failed_scenario_count=1,
            passed=True,
            reasons_ru=("Некорректный результат.",),
            evidence_refs=("red-team-report",),
        )


def test_failed_sandbox_rejects_candidate_without_activation() -> None:
    successful = build_synthetic_sandbox_and_rollback_record()
    sandbox_decision = next(
        decision
        for decision in successful.decisions
        if decision.from_stage == GovernanceStage.SANDBOX
    )
    record = successful.model_copy(
        update={
            "current_stage": GovernanceStage.SANDBOX,
            "current_stage_label_ru": "Предактивационная песочница",
            "decisions": [
                decision
                for decision in successful.decisions
                if decision.sequence < sandbox_decision.sequence
            ],
            "activations": [],
            "sandbox_evaluations": [],
            "rollbacks": [],
            "active_candidate_version": None,
        }
    )
    sandbox_started_at = record.decisions[-1].decided_at + timedelta(minutes=1)
    sandbox = SandboxEvaluationRecord(
        id="sandbox-failed",
        candidate_id=record.candidate_id,
        started_at=sandbox_started_at,
        completed_at=sandbox_started_at + timedelta(minutes=1),
        evaluator_id="reviewer",
        isolation_scope_ru="Синтетические данные.",
        scenario_count=3,
        failed_scenario_count=1,
        passed=False,
        reasons_ru=("Выявлен запрещенный результат.",),
        evidence_refs=("red-team-report:failed",),
    )
    record = complete_sandbox(record, sandbox)

    assert record.current_stage == GovernanceStage.REJECTED
    assert record.activations == []
    assert record.sandbox_evaluations[0].passed is False


def test_successful_revalidation_renews_expiration_without_new_activation() -> None:
    record = build_synthetic_gap_governance_record("candidate-revalidation")
    active_version = record.active_candidate_version
    old_expiration = record.expires_at
    record = start_revalidation(
        record,
        actor_id="controller",
        started_at=old_expiration,
        reasons_ru=("Наступил срок проверки.",),
        evidence_refs=("monitoring-report",),
    )
    completed_at = old_expiration + timedelta(minutes=5)
    record = complete_revalidation(
        record,
        passed=True,
        reviewer_id="domain-owner",
        completed_at=completed_at,
        reasons_ru=("Оснований для отката не выявлено.",),
        evidence_refs=("benchmark-report", "red-team-report"),
    )

    assert record.current_stage == GovernanceStage.ACTIVE
    assert record.active_candidate_version == active_version
    assert len(record.activations) == 1
    assert record.expires_at == completed_at + timedelta(days=365)
    assert record.revalidations[0].passed is True


def test_failed_revalidation_creates_rollback_record() -> None:
    record = build_synthetic_gap_governance_record("candidate-revalidation-failed")
    active_version = record.active_candidate_version
    record = start_revalidation(
        record,
        actor_id="controller",
        started_at=record.expires_at,
        reasons_ru=("Наступил срок проверки.",),
        evidence_refs=("monitoring-report",),
    )
    record = complete_revalidation(
        record,
        passed=False,
        reviewer_id="domain-owner",
        completed_at=CREATED_AT + timedelta(days=366),
        reasons_ru=("Контрольные задачи выявили регрессию.",),
        evidence_refs=("benchmark-report:regression",),
    )

    assert record.current_stage == GovernanceStage.ROLLED_BACK
    assert record.active_candidate_version is None
    assert record.rollbacks[0].rolled_back_candidate_version == active_version


def test_manual_rollback_is_auditable_and_clears_active_version() -> None:
    record = build_synthetic_gap_governance_record("candidate-manual-rollback")
    active_version = record.active_candidate_version
    record = rollback_candidate(
        record,
        actor_id="governance-controller",
        rolled_back_at=CREATED_AT + timedelta(days=1),
        reasons_ru=("Выявлен критический инцидент качества.",),
        evidence_refs=("incident:critical-1",),
    )

    assert record.current_stage == GovernanceStage.ROLLED_BACK
    assert record.active_candidate_version is None
    assert record.rollbacks[0].rolled_back_candidate_version == active_version
    assert record.rollbacks[0].decision_id == record.decisions[-1].id


def test_synthetic_governance_artifact_is_deterministic() -> None:
    first = build_synthetic_governance_lifecycle_artifact()
    second = build_synthetic_governance_lifecycle_artifact()

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_exported_governance_lifecycle_fixture_is_valid() -> None:
    fixture_path = Path("examples/synthetic_governance_lifecycle_report.json")
    artifact = GovernanceLifecycleArtifact.model_validate(
        json.loads(fixture_path.read_text(encoding="utf-8"))
    )

    assert artifact.locale == "ru-RU"
    assert {record.current_stage for record in artifact.records} == {
        GovernanceStage.ACTIVE,
        GovernanceStage.ROLLED_BACK,
    }
    assert any(record.sandbox_evaluations for record in artifact.records)
    assert any(record.revalidations for record in artifact.records)
    assert any(record.rollbacks for record in artifact.records)
