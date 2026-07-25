from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.freedom import (
    FREEDOM_EVIDENCE_SCHEMA_VERSION,
    FREEDOM_MAPPING_VERSION,
    FREEDOM_MODEL_VERSION,
    FreedomFactSet,
    ReviewedFreedomEvidence,
)
from causa.institutional.contracts.freedom_evaluation import (
    SYNTHETIC_FREEDOM_BENCHMARKS,
    SYNTHETIC_FREEDOM_RED_TEAM_CASES,
    run_freedom_benchmark_suite,
    run_freedom_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_freedom import (
    SyntheticFreedomEvaluationArtifact,
    build_synthetic_freedom_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_freedom_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.freedom_evidence_mapping
    assert mapping.schema_version == FREEDOM_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == FREEDOM_MAPPING_VERSION
    assert result.freedom_constraint_set.model_version == FREEDOM_MODEL_VERSION
    evaluation = result.freedom_evaluation
    # В демонстрационном деле договор заключён свободно, возмезден, цена согласована.
    assert evaluation.contract_conclusion_free is True
    assert evaluation.contract_presumed_onerous is True
    assert evaluation.price_determined is True
    assert evaluation.requires_human_freedom_assessment is False


def test_freedom_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.freedom_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedFreedomEvidence(
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
            request.model_copy(update={"freedom_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_freedom_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.freedom_evidence

    with pytest.raises(ValueError, match="Freedom evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "freedom_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Freedom evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"freedom_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "freedom_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-freedom-evidence",
                                "synthetic-ru-gk423-424-onerousness-and-price-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_freedom_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in FreedomFactSet.model_fields}
    values.update(new_law_given_retroactive_effect=True)
    with pytest.raises(ValidationError, match="Обратная сила невозможна"):
        FreedomFactSet(**values)


def test_freedom_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk421-422-freedom-of-contract-v1",
        "synthetic-ru-gk423-424-onerousness-and-price-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_freedom_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_freedom_benchmark_suite()
    red_team = run_freedom_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_FREEDOM_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_FREEDOM_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_freedom_artifact_is_reproducible() -> None:
    fixture = SyntheticFreedomEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_freedom_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_freedom_evaluation_artifact()
