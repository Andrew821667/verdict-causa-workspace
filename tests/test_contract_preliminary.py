from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.preliminary import (
    PRELIMINARY_EVIDENCE_SCHEMA_VERSION,
    PRELIMINARY_MAPPING_VERSION,
    PRELIMINARY_MODEL_VERSION,
    PreliminaryFactSet,
    ReviewedPreliminaryEvidence,
)
from causa.institutional.contracts.preliminary_evaluation import (
    SYNTHETIC_PRELIMINARY_BENCHMARKS,
    SYNTHETIC_PRELIMINARY_RED_TEAM_CASES,
    run_preliminary_benchmark_suite,
    run_preliminary_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_preliminary import (
    SyntheticPreliminaryEvaluationArtifact,
    build_synthetic_preliminary_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_preliminary_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.preliminary_evidence_mapping
    assert mapping.schema_version == PRELIMINARY_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == PRELIMINARY_MAPPING_VERSION
    assert result.preliminary_constraint_set.model_version == PRELIMINARY_MODEL_VERSION
    evaluation = result.preliminary_evaluation
    # В демонстрационном деле предварительный договор действителен, обязанность заключить активна.
    assert evaluation.preliminary_contract_valid is True
    assert evaluation.conclusion_obligation_active is True
    assert evaluation.requires_human_preliminary_assessment is False


def test_preliminary_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.preliminary_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedPreliminaryEvidence(
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
            request.model_copy(update={"preliminary_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_preliminary_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.preliminary_evidence

    with pytest.raises(ValueError, match="Preliminary evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "preliminary_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Preliminary evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"preliminary_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "preliminary_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-preliminary-evidence",
                                "synthetic-ru-gk429-445-preliminary-compulsion-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_preliminary_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in PreliminaryFactSet.model_fields}
    values.update(demand_to_conclude_made=True)
    with pytest.raises(ValidationError, match="Требование о понуждении"):
        PreliminaryFactSet(**values)


def test_preliminary_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk429-preliminary-framework-v1",
        "synthetic-ru-gk429-445-preliminary-compulsion-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_preliminary_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_preliminary_benchmark_suite()
    red_team = run_preliminary_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_PRELIMINARY_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_PRELIMINARY_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_preliminary_artifact_is_reproducible() -> None:
    fixture = SyntheticPreliminaryEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_preliminary_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_preliminary_evaluation_artifact()
