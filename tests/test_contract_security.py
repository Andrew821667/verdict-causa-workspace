from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.security import (
    SECURITY_EVIDENCE_SCHEMA_VERSION,
    SECURITY_MAPPING_VERSION,
    SECURITY_MODEL_VERSION,
    ReviewedSecurityEvidence,
    SecurityFactSet,
)
from causa.institutional.contracts.security_evaluation import (
    SYNTHETIC_SECURITY_BENCHMARKS,
    SYNTHETIC_SECURITY_RED_TEAM_CASES,
    run_security_benchmark_suite,
    run_security_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_security import (
    SyntheticSecurityEvaluationArtifact,
    build_synthetic_security_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_security_replays_after_obligation_breach() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert result.security_evidence_mapping.schema_version == SECURITY_EVIDENCE_SCHEMA_VERSION
    assert result.security_evidence_mapping.mapping_version == SECURITY_MAPPING_VERSION
    assert result.security_constraint_set.model_version == SECURITY_MODEL_VERSION
    assert result.security_evaluation.security_mechanism_detected is False
    assert result.security_evidence_mapping.facts.main_obligation_exists is True
    assert result.security_evidence_mapping.facts.main_obligation_breached is True


def test_security_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.security_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedSecurityEvidence(
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
            request.model_copy(update={"security_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_wrong_case_and_factual_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.security_evidence

    with pytest.raises(ValueError, match="Security evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "security_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Security evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"security_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "security_evidence": evidence.model_copy(
                        update={"legal_source_refs": ("synthetic-case-supply-1-security-evidence",)}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


@pytest.mark.parametrize(
    ("predicate", "message"),
    [
        ("main_obligation_exists", "main obligation status"),
        ("main_obligation_breached", "breach status"),
    ],
)
def test_analysis_rejects_security_status_mismatch(predicate: str, message: str) -> None:
    request = build_synthetic_supply_analysis_request()
    assertions = tuple(
        assertion.model_copy(update={"value": False})
        if assertion.predicate.value == predicate
        or (
            predicate == "main_obligation_exists"
            and assertion.predicate.value == "main_obligation_breached"
        )
        else assertion
        for assertion in request.security_evidence.assertions
    )
    evidence = request.security_evidence.model_copy(update={"assertions": assertions})

    with pytest.raises(ValueError, match=message):
        run_reviewed_contract_analysis(
            request.model_copy(update={"security_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_security_fact_consistency_rejects_breach_without_obligation() -> None:
    values = {field_name: False for field_name in SecurityFactSet.model_fields}
    values["main_obligation_breached"] = True
    with pytest.raises(ValidationError, match="must exist"):
        SecurityFactSet(**values)


def test_security_sources_have_official_basis_and_review_flag() -> None:
    source_ids = (
        "synthetic-ru-gk329-333-security-framework-v1",
        "synthetic-ru-gk334-360-pledge-retention-v1",
        "synthetic-ru-gk361-367-suretyship-v1",
        "synthetic-ru-gk368-379-independent-guarantee-v1",
        "synthetic-ru-gk380-3812-deposit-security-payment-v1",
        "synthetic-ru-plenum23-pledge-guidance-v1",
        "synthetic-ru-plenum45-suretyship-guidance-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_security_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_security_benchmark_suite()
    red_team = run_security_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_SECURITY_BENCHMARKS) == 16
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_SECURITY_RED_TEAM_CASES) == 16
    assert red_team.blocked == red_team.total


def test_exported_security_artifact_is_reproducible() -> None:
    fixture = SyntheticSecurityEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_security_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_security_evaluation_artifact()
