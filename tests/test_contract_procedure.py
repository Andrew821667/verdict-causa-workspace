from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.procedure import (
    PROCEDURE_EVIDENCE_SCHEMA_VERSION,
    PROCEDURE_MAPPING_VERSION,
    PROCEDURE_MODEL_VERSION,
    ProcedureFactSet,
    ReviewedProcedureEvidence,
)
from causa.institutional.contracts.procedure_evaluation import (
    SYNTHETIC_PROCEDURE_BENCHMARKS,
    SYNTHETIC_PROCEDURE_RED_TEAM_CASES,
    run_procedure_benchmark_suite,
    run_procedure_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_procedure import (
    SyntheticProcedureEvaluationArtifact,
    build_synthetic_procedure_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_procedure_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.procedure_evidence_mapping
    assert mapping.schema_version == PROCEDURE_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == PROCEDURE_MAPPING_VERSION
    assert result.procedure_constraint_set.model_version == PROCEDURE_MODEL_VERSION
    evaluation = result.procedure_evaluation
    # В демонстрационном деле обычное заключение без обязательного порядка и торгов.
    assert evaluation.conclusion_compellable is False
    assert evaluation.auction_contract_formed is False
    assert evaluation.requires_human_procedure_assessment is False


def test_procedure_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.procedure_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedProcedureEvidence(
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
            request.model_copy(update={"procedure_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_procedure_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.procedure_evidence

    with pytest.raises(ValueError, match="Procedure evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "procedure_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Procedure evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"procedure_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "procedure_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-procedure-evidence",
                                "synthetic-ru-gk447-449-auction-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_procedure_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in ProcedureFactSet.model_fields}
    values.update(winner_determined=True)
    with pytest.raises(ValidationError, match="без проведения торгов"):
        ProcedureFactSet(**values)


def test_procedure_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk445-446-mandatory-conclusion-v1",
        "synthetic-ru-gk447-449-auction-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_procedure_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_procedure_benchmark_suite()
    red_team = run_procedure_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_PROCEDURE_BENCHMARKS) == 14
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_PROCEDURE_RED_TEAM_CASES) == 12
    assert red_team.blocked == red_team.total


def test_exported_procedure_artifact_is_reproducible() -> None:
    fixture = SyntheticProcedureEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_procedure_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_procedure_evaluation_artifact()
