from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.paid_services import (
    PAID_SERVICES_EVIDENCE_SCHEMA_VERSION,
    PAID_SERVICES_MAPPING_VERSION,
    PAID_SERVICES_MODEL_VERSION,
    PaidServicesFactSet,
    ReviewedPaidServicesEvidence,
)
from causa.institutional.contracts.paid_services_evaluation import (
    SYNTHETIC_PAID_SERVICES_BENCHMARKS,
    SYNTHETIC_PAID_SERVICES_RED_TEAM_CASES,
    run_paid_services_benchmark_suite,
    run_paid_services_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_paid_services import (
    SyntheticPaidServicesEvaluationArtifact,
    build_synthetic_paid_services_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_paid_services_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.paid_services_evidence_mapping
    assert mapping.schema_version == PAID_SERVICES_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == PAID_SERVICES_MAPPING_VERSION
    assert result.paid_services_constraint_set.model_version == PAID_SERVICES_MODEL_VERSION
    evaluation = result.paid_services_evaluation
    # В демонстрационном деле спор о поставке товаров, а не об оказании услуг.
    assert evaluation.paid_services_qualified is False
    assert evaluation.payment_duty_breached is False
    assert evaluation.requires_human_paid_services_assessment is False


def test_paid_services_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.paid_services_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedPaidServicesEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=(*evidence.assertions, evidence.assertions[0]),
            legal_source_refs=evidence.legal_source_refs,
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )

    incomplete = evidence.model_copy(update={"assertions": evidence.assertions[:-1]})
    with pytest.raises(ValueError, match="missing predicates"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"paid_services_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_paid_services_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.paid_services_evidence

    with pytest.raises(ValueError, match="Paid-services evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "paid_services_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Paid-services evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"paid_services_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "paid_services_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-paid-services-evidence",
                                "synthetic-ru-gk782-783-1-paid-services-withdrawal-and-communication-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_paid_services_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in PaidServicesFactSet.model_fields}
    values.update(actual_expenses_not_reimbursed=True)
    with pytest.raises(ValidationError, match="Невозмещение фактически понесённых расходов"):
        PaidServicesFactSet(**values)

    conflicting = {field_name: False for field_name in PaidServicesFactSet.model_fields}
    conflicting.update(
        services_rendered_for_fee_by_assignment=True,
        impossibility_caused_by_customer=True,
        impossibility_without_party_fault=True,
    )
    with pytest.raises(ValidationError, match="исключают друг друга"):
        PaidServicesFactSet(**conflicting)


def test_paid_services_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk779-781-paid-services-concept-personal-performance-and-payment-v1",
        "synthetic-ru-gk782-783-1-paid-services-withdrawal-and-communication-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_paid_services_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_paid_services_benchmark_suite()
    red_team = run_paid_services_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_PAID_SERVICES_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_PAID_SERVICES_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_paid_services_artifact_is_reproducible() -> None:
    fixture = SyntheticPaidServicesEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_paid_services_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_paid_services_evaluation_artifact()
