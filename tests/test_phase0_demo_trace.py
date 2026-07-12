import json
from pathlib import Path

from causa.governance.candidate_types import CandidateType
from causa.phase0.demo_trace import Phase0DemoTrace, build_supply_dispute_demo_trace
from causa.translation import TranslationLevel


def test_supply_dispute_demo_trace_has_phase0_path() -> None:
    trace = build_supply_dispute_demo_trace()

    assert trace.reviewed_norm.is_reviewed is True
    assert trace.formal_translation.translator_version == "contracts-json-to-formal-v0"
    assert trace.formal_translation.obligation_rule.debtor == "поставщик"
    assert trace.formal_translation.obligation_rule.creditor == "покупатель"
    assert trace.temporal_evaluation.due_date_missed is True
    assert trace.source_applicability.applicable is True
    assert trace.analysis_result.pipeline_version == "contracts-reviewed-analysis-v7"
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
    assert (
        trace.translation.template_version
        == trace.decision_trace.versions.translation_template_version
    )
    assert len(trace.translation_bundle.artifacts) == 3
    assert {artifact.level for artifact in trace.translation_bundle.artifacts} == set(
        TranslationLevel
    )
    assert trace.translation_bundle.faithfulness_report.passed is True
    assert trace.translation_bundle.usability_report.structural_checks_passed is True
    assert trace.translation_bundle.usability_report.requires_human_pilot is True
    assert trace.translation_bundle.ready_for_human_review is True
    assert trace.policy_snapshot.payload.allow_counterfactual is True
    assert trace.analysis_result.counterfactual_sensitivity.budget.max_scenarios == 8
    assert trace.analysis_result.liability_evaluation.liability_issue is True
    assert trace.analysis_result.liability_evaluation.force_majeure_qualified is False
    assert trace.analysis_result.formation_evaluation.valid_offer is True
    assert trace.analysis_result.formation_evaluation.conduct_acceptance_valid is True
    assert trace.analysis_result.formation_evaluation.contract_concluded_prerequisites is True
    assert trace.analysis_result.invalidity_evaluation.transaction_presumed_effective is True
    assert trace.analysis_result.invalidity_evaluation.void_ground_detected is False
    assert trace.analysis_result.invalidity_evaluation.voidable_ground_detected is False
    assert trace.analysis_result.security_evaluation.security_mechanism_detected is False
    assert trace.analysis_result.security_evaluation.security_enforcement_available is False
    assert trace.analysis_result.obligation_dynamics_evaluation.obligation_discharged_full is True
    assert trace.analysis_result.obligation_dynamics_evaluation.accrued_claims_preserved is True
    assert trace.analysis_result.performance_remedies_evaluation.debtor_in_delay is True
    assert trace.analysis_result.performance_remedies_evaluation.proper_performance is False
    assert trace.analysis_result.termination_evaluation.contract_continues_unchanged is True
    assert trace.analysis_result.termination_evaluation.effective_modification is False
    assert trace.analysis_result.termination_evaluation.effective_termination is False
    assert (
        trace.decision_trace.versions.legal_operator_library_hash
        == trace.analysis_result.counterfactual_sensitivity.operator_library_hash
    )
    assert (
        trace.decision_trace.versions.legal_operator_library_version
        == trace.analysis_result.counterfactual_sensitivity.operator_library_version
    )
    assert (
        trace.translation_bundle.template_content_hash
        == trace.decision_trace.versions.translation_template_hash
    )
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
    assert trace.decision_trace.versions.institutional_package_version == "contracts-ru-v0@0.15.0"
    assert trace.analysis_result.security_constraint_set.model_version == (
        "contracts-performance-security-articles-329-3812-v0"
    )
    assert trace.analysis_result.obligation_dynamics_constraint_set.model_version == (
        "contracts-obligation-dynamics-articles-382-419-v0"
    )
    assert trace.analysis_result.performance_remedies_constraint_set.model_version == (
        "contracts-performance-remedies-articles-309-328-393-4061-v0"
    )
    assert trace.decision_trace.versions.policy_version == trace.policy_snapshot.id
    assert trace.decision_trace.versions.policy_content_hash == trace.policy_snapshot.content_hash
    assert trace.governance_record.policy_version == trace.policy_snapshot.id
    assert trace.governance_record.policy_content_hash == trace.policy_snapshot.content_hash
    assert (
        trace.formal_translation.obligation_rule.id
        == "obligation-rule:norm-supply-delivery-duty-v0"
    )
    assert trace.constraint_set.id == "constraint-set:obligation-rule:norm-supply-delivery-duty-v0"
    assert trace.temporal_facts.agreed_due_date.isoformat() == "2026-01-15"
    assert trace.legal_source.valid_from == "2026-01-01"
