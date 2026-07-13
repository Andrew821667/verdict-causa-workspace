from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.supply import (
    SUPPLY_EVIDENCE_SCHEMA_VERSION,
    SUPPLY_MAPPING_VERSION,
    SUPPLY_MODEL_VERSION,
    ReviewedSupplyEvidence,
    SupplyEvidencePredicate,
    SupplyFactSet,
)
from causa.institutional.contracts.supply_evaluation import (
    SYNTHETIC_SUPPLY_ARTICLES_BENCHMARKS,
    SYNTHETIC_SUPPLY_ARTICLES_RED_TEAM_CASES,
    run_supply_benchmark_suite,
    run_supply_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source
from causa.institutional.contracts.synthetic_supply import (
    SyntheticSupplyEvaluationArtifact,
    build_synthetic_supply_evaluation_artifact,
)


def test_reviewed_supply_replay_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert result.supply_evidence_mapping.schema_version == SUPPLY_EVIDENCE_SCHEMA_VERSION
    assert result.supply_evidence_mapping.mapping_version == SUPPLY_MAPPING_VERSION
    assert result.supply_constraint_set.model_version == SUPPLY_MODEL_VERSION
    assert result.supply_evaluation.supply_contract_qualified is True
    assert result.supply_evaluation.acceptance_duties_satisfied is True
    assert result.supply_evaluation.supply_breach_established is True
    assert result.supply_evaluation.supplier_material_breach is False


def test_supply_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.supply_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedSupplyEvidence(
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
            request.model_copy(update={"supply_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_wrong_case_and_factual_supply_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.supply_evidence

    with pytest.raises(ValueError, match="Supply evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "supply_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Supply evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"supply_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "supply_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-special-supply-evidence",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


@pytest.mark.parametrize(
    ("predicate", "value", "message"),
    [
        (SupplyEvidencePredicate.CONTRACT_CONCLUDED, False, "contract status"),
        (SupplyEvidencePredicate.DELIVERY_COMPLETED, False, "delivery status"),
        (SupplyEvidencePredicate.DELIVERY_LATE, False, "delay status"),
        (SupplyEvidencePredicate.QUALITY_DEFECT, True, "nonconformity"),
        (SupplyEvidencePredicate.LOSS_CLAIMED, True, "loss claim"),
        (SupplyEvidencePredicate.PAYMENT_DUE, True, "payment due status"),
    ],
)
def test_analysis_rejects_supply_status_mismatch(
    predicate: SupplyEvidencePredicate,
    value: bool,
    message: str,
) -> None:
    request = build_synthetic_supply_analysis_request()
    assertions = tuple(
        assertion.model_copy(update={"value": value})
        if assertion.predicate == predicate
        else assertion
        for assertion in request.supply_evidence.assertions
    )
    evidence = request.supply_evidence.model_copy(update={"assertions": assertions})

    with pytest.raises(ValueError, match=message):
        run_reviewed_contract_analysis(
            request.model_copy(update={"supply_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )


def test_supply_fact_consistency_rejects_custody_without_lawful_refusal() -> None:
    values = {field_name: False for field_name in SupplyFactSet.model_fields}
    values["goods_preserved"] = True

    with pytest.raises(ValidationError, match="lawful refusal"):
        SupplyFactSet(**values)


def test_supply_sources_have_official_basis_and_review_flag() -> None:
    source_ids = (
        "synthetic-ru-gk506-512-supply-framework-v1",
        "synthetic-ru-gk513-517-supply-acceptance-v1",
        "synthetic-ru-gk518-524-supply-remedies-v1",
        "synthetic-ru-plenum18-supply-guidance-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_supply_benchmark_and_red_team_cover_articles_506_through_524() -> None:
    benchmark = run_supply_benchmark_suite()
    red_team = run_supply_red_team_suite()

    assert len(SupplyEvidencePredicate) == 82
    assert benchmark.total == len(SYNTHETIC_SUPPLY_ARTICLES_BENCHMARKS) == 32
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_SUPPLY_ARTICLES_RED_TEAM_CASES) == 32
    assert red_team.blocked == red_team.total


def test_exported_supply_artifact_is_reproducible() -> None:
    fixture = SyntheticSupplyEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_supply_articles_506_524_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_supply_evaluation_artifact()
