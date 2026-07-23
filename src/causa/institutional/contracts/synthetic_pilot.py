from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.institutional.contracts.pilot_evaluation import (
    run_pilot_gate_benchmark_suite,
    run_pilot_gate_red_team_suite,
)
from causa.institutional.contracts.pilot_fixtures import (
    PILOT_REHEARSAL_DATE,
    build_maximally_realistic_pilot_intake,
)
from causa.institutional.contracts.pilot_utility import (
    build_privacy_safe_pilot_utility_report,
)
from causa.management.policy_registry import active_policy_snapshot
from causa.management.synthetic_registry import (
    SYNTHETIC_POLICY_FAMILY_ID,
    build_synthetic_management_policy_registry_artifact,
)
from causa.pilot import (
    PilotRehearsalArtifact,
    PilotRunManifest,
    evaluate_pilot_intake,
)


def build_synthetic_pilot_rehearsal_artifact() -> PilotRehearsalArtifact:
    intake = build_maximally_realistic_pilot_intake()
    gate = evaluate_pilot_intake(
        intake,
        evaluated_on=PILOT_REHEARSAL_DATE,
        expected_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_package_version=CONTRACTS_PACKAGE_MANIFEST.version,
    )
    registry = build_synthetic_management_policy_registry_artifact().registry
    policy = active_policy_snapshot(registry, SYNTHETIC_POLICY_FAMILY_ID)
    trace_ref = "trace-phase0-supply-dispute-v0"
    run = PilotRunManifest(
        id="pilot-run-5a1e0001",
        intake_fingerprint=gate.intake_fingerprint,
        gate_decision_id=gate.id,
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        institutional_package_version=CONTRACTS_PACKAGE_MANIFEST.version,
        decision_trace_ref=trace_ref,
        reviewed_analysis_ref="analysis-request-case-supply-1-v0",
        translation_bundle_ref=f"translation-bundle:{trace_ref}",
        policy_snapshot_ref=policy.id,
        policy_content_hash=policy.content_hash,
        source_hashes=tuple(sorted(document.content_sha256 for document in intake.documents)),
        executed_on=PILOT_REHEARSAL_DATE,
    )
    return PilotRehearsalArtifact(
        id="contracts-max-realistic-pilot-rehearsal-v1",
        disclaimer_ru=(
            "Это синтетическая репетиция допуска максимально приближенного к реальности "
            "дела. Она не содержит клиентских документов, не доказывает промышленную "
            "готовность и не заменяет одобрение реального пилота."
        ),
        intake=intake,
        gate_decision=gate,
        run_manifest=run,
        utility_report=build_privacy_safe_pilot_utility_report(),
        benchmark_report=run_pilot_gate_benchmark_suite(),
        red_team_report=run_pilot_gate_red_team_suite(),
    )
