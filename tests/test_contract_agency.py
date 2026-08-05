from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.agency import (
    AGENCY_EVIDENCE_SCHEMA_VERSION,
    AGENCY_MAPPING_VERSION,
    AGENCY_MODEL_VERSION,
    AgencyFactSet,
    ReviewedAgencyEvidence,
)
from causa.institutional.contracts.agency_evaluation import (
    SYNTHETIC_AGENCY_BENCHMARKS,
    SYNTHETIC_AGENCY_RED_TEAM_CASES,
    run_agency_benchmark_suite,
    run_agency_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_agency import (
    SyntheticAgencyEvaluationArtifact,
    build_synthetic_agency_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_agency_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.agency_evidence_mapping
    assert mapping.schema_version == AGENCY_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == AGENCY_MAPPING_VERSION
    assert result.agency_constraint_set.model_version == AGENCY_MODEL_VERSION
    evaluation = result.agency_evaluation
    # В демонстрационном деле агентский договор между сторонами не заключался.
    assert evaluation.agency_qualified is False
    assert evaluation.requires_human_agency_assessment is False


def test_agency_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.agency_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedAgencyEvidence(
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
            request.model_copy(update={"agency_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_agency_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.agency_evidence

    with pytest.raises(ValueError, match="Agency evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "agency_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Agency evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"agency_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "agency_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-agency-evidence",
                                "synthetic-ru-gk1005-1008-agency-concept-remuneration-and-reports-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_agency_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in AgencyFactSet.model_fields}
    values.update(restrictions_against_consumers_imposed=True)
    with pytest.raises(ValidationError, match="категории покупателей"):
        AgencyFactSet(**values)

    remuneration = {field_name: False for field_name in AgencyFactSet.model_fields}
    remuneration.update(agency_remuneration_rules_breached=True)
    with pytest.raises(ValidationError, match="агентском вознаграждении"):
        AgencyFactSet(**remuneration)


def test_agency_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1005-1008-agency-concept-remuneration-and-reports-v1",
        "synthetic-ru-gk1009-1011-agency-subagency-termination-and-rules-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_agency_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_agency_benchmark_suite()
    red_team = run_agency_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_AGENCY_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_AGENCY_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_agency_artifact_is_reproducible() -> None:
    fixture = SyntheticAgencyEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_agency_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_agency_evaluation_artifact()
