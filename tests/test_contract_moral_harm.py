from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.moral_harm import (
    MORAL_HARM_EVIDENCE_SCHEMA_VERSION,
    MORAL_HARM_MAPPING_VERSION,
    MORAL_HARM_MODEL_VERSION,
    MoralHarmFactSet,
    ReviewedMoralHarmEvidence,
)
from causa.institutional.contracts.moral_harm_evaluation import (
    SYNTHETIC_MORAL_HARM_BENCHMARKS,
    SYNTHETIC_MORAL_HARM_RED_TEAM_CASES,
    run_moral_harm_benchmark_suite,
    run_moral_harm_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_moral_harm import (
    SyntheticMoralHarmEvaluationArtifact,
    build_synthetic_moral_harm_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_moral_harm_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.moral_harm_evidence_mapping
    assert mapping.schema_version == MORAL_HARM_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == MORAL_HARM_MAPPING_VERSION
    assert result.moral_harm_constraint_set.model_version == MORAL_HARM_MODEL_VERSION
    evaluation = result.moral_harm_evaluation
    # В демонстрационном деле требование о компенсации морального вреда не заявлялось.
    assert evaluation.moral_harm_qualified is False
    assert evaluation.requires_human_moral_harm_assessment is False


def test_moral_harm_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.moral_harm_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedMoralHarmEvidence(
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
            request.model_copy(update={"moral_harm_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_moral_harm_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.moral_harm_evidence

    with pytest.raises(ValueError, match="Moral-harm evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "moral_harm_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Moral-harm evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"moral_harm_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "moral_harm_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-moral-harm-evidence",
                                "synthetic-ru-gk1101-moral-harm-form-and-amount-of-compensation-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_moral_harm_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in MoralHarmFactSet.model_fields}
    values.update(victim_individual_features_disregarded=True)
    with pytest.raises(ValidationError, match="размера компенсации морального вреда"):
        MoralHarmFactSet(**values)

    scope = {field_name: False for field_name in MoralHarmFactSet.model_fields}
    scope.update(non_material_benefits_scope_breached=True)
    with pytest.raises(ValidationError, match="посягательстве на нематериальные блага"):
        MoralHarmFactSet(**scope)


def test_moral_harm_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1099-1100-moral-harm-grounds-and-no-fault-cases-v1",
        "synthetic-ru-gk1101-moral-harm-form-and-amount-of-compensation-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_moral_harm_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_moral_harm_benchmark_suite()
    red_team = run_moral_harm_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_MORAL_HARM_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_MORAL_HARM_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_moral_harm_artifact_is_reproducible() -> None:
    fixture = SyntheticMoralHarmEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_moral_harm_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_moral_harm_evaluation_artifact()
