from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.bank_account import (
    BANK_ACCOUNT_EVIDENCE_SCHEMA_VERSION,
    BANK_ACCOUNT_MAPPING_VERSION,
    BANK_ACCOUNT_MODEL_VERSION,
    BankAccountFactSet,
    ReviewedBankAccountEvidence,
)
from causa.institutional.contracts.bank_account_evaluation import (
    SYNTHETIC_BANK_ACCOUNT_BENCHMARKS,
    SYNTHETIC_BANK_ACCOUNT_RED_TEAM_CASES,
    run_bank_account_benchmark_suite,
    run_bank_account_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_bank_account import (
    SyntheticBankAccountEvaluationArtifact,
    build_synthetic_bank_account_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_bank_account_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.bank_account_evidence_mapping
    assert mapping.schema_version == BANK_ACCOUNT_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == BANK_ACCOUNT_MAPPING_VERSION
    assert result.bank_account_constraint_set.model_version == BANK_ACCOUNT_MODEL_VERSION
    evaluation = result.bank_account_evaluation
    # В демонстрационном деле банковский счёт по спорному договору не открывался.
    assert evaluation.bank_account_qualified is False
    assert evaluation.requires_human_bank_account_assessment is False


def test_bank_account_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.bank_account_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedBankAccountEvidence(
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
            request.model_copy(update={"bank_account_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_bank_account_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.bank_account_evidence

    with pytest.raises(ValueError, match="Bank-account evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "bank_account_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Bank-account evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"bank_account_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "bank_account_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-bank-account-evidence",
                                "synthetic-ru-gk845-853-bank-account-concept-operations-and-payment-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_bank_account_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in BankAccountFactSet.model_fields}
    values.update(improper_operation_liability_not_applied=True)
    with pytest.raises(ValidationError, match="Неприменение ответственности банка"):
        BankAccountFactSet(**values)

    debiting = {field_name: False for field_name in BankAccountFactSet.model_fields}
    debiting.update(funds_debited_without_client_order=True)
    with pytest.raises(ValidationError, match="Списание денежных средств"):
        BankAccountFactSet(**debiting)


def test_bank_account_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk845-853-bank-account-concept-operations-and-payment-v1",
        "synthetic-ru-gk854-860-bank-account-debiting-secrecy-and-termination-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_bank_account_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_bank_account_benchmark_suite()
    red_team = run_bank_account_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_BANK_ACCOUNT_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_BANK_ACCOUNT_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_bank_account_artifact_is_reproducible() -> None:
    fixture = SyntheticBankAccountEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_bank_account_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_bank_account_evaluation_artifact()
