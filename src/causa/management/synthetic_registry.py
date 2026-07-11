from datetime import datetime, timedelta

from causa.management.policy_registry import (
    BehaviorPolicyPayload,
    PolicyRegistryArtifact,
    activate_policy_snapshot,
    compare_policy_snapshots,
    create_policy_registry,
    create_policy_snapshot,
    register_policy_snapshot,
    rollback_policy_snapshot,
)
from causa.management.risk_tiers import RiskTier
from causa.management.sla_modes import SLAMode


SYNTHETIC_POLICY_FAMILY_ID = "phase0-standard-t3"
SYNTHETIC_ACTIVE_POLICY_SNAPSHOT_ID = (
    f"policy-snapshot:{SYNTHETIC_POLICY_FAMILY_ID}@1"
)


def build_synthetic_management_policy_registry_artifact() -> PolicyRegistryArtifact:
    started_at = datetime.fromisoformat("2026-07-11T09:00:00+03:00")
    baseline_payload = BehaviorPolicyPayload(
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
        translation_template_version="translation-template-v0",
        model_profile="no-llm-synthetic-demo",
    )
    strengthened_payload = baseline_payload.model_copy(
        update={
            "max_agent_passes": 4,
            "max_requests": 8,
            "max_tokens": 18_000,
            "retrieval_depth": 6,
            "confidence_threshold": 0.75,
            "allow_candidate_principles": False,
            "require_red_team": True,
            "human_review": True,
            "complete_provenance": True,
        }
    )
    baseline = create_policy_snapshot(
        family_id=SYNTHETIC_POLICY_FAMILY_ID,
        version=1,
        payload=baseline_payload,
        created_at=started_at,
        created_by="synthetic-policy-owner",
        reviewer_ids=("synthetic-domain-owner",),
        evidence_refs=("policy-matrix:standard:t3",),
        change_summary_ru="Базовая политика стандартного режима для уровня риска T3.",
    )
    strengthened = create_policy_snapshot(
        family_id=SYNTHETIC_POLICY_FAMILY_ID,
        version=2,
        parent_snapshot_id=baseline.id,
        payload=strengthened_payload,
        created_at=started_at + timedelta(minutes=8),
        created_by="synthetic-policy-owner",
        reviewer_ids=("synthetic-domain-owner", "synthetic-cross-reviewer"),
        evidence_refs=(
            "synthetic-supply-benchmark-suite-v0",
            "synthetic-supply-red-team-suite-v0",
        ),
        change_summary_ru=(
            "Усилены экспертный контроль, Red Team, provenance и порог уверенности."
        ),
    )

    registry = create_policy_registry()
    registry = register_policy_snapshot(
        registry,
        baseline,
        expected_revision=0,
        actor_id="synthetic-policy-owner",
        occurred_at=started_at,
        reasons_ru=("Зарегистрирована исходная воспроизводимая политика Этапа 0.",),
        evidence_refs=("policy-matrix:standard:t3",),
    )
    registry = activate_policy_snapshot(
        registry,
        baseline.id,
        expected_revision=1,
        expected_active_snapshot_id=None,
        actor_id="synthetic-governance-controller",
        occurred_at=started_at + timedelta(minutes=5),
        reasons_ru=("Исходная политика одобрена для синтетического пути Этапа 0.",),
        evidence_refs=("policy-approval:baseline-v1",),
    )
    registry = register_policy_snapshot(
        registry,
        strengthened,
        expected_revision=2,
        actor_id="synthetic-policy-owner",
        occurred_at=started_at + timedelta(minutes=10),
        reasons_ru=("Зарегистрирован снимок с усиленными контрольными требованиями.",),
        evidence_refs=("policy-review:strengthened-v2",),
    )
    registry = activate_policy_snapshot(
        registry,
        strengthened.id,
        expected_revision=3,
        expected_active_snapshot_id=baseline.id,
        actor_id="synthetic-governance-controller",
        occurred_at=started_at + timedelta(minutes=15),
        reasons_ru=("Усиленная политика допущена к синтетической проверке.",),
        evidence_refs=("policy-activation:strengthened-v2",),
    )
    registry = rollback_policy_snapshot(
        registry,
        family_id=SYNTHETIC_POLICY_FAMILY_ID,
        target_snapshot_id=baseline.id,
        expected_current_snapshot_id=strengthened.id,
        expected_revision=4,
        actor_id="synthetic-governance-controller",
        occurred_at=started_at + timedelta(minutes=20),
        reasons_ru=(
            "Синтетическая тренировка отката возвращает исходную политику; "
            "инцидент не моделируется.",
        ),
        evidence_refs=("policy-rollback-drill:v2-to-v1",),
    )
    semantic_diff = compare_policy_snapshots(baseline, strengthened)
    return PolicyRegistryArtifact(
        id="synthetic-management-policy-registry-report-v0",
        title_ru="Синтетический журнал версий политик Management Plane",
        summary_ru=[
            "Зарегистрированы два неизменяемых снимка одной семьи политик.",
            "Усиленная версия активирована после semantic diff и затем явно откачена.",
            "Активная версия определяется реестром, а trace хранит ее ID и content hash.",
        ],
        registry=registry,
        diffs=[semantic_diff],
    )
