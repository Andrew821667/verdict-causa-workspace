from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.formation import (
    FORMATION_EVIDENCE_SCHEMA_VERSION,
    FORMATION_MAPPING_VERSION,
    FORMATION_MODEL_VERSION,
    FormationFactSet,
    ReviewedFormationEvidence,
)
from causa.institutional.contracts.formation_evaluation import (
    SYNTHETIC_FORMATION_BENCHMARKS,
    SYNTHETIC_FORMATION_RED_TEAM_CASES,
    run_formation_benchmark_suite,
    run_formation_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_formation import (
    SyntheticFormationEvaluationArtifact,
    build_synthetic_formation_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_formation_is_replayed_before_obligation() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert result.formation_evidence_mapping.schema_version == FORMATION_EVIDENCE_SCHEMA_VERSION
    assert result.formation_evidence_mapping.mapping_version == FORMATION_MAPPING_VERSION
    assert result.formation_constraint_set.model_version == FORMATION_MODEL_VERSION
    assert result.formation_evaluation.valid_offer is True
    assert result.formation_evaluation.conduct_acceptance_valid is True
    assert result.formation_evaluation.contract_concluded_prerequisites is True
    assert (
        result.formation_evaluation.contract_concluded_prerequisites
        == result.evidence_mapping.facts.duty_exists
    )


def test_formation_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.formation_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedFormationEvidence(
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
            request.model_copy(update={"formation_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_wrong_case_and_factual_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.formation_evidence

    with pytest.raises(ValueError, match="Formation evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "formation_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Formation evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"formation_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "formation_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": ("synthetic-case-supply-1-formation-evidence",)
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_formation_duty_mismatch() -> None:
    request = build_synthetic_supply_analysis_request()
    assertions = tuple(
        assertion.model_copy(update={"value": False})
        if assertion.predicate.value == "performance_conduct_started_in_time"
        else assertion
        for assertion in request.formation_evidence.assertions
    )
    evidence = request.formation_evidence.model_copy(update={"assertions": assertions})

    with pytest.raises(ValueError, match="does not match formation result"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"formation_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_formation_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in FormationFactSet.model_fields}
    values.update(
        acceptance_full_and_unconditional=True,
        acceptance_on_other_terms=True,
    )
    with pytest.raises(ValidationError, match="unconditional and on other terms"):
        FormationFactSet(**values)


def test_formation_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk432-contract-formation-model-v1",
        "synthetic-ru-gk435-offer-model-v1",
        "synthetic-ru-gk438-443-acceptance-model-v1",
        "synthetic-ru-plenum49-formation-guidance-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_formation_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_formation_benchmark_suite()
    red_team = run_formation_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_FORMATION_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_FORMATION_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_formation_artifact_is_reproducible() -> None:
    fixture = SyntheticFormationEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_formation_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_formation_evaluation_artifact()
