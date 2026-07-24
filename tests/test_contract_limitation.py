from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.limitation import (
    LIMITATION_EVIDENCE_SCHEMA_VERSION,
    LIMITATION_MAPPING_VERSION,
    LIMITATION_MODEL_VERSION,
    LimitationFactSet,
    ReviewedLimitationEvidence,
)
from causa.institutional.contracts.limitation_evaluation import (
    SYNTHETIC_LIMITATION_BENCHMARKS,
    SYNTHETIC_LIMITATION_RED_TEAM_CASES,
    run_limitation_benchmark_suite,
    run_limitation_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_limitation import (
    SyntheticLimitationEvaluationArtifact,
    build_synthetic_limitation_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_limitation_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.limitation_evidence_mapping
    assert mapping.schema_version == LIMITATION_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == LIMITATION_MAPPING_VERSION
    assert result.limitation_constraint_set.model_version == LIMITATION_MODEL_VERSION
    evaluation = result.limitation_evaluation
    # В демонстрационном деле требование подпадает под давность, течение началось,
    # но трехлетний срок ещё не истёк.
    assert evaluation.limitation_period_started is True
    assert evaluation.limitation_period_expired is False
    assert evaluation.claim_not_subject_to_limitation is False


def test_limitation_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.limitation_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedLimitationEvidence(
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
            request.model_copy(update={"limitation_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_limitation_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.limitation_evidence

    with pytest.raises(ValueError, match="Limitation evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "limitation_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Limitation evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"limitation_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "limitation_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-limitation-evidence",
                                "synthetic-ru-gk202-208-limitation-effects-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_limitation_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in LimitationFactSet.model_fields}
    values.update(special_term_elapsed=True)
    with pytest.raises(ValidationError, match="Special limitation term cannot elapse"):
        LimitationFactSet(**values)


def test_limitation_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk195-200-limitation-framework-v1",
        "synthetic-ru-gk202-208-limitation-effects-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_limitation_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_limitation_benchmark_suite()
    red_team = run_limitation_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_LIMITATION_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_LIMITATION_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_limitation_artifact_is_reproducible() -> None:
    fixture = SyntheticLimitationEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_limitation_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_limitation_evaluation_artifact()
