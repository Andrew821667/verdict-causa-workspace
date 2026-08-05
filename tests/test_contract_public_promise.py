from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.public_promise import (
    PUBLIC_PROMISE_EVIDENCE_SCHEMA_VERSION,
    PUBLIC_PROMISE_MAPPING_VERSION,
    PUBLIC_PROMISE_MODEL_VERSION,
    PublicPromiseFactSet,
    ReviewedPublicPromiseEvidence,
)
from causa.institutional.contracts.public_promise_evaluation import (
    SYNTHETIC_PUBLIC_PROMISE_BENCHMARKS,
    SYNTHETIC_PUBLIC_PROMISE_RED_TEAM_CASES,
    run_public_promise_benchmark_suite,
    run_public_promise_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_public_promise import (
    SyntheticPublicPromiseEvaluationArtifact,
    build_synthetic_public_promise_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_public_promise_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.public_promise_evidence_mapping
    assert mapping.schema_version == PUBLIC_PROMISE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == PUBLIC_PROMISE_MAPPING_VERSION
    assert result.public_promise_constraint_set.model_version == PUBLIC_PROMISE_MODEL_VERSION
    evaluation = result.public_promise_evaluation
    # В демонстрационном деле публичное обещание награды не объявлялось.
    assert evaluation.public_promise_qualified is False
    assert evaluation.requires_human_public_promise_assessment is False


def test_public_promise_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.public_promise_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedPublicPromiseEvidence(
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
            request.model_copy(update={"public_promise_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_public_promise_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.public_promise_evidence

    with pytest.raises(ValueError, match="Public-promise evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "public_promise_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Public-promise evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"public_promise_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "public_promise_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-public-promise-evidence",
                                "synthetic-ru-gk1057-1061-public-contest-terms-award-and-works-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_public_promise_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in PublicPromiseFactSet.model_fields}
    values.update(revocation_expense_compensation_not_applied=True)
    with pytest.raises(ValidationError, match="отмене публичного обещания награды"):
        PublicPromiseFactSet(**values)

    scope = {field_name: False for field_name in PublicPromiseFactSet.model_fields}
    scope.update(promise_announcement_requirements_breached=True)
    with pytest.raises(ValidationError, match="требований к объявлению"):
        PublicPromiseFactSet(**scope)


def test_public_promise_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1055-1056-public-promise-of-reward-and-revocation-v1",
        "synthetic-ru-gk1057-1061-public-contest-terms-award-and-works-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_public_promise_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_public_promise_benchmark_suite()
    red_team = run_public_promise_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_PUBLIC_PROMISE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_PUBLIC_PROMISE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_public_promise_artifact_is_reproducible() -> None:
    fixture = SyntheticPublicPromiseEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_public_promise_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_public_promise_evaluation_artifact()
