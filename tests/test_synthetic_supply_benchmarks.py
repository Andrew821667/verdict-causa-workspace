import json
from pathlib import Path

from causa.evaluation import BenchmarkSuiteReport
from causa.institutional.contracts.benchmark_runner import (
    run_benchmark_task,
    run_synthetic_supply_benchmark_suite,
)
from causa.institutional.contracts.benchmarks import SYNTHETIC_SUPPLY_BENCHMARKS
from causa.institutional.contracts.synthetic_sources import (
    SYNTHETIC_CONTRACT_SOURCES,
    get_synthetic_contract_source,
)
from causa.phase0.pipeline import build_phase0_readiness_report


def test_synthetic_contract_source_set_has_initial_coverage() -> None:
    topics = {source.metadata["topic"] for source in SYNTHETIC_CONTRACT_SOURCES}

    assert len(SYNTHETIC_CONTRACT_SOURCES) >= 8
    assert {
        "delivery_duty",
        "delivery_term",
        "valid_excuse",
        "acceptance_defects",
        "payment_duty",
        "penalty_reduction",
    } <= topics


def test_synthetic_contract_source_set_has_delivery_duty_revisions() -> None:
    revisions = {
        source.metadata.get("revision")
        for source in SYNTHETIC_CONTRACT_SOURCES
        if source.metadata["topic"] == "delivery_duty"
    }

    assert {"v1", "v2"} <= revisions


def test_synthetic_contract_source_set_has_general_and_special_sources() -> None:
    specificity_by_id = {
        source.id: source.metadata.get("specificity")
        for source in SYNTHETIC_CONTRACT_SOURCES
    }

    assert specificity_by_id["synthetic-ru-contract-general-performance-duty"] == "general"
    assert (
        specificity_by_id["synthetic-ru-contract-supply-specific-delivery-duty"]
        == "special"
    )


def test_get_synthetic_contract_source_by_id() -> None:
    source = get_synthetic_contract_source("synthetic-ru-contract-valid-excuse")

    assert source.metadata["topic"] == "valid_excuse"


def test_synthetic_supply_benchmark_suite_passes_current_narrow_expectations() -> None:
    report = run_synthetic_supply_benchmark_suite()

    assert report.total == len(SYNTHETIC_SUPPLY_BENCHMARKS)
    assert report.failed == 0
    assert report.success_rate == 1.0
    assert any(result.temporal_reasons for result in report.results)
    assert any(result.source_applicability_reasons for result in report.results)
    assert any(result.authority_winner for result in report.results)
    assert any(result.authority_rules for result in report.results)


def test_revision_benchmark_records_old_source_not_applicable() -> None:
    task = next(task for task in SYNTHETIC_SUPPLY_BENCHMARKS if task.id.endswith("not-applicable-in-2026"))
    result = run_benchmark_task(task)

    assert result.passed is True
    assert any("after source valid_to" in reason for reason in result.source_applicability_reasons)


def test_lex_specialis_benchmarks_select_supply_specific_source() -> None:
    authority_results = [
        run_benchmark_task(task)
        for task in SYNTHETIC_SUPPLY_BENCHMARKS
        if "specialis" in task.id or "supply-special" in task.id
    ]

    assert len(authority_results) == 2
    assert all(result.passed for result in authority_results)
    assert {
        result.authority_winner for result in authority_results
    } == {"synthetic-ru-contract-supply-specific-delivery-duty"}
    assert all(
        "Special source prevails over general source at the same authority level."
        in result.authority_reasons
        for result in authority_results
    )


def test_authority_hierarchy_benchmarks_record_priority_and_temporal_rules() -> None:
    hierarchy_results = {
        task.id: run_benchmark_task(task)
        for task in SYNTHETIC_SUPPLY_BENCHMARKS
        if task.expected_authority_rules
    }

    assert hierarchy_results["bench-statutory-source-prevails-over-contract-specific"].authority_rules == [
        "higher_authority"
    ]
    assert hierarchy_results["bench-statutory-source-prevails-over-factual-assertion"].authority_rules == [
        "higher_authority"
    ]
    assert hierarchy_results[
        "bench-constitutional-source-prevails-over-special-statute"
    ].authority_winner == "synthetic-ru-constitutional-contract-guarantee"
    assert hierarchy_results[
        "bench-statutory-source-prevails-over-special-regulation"
    ].authority_winner == "synthetic-ru-contract-general-performance-duty"
    expired_source_result = hierarchy_results[
        "bench-inapplicable-statute-yields-to-current-case-law"
    ]
    assert expired_source_result.authority_rules == ["temporal_applicability"]
    assert expired_source_result.authority_excluded_source_refs == [
        "synthetic-ru-contract-supply-delivery-duty-v1"
    ]


def test_extended_constraint_benchmarks_keep_delay_defect_and_payment_distinct() -> None:
    extended_results = {
        task.id: run_benchmark_task(task)
        for task in SYNTHETIC_SUPPLY_BENCHMARKS
        if "defect" in task.id or "payment-default" in task.id or "payment-defense" in task.id
    }

    defect_result = extended_results["bench-confirmed-defect-after-timely-performance"]
    assert defect_result.breach_issue is True
    assert defect_result.late_performance_issue is False
    assert defect_result.defect_issue is True

    payment_default_result = extended_results["bench-payment-default-without-defense"]
    assert payment_default_result.breach_issue is True
    assert payment_default_result.payment_default_issue is True

    payment_defense_result = extended_results[
        "bench-payment-defense-prevents-payment-default-issue"
    ]
    assert payment_defense_result.breach_issue is False
    assert payment_defense_result.payment_default_issue is False


def test_remedy_constraint_benchmarks_keep_causation_and_limitation_distinct() -> None:
    remedy_results = {
        task.id: run_benchmark_task(task)
        for task in SYNTHETIC_SUPPLY_BENCHMARKS
        if "damages-remedy" in task.id or "limitation-period" in task.id
    }

    available_result = remedy_results["bench-damages-remedy-available-after-late-delivery"]
    assert available_result.damages_remedy_available is True
    assert available_result.causation_evidence_gap is False
    assert available_result.limitation_bar is False

    causation_result = remedy_results["bench-damages-remedy-needs-causation"]
    assert causation_result.damages_remedy_available is False
    assert causation_result.causation_evidence_gap is True

    limitation_result = remedy_results["bench-limitation-period-bars-damages-remedy"]
    assert limitation_result.damages_remedy_available is False
    assert limitation_result.limitation_bar is True


def test_payment_benchmark_records_separate_analysis_warning() -> None:
    task = next(task for task in SYNTHETIC_SUPPLY_BENCHMARKS if "payment" in task.id)
    result = run_benchmark_task(task)

    assert result.passed is True
    assert "payment duty requires separate analysis" in result.warnings


def test_exported_synthetic_supply_benchmark_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/synthetic_supply_benchmark_report.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    report = BenchmarkSuiteReport.model_validate(data)

    assert report.id == "synthetic-supply-benchmark-suite-v0"
    assert report.total == len(SYNTHETIC_SUPPLY_BENCHMARKS)
    assert report.failed == 0


def test_readiness_report_references_synthetic_benchmark_suite() -> None:
    report = build_phase0_readiness_report()
    evaluation_item = next(item for item in report.items if item.id == "ws8-evaluation-red-team")

    assert "synthetic-supply-benchmark-suite-v0" in evaluation_item.evidence_refs
