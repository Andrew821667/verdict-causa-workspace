from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.insurance_settlement import (
    INSURANCE_SETTLEMENT_EVIDENCE_SCHEMA_VERSION,
    INSURANCE_SETTLEMENT_MAPPING_VERSION,
    INSURANCE_SETTLEMENT_MODEL_VERSION,
    InsuranceSettlementFactSet,
    ReviewedInsuranceSettlementEvidence,
)
from causa.institutional.contracts.insurance_settlement_evaluation import (
    SYNTHETIC_INSURANCE_SETTLEMENT_BENCHMARKS,
    SYNTHETIC_INSURANCE_SETTLEMENT_RED_TEAM_CASES,
    run_insurance_settlement_benchmark_suite,
    run_insurance_settlement_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_insurance_settlement import (
    SyntheticInsuranceSettlementEvaluationArtifact,
    build_synthetic_insurance_settlement_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_insurance_settlement_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.insurance_settlement_evidence_mapping
    assert mapping.schema_version == INSURANCE_SETTLEMENT_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == INSURANCE_SETTLEMENT_MAPPING_VERSION
    assert (
        result.insurance_settlement_constraint_set.model_version
        == INSURANCE_SETTLEMENT_MODEL_VERSION
    )
    evaluation = result.insurance_settlement_evaluation
    # В демонстрационном деле страховой случай не наступал.
    assert evaluation.insurance_settlement_qualified is False
    assert evaluation.requires_human_insurance_settlement_assessment is False


def test_insurance_settlement_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.insurance_settlement_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedInsuranceSettlementEvidence(
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
            request.model_copy(update={"insurance_settlement_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_insurance_settlement_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.insurance_settlement_evidence

    with pytest.raises(ValueError, match="Insurance-settlement evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "insurance_settlement_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Insurance-settlement evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "insurance_settlement_evidence": evidence.model_copy(
                        update={"case_id": "other"}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "insurance_settlement_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-insurance-settlement-evidence",
                                "synthetic-ru-gk944-959-insurance-settlement-disclosure-sum-and-premium-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_insurance_settlement_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in InsuranceSettlementFactSet.model_fields}
    values.update(notice_delay_consequences_not_applied=True)
    with pytest.raises(ValidationError, match="несвоевременного уведомления"):
        InsuranceSettlementFactSet(**values)

    disclosure = {field_name: False for field_name in InsuranceSettlementFactSet.model_fields}
    disclosure.update(material_information_not_disclosed=True)
    with pytest.raises(ValidationError, match="Несообщение существенных сведений"):
        InsuranceSettlementFactSet(**disclosure)


def test_insurance_settlement_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk944-959-insurance-settlement-disclosure-sum-and-premium-v1",
        "synthetic-ru-gk960-970-insurance-settlement-notice-release-and-subrogation-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_insurance_settlement_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_insurance_settlement_benchmark_suite()
    red_team = run_insurance_settlement_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_INSURANCE_SETTLEMENT_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_INSURANCE_SETTLEMENT_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_insurance_settlement_artifact_is_reproducible() -> None:
    fixture = SyntheticInsuranceSettlementEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_insurance_settlement_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_insurance_settlement_evaluation_artifact()
