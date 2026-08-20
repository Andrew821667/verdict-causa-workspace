"""Однофакторный обход: система спрашивает обо всём, а не из списка.

Главная проверка здесь одна и она сравнительная: обход обязан находить то, чего
библиотека из семи операторов не спрашивает никогда. Если оба множества
совпадут, обход не нужен.
"""

import pytest

from causa.institutional.contracts.legal_operators import (
    FACT_LABELS_RU,
    OUTCOME_LABELS_RU,
    build_contract_legal_operator_library,
)
from causa.phase0.demo_trace import build_supply_dispute_demo_trace
from causa.reasoning.formal_checks import evaluate_obligation_constraints
from causa.reasoning.sensitivity import DECISIVE_OUTCOMES, sweep_obligation_facts
from causa.ui.gaps import GapKind, build_gap_queue


@pytest.fixture(scope="module")
def result():
    return build_supply_dispute_demo_trace().analysis_result


def _library_facts() -> set[str]:
    return {
        field
        for operator in build_contract_legal_operator_library().operators
        for field in operator.fact_patch
    }


def test_three_facts_are_outside_the_library_entirely() -> None:
    """Три главных возражения ответчика библиотека не умеет задать.

    «Обязанности не было», «я исполнил», «у меня есть возражение против
    платежа». Это не придирка к формулировкам: ни один из семи операторов не
    меняет этих фактов, значит вопрос о них не возникает ни при какой
    конфигурации дела.
    """
    outside = set(FACT_LABELS_RU) - _library_facts()

    assert outside == {"duty_exists", "performance_completed", "payment_defense_applies"}


def test_the_sweep_finds_what_the_library_never_asks(result) -> None:
    found = {item.fact for item in sweep_obligation_facts(result)}

    assert "duty_exists" in found
    assert "duty_exists" not in _library_facts()


def test_the_sweep_reports_only_facts_that_change_something(result) -> None:
    """Список полей — не список вопросов."""
    for item in sweep_obligation_facts(result):
        assert item.flips


def test_every_reported_flip_is_reproducible(result) -> None:
    """Обход не имеет права утверждать переворот, которого не будет."""
    facts = result.evidence_mapping.facts
    for item in sweep_obligation_facts(result):
        probe = evaluate_obligation_constraints(
            result.constraint_set, facts.model_copy(update={item.fact: item.to_value})
        )
        for flip in item.flips:
            assert bool(getattr(probe, flip.outcome)) == flip.after
            assert bool(getattr(result.constraint_evaluation, flip.outcome)) == flip.before


def test_a_generated_question_says_it_is_generated(result) -> None:
    """Сгенерированную фразу нельзя выдавать за юридическую постановку вопроса."""
    swept = [gap for gap in build_gap_queue(result).gaps if gap.kind is GapKind.FOUND_BY_SWEEP]

    assert swept
    for gap in swept:
        assert any("библиотеке операторов нет" in line for line in gap.closes_with_ru)


# --- пометка «блокирует вывод» ----------------------------------------------


def test_blocking_is_no_longer_a_tautology(result) -> None:
    """Пометка стояла у каждого пробела всегда и потому не значила ничего.

    Она ставилась по признаку «сценарий критический», а список критических
    сценариев по построению совпадал со списком материальных, из которых
    пробелы и собираются.
    """
    queue = build_gap_queue(result)
    decisive = [gap for gap in queue.gaps if gap.blocking]
    detail = [gap for gap in queue.gaps if not gap.blocking]

    assert decisive, "ни один пробел не помечен блокирующим — проверка потеряла смысл"
    assert detail, "все пробелы блокирующие: пометка снова ничего не сообщает"


def test_a_detail_flip_does_not_block(result) -> None:
    """Пробел причинной связи меняет подробность внутри уже возникшего вопроса."""
    queue = build_gap_queue(result)
    gap = next(gap for gap in queue.gaps if "доказательственный пробел" in gap.question_ru)

    assert gap.blocking is False
    assert all("Пробел причинной связи" in line for line in gap.consequence_ru)


def test_decisive_outcomes_are_real_fields() -> None:
    """Список решающих выводов ведётся вручную и обязан ломаться при их переименовании."""
    assert DECISIVE_OUTCOMES <= set(OUTCOME_LABELS_RU)
