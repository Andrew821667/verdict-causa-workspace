from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.storage import (
    STORAGE_EVIDENCE_SCHEMA_VERSION,
    STORAGE_MAPPING_VERSION,
    STORAGE_MODEL_VERSION,
    ReviewedStorageEvidence,
    StorageFactSet,
)
from causa.institutional.contracts.storage_evaluation import (
    SYNTHETIC_STORAGE_BENCHMARKS,
    SYNTHETIC_STORAGE_RED_TEAM_CASES,
    run_storage_benchmark_suite,
    run_storage_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source
from causa.institutional.contracts.synthetic_storage import (
    SyntheticStorageEvaluationArtifact,
    build_synthetic_storage_evaluation_artifact,
)


def test_reviewed_storage_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.storage_evidence_mapping
    assert mapping.schema_version == STORAGE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == STORAGE_MAPPING_VERSION
    assert result.storage_constraint_set.model_version == STORAGE_MODEL_VERSION
    evaluation = result.storage_evaluation
    # В демонстрационном деле поставка товаров, а не передача вещи на хранение.
    assert evaluation.storage_qualified is False
    assert evaluation.requires_human_storage_assessment is False


def test_storage_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.storage_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedStorageEvidence(
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
            request.model_copy(update={"storage_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_storage_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.storage_evidence

    with pytest.raises(ValueError, match="Storage evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "storage_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Storage evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"storage_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "storage_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-storage-evidence",
                                "synthetic-ru-gk886-895-storage-concept-form-period-and-safekeeping-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_storage_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in StorageFactSet.model_fields}
    values.update(custodian_liability_rules_breached=True)
    with pytest.raises(ValidationError, match="ответственности хранителя"):
        StorageFactSet(**values)

    form = {field_name: False for field_name in StorageFactSet.model_fields}
    form.update(storage_written_form_not_observed=True)
    with pytest.raises(ValidationError, match="Несоблюдение письменной формы"):
        StorageFactSet(**form)


def test_storage_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk886-895-storage-concept-form-period-and-safekeeping-v1",
        "synthetic-ru-gk896-906-storage-remuneration-return-and-liability-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_storage_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_storage_benchmark_suite()
    red_team = run_storage_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_STORAGE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_STORAGE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_storage_artifact_is_reproducible() -> None:
    fixture = SyntheticStorageEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_storage_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_storage_evaluation_artifact()
