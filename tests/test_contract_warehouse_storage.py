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
from causa.institutional.contracts.synthetic_warehouse_storage import (
    SyntheticWarehouseStorageEvaluationArtifact,
    build_synthetic_warehouse_storage_evaluation_artifact,
)
from causa.institutional.contracts.warehouse_storage import (
    WAREHOUSE_STORAGE_EVIDENCE_SCHEMA_VERSION,
    WAREHOUSE_STORAGE_MAPPING_VERSION,
    WAREHOUSE_STORAGE_MODEL_VERSION,
    ReviewedWarehouseStorageEvidence,
    WarehouseStorageFactSet,
)
from causa.institutional.contracts.warehouse_storage_evaluation import (
    SYNTHETIC_WAREHOUSE_STORAGE_BENCHMARKS,
    SYNTHETIC_WAREHOUSE_STORAGE_RED_TEAM_CASES,
    run_warehouse_storage_benchmark_suite,
    run_warehouse_storage_red_team_suite,
)


def test_reviewed_warehouse_storage_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.warehouse_storage_evidence_mapping
    assert mapping.schema_version == WAREHOUSE_STORAGE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == WAREHOUSE_STORAGE_MAPPING_VERSION
    assert result.warehouse_storage_constraint_set.model_version == WAREHOUSE_STORAGE_MODEL_VERSION
    evaluation = result.warehouse_storage_evaluation
    # В демонстрационном деле товары передавались покупателю, а не товарному складу.
    assert evaluation.warehouse_storage_qualified is False
    assert evaluation.requires_human_warehouse_storage_assessment is False


def test_warehouse_storage_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.warehouse_storage_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedWarehouseStorageEvidence(
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
            request.model_copy(update={"warehouse_storage_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_warehouse_storage_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.warehouse_storage_evidence

    with pytest.raises(ValueError, match="Warehouse-storage evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "warehouse_storage_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Warehouse-storage evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "warehouse_storage_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "warehouse_storage_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-warehouse-storage-evidence",
                                "synthetic-ru-gk907-911-warehouse-storage-concept-and-inspection-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_warehouse_storage_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in WarehouseStorageFactSet.model_fields}
    values.update(acceptance_discrepancy_not_recorded=True)
    with pytest.raises(ValidationError, match="Незафиксированные расхождения"):
        WarehouseStorageFactSet(**values)

    document = {field_name: False for field_name in WarehouseStorageFactSet.model_fields}
    document.update(warehouse_document_not_issued=True)
    with pytest.raises(ValidationError, match="Невыдача складского документа"):
        WarehouseStorageFactSet(**document)


def test_warehouse_storage_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk907-911-warehouse-storage-concept-and-inspection-v1",
        "synthetic-ru-gk912-918-warehouse-documents-and-goods-release-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_warehouse_storage_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_warehouse_storage_benchmark_suite()
    red_team = run_warehouse_storage_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_WAREHOUSE_STORAGE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_WAREHOUSE_STORAGE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_warehouse_storage_artifact_is_reproducible() -> None:
    fixture = SyntheticWarehouseStorageEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_warehouse_storage_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_warehouse_storage_evaluation_artifact()
