from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.barter import (
    BARTER_EVIDENCE_SCHEMA_VERSION,
    BARTER_MAPPING_VERSION,
    BARTER_MODEL_VERSION,
    BarterFactSet,
    ReviewedBarterEvidence,
)
from causa.institutional.contracts.barter_evaluation import (
    SYNTHETIC_BARTER_BENCHMARKS,
    SYNTHETIC_BARTER_RED_TEAM_CASES,
    run_barter_benchmark_suite,
    run_barter_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_barter import (
    SyntheticBarterEvaluationArtifact,
    build_synthetic_barter_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_barter_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.barter_evidence_mapping
    assert mapping.schema_version == BARTER_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == BARTER_MAPPING_VERSION
    assert result.barter_constraint_set.model_version == BARTER_MODEL_VERSION
    evaluation = result.barter_evaluation
    # В демонстрационном деле спор о возмездной поставке за деньги, а не о мене.
    assert evaluation.barter_qualified is False
    assert evaluation.price_difference_obligation is False
    assert evaluation.requires_human_barter_assessment is False


def test_barter_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.barter_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedBarterEvidence(
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
            request.model_copy(update={"barter_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_barter_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.barter_evidence

    with pytest.raises(ValueError, match="Barter evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "barter_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Barter evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"barter_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "barter_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-barter-evidence",
                                "synthetic-ru-gk569-571-barter-performance-and-eviction-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_barter_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in BarterFactSet.model_fields}
    values.update(goods_treated_as_equal_value=True, goods_unequal_value=True)
    with pytest.raises(ValidationError, match="равноценными и неравноценными"):
        BarterFactSet(**values)

    values = {field_name: False for field_name in BarterFactSet.model_fields}
    values.update(lower_price_party_paid_difference=True)
    with pytest.raises(ValidationError, match="только при неравноценности товаров"):
        BarterFactSet(**values)

    values = {field_name: False for field_name in BarterFactSet.model_fields}
    values.update(eviction_ground_arose_before_performance=True)
    with pytest.raises(ValidationError, match="только при фактическом изъятии товара"):
        BarterFactSet(**values)


def test_barter_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk567-568-barter-concept-and-price-v1",
        "synthetic-ru-gk569-571-barter-performance-and-eviction-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_barter_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_barter_benchmark_suite()
    red_team = run_barter_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_BARTER_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_BARTER_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_barter_artifact_is_reproducible() -> None:
    fixture = SyntheticBarterEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_barter_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_barter_evaluation_artifact()
