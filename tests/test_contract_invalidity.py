from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.invalidity import (
    INVALIDITY_EVIDENCE_SCHEMA_VERSION,
    INVALIDITY_MAPPING_VERSION,
    INVALIDITY_MODEL_VERSION,
    InvalidityFactSet,
    ReviewedInvalidityEvidence,
)
from causa.institutional.contracts.invalidity_evaluation import (
    SYNTHETIC_INVALIDITY_BENCHMARKS,
    SYNTHETIC_INVALIDITY_RED_TEAM_CASES,
    run_invalidity_benchmark_suite,
    run_invalidity_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_invalidity import (
    SyntheticInvalidityEvaluationArtifact,
    build_synthetic_invalidity_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_invalidity_precedes_contractual_duty_effects() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert result.invalidity_evidence_mapping.schema_version == INVALIDITY_EVIDENCE_SCHEMA_VERSION
    assert result.invalidity_evidence_mapping.mapping_version == INVALIDITY_MAPPING_VERSION
    assert result.invalidity_constraint_set.model_version == INVALIDITY_MODEL_VERSION
    assert result.invalidity_evaluation.transaction_presumed_effective is True
    assert result.invalidity_evaluation.contractual_effect_displaced is False
    assert result.invalidity_evidence_mapping.facts.transaction_concluded == (
        result.formation_evaluation.contract_concluded_prerequisites
    )


def test_invalidity_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.invalidity_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedInvalidityEvidence(
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
            request.model_copy(update={"invalidity_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_wrong_case_and_factual_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.invalidity_evidence

    with pytest.raises(ValueError, match="Invalidity evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "invalidity_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Invalidity evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"invalidity_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "invalidity_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": ("synthetic-case-supply-1-invalidity-evidence",)
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_invalidity_transaction_status_mismatch() -> None:
    request = build_synthetic_supply_analysis_request()
    assertions = tuple(
        assertion.model_copy(update={"value": False})
        if assertion.predicate.value == "transaction_concluded"
        else assertion
        for assertion in request.invalidity_evidence.assertions
    )
    evidence = request.invalidity_evidence.model_copy(update={"assertions": assertions})

    with pytest.raises(ValueError, match="does not match formation result"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"invalidity_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_displaced_effect_with_contractual_duty() -> None:
    request = build_synthetic_supply_analysis_request()
    assertions = tuple(
        assertion.model_copy(update={"value": True})
        if assertion.predicate.value == "sham_intent_proven"
        else assertion
        for assertion in request.invalidity_evidence.assertions
    )
    evidence = request.invalidity_evidence.model_copy(update={"assertions": assertions})

    with pytest.raises(ValueError, match="do not match contractual duty evidence"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"invalidity_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_invalidity_fact_consistency_rejects_knowledge_without_ground() -> None:
    values = {field_name: False for field_name in InvalidityFactSet.model_fields}
    values.update(transaction_concluded=True, counterparty_knew_consent_absent=True)
    with pytest.raises(ValidationError, match="requires absent consent"):
        InvalidityFactSet(**values)


def test_invalidity_sources_have_official_basis_and_review_flag() -> None:
    source_ids = (
        "synthetic-ru-gk166-168-invalidity-framework-v1",
        "synthetic-ru-gk169-172-void-transactions-v1",
        "synthetic-ru-gk173-179-voidable-transactions-v1",
        "synthetic-ru-gk180-181-invalidity-effects-v1",
        "synthetic-ru-plenum25-invalidity-guidance-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_invalidity_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_invalidity_benchmark_suite()
    red_team = run_invalidity_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_INVALIDITY_BENCHMARKS) == 14
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_INVALIDITY_RED_TEAM_CASES) == 14
    assert red_team.blocked == red_team.total


def test_exported_invalidity_artifact_is_reproducible() -> None:
    fixture = SyntheticInvalidityEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_invalidity_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_invalidity_evaluation_artifact()
