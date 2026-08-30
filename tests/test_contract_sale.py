from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.fact_consistency import FactConsistencyError
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.sale import (
    SALE_EVIDENCE_SCHEMA_VERSION,
    SALE_MAPPING_VERSION,
    SALE_MODEL_VERSION,
    ReviewedSaleEvidence,
    SaleEvidencePredicate,
    SaleFactSet,
)
from causa.institutional.contracts.sale_evaluation import (
    SYNTHETIC_SALE_ARTICLES_BENCHMARKS,
    SYNTHETIC_SALE_ARTICLES_RED_TEAM_CASES,
    run_sale_benchmark_suite,
    run_sale_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sale import (
    SyntheticSaleEvaluationArtifact,
    build_synthetic_sale_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_sale_replay_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert result.sale_evidence_mapping.schema_version == SALE_EVIDENCE_SCHEMA_VERSION
    assert result.sale_evidence_mapping.mapping_version == SALE_MAPPING_VERSION
    assert result.sale_constraint_set.model_version == SALE_MODEL_VERSION
    assert result.sale_evaluation.sale_contract_qualified is True
    assert result.sale_evaluation.transfer_duty_performed is True
    assert result.sale_evaluation.sale_breach_established is True
    assert result.sale_evaluation.requires_human_sale_assessment is False


def test_sale_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.sale_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedSaleEvidence(
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
            request.model_copy(update={"sale_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_wrong_case_and_factual_sale_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.sale_evidence

    with pytest.raises(ValueError, match="Sale evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "sale_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Sale evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"sale_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "sale_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": ("synthetic-case-supply-1-general-sale-evidence",)
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


@pytest.mark.parametrize(
    ("predicate", "value", "key"),
    [
        (SaleEvidencePredicate.CONTRACT_CONCLUDED, False, "sale_contract_status"),
        (SaleEvidencePredicate.GOODS_TRANSFER_COMPLETED, False, "sale_transfer_status"),
        (SaleEvidencePredicate.DELIVERY_LATE, False, "sale_delay_status"),
        (SaleEvidencePredicate.QUALITY_DEFECT, True, "sale_nonconformity"),
        (SaleEvidencePredicate.LOSS_CLAIMED, True, "sale_loss_claim"),
        (SaleEvidencePredicate.PAYMENT_DUE, True, "sale_payment_due"),
    ],
)
def test_analysis_rejects_sale_status_mismatch(
    predicate: SaleEvidencePredicate,
    value: bool,
    key: str,
) -> None:
    request = build_synthetic_supply_analysis_request()
    assertions = tuple(
        assertion.model_copy(update={"value": value})
        if assertion.predicate == predicate
        else assertion
        for assertion in request.sale_evidence.assertions
    )
    evidence = request.sale_evidence.model_copy(update={"assertions": assertions})

    with pytest.raises(FactConsistencyError) as failure:
        run_reviewed_contract_analysis(
            request.model_copy(update={"sale_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )

    assert key in failure.value.keys


def test_sale_fact_consistency_rejects_late_delivery_without_due_term() -> None:
    values = {field_name: False for field_name in SaleFactSet.model_fields}
    values["delivery_late"] = True

    with pytest.raises(ValidationError, match="due transfer term"):
        SaleFactSet(**values)


def test_sale_sources_have_official_basis_and_review_flag() -> None:
    source_ids = (
        "synthetic-ru-gk454-464-sale-transfer-v1",
        "synthetic-ru-gk465-477-sale-conformity-v1",
        "synthetic-ru-gk478-491-sale-payment-v1",
        "synthetic-ru-vs-review2024-sale-quality-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_vs_review_source_carries_verbatim_text_not_a_paraphrase() -> None:
    """Последний источник пакета, пересаженный с пересказа на текст обзора.

    Прежний пересказ склеивал две вещи: дословный пункт 2 статьи 476 ГК (уже
    источникован отдельно) и настоящую позицию ВС РФ о безрезультатном
    гарантийном ремонте. Ссылка называла сразу три документа («Обзор № 2, 3
    (2024), определение № 301-ЭС23-10631») — выгрузка установила, что это один
    документ и один пункт, а не выбор между обзором № 2 и обзором № 3.
    """
    source = get_synthetic_contract_source("synthetic-ru-vs-review2024-sale-quality-v1")

    assert source.metadata["text_verbatim"] is True
    assert source.metadata["document_slug"] == "vs-review-2-3-2024"
    assert source.metadata["paragraph"] == "17"
    assert "не должен лишаться прав" in source.text
    assert "301-ЭС23-10631" in source.text
    assert "N 2, 3 (2024)" in source.metadata["legal_reference"]


def test_sale_benchmark_and_red_team_cover_articles_454_through_491() -> None:
    benchmark = run_sale_benchmark_suite()
    red_team = run_sale_red_team_suite()

    assert len(SaleEvidencePredicate) == 152
    assert benchmark.total == len(SYNTHETIC_SALE_ARTICLES_BENCHMARKS) == 48
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_SALE_ARTICLES_RED_TEAM_CASES) == 51
    assert red_team.blocked == red_team.total


def test_exported_sale_artifact_is_reproducible() -> None:
    fixture = SyntheticSaleEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_sale_articles_454_491_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_sale_evaluation_artifact()
