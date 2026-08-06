from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.objects import (
    OBJECTS_EVIDENCE_SCHEMA_VERSION,
    OBJECTS_MAPPING_VERSION,
    OBJECTS_MODEL_VERSION,
    ObjectsFactSet,
    ReviewedObjectsEvidence,
)
from causa.institutional.contracts.objects_evaluation import (
    SYNTHETIC_OBJECTS_BENCHMARKS,
    SYNTHETIC_OBJECTS_RED_TEAM_CASES,
    run_objects_benchmark_suite,
    run_objects_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_objects import (
    SyntheticObjectsEvaluationArtifact,
    build_synthetic_objects_evaluation_artifact,
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


def test_reviewed_objects_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.objects_evidence_mapping
    assert mapping.schema_version == OBJECTS_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == OBJECTS_MAPPING_VERSION
    assert result.objects_constraint_set.model_version == OBJECTS_MODEL_VERSION
    evaluation = result.objects_evaluation
    # В демонстрационном деле предмет поставки не ограничен в обороте.
    assert evaluation.objects_qualified is False
    assert evaluation.requires_human_objects_assessment is False


def test_objects_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.objects_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedObjectsEvidence(
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
            request.model_copy(update={"objects_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_objects_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.objects_evidence

    with pytest.raises(ValueError, match="Objects evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "objects_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Objects evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"objects_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "objects_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-objects-evidence",
                                "synthetic-ru-gk140-152-money-securities-and-intangible-benefits-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_objects_fact_consistency_is_enforced() -> None:
    reputation = {field_name: False for field_name in ObjectsFactSet.model_fields}
    reputation.update(honour_and_reputation_protection_breached=True)
    with pytest.raises(ValidationError, match="нематериальных благ"):
        ObjectsFactSet(**reputation)

    circulation = {field_name: False for field_name in ObjectsFactSet.model_fields}
    circulation.update(object_not_in_civil_circulation=True)
    with pytest.raises(ValidationError, match="объекту"):
        ObjectsFactSet(**circulation)


def test_objects_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk128-136-objects-circulation-and-kinds-of-things-v1",
        "synthetic-ru-gk140-152-money-securities-and-intangible-benefits-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_object_excluded_from_circulation_voids_the_contract() -> None:
    """Отчуждение объекта, изъятого из оборота, лишает договор действия.

    Объекты гражданских прав свободно отчуждаются, если они не ограничены в обороте
    (статья 129 ГК РФ); сделка, нарушающая это требование и посягающая на публичные
    интересы, ничтожна (пункт 2 статьи 168 ГК РФ).
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    assert baseline.general_effects_evaluation.restricted_object_voids_transaction is False

    restricted = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "objects_evidence": _flip(
                    request.objects_evidence,
                    object_of_rights_asserted=True,
                    object_not_in_civil_circulation=True,
                )
            }
        ),
        sources,
    )

    assert restricted.objects_evaluation.object_excluded_from_circulation is True
    evaluation = restricted.general_effects_evaluation
    assert evaluation.restricted_object_voids_transaction is True
    assert evaluation.contract_legally_effective is False
    assert evaluation.institute_conclusions_displaced is True
    assert evaluation.contractual_claims_enforceable is False
    assert restricted.requires_human_resolution is True


def test_objects_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_objects_benchmark_suite()
    red_team = run_objects_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_OBJECTS_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_OBJECTS_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_objects_artifact_is_reproducible() -> None:
    fixture = SyntheticObjectsEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_objects_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_objects_evaluation_artifact()
