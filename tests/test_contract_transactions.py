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
from causa.institutional.contracts.synthetic_transactions import (
    SyntheticTransactionsEvaluationArtifact,
    build_synthetic_transactions_evaluation_artifact,
)
from causa.institutional.contracts.transactions import (
    TRANSACTIONS_EVIDENCE_SCHEMA_VERSION,
    TRANSACTIONS_MAPPING_VERSION,
    TRANSACTIONS_MODEL_VERSION,
    ReviewedTransactionsEvidence,
    TransactionsFactSet,
)
from causa.institutional.contracts.transactions_evaluation import (
    SYNTHETIC_TRANSACTIONS_BENCHMARKS,
    SYNTHETIC_TRANSACTIONS_RED_TEAM_CASES,
    run_transactions_benchmark_suite,
    run_transactions_red_team_suite,
)


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


def test_reviewed_transactions_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.transactions_evidence_mapping
    assert mapping.schema_version == TRANSACTIONS_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == TRANSACTIONS_MAPPING_VERSION
    assert result.transactions_constraint_set.model_version == TRANSACTIONS_MODEL_VERSION
    evaluation = result.transactions_evaluation
    # В демонстрационном деле правила о сделках отдельно не заявлялись.
    assert evaluation.transactions_qualified is False
    assert evaluation.requires_human_transactions_assessment is False


def test_transactions_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.transactions_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedTransactionsEvidence(
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
            request.model_copy(update={"transactions_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_transactions_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.transactions_evidence

    with pytest.raises(ValueError, match="Transactions evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "transactions_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Transactions evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"transactions_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "transactions_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-transactions-evidence",
                                "synthetic-ru-gk157-1-consent-to-a-transaction-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_transactions_fact_consistency_is_enforced() -> None:
    silence = {field_name: False for field_name in TransactionsFactSet.model_fields}
    silence.update(silence_treated_as_consent=True)
    with pytest.raises(ValidationError, match="согласие на совершение сделки"):
        TransactionsFactSet(**silence)

    definition = {field_name: False for field_name in TransactionsFactSet.model_fields}
    definition.update(transaction_definition_breached=True)
    with pytest.raises(ValidationError, match="понятия сделки"):
        TransactionsFactSet(**definition)


def test_transactions_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk153-157-transaction-concept-kinds-and-conditions-v1",
        "synthetic-ru-gk157-1-consent-to-a-transaction-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_missing_consent_makes_transaction_challengeable_without_voiding_it() -> None:
    """Сделка без необходимого согласия оспорима, но не ничтожна.

    Слой общих положений применяет статью 173.1 ГК РФ: сделка может быть признана
    недействительной судом, поэтому до такого признания договор сохраняет действие
    и договорные требования остаются исполнимыми (пункт 1 статьи 166 ГК РФ).
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    assert (
        baseline.general_effects_evaluation.transaction_challengeable_for_missing_consent is False
    )
    assert baseline.requires_human_resolution is False

    without_consent = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "transactions_evidence": _flip(
                    request.transactions_evidence,
                    transaction_asserted=True,
                    statutory_consent_not_obtained=True,
                )
            }
        ),
        sources,
    )

    assert without_consent.transactions_evaluation.consent_missing_for_transaction is True
    evaluation = without_consent.general_effects_evaluation
    assert evaluation.transaction_challengeable_for_missing_consent is True
    # Оспоримость не лишает договор действия автоматически.
    assert evaluation.contract_legally_effective is True
    assert evaluation.contractual_claims_enforceable is True
    assert evaluation.institute_conclusions_displaced is False
    # Но вопрос выносится на экспертизу для всего анализа.
    assert without_consent.requires_human_resolution is True


def test_transactions_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_transactions_benchmark_suite()
    red_team = run_transactions_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_TRANSACTIONS_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_TRANSACTIONS_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_transactions_artifact_is_reproducible() -> None:
    fixture = SyntheticTransactionsEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_transactions_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_transactions_evaluation_artifact()
