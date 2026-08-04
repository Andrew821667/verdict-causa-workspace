from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.bank_deposit import (
    BANK_DEPOSIT_EVIDENCE_SCHEMA_VERSION,
    BANK_DEPOSIT_MAPPING_VERSION,
    BANK_DEPOSIT_MODEL_VERSION,
    BankDepositFactSet,
    ReviewedBankDepositEvidence,
)
from causa.institutional.contracts.bank_deposit_evaluation import (
    SYNTHETIC_BANK_DEPOSIT_BENCHMARKS,
    SYNTHETIC_BANK_DEPOSIT_RED_TEAM_CASES,
    run_bank_deposit_benchmark_suite,
    run_bank_deposit_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_bank_deposit import (
    SyntheticBankDepositEvaluationArtifact,
    build_synthetic_bank_deposit_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_bank_deposit_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.bank_deposit_evidence_mapping
    assert mapping.schema_version == BANK_DEPOSIT_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == BANK_DEPOSIT_MAPPING_VERSION
    assert result.bank_deposit_constraint_set.model_version == BANK_DEPOSIT_MODEL_VERSION
    evaluation = result.bank_deposit_evaluation
    # В демонстрационном деле поставка товаров, а не принятие денежной суммы во вклад.
    assert evaluation.bank_deposit_qualified is False
    assert evaluation.requires_human_bank_deposit_assessment is False


def test_bank_deposit_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.bank_deposit_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedBankDepositEvidence(
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
            request.model_copy(update={"bank_deposit_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_bank_deposit_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.bank_deposit_evidence

    with pytest.raises(ValueError, match="Bank-deposit evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "bank_deposit_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Bank-deposit evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"bank_deposit_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "bank_deposit_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-bank-deposit-evidence",
                                "synthetic-ru-gk834-839-bank-deposit-concept-form-and-interest-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_bank_deposit_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in BankDepositFactSet.model_fields}
    values.update(early_repayment_interest_miscalculated=True)
    with pytest.raises(ValidationError, match="Неверный перерасчёт процентов"):
        BankDepositFactSet(**values)

    form = {field_name: False for field_name in BankDepositFactSet.model_fields}
    form.update(deposit_written_form_not_observed=True)
    with pytest.raises(ValidationError, match="Несоблюдение письменной формы"):
        BankDepositFactSet(**form)


def test_bank_deposit_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk834-839-bank-deposit-concept-form-and-interest-v1",
        "synthetic-ru-gk840-844-bank-deposit-security-third-parties-and-documents-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_bank_deposit_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_bank_deposit_benchmark_suite()
    red_team = run_bank_deposit_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_BANK_DEPOSIT_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_BANK_DEPOSIT_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_bank_deposit_artifact_is_reproducible() -> None:
    fixture = SyntheticBankDepositEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_bank_deposit_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_bank_deposit_evaluation_artifact()
