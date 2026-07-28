from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.leasing import (
    LEASING_EVIDENCE_SCHEMA_VERSION,
    LEASING_MAPPING_VERSION,
    LEASING_MODEL_VERSION,
    LeasingFactSet,
    ReviewedLeasingEvidence,
)
from causa.institutional.contracts.leasing_evaluation import (
    SYNTHETIC_LEASING_BENCHMARKS,
    SYNTHETIC_LEASING_RED_TEAM_CASES,
    run_leasing_benchmark_suite,
    run_leasing_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_leasing import (
    SyntheticLeasingEvaluationArtifact,
    build_synthetic_leasing_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_leasing_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.leasing_evidence_mapping
    assert mapping.schema_version == LEASING_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == LEASING_MAPPING_VERSION
    assert result.leasing_constraint_set.model_version == LEASING_MODEL_VERSION
    evaluation = result.leasing_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о финансовой аренде.
    assert evaluation.leasing_qualified is False
    assert evaluation.lessor_solidarily_liable_for_seller is False
    assert evaluation.requires_human_leasing_assessment is False


def test_leasing_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.leasing_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedLeasingEvidence(
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
            request.model_copy(update={"leasing_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_leasing_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.leasing_evidence

    with pytest.raises(ValueError, match="Leasing evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "leasing_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Leasing evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"leasing_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "leasing_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-leasing-evidence",
                                "synthetic-ru-gk668-670-leasing-delivery-risk-and-seller-claims-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_leasing_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in LeasingFactSet.model_fields}
    values.update(delay_attributable_to_lessor=True)
    with pytest.raises(ValidationError, match="непередачи предмета лизинга"):
        LeasingFactSet(**values)

    values = {field_name: False for field_name in LeasingFactSet.model_fields}
    values.update(
        leased_object_is_non_consumable_thing=True,
        object_excluded_from_leasing=True,
    )
    with pytest.raises(ValidationError, match="изъятым из круга предметов лизинга"):
        LeasingFactSet(**values)


def test_leasing_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk665-667-leasing-concept-object-and-notice-v1",
        "synthetic-ru-gk668-670-leasing-delivery-risk-and-seller-claims-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_leasing_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_leasing_benchmark_suite()
    red_team = run_leasing_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_LEASING_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_LEASING_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_leasing_artifact_is_reproducible() -> None:
    fixture = SyntheticLeasingEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_leasing_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_leasing_evaluation_artifact()
