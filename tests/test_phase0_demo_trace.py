import json
from pathlib import Path

from causa.governance.candidate_types import CandidateType
from causa.phase0.demo_trace import Phase0DemoTrace, build_supply_dispute_demo_trace


def test_supply_dispute_demo_trace_has_phase0_path() -> None:
    trace = build_supply_dispute_demo_trace()

    assert trace.reviewed_norm.is_reviewed is True
    assert trace.formal_translation.translator_version == "contracts-json-to-formal-v0"
    assert trace.formal_translation.obligation_rule.debtor == "supplier"
    assert trace.formal_translation.obligation_rule.creditor == "buyer"
    assert trace.constraint_evaluation.breach_issue is True
    assert trace.claim.sources == [trace.legal_source.id]
    assert trace.candidate_type == CandidateType.GAP_HEURISTIC
    assert trace.policy.mode.value == "standard"
    assert trace.translation.template_version == trace.decision_trace.versions.translation_template_version
    assert "Not legal advice." in trace.decision_trace.warnings


def test_supply_dispute_demo_trace_covers_all_knowledge_layers() -> None:
    trace = build_supply_dispute_demo_trace()
    layers = {node.layer.value for node in trace.decision_trace.nodes}

    assert layers == {"source", "formal_norm", "case", "doctrine"}


def test_exported_supply_dispute_trace_fixture_is_valid() -> None:
    fixture_path = Path("examples/phase0_supply_dispute_trace.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    trace = Phase0DemoTrace.model_validate(data)

    assert trace.disclaimer.startswith("Synthetic Phase 0 trace")
    assert trace.decision_trace.versions.institutional_package_version == "contracts-ru-v0@0.1.0"
    assert trace.formal_translation.obligation_rule.id == "obligation-rule:norm-supply-delivery-duty-v0"
    assert trace.constraint_set.id == "constraint-set:obligation-rule:norm-supply-delivery-duty-v0"
