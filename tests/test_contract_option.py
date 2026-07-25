from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.option import (
    OPTION_EVIDENCE_SCHEMA_VERSION,
    OPTION_MAPPING_VERSION,
    OPTION_MODEL_VERSION,
    OptionFactSet,
    ReviewedOptionEvidence,
)
from causa.institutional.contracts.option_evaluation import (
    SYNTHETIC_OPTION_BENCHMARKS,
    SYNTHETIC_OPTION_RED_TEAM_CASES,
    run_option_benchmark_suite,
    run_option_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_option import (
    SyntheticOptionEvaluationArtifact,
    build_synthetic_option_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_option_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.option_evidence_mapping
    assert mapping.schema_version == OPTION_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == OPTION_MAPPING_VERSION
    assert result.option_constraint_set.model_version == OPTION_MODEL_VERSION
    evaluation = result.option_evaluation
    # В демонстрационном деле опцион действителен и акцептован в срок.
    assert evaluation.option_offer_valid is True
    assert evaluation.main_contract_formed_by_option is True
    assert evaluation.requires_human_option_assessment is False


def test_option_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.option_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedOptionEvidence(
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
            request.model_copy(update={"option_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_option_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.option_evidence

    with pytest.raises(ValueError, match="Option evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "option_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Option evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"option_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "option_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-option-evidence",
                                "synthetic-ru-gk429-3-option-contract-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_option_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in OptionFactSet.model_fields}
    values.update(option_acceptance_within_term=True)
    with pytest.raises(ValidationError, match="без предоставленного опциона"):
        OptionFactSet(**values)


def test_option_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk429-2-option-framework-v1",
        "synthetic-ru-gk429-3-option-contract-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_option_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_option_benchmark_suite()
    red_team = run_option_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_OPTION_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_OPTION_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_option_artifact_is_reproducible() -> None:
    fixture = SyntheticOptionEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_option_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_option_evaluation_artifact()
