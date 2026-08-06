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
from causa.institutional.contracts.synthetic_terms import (
    SyntheticTermsEvaluationArtifact,
    build_synthetic_terms_evaluation_artifact,
)
from causa.institutional.contracts.terms import (
    TERMS_EVIDENCE_SCHEMA_VERSION,
    TERMS_MAPPING_VERSION,
    TERMS_MODEL_VERSION,
    ReviewedTermsEvidence,
    TermsFactSet,
)
from causa.institutional.contracts.terms_evaluation import (
    SYNTHETIC_TERMS_BENCHMARKS,
    SYNTHETIC_TERMS_RED_TEAM_CASES,
    run_terms_benchmark_suite,
    run_terms_red_team_suite,
)

_LIMITATION_ELAPSED = {
    "claim_subject_to_limitation": True,
    "right_violation_and_defendant_known": True,
    "general_three_year_term_elapsed": True,
    "limitation_pleaded_by_party_before_judgment": True,
}


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


def test_reviewed_terms_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.terms_evidence_mapping
    assert mapping.schema_version == TERMS_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == TERMS_MAPPING_VERSION
    assert result.terms_constraint_set.model_version == TERMS_MODEL_VERSION
    evaluation = result.terms_evaluation
    # В демонстрационном деле самостоятельных возражений об исчислении срока нет.
    assert evaluation.terms_qualified is False
    assert evaluation.requires_human_terms_assessment is False


def test_terms_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.terms_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedTermsEvidence(
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
            request.model_copy(update={"terms_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_terms_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.terms_evidence

    with pytest.raises(ValueError, match="Terms evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "terms_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Terms evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"terms_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "terms_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-terms-evidence",
                                "synthetic-ru-gk194-actions-on-the-last-day-of-a-term-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_terms_fact_consistency_is_enforced() -> None:
    event = {field_name: False for field_name in TermsFactSet.model_fields}
    event.update(term_event_certainty_breached=True)
    with pytest.raises(ValidationError, match="неизбежности события"):
        TermsFactSet(**event)

    limitation = {field_name: False for field_name in TermsFactSet.model_fields}
    limitation.update(limitation_term_calculation_breached=True)
    with pytest.raises(ValidationError, match="исковой давности"):
        TermsFactSet(**limitation)


def test_terms_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk190-193-term-definition-start-and-end-v1",
        "synthetic-ru-gk194-actions-on-the-last-day-of-a-term-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_defective_term_calculation_suspends_the_limitation_bar() -> None:
    """Порок исчисления срока обесценивает вывод об истечении исковой давности.

    Срок исковой давности исчисляется по общим правилам главы 11 ГК РФ, поэтому
    при нарушении статей 190–194 истечение срока не считается установленным и не
    может быть положено в основание отказа в иске (статья 199 ГК РФ).
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    barred = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "limitation_evidence": _flip(request.limitation_evidence, **_LIMITATION_ELAPSED)
            }
        ),
        sources,
    )
    # Без порока исчисления давность закрывает судебную защиту.
    assert barred.general_effects_evaluation.claims_barred_by_limitation is True
    assert barred.general_effects_evaluation.contractual_claims_enforceable is False

    with_defect = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "limitation_evidence": _flip(request.limitation_evidence, **_LIMITATION_ELAPSED),
                "terms_evidence": _flip(
                    request.terms_evidence,
                    term_asserted=True,
                    limitation_term_calculation_breached=True,
                ),
            }
        ),
        sources,
    )

    assert with_defect.terms_evaluation.term_calculation_defective is True
    evaluation = with_defect.general_effects_evaluation
    # Отказ в защите снят: истечение срока больше не считается установленным.
    assert evaluation.claims_barred_by_limitation is False
    assert evaluation.limitation_conclusion_unreliable is True
    assert evaluation.contractual_claims_enforceable is True
    assert evaluation.breach_findings_without_effect is False
    # Вопрос остаётся на экспертизе.
    assert with_defect.requires_human_resolution is True


def test_terms_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_terms_benchmark_suite()
    red_team = run_terms_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_TERMS_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_TERMS_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_terms_artifact_is_reproducible() -> None:
    fixture = SyntheticTermsEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_terms_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_terms_evaluation_artifact()
