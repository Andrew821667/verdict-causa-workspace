from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.forwarding import (
    FORWARDING_EVIDENCE_SCHEMA_VERSION,
    FORWARDING_MAPPING_VERSION,
    FORWARDING_MODEL_VERSION,
    ForwardingFactSet,
    ReviewedForwardingEvidence,
)
from causa.institutional.contracts.forwarding_evaluation import (
    SYNTHETIC_FORWARDING_BENCHMARKS,
    SYNTHETIC_FORWARDING_RED_TEAM_CASES,
    run_forwarding_benchmark_suite,
    run_forwarding_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_forwarding import (
    SyntheticForwardingEvaluationArtifact,
    build_synthetic_forwarding_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_forwarding_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.forwarding_evidence_mapping
    assert mapping.schema_version == FORWARDING_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == FORWARDING_MAPPING_VERSION
    assert result.forwarding_constraint_set.model_version == FORWARDING_MODEL_VERSION
    evaluation = result.forwarding_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о транспортной экспедиции.
    assert evaluation.forwarding_qualified is False
    assert evaluation.forwarding_services_not_performed is False
    assert evaluation.requires_human_forwarding_assessment is False


def test_forwarding_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.forwarding_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedForwardingEvidence(
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
            request.model_copy(update={"forwarding_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_forwarding_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.forwarding_evidence

    with pytest.raises(ValueError, match="Forwarding evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "forwarding_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Forwarding evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"forwarding_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "forwarding_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-forwarding-evidence",
                                "synthetic-ru-gk805-806-forwarding-third-parties-and-withdrawal-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_forwarding_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in ForwardingFactSet.model_fields}
    values.update(forwarder_did_not_report_incomplete_information=True)
    with pytest.raises(ValidationError, match="Несообщение экспедитора о неполноте сведений"):
        ForwardingFactSet(**values)

    withdrawal = {field_name: False for field_name in ForwardingFactSet.model_fields}
    withdrawal.update(withdrawal_losses_not_compensated=True)
    with pytest.raises(ValidationError, match="Невозмещение убытков, вызванных расторжением"):
        ForwardingFactSet(**withdrawal)


def test_forwarding_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk801-804-forwarding-concept-form-and-information-v1",
        "synthetic-ru-gk805-806-forwarding-third-parties-and-withdrawal-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_forwarding_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_forwarding_benchmark_suite()
    red_team = run_forwarding_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_FORWARDING_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_FORWARDING_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_forwarding_artifact_is_reproducible() -> None:
    fixture = SyntheticForwardingEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_forwarding_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_forwarding_evaluation_artifact()
