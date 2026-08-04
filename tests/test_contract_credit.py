from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.credit import (
    CREDIT_EVIDENCE_SCHEMA_VERSION,
    CREDIT_MAPPING_VERSION,
    CREDIT_MODEL_VERSION,
    CreditFactSet,
    ReviewedCreditEvidence,
)
from causa.institutional.contracts.credit_evaluation import (
    SYNTHETIC_CREDIT_BENCHMARKS,
    SYNTHETIC_CREDIT_RED_TEAM_CASES,
    run_credit_benchmark_suite,
    run_credit_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_credit import (
    SyntheticCreditEvaluationArtifact,
    build_synthetic_credit_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_credit_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.credit_evidence_mapping
    assert mapping.schema_version == CREDIT_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == CREDIT_MAPPING_VERSION
    assert result.credit_constraint_set.model_version == CREDIT_MODEL_VERSION
    evaluation = result.credit_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о кредите.
    assert evaluation.credit_qualified is False
    assert evaluation.written_form_nullity is False
    assert evaluation.requires_human_credit_assessment is False


def test_credit_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.credit_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedCreditEvidence(
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
            request.model_copy(update={"credit_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_credit_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.credit_evidence

    with pytest.raises(ValueError, match="Credit evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "credit_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Credit evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"credit_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "credit_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-credit-evidence",
                                "synthetic-ru-gk821-821-1-credit-refusal-and-early-repayment-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_credit_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in CreditFactSet.model_fields}
    values.update(early_repayment_from_citizen_without_statutory_ground=True)
    with pytest.raises(ValidationError, match="Требование досрочного возврата от гражданина"):
        CreditFactSet(**values)


def test_credit_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk819-820-credit-concept-parties-and-form-v1",
        "synthetic-ru-gk821-821-1-credit-refusal-and-early-repayment-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_credit_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_credit_benchmark_suite()
    red_team = run_credit_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_CREDIT_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_CREDIT_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_credit_artifact_is_reproducible() -> None:
    fixture = SyntheticCreditEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_credit_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_credit_evaluation_artifact()
