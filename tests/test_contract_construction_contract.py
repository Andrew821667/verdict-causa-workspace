from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.construction_contract import (
    CONSTRUCTION_CONTRACT_EVIDENCE_SCHEMA_VERSION,
    CONSTRUCTION_CONTRACT_MAPPING_VERSION,
    CONSTRUCTION_CONTRACT_MODEL_VERSION,
    ConstructionContractFactSet,
    ReviewedConstructionContractEvidence,
)
from causa.institutional.contracts.construction_contract_evaluation import (
    SYNTHETIC_CONSTRUCTION_CONTRACT_BENCHMARKS,
    SYNTHETIC_CONSTRUCTION_CONTRACT_RED_TEAM_CASES,
    run_construction_contract_benchmark_suite,
    run_construction_contract_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_construction_contract import (
    SyntheticConstructionContractEvaluationArtifact,
    build_synthetic_construction_contract_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_construction_contract_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.construction_contract_evidence_mapping
    assert mapping.schema_version == CONSTRUCTION_CONTRACT_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == CONSTRUCTION_CONTRACT_MAPPING_VERSION
    assert (
        result.construction_contract_constraint_set.model_version
        == CONSTRUCTION_CONTRACT_MODEL_VERSION
    )
    evaluation = result.construction_contract_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о строительном подряде.
    assert evaluation.construction_contract_qualified is False
    assert evaluation.construction_quality_breached is False
    assert evaluation.requires_human_construction_contract_assessment is False


def test_construction_contract_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.construction_contract_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedConstructionContractEvidence(
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
            request.model_copy(update={"construction_contract_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_construction_contract_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.construction_contract_evidence

    with pytest.raises(ValueError, match="Construction-contract evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "construction_contract_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Construction-contract evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "construction_contract_evidence": evidence.model_copy(
                        update={"case_id": "other"}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "construction_contract_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-construction-contract-evidence",
                                "synthetic-ru-gk752-757-construction-contract-conservation-acceptance-and-quality-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_construction_contract_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in ConstructionContractFactSet.model_fields}
    values.update(defect_found_within_five_year_period=True)
    with pytest.raises(
        ValidationError, match="Обнаружение недостатка в пределах пятилетнего срока"
    ):
        ConstructionContractFactSet(**values)


def test_construction_contract_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk740-749-construction-contract-concept-documentation-and-duties-v1",
        "synthetic-ru-gk752-757-construction-contract-conservation-acceptance-and-quality-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_construction_contract_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_construction_contract_benchmark_suite()
    red_team = run_construction_contract_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_CONSTRUCTION_CONTRACT_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_CONSTRUCTION_CONTRACT_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_construction_contract_artifact_is_reproducible() -> None:
    fixture = SyntheticConstructionContractEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_construction_contract_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_construction_contract_evaluation_artifact()
