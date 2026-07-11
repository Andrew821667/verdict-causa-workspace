import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.management.policy_registry import (
    BehaviorPolicyPayload,
    JSONPolicyRegistryStore,
    PolicyChangeImpact,
    PolicyDiffDirection,
    PolicyRegistryArtifact,
    PolicyRegistryState,
    PolicySnapshot,
    activate_policy_snapshot,
    active_policy_snapshot,
    compute_policy_content_hash,
    create_policy_registry,
    create_policy_snapshot,
    register_policy_snapshot,
)
from causa.management.risk_tiers import RiskTier
from causa.management.sla_modes import SLAMode
from causa.management.synthetic_registry import (
    SYNTHETIC_ACTIVE_POLICY_SNAPSHOT_ID,
    SYNTHETIC_POLICY_FAMILY_ID,
    build_synthetic_management_policy_registry_artifact,
)
from causa.translation_templates import build_russian_translation_template_set


STARTED_AT = datetime.fromisoformat("2026-07-11T09:00:00+03:00")


def _baseline_payload() -> BehaviorPolicyPayload:
    translation_templates = build_russian_translation_template_set()
    return BehaviorPolicyPayload(
        mode=SLAMode.STANDARD,
        risk_tier=RiskTier.T3_DRAFT_LETTER,
        max_agent_passes=3,
        max_requests=6,
        max_tokens=12_000,
        retrieval_depth=4,
        confidence_threshold=0.62,
        allow_candidate_principles=True,
        require_formal_check=True,
        require_red_team=False,
        human_review=False,
        cross_review=False,
        replayable_trace=True,
        complete_provenance=False,
        escalate_on_low_confidence=True,
        translation_template_version=translation_templates.version,
        translation_template_hash=translation_templates.content_hash,
        model_profile="no-llm-synthetic-demo",
    )


def _snapshot(
    version: int,
    payload: BehaviorPolicyPayload | None = None,
    parent_snapshot_id: str | None = None,
) -> PolicySnapshot:
    return create_policy_snapshot(
        family_id="test-standard-t3",
        version=version,
        payload=payload or _baseline_payload(),
        parent_snapshot_id=parent_snapshot_id,
        created_at=STARTED_AT + timedelta(minutes=version),
        created_by="policy-owner-test",
        reviewer_ids=("domain-owner-test",),
        evidence_refs=(f"policy-review:{version}",),
        change_summary_ru=f"Тестовая версия политики {version}.",
    )


def _register(
    registry: PolicyRegistryState,
    snapshot: PolicySnapshot,
    minute: int,
) -> PolicyRegistryState:
    return register_policy_snapshot(
        registry,
        snapshot,
        expected_revision=registry.revision,
        actor_id="policy-owner-test",
        occurred_at=STARTED_AT + timedelta(minutes=minute),
        reasons_ru=("Снимок проверен и зарегистрирован.",),
        evidence_refs=(f"registration:{snapshot.version}",),
    )


def test_policy_hash_is_deterministic_and_sensitive_to_behavior() -> None:
    baseline = _baseline_payload()
    changed = baseline.model_copy(update={"confidence_threshold": 0.75})

    assert compute_policy_content_hash(baseline) == compute_policy_content_hash(
        _baseline_payload()
    )
    assert compute_policy_content_hash(baseline) != compute_policy_content_hash(changed)


def test_policy_snapshot_rejects_tampered_payload() -> None:
    snapshot = _snapshot(1)
    payload = snapshot.model_dump(mode="json")
    payload["payload"]["confidence_threshold"] = 0.99

    with pytest.raises(ValidationError, match="Hash содержимого"):
        PolicySnapshot.model_validate(payload)


def test_high_risk_policy_requires_human_red_team_provenance_and_cross_review() -> None:
    payload = _baseline_payload().model_dump(mode="json")
    payload.update(
        {
            "risk_tier": RiskTier.T5_HIGH_STAKES_RECOMMENDATION,
            "human_review": False,
            "require_red_team": False,
            "complete_provenance": False,
            "cross_review": False,
        }
    )

    with pytest.raises(ValidationError, match="T4-T6 требует экспертной"):
        BehaviorPolicyPayload.model_validate(payload)


def test_policy_always_requires_replayable_trace() -> None:
    payload = _baseline_payload().model_dump(mode="json")
    payload["replayable_trace"] = False

    with pytest.raises(ValidationError, match="воспроизводимую трассировку"):
        BehaviorPolicyPayload.model_validate(payload)


def test_registry_registers_and_activates_snapshot_with_revision_log() -> None:
    snapshot = _snapshot(1)
    registry = _register(create_policy_registry(), snapshot, minute=2)
    registry = activate_policy_snapshot(
        registry,
        snapshot.id,
        expected_revision=1,
        expected_active_snapshot_id=None,
        actor_id="governance-controller-test",
        occurred_at=STARTED_AT + timedelta(minutes=3),
        reasons_ru=("Политика одобрена к применению.",),
        evidence_refs=("activation-approval:1",),
    )

    assert registry.revision == 2
    assert active_policy_snapshot(registry, snapshot.family_id) == snapshot
    assert [event.event_type.value for event in registry.events] == [
        "registered",
        "activated",
    ]
    assert all(event.reasons_ru for event in registry.events)


