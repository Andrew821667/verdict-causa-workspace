from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.enterprise_lease import (
    ENTERPRISE_LEASE_EVIDENCE_SCHEMA_VERSION,
    ENTERPRISE_LEASE_MAPPING_VERSION,
    ENTERPRISE_LEASE_MODEL_VERSION,
    EnterpriseLeaseFactSet,
    ReviewedEnterpriseLeaseEvidence,
)
from causa.institutional.contracts.enterprise_lease_evaluation import (
    SYNTHETIC_ENTERPRISE_LEASE_BENCHMARKS,
    SYNTHETIC_ENTERPRISE_LEASE_RED_TEAM_CASES,
    run_enterprise_lease_benchmark_suite,
    run_enterprise_lease_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_enterprise_lease import (
    SyntheticEnterpriseLeaseEvaluationArtifact,
    build_synthetic_enterprise_lease_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_enterprise_lease_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.enterprise_lease_evidence_mapping
    assert mapping.schema_version == ENTERPRISE_LEASE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == ENTERPRISE_LEASE_MAPPING_VERSION
    assert result.enterprise_lease_constraint_set.model_version == ENTERPRISE_LEASE_MODEL_VERSION
    evaluation = result.enterprise_lease_evaluation
    # В демонстрационном деле спор о поставке товаров, а не об аренде предприятия.
    assert evaluation.enterprise_lease_qualified is False
    assert evaluation.creditor_notice_not_given is False
    assert evaluation.requires_human_enterprise_lease_assessment is False


def test_enterprise_lease_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.enterprise_lease_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedEnterpriseLeaseEvidence(
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
            request.model_copy(update={"enterprise_lease_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_enterprise_lease_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.enterprise_lease_evidence

    with pytest.raises(ValueError, match="Enterprise-lease evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "enterprise_lease_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Enterprise-lease evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "enterprise_lease_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "enterprise_lease_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-enterprise-lease-evidence",
                                "synthetic-ru-gk660-664-enterprise-lease-use-maintenance-and-return-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_enterprise_lease_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in EnterpriseLeaseFactSet.model_fields}
    values.update(debt_transferred_without_creditor_consent=True)
    with pytest.raises(ValidationError, match="как имущественного комплекса"):
        EnterpriseLeaseFactSet(**values)


def test_enterprise_lease_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk656-659-enterprise-lease-concept-form-and-creditors-v1",
        "synthetic-ru-gk660-664-enterprise-lease-use-maintenance-and-return-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_enterprise_lease_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_enterprise_lease_benchmark_suite()
    red_team = run_enterprise_lease_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_ENTERPRISE_LEASE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_ENTERPRISE_LEASE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_enterprise_lease_artifact_is_reproducible() -> None:
    fixture = SyntheticEnterpriseLeaseEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_enterprise_lease_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_enterprise_lease_evaluation_artifact()
