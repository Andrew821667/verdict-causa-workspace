"""Извлечение текста из документов и поиск мест под пробелы.

Граница здесь единственная и решающая: текст извлекается, факты — нет. Тесты
проверяют, что извлечение не превращается в понимание ни в данных, ни в
подписях.
"""

import io
import zipfile

import pytest

from causa.ui.desktop import build_demo_case_inputs
from causa.ui.document_text import (
    FACT_KEYWORDS_RU,
    MAX_TEXT_CHARACTERS,
    build_gap_hints,
    extract_text,
)
from causa.ui.documents import FACT_TO_PREDICATE, build_document
from causa.ui.session import CaseSession

CONTRACT_RU = """ДОГОВОР ПОСТАВКИ № 14/2025

1. Предмет договора
1.1. Поставщик обязуется поставить, а Покупатель принять и оплатить товар.

2. Срок поставки
2.1. Поставщик обязан передать товар не позднее 15.01.2026.

3. Ответственность
3.1. Стороны освобождаются от ответственности при наступлении обстоятельств
непреодолимой силы.

4. Приёмка
4.1. Товар передан «20» января 2026 года по товарной накладной № 7.
"""


def _document(filename: str, content: bytes):
    return build_document(
        case_id="case-supply-1",
        filename=filename,
        content=content,
        uploaded_by="op-demo",
    )


def _docx(paragraphs: list[str]) -> bytes:
    body = "".join(f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>" for text in paragraphs)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body></w:document>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return buffer.getvalue()


def test_plain_text_in_cp1251_is_read() -> None:
    """Русские документы из старых систем приходят именно в этой кодировке."""
    content = "Договор поставки № 5".encode("cp1251")
    extracted = extract_text(_document("dogovor.txt", content), content)

    assert extracted.extracted is True
    assert "Договор поставки" in extracted.text


def test_docx_paragraphs_do_not_glue_together() -> None:
    """Без разрыва по </w:p> весь договор превращается в одну строку."""
    content = _docx(["Первый пункт", "Второй пункт"])
    extracted = extract_text(_document("dogovor.docx", content), content)

    assert extracted.extracted is True
    assert "Первый пункт" in extracted.text
    assert "Второй пункт" in extracted.text
    assert extracted.text.count("\n") >= 1


def test_an_unreadable_format_says_so_instead_of_showing_nothing() -> None:
    """Пустой текст неотличим от документа без слов — так отвечать нельзя."""
    extracted = extract_text(_document("скан.jpg", b"\xff\xd8\xff"), b"\xff\xd8\xff")

    assert extracted.extracted is False
    assert extracted.text == ""
    assert "не читает" in extracted.note_ru


def test_long_text_is_cut_and_says_that_it_was_cut() -> None:
    content = ("А" * (MAX_TEXT_CHARACTERS + 1000)).encode("utf-8")
    extracted = extract_text(_document("big.txt", content), content)

    assert extracted.truncated is True
    assert extracted.characters == MAX_TEXT_CHARACTERS
    assert "отсечено" in extracted.note_ru


def test_every_assertable_fact_has_search_words() -> None:
    """Факт без слов поиска молча не получит ни одной подсказки."""
    assert set(FACT_TO_PREDICATE) <= set(FACT_KEYWORDS_RU)


@pytest.fixture(scope="module")
def view_with_contract():
    inputs = build_demo_case_inputs()
    session = CaseSession(inputs)
    content = CONTRACT_RU.encode("utf-8")
    session.add_document(_document("dogovor-postavki.txt", content), content)
    return session.build_view()


def test_the_text_reaches_the_operator(view_with_contract) -> None:
    """Извлечённый текст, оставшийся в сессии, оператору не помогает."""
    texts = view_with_contract.document_texts

    assert len(texts) == 1
    assert texts[0].extracted is True
    assert "не позднее 15.01.2026" in texts[0].text


def test_hints_point_at_places_and_claim_nothing(view_with_contract) -> None:
    """Совпадение по словам — подсказка, где смотреть, а не установленный факт."""
    hints = view_with_contract.hints

    assert hints
    for hint in hints:
        assert "совпадения по словам" in hint.note_ru.lower()
        assert "утверждение о факте делает оператор" in hint.note_ru.lower()


def test_dates_from_the_document_are_offered_for_date_gaps(view_with_contract) -> None:
    """Пробел о сроке закрывается датой, поэтому даты ищутся отдельно."""
    from datetime import date

    found = {candidate.value for hint in view_with_contract.hints for candidate in hint.dates}

    assert date(2026, 1, 15) in found
    assert date(2026, 1, 20) in found


def test_reading_a_document_changes_no_fact(view_with_contract) -> None:
    """Главная граница: текст извлечён, но вывод по делу тот же."""
    plain = CaseSession(build_demo_case_inputs()).build_view()

    assert view_with_contract.verdict.headline_ru == plain.verdict.headline_ru
    assert view_with_contract.gaps.blocking_count == plain.gaps.blocking_count
    assert view_with_contract.reasoning.line[0].value == plain.reasoning.line[0].value


def test_no_hints_without_documents() -> None:
    """Подсказка без документа была бы подсказкой из ниоткуда."""
    assert build_gap_hints([], []) == []
