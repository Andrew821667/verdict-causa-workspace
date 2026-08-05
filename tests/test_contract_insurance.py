from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.insurance import (
    INSURANCE_EVIDENCE_SCHEMA_VERSION,
    INSURANCE_MAPPING_VERSION,
    INSURANCE_MODEL_VERSION,
    InsuranceFactSet,
    ReviewedInsuranceEvidence,
)
from causa.institutional.contracts.insurance_evaluation import (
    SYNTHETIC_INSURANCE_BENCHMARKS,
    SYNTHETIC_INSURANCE_RED_TEAM_CASES,
    run_insurance_benchmark_suite,
    run_insurance_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_insurance import (
    SyntheticInsuranceEvaluationArtifact,
    build_synthetic_insurance_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_insurance_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.insurance_evidence_mapping
    assert mapping.schema_version == INSURANCE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == INSURANCE_MAPPING_VERSION
    assert result.insurance_constraint_set.model_version == INSURANCE_MODEL_VERSION
    evaluation = result.insurance_evaluation
    # В демонстрационном деле договор страхования сторонами не заключался.
    assert evaluation.insurance_qualified is False
    assert evaluation.requires_human_insurance_assessment is False


def test_insurance_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.insurance_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedInsuranceEvidence(
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
            request.model_copy(update={"insurance_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_insurance_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.insurance_evidence

    with pytest.raises(ValueError, match="Insurance evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "insurance_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Insurance evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"insurance_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "insurance_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-insurance-evidence",
                                "synthetic-ru-gk927-938-insurance-forms-interests-and-parties-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_insurance_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in InsuranceFactSet.model_fields}
    values.update(insurance_rules_application_breached=True)
    with pytest.raises(ValidationError, match="применения правил страхования"):
        InsuranceFactSet(**values)

    form = {field_name: False for field_name in InsuranceFactSet.model_fields}
    form.update(insurance_written_form_not_observed=True)
    with pytest.raises(ValidationError, match="Несоблюдение письменной формы"):
        InsuranceFactSet(**form)


def test_insurance_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk927-938-insurance-forms-interests-and-parties-v1",
        "synthetic-ru-gk939-943-insurance-contract-form-and-terms-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_insurance_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_insurance_benchmark_suite()
    red_team = run_insurance_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_INSURANCE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_INSURANCE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_insurance_artifact_is_reproducible() -> None:
    fixture = SyntheticInsuranceEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_insurance_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_insurance_evaluation_artifact()
