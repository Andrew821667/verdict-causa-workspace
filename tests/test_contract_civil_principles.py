from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.civil_principles import (
    CIVIL_PRINCIPLES_EVIDENCE_SCHEMA_VERSION,
    CIVIL_PRINCIPLES_MAPPING_VERSION,
    CIVIL_PRINCIPLES_MODEL_VERSION,
    CivilPrinciplesFactSet,
    ReviewedCivilPrinciplesEvidence,
)
from causa.institutional.contracts.civil_principles_evaluation import (
    SYNTHETIC_CIVIL_PRINCIPLES_BENCHMARKS,
    SYNTHETIC_CIVIL_PRINCIPLES_RED_TEAM_CASES,
    run_civil_principles_benchmark_suite,
    run_civil_principles_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_civil_principles import (
    SyntheticCivilPrinciplesEvaluationArtifact,
    build_synthetic_civil_principles_evaluation_artifact,
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


def test_reviewed_civil_principles_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.civil_principles_evidence_mapping
    assert mapping.schema_version == CIVIL_PRINCIPLES_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == CIVIL_PRINCIPLES_MAPPING_VERSION
    assert result.civil_principles_constraint_set.model_version == CIVIL_PRINCIPLES_MODEL_VERSION
    evaluation = result.civil_principles_evaluation
    # В демонстрационном деле о злоупотреблении правом не заявлялось.
    assert evaluation.civil_principles_qualified is False
    assert evaluation.requires_human_civil_principles_assessment is False


def test_civil_principles_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.civil_principles_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedCivilPrinciplesEvidence(
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
            request.model_copy(update={"civil_principles_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_civil_principles_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.civil_principles_evidence

    with pytest.raises(ValueError, match="Civil-principles evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "civil_principles_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Civil-principles evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "civil_principles_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "civil_principles_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-civil-principles-evidence",
                                "synthetic-ru-gk1-10-civil-principles-and-limits-of-exercise-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_civil_principles_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in CivilPrinciplesFactSet.model_fields}
    values.update(protection_refusal_not_applied=True)
    with pytest.raises(ValidationError, match="злоупотребление правом"):
        CivilPrinciplesFactSet(**values)

    scope = {field_name: False for field_name in CivilPrinciplesFactSet.model_fields}
    scope.update(good_faith_principle_breached=True)
    with pytest.raises(ValidationError, match="принципа добросовестности"):
        CivilPrinciplesFactSet(**scope)


def test_civil_principles_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1-10-civil-principles-and-limits-of-exercise-v1",
        "synthetic-ru-gk12-16-1-protection-methods-damages-and-authority-liability-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_abuse_of_right_refuses_protection_through_general_effects() -> None:
    """Злоупотребление правом влечёт отказ в защите права (статья 10 ГК РФ)."""
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    assert baseline.general_effects_evaluation.judicial_protection_available is True

    abusive = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "civil_principles_evidence": _flip(
                    request.civil_principles_evidence,
                    civil_rights_exercise_asserted=True,
                    abuse_of_right_established=True,
                )
            }
        ),
        sources,
    )

    assert abusive.civil_principles_evaluation.abuse_of_right_detected is True
    evaluation = abusive.general_effects_evaluation
    assert evaluation.protection_refused_for_abuse is True
    assert evaluation.judicial_protection_available is False
    assert evaluation.contractual_claims_enforceable is False
    assert evaluation.breach_findings_without_effect is True
    # Договор при этом сохраняет силу: отказано именно в защите права.
    assert evaluation.contract_legally_effective is True
    assert abusive.requires_human_resolution is True


def test_civil_principles_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_civil_principles_benchmark_suite()
    red_team = run_civil_principles_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_CIVIL_PRINCIPLES_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_CIVIL_PRINCIPLES_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_civil_principles_artifact_is_reproducible() -> None:
    fixture = SyntheticCivilPrinciplesEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_civil_principles_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_civil_principles_evaluation_artifact()
