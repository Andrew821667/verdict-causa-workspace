from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.representation import (
    REPRESENTATION_EVIDENCE_SCHEMA_VERSION,
    REPRESENTATION_MAPPING_VERSION,
    REPRESENTATION_MODEL_VERSION,
    RepresentationFactSet,
    ReviewedRepresentationEvidence,
)
from causa.institutional.contracts.representation_evaluation import (
    SYNTHETIC_REPRESENTATION_BENCHMARKS,
    SYNTHETIC_REPRESENTATION_RED_TEAM_CASES,
    run_representation_benchmark_suite,
    run_representation_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_representation import (
    SyntheticRepresentationEvaluationArtifact,
    build_synthetic_representation_evaluation_artifact,
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


def test_reviewed_representation_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.representation_evidence_mapping
    assert mapping.schema_version == REPRESENTATION_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == REPRESENTATION_MAPPING_VERSION
    assert result.representation_constraint_set.model_version == REPRESENTATION_MODEL_VERSION
    evaluation = result.representation_evaluation
    # В демонстрационном деле договор подписан органами сторон без представителей.
    assert evaluation.representation_qualified is False
    assert evaluation.requires_human_representation_assessment is False


def test_representation_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.representation_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedRepresentationEvidence(
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
            request.model_copy(update={"representation_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_representation_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.representation_evidence

    with pytest.raises(ValueError, match="Representation evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "representation_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Representation evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"representation_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "representation_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-representation-evidence",
                                "synthetic-ru-gk182-184-representation-authority-and-limits-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_representation_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in RepresentationFactSet.model_fields}
    values.update(ratification_effect_disregarded=True)
    with pytest.raises(ValidationError, match="неуполномоченным лицом"):
        RepresentationFactSet(**values)

    scope = {field_name: False for field_name in RepresentationFactSet.model_fields}
    scope.update(authority_basis_invalid=True)
    with pytest.raises(ValidationError, match="основания полномочия"):
        RepresentationFactSet(**scope)


def test_representation_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk182-184-representation-authority-and-limits-v1",
        "synthetic-ru-gk185-189-power-of-attorney-form-term-and-termination-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_unauthorized_representation_propagates_through_general_effects() -> None:
    """Сделка неуполномоченного лица лишает договор эффекта для представляемого.

    Новый институт части первой подключён к слою общих положений, а не добавлен
    как изолированный чек-лист: вывод по статье 183 меняет итог всего анализа.
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    assert baseline.general_effects_evaluation.contract_legally_effective is True

    unauthorized = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "representation_evidence": _flip(
                    request.representation_evidence,
                    representation_relation_established=True,
                    unauthorized_act_without_ratification=True,
                )
            }
        ),
        sources,
    )

    assert unauthorized.representation_evaluation.unauthorized_representation_detected is True
    evaluation = unauthorized.general_effects_evaluation
    assert evaluation.unauthorized_representation_displaces_contract is True
    assert evaluation.contract_legally_effective is False
    assert evaluation.institute_conclusions_displaced is True
    assert evaluation.contractual_claims_enforceable is False
    assert evaluation.breach_findings_without_effect is True
    assert unauthorized.requires_human_resolution is True


def test_representation_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_representation_benchmark_suite()
    red_team = run_representation_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_REPRESENTATION_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_REPRESENTATION_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_representation_artifact_is_reproducible() -> None:
    fixture = SyntheticRepresentationEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_representation_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_representation_evaluation_artifact()
