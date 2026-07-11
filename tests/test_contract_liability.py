from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.liability import (
    LiabilityEvidencePredicate,
    LiabilityFactSet,
    ReviewedLiabilityEvidence,
)
from causa.institutional.contracts.liability_evaluation import (
    SYNTHETIC_LIABILITY_BENCHMARKS,
    SYNTHETIC_LIABILITY_RED_TEAM_CASES,
    SyntheticLiabilityEvaluationArtifact,
    run_liability_benchmark_suite,
    run_liability_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_liability import (
    build_synthetic_liability_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_liability_evidence_maps_every_fact_with_provenance() -> None:
    result = build_synthetic_supply_analysis_artifact().result
    mapping = result.liability_evidence_mapping

    assert len(mapping.provenance) == len(LiabilityEvidencePredicate) == 20
    assert {item.fact_name for item in mapping.provenance} == {
        predicate.value for predicate in LiabilityEvidencePredicate
    }
    assert len(mapping.legal_source_refs) == 3
    assert all(item.source_refs for item in mapping.provenance)
    assert result.liability_evaluation.liability_issue is True
    assert result.liability_evaluation.force_majeure_qualified is False
    assert result.liability_evaluation.requires_judicial_assessment is True


def test_liability_evidence_rejects_duplicates_and_incomplete_input() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.liability_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedLiabilityEvidence(
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
            request.model_copy(update={"liability_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_liability_facts_reject_reduction_request_without_claimed_penalty() -> None:
    payload = {
        field_name: False for field_name in LiabilityFactSet.model_fields
    }
    payload.update(
        {
            "breach_established": True,
            "penalty_reduction_requested": True,
        }
    )

    with pytest.raises(ValidationError, match="without a claimed penalty"):
        LiabilityFactSet.model_validate(payload)

def test_analysis_rejects_unreviewed_or_mismatched_liability_evidence() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.liability_evidence
    unreviewed = evidence.model_copy(update={"review_status": BootstrapReviewStatus.DRAFT})
    wrong_case = evidence.model_copy(update={"case_id": "other-case"})

    with pytest.raises(ValueError, match="Liability evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"liability_evidence": unreviewed}),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Liability evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"liability_evidence": wrong_case}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unknown_liability_source_reference() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.liability_evidence.model_copy(
        update={"legal_source_refs": ("missing-liability-source",)}
    )

    with pytest.raises(ValueError, match="missing-liability-source"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"liability_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unsupported_liability_schema() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.liability_evidence.model_copy(
        update={"schema_version": "contracts.liability-evidence.v999"}
    )

    with pytest.raises(ValueError, match="Liability evidence uses an unsupported"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"liability_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_factual_source_as_liability_legal_model() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.liability_evidence.model_copy(
        update={
            "legal_source_refs": (
                "synthetic-case-supply-1-liability-evidence",
            )
        }
    )

    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"liability_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_liability_breach_fact_that_conflicts_with_obligation_model() -> None:
    request = build_synthetic_supply_analysis_request()
    assertions = tuple(
        assertion.model_copy(update={"value": False})
        if assertion.predicate
        in {
            LiabilityEvidencePredicate.BREACH_ESTABLISHED,
            LiabilityEvidencePredicate.PENALTY_CLAIMED,
            LiabilityEvidencePredicate.PENALTY_REDUCTION_REQUESTED,
        }
        else assertion
        for assertion in request.liability_evidence.assertions
    )
    evidence = request.liability_evidence.model_copy(update={"assertions": assertions})

    with pytest.raises(ValueError, match="does not match obligation evaluation"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"liability_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_liability_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk401-liability-model-v1",
        "synthetic-ru-gk333-penalty-model-v1",
        "synthetic-ru-plenum7-liability-guidance-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)
    assert {source.metadata["topic"] for source in sources} == {
        "liability_article_401",
        "penalty_article_333",
        "liability_plenum_guidance",
    }


def test_liability_benchmark_suite_covers_formal_boundaries() -> None:
    report = run_liability_benchmark_suite()

    assert report.total == len(SYNTHETIC_LIABILITY_BENCHMARKS) == 10
    assert report.passed == report.total
    assert report.failed == 0
    assert all(result.reasons_ru for result in report.results)


def test_liability_red_team_blocks_overreach() -> None:
    report = run_liability_red_team_suite()

    assert report.total == len(SYNTHETIC_LIABILITY_RED_TEAM_CASES) == 10
    assert report.blocked == report.total
    assert report.unblocked == 0
    assert all(result.reasons_ru for result in report.results)


def test_liability_model_keeps_penalty_reduction_judicial_and_liability_intact() -> None:
    artifact = build_synthetic_liability_evaluation_artifact()
    business_penalty = next(
        result
        for result in artifact.benchmark_report.results
        if result.task_id == "liability-bench-business-contractual-penalty"
    )

    assert business_penalty.observed_outcomes == {
        "penalty_reduction_prerequisites_satisfied": True,
        "liability_survives_penalty_reduction": True,
        "requires_judicial_assessment": True,
    }


def test_exported_liability_artifact_is_valid_and_reproducible() -> None:
    fixture_path = Path("examples/synthetic_liability_evaluation_report.json")
    fixture = SyntheticLiabilityEvaluationArtifact.model_validate_json(
        fixture_path.read_text(encoding="utf-8")
    )

    assert fixture == build_synthetic_liability_evaluation_artifact()
    assert fixture.benchmark_report.failed == 0
    assert fixture.red_team_report.unblocked == 0


def test_liability_artifact_rejects_tampered_evaluation() -> None:
    artifact = build_synthetic_liability_evaluation_artifact()
    payload = artifact.model_dump(mode="json")
    payload["reviewed_evaluation"]["liability_issue"] = False

    with pytest.raises(ValidationError, match="evaluation is not reproducible"):
        SyntheticLiabilityEvaluationArtifact.model_validate(payload)
