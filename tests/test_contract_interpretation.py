from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.interpretation import (
    INTERPRETATION_EVIDENCE_SCHEMA_VERSION,
    INTERPRETATION_MAPPING_VERSION,
    INTERPRETATION_MODEL_VERSION,
    InterpretationFactSet,
    ReviewedInterpretationEvidence,
)
from causa.institutional.contracts.interpretation_evaluation import (
    SYNTHETIC_INTERPRETATION_BENCHMARKS,
    SYNTHETIC_INTERPRETATION_RED_TEAM_CASES,
    run_interpretation_benchmark_suite,
    run_interpretation_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_interpretation import (
    SyntheticInterpretationEvaluationArtifact,
    build_synthetic_interpretation_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_interpretation_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.interpretation_evidence_mapping
    assert mapping.schema_version == INTERPRETATION_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == INTERPRETATION_MAPPING_VERSION
    assert result.interpretation_constraint_set.model_version == INTERPRETATION_MODEL_VERSION
    evaluation = result.interpretation_evaluation
    # В демонстрационном деле буквальное значение ясно и согласовано.
    assert evaluation.literal_interpretation_controls is True
    assert evaluation.interpretation_resolved is True
    assert evaluation.requires_human_interpretation_assessment is False


def test_interpretation_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.interpretation_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedInterpretationEvidence(
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
            request.model_copy(update={"interpretation_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_interpretation_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.interpretation_evidence

    with pytest.raises(ValueError, match="Interpretation evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "interpretation_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Interpretation evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"interpretation_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "interpretation_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-interpretation-evidence",
                                "synthetic-ru-gk431-common-intent-model-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_interpretation_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in InterpretationFactSet.model_fields}
    values.update(common_intent_established=True)
    with pytest.raises(ValidationError, match="Common intent cannot be established"):
        InterpretationFactSet(**values)


def test_interpretation_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk431-interpretation-model-v1",
        "synthetic-ru-gk431-common-intent-model-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_interpretation_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_interpretation_benchmark_suite()
    red_team = run_interpretation_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_INTERPRETATION_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_INTERPRETATION_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_interpretation_artifact_is_reproducible() -> None:
    fixture = SyntheticInterpretationEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_interpretation_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_interpretation_evaluation_artifact()
