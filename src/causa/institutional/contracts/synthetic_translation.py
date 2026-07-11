from causa.governance.synthetic_lifecycle import build_synthetic_gap_governance_record
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
)
from causa.management.policy_registry import active_policy_snapshot
from causa.management.synthetic_registry import (
    SYNTHETIC_POLICY_FAMILY_ID,
    build_synthetic_management_policy_registry_artifact,
)
from causa.translation_pipeline import TranslationBundleArtifact, build_translation_bundle


SYNTHETIC_TRANSLATION_TRACE_ID = "trace-phase0-supply-dispute-v0"


def build_synthetic_translation_bundle_artifact() -> TranslationBundleArtifact:
    analysis = build_synthetic_supply_analysis_artifact()
    registry = build_synthetic_management_policy_registry_artifact().registry
    policy_snapshot = active_policy_snapshot(registry, SYNTHETIC_POLICY_FAMILY_ID)
    governance = build_synthetic_gap_governance_record(
        "candidate-supply-excuse-scope",
        policy_version=policy_snapshot.id,
        policy_content_hash=policy_snapshot.content_hash,
    )
    bundle = build_translation_bundle(
        trace_id=SYNTHETIC_TRANSLATION_TRACE_ID,
        request=analysis.request,
        result=analysis.result,
        governance=governance,
        policy_snapshot=policy_snapshot,
    )
    return TranslationBundleArtifact(bundle=bundle)
