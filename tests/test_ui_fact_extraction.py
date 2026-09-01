"""Ворота проверки юристом на пути предложения факта в дело.

Модуль извлечения строится под подключение языковой модели в эксплуатации.
Здесь модель не вызывается ни разу; проверяется другое — что предложение не
может стать фактом, минуя человека, и что путь в обход не появился.
"""

import pytest

from causa.ui.document_text import ExtractedText
from causa.ui.documents import ClosureKind, apply_closure, build_document
from causa.ui.fact_extraction import (
    PROPOSAL_CAVEAT_RU,
    ExtractionResult,
    ExtractionTarget,
    ExtractorKind,
    ExtractorNotConfiguredError,
    FactCandidate,
    KeywordFactExtractor,
    LanguageModelFactExtractor,
    UnreviewedCandidateError,
    UnverifiedQuoteError,
    closure_from_confirmed,
    confirm_candidate,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)

CONTRACT_TEXT = (
    "Договор поставки № 12 от 15.12.2025.\n\n"
    "1.1. Поставщик обязуется передать товар покупателю не позднее 15 января 2026 года.\n"
    "2.1. Покупатель обязан оплатить товар в течение десяти дней с момента поставки.\n"
    "3.1. За просрочку поставки поставщик уплачивает неустойку.\n"
    "4.1. Претензия направляется в письменной форме.\n"
)


def _text(document_id: str = "doc:case-supply-1:abc") -> ExtractedText:
    return ExtractedText(
        document_id=document_id,
        filename="dogovor.txt",
        extracted=True,
        format_ru="текстовый файл",
        text=CONTRACT_TEXT,
        characters=len(CONTRACT_TEXT),
    )


def _targets(*predicates: str) -> tuple[ExtractionTarget, ...]:
    return tuple(
        ExtractionTarget(institute="case", predicate=predicate) for predicate in predicates
    )


def test_the_keyword_extractor_proposes_only_what_it_found() -> None:
    """Совпадение по словам предлагает «да» и никогда «нет».

    Отсутствие слова отсутствия обстоятельства не доказывает, и предлагать
    `False` значило бы выдавать молчание документа за его содержание.
    """
    result = KeywordFactExtractor().propose(_text(), _targets("duty_exists", "remedy_requested"))

    assert result.extractor is ExtractorKind.KEYWORDS
    assert {c.predicate for c in result.candidates} == {"duty_exists", "remedy_requested"}
    assert all(c.proposed_value is True for c in result.candidates)
    # Каждая цитата обязана быть вырезана из текста, а не пересказана.
    for candidate in result.candidates:
        assert candidate.quote_ru.strip("… ") in CONTRACT_TEXT


def test_predicates_without_a_dictionary_are_named_not_omitted() -> None:
    """Пропуск молча читался бы как «в документе ничего нет»."""
    result = KeywordFactExtractor().propose(_text(), _targets("is_utility_payment"))

    assert result.candidates == ()
    assert any("Словаря нет для предикатов" in note for note in result.notes_ru)
    assert PROPOSAL_CAVEAT_RU in result.notes_ru


def test_every_proposal_set_carries_the_caveat() -> None:
    """Набор предложений без оговорки читается как разбор документа."""
    with pytest.raises(ValueError, match="оговорку"):
        ExtractionResult(
            document_id="doc:1",
            extractor=ExtractorKind.KEYWORDS,
            extractor_id="x",
            notes_ru=(),
        )


def test_the_language_model_seam_refuses_out_loud() -> None:
    """Отказ, а не пустой список: молчание модели дороже всего.

    Пустой ответ неотличим от «модель прочитала документ и ничего не нашла», и
    оператор решил бы, что вопрос закрыт.
    """
    with pytest.raises(ExtractorNotConfiguredError, match="не подключена"):
        LanguageModelFactExtractor().propose(_text(), _targets("duty_exists"))


def test_a_candidate_cannot_become_a_fact_without_a_reviewer() -> None:
    candidate = KeywordFactExtractor().propose(_text(), _targets("duty_exists")).candidates[0]

    with pytest.raises(UnreviewedCandidateError, match="без проверившего"):
        confirm_candidate(candidate=candidate, text=_text(), reviewer_id="  ", value=True)


def test_the_extractor_cannot_review_itself() -> None:
    candidate = KeywordFactExtractor().propose(_text(), _targets("duty_exists")).candidates[0]

    with pytest.raises(UnreviewedCandidateError, match="сам извлекатель"):
        confirm_candidate(
            candidate=candidate,
            text=_text(),
            reviewer_id=candidate.extractor_id,
            value=True,
        )


def test_a_quote_that_is_not_in_the_document_is_rejected() -> None:
    """Одна проверка ловит два случая: сочинённую цитату и подменённый документ."""
    candidate = FactCandidate(
        document_id="doc:case-supply-1:abc",
        institute="case",
        predicate="duty_exists",
        proposed_value=True,
        quote_ru="Поставщик обязуется передать товар не позднее 1 марта 2026 года.",
        position=0,
        extractor=ExtractorKind.LANGUAGE_MODEL,
        extractor_id="language-model-extractor-v0",
        confidence=0.9,
    )

    with pytest.raises(UnverifiedQuoteError, match="не найдена в тексте"):
        confirm_candidate(candidate=candidate, text=_text(), reviewer_id="lawyer-1", value=True)


