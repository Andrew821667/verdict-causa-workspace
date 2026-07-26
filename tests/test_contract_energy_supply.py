from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.energy_supply import (
    ENERGY_SUPPLY_EVIDENCE_SCHEMA_VERSION,
    ENERGY_SUPPLY_MAPPING_VERSION,
    ENERGY_SUPPLY_MODEL_VERSION,
    EnergySupplyFactSet,
    ReviewedEnergySupplyEvidence,
)
from causa.institutional.contracts.energy_supply_evaluation import (
    SYNTHETIC_ENERGY_SUPPLY_BENCHMARKS,
    SYNTHETIC_ENERGY_SUPPLY_RED_TEAM_CASES,
    run_energy_supply_benchmark_suite,
    run_energy_supply_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_energy_supply import (
    SyntheticEnergySupplyEvaluationArtifact,
    build_synthetic_energy_supply_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_energy_supply_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.energy_supply_evidence_mapping
    assert mapping.schema_version == ENERGY_SUPPLY_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == ENERGY_SUPPLY_MAPPING_VERSION
    assert result.energy_supply_constraint_set.model_version == ENERGY_SUPPLY_MODEL_VERSION
    evaluation = result.energy_supply_evaluation
    # В демонстрационном деле спор о поставке товаров, а не об энергоснабжении.
    assert evaluation.energy_supply_qualified is False
    assert evaluation.unlawful_supply_interruption is False
    assert evaluation.requires_human_energy_supply_assessment is False


def test_energy_supply_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.energy_supply_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedEnergySupplyEvidence(
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
            request.model_copy(update={"energy_supply_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_energy_supply_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.energy_supply_evidence

    with pytest.raises(ValueError, match="Energy supply evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "energy_supply_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Energy supply evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"energy_supply_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "energy_supply_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-energy-supply-evidence",
                                "synthetic-ru-gk543-547-energy-supply-duties-and-interruption-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_energy_supply_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in EnergySupplyFactSet.model_fields}
    values.update(supply_interruption_agreed=True)
    with pytest.raises(ValidationError, match="при фактическом перерыве подачи"):
        EnergySupplyFactSet(**values)


def test_energy_supply_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk539-542-energy-supply-concept-v1",
        "synthetic-ru-gk543-547-energy-supply-duties-and-interruption-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_energy_supply_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_energy_supply_benchmark_suite()
    red_team = run_energy_supply_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_ENERGY_SUPPLY_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_ENERGY_SUPPLY_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_energy_supply_artifact_is_reproducible() -> None:
    fixture = SyntheticEnergySupplyEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_energy_supply_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_energy_supply_evaluation_artifact()
