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
from causa.institutional.contracts.synthetic_unjust_enrichment import (
    SyntheticUnjustEnrichmentEvaluationArtifact,
    build_synthetic_unjust_enrichment_evaluation_artifact,
)
from causa.institutional.contracts.unjust_enrichment import (
    UNJUST_ENRICHMENT_EVIDENCE_SCHEMA_VERSION,
    UNJUST_ENRICHMENT_MAPPING_VERSION,
    UNJUST_ENRICHMENT_MODEL_VERSION,
    ReviewedUnjustEnrichmentEvidence,
    UnjustEnrichmentFactSet,
)
from causa.institutional.contracts.unjust_enrichment_evaluation import (
    SYNTHETIC_UNJUST_ENRICHMENT_BENCHMARKS,
    SYNTHETIC_UNJUST_ENRICHMENT_RED_TEAM_CASES,
    run_unjust_enrichment_benchmark_suite,
    run_unjust_enrichment_red_team_suite,
)


def test_reviewed_unjust_enrichment_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.unjust_enrichment_evidence_mapping
    assert mapping.schema_version == UNJUST_ENRICHMENT_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == UNJUST_ENRICHMENT_MAPPING_VERSION
    assert result.unjust_enrichment_constraint_set.model_version == UNJUST_ENRICHMENT_MODEL_VERSION
    evaluation = result.unjust_enrichment_evaluation
    # В демонстрационном деле имущество приобреталось по договору.
    assert evaluation.unjust_enrichment_qualified is False
    assert evaluation.requires_human_unjust_enrichment_assessment is False


def test_unjust_enrichment_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.unjust_enrichment_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedUnjustEnrichmentEvidence(
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
            request.model_copy(update={"unjust_enrichment_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_unjust_enrichment_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.unjust_enrichment_evidence

    with pytest.raises(ValueError, match="Unjust-enrichment evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "unjust_enrichment_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Unjust-enrichment evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "unjust_enrichment_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "unjust_enrichment_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-unjust-enrichment-evidence",
                                "synthetic-ru-gk1102-1105-unjust-enrichment-duty-and-return-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_unjust_enrichment_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in UnjustEnrichmentFactSet.model_fields}
    values.update(non_returnable_enrichment_not_applied=True)
    with pytest.raises(ValidationError, match="не подлежащем возврату"):
        UnjustEnrichmentFactSet(**values)

    scope = {field_name: False for field_name in UnjustEnrichmentFactSet.model_fields}
    scope.update(irrelevance_of_cause_disregarded=True)
    with pytest.raises(ValidationError, match="независимости обязанности возврата"):
        UnjustEnrichmentFactSet(**scope)


def test_unjust_enrichment_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1102-1105-unjust-enrichment-duty-and-return-v1",
        "synthetic-ru-gk1106-1109-unjust-enrichment-income-costs-and-exceptions-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_unjust_enrichment_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_unjust_enrichment_benchmark_suite()
    red_team = run_unjust_enrichment_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_UNJUST_ENRICHMENT_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_UNJUST_ENRICHMENT_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_unjust_enrichment_artifact_is_reproducible() -> None:
    fixture = SyntheticUnjustEnrichmentEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_unjust_enrichment_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_unjust_enrichment_evaluation_artifact()
