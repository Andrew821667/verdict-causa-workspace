from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.contractation import (
    CONTRACTATION_EVIDENCE_SCHEMA_VERSION,
    CONTRACTATION_MAPPING_VERSION,
    CONTRACTATION_MODEL_VERSION,
    ContractationFactSet,
    ReviewedContractationEvidence,
)
from causa.institutional.contracts.contractation_evaluation import (
    SYNTHETIC_CONTRACTATION_BENCHMARKS,
    SYNTHETIC_CONTRACTATION_RED_TEAM_CASES,
    run_contractation_benchmark_suite,
    run_contractation_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_contractation import (
    SyntheticContractationEvaluationArtifact,
    build_synthetic_contractation_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_contractation_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.contractation_evidence_mapping
    assert mapping.schema_version == CONTRACTATION_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == CONTRACTATION_MAPPING_VERSION
    assert result.contractation_constraint_set.model_version == CONTRACTATION_MODEL_VERSION
    evaluation = result.contractation_evaluation
    # В демонстрационном деле поставка коммерческая, не сельскохозяйственная контрактация.
    assert evaluation.contractation_qualified is False
    assert evaluation.producer_delivery_duty_met is False
    assert evaluation.requires_human_contractation_assessment is False


def test_contractation_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.contractation_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedContractationEvidence(
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
            request.model_copy(update={"contractation_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_contractation_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.contractation_evidence

    with pytest.raises(ValueError, match="Contractation evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "contractation_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Contractation evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"contractation_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "contractation_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-contractation-evidence",
                                "synthetic-ru-gk537-538-contractation-duties-and-liability-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_contractation_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in ContractationFactSet.model_fields}
    values.update(producer_at_fault=True)
    with pytest.raises(ValidationError, match="Вина производителя учитывается только"):
        ContractationFactSet(**values)


def test_contractation_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk535-536-contractation-concept-v1",
        "synthetic-ru-gk537-538-contractation-duties-and-liability-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_contractation_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_contractation_benchmark_suite()
    red_team = run_contractation_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_CONTRACTATION_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_CONTRACTATION_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_contractation_artifact_is_reproducible() -> None:
    fixture = SyntheticContractationEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_contractation_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_contractation_evaluation_artifact()
