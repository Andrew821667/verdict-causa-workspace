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

    assert len(SYNTHETIC_CONTRACT_SOURCES) >= 6
    assert {
        "delivery_duty",
        "delivery_term",
        "valid_excuse",
        "acceptance_defects",
        "payment_duty",
        "penalty_reduction",
    } <= topics


def test_get_synthetic_contract_source_by_id() -> None:
    source = get_synthetic_contract_source("synthetic-ru-contract-valid-excuse")

    assert source.metadata["topic"] == "valid_excuse"


def test_synthetic_supply_benchmark_suite_passes_current_narrow_expectations() -> None:
    report = run_synthetic_supply_benchmark_suite()

    assert report.total == len(SYNTHETIC_SUPPLY_BENCHMARKS)
    assert report.failed == 0
    assert report.success_rate == 1.0


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
    assert report.total >= 6
    assert report.failed == 0


def test_readiness_report_references_synthetic_benchmark_suite() -> None:
    report = build_phase0_readiness_report()
    evaluation_item = next(item for item in report.items if item.id == "ws8-evaluation-red-team")

    assert "synthetic-supply-benchmark-suite-v0" in evaluation_item.evidence_refs
