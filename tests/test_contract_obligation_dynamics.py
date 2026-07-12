from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.obligation_dynamics import (
    OBLIGATION_DYNAMICS_EVIDENCE_SCHEMA_VERSION,
    OBLIGATION_DYNAMICS_MAPPING_VERSION,
    OBLIGATION_DYNAMICS_MODEL_VERSION,
    ObligationDynamicsFactSet,
    ReviewedObligationDynamicsEvidence,
)
from causa.institutional.contracts.obligation_dynamics_evaluation import (
    SYNTHETIC_OBLIGATION_DYNAMICS_BENCHMARKS,
    SYNTHETIC_OBLIGATION_DYNAMICS_RED_TEAM_CASES,
    run_obligation_dynamics_benchmark_suite,
    run_obligation_dynamics_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_obligation_dynamics import (
    SyntheticObligationDynamicsEvaluationArtifact,
    build_synthetic_obligation_dynamics_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_obligation_dynamics_replays_after_obligation_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert (
        result.obligation_dynamics_evidence_mapping.schema_version
        == OBLIGATION_DYNAMICS_EVIDENCE_SCHEMA_VERSION
    )
    assert (
        result.obligation_dynamics_evidence_mapping.mapping_version
        == OBLIGATION_DYNAMICS_MAPPING_VERSION
    )
    assert (
        result.obligation_dynamics_constraint_set.model_version == OBLIGATION_DYNAMICS_MODEL_VERSION
    )
    assert result.obligation_dynamics_evaluation.proper_performance_discharge is True
    assert result.obligation_dynamics_evaluation.accrued_claims_preserved is True


def test_dynamics_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.obligation_dynamics_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedObligationDynamicsEvidence(
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
            request.model_copy(update={"obligation_dynamics_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_wrong_case_and_factual_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.obligation_dynamics_evidence

    with pytest.raises(ValueError, match="Obligation-dynamics evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "obligation_dynamics_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Obligation-dynamics evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "obligation_dynamics_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "obligation_dynamics_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-obligation-dynamics-evidence",
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
        ("obligation_breached", "breach status"),
        ("performance_rendered", "performance status"),
    ],
)
def test_analysis_rejects_dynamics_status_mismatch(predicate: str, message: str) -> None:
    request = build_synthetic_supply_analysis_request()
    assertions = tuple(
        assertion.model_copy(update={"value": False})
        if assertion.predicate.value == predicate
        or (
            predicate == "obligation_exists"
            and assertion.predicate.value
            in {
                "obligation_breached",
                "accrued_claims_exist",
                "performance_rendered",
                "performance_accepted_as_proper",
                "creditor_issued_receipt",
            }
        )
        or (
            predicate == "performance_rendered"
            and assertion.predicate.value
            in {"performance_accepted_as_proper", "creditor_issued_receipt"}
        )
        else assertion
        for assertion in request.obligation_dynamics_evidence.assertions
    )
    evidence = request.obligation_dynamics_evidence.model_copy(update={"assertions": assertions})

    with pytest.raises(ValueError, match=message):
        run_reviewed_contract_analysis(
            request.model_copy(update={"obligation_dynamics_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_dynamics_fact_consistency_rejects_breach_without_obligation() -> None:
    values = {field_name: False for field_name in ObligationDynamicsFactSet.model_fields}
    values["obligation_breached"] = True
    with pytest.raises(ValidationError, match="must exist"):
        ObligationDynamicsFactSet(**values)


def test_dynamics_sources_have_official_basis_and_review_flag() -> None:
    source_ids = (
        "synthetic-ru-gk382-390-assignment-v1",
        "synthetic-ru-gk391-3923-debt-transfer-v1",
        "synthetic-ru-gk407-413-discharge-v1",
        "synthetic-ru-gk414-419-discharge-v1",
        "synthetic-ru-plenum54-party-change-guidance-v1",
        "synthetic-ru-plenum6-discharge-guidance-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_dynamics_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_obligation_dynamics_benchmark_suite()
    red_team = run_obligation_dynamics_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_OBLIGATION_DYNAMICS_BENCHMARKS) == 21
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_OBLIGATION_DYNAMICS_RED_TEAM_CASES) == 22
    assert red_team.blocked == red_team.total


def test_exported_dynamics_artifact_is_reproducible() -> None:
    fixture = SyntheticObligationDynamicsEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_obligation_dynamics_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_obligation_dynamics_evaluation_artifact()
