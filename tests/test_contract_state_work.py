from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.state_work import (
    STATE_WORK_EVIDENCE_SCHEMA_VERSION,
    STATE_WORK_MAPPING_VERSION,
    STATE_WORK_MODEL_VERSION,
    ReviewedStateWorkEvidence,
    StateWorkFactSet,
)
from causa.institutional.contracts.state_work_evaluation import (
    SYNTHETIC_STATE_WORK_BENCHMARKS,
    SYNTHETIC_STATE_WORK_RED_TEAM_CASES,
    run_state_work_benchmark_suite,
    run_state_work_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source
from causa.institutional.contracts.synthetic_state_work import (
    SyntheticStateWorkEvaluationArtifact,
    build_synthetic_state_work_evaluation_artifact,
)


def test_reviewed_state_work_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.state_work_evidence_mapping
    assert mapping.schema_version == STATE_WORK_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == STATE_WORK_MAPPING_VERSION
    assert result.state_work_constraint_set.model_version == STATE_WORK_MODEL_VERSION
    evaluation = result.state_work_evaluation
    # В демонстрационном деле спор о поставке товаров между коммерческими организациями.
    assert evaluation.state_work_qualified is False
    assert evaluation.state_contract_requirement_breached is False
    assert evaluation.requires_human_state_work_assessment is False


def test_state_work_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.state_work_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedStateWorkEvidence(
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
            request.model_copy(update={"state_work_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_state_work_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.state_work_evidence

    with pytest.raises(ValueError, match="State-work evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "state_work_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="State-work evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"state_work_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "state_work_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-state-work-evidence",
                                "synthetic-ru-gk767-768-state-work-budget-changes-and-special-law-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_state_work_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in StateWorkFactSet.model_fields}
    values.update(contractor_losses_from_changed_terms_not_compensated=True)
    with pytest.raises(ValidationError, match="Невозмещение убытков"):
        StateWorkFactSet(**values)


def test_state_work_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk763-766-state-work-contract-basis-parties-and-terms-v1",
        "synthetic-ru-gk767-768-state-work-budget-changes-and-special-law-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_state_work_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_state_work_benchmark_suite()
    red_team = run_state_work_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_STATE_WORK_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_STATE_WORK_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_state_work_artifact_is_reproducible() -> None:
    fixture = SyntheticStateWorkEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_state_work_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_state_work_evaluation_artifact()
