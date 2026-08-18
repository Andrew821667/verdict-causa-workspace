"""Фабула дела и проект процессуального документа.

Здесь проверяется не красота формулировок, а границы: фабула не должна
утверждать того, чего нет в фактах, а документ в дело не должен нести ни одного
следа машины. Обе границы легко нарушить незаметно, и обе — существенные.
"""

import pytest

from causa.phase0.demo_trace import build_supply_dispute_demo_trace
from causa.ui.case_story import FACT_SENTENCES_RU, STORY_SECTIONS, build_case_story
from causa.ui.court_filing import (
    MACHINE_MARKERS,
    FilingKind,
    build_court_filing,
)
from causa.ui.gaps import build_gap_queue
from causa.ui.qualification import build_case_qualification
from causa.ui.reasoning import build_reasoning_view
from causa.ui.verdict import build_case_verdict, VerdictState


@pytest.fixture(scope="module")
def parts():
    trace = build_supply_dispute_demo_trace()
    result = trace.analysis_result
    qualification = build_case_qualification(result)
    gaps = build_gap_queue(result)
    verdict = build_case_verdict(result, qualification, gaps)
    story = build_case_story(result, qualification)
    reasoning = build_reasoning_view(trace.analysis_request, result, trace.translation_bundle)
    filing = build_court_filing(
        result=result,
        story=story,
        line=reasoning.line,
        qualification=qualification,
        verdict=verdict,
        gaps=gaps,
    )
    return trace, result, qualification, gaps, verdict, story, filing


def test_every_obligation_fact_has_a_sentence(parts) -> None:
    """Новый факт обязан сломать словарь формулировок, а не проскользнуть немым."""
    _, result, _, _, _, _, _ = parts
    declared = set(type(result.evidence_mapping.facts).model_fields)

    assert declared <= set(FACT_SENTENCES_RU)
    placed = {name for _, names in STORY_SECTIONS for name in names}
    assert placed == declared


def test_the_story_states_missing_facts_as_not_established(parts) -> None:
    """Замкнутая модель считает неутверждённое ложным, но это не отрицание по существу."""
    _, _, _, _, _, story, _ = parts
    missing = [fact for section in story.sections for fact in section.facts if not fact.established]

    assert missing
    for fact in missing:
        assert (
            "не установлен" in fact.text_ru
            or "не заявлен" in fact.text_ru
            or ("не доказан" in fact.text_ru)
        )


def test_the_summary_carries_the_dates_of_the_case(parts) -> None:
    """Фабула без дат — это не фабула, а название спора."""
    _, result, _, _, _, story, _ = parts
    agreed = result.temporal_facts.agreed_due_date

    assert agreed is not None
    assert f"{agreed:%d.%m.%Y}" in story.summary_ru


def test_the_story_invents_no_party_names(parts) -> None:
    """Имён сторон во входах модели нет, и появиться им неоткуда."""
    _, _, _, _, _, story, _ = parts
    text = story.summary_ru + " ".join(
        fact.text_ru for section in story.sections for fact in section.facts
    )

    for invented in ("ООО", "истец ", "ответчик ", "«Ромашка»"):
        assert invented not in text


def test_the_filing_genre_follows_the_verdict(parts) -> None:
    """Исковое по делу, где требование перекрыто давностью, — вредительство."""
    _, _, _, _, verdict, _, filing = parts

    assert verdict.state is VerdictState.BREACH_ESTABLISHED
    assert filing.kind is FilingKind.STATEMENT_OF_CLAIM


def test_the_filing_carries_no_machine_detail(parts) -> None:
    """Документ в дело отличается от машинного вывода именно этим."""
    _, _, _, _, _, _, filing = parts

    for marker in MACHINE_MARKERS:
        assert marker not in filing.text
    assert all(
        check.passed
        for check in filing.checks
        if check.code in {"no_machine_detail", "no_identifiers", "cyrillic_ratio"}
    )


def test_the_filing_refuses_to_be_filed_while_gaps_are_open(parts) -> None:
    """Бумага, подписанная не глядя, — способ, которым такие системы вредят."""
    _, _, _, gaps, _, _, filing = parts

    assert gaps.blocking_count > 0
    assert filing.ready_to_file is False
    assert any(str(gaps.blocking_count) in paragraph for paragraph in _caveats(filing))


def test_the_filing_cites_norms_and_not_source_identifiers(parts) -> None:
    """Ссылка «synthetic-ru-gk432-...» в заседании не читается вслух."""
    _, _, _, _, _, _, filing = parts
    grounds = next(
        section for section in filing.sections if section.title_ru == "Правовое обоснование"
    )
    text = " ".join(grounds.paragraphs_ru)

    assert "ГК РФ" in text
    assert "synthetic" not in text


def _caveats(filing) -> list[str]:
    return next(
        section for section in filing.sections if section.title_ru == "Оговорки"
    ).paragraphs_ru
