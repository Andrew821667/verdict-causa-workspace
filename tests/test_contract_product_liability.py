from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.product_liability import (
    PRODUCT_LIABILITY_EVIDENCE_SCHEMA_VERSION,
    PRODUCT_LIABILITY_MAPPING_VERSION,
    PRODUCT_LIABILITY_MODEL_VERSION,
    ProductLiabilityFactSet,
    ReviewedProductLiabilityEvidence,
)
from causa.institutional.contracts.product_liability_evaluation import (
    SYNTHETIC_PRODUCT_LIABILITY_BENCHMARKS,
    SYNTHETIC_PRODUCT_LIABILITY_RED_TEAM_CASES,
    run_product_liability_benchmark_suite,
    run_product_liability_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_product_liability import (
    SyntheticProductLiabilityEvaluationArtifact,
    build_synthetic_product_liability_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_product_liability_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.product_liability_evidence_mapping
    assert mapping.schema_version == PRODUCT_LIABILITY_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == PRODUCT_LIABILITY_MAPPING_VERSION
    assert result.product_liability_constraint_set.model_version == PRODUCT_LIABILITY_MODEL_VERSION
    evaluation = result.product_liability_evaluation
    # В демонстрационном деле вред вследствие недостатков товара не причинялся.
    assert evaluation.product_liability_qualified is False
    assert evaluation.requires_human_product_liability_assessment is False


def test_product_liability_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.product_liability_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedProductLiabilityEvidence(
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
            request.model_copy(update={"product_liability_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_product_liability_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.product_liability_evidence

    with pytest.raises(ValueError, match="Product-liability evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "product_liability_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Product-liability evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "product_liability_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "product_liability_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-product-liability-evidence",
                                "synthetic-ru-gk1095-1096-product-defect-harm-and-liable-persons-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_product_liability_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in ProductLiabilityFactSet.model_fields}
    values.update(victim_rules_violation_not_applied=True)
    with pytest.raises(ValidationError, match="освобождения от ответственности"):
        ProductLiabilityFactSet(**values)

    scope = {field_name: False for field_name in ProductLiabilityFactSet.model_fields}
    scope.update(compensation_regardless_of_fault_breached=True)
    with pytest.raises(ValidationError, match="возмещении вреда независимо от вины"):
        ProductLiabilityFactSet(**scope)


def test_product_liability_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1095-1096-product-defect-harm-and-liable-persons-v1",
        "synthetic-ru-gk1097-1098-product-liability-periods-and-exculpation-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_product_liability_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_product_liability_benchmark_suite()
    red_team = run_product_liability_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_PRODUCT_LIABILITY_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_PRODUCT_LIABILITY_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_product_liability_artifact_is_reproducible() -> None:
    fixture = SyntheticProductLiabilityEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_product_liability_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_product_liability_evaluation_artifact()
