from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.settlements import (
    SETTLEMENTS_EVIDENCE_SCHEMA_VERSION,
    SETTLEMENTS_MAPPING_VERSION,
    SETTLEMENTS_MODEL_VERSION,
    ReviewedSettlementsEvidence,
    SettlementsFactSet,
)
from causa.institutional.contracts.settlements_evaluation import (
    SYNTHETIC_SETTLEMENTS_BENCHMARKS,
    SYNTHETIC_SETTLEMENTS_RED_TEAM_CASES,
    run_settlements_benchmark_suite,
    run_settlements_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_settlements import (
    SyntheticSettlementsEvaluationArtifact,
    build_synthetic_settlements_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_settlements_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.settlements_evidence_mapping
    assert mapping.schema_version == SETTLEMENTS_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == SETTLEMENTS_MAPPING_VERSION
    assert result.settlements_constraint_set.model_version == SETTLEMENTS_MODEL_VERSION
    evaluation = result.settlements_evaluation
    # В демонстрационном деле оплата произведена единовременно без безналичных расчётов.
    assert evaluation.cashless_settlements_qualified is False
    assert evaluation.requires_human_settlements_assessment is False


def test_settlements_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.settlements_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedSettlementsEvidence(
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
            request.model_copy(update={"settlements_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_settlements_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.settlements_evidence

    with pytest.raises(ValueError, match="Settlements evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "settlements_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Settlements evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"settlements_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "settlements_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-settlements-evidence",
                                "synthetic-ru-gk877-885-settlements-cheque-rules-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_settlements_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in SettlementsFactSet.model_fields}
    values.update(payment_order_liability_not_applied=True)
    with pytest.raises(ValidationError, match="Неприменение ответственности"):
        SettlementsFactSet(**values)

    form = {field_name: False for field_name in SettlementsFactSet.model_fields}
    form.update(settlement_form_not_provided_by_law=True)
    with pytest.raises(ValidationError, match="Использование формы расчётов"):
        SettlementsFactSet(**form)


def test_settlements_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk861-876-settlements-forms-orders-credit-and-collection-v1",
        "synthetic-ru-gk877-885-settlements-cheque-rules-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_settlements_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_settlements_benchmark_suite()
    red_team = run_settlements_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_SETTLEMENTS_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_SETTLEMENTS_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_settlements_artifact_is_reproducible() -> None:
    fixture = SyntheticSettlementsEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_settlements_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_settlements_evaluation_artifact()
