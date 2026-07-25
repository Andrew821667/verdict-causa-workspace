from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.adhesion import (
    ADHESION_EVIDENCE_SCHEMA_VERSION,
    ADHESION_MAPPING_VERSION,
    ADHESION_MODEL_VERSION,
    AdhesionFactSet,
    ReviewedAdhesionEvidence,
)
from causa.institutional.contracts.adhesion_evaluation import (
    SYNTHETIC_ADHESION_BENCHMARKS,
    SYNTHETIC_ADHESION_RED_TEAM_CASES,
    run_adhesion_benchmark_suite,
    run_adhesion_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_adhesion import (
    SyntheticAdhesionEvaluationArtifact,
    build_synthetic_adhesion_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_adhesion_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.adhesion_evidence_mapping
    assert mapping.schema_version == ADHESION_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == ADHESION_MAPPING_VERSION
    assert result.adhesion_constraint_set.model_version == ADHESION_MODEL_VERSION
    evaluation = result.adhesion_evaluation
    # В демонстрационном деле применяется режим присоединения без обременительных условий.
    assert evaluation.adhesion_regime_applies is True
    assert evaluation.relief_available is False
    assert evaluation.requires_human_adhesion_assessment is False


def test_adhesion_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.adhesion_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedAdhesionEvidence(
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
            request.model_copy(update={"adhesion_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_adhesion_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.adhesion_evidence

    with pytest.raises(ValueError, match="Adhesion evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "adhesion_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Adhesion evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"adhesion_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "adhesion_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-adhesion-evidence",
                                "synthetic-ru-gk428-adhesion-relief-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_adhesion_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in AdhesionFactSet.model_fields}
    values.update(adhesion_contract=True, terms_individually_negotiated=True)
    with pytest.raises(ValidationError, match="индивидуальное согласование"):
        AdhesionFactSet(**values)


def test_adhesion_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk428-adhesion-framework-v1",
        "synthetic-ru-gk428-adhesion-relief-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_adhesion_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_adhesion_benchmark_suite()
    red_team = run_adhesion_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_ADHESION_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_ADHESION_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_adhesion_artifact_is_reproducible() -> None:
    fixture = SyntheticAdhesionEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_adhesion_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_adhesion_evaluation_artifact()
