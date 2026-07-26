from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.gift import (
    GIFT_EVIDENCE_SCHEMA_VERSION,
    GIFT_MAPPING_VERSION,
    GIFT_MODEL_VERSION,
    GiftFactSet,
    ReviewedGiftEvidence,
)
from causa.institutional.contracts.gift_evaluation import (
    SYNTHETIC_GIFT_BENCHMARKS,
    SYNTHETIC_GIFT_RED_TEAM_CASES,
    run_gift_benchmark_suite,
    run_gift_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_gift import (
    SyntheticGiftEvaluationArtifact,
    build_synthetic_gift_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_gift_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.gift_evidence_mapping
    assert mapping.schema_version == GIFT_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == GIFT_MAPPING_VERSION
    assert result.gift_constraint_set.model_version == GIFT_MODEL_VERSION
    evaluation = result.gift_evaluation
    # В демонстрационном деле спор о возмездной поставке, а не о безвозмездном дарении.
    assert evaluation.gift_qualified is False
    assert evaluation.donation_prohibited is False
    assert evaluation.requires_human_gift_assessment is False


def test_gift_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.gift_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedGiftEvidence(
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
            request.model_copy(update={"gift_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_gift_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.gift_evidence

    with pytest.raises(ValueError, match="Gift evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "gift_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Gift evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"gift_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "gift_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-gift-evidence",
                                "synthetic-ru-gk573-582-gift-refusal-revocation-and-donation-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_gift_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in GiftFactSet.model_fields}
    values.update(charitable_donation_purpose_violated=True)
    with pytest.raises(ValidationError, match="только при безвозмездной передаче"):
        GiftFactSet(**values)

    values = {field_name: False for field_name in GiftFactSet.model_fields}
    values.update(donee_refused_before_delivery=True)
    with pytest.raises(ValidationError, match="Отказ одаряемого от дара"):
        GiftFactSet(**values)


def test_gift_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk572-576-gift-concept-and-form-v1",
        "synthetic-ru-gk573-582-gift-refusal-revocation-and-donation-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_gift_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_gift_benchmark_suite()
    red_team = run_gift_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_GIFT_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_GIFT_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_gift_artifact_is_reproducible() -> None:
    fixture = SyntheticGiftEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_gift_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_gift_evaluation_artifact()
