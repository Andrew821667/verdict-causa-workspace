from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.real_estate_sale import (
    REAL_ESTATE_SALE_EVIDENCE_SCHEMA_VERSION,
    REAL_ESTATE_SALE_MAPPING_VERSION,
    REAL_ESTATE_SALE_MODEL_VERSION,
    RealEstateSaleFactSet,
    ReviewedRealEstateSaleEvidence,
)
from causa.institutional.contracts.real_estate_sale_evaluation import (
    SYNTHETIC_REAL_ESTATE_SALE_BENCHMARKS,
    SYNTHETIC_REAL_ESTATE_SALE_RED_TEAM_CASES,
    run_real_estate_sale_benchmark_suite,
    run_real_estate_sale_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_real_estate_sale import (
    SyntheticRealEstateSaleEvaluationArtifact,
    build_synthetic_real_estate_sale_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_real_estate_sale_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.real_estate_sale_evidence_mapping
    assert mapping.schema_version == REAL_ESTATE_SALE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == REAL_ESTATE_SALE_MAPPING_VERSION
    assert result.real_estate_sale_constraint_set.model_version == REAL_ESTATE_SALE_MODEL_VERSION
    evaluation = result.real_estate_sale_evaluation
    # В демонстрационном деле спор о поставке движимых товаров, а не о недвижимости.
    assert evaluation.real_estate_sale_qualified is False
    assert evaluation.contract_concluded is False
    assert evaluation.requires_human_real_estate_sale_assessment is False


def test_real_estate_sale_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.real_estate_sale_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedRealEstateSaleEvidence(
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
            request.model_copy(update={"real_estate_sale_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_real_estate_sale_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.real_estate_sale_evidence

    with pytest.raises(ValueError, match="Real estate sale evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "real_estate_sale_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Real estate sale evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "real_estate_sale_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "real_estate_sale_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-real-estate-sale-evidence",
                                "synthetic-ru-gk554-558-real-estate-sale-terms-and-transfer-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_real_estate_sale_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in RealEstateSaleFactSet.model_fields}
    values.update(occupant_rights_list_included=True)
    with pytest.raises(ValidationError, match="только при продаже жилого помещения"):
        RealEstateSaleFactSet(**values)

    values = {field_name: False for field_name in RealEstateSaleFactSet.model_fields}
    values.update(party_evaded_transfer_deed=True, property_handed_over_by_deed=True)
    with pytest.raises(ValidationError, match="уклонение от подписания акта несовместимы"):
        RealEstateSaleFactSet(**values)


def test_real_estate_sale_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk549-552-real-estate-sale-concept-v1",
        "synthetic-ru-gk554-558-real-estate-sale-terms-and-transfer-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_real_estate_sale_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_real_estate_sale_benchmark_suite()
    red_team = run_real_estate_sale_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_REAL_ESTATE_SALE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_REAL_ESTATE_SALE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_real_estate_sale_artifact_is_reproducible() -> None:
    fixture = SyntheticRealEstateSaleEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_real_estate_sale_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_real_estate_sale_evaluation_artifact()
