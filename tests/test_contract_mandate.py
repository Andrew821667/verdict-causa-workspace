from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.mandate import (
    MANDATE_EVIDENCE_SCHEMA_VERSION,
    MANDATE_MAPPING_VERSION,
    MANDATE_MODEL_VERSION,
    MandateFactSet,
    ReviewedMandateEvidence,
)
from causa.institutional.contracts.mandate_evaluation import (
    SYNTHETIC_MANDATE_BENCHMARKS,
    SYNTHETIC_MANDATE_RED_TEAM_CASES,
    run_mandate_benchmark_suite,
    run_mandate_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_mandate import (
    SyntheticMandateEvaluationArtifact,
    build_synthetic_mandate_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_mandate_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.mandate_evidence_mapping
    assert mapping.schema_version == MANDATE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == MANDATE_MAPPING_VERSION
    assert result.mandate_constraint_set.model_version == MANDATE_MODEL_VERSION
    evaluation = result.mandate_evaluation
    # В демонстрационном деле договор поручения между сторонами не заключался.
    assert evaluation.mandate_qualified is False
    assert evaluation.requires_human_mandate_assessment is False


def test_mandate_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.mandate_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedMandateEvidence(
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
            request.model_copy(update={"mandate_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_mandate_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.mandate_evidence

    with pytest.raises(ValueError, match="Mandate evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "mandate_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Mandate evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"mandate_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "mandate_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-mandate-evidence",
                                "synthetic-ru-gk971-976-mandate-concept-instructions-and-duties-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_mandate_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in MandateFactSet.model_fields}
    values.update(deviation_notice_not_given=True)
    with pytest.raises(ValidationError, match="Неуведомление об отступлении"):
        MandateFactSet(**values)

    remuneration = {field_name: False for field_name in MandateFactSet.model_fields}
    remuneration.update(mandate_remuneration_rules_breached=True)
    with pytest.raises(ValidationError, match="вознаграждении поверенного"):
        MandateFactSet(**remuneration)


def test_mandate_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk971-976-mandate-concept-instructions-and-duties-v1",
        "synthetic-ru-gk977-979-mandate-termination-and-consequences-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_mandate_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_mandate_benchmark_suite()
    red_team = run_mandate_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_MANDATE_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_MANDATE_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_mandate_artifact_is_reproducible() -> None:
    fixture = SyntheticMandateEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_mandate_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_mandate_evaluation_artifact()
