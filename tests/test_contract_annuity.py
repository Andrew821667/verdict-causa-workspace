from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.annuity import (
    ANNUITY_EVIDENCE_SCHEMA_VERSION,
    ANNUITY_MAPPING_VERSION,
    ANNUITY_MODEL_VERSION,
    AnnuityFactSet,
    ReviewedAnnuityEvidence,
)
from causa.institutional.contracts.annuity_evaluation import (
    SYNTHETIC_ANNUITY_BENCHMARKS,
    SYNTHETIC_ANNUITY_RED_TEAM_CASES,
    run_annuity_benchmark_suite,
    run_annuity_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_annuity import (
    SyntheticAnnuityEvaluationArtifact,
    build_synthetic_annuity_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_annuity_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.annuity_evidence_mapping
    assert mapping.schema_version == ANNUITY_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == ANNUITY_MAPPING_VERSION
    assert result.annuity_constraint_set.model_version == ANNUITY_MODEL_VERSION
    evaluation = result.annuity_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о ренте.
    assert evaluation.annuity_qualified is False
    assert evaluation.overdue_interest_due is False
    assert evaluation.requires_human_annuity_assessment is False


def test_annuity_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.annuity_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedAnnuityEvidence(
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
            request.model_copy(update={"annuity_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_annuity_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.annuity_evidence

    with pytest.raises(ValueError, match="Annuity evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "annuity_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Annuity evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"annuity_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "annuity_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-annuity-evidence",
                                "synthetic-ru-gk596-605-annuity-life-and-maintenance-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_annuity_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in AnnuityFactSet.model_fields}
    values.update(permanent_rent=True, life_annuity_or_maintenance=True)
    with pytest.raises(ValidationError, match="постоянной и пожизненной"):
        AnnuityFactSet(**values)

    values = {field_name: False for field_name in AnnuityFactSet.model_fields}
    values.update(payer_waived_redemption_right=True)
    with pytest.raises(ValidationError, match="только к постоянной ренте"):
        AnnuityFactSet(**values)

    values = {field_name: False for field_name in AnnuityFactSet.model_fields}
    values.update(maintenance_property_encumbered_without_consent=True)
    with pytest.raises(ValidationError, match="только к пожизненному содержанию"):
        AnnuityFactSet(**values)


def test_annuity_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk583-593-annuity-general-and-permanent-v1",
        "synthetic-ru-gk596-605-annuity-life-and-maintenance-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_annuity_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_annuity_benchmark_suite()
    red_team = run_annuity_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_ANNUITY_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_ANNUITY_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_annuity_artifact_is_reproducible() -> None:
    fixture = SyntheticAnnuityEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_annuity_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_annuity_evaluation_artifact()
