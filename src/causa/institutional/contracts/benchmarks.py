from causa.evaluation import BenchmarkTask
from causa.governance.failure_taxonomy import FailureType
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST


SYNTHETIC_SUPPLY_BENCHMARKS = [
    BenchmarkTask(
        id="bench-supply-late-no-excuse",
        title="Late delivery with no valid excuse raises breach issue",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_source_refs=[
            "synthetic-ru-contract-supply-delivery-duty",
            "synthetic-ru-contract-delivery-term",
        ],
        facts={
            "duty_exists": True,
            "valid_exception_applies": False,
        },
        temporal_facts={
            "agreed_due_date": "2026-01-15",
            "actual_performance_date": "2026-01-20",
            "evaluation_date": "2026-01-21",
        },
        expected_breach_issue=True,
    ),
    BenchmarkTask(
        id="bench-supply-late-valid-excuse",
        title="Late delivery with valid excuse does not raise breach issue",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_source_refs=[
            "synthetic-ru-contract-supply-delivery-duty",
            "synthetic-ru-contract-valid-excuse",
        ],
        facts={
            "duty_exists": True,
            "valid_exception_applies": True,
        },
        temporal_facts={
            "agreed_due_date": "2026-01-15",
            "actual_performance_date": "2026-01-20",
            "evaluation_date": "2026-01-21",
        },
        expected_breach_issue=False,
    ),
    BenchmarkTask(
        id="bench-no-duty-no-breach",
        title="No delivery duty means no breach issue",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_source_refs=["synthetic-ru-contract-supply-delivery-duty"],
        facts={
            "duty_exists": False,
            "valid_exception_applies": False,
        },
        temporal_facts={
            "agreed_due_date": "2026-01-15",
            "actual_performance_date": "2026-01-20",
            "evaluation_date": "2026-01-21",
        },
        expected_breach_issue=False,
    ),
    BenchmarkTask(
        id="bench-payment-duty-needs-separate-analysis",
        title="Payment duty should not be erased by unrelated delivery argument",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_source_refs=["synthetic-ru-contract-payment-duty"],
        expected_failure_types=[FailureType.OVERBROAD_CANDIDATE_PRINCIPLE],
        facts={
            "duty_exists": True,
            "valid_exception_applies": False,
        },
        temporal_facts={
            "agreed_due_date": "2026-01-15",
            "actual_performance_date": "2026-01-15",
            "evaluation_date": "2026-01-21",
        },
        expected_breach_issue=False,
        required_warning_fragments=["payment duty requires separate analysis"],
    ),
    BenchmarkTask(
        id="bench-defects-not-basic-delivery-date",
        title="Defects are separate from basic delivery date issue",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_source_refs=["synthetic-ru-contract-acceptance-defects"],
        facts={
            "duty_exists": True,
            "valid_exception_applies": False,
        },
        temporal_facts={
            "agreed_due_date": "2026-01-15",
            "actual_performance_date": "2026-01-14",
            "evaluation_date": "2026-01-21",
        },
        expected_breach_issue=False,
        required_warning_fragments=["defects require separate analysis"],
    ),
    BenchmarkTask(
        id="bench-penalty-reduction-boundary",
        title="Penalty reduction does not erase liability automatically",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_source_refs=["synthetic-ru-contract-penalty-reduction"],
        expected_failure_types=[FailureType.OVERBROAD_CANDIDATE_PRINCIPLE],
        facts={
            "duty_exists": True,
            "valid_exception_applies": False,
        },
        temporal_facts={
            "agreed_due_date": "2026-01-15",
            "actual_performance_date": "2026-01-20",
            "evaluation_date": "2026-01-21",
        },
        expected_breach_issue=True,
        required_warning_fragments=["penalty reduction does not erase liability"],
    ),
    BenchmarkTask(
        id="bench-delivery-duty-v1-applies-before-2026",
        title="Delivery duty v1 applies before 2026",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_source_refs=["synthetic-ru-contract-supply-delivery-duty-v1"],
        facts={
            "duty_exists": True,
            "valid_exception_applies": False,
        },
        temporal_facts={
            "agreed_due_date": "2025-12-20",
            "actual_performance_date": "2025-12-22",
            "evaluation_date": "2025-12-30",
        },
        expected_breach_issue=True,
    ),
    BenchmarkTask(
        id="bench-delivery-duty-v2-applies-from-2026",
        title="Delivery duty v2 applies from 2026",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_source_refs=["synthetic-ru-contract-supply-delivery-duty-v2"],
        facts={
            "duty_exists": True,
            "valid_exception_applies": False,
        },
        temporal_facts={
            "agreed_due_date": "2026-01-15",
            "actual_performance_date": "2026-01-20",
            "evaluation_date": "2026-01-21",
        },
        expected_breach_issue=True,
    ),
    BenchmarkTask(
        id="bench-delivery-duty-v1-not-applicable-in-2026",
        title="Delivery duty v1 is not applicable in 2026",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_source_refs=["synthetic-ru-contract-supply-delivery-duty-v1"],
        expected_source_applicability={
            "synthetic-ru-contract-supply-delivery-duty-v1": False,
        },
        facts={
            "duty_exists": True,
            "valid_exception_applies": False,
        },
        temporal_facts={
            "agreed_due_date": "2026-01-15",
            "actual_performance_date": "2026-01-20",
            "evaluation_date": "2026-01-21",
        },
        expected_breach_issue=True,
    ),
]
