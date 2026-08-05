from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source
from causa.institutional.contracts.synthetic_trust_management import (
    SyntheticTrustManagementEvaluationArtifact,
    build_synthetic_trust_management_evaluation_artifact,
)
from causa.institutional.contracts.trust_management import (
    TRUST_MANAGEMENT_EVIDENCE_SCHEMA_VERSION,
    TRUST_MANAGEMENT_MAPPING_VERSION,
    TRUST_MANAGEMENT_MODEL_VERSION,
    ReviewedTrustManagementEvidence,
    TrustManagementFactSet,
)
from causa.institutional.contracts.trust_management_evaluation import (
    SYNTHETIC_TRUST_MANAGEMENT_BENCHMARKS,
    SYNTHETIC_TRUST_MANAGEMENT_RED_TEAM_CASES,
    run_trust_management_benchmark_suite,
    run_trust_management_red_team_suite,
)


def test_reviewed_trust_management_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.trust_management_evidence_mapping
    assert mapping.schema_version == TRUST_MANAGEMENT_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == TRUST_MANAGEMENT_MAPPING_VERSION
    assert result.trust_management_constraint_set.model_version == TRUST_MANAGEMENT_MODEL_VERSION
    evaluation = result.trust_management_evaluation
    # В демонстрационном деле имущество в доверительное управление не передавалось.
    assert evaluation.trust_management_qualified is False
    assert evaluation.requires_human_trust_management_assessment is False


def test_trust_management_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.trust_management_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedTrustManagementEvidence(
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
            request.model_copy(update={"trust_management_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_trust_management_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.trust_management_evidence

    with pytest.raises(ValueError, match="Trust-management evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "trust_management_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Trust-management evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "trust_management_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "trust_management_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-trust-management-evidence",
                                "synthetic-ru-gk1012-1019-trust-management-concept-terms-and-property-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_trust_management_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in TrustManagementFactSet.model_fields}
    values.update(form_invalidity_not_applied=True)
    with pytest.raises(ValidationError, match="несоблюдения формы"):
        TrustManagementFactSet(**values)

    scope = {field_name: False for field_name in TrustManagementFactSet.model_fields}
    scope.update(trust_property_scope_breached=True)
    with pytest.raises(ValidationError, match="объекта доверительного управления"):
        TrustManagementFactSet(**scope)


def test_trust_management_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1012-1019-trust-management-concept-terms-and-property-v1",
        "synthetic-ru-gk1020-1026-trust-management-duties-liability-and-termination-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_trust_management_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_trust_management_benchmark_suite()
    red_team = run_trust_management_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_TRUST_MANAGEMENT_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_TRUST_MANAGEMENT_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_trust_management_artifact_is_reproducible() -> None:
    fixture = SyntheticTrustManagementEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_trust_management_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_trust_management_evaluation_artifact()
