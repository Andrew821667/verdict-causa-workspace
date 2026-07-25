from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.precontractual import (
    PRECONTRACTUAL_EVIDENCE_SCHEMA_VERSION,
    PRECONTRACTUAL_MAPPING_VERSION,
    PRECONTRACTUAL_MODEL_VERSION,
    PrecontractualFactSet,
    ReviewedPrecontractualEvidence,
)
from causa.institutional.contracts.precontractual_evaluation import (
    SYNTHETIC_PRECONTRACTUAL_BENCHMARKS,
    SYNTHETIC_PRECONTRACTUAL_RED_TEAM_CASES,
    run_precontractual_benchmark_suite,
    run_precontractual_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_precontractual import (
    SyntheticPrecontractualEvaluationArtifact,
    build_synthetic_precontractual_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_precontractual_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.precontractual_evidence_mapping
    assert mapping.schema_version == PRECONTRACTUAL_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == PRECONTRACTUAL_MAPPING_VERSION
    assert result.precontractual_constraint_set.model_version == PRECONTRACTUAL_MODEL_VERSION
    evaluation = result.precontractual_evaluation
    # В демонстрационном деле переговоры велись добросовестно, ответственности нет.
    assert evaluation.bad_faith_negotiation is False
    assert evaluation.precontractual_liability_present is False
    assert evaluation.requires_human_precontractual_assessment is False


def test_precontractual_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.precontractual_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedPrecontractualEvidence(
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
            request.model_copy(update={"precontractual_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_precontractual_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.precontractual_evidence

    with pytest.raises(ValueError, match="Precontractual evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "precontractual_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Precontractual evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"precontractual_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "precontractual_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-precontractual-evidence",
                                "synthetic-ru-gk434-1-precontractual-remedies-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_precontractual_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in PrecontractualFactSet.model_fields}
    values.update(incomplete_or_false_information_provided=True)
    with pytest.raises(ValidationError, match="без переговоров"):
        PrecontractualFactSet(**values)


def test_precontractual_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk434-1-precontractual-framework-v1",
        "synthetic-ru-gk434-1-precontractual-remedies-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_precontractual_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_precontractual_benchmark_suite()
    red_team = run_precontractual_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_PRECONTRACTUAL_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_PRECONTRACTUAL_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_precontractual_artifact_is_reproducible() -> None:
    fixture = SyntheticPrecontractualEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_precontractual_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_precontractual_evaluation_artifact()
