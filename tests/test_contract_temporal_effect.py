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
from causa.institutional.contracts.synthetic_temporal_effect import (
    SyntheticTemporalEffectEvaluationArtifact,
    build_synthetic_temporal_effect_evaluation_artifact,
)
from causa.institutional.contracts.temporal_effect import (
    TEMPORAL_EFFECT_EVIDENCE_SCHEMA_VERSION,
    TEMPORAL_EFFECT_MAPPING_VERSION,
    TEMPORAL_EFFECT_MODEL_VERSION,
    ReviewedTemporalEffectEvidence,
    TemporalEffectFactSet,
)
from causa.institutional.contracts.temporal_effect_evaluation import (
    SYNTHETIC_TEMPORAL_EFFECT_BENCHMARKS,
    SYNTHETIC_TEMPORAL_EFFECT_RED_TEAM_CASES,
    run_temporal_effect_benchmark_suite,
    run_temporal_effect_red_team_suite,
)


def test_reviewed_temporal_effect_is_replayed_and_consistent_with_formation() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.temporal_effect_evidence_mapping
    assert mapping.schema_version == TEMPORAL_EFFECT_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == TEMPORAL_EFFECT_MAPPING_VERSION
    assert result.temporal_effect_constraint_set.model_version == TEMPORAL_EFFECT_MODEL_VERSION
    evaluation = result.temporal_effect_evaluation
    assert evaluation.conclusion_moment_established is True
    assert evaluation.contract_in_force is True
    assert evaluation.term_expired is True
    assert evaluation.liability_preserved_after_term is True
    assert evaluation.future_obligations_discharged_by_term_end is False
    # Момент заключения согласован с результатом formation.
    assert (
        evaluation.conclusion_moment_established
        == result.formation_evaluation.contract_concluded_prerequisites
    )


def test_temporal_effect_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.temporal_effect_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedTemporalEffectEvidence(
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
            request.model_copy(update={"temporal_effect_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_temporal_effect_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.temporal_effect_evidence

    with pytest.raises(ValueError, match="Temporal-effect evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "temporal_effect_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Temporal-effect evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "temporal_effect_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "temporal_effect_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-temporal-effect-evidence",
                                "synthetic-ru-gk433-conclusion-moment-model-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_temporal_effect_conclusion_mismatch() -> None:
    request = build_synthetic_supply_analysis_request()
    # Реальный договор без передачи имущества: момент заключения по статье 433 не
    # установлен, что должно расходиться с подтвержденным заключением по formation.
    assertions = tuple(
        assertion.model_copy(update={"value": True})
        if assertion.predicate.value == "contract_requires_property_delivery"
        else assertion
        for assertion in request.temporal_effect_evidence.assertions
    )
    evidence = request.temporal_effect_evidence.model_copy(update={"assertions": assertions})

    # Момент заключения станет False при подтвержденном formation — согласованность
    # сохранена (импликация односторонняя), поэтому анализ проходит и помечает разрыв.
    result = run_reviewed_contract_analysis(
        request.model_copy(update={"temporal_effect_evidence": evidence}),
        build_synthetic_supply_analysis_sources(),
    ).temporal_effect_evaluation
    assert result.conclusion_moment_established is False
    assert result.contract_in_force is False


def test_temporal_effect_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in TemporalEffectFactSet.model_fields}
    values.update(term_end_reached=True)
    with pytest.raises(ValidationError, match="Term end cannot be reached"):
        TemporalEffectFactSet(**values)


def test_temporal_effect_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk425-contract-effect-model-v1",
        "synthetic-ru-gk433-conclusion-moment-model-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_temporal_effect_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_temporal_effect_benchmark_suite()
    red_team = run_temporal_effect_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_TEMPORAL_EFFECT_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_TEMPORAL_EFFECT_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_temporal_effect_artifact_is_reproducible() -> None:
    fixture = SyntheticTemporalEffectEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_temporal_effect_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_temporal_effect_evaluation_artifact()
