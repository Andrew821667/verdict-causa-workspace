"""Тесты института возложения ответственности и просрочки сторон (статьи 402–406)."""

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.attribution_delay import (
    ATTRIBUTION_DELAY_EVIDENCE_SCHEMA_VERSION,
    ATTRIBUTION_DELAY_MAPPING_VERSION,
    ATTRIBUTION_DELAY_MODEL_VERSION,
    AttributionDelayFactSet,
    ReviewedAttributionDelayEvidence,
)
from causa.institutional.contracts.attribution_delay_evaluation import (
    SYNTHETIC_ATTRIBUTION_DELAY_BENCHMARKS,
    SYNTHETIC_ATTRIBUTION_DELAY_RED_TEAM_CASES,
    run_attribution_delay_benchmark_suite,
    run_attribution_delay_red_team_suite,
)
from causa.institutional.contracts.practice_coverage import institutes_for_article
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_attribution_delay import (
    build_synthetic_attribution_delay_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)


def _flip(evidence, **updates: bool):
    return evidence.model_copy(
        update={
            "assertions": tuple(
                assertion.model_copy(update={"value": updates[assertion.predicate.value]})
                if assertion.predicate.value in updates
                else assertion
                for assertion in evidence.assertions
            )
        }
    )


def _facts(**updates: bool) -> AttributionDelayFactSet:
    values = {field_name: False for field_name in AttributionDelayFactSet.model_fields}
    values.update(updates)
    return AttributionDelayFactSet(**values)


def test_institute_closes_the_gap_real_practice_found() -> None:
    """Институт появился ради статей, на которые сослались реальные суды.

    Статьи 402–406 лежали между моделью ответственности (333–401) и моделью
    средств защиты, берущей из главы 25 только 393 и 406.1. Пробел нашло
    измерение покрытия на полученной выгрузке практики.
    """
    for article in ("402", "403", "404", "405", "406"):
        assert institutes_for_article(article) == ["attribution_delay"]


def test_reviewed_attribution_delay_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.attribution_delay_evidence_mapping
    assert mapping.schema_version == ATTRIBUTION_DELAY_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == ATTRIBUTION_DELAY_MAPPING_VERSION
    assert result.attribution_delay_constraint_set.model_version == ATTRIBUTION_DELAY_MODEL_VERSION
    evaluation = result.attribution_delay_evaluation
    # В демонстрационном деле нарушение заявлено, но исполнение на третьих лиц
    # не возлагалось и о просрочке кредитора не заявлялось.
    assert evaluation.attribution_qualified is True
    assert evaluation.requires_human_attribution_assessment is False


def test_entrusting_performance_does_not_shift_liability() -> None:
    """Ключевое правило статьи 403: возложение исполнения не переносит ответственность."""
    entrusted = _facts(
        obligation_breach_asserted=True,
        performance_entrusted_to_third_party=True,
        third_party_caused_breach=True,
    )
    shifted = entrusted.model_copy(update={"law_assigns_liability_to_performer": True})

    from causa.institutional.contracts.attribution_delay import (
        AttributionDelayEvidenceMappingResult,
        build_attribution_delay_constraint_set,
        evaluate_attribution_delay_constraints,
    )

    def run(facts: AttributionDelayFactSet):
        mapping = AttributionDelayEvidenceMappingResult(
            evidence_id="test",
            schema_version="test",
            mapping_version="test",
            facts=facts,
            legal_source_refs=["test-law"],
        )
        return evaluate_attribution_delay_constraints(
            build_attribution_delay_constraint_set(mapping), facts
        )

    default = run(entrusted)
    assert default.debtor_answerable_for_third_party is True
    assert default.liability_shifted_to_performer is False

    by_statute = run(shifted)
    assert by_statute.liability_shifted_to_performer is True
    assert by_statute.debtor_answerable_for_third_party is False


def test_creditor_delay_removes_the_debtors_delay() -> None:
    """Статья 406: пока длится просрочка кредитора, должник не считается просрочившим."""
    request = build_synthetic_supply_analysis_request()
    both_delayed = request.model_copy(
        update={
            "attribution_delay_evidence": _flip(
                request.attribution_delay_evidence,
                debtor_delay_established=True,
                creditor_delay_established=True,
            )
        }
    )

    evaluation = run_reviewed_contract_analysis(
        both_delayed, build_synthetic_supply_analysis_sources()
    ).attribution_delay_evaluation

    assert evaluation.creditor_in_delay is True
    assert evaluation.creditor_delay_excuses_debtor is True
    assert evaluation.debtor_in_delay is False
    assert evaluation.creditor_may_refuse_performance is False


def test_fact_set_rejects_third_party_breach_without_entrustment() -> None:
    with pytest.raises(ValidationError, match="возложено исполнение"):
        _facts(obligation_breach_asserted=True, third_party_caused_breach=True)

    with pytest.raises(ValidationError, match="Утрата интереса"):
        _facts(obligation_breach_asserted=True, performance_lost_interest_for_creditor=True)


def test_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.attribution_delay_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedAttributionDelayEvidence(
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
            request.model_copy(update={"attribution_delay_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_evidence() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.attribution_delay_evidence

    with pytest.raises(ValueError, match="Attribution and delay evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "attribution_delay_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_attribution_delay_benchmark_suite()
    red_team = run_attribution_delay_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_ATTRIBUTION_DELAY_BENCHMARKS) == 10
    assert benchmark.failed == 0, [r for r in benchmark.results if not r.passed]
    assert red_team.total == len(SYNTHETIC_ATTRIBUTION_DELAY_RED_TEAM_CASES) == 10
    assert red_team.unblocked == 0, [r for r in red_team.results if not r.blocked]


def test_synthetic_artifact_is_reproducible() -> None:
    artifact = build_synthetic_attribution_delay_evaluation_artifact()

    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0
    assert "402–406" in artifact.disclaimer_ru
    assert artifact.reviewed_evaluation.reasons_ru


def test_breach_flag_raises_human_review_but_a_quiet_case_does_not() -> None:
    """Флаг экспертизы поднимается основанием, а не самим фактом нарушения."""
    quiet = _facts(obligation_breach_asserted=True)
    from causa.institutional.contracts.attribution_delay import (
        AttributionDelayEvidenceMappingResult,
        build_attribution_delay_constraint_set,
        evaluate_attribution_delay_constraints,
    )

    mapping = AttributionDelayEvidenceMappingResult(
        evidence_id="quiet",
        schema_version="test",
        mapping_version="test",
        facts=quiet,
        legal_source_refs=["test-law"],
    )
    evaluation = evaluate_attribution_delay_constraints(
        build_attribution_delay_constraint_set(mapping), quiet
    )

    assert evaluation.attribution_qualified is True
    assert evaluation.requires_human_attribution_assessment is False