def test_registry_rejects_stale_revision() -> None:
    snapshot = _snapshot(1)
    registry = _register(create_policy_registry(), snapshot, minute=2)

    with pytest.raises(ValueError, match="Ревизия реестра изменилась"):
        activate_policy_snapshot(
            registry,
            snapshot.id,
            expected_revision=0,
            expected_active_snapshot_id=None,
            actor_id="controller",
            occurred_at=STARTED_AT + timedelta(minutes=3),
            reasons_ru=("Устаревшая команда.",),
            evidence_refs=("stale-command",),
        )


def test_registry_rejects_noop_policy_version() -> None:
    first = _snapshot(1)
    registry = _register(create_policy_registry(), first, minute=2)
    duplicate = _snapshot(2, parent_snapshot_id=first.id)

    with pytest.raises(ValueError, match="повторяет существующее"):
        _register(registry, duplicate, minute=3)


def test_older_policy_requires_explicit_rollback() -> None:
    artifact = build_synthetic_management_policy_registry_artifact()
    baseline, strengthened = artifact.registry.snapshots
    registry = PolicyRegistryState.model_validate(
        {
            **artifact.registry.model_dump(mode="json"),
            "revision": 4,
            "events": artifact.registry.model_dump(mode="json")["events"][:4],
            "active_snapshot_ids": {SYNTHETIC_POLICY_FAMILY_ID: strengthened.id},
        }
    )

    with pytest.raises(ValueError, match="явный откат"):
        activate_policy_snapshot(
            registry,
            baseline.id,
            expected_revision=registry.revision,
            expected_active_snapshot_id=strengthened.id,
            actor_id="controller",
            occurred_at=registry.events[-1].occurred_at + timedelta(minutes=1),
            reasons_ru=("Некорректная повторная активация.",),
            evidence_refs=("activation:no-op",),
        )

    assert strengthened.version > baseline.version


def test_explicit_rollback_records_previous_and_target_snapshots() -> None:
    artifact = build_synthetic_management_policy_registry_artifact()
    registry = artifact.registry
    rollback_event = registry.events[-1]

    assert rollback_event.event_type.value == "rolled_back"
    assert rollback_event.snapshot_id == registry.snapshots[0].id
    assert rollback_event.previous_snapshot_id == registry.snapshots[1].id
    assert registry.active_snapshot_ids[SYNTHETIC_POLICY_FAMILY_ID] == (
        SYNTHETIC_ACTIVE_POLICY_SNAPSHOT_ID
    )


def test_semantic_diff_classifies_tightening_and_russian_labels() -> None:
    artifact = build_synthetic_management_policy_registry_artifact()
    semantic_diff = artifact.diffs[0]

    assert semantic_diff.direction == PolicyDiffDirection.TIGHTENED
    assert semantic_diff.direction_label_ru == "Контроль усилен"
    assert any(
        change.field_name == "human_review"
        and change.impact == PolicyChangeImpact.TIGHTENING
        and change.field_label_ru == "Обязательная экспертная проверка"
        and change.before_label_ru == "Нет"
        and change.after_label_ru == "Да"
        for change in semantic_diff.changes
    )
    assert any(
        change.field_name == "max_tokens"
        and change.impact == PolicyChangeImpact.BEHAVIORAL
        for change in semantic_diff.changes
    )


def test_loaded_registry_rejects_broken_event_sequence() -> None:
    registry = build_synthetic_management_policy_registry_artifact().registry
    payload = registry.model_dump(mode="json")
    payload["events"][2]["sequence"] = 99

    with pytest.raises(ValidationError, match="последовательность"):
        PolicyRegistryState.model_validate(payload)


def test_json_store_round_trip_and_stale_write_protection(tmp_path: Path) -> None:
    registry = build_synthetic_management_policy_registry_artifact().registry
    store = JSONPolicyRegistryStore(tmp_path / "management-policy-registry.json")
    store.save(registry, expected_persisted_revision=None)

    assert store.load() == registry
    assert not (tmp_path / "management-policy-registry.json.tmp").exists()
    with pytest.raises(ValueError, match="Сохраненная ревизия"):
        store.save(registry, expected_persisted_revision=registry.revision - 1)


def test_synthetic_policy_registry_artifact_is_deterministic() -> None:
    first = build_synthetic_management_policy_registry_artifact()
    second = build_synthetic_management_policy_registry_artifact()

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_exported_policy_registry_fixture_is_valid() -> None:
    fixture_path = Path("examples/synthetic_management_policy_registry_report.json")
    artifact = PolicyRegistryArtifact.model_validate(
        json.loads(fixture_path.read_text(encoding="utf-8"))
    )

    active = active_policy_snapshot(artifact.registry, SYNTHETIC_POLICY_FAMILY_ID)
    assert active.id == SYNTHETIC_ACTIVE_POLICY_SNAPSHOT_ID
    assert artifact.registry.revision == 5
    assert artifact.diffs[0].changes
