from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.commercial_credit import (
    COMMERCIAL_CREDIT_EVIDENCE_SCHEMA_VERSION,
    COMMERCIAL_CREDIT_MAPPING_VERSION,
    COMMERCIAL_CREDIT_MODEL_VERSION,
    CommercialCreditFactSet,
    ReviewedCommercialCreditEvidence,
)
from causa.institutional.contracts.commercial_credit_evaluation import (
    SYNTHETIC_COMMERCIAL_CREDIT_BENCHMARKS,
    SYNTHETIC_COMMERCIAL_CREDIT_RED_TEAM_CASES,
    run_commercial_credit_benchmark_suite,
    run_commercial_credit_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_commercial_credit import (
    SyntheticCommercialCreditEvaluationArtifact,
    build_synthetic_commercial_credit_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_commercial_credit_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.commercial_credit_evidence_mapping
    assert mapping.schema_version == COMMERCIAL_CREDIT_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == COMMERCIAL_CREDIT_MAPPING_VERSION
    assert result.commercial_credit_constraint_set.model_version == COMMERCIAL_CREDIT_MODEL_VERSION
    evaluation = result.commercial_credit_evaluation
    # В демонстрационном деле поставка с единовременной оплатой без кредитных условий.
    assert evaluation.goods_credit_qualified is False
    assert evaluation.commercial_credit_qualified is False
    assert evaluation.requires_human_commercial_credit_assessment is False


def test_commercial_credit_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.commercial_credit_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedCommercialCreditEvidence(
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
            request.model_copy(update={"commercial_credit_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_commercial_credit_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.commercial_credit_evidence

    with pytest.raises(ValueError, match="Commercial-credit evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "commercial_credit_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Commercial-credit evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "commercial_credit_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "commercial_credit_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-commercial-credit-evidence",
                                "synthetic-ru-gk823-commercial-credit-forms-and-applicable-rules-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_commercial_credit_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in CommercialCreditFactSet.model_fields}
    values.update(goods_credit_items_not_provided=True)
    with pytest.raises(ValidationError, match="Непредоставление вещей"):
        CommercialCreditFactSet(**values)

    commercial = {field_name: False for field_name in CommercialCreditFactSet.model_fields}
    commercial.update(commercial_credit_terms_not_agreed_in_main_contract=True)
    with pytest.raises(ValidationError, match="Несогласование условий коммерческого кредита"):
        CommercialCreditFactSet(**commercial)


def test_commercial_credit_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk822-goods-credit-concept-and-sale-rules-v1",
        "synthetic-ru-gk823-commercial-credit-forms-and-applicable-rules-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_commercial_credit_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_commercial_credit_benchmark_suite()
    red_team = run_commercial_credit_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_COMMERCIAL_CREDIT_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_COMMERCIAL_CREDIT_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_commercial_credit_artifact_is_reproducible() -> None:
    fixture = SyntheticCommercialCreditEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_commercial_credit_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_commercial_credit_evaluation_artifact()
