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
from causa.institutional.contracts.synthetic_vehicle_lease import (
    SyntheticVehicleLeaseEvaluationArtifact,
    build_synthetic_vehicle_lease_evaluation_artifact,
)
from causa.institutional.contracts.vehicle_lease import (
    VEHICLE_LEASE_EVIDENCE_SCHEMA_VERSION,
    VEHICLE_LEASE_MAPPING_VERSION,
    VEHICLE_LEASE_MODEL_VERSION,
    ReviewedVehicleLeaseEvidence,
    VehicleLeaseFactSet,
)
from causa.institutional.contracts.vehicle_lease_evaluation import (
    SYNTHETIC_VEHICLE_LEASE_BENCHMARKS,
    SYNTHETIC_VEHICLE_LEASE_RED_TEAM_CASES,
    run_vehicle_lease_benchmark_suite,
    run_vehicle_lease_red_team_suite,
)


def test_reviewed_vehicle_lease_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.vehicle_lease_evidence_mapping
    assert mapping.schema_version == VEHICLE_LEASE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == VEHICLE_LEASE_MAPPING_VERSION
    assert result.vehicle_lease_constraint_set.model_version == VEHICLE_LEASE_MODEL_VERSION
    evaluation = result.vehicle_lease_evaluation
    # В демонстрационном деле спор о поставке товаров, а не об аренде транспортного средства.
    assert evaluation.vehicle_lease_qualified is False
    assert evaluation.crew_service_shortfall is False
    assert evaluation.requires_human_vehicle_lease_assessment is False


def test_vehicle_lease_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.vehicle_lease_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedVehicleLeaseEvidence(
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
            request.model_copy(update={"vehicle_lease_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_vehicle_lease_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.vehicle_lease_evidence

    with pytest.raises(ValueError, match="Vehicle-lease evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "vehicle_lease_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Vehicle-lease evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"vehicle_lease_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "vehicle_lease_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-vehicle-lease-evidence",
                                "synthetic-ru-gk642-649-vehicle-lease-without-crew-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_vehicle_lease_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in VehicleLeaseFactSet.model_fields}
    values.update(crew_service_not_provided=True)
    with pytest.raises(ValidationError, match="только к аренде транспортного средства с"):
        VehicleLeaseFactSet(**values)


def test_vehicle_lease_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk632-641-vehicle-lease-with-crew-v1",
        "synthetic-ru-gk642-649-vehicle-lease-without-crew-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_vehicle_lease_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_vehicle_lease_benchmark_suite()
    red_team = run_vehicle_lease_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_VEHICLE_LEASE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_VEHICLE_LEASE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_vehicle_lease_artifact_is_reproducible() -> None:
    fixture = SyntheticVehicleLeaseEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_vehicle_lease_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_vehicle_lease_evaluation_artifact()
