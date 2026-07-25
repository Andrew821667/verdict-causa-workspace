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
from causa.institutional.contracts.synthetic_third_party import (
    SyntheticThirdPartyEvaluationArtifact,
    build_synthetic_third_party_evaluation_artifact,
)
from causa.institutional.contracts.third_party import (
    THIRD_PARTY_EVIDENCE_SCHEMA_VERSION,
    THIRD_PARTY_MAPPING_VERSION,
    THIRD_PARTY_MODEL_VERSION,
    ReviewedThirdPartyEvidence,
    ThirdPartyFactSet,
)
from causa.institutional.contracts.third_party_evaluation import (
    SYNTHETIC_THIRD_PARTY_BENCHMARKS,
    SYNTHETIC_THIRD_PARTY_RED_TEAM_CASES,
    run_third_party_benchmark_suite,
    run_third_party_red_team_suite,
)


def test_reviewed_third_party_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.third_party_evidence_mapping
    assert mapping.schema_version == THIRD_PARTY_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == THIRD_PARTY_MAPPING_VERSION
    assert result.third_party_constraint_set.model_version == THIRD_PARTY_MODEL_VERSION
    evaluation = result.third_party_evaluation
    # В демонстрационном деле договор в пользу третьего лица действителен, право требования есть.
    assert evaluation.beneficiary_contract_valid is True
    assert evaluation.third_party_may_demand_performance is True
    assert evaluation.requires_human_third_party_assessment is False


def test_third_party_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.third_party_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedThirdPartyEvidence(
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
            request.model_copy(update={"third_party_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_third_party_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.third_party_evidence

    with pytest.raises(ValueError, match="Third-party evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "third_party_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Third-party evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"third_party_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "third_party_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-third-party-evidence",
                                "synthetic-ru-gk430-third-party-change-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_third_party_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in ThirdPartyFactSet.model_fields}
    values.update(creditor_reclaims_right=True)
    with pytest.raises(ValidationError, match="после отказа третьего лица"):
        ThirdPartyFactSet(**values)


def test_third_party_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk430-third-party-framework-v1",
        "synthetic-ru-gk430-third-party-change-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_third_party_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_third_party_benchmark_suite()
    red_team = run_third_party_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_THIRD_PARTY_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_THIRD_PARTY_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_third_party_artifact_is_reproducible() -> None:
    fixture = SyntheticThirdPartyEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_third_party_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_third_party_evaluation_artifact()
