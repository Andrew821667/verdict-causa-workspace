from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.enterprise_sale import (
    ENTERPRISE_SALE_EVIDENCE_SCHEMA_VERSION,
    ENTERPRISE_SALE_MAPPING_VERSION,
    ENTERPRISE_SALE_MODEL_VERSION,
    EnterpriseSaleFactSet,
    ReviewedEnterpriseSaleEvidence,
)
from causa.institutional.contracts.enterprise_sale_evaluation import (
    SYNTHETIC_ENTERPRISE_SALE_BENCHMARKS,
    SYNTHETIC_ENTERPRISE_SALE_RED_TEAM_CASES,
    run_enterprise_sale_benchmark_suite,
    run_enterprise_sale_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_enterprise_sale import (
    SyntheticEnterpriseSaleEvaluationArtifact,
    build_synthetic_enterprise_sale_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_enterprise_sale_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.enterprise_sale_evidence_mapping
    assert mapping.schema_version == ENTERPRISE_SALE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == ENTERPRISE_SALE_MAPPING_VERSION
    assert result.enterprise_sale_constraint_set.model_version == ENTERPRISE_SALE_MODEL_VERSION
    evaluation = result.enterprise_sale_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о продаже предприятия.
    assert evaluation.enterprise_sale_qualified is False
    assert evaluation.joint_liability_for_unconsented_debt is False
    assert evaluation.requires_human_enterprise_sale_assessment is False


def test_enterprise_sale_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.enterprise_sale_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedEnterpriseSaleEvidence(
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
            request.model_copy(update={"enterprise_sale_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_enterprise_sale_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.enterprise_sale_evidence

    with pytest.raises(ValueError, match="Enterprise sale evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "enterprise_sale_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Enterprise sale evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "enterprise_sale_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "enterprise_sale_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-enterprise-sale-evidence",
                                "synthetic-ru-gk562-566-enterprise-sale-creditors-and-transfer-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_enterprise_sale_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in EnterpriseSaleFactSet.model_fields}
    values.update(sale_contract_registered=True)
    with pytest.raises(ValidationError, match="без письменной формы с обязательными приложениями"):
        EnterpriseSaleFactSet(**values)


def test_enterprise_sale_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk559-561-enterprise-sale-concept-v1",
        "synthetic-ru-gk562-566-enterprise-sale-creditors-and-transfer-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_enterprise_sale_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_enterprise_sale_benchmark_suite()
    red_team = run_enterprise_sale_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_ENTERPRISE_SALE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_ENTERPRISE_SALE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_enterprise_sale_artifact_is_reproducible() -> None:
    fixture = SyntheticEnterpriseSaleEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_enterprise_sale_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_enterprise_sale_evaluation_artifact()
