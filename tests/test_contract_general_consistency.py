"""Тесты слоя сверки проверенных фактов между институтами пакета."""

from causa.institutional.contracts.contradiction_taxonomy import (
    CROSS_INSTITUTE_CONTRADICTION_TYPES,
)
from causa.institutional.contracts.general_consistency import (
    GENERAL_CONSISTENCY_MODEL_VERSION,
    GeneralConsistencyEvaluation,
    build_general_consistency_constraint_set,
    build_general_consistency_inputs,
    evaluate_general_consistency_constraints,
)
from causa.institutional.contracts.general_consistency_evaluation import (
    SYNTHETIC_GENERAL_CONSISTENCY_BENCHMARKS,
    SYNTHETIC_GENERAL_CONSISTENCY_RED_TEAM_CASES,
    run_general_consistency_benchmark_suite,
    run_general_consistency_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
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


def test_every_declared_cross_institute_type_is_checked() -> None:
    """Объявленный тип противоречия обязан проверяться слоем.

    До появления слоя `contradiction_taxonomy` объявлял 45 типов противоречий, и
    ни один из них ничего не проверял: список не импортировался никуда, кроме
    перечня файлов пакета. Этот тест не даёт набору снова стать мёртвым.
    """
    checked = {
        name
        for name, annotation in GeneralConsistencyEvaluation.model_fields.items()
        if name.endswith("_conflict") and annotation.annotation is bool
    }
    assert set(CROSS_INSTITUTE_CONTRADICTION_TYPES) == checked
    assert len(CROSS_INSTITUTE_CONTRADICTION_TYPES) == 10


def test_consistency_layer_is_derived_from_reviewed_facts() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert (
        result.general_consistency_constraint_set.model_version == GENERAL_CONSISTENCY_MODEL_VERSION
    )
    assert result.general_consistency_inputs == build_general_consistency_inputs(
        result.persons_evidence_mapping.facts,
        result.invalidity_evidence_mapping.facts,
        result.transactions_evidence_mapping.facts,
        result.objects_evidence_mapping.facts,
        result.form_evidence_mapping.facts,
        result.formation_evidence_mapping.facts,
        result.termination_evidence_mapping.facts,
        result.formation_evaluation,
    )
    # Демонстрационное дело согласовано: слой ничего не выдумывает.
    evaluation = result.general_consistency_evaluation
    assert evaluation.contradictions_detected is False
    assert evaluation.requires_human_consistency_assessment is False


def test_consistency_replays_from_its_inputs() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    expected_set = build_general_consistency_constraint_set(
        result.general_consistency_inputs, result.case_id
    )
    assert result.general_consistency_constraint_set == expected_set
    assert result.general_consistency_evaluation == evaluate_general_consistency_constraints(
        expected_set, result.general_consistency_inputs
    )


def test_contradictory_capacity_facts_are_named_not_silently_resolved() -> None:
    """Регрессия: расхождение о недееспособности стороны больше не проходит молча.

    Модель лиц утверждала недееспособность, модель недействительности её
    отрицала, слой общих положений молча выбирал первую версию и выдавал
    уверенный вывод о ничтожности договора. Теперь противоречие названо.
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    assert baseline.general_consistency_evaluation.contradictions_detected is False
    assert baseline.requires_human_resolution is False

    conflicting = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "persons_evidence": _flip(
                    request.persons_evidence,
                    party_capacity_asserted=True,
                    incapacity_declared_by_court=True,
                ),
                "invalidity_evidence": _flip(
                    request.invalidity_evidence,
                    transaction_concluded=True,
                    incapacitated_person_transaction=False,
                ),
            }
        ),
        sources,
    )

    evaluation = conflicting.general_consistency_evaluation
    assert evaluation.capacity_invalidity_conflict is True
    assert evaluation.contradictions_detected is True
    # Слой не выбирает версию: он называет расхождение.
    assert any("Противоречие между институтами" in reason for reason in evaluation.reasons_ru)
    assert conflicting.requires_human_resolution is True


def test_agreed_facts_across_institutes_raise_no_conflict() -> None:
    """Согласованное утверждение того же факта в двух институтах — не противоречие."""
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()

    agreed = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "transactions_evidence": _flip(
                    request.transactions_evidence,
                    transaction_asserted=True,
                    statutory_consent_not_obtained=True,
                ),
                "invalidity_evidence": _flip(
                    request.invalidity_evidence,
                    transaction_concluded=True,
                    required_consent_absent=True,
                ),
            }
        ),
        sources,
    )

    assert agreed.transactions_evaluation.consent_missing_for_transaction is True
    assert agreed.general_consistency_evaluation.consent_invalidity_conflict is False
    assert agreed.general_consistency_evaluation.contradictions_detected is False


def test_consistency_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_general_consistency_benchmark_suite()
    red_team = run_general_consistency_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_GENERAL_CONSISTENCY_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_GENERAL_CONSISTENCY_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total
