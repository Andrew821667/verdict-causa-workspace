from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.retail_sale import (
    RETAIL_SALE_EVIDENCE_SCHEMA_VERSION,
    RETAIL_SALE_MAPPING_VERSION,
    RETAIL_SALE_MODEL_VERSION,
    RetailSaleFactSet,
    ReviewedRetailSaleEvidence,
)
from causa.institutional.contracts.retail_sale_evaluation import (
    SYNTHETIC_RETAIL_SALE_BENCHMARKS,
    SYNTHETIC_RETAIL_SALE_RED_TEAM_CASES,
    run_retail_sale_benchmark_suite,
    run_retail_sale_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_retail_sale import (
    SyntheticRetailSaleEvaluationArtifact,
    build_synthetic_retail_sale_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_retail_sale_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.retail_sale_evidence_mapping
    assert mapping.schema_version == RETAIL_SALE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == RETAIL_SALE_MAPPING_VERSION
    assert result.retail_sale_constraint_set.model_version == RETAIL_SALE_MODEL_VERSION
    evaluation = result.retail_sale_evaluation
    # В демонстрационном деле спор является оптовой поставкой, не розницей.
    assert evaluation.retail_contract_is_public is False
    assert evaluation.quality_remedy_available is False
    assert evaluation.requires_human_retail_sale_assessment is False


def test_retail_sale_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.retail_sale_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedRetailSaleEvidence(
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
            request.model_copy(update={"retail_sale_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_retail_sale_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.retail_sale_evidence

    with pytest.raises(ValueError, match="Retail sale evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "retail_sale_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Retail sale evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"retail_sale_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "retail_sale_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-retail-sale-evidence",
                                "synthetic-ru-gk502-504-retail-exchange-and-quality-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_retail_sale_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in RetailSaleFactSet.model_fields}
    values.update(receipt_or_confirmation_issued=True)
    with pytest.raises(ValidationError, match="без розничной купли-продажи"):
        RetailSaleFactSet(**values)


def test_retail_sale_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk492-495-retail-sale-concept-v1",
        "synthetic-ru-gk502-504-retail-exchange-and-quality-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_retail_sale_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_retail_sale_benchmark_suite()
    red_team = run_retail_sale_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_RETAIL_SALE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_RETAIL_SALE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_retail_sale_artifact_is_reproducible() -> None:
    fixture = SyntheticRetailSaleEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_retail_sale_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_retail_sale_evaluation_artifact()