def test_correcting_the_model_costs_no_more_than_agreeing_with_it() -> None:
    """Оба исхода проходят одной дверью, и расхождение остаётся видимым."""
    candidate = KeywordFactExtractor().propose(_text(), _targets("duty_exists")).candidates[0]

    agreed = confirm_candidate(
        candidate=candidate, text=_text(), reviewer_id="lawyer-1", value=True
    )
    corrected = confirm_candidate(
        candidate=candidate,
        text=_text(),
        reviewer_id="lawyer-1",
        value=False,
        reviewer_note_ru="Пункт 1.1 относится к другой поставке, обязанности по спорной нет.",
    )

    assert agreed.differs_from_proposal is False
    assert corrected.differs_from_proposal is True
    assert "исправлено: lawyer-1" in corrected.line_ru


def test_a_correction_without_a_reason_is_rejected() -> None:
    """Иначе в деле остаётся значение, а основание теряется."""
    candidate = KeywordFactExtractor().propose(_text(), _targets("duty_exists")).candidates[0]

    with pytest.raises(UnreviewedCandidateError, match="не сказав почему"):
        confirm_candidate(candidate=candidate, text=_text(), reviewer_id="lawyer-1", value=False)


def test_confirmed_facts_reach_the_case_through_the_existing_door() -> None:
    """Единственный вход в проверенные факты — `documents.apply_closure`."""
    document = build_document(
        case_id="case-supply-1",
        filename="dogovor.txt",
        content=CONTRACT_TEXT.encode("utf-8"),
        uploaded_by="operator-1",
    )
    text = _text(document.id)
    result = KeywordFactExtractor().propose(text, _targets("duty_exists", "payment_duty_exists"))
    confirmed = tuple(
        confirm_candidate(candidate=candidate, text=text, reviewer_id="lawyer-1", value=True)
        for candidate in result.candidates
    )

    closure = closure_from_confirmed(
        gap_id="gap-duty",
        document_id=document.id,
        confirmed=confirmed,
        statement_ru="Договор поставки устанавливает обязанность передать товар и оплатить его.",
    )
    assert closure.kind is ClosureKind.ASSERTED_FACT

    request = apply_closure(build_synthetic_supply_analysis_request(), closure, document)
    duty = next(
        assertion
        for assertion in request.case_evidence.assertions
        if assertion.predicate.value == "duty_exists"
    )
    # Документ записан основанием утверждения — provenance сохранён.
    assert document.id in duty.source_refs


def test_there_is_no_path_from_a_candidate_straight_into_the_case() -> None:
    """Отсутствие обходного пути проверяется, а не только описывается.

    Ни одна функция модуля не принимает `FactCandidate` и не возвращает
    закрытие пробела или запрос анализа. Появление такой функции означало бы
    вторую дверь в проверенные факты — рядом с проверяемой и мимо неё.
    """
    import inspect

    from causa.ui import fact_extraction

    for name, function in inspect.getmembers(fact_extraction, inspect.isfunction):
        if name.startswith("_"):
            continue
        signature = inspect.signature(function)
        takes_candidate = any(
            parameter.annotation is FactCandidate for parameter in signature.parameters.values()
        )
        if not takes_candidate:
            continue
        assert signature.return_annotation != "GapClosure", name
        # Единственная функция, принимающая предложение, обязана требовать имя
        # проверившего.
        assert "reviewer_id" in signature.parameters, name


def test_closure_refuses_facts_of_other_institutes() -> None:
    """Факт одного контракта данных не записывается в другой."""
    candidate = KeywordFactExtractor().propose(_text(), _targets("duty_exists")).candidates[0]
    confirmed = confirm_candidate(
        candidate=candidate.model_copy(update={"institute": "supply"}),
        text=_text(),
        reviewer_id="lawyer-1",
        value=True,
    )

    with pytest.raises(ValueError, match="факты институтов"):
        closure_from_confirmed(
            gap_id="gap-duty",
            document_id=candidate.document_id,
            confirmed=(confirmed,),
            statement_ru="Обязанность есть.",
        )


def test_closure_refuses_two_values_for_one_predicate() -> None:
    """Выбирать между двумя подтверждениями система не станет."""
    candidate = KeywordFactExtractor().propose(_text(), _targets("duty_exists")).candidates[0]
    yes = confirm_candidate(candidate=candidate, text=_text(), reviewer_id="lawyer-1", value=True)
    no = confirm_candidate(
        candidate=candidate,
        text=_text(),
        reviewer_id="lawyer-2",
        value=False,
        reviewer_note_ru="Второй рецензент прочитал пункт 1.1 иначе.",
    )

    with pytest.raises(ValueError, match="разные значения"):
        closure_from_confirmed(
            gap_id="gap-duty",
            document_id=candidate.document_id,
            confirmed=(yes, no),
            statement_ru="Обязанность есть.",
        )
