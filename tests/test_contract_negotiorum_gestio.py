from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.negotiorum_gestio import (
    NEGOTIORUM_GESTIO_EVIDENCE_SCHEMA_VERSION,
    NEGOTIORUM_GESTIO_MAPPING_VERSION,
    NEGOTIORUM_GESTIO_MODEL_VERSION,
    NegotiorumGestioFactSet,
    ReviewedNegotiorumGestioEvidence,
)
from causa.institutional.contracts.negotiorum_gestio_evaluation import (
    SYNTHETIC_NEGOTIORUM_GESTIO_BENCHMARKS,
    SYNTHETIC_NEGOTIORUM_GESTIO_RED_TEAM_CASES,
    run_negotiorum_gestio_benchmark_suite,
    run_negotiorum_gestio_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_negotiorum_gestio import (
    SyntheticNegotiorumGestioEvaluationArtifact,
    build_synthetic_negotiorum_gestio_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_negotiorum_gestio_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.negotiorum_gestio_evidence_mapping
    assert mapping.schema_version == NEGOTIORUM_GESTIO_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == NEGOTIORUM_GESTIO_MAPPING_VERSION
    assert result.negotiorum_gestio_constraint_set.model_version == NEGOTIORUM_GESTIO_MODEL_VERSION
    evaluation = result.negotiorum_gestio_evaluation
    # В демонстрационном деле стороны действовали по договору поставки.
    assert evaluation.negotiorum_gestio_qualified is False
    assert evaluation.requires_human_negotiorum_gestio_assessment is False


def test_negotiorum_gestio_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.negotiorum_gestio_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedNegotiorumGestioEvidence(
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
            request.model_copy(update={"negotiorum_gestio_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_negotiorum_gestio_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.negotiorum_gestio_evidence

    with pytest.raises(ValueError, match="Negotiorum-gestio evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "negotiorum_gestio_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Negotiorum-gestio evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "negotiorum_gestio_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "negotiorum_gestio_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-negotiorum-gestio-evidence",
                                "synthetic-ru-gk980-983-gestio-conditions-notice-and-approval-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_negotiorum_gestio_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in NegotiorumGestioFactSet.model_fields}
    values.update(notice_waiting_duty_breached=True)
    with pytest.raises(ValidationError, match="выждать решение"):
        NegotiorumGestioFactSet(**values)

    remuneration = {field_name: False for field_name in NegotiorumGestioFactSet.model_fields}
    remuneration.update(remuneration_rules_breached=True)
    with pytest.raises(ValidationError, match="о вознаграждении"):
        NegotiorumGestioFactSet(**remuneration)


def test_negotiorum_gestio_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk980-983-gestio-conditions-notice-and-approval-v1",
        "synthetic-ru-gk984-989-gestio-expenses-remuneration-and-reporting-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_negotiorum_gestio_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_negotiorum_gestio_benchmark_suite()
    red_team = run_negotiorum_gestio_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_NEGOTIORUM_GESTIO_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_NEGOTIORUM_GESTIO_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_negotiorum_gestio_artifact_is_reproducible() -> None:
    fixture = SyntheticNegotiorumGestioEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_negotiorum_gestio_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_negotiorum_gestio_evaluation_artifact()
