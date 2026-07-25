from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.representations import (
    REPRESENTATIONS_EVIDENCE_SCHEMA_VERSION,
    REPRESENTATIONS_MAPPING_VERSION,
    REPRESENTATIONS_MODEL_VERSION,
    RepresentationsFactSet,
    ReviewedRepresentationsEvidence,
)
from causa.institutional.contracts.representations_evaluation import (
    SYNTHETIC_REPRESENTATIONS_BENCHMARKS,
    SYNTHETIC_REPRESENTATIONS_RED_TEAM_CASES,
    run_representations_benchmark_suite,
    run_representations_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_representations import (
    SyntheticRepresentationsEvaluationArtifact,
    build_synthetic_representations_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_representations_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.representations_evidence_mapping
    assert mapping.schema_version == REPRESENTATIONS_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == REPRESENTATIONS_MAPPING_VERSION
    assert result.representations_constraint_set.model_version == REPRESENTATIONS_MODEL_VERSION
    evaluation = result.representations_evaluation
    # В демонстрационном деле заверения достоверны, ответственности нет.
    assert evaluation.material_false_representation is False
    assert evaluation.liability_basis_present is False
    assert evaluation.requires_human_representations_assessment is False


def test_representations_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.representations_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedRepresentationsEvidence(
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
            request.model_copy(update={"representations_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_representations_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.representations_evidence

    with pytest.raises(ValueError, match="Representations evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "representations_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Representations evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "representations_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "representations_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-representations-evidence",
                                "synthetic-ru-gk431-2-representations-remedies-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_representations_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in RepresentationsFactSet.model_fields}
    values.update(representation_false=True)
    with pytest.raises(ValidationError, match="без данного заверения"):
        RepresentationsFactSet(**values)


def test_representations_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk431-2-representations-framework-v1",
        "synthetic-ru-gk431-2-representations-remedies-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_representations_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_representations_benchmark_suite()
    red_team = run_representations_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_REPRESENTATIONS_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_REPRESENTATIONS_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_representations_artifact_is_reproducible() -> None:
    fixture = SyntheticRepresentationsEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_representations_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_representations_evaluation_artifact()
