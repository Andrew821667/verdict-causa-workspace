from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.property_rights import (
    PROPERTY_RIGHTS_EVIDENCE_SCHEMA_VERSION,
    PROPERTY_RIGHTS_MAPPING_VERSION,
    PROPERTY_RIGHTS_MODEL_VERSION,
    PropertyRightsFactSet,
    ReviewedPropertyRightsEvidence,
)
from causa.institutional.contracts.property_rights_evaluation import (
    SYNTHETIC_PROPERTY_RIGHTS_BENCHMARKS,
    SYNTHETIC_PROPERTY_RIGHTS_RED_TEAM_CASES,
    run_property_rights_benchmark_suite,
    run_property_rights_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_property_rights import (
    SyntheticPropertyRightsEvaluationArtifact,
    build_synthetic_property_rights_evaluation_artifact,
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


def test_reviewed_property_rights_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.property_rights_evidence_mapping
    assert mapping.schema_version == PROPERTY_RIGHTS_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == PROPERTY_RIGHTS_MAPPING_VERSION
    assert result.property_rights_constraint_set.model_version == PROPERTY_RIGHTS_MODEL_VERSION
    evaluation = result.property_rights_evaluation
    # В демонстрационном деле вещно-правовые требования не заявлялись.
    assert evaluation.property_rights_qualified is False
    assert evaluation.requires_human_property_rights_assessment is False


def test_property_rights_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.property_rights_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedPropertyRightsEvidence(
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
            request.model_copy(update={"property_rights_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_property_rights_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.property_rights_evidence

    with pytest.raises(ValueError, match="Property-rights evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "property_rights_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Property-rights evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "property_rights_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "property_rights_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-property-rights-evidence",
                                "synthetic-ru-gk209-234-ownership-content-acquisition-and-prescription-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_property_rights_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in PropertyRightsFactSet.model_fields}
    values.update(good_faith_purchaser_protection_disregarded=True)
    with pytest.raises(ValidationError, match="об истребовании имущества"):
        PropertyRightsFactSet(**values)

    scope = {field_name: False for field_name in PropertyRightsFactSet.model_fields}
    scope.update(ownership_powers_breached=True)
    with pytest.raises(ValidationError, match="правомочий собственника"):
        PropertyRightsFactSet(**scope)


def test_property_rights_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk209-234-ownership-content-acquisition-and-prescription-v1",
        "synthetic-ru-gk244-305-common-property-and-protection-of-rights-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_unauthorized_disposal_propagates_through_general_effects() -> None:
    """Распоряжение неуправомоченным лицом не переносит титул на приобретателя.

    Вещные права подключены к слою общих положений: вывод по статье 209 ГК РФ
    меняет итог всего анализа, а не остаётся изолированным.
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    assert baseline.general_effects_evaluation.title_transfer_defeated is False

    unauthorized = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "property_rights_evidence": _flip(
                    request.property_rights_evidence,
                    property_right_asserted=True,
                    disposal_by_non_owner_detected=True,
                )
            }
        ),
        sources,
    )

    assert unauthorized.property_rights_evaluation.unauthorized_disposal_detected is True
    assert unauthorized.general_effects_evaluation.title_transfer_defeated is True
    assert unauthorized.requires_human_resolution is True


def test_property_rights_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_property_rights_benchmark_suite()
    red_team = run_property_rights_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_PROPERTY_RIGHTS_BENCHMARKS) == 12
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_PROPERTY_RIGHTS_RED_TEAM_CASES) == 12
    assert red_team.blocked == red_team.total


def test_exported_property_rights_artifact_is_reproducible() -> None:
    fixture = SyntheticPropertyRightsEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_property_rights_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_property_rights_evaluation_artifact()
