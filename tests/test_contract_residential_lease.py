from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.residential_lease import (
    RESIDENTIAL_LEASE_EVIDENCE_SCHEMA_VERSION,
    RESIDENTIAL_LEASE_MAPPING_VERSION,
    RESIDENTIAL_LEASE_MODEL_VERSION,
    ResidentialLeaseFactSet,
    ReviewedResidentialLeaseEvidence,
)
from causa.institutional.contracts.residential_lease_evaluation import (
    SYNTHETIC_RESIDENTIAL_LEASE_BENCHMARKS,
    SYNTHETIC_RESIDENTIAL_LEASE_RED_TEAM_CASES,
    run_residential_lease_benchmark_suite,
    run_residential_lease_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_residential_lease import (
    SyntheticResidentialLeaseEvaluationArtifact,
    build_synthetic_residential_lease_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_residential_lease_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.residential_lease_evidence_mapping
    assert mapping.schema_version == RESIDENTIAL_LEASE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == RESIDENTIAL_LEASE_MAPPING_VERSION
    assert result.residential_lease_constraint_set.model_version == RESIDENTIAL_LEASE_MODEL_VERSION
    evaluation = result.residential_lease_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о найме жилого помещения.
    assert evaluation.residential_lease_qualified is False
    assert evaluation.extrajudicial_termination_invalid is False
    assert evaluation.requires_human_residential_lease_assessment is False


def test_residential_lease_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.residential_lease_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedResidentialLeaseEvidence(
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
            request.model_copy(update={"residential_lease_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_residential_lease_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.residential_lease_evidence

    with pytest.raises(ValueError, match="Residential-lease evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "residential_lease_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Residential-lease evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "residential_lease_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "residential_lease_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-residential-lease-evidence",
                                "synthetic-ru-gk682-688-residential-lease-rent-renewal-and-termination-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_residential_lease_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in ResidentialLeaseFactSet.model_fields}
    values.update(
        renewal_offer_not_made_before_expiry=True,
        short_term_lease_up_to_one_year=True,
    )
    with pytest.raises(ValidationError, match="краткосрочному найму"):
        ResidentialLeaseFactSet(**values)

    values = {field_name: False for field_name in ResidentialLeaseFactSet.model_fields}
    values.update(tenant_denied_remedy_period=True)
    with pytest.raises(ValidationError, match="нарушения нанимателем условий пользования"):
        ResidentialLeaseFactSet(**values)


def test_residential_lease_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk671-678-residential-lease-concept-form-and-duties-v1",
        "synthetic-ru-gk682-688-residential-lease-rent-renewal-and-termination-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_residential_lease_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_residential_lease_benchmark_suite()
    red_team = run_residential_lease_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_RESIDENTIAL_LEASE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_RESIDENTIAL_LEASE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_residential_lease_artifact_is_reproducible() -> None:
    fixture = SyntheticResidentialLeaseEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_residential_lease_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_residential_lease_evaluation_artifact()
