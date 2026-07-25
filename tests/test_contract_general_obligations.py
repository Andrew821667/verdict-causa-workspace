from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.general_obligations import (
    GENERAL_OBLIGATIONS_EVIDENCE_SCHEMA_VERSION,
    GENERAL_OBLIGATIONS_MAPPING_VERSION,
    GENERAL_OBLIGATIONS_MODEL_VERSION,
    GeneralObligationsFactSet,
    ReviewedGeneralObligationsEvidence,
)
from causa.institutional.contracts.general_obligations_evaluation import (
    SYNTHETIC_GENERAL_OBLIGATIONS_BENCHMARKS,
    SYNTHETIC_GENERAL_OBLIGATIONS_RED_TEAM_CASES,
    run_general_obligations_benchmark_suite,
    run_general_obligations_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_general_obligations import (
    SyntheticGeneralObligationsEvaluationArtifact,
    build_synthetic_general_obligations_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_general_obligations_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.general_obligations_evidence_mapping
    assert mapping.schema_version == GENERAL_OBLIGATIONS_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == GENERAL_OBLIGATIONS_MAPPING_VERSION
    assert result.general_obligations_constraint_set.model_version == (
        GENERAL_OBLIGATIONS_MODEL_VERSION
    )
    evaluation = result.general_obligations_evaluation
    # В демонстрационном деле обязательство установлено и требуется натура.
    assert evaluation.creditor_may_demand_performance is True
    assert evaluation.specific_performance_available is True
    assert evaluation.good_faith_breach_flagged is False
    assert evaluation.requires_human_general_obligations_assessment is False


def test_general_obligations_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.general_obligations_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedGeneralObligationsEvidence(
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
            request.model_copy(update={"general_obligations_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_general_obligations_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.general_obligations_evidence

    with pytest.raises(ValueError, match="General obligations evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "general_obligations_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="General obligations evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "general_obligations_evidence": evidence.model_copy(update={"case_id": "other"})
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "general_obligations_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-general-obligations-evidence",
                                "synthetic-ru-gk3081-3083-obligation-types-and-protection-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_general_obligations_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in GeneralObligationsFactSet.model_fields}
    values.update(choice_made_in_alternative=True)
    with pytest.raises(ValidationError, match="без альтернативного обязательства"):
        GeneralObligationsFactSet(**values)


def test_general_obligations_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk307-308-obligation-concept-v1",
        "synthetic-ru-gk3081-3083-obligation-types-and-protection-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_general_obligations_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_general_obligations_benchmark_suite()
    red_team = run_general_obligations_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_GENERAL_OBLIGATIONS_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_GENERAL_OBLIGATIONS_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_general_obligations_artifact_is_reproducible() -> None:
    fixture = SyntheticGeneralObligationsEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_general_obligations_evaluation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture == build_synthetic_general_obligations_evaluation_artifact()
