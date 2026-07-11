from datetime import datetime, timedelta

from causa.governance.candidate_types import CandidateType
from causa.governance.engine import (
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
from causa.management.policy_registry import active_policy_snapshot
from causa.management.synthetic_registry import (
    SYNTHETIC_ACTIVE_POLICY_SNAPSHOT_ID,
    SYNTHETIC_POLICY_FAMILY_ID,
    build_synthetic_management_policy_registry_artifact,
)


def _approve_until(
    record: GovernanceRecord,
    target_stage: GovernanceStage,
    *,
    actor_id: str,
    started_at: datetime,
) -> GovernanceRecord:
    current = record
    decided_at = started_at
    while current.current_stage != target_stage:
        current = submit_stage_decision(
            current,
            expected_stage=current.current_stage,
            passed=True,
            actor_id=actor_id,
            decided_at=decided_at,
            reasons_ru=(
                f"Стадия «{current.current_stage_label_ru}» успешно пройдена "
                "на синтетических проверочных данных.",
            ),
            evidence_refs=(
                f"synthetic-governance-evidence:{current.current_stage.value}",
            ),
        )
        decided_at += timedelta(minutes=1)
    return current


def build_synthetic_gap_governance_record(
    candidate_id: str,
    *,
    include_revalidation: bool = False,
    policy_version: str = SYNTHETIC_ACTIVE_POLICY_SNAPSHOT_ID,
    policy_content_hash: str | None = None,
) -> GovernanceRecord:
    if policy_content_hash is None:
        registry = build_synthetic_management_policy_registry_artifact().registry
        policy_content_hash = active_policy_snapshot(
            registry,
            SYNTHETIC_POLICY_FAMILY_ID,
        ).content_hash
    created_at = datetime.fromisoformat("2026-07-11T10:00:00+03:00")
    record = create_governance_record(
        candidate_id=candidate_id,
        candidate_type=CandidateType.GAP_HEURISTIC,
        policy_version=policy_version,
        policy_content_hash=policy_content_hash,
        created_at=created_at,
    )
    record = _approve_until(
        record,
        GovernanceStage.ACTIVE,
        actor_id="synthetic-domain-owner",
        started_at=created_at + timedelta(minutes=1),
    )
    if not include_revalidation:
        return record

    revalidation_started_at = record.expires_at or created_at + timedelta(days=365)
    record = start_revalidation(
        record,
        actor_id="synthetic-governance-controller",
        started_at=revalidation_started_at,
        reasons_ru=("Наступил плановый срок повторной валидации кандидата.",),
        evidence_refs=("synthetic-monitoring-report:gap-heuristic-v0",),
    )
    return complete_revalidation(
        record,
        passed=True,
        reviewer_id="synthetic-domain-owner",
        completed_at=revalidation_started_at + timedelta(minutes=5),
        reasons_ru=(
            "Повторная проверка источников и контрольных задач не выявила оснований для отката.",
        ),
        evidence_refs=(
            "synthetic-supply-benchmark-suite-v0",
            "synthetic-supply-red-team-suite-v0",
        ),
    )


def build_synthetic_sandbox_and_rollback_record() -> GovernanceRecord:
    candidate_id = "candidate-conflict-resolution-sandbox-v0"
    created_at = datetime.fromisoformat("2026-07-11T11:00:00+03:00")
    policy_registry = build_synthetic_management_policy_registry_artifact().registry
    policy_snapshot = active_policy_snapshot(
        policy_registry,
        SYNTHETIC_POLICY_FAMILY_ID,
    )
    record = create_governance_record(
        candidate_id=candidate_id,
        candidate_type=CandidateType.CONFLICT_RESOLUTION_PATTERN,
        policy_version=SYNTHETIC_ACTIVE_POLICY_SNAPSHOT_ID,
        policy_content_hash=policy_snapshot.content_hash,
        created_at=created_at,
    )
    record = _approve_until(
        record,
        GovernanceStage.SANDBOX,
        actor_id="synthetic-domain-owner",
        started_at=created_at + timedelta(minutes=1),
    )
    sandbox = SandboxEvaluationRecord(
        id="sandbox-evaluation-conflict-resolution-v0",
        candidate_id=candidate_id,
        started_at=created_at + timedelta(minutes=8),
        completed_at=created_at + timedelta(minutes=20),
        evaluator_id="synthetic-red-team-reviewer",
        isolation_scope_ru=(
            "Только синтетические договорные задачи; доступ к активному знанию и клиентским данным закрыт."
        ),
        scenario_count=13,
        failed_scenario_count=0,
        passed=True,
        reasons_ru=(
            "Кандидат не привел к запрещенным результатам в изолированном наборе сценариев.",
        ),
        evidence_refs=("synthetic-supply-red-team-suite-v0",),
    )
    record = complete_sandbox(record, sandbox)
    return rollback_candidate(
        record,
        actor_id="synthetic-governance-controller",
        rolled_back_at=created_at + timedelta(minutes=30),
        reasons_ru=(
            "Синтетический откат демонстрирует обратимость активации; инцидент не моделируется.",
        ),
        evidence_refs=("synthetic-rollback-drill:conflict-resolution-v0",),
    )


def build_synthetic_governance_lifecycle_artifact() -> GovernanceLifecycleArtifact:
    policy_registry = build_synthetic_management_policy_registry_artifact().registry
    policy_snapshot = active_policy_snapshot(
        policy_registry,
        SYNTHETIC_POLICY_FAMILY_ID,
    )
    gap_record = build_synthetic_gap_governance_record(
        "candidate-supply-excuse-scope",
        include_revalidation=True,
    )
    rollback_record = build_synthetic_sandbox_and_rollback_record()
    return GovernanceLifecycleArtifact(
        id="synthetic-governance-lifecycle-report-v0",
        title_ru="Синтетический журнал governance-жизненного цикла",
        policy_snapshot_id=policy_snapshot.id,
        policy_content_hash=policy_snapshot.content_hash,
        summary_ru=[
            "Эвристика пробела активирована и успешно прошла плановую повторную валидацию.",
            "Паттерн разрешения противоречий прошел песочницу и затем был явно откачен.",
            "Все решения содержат русские причины, доказательства, исполнителя и версию политики.",
        ],
        records=[gap_record, rollback_record],
    )
