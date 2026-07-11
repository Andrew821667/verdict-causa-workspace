import json
from pathlib import Path

from causa.governance.candidate_types import CandidateType
from causa.phase0.demo_trace import Phase0DemoTrace, build_supply_dispute_demo_trace


def test_supply_dispute_demo_trace_has_phase0_path() -> None:
    trace = build_supply_dispute_demo_trace()

    assert trace.reviewed_norm.is_reviewed is True
    assert trace.formal_translation.translator_version == "contracts-json-to-formal-v0"
    assert trace.formal_translation.obligation_rule.debtor == "поставщик"
    assert trace.formal_translation.obligation_rule.creditor == "покупатель"
    assert trace.temporal_evaluation.due_date_missed is True
    assert trace.source_applicability.applicable is True
    assert trace.analysis_result.pipeline_version == "contracts-reviewed-analysis-v0"
    assert len(trace.analysis_result.evidence_mapping.provenance) == 13
    assert (
        trace.analysis_result.authority_evaluation.selected_source_id
        == trace.reviewed_norm.source_id
    )
    assert trace.obligation_facts.due_date_missed is True
    assert trace.constraint_evaluation.breach_issue is True
    assert trace.constraint_evaluation.late_performance_issue is True
    assert trace.constraint_evaluation.defect_issue is False
    assert trace.constraint_evaluation.payment_default_issue is False
    assert trace.constraint_evaluation.damages_remedy_available is False
    assert trace.constraint_evaluation.causation_evidence_gap is False
    assert trace.constraint_evaluation.limitation_bar is False
    assert trace.claim.sources == [trace.legal_source.id]
    assert trace.candidate_type == CandidateType.GAP_HEURISTIC
    assert trace.policy.mode.value == "standard"
    assert trace.governance_record.current_stage.value == "active"
    assert trace.governance_record.current_stage_label_ru == "Активно"
    assert trace.translation.template_version == trace.decision_trace.versions.translation_template_version
    assert "Не является юридической консультацией." in trace.decision_trace.warnings


def test_supply_dispute_demo_trace_covers_all_knowledge_layers() -> None:
    trace = build_supply_dispute_demo_trace()
    layers = {node.layer.value for node in trace.decision_trace.nodes}

    assert layers == {"source", "formal_norm", "case", "doctrine"}


def test_exported_supply_dispute_trace_fixture_is_valid() -> None:
    fixture_path = Path("examples/phase0_supply_dispute_trace.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    trace = Phase0DemoTrace.model_validate(data)

    assert trace.locale == "ru-RU"
    assert trace.disclaimer.startswith("Синтетическая трассировка Этапа 0")
    assert trace.decision_trace.versions.institutional_package_version == "contracts-ru-v0@0.6.0"
    assert trace.decision_trace.versions.policy_version == trace.policy_snapshot.id
    assert (
        trace.decision_trace.versions.policy_content_hash
        == trace.policy_snapshot.content_hash
    )
    assert trace.governance_record.policy_version == trace.policy_snapshot.id
    assert (
        trace.governance_record.policy_content_hash
        == trace.policy_snapshot.content_hash
    )
    assert trace.formal_translation.obligation_rule.id == "obligation-rule:norm-supply-delivery-duty-v0"
    assert trace.constraint_set.id == "constraint-set:obligation-rule:norm-supply-delivery-duty-v0"
    assert trace.temporal_facts.agreed_due_date.isoformat() == "2026-01-15"
    assert trace.legal_source.valid_from == "2026-01-01"
