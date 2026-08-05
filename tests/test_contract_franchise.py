from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.franchise import (
    FRANCHISE_EVIDENCE_SCHEMA_VERSION,
    FRANCHISE_MAPPING_VERSION,
    FRANCHISE_MODEL_VERSION,
    FranchiseFactSet,
    ReviewedFranchiseEvidence,
)
from causa.institutional.contracts.franchise_evaluation import (
    SYNTHETIC_FRANCHISE_BENCHMARKS,
    SYNTHETIC_FRANCHISE_RED_TEAM_CASES,
    run_franchise_benchmark_suite,
    run_franchise_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_franchise import (
    SyntheticFranchiseEvaluationArtifact,
    build_synthetic_franchise_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_franchise_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.franchise_evidence_mapping
    assert mapping.schema_version == FRANCHISE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == FRANCHISE_MAPPING_VERSION
    assert result.franchise_constraint_set.model_version == FRANCHISE_MODEL_VERSION
    evaluation = result.franchise_evaluation
    # В демонстрационном деле комплекс исключительных прав не предоставлялся.
    assert evaluation.franchise_qualified is False
    assert evaluation.requires_human_franchise_assessment is False


def test_franchise_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.franchise_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedFranchiseEvidence(
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
            request.model_copy(update={"franchise_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_franchise_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.franchise_evidence

    with pytest.raises(ValueError, match="Franchise evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "franchise_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Franchise evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"franchise_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "franchise_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-franchise-evidence",
                                "synthetic-ru-gk1027-1029-franchise-concept-form-and-subconcession-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_franchise_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in FranchiseFactSet.model_fields}
    values.update(form_invalidity_not_applied=True)
    with pytest.raises(ValidationError, match="несоблюдения формы"):
        FranchiseFactSet(**values)

    scope = {field_name: False for field_name in FranchiseFactSet.model_fields}
    scope.update(franchise_scope_or_parties_breached=True)
    with pytest.raises(ValidationError, match="объёма предоставленных прав"):
        FranchiseFactSet(**scope)


def test_franchise_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1027-1029-franchise-concept-form-and-subconcession-v1",
        "synthetic-ru-gk1030-1040-franchise-obligations-restrictions-and-termination-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_franchise_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_franchise_benchmark_suite()
    red_team = run_franchise_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_FRANCHISE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_FRANCHISE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_franchise_artifact_is_reproducible() -> None:
    fixture = SyntheticFranchiseEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_franchise_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_franchise_evaluation_artifact()
