from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.commission import (
    COMMISSION_EVIDENCE_SCHEMA_VERSION,
    COMMISSION_MAPPING_VERSION,
    COMMISSION_MODEL_VERSION,
    CommissionFactSet,
    ReviewedCommissionEvidence,
)
from causa.institutional.contracts.commission_evaluation import (
    SYNTHETIC_COMMISSION_BENCHMARKS,
    SYNTHETIC_COMMISSION_RED_TEAM_CASES,
    run_commission_benchmark_suite,
    run_commission_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_commission import (
    SyntheticCommissionEvaluationArtifact,
    build_synthetic_commission_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_commission_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.commission_evidence_mapping
    assert mapping.schema_version == COMMISSION_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == COMMISSION_MAPPING_VERSION
    assert result.commission_constraint_set.model_version == COMMISSION_MODEL_VERSION
    evaluation = result.commission_evaluation
    # В демонстрационном деле договор комиссии между сторонами не заключался.
    assert evaluation.commission_qualified is False
    assert evaluation.requires_human_commission_assessment is False


def test_commission_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.commission_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedCommissionEvidence(
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
            request.model_copy(update={"commission_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_commission_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.commission_evidence

    with pytest.raises(ValueError, match="Commission evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "commission_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Commission evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"commission_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "commission_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-commission-evidence",
                                "synthetic-ru-gk990-998-commission-concept-execution-and-property-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_commission_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in CommissionFactSet.model_fields}
    values.update(deviation_notice_not_given=True)
    with pytest.raises(ValidationError, match="Неуведомление об отступлении"):
        CommissionFactSet(**values)

    remuneration = {field_name: False for field_name in CommissionFactSet.model_fields}
    remuneration.update(commission_remuneration_rules_breached=True)
    with pytest.raises(ValidationError, match="комиссионном вознаграждении"):
        CommissionFactSet(**remuneration)


def test_commission_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk990-998-commission-concept-execution-and-property-v1",
        "synthetic-ru-gk999-1004-commission-report-duties-and-termination-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_commission_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_commission_benchmark_suite()
    red_team = run_commission_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_COMMISSION_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_COMMISSION_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_commission_artifact_is_reproducible() -> None:
    fixture = SyntheticCommissionEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_commission_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_commission_evaluation_artifact()
