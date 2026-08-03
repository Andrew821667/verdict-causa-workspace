from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.carriage import (
    CARRIAGE_EVIDENCE_SCHEMA_VERSION,
    CARRIAGE_MAPPING_VERSION,
    CARRIAGE_MODEL_VERSION,
    CarriageFactSet,
    ReviewedCarriageEvidence,
)
from causa.institutional.contracts.carriage_evaluation import (
    SYNTHETIC_CARRIAGE_BENCHMARKS,
    SYNTHETIC_CARRIAGE_RED_TEAM_CASES,
    run_carriage_benchmark_suite,
    run_carriage_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_carriage import (
    SyntheticCarriageEvaluationArtifact,
    build_synthetic_carriage_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_carriage_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.carriage_evidence_mapping
    assert mapping.schema_version == CARRIAGE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == CARRIAGE_MAPPING_VERSION
    assert result.carriage_constraint_set.model_version == CARRIAGE_MODEL_VERSION
    evaluation = result.carriage_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о перевозке.
    assert evaluation.carriage_qualified is False
    assert evaluation.cargo_damage_established is False
    assert evaluation.requires_human_carriage_assessment is False


def test_carriage_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.carriage_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedCarriageEvidence(
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
            request.model_copy(update={"carriage_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_carriage_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.carriage_evidence

    with pytest.raises(ValueError, match="Carriage evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "carriage_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Carriage evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"carriage_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "carriage_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-carriage-evidence",
                                "synthetic-ru-gk793-800-carriage-liability-and-claims-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_carriage_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in CarriageFactSet.model_fields}
    values.update(carrier_fault_not_disproved_for_cargo_loss=True)
    with pytest.raises(ValidationError, match="Недоказанность отсутствия вины перевозчика"):
        CarriageFactSet(**values)


def test_carriage_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk784-792-carriage-concept-documents-and-obligations-v1",
        "synthetic-ru-gk793-800-carriage-liability-and-claims-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_carriage_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_carriage_benchmark_suite()
    red_team = run_carriage_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_CARRIAGE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_CARRIAGE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_carriage_artifact_is_reproducible() -> None:
    fixture = SyntheticCarriageEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_carriage_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_carriage_evaluation_artifact()
