"""Три значения факта и бремя доказывания.

Корневой дефект, который здесь закрывается: «основание освобождения не
установлено» и «основания освобождения нет» кодировались одним битом и
подавались в правило как факт в пользу истца.

Главная проверка — не в том, что система научилась говорить «зависит». Это
было бы перекладыванием задачи: суд такие дела решает уверенно. Главная в том,
что «зависит» разрешается по бремени доказывания и разрешается **в разные
стороны** в зависимости от того, кто обязан был доказать.
"""

import pytest

from causa.phase0.demo_trace import build_supply_dispute_demo_trace
from causa.reasoning.formal_checks import ObligationFactSet
from causa.reasoning.three_valued import (
    BURDEN_BY_FACT,
    BURDEN_OF_PROOF,
    OutcomeStatus,
    Party,
    UnknownFactError,
    evaluate_with_unknowns,
)


@pytest.fixture(scope="module")
def case():
    result = build_supply_dispute_demo_trace().analysis_result
    return result.constraint_set, result.evidence_mapping.facts


def test_without_unknowns_nothing_changes(case) -> None:
    """Третье значение не имеет права влиять на дело, где всё установлено."""
    constraint_set, facts = case
    evaluation = evaluate_with_unknowns(constraint_set, facts)

    assert not evaluation.depends_on_anything
    assert evaluation.outcome("breach_issue").status is OutcomeStatus.PROVEN
    assert evaluation.outcome("breach_issue").resolved is True


def test_unproven_exemption_is_resolved_against_the_respondent(case) -> None:
    """Отсутствие вины доказывает должник — пункт 2 статьи 401 ГК РФ."""
    constraint_set, facts = case
    evaluation = evaluate_with_unknowns(constraint_set, facts, {"valid_exception_applies"})
    breach = evaluation.outcome("breach_issue")

    assert breach.status is OutcomeStatus.DEPENDS
    assert breach.driven_by == ["valid_exception_applies"]
    assert breach.resolved is True
    assert "ответчик" in breach.resolution_ru


def test_unproven_duty_is_resolved_against_the_claimant(case) -> None:
    """Существование обязательства доказывает тот, кто на нём строит требование."""
    constraint_set, facts = case
    evaluation = evaluate_with_unknowns(constraint_set, facts, {"duty_exists"})
    breach = evaluation.outcome("breach_issue")

    assert breach.status is OutcomeStatus.DEPENDS
    assert breach.resolved is False
    assert "истец" in breach.resolution_ru


def test_the_same_uncertainty_resolves_both_ways(case) -> None:
    """Ровно в этом смысл бремени: «не доказано» — правило, а не факт о мире."""
    constraint_set, facts = case
    against_respondent = evaluate_with_unknowns(
        constraint_set, facts, {"valid_exception_applies"}
    ).outcome("breach_issue")
    against_claimant = evaluate_with_unknowns(constraint_set, facts, {"duty_exists"}).outcome(
        "breach_issue"
    )

    assert against_respondent.status is against_claimant.status is OutcomeStatus.DEPENDS
    assert against_respondent.resolved != against_claimant.resolved


def test_only_the_facts_that_decide_are_named(case) -> None:
    """Неизвестных может быть много, а решать может один.

    Требовать доказывания того, что ничего не изменит, — способ утопить юриста
    в работе, из которой ничего не следует.
    """
    constraint_set, facts = case
    evaluation = evaluate_with_unknowns(
        constraint_set, facts, {"valid_exception_applies", "payment_defense_applies"}
    )
    breach = evaluation.outcome("breach_issue")

    assert breach.status is OutcomeStatus.DEPENDS
    assert breach.driven_by == ["valid_exception_applies"]


def test_a_conclusion_can_be_refuted_under_every_completion(case) -> None:
    """«Нет при любом доопределении» — самостоятельный ответ, а не разновидность «зависит»."""
    constraint_set, _ = case
    facts = ObligationFactSet(duty_exists=False, due_date_missed=False)
    evaluation = evaluate_with_unknowns(constraint_set, facts, {"valid_exception_applies"})

    assert evaluation.outcome("breach_issue").status is OutcomeStatus.REFUTED
    assert evaluation.outcome("breach_issue").resolved is False


def test_the_note_distinguishes_not_established_from_established_otherwise(case) -> None:
    constraint_set, facts = case
    evaluation = evaluate_with_unknowns(constraint_set, facts, {"duty_exists"})

    assert any("а не «установлено обратное»" in note for note in evaluation.notes_ru)


# --- таблица бремени --------------------------------------------------------


def test_every_obligation_fact_has_a_burden_rule() -> None:
    """Факт без записанного бремени нельзя объявить неустановленным."""
    declared = set(ObligationFactSet.model_fields)

    assert declared == set(BURDEN_BY_FACT)


def test_every_burden_rule_carries_its_legal_basis() -> None:
    """Распределение бремени — утверждение о праве, а не настройка."""
    for rule in BURDEN_OF_PROOF:
        assert rule.basis_ru
        assert len(rule.basis_ru) > 20


def test_payment_is_proved_by_the_debtor() -> None:
    """Статья 408: доказательство исполнения лежит на должнике.

    Поэтому недоказанная оплата означает, что платёж не произведён, — это
    единственный факт в таблице, недоказанность которого даёт «да».
    """
    rule = BURDEN_BY_FACT["payment_missed"]

    assert rule.borne_by is Party.RESPONDENT
    assert rule.unproven_value is True
    assert [item.fact for item in BURDEN_OF_PROOF if item.unproven_value] == ["payment_missed"]


def test_an_unknown_fact_outside_the_model_is_refused(case) -> None:
    constraint_set, facts = case

    with pytest.raises(UnknownFactError):
        evaluate_with_unknowns(constraint_set, facts, {"heir_accepted_inheritance"})
