import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.authority_model import AuthorityResolutionRule
from causa.institutional.contracts.reviewed_analysis import (
    ANALYSIS_PIPELINE_VERSION,
    CASE_EVIDENCE_SCHEMA_VERSION,
    EVIDENCE_MAPPING_VERSION,
    ContractEvidencePredicate,
    ReviewedCaseEvidence,
    ReviewedContractAnalysisArtifact,
    run_reviewed_contract_analysis,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_analysis_maps_every_fact_with_provenance() -> None:
    artifact = build_synthetic_supply_analysis_artifact()
    result = artifact.result

    assert result.pipeline_version == ANALYSIS_PIPELINE_VERSION
    assert result.evidence_mapping.schema_version == CASE_EVIDENCE_SCHEMA_VERSION
    assert result.evidence_mapping.mapping_version == EVIDENCE_MAPPING_VERSION
    assert len(result.evidence_mapping.provenance) == 13
    assert {item.fact_name for item in result.evidence_mapping.provenance} == {
        "due_date_missed",
        *(predicate.value for predicate in ContractEvidencePredicate),
    }
    assert result.evidence_mapping.facts.due_date_missed is True
    provenance_by_fact = {
        item.fact_name: item for item in result.evidence_mapping.provenance
    }
    assert provenance_by_fact["duty_exists"].formal_atom_refs == [
        "condition-supply-relation",
        "condition-agreed-date",
    ]
    assert provenance_by_fact["valid_exception_applies"].formal_atom_refs == [
        "exception-valid-excuse"
    ]
    assert result.constraint_evaluation.late_performance_issue is True
    assert result.constraint_evaluation.breach_issue is True


def test_reviewed_analysis_resolves_temporal_authority_before_formal_evaluation() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert (
        result.authority_evaluation.selected_source_id
        == "synthetic-ru-contract-supply-delivery-duty-v2"
    )
    assert result.authority_evaluation.excluded_source_ids == [
        "synthetic-ru-contract-supply-delivery-duty-v1"
    ]
    assert (
        AuthorityResolutionRule.TEMPORAL_APPLICABILITY
        in result.authority_evaluation.applied_rules
    )
    assert result.requires_human_resolution is False


@pytest.mark.parametrize(
    ("artifact_field", "error_fragment"),
    [
        ("reviewed_norm", "Reviewed norm must be reviewed"),
        ("case_evidence", "Case evidence must be reviewed"),
        ("temporal_evidence", "Temporal evidence must be reviewed"),
        ("authority_input", "Authority input must be reviewed"),
    ],
)
def test_analysis_rejects_each_unreviewed_input(
    artifact_field: str,
    error_fragment: str,
) -> None:
    request = build_synthetic_supply_analysis_request()
    artifact = getattr(request, artifact_field)
    unreviewed_artifact = artifact.model_copy(
        update={"review_status": BootstrapReviewStatus.DRAFT}
    )
    invalid_request = request.model_copy(update={artifact_field: unreviewed_artifact})

    with pytest.raises(ValueError, match=error_fragment):
        run_reviewed_contract_analysis(
            invalid_request,
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_requires_reviewer_coordinates() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence_without_reviewer = request.case_evidence.model_copy(update={"reviewer_id": None})
    invalid_request = request.model_copy(update={"case_evidence": evidence_without_reviewer})

    with pytest.raises(ValueError, match="Case evidence requires a reviewer_id"):
        run_reviewed_contract_analysis(
            invalid_request,
            build_synthetic_supply_analysis_sources(),
        )


def test_case_evidence_rejects_duplicate_predicates() -> None:
    evidence = build_synthetic_supply_analysis_request().case_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedCaseEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=(*evidence.assertions, evidence.assertions[0]),
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )


def test_analysis_rejects_incomplete_evidence() -> None:
    request = build_synthetic_supply_analysis_request()
    incomplete_evidence = request.case_evidence.model_copy(
        update={"assertions": request.case_evidence.assertions[:-1]}
    )
    invalid_request = request.model_copy(update={"case_evidence": incomplete_evidence})

    with pytest.raises(ValueError, match="missing predicates"):
        run_reviewed_contract_analysis(
            invalid_request,
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unknown_source_references() -> None:
    request = build_synthetic_supply_analysis_request()
    first_assertion = request.case_evidence.assertions[0].model_copy(
        update={"source_refs": ("missing-source",)}
    )
    evidence = request.case_evidence.model_copy(
        update={"assertions": (first_assertion, *request.case_evidence.assertions[1:])}
    )
    invalid_request = request.model_copy(update={"case_evidence": evidence})

    with pytest.raises(ValueError, match="Unknown source references: missing-source"):
        run_reviewed_contract_analysis(
            invalid_request,
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_mismatched_case_and_evaluation_coordinates() -> None:
    request = build_synthetic_supply_analysis_request()
    wrong_case = request.case_evidence.model_copy(update={"case_id": "other-case"})
    wrong_date = request.authority_input.model_copy(update={"evaluation_date": "2026-01-22"})

    with pytest.raises(ValueError, match="Case evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"case_evidence": wrong_case}),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="evaluation dates must match"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"authority_input": wrong_date}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unsupported_evidence_schema() -> None:
    request = build_synthetic_supply_analysis_request()
    future_evidence = request.case_evidence.model_copy(update={"schema_version": "future.v1"})

    with pytest.raises(ValueError, match="unsupported schema version"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"case_evidence": future_evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unsupported_norm_schema() -> None:
    request = build_synthetic_supply_analysis_request()
    future_norm = request.reviewed_norm.model_copy(update={"schema_version": "future.norm.v1"})

    with pytest.raises(ValueError, match="unsupported bootstrap schema"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"reviewed_norm": future_norm}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_requires_norm_source_among_authority_candidates() -> None:
    request = build_synthetic_supply_analysis_request()
    authority_input = request.authority_input.model_copy(
        update={
            "candidate_source_ids": (
                "synthetic-ru-contract-supply-delivery-duty-v1",
            )
        }
    )

    with pytest.raises(ValueError, match="must be an authority candidate"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"authority_input": authority_input}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_inapplicable_norm_source() -> None:
    request = build_synthetic_supply_analysis_request()
    expired_source_id = "synthetic-ru-contract-supply-delivery-duty-v1"
    expired_norm = request.reviewed_norm.model_copy(update={"source_id": expired_source_id})
    authority_input = request.authority_input.model_copy(
        update={"candidate_source_ids": (expired_source_id,)}
    )

    with pytest.raises(ValueError, match="not applicable"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "reviewed_norm": expired_norm,
                    "authority_input": authority_input,
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_duplicate_source_registry_entries() -> None:
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()

    with pytest.raises(ValueError, match="duplicate source ids"):
        run_reviewed_contract_analysis(request, [*sources, sources[0]])


def test_analysis_rejects_different_authority_winner() -> None:
    request = build_synthetic_supply_analysis_request()
    constitutional_source = get_synthetic_contract_source(
        "synthetic-ru-constitutional-contract-guarantee"
    )
    authority_input = request.authority_input.model_copy(
        update={
            "candidate_source_ids": (
                request.reviewed_norm.source_id,
                constitutional_source.id,
            )
        }
    )

    with pytest.raises(ValueError, match="selected a different source"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"authority_input": authority_input}),
            [*build_synthetic_supply_analysis_sources(), constitutional_source],
        )


def test_analysis_marks_equal_authority_for_human_resolution() -> None:
    request = build_synthetic_supply_analysis_request()
    equal_source = get_synthetic_contract_source(
        "synthetic-ru-contract-supply-delivery-duty"
    )
    authority_input = request.authority_input.model_copy(
        update={"candidate_source_ids": (request.reviewed_norm.source_id, equal_source.id)}
    )
    result = run_reviewed_contract_analysis(
        request.model_copy(update={"authority_input": authority_input}),
        [*build_synthetic_supply_analysis_sources(), equal_source],
    )

    assert result.authority_evaluation.selected_source_id is None
    assert result.requires_human_resolution is True


def test_reviewed_remedy_assertions_drive_remedy_constraints() -> None:
    request = build_synthetic_supply_analysis_request()
    true_predicates = {
        ContractEvidencePredicate.LOSS_CLAIMED,
        ContractEvidencePredicate.CAUSATION_ESTABLISHED,
        ContractEvidencePredicate.REMEDY_REQUESTED,
    }
    assertions = tuple(
        assertion.model_copy(update={"value": True})
        if assertion.predicate in true_predicates
        else assertion
        for assertion in request.case_evidence.assertions
    )
    evidence = request.case_evidence.model_copy(update={"assertions": assertions})
    result = run_reviewed_contract_analysis(
        request.model_copy(update={"case_evidence": evidence}),
        build_synthetic_supply_analysis_sources(),
    )

    assert result.evidence_mapping.facts.causation_established is True
    assert result.constraint_evaluation.damages_remedy_available is True
    assert result.constraint_evaluation.causation_evidence_gap is False


def test_exported_reviewed_analysis_fixture_is_valid() -> None:
    fixture_path = Path("examples/synthetic_reviewed_contract_analysis.json")
    artifact = ReviewedContractAnalysisArtifact.model_validate(
        json.loads(fixture_path.read_text(encoding="utf-8"))
    )

    assert artifact.result.request_id == artifact.request.id
    assert artifact.result.source_ids
    assert all(artifact.result.reviewer_ids)


def test_reviewed_analysis_is_deterministic() -> None:
    first = build_synthetic_supply_analysis_artifact()
    second = build_synthetic_supply_analysis_artifact()

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
