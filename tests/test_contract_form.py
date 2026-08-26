from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.form import (
    FORM_EVIDENCE_SCHEMA_VERSION,
    FORM_MAPPING_VERSION,
    FORM_MODEL_VERSION,
    FormFactSet,
    ReviewedFormEvidence,
)
from causa.institutional.contracts.form_evaluation import (
    SYNTHETIC_FORM_BENCHMARKS,
    SYNTHETIC_FORM_RED_TEAM_CASES,
    run_form_benchmark_suite,
    run_form_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_form import (
    SyntheticFormEvaluationArtifact,
    build_synthetic_form_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_form_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.form_evidence_mapping
    assert mapping.schema_version == FORM_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == FORM_MAPPING_VERSION
    assert result.form_constraint_set.model_version == FORM_MODEL_VERSION
    evaluation = result.form_evaluation
    # В демонстрационном деле письменная форма требуется и соблюдена.
    assert evaluation.form_requirement_satisfied is True
    assert evaluation.transaction_void_for_form is False
    assert evaluation.requires_human_form_assessment is False


def test_form_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.form_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedFormEvidence(
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
            request.model_copy(update={"form_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_form_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.form_evidence

    with pytest.raises(ValueError, match="Form evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "form_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Form evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"form_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "form_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-form-evidence",
                                "synthetic-ru-gk160-434-written-form-model-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_form_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in FormFactSet.model_fields}
    values.update(oral_form_permitted=True, simple_written_form_required=True)
    with pytest.raises(ValidationError, match="Oral form cannot be permitted"):
        FormFactSet(**values)


def test_form_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk158-165-form-framework-v1",
        "synthetic-ru-gk160-434-written-form-model-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_form_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_form_benchmark_suite()
    red_team = run_form_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_FORM_BENCHMARKS) == 12
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_FORM_RED_TEAM_CASES) == 11
    assert red_team.blocked == red_team.total


def test_exported_form_artifact_is_reproducible() -> None:
    fixture = SyntheticFormEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_form_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_form_evaluation_artifact()
