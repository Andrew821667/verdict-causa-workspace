from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.loan import (
    LOAN_EVIDENCE_SCHEMA_VERSION,
    LOAN_MAPPING_VERSION,
    LOAN_MODEL_VERSION,
    LoanFactSet,
    ReviewedLoanEvidence,
)
from causa.institutional.contracts.loan_evaluation import (
    SYNTHETIC_LOAN_BENCHMARKS,
    SYNTHETIC_LOAN_RED_TEAM_CASES,
    run_loan_benchmark_suite,
    run_loan_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_loan import (
    SyntheticLoanEvaluationArtifact,
    build_synthetic_loan_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_loan_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.loan_evidence_mapping
    assert mapping.schema_version == LOAN_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == LOAN_MAPPING_VERSION
    assert result.loan_constraint_set.model_version == LOAN_MODEL_VERSION
    evaluation = result.loan_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о займе.
    assert evaluation.loan_qualified is False
    assert evaluation.repayment_duty_breached is False
    assert evaluation.requires_human_loan_assessment is False


def test_loan_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.loan_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedLoanEvidence(
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
            request.model_copy(update={"loan_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_loan_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.loan_evidence

    with pytest.raises(ValueError, match="Loan evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "loan_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Loan evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"loan_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "loan_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-loan-evidence",
                                "synthetic-ru-gk812-818-loan-challenge-security-purpose-and-novation-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_loan_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in LoanFactSet.model_fields}
    values.update(late_payment_interest_not_accrued=True)
    with pytest.raises(ValidationError, match="Неначисление процентов за просрочку"):
        LoanFactSet(**values)


def test_loan_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk807-811-loan-concept-form-interest-and-repayment-v1",
        "synthetic-ru-gk812-818-loan-challenge-security-purpose-and-novation-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_loan_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_loan_benchmark_suite()
    red_team = run_loan_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_LOAN_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_LOAN_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_loan_artifact_is_reproducible() -> None:
    fixture = SyntheticLoanEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_loan_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_loan_evaluation_artifact()
