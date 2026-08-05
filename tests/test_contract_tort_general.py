from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source
from causa.institutional.contracts.synthetic_tort_general import (
    SyntheticTortGeneralEvaluationArtifact,
    build_synthetic_tort_general_evaluation_artifact,
)
from causa.institutional.contracts.tort_general import (
    TORT_GENERAL_EVIDENCE_SCHEMA_VERSION,
    TORT_GENERAL_MAPPING_VERSION,
    TORT_GENERAL_MODEL_VERSION,
    ReviewedTortGeneralEvidence,
    TortGeneralFactSet,
)
from causa.institutional.contracts.tort_general_evaluation import (
    SYNTHETIC_TORT_GENERAL_BENCHMARKS,
    SYNTHETIC_TORT_GENERAL_RED_TEAM_CASES,
    run_tort_general_benchmark_suite,
    run_tort_general_red_team_suite,
)


def test_reviewed_tort_general_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.tort_general_evidence_mapping
    assert mapping.schema_version == TORT_GENERAL_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == TORT_GENERAL_MAPPING_VERSION
    assert result.tort_general_constraint_set.model_version == TORT_GENERAL_MODEL_VERSION
    evaluation = result.tort_general_evaluation
    # В демонстрационном деле внедоговорное причинение вреда не устанавливалось.
    assert evaluation.tort_qualified is False
    assert evaluation.requires_human_tort_assessment is False


def test_tort_general_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.tort_general_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedTortGeneralEvidence(
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
            request.model_copy(update={"tort_general_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_tort_general_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.tort_general_evidence

    with pytest.raises(ValueError, match="Tort-general evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "tort_general_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Tort-general evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"tort_general_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "tort_general_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-tort-general-evidence",
                                "synthetic-ru-gk1064-1070-tort-general-grounds-and-liability-for-others-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_tort_general_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in TortGeneralFactSet.model_fields}
    values.update(gross_negligence_reduction_not_applied=True)
    with pytest.raises(ValidationError, match="грубой неосторожности"):
        TortGeneralFactSet(**values)

    scope = {field_name: False for field_name in TortGeneralFactSet.model_fields}
    scope.update(full_compensation_rule_breached=True)
    with pytest.raises(ValidationError, match="возмещении вреда в полном объёме"):
        TortGeneralFactSet(**scope)


def test_tort_general_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1064-1070-tort-general-grounds-and-liability-for-others-v1",
        "synthetic-ru-gk1073-1083-tort-high-risk-source-recourse-and-victim-fault-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_tort_general_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_tort_general_benchmark_suite()
    red_team = run_tort_general_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_TORT_GENERAL_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_TORT_GENERAL_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_tort_general_artifact_is_reproducible() -> None:
    fixture = SyntheticTortGeneralEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_tort_general_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_tort_general_evaluation_artifact()
