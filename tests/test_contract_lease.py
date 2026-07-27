from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.lease import (
    LEASE_EVIDENCE_SCHEMA_VERSION,
    LEASE_MAPPING_VERSION,
    LEASE_MODEL_VERSION,
    LeaseFactSet,
    ReviewedLeaseEvidence,
)
from causa.institutional.contracts.lease_evaluation import (
    SYNTHETIC_LEASE_BENCHMARKS,
    SYNTHETIC_LEASE_RED_TEAM_CASES,
    run_lease_benchmark_suite,
    run_lease_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_lease import (
    SyntheticLeaseEvaluationArtifact,
    build_synthetic_lease_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_lease_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.lease_evidence_mapping
    assert mapping.schema_version == LEASE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == LEASE_MAPPING_VERSION
    assert result.lease_constraint_set.model_version == LEASE_MODEL_VERSION
    evaluation = result.lease_evaluation
    # В демонстрационном деле спор о поставке товаров, а не об аренде.
    assert evaluation.lease_qualified is False
    assert evaluation.unauthorized_sublease is False
    assert evaluation.requires_human_lease_assessment is False


def test_lease_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.lease_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedLeaseEvidence(
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
            request.model_copy(update={"lease_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_lease_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.lease_evidence

    with pytest.raises(ValueError, match="Lease evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "lease_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Lease evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"lease_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "lease_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-lease-evidence",
                                "synthetic-ru-gk615-625-lease-use-repair-and-renewal-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_lease_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in LeaseFactSet.model_fields}
    values.update(tenant_seeks_renewal_with_priority=True, tenant_materially_breached=True)
    with pytest.raises(ValidationError, match="исключает преимущественное право"):
        LeaseFactSet(**values)

    values = {field_name: False for field_name in LeaseFactSet.model_fields}
    values.update(tenant_seeks_renewal_with_priority=True, lease_object_not_identifiable=True)
    with pytest.raises(ValidationError, match="Преимущественное право"):
        LeaseFactSet(**values)

    values = {field_name: False for field_name in LeaseFactSet.model_fields}
    values.update(inseparable_improvements_with_consent=True, lease_object_not_identifiable=True)
    with pytest.raises(ValidationError, match="неотделимых улучшений"):
        LeaseFactSet(**values)


def test_lease_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk606-614-lease-concept-object-and-rent-v1",
        "synthetic-ru-gk615-625-lease-use-repair-and-renewal-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_lease_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_lease_benchmark_suite()
    red_team = run_lease_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_LEASE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_LEASE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_lease_artifact_is_reproducible() -> None:
    fixture = SyntheticLeaseEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_lease_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_lease_evaluation_artifact()
