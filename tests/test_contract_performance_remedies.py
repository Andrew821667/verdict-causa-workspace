from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.performance_remedies import (
    PERFORMANCE_REMEDIES_EVIDENCE_SCHEMA_VERSION,
    PERFORMANCE_REMEDIES_MAPPING_VERSION,
    PERFORMANCE_REMEDIES_MODEL_VERSION,
    PerformanceRemediesFactSet,
    ReviewedPerformanceRemediesEvidence,
)
from causa.institutional.contracts.performance_remedies_evaluation import (
    SYNTHETIC_PERFORMANCE_REMEDIES_BENCHMARKS,
    SYNTHETIC_PERFORMANCE_REMEDIES_RED_TEAM_CASES,
    run_performance_remedies_benchmark_suite,
    run_performance_remedies_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_performance_remedies import (
    SyntheticPerformanceRemediesEvaluationArtifact,
    build_synthetic_performance_remedies_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_performance_remedies_replay_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert (
        result.performance_remedies_evidence_mapping.schema_version
        == PERFORMANCE_REMEDIES_EVIDENCE_SCHEMA_VERSION
    )
    assert (
        result.performance_remedies_evidence_mapping.mapping_version
        == PERFORMANCE_REMEDIES_MAPPING_VERSION
    )
    assert (
        result.performance_remedies_constraint_set.model_version
        == PERFORMANCE_REMEDIES_MODEL_VERSION
    )
    assert result.performance_remedies_evaluation.debtor_in_delay is True
    assert result.performance_remedies_evaluation.proper_performance is False


def test_performance_remedies_reject_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.performance_remedies_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedPerformanceRemediesEvidence(
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
            request.model_copy(update={"performance_remedies_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_wrong_case_and_factual_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.performance_remedies_evidence

    with pytest.raises(ValueError, match="Performance-remedies evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "performance_remedies_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Performance-remedies evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "performance_remedies_evidence": evidence.model_copy(
                        update={"case_id": "other"}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "performance_remedies_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-performance-remedies-evidence",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


@pytest.mark.parametrize(
    ("predicate", "message"),
    [
        ("obligation_exists", "obligation status"),
        ("breach_established", "breach status"),
        ("performance_tendered", "tender status"),
        ("loss_claimed", "loss claim"),
        ("causation_proven", "causation"),
        ("monetary_delay", "monetary-delay status"),
    ],
)
def test_analysis_rejects_performance_remedies_status_mismatch(
    predicate: str,
    message: str,
) -> None:
    request = build_synthetic_supply_analysis_request()
    target_value = predicate in {"loss_claimed", "causation_proven", "monetary_delay"}
    assertions = tuple(
        assertion.model_copy(update={"value": target_value})
        if assertion.predicate.value == predicate
        or (
            predicate == "obligation_exists"
            and assertion.predicate.value in {"breach_established", "performance_tendered"}
        )
        else assertion
        for assertion in request.performance_remedies_evidence.assertions
    )
    evidence = request.performance_remedies_evidence.model_copy(update={"assertions": assertions})

    with pytest.raises(ValueError, match=message):
        run_reviewed_contract_analysis(
            request.model_copy(update={"performance_remedies_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_performance_remedies_fact_consistency_rejects_breach_without_obligation() -> None:
    values = {field_name: False for field_name in PerformanceRemediesFactSet.model_fields}
    values["breach_established"] = True
    with pytest.raises(ValidationError, match="existing obligation"):
        PerformanceRemediesFactSet(**values)


def test_performance_remedies_sources_have_official_basis_and_review_flag() -> None:
    source_ids = (
        "synthetic-ru-gk309-328-performance-v1",
        "synthetic-ru-gk393-4061-remedies-v1",
        "synthetic-ru-plenum54-performance-guidance-v1",
        "synthetic-ru-plenum7-remedies-guidance-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_performance_remedies_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_performance_remedies_benchmark_suite()
    red_team = run_performance_remedies_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_PERFORMANCE_REMEDIES_BENCHMARKS) == 27
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_PERFORMANCE_REMEDIES_RED_TEAM_CASES) == 30
    assert red_team.blocked == red_team.total


def test_exported_performance_remedies_artifact_is_reproducible() -> None:
    fixture = SyntheticPerformanceRemediesEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_performance_remedies_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_performance_remedies_evaluation_artifact()
