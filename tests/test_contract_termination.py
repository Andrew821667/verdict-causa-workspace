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
from causa.institutional.contracts.synthetic_termination import (
    SyntheticTerminationEvaluationArtifact,
    build_synthetic_termination_evaluation_artifact,
)
from causa.institutional.contracts.termination import (
    TERMINATION_EVIDENCE_SCHEMA_VERSION,
    TERMINATION_MAPPING_VERSION,
    TERMINATION_MODEL_VERSION,
    ReviewedTerminationEvidence,
    TerminationFactSet,
)
from causa.institutional.contracts.termination_evaluation import (
    SYNTHETIC_TERMINATION_BENCHMARKS,
    SYNTHETIC_TERMINATION_RED_TEAM_CASES,
    run_termination_benchmark_suite,
    run_termination_red_team_suite,
)


def test_reviewed_termination_is_replayed_after_formation() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert result.termination_evidence_mapping.schema_version == (
        TERMINATION_EVIDENCE_SCHEMA_VERSION
    )
    assert result.termination_evidence_mapping.mapping_version == TERMINATION_MAPPING_VERSION
    assert result.termination_constraint_set.model_version == TERMINATION_MODEL_VERSION
    assert result.termination_evaluation.contract_continues_unchanged is True
    assert result.termination_evaluation.effective_termination is False
    assert result.termination_evidence_mapping.facts.contract_formed == (
        result.formation_evaluation.contract_concluded_prerequisites
    )


def test_termination_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.termination_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedTerminationEvidence(
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
            request.model_copy(update={"termination_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_wrong_case_and_factual_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.termination_evidence

    with pytest.raises(ValueError, match="Termination evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "termination_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Termination evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "termination_evidence": evidence.model_copy(update={"case_id": "other-case"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "termination_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": ("synthetic-case-supply-1-termination-evidence",)
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_contract_status_mismatch() -> None:
    request = build_synthetic_supply_analysis_request()
    assertions = tuple(
        assertion.model_copy(update={"value": False})
        if assertion.predicate.value == "contract_formed"
        else assertion
        for assertion in request.termination_evidence.assertions
    )
    evidence = request.termination_evidence.model_copy(update={"assertions": assertions})

    with pytest.raises(ValueError, match="does not match formation result"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"termination_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_termination_fact_consistency_rejects_ambiguous_target() -> None:
    values = {field_name: False for field_name in TerminationFactSet.model_fields}
    values.update(
        contract_formed=True,
        unilateral_action_declared=True,
        unilateral_action_targets_modification=True,
        unilateral_action_targets_termination=True,
    )
    with pytest.raises(ValidationError, match="exactly one legal effect"):
        TerminationFactSet(**values)


def test_termination_sources_are_synthetic_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk450-453-termination-model-v1",
        "synthetic-ru-gk310-4501-unilateral-model-v1",
        "synthetic-ru-plenum54-unilateral-guidance-v1",
        "synthetic-ru-plenum18-pretrial-guidance-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_termination_benchmark_and_red_team_cover_formal_boundaries() -> None:
    benchmark = run_termination_benchmark_suite()
    red_team = run_termination_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_TERMINATION_BENCHMARKS) == 12
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_TERMINATION_RED_TEAM_CASES) == 12
    assert red_team.blocked == red_team.total


def test_termination_model_preserves_accrued_claims() -> None:
    artifact = build_synthetic_termination_evaluation_artifact()
    result = next(
        item
        for item in artifact.benchmark_report.results
        if item.task_id == "termination-bench-mutual-termination"
    )

    assert result.observed_outcomes["effective_termination"] is True
    assert result.observed_outcomes["accrued_claims_preserved"] is True


def test_exported_termination_artifact_is_reproducible() -> None:
    fixture = SyntheticTerminationEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_termination_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_termination_evaluation_artifact()
