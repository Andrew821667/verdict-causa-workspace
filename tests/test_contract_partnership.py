from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.partnership import (
    PARTNERSHIP_EVIDENCE_SCHEMA_VERSION,
    PARTNERSHIP_MAPPING_VERSION,
    PARTNERSHIP_MODEL_VERSION,
    PartnershipFactSet,
    ReviewedPartnershipEvidence,
)
from causa.institutional.contracts.partnership_evaluation import (
    SYNTHETIC_PARTNERSHIP_BENCHMARKS,
    SYNTHETIC_PARTNERSHIP_RED_TEAM_CASES,
    run_partnership_benchmark_suite,
    run_partnership_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_partnership import (
    SyntheticPartnershipEvaluationArtifact,
    build_synthetic_partnership_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_partnership_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.partnership_evidence_mapping
    assert mapping.schema_version == PARTNERSHIP_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == PARTNERSHIP_MAPPING_VERSION
    assert result.partnership_constraint_set.model_version == PARTNERSHIP_MODEL_VERSION
    evaluation = result.partnership_evaluation
    # В демонстрационном деле вклады в общее дело не соединялись.
    assert evaluation.partnership_qualified is False
    assert evaluation.requires_human_partnership_assessment is False


def test_partnership_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.partnership_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedPartnershipEvidence(
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
            request.model_copy(update={"partnership_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_partnership_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.partnership_evidence

    with pytest.raises(ValueError, match="Partnership evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "partnership_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Partnership evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"partnership_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "partnership_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-partnership-evidence",
                                "synthetic-ru-gk1047-1054-partnership-liability-profit-and-termination-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_partnership_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in PartnershipFactSet.model_fields}
    values.update(profit_exclusion_void_not_applied=True)
    with pytest.raises(ValidationError, match="устранении товарища от участия в прибыли"):
        PartnershipFactSet(**values)

    scope = {field_name: False for field_name in PartnershipFactSet.model_fields}
    scope.update(partnership_parties_or_purpose_breached=True)
    with pytest.raises(ValidationError, match="цели совместной деятельности"):
        PartnershipFactSet(**scope)


def test_partnership_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1041-1046-partnership-concept-contributions-and-common-affairs-v1",
        "synthetic-ru-gk1047-1054-partnership-liability-profit-and-termination-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_partnership_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_partnership_benchmark_suite()
    red_team = run_partnership_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_PARTNERSHIP_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_PARTNERSHIP_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_partnership_artifact_is_reproducible() -> None:
    fixture = SyntheticPartnershipEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_partnership_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_partnership_evaluation_artifact()
