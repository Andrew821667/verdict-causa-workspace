from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.persons import (
    PERSONS_EVIDENCE_SCHEMA_VERSION,
    PERSONS_MAPPING_VERSION,
    PERSONS_MODEL_VERSION,
    PersonsFactSet,
    ReviewedPersonsEvidence,
)
from causa.institutional.contracts.persons_evaluation import (
    SYNTHETIC_PERSONS_BENCHMARKS,
    SYNTHETIC_PERSONS_RED_TEAM_CASES,
    run_persons_benchmark_suite,
    run_persons_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_persons import (
    SyntheticPersonsEvaluationArtifact,
    build_synthetic_persons_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def _flip(evidence, **updates: bool):
    return evidence.model_copy(
        update={
            "assertions": tuple(
                assertion.model_copy(update={"value": updates[assertion.predicate.value]})
                if assertion.predicate.value in updates
                else assertion
                for assertion in evidence.assertions
            )
        }
    )


def test_reviewed_persons_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.persons_evidence_mapping
    assert mapping.schema_version == PERSONS_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == PERSONS_MAPPING_VERSION
    assert result.persons_constraint_set.model_version == PERSONS_MODEL_VERSION
    evaluation = result.persons_evaluation
    # В демонстрационном деле обе стороны — действующие юридические лица.
    assert evaluation.persons_qualified is False
    assert evaluation.requires_human_persons_assessment is False


def test_persons_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.persons_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedPersonsEvidence(
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
            request.model_copy(update={"persons_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_persons_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.persons_evidence

    with pytest.raises(ValueError, match="Persons evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "persons_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Persons evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"persons_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "persons_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-persons-evidence",
                                "synthetic-ru-gk17-30-legal-and-active-capacity-of-citizens-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_persons_fact_consistency_is_enforced() -> None:
    guardianship = {field_name: False for field_name in PersonsFactSet.model_fields}
    guardianship.update(guardianship_consent_missing=True)
    with pytest.raises(ValidationError, match="согласия попечителя"):
        PersonsFactSet(**guardianship)

    incapacity = {field_name: False for field_name in PersonsFactSet.model_fields}
    incapacity.update(incapacity_declared_by_court=True)
    with pytest.raises(ValidationError, match="недееспособным"):
        PersonsFactSet(**incapacity)


def test_persons_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk17-30-legal-and-active-capacity-of-citizens-v1",
        "synthetic-ru-gk49-53-capacity-registration-and-bodies-of-legal-entities-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_declared_incapacity_voids_the_contract_through_general_effects() -> None:
    """Сделка недееспособного ничтожна, а не оспорима.

    В отличие от отсутствия согласия по статье 173.1, недействительность здесь
    наступает независимо от признания её судом (пункт 1 статьи 166 ГК РФ), поэтому
    слой снимает действие договора, а не помечает сделку оспоримой.
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    assert baseline.general_effects_evaluation.contract_legally_effective is True

    incapable = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "persons_evidence": _flip(
                    request.persons_evidence,
                    party_capacity_asserted=True,
                    incapacity_declared_by_court=True,
                )
            }
        ),
        sources,
    )

    assert incapable.persons_evaluation.party_lacks_capacity is True
    evaluation = incapable.general_effects_evaluation
    assert evaluation.incapacity_voids_transaction is True
    assert evaluation.contract_legally_effective is False
    assert evaluation.institute_conclusions_displaced is True
    assert evaluation.contractual_claims_enforceable is False
    # Ничтожность не помечается как оспоримость.
    assert evaluation.transaction_challengeable_for_missing_consent is False
    assert incapable.requires_human_resolution is True


def test_persons_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_persons_benchmark_suite()
    red_team = run_persons_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_PERSONS_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_PERSONS_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_persons_artifact_is_reproducible() -> None:
    fixture = SyntheticPersonsEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_persons_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_persons_evaluation_artifact()
