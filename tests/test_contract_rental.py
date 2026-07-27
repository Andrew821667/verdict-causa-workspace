from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.rental import (
    RENTAL_EVIDENCE_SCHEMA_VERSION,
    RENTAL_MAPPING_VERSION,
    RENTAL_MODEL_VERSION,
    RentalFactSet,
    ReviewedRentalEvidence,
)
from causa.institutional.contracts.rental_evaluation import (
    SYNTHETIC_RENTAL_BENCHMARKS,
    SYNTHETIC_RENTAL_RED_TEAM_CASES,
    run_rental_benchmark_suite,
    run_rental_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_rental import (
    SyntheticRentalEvaluationArtifact,
    build_synthetic_rental_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_rental_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.rental_evidence_mapping
    assert mapping.schema_version == RENTAL_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == RENTAL_MAPPING_VERSION
    assert result.rental_constraint_set.model_version == RENTAL_MODEL_VERSION
    evaluation = result.rental_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о прокате.
    assert evaluation.rental_qualified is False
    assert evaluation.transfer_restriction_violated is False
    assert evaluation.requires_human_rental_assessment is False


def test_rental_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.rental_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedRentalEvidence(
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
            request.model_copy(update={"rental_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_rental_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.rental_evidence

    with pytest.raises(ValueError, match="Rental evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "rental_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Rental evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"rental_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "rental_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-rental-evidence",
                                "synthetic-ru-gk629-631-rental-defects-payment-and-repair-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_rental_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in RentalFactSet.model_fields}
    values.update(defect_from_tenant_misuse=True)
    with pytest.raises(ValidationError, match="Нарушение арендатором правил эксплуатации"):
        RentalFactSet(**values)

    values = {field_name: False for field_name in RentalFactSet.model_fields}
    values.update(lessor_failed_to_remedy_defect=True)
    with pytest.raises(ValidationError, match="Неустранение недостатка"):
        RentalFactSet(**values)

    values = {field_name: False for field_name in RentalFactSet.model_fields}
    values.update(
        defect_present=True,
        defect_from_tenant_misuse=True,
        lessor_failed_to_remedy_defect=True,
    )
    with pytest.raises(ValidationError, match="за счёт арендодателя не применяется"):
        RentalFactSet(**values)


def test_rental_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk626-628-rental-concept-form-and-term-v1",
        "synthetic-ru-gk629-631-rental-defects-payment-and-repair-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_rental_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_rental_benchmark_suite()
    red_team = run_rental_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_RENTAL_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_RENTAL_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_rental_artifact_is_reproducible() -> None:
    fixture = SyntheticRentalEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_rental_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_rental_evaluation_artifact()
