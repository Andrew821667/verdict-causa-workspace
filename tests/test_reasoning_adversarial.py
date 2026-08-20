"""Спор как расхождение двух допустимых миров.

Прежний «Критик пути» был литеральной константой: из шести его строк пять
совпадали дословно для любого дела. Главная проверка здесь — что новый спор
зависит от дела. Если два разных дела дадут одинаковый спор, работа не сделана.
"""

import pytest

from causa.phase0.demo_trace import build_supply_dispute_demo_trace
from causa.reasoning.adversarial import Party, build_two_world_debate, favourable_value
from causa.reasoning.three_valued import BURDEN_BY_FACT, UnknownFactError


@pytest.fixture(scope="module")
def case():
    result = build_supply_dispute_demo_trace().analysis_result
    return result.constraint_set, result.evidence_mapping.facts


def test_without_contested_facts_the_worlds_coincide(case) -> None:
    """Нечего толковать по-разному — значит спорить не о чем, и это ответ."""
    constraint_set, facts = case
    debate = build_two_world_debate(constraint_set, facts)

    assert debate.disputed is False
    assert debate.opposing_ru == []
    assert any("спорить не о чем" in note for note in debate.notes_ru)


def test_the_dispute_is_computed_from_the_case(case) -> None:
    constraint_set, facts = case
    debate = build_two_world_debate(
        constraint_set, facts, {"valid_exception_applies", "due_date_missed"}
    )

    assert debate.disputed is True
    assert any("Вопрос о нарушении обязательства" in line for line in debate.opposing_ru)


def test_the_critic_depends_on_the_case_unlike_the_constant_it_replaces(case) -> None:
    """Прежний критик был одинаков для любого дела. Этот обязан различаться."""
    constraint_set, facts = case
    about_breach = build_two_world_debate(constraint_set, facts, {"valid_exception_applies"})
    about_damages = build_two_world_debate(constraint_set, facts, {"causation_established"})

    assert about_breach.critic_ru != about_damages.critic_ru


def test_a_fact_that_decides_nothing_is_not_named(case) -> None:
    """Требовать доказывания того, что ничего не меняет, — вредная работа."""
    constraint_set, facts = case
    debate = build_two_world_debate(
        constraint_set, facts, {"valid_exception_applies", "causation_established"}
    )
    named = {item.fact for item in debate.contested if item.switches}

    assert "valid_exception_applies" in named
    assert "causation_established" not in named


def test_two_sufficient_facts_are_both_named(case) -> None:
    """Если расхождение держат два факта, каждый из которых достаточен сам по себе.

    Первая версия считала вклад удалением факта из спорных — и оба выглядели ни
    на что не влияющими, потому что удаление любого ничего не меняло. Колонка
    «критик» выходила пустой при двух живых расхождениях.
    """
    constraint_set, facts = case
    debate = build_two_world_debate(
        constraint_set, facts, {"valid_exception_applies", "due_date_missed"}
    )
    named = {item.fact for item in debate.contested if item.switches}

    assert named == {"valid_exception_applies", "due_date_missed"}


def test_stable_conclusions_are_the_supporting_side(case) -> None:
    """«За» — то, что не поколеблет ни одно толкование спорного."""
    constraint_set, facts = case
    debate = build_two_world_debate(constraint_set, facts, {"valid_exception_applies"})

    assert debate.supporting_ru
    for line in debate.supporting_ru:
        assert "при любом толковании" in line


def test_the_favourable_value_comes_from_the_burden_table() -> None:
    """Второй таблицы «что кому выгодно» заводить нельзя — разойдутся."""
    for fact, rule in BURDEN_BY_FACT.items():
        bearer_value = favourable_value(fact, rule.borne_by)
        other = Party.RESPONDENT if rule.borne_by is Party.CLAIMANT else Party.CLAIMANT

        assert bearer_value is not rule.unproven_value
        assert favourable_value(fact, other) is rule.unproven_value


def test_the_disclaimer_about_section_8_2_survives(case) -> None:
    """Три роли из пяти — не пять. Отсутствие называется, а не имитируется."""
    constraint_set, facts = case
    debate = build_two_world_debate(constraint_set, facts, {"due_date_missed"})

    assert any("8.2" in note for note in debate.notes_ru)
    assert any("доктрины и калибратора нет" in note for note in debate.notes_ru)


def test_a_contested_fact_outside_the_model_is_refused(case) -> None:
    constraint_set, facts = case

    with pytest.raises(UnknownFactError):
        build_two_world_debate(constraint_set, facts, {"testament_valid"})
