"""Тесты очереди пробелов и основного окна."""

import pytest

from causa.phase0.demo_trace import build_supply_dispute_demo_trace
from causa.translation import TranslationAssertionCode, TranslationLevel
from causa.ui.gaps import GapKind, build_gap_queue
from causa.ui.reasoning import CONCLUSION_SPINE, READABLE_LEVELS, build_reasoning_view


@pytest.fixture(scope="module")
def trace():
    return build_supply_dispute_demo_trace()


def test_every_gap_says_what_changes_if_closed(trace) -> None:
    """Пробел без последствия — просьба донести документ «на всякий случай»."""
    queue = build_gap_queue(trace.analysis_result)

    decisive = [gap for gap in queue.gaps if gap.kind is GapKind.DECISIVE_FACT]
    assert decisive
    for gap in decisive:
        assert gap.consequence_ru, gap.id
        assert gap.closes_with_ru, gap.id


def test_blocking_gaps_are_counted_and_explained(trace) -> None:
    """Пока пробелы открыты, вывод нельзя показывать окончательным."""
    queue = build_gap_queue(trace.analysis_result)

    assert queue.blocking_count > 0
    assert any("нельзя считать окончательным" in note for note in queue.notes_ru)


def test_human_review_flags_become_tasks() -> None:
    """Флаг «требует человека» — задача оператору, а не строка в логе."""
    trace = build_supply_dispute_demo_trace()
    result = trace.analysis_result
    flagged = result.model_copy(
        update={
            "general_effects_evaluation": result.general_effects_evaluation.model_copy(
                update={"requires_human_general_effects_assessment": True}
            )
        }
    )

    queue = build_gap_queue(flagged)

    human = [gap for gap in queue.gaps if gap.kind is GapKind.HUMAN_REVIEW]
    assert len(human) == 1
    assert human[0].blocking is True
    assert human[0].institute == "general_effects"


def test_conclusion_spine_names_real_assertion_codes() -> None:
    """Линия вывода ведётся вручную и обязана ломаться, а не подстраиваться."""
    known = set(TranslationAssertionCode)

    codes = [code for code, _ in CONCLUSION_SPINE]
    assert len(codes) == len(set(codes))
    for code in codes:
        assert code in known, code


def test_the_line_answers_its_own_questions(trace) -> None:
    """Каждое звено несёт вопрос, ответ и источники."""
    view = build_reasoning_view(trace.analysis_request, trace.analysis_result)

    assert len(view.line) == len(CONCLUSION_SPINE)
    for step in view.line:
        assert step.question_ru
        assert step.text_ru
        assert isinstance(step.value, (bool, str))


def test_the_debate_does_not_pretend_to_be_multi_agent(trace) -> None:
    """Раздела 8.2 в ядре нет, и интерфейс не рисует несуществующий спор агентов."""
    view = build_reasoning_view(trace.analysis_request, trace.analysis_result)

    assert "8.2" in view.debate.disclaimer_ru
    assert view.debate.supporting.points_ru
    assert view.debate.opposing.points_ru
    assert view.debate.critic.points_ru
    for side in (view.debate.supporting, view.debate.opposing, view.debate.critic):
        assert len(side.origin_ru) > 30, side.title_ru


def test_opposing_side_comes_from_the_solver(trace) -> None:
    """«Против» — вычисленные контрфакты, а не сочинённые возражения."""
    view = build_reasoning_view(trace.analysis_request, trace.analysis_result)
    material = [s for s in trace.analysis_result.counterfactual_sensitivity.scenarios if s.material]

    assert len(view.debate.opposing.points_ru) == len(material)


def test_registers_are_absent_without_a_bundle_and_said_so(trace) -> None:
    """Один уровень изложения не подменяется другим — этого просто нет."""
    without = build_reasoning_view(trace.analysis_request, trace.analysis_result)
    with_bundle = build_reasoning_view(
        trace.analysis_request, trace.analysis_result, trace.translation_bundle
    )

    assert without.registers == []
    assert without.trace is None
    assert any("не собрано" in note for note in without.notes_ru)
    assert [register.level for register in with_bundle.registers] == list(READABLE_LEVELS)
    assert with_bundle.notes_ru == []


def test_the_machine_trace_is_not_shown_as_a_text_for_the_court(trace) -> None:
    """Forensic-уровень — это протокол наладки, и подпись у него соответствующая.

    Проверяется не формулировка, а граница: уровень, которому правила конвейера
    намеренно разрешают машинную деталь, не должен стоять среди текстов, по
    которым юрист работает.
    """
    view = build_reasoning_view(
        trace.analysis_request, trace.analysis_result, trace.translation_bundle
    )

    assert view.trace is not None
    assert view.trace.level is TranslationLevel.FORENSIC
    assert TranslationLevel.FORENSIC not in [register.level for register in view.registers]
    assert "суд" not in view.trace.level_ru.lower()
    assert "наладк" in view.trace.level_ru


def test_a_missing_spine_link_is_shown_as_missing(trace) -> None:
    """Отсутствующее звено показывается пробелом линии, а не достраивается догадкой."""
    from causa.ui import reasoning

    dropped = TranslationAssertionCode.BREACH_ISSUE
    original = reasoning.build_translation_assertions
    reasoning.build_translation_assertions = lambda request, result: [
        assertion for assertion in original(request, result) if assertion.code is not dropped
    ]
    try:
        view = build_reasoning_view(trace.analysis_request, trace.analysis_result)
    finally:
        reasoning.build_translation_assertions = original

    assert any(dropped.value in note for note in view.notes_ru)
    assert len(view.line) == len(CONCLUSION_SPINE) - 1
