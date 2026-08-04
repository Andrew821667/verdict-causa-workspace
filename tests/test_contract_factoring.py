from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.factoring import (
    FACTORING_EVIDENCE_SCHEMA_VERSION,
    FACTORING_MAPPING_VERSION,
    FACTORING_MODEL_VERSION,
    FactoringFactSet,
    ReviewedFactoringEvidence,
)
from causa.institutional.contracts.factoring_evaluation import (
    SYNTHETIC_FACTORING_BENCHMARKS,
    SYNTHETIC_FACTORING_RED_TEAM_CASES,
    run_factoring_benchmark_suite,
    run_factoring_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_factoring import (
    SyntheticFactoringEvaluationArtifact,
    build_synthetic_factoring_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_factoring_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.factoring_evidence_mapping
    assert mapping.schema_version == FACTORING_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == FACTORING_MAPPING_VERSION
    assert result.factoring_constraint_set.model_version == FACTORING_MODEL_VERSION
    evaluation = result.factoring_evaluation
    # В демонстрационном деле поставка без финансирования под уступку требования.
    assert evaluation.factoring_qualified is False
    assert evaluation.requires_human_factoring_assessment is False


def test_factoring_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.factoring_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedFactoringEvidence(
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
            request.model_copy(update={"factoring_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_factoring_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.factoring_evidence

    with pytest.raises(ValueError, match="Factoring evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "factoring_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Factoring evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"factoring_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "factoring_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-factoring-evidence",
                                "synthetic-ru-gk824-829-factoring-concept-parties-and-assignment-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_factoring_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in FactoringFactSet.model_fields}
    values.update(debtor_set_off_claims_disregarded=True)
    with pytest.raises(ValidationError, match="Игнорирование зачётных требований"):
        FactoringFactSet(**values)

    identification = {field_name: False for field_name in FactoringFactSet.model_fields}
    identification.update(assigned_claim_not_identified=True)
    with pytest.raises(ValidationError, match="Неопределённость уступаемого требования"):
        FactoringFactSet(**identification)


def test_factoring_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk824-829-factoring-concept-parties-and-assignment-v1",
        "synthetic-ru-gk830-833-factoring-debtor-performance-and-settlements-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_factoring_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_factoring_benchmark_suite()
    red_team = run_factoring_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_FACTORING_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_FACTORING_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_factoring_artifact_is_reproducible() -> None:
    fixture = SyntheticFactoringEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_factoring_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_factoring_evaluation_artifact()
