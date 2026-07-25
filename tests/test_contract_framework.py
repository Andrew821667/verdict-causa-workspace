from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.framework import (
    FRAMEWORK_EVIDENCE_SCHEMA_VERSION,
    FRAMEWORK_MAPPING_VERSION,
    FRAMEWORK_MODEL_VERSION,
    FrameworkFactSet,
    ReviewedFrameworkEvidence,
)
from causa.institutional.contracts.framework_evaluation import (
    SYNTHETIC_FRAMEWORK_BENCHMARKS,
    SYNTHETIC_FRAMEWORK_RED_TEAM_CASES,
    run_framework_benchmark_suite,
    run_framework_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_framework import (
    SyntheticFrameworkEvaluationArtifact,
    build_synthetic_framework_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_framework_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.framework_evidence_mapping
    assert mapping.schema_version == FRAMEWORK_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == FRAMEWORK_MAPPING_VERSION
    assert result.framework_constraint_set.model_version == FRAMEWORK_MODEL_VERSION
    evaluation = result.framework_evaluation
    # В демонстрационном деле рамочный договор конкретизирован отдельными заявками.
    assert evaluation.framework_agreement_valid is True
    assert evaluation.framework_terms_apply_to_relations is True
    assert evaluation.specifying_agreement_on_framework is True
    assert evaluation.requires_human_framework_assessment is False


def test_framework_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.framework_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedFrameworkEvidence(
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
            request.model_copy(update={"framework_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_framework_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.framework_evidence

    with pytest.raises(ValueError, match="Framework evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "framework_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Framework evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"framework_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "framework_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-framework-evidence",
                                "synthetic-ru-gk429-4-subscription-agreement-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_framework_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in FrameworkFactSet.model_fields}
    values.update(specifying_agreement_concluded=True)
    with pytest.raises(ValidationError, match="без рамочного договора"):
        FrameworkFactSet(**values)


def test_framework_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk429-1-framework-agreement-v1",
        "synthetic-ru-gk429-4-subscription-agreement-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_framework_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_framework_benchmark_suite()
    red_team = run_framework_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_FRAMEWORK_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_FRAMEWORK_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_framework_artifact_is_reproducible() -> None:
    fixture = SyntheticFrameworkEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_framework_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_framework_evaluation_artifact()
