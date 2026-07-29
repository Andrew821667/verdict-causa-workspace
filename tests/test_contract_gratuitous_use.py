from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.gratuitous_use import (
    GRATUITOUS_USE_EVIDENCE_SCHEMA_VERSION,
    GRATUITOUS_USE_MAPPING_VERSION,
    GRATUITOUS_USE_MODEL_VERSION,
    GratuitousUseFactSet,
    ReviewedGratuitousUseEvidence,
)
from causa.institutional.contracts.gratuitous_use_evaluation import (
    SYNTHETIC_GRATUITOUS_USE_BENCHMARKS,
    SYNTHETIC_GRATUITOUS_USE_RED_TEAM_CASES,
    run_gratuitous_use_benchmark_suite,
    run_gratuitous_use_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_gratuitous_use import (
    SyntheticGratuitousUseEvaluationArtifact,
    build_synthetic_gratuitous_use_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_gratuitous_use_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.gratuitous_use_evidence_mapping
    assert mapping.schema_version == GRATUITOUS_USE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == GRATUITOUS_USE_MAPPING_VERSION
    assert result.gratuitous_use_constraint_set.model_version == GRATUITOUS_USE_MODEL_VERSION
    evaluation = result.gratuitous_use_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о безвозмездном пользовании.
    assert evaluation.gratuitous_use_qualified is False
    assert evaluation.prohibited_transfer_to_insider is False
    assert evaluation.requires_human_gratuitous_use_assessment is False


def test_gratuitous_use_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.gratuitous_use_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedGratuitousUseEvidence(
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
            request.model_copy(update={"gratuitous_use_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_gratuitous_use_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.gratuitous_use_evidence

    with pytest.raises(ValueError, match="Gratuitous-use evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "gratuitous_use_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Gratuitous-use evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"gratuitous_use_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "gratuitous_use_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-gratuitous-use-evidence",
                                "synthetic-ru-gk695-701-gratuitous-use-maintenance-risk-and-termination-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_gratuitous_use_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in GratuitousUseFactSet.model_fields}
    values.update(lender_is_organization_transferring_to_insider=True)
    with pytest.raises(ValidationError, match="договору безвозмездного пользования"):
        GratuitousUseFactSet(**values)


def test_gratuitous_use_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk689-694-gratuitous-use-concept-limits-and-defects-v1",
        "synthetic-ru-gk695-701-gratuitous-use-maintenance-risk-and-termination-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_gratuitous_use_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_gratuitous_use_benchmark_suite()
    red_team = run_gratuitous_use_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_GRATUITOUS_USE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_GRATUITOUS_USE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_gratuitous_use_artifact_is_reproducible() -> None:
    fixture = SyntheticGratuitousUseEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_gratuitous_use_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_gratuitous_use_evaluation_artifact()
