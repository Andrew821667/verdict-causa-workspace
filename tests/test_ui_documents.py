"""Тесты загрузки документов и пересчёта дела."""

import base64

import pytest

from causa.ui.documents import (
    MAX_DOCUMENT_BYTES,
    ClosureKind,
    DocumentTooLargeError,
    GapClosure,
    apply_closure,
    build_document,
    document_source,
)
from causa.ui.server import DesktopService
from causa.ui.session import GapClosureConflict

WORKSPACE = "ws-demo-supply"
CASE = "case-supply-1"


@pytest.fixture(scope="module")
def service():
    return DesktopService()


def _upload(service, filename="Дополнительное соглашение.pdf", content=b"annex"):
    return service.add_document(
        WORKSPACE,
        CASE,
        {
            "filename": filename,
            "content_base64": base64.b64encode(content).decode(),
            "media_type": "application/pdf",
        },
    )


def test_the_system_says_plainly_that_it_draws_no_conclusions_from_the_file(service) -> None:
    """Файл, из которого система якобы что-то поняла, — худший вид обмана здесь.

    Текст из документа стенд теперь достаёт и показывает. Выводов из него он
    по-прежнему не делает, и разница названа в ответе прямо: иначе извлечение
    текста читалось бы как понимание.
    """
    uploaded = _upload(service)

    assert "выводов из текста" in uploaded["note_ru"].lower()
    assert "не делает" in uploaded["note_ru"]
    assert uploaded["document"]["sha256"]


def test_a_document_becomes_a_factual_source_without_content(service) -> None:
    """Ссылка на незарегистрированный источник непроверяема, а текста у нас нет."""
    document = build_document(case_id=CASE, filename="Акт.pdf", content=b"act", uploaded_by="op")
    source = document_source(document)

    assert source.id == document.id
    assert source.source_type.value == "fact"
    assert "не" in source.text and "разбирал" in source.text
    assert document.sha256 in source.text


def test_the_same_file_is_not_attached_twice(service) -> None:
    """Отпечаток одинаковый — значит это тот же документ, а не второй."""
    first = _upload(service, content=b"same bytes")
    second = _upload(service, content=b"same bytes")

    assert first["document"]["id"] == second["document"]["id"]


def test_a_file_beyond_the_limit_is_refused() -> None:
    with pytest.raises(DocumentTooLargeError, match="МиБ"):
        build_document(
            case_id=CASE,
            filename="огромный.pdf",
            content=b"x" * (MAX_DOCUMENT_BYTES + 1),
            uploaded_by="op",
        )


def test_a_closure_records_the_document_in_the_provenance(service) -> None:
    """Вывод меняет утверждение оператора, а документ — записанное основание."""
    document = build_document(
        case_id=CASE, filename="Расчёт.pdf", content=b"calc", uploaded_by="op"
    )
    session = service.session(WORKSPACE, CASE)
    request = session.inputs.request
    closure = GapClosure(
        gap_id="gap:decisive:request_damages_with_causation",
        document_id=document.id,
        kind=ClosureKind.ASSERTED_FACT,
        fact_updates={"causation_established": True},
    )

    updated = apply_closure(request, closure, document)

    assertion = next(
        item
        for item in updated.case_evidence.assertions
        if item.predicate.value == "causation_established"
    )
    assert assertion.value is True
    assert document.id in assertion.source_refs


def test_a_derived_fact_cannot_be_asserted(service) -> None:
    """Пропуск срока вычисляется из дат, а не утверждается галочкой."""
    document = build_document(
        case_id=CASE, filename="Соглашение.pdf", content=b"annex", uploaded_by="op"
    )
    closure = GapClosure(
        gap_id="gap:decisive:correct_performance_date",
        document_id=document.id,
        kind=ClosureKind.ASSERTED_FACT,
        fact_updates={"due_date_missed": False},
    )

    with pytest.raises(ValueError, match="вычисляются"):
        apply_closure(service.session(WORKSPACE, CASE).inputs.request, closure, document)


def test_a_closure_by_date_needs_a_date(service) -> None:
    document = build_document(
        case_id=CASE, filename="Соглашение.pdf", content=b"annex", uploaded_by="op"
    )
    closure = GapClosure(
        gap_id="gap:decisive:correct_performance_date",
        document_id=document.id,
        kind=ClosureKind.SUPPLIED_DATE,
    )

    with pytest.raises(ValueError, match="ни одной даты"):
        apply_closure(service.session(WORKSPACE, CASE).inputs.request, closure, document)


def test_a_conflicting_closure_is_rolled_back_and_explained(service) -> None:
    """Слой сверки не даёт решателю молча выбрать одну из двух версий факта.

    На демонстрационном деле один и тот же факт описан в нескольких институтах,
    поэтому закрытие пробела расходится с тем, что заявлено там. Изменение
    откатывается, а расхождения показываются: согласовать их должен человек.
    """
    uploaded = _upload(service, filename="Акт приёмки.pdf", content=b"acceptance")
    session = service.session(WORKSPACE, CASE)
    before = session.request

    with pytest.raises(GapClosureConflict) as failure:
        service.close_gap(
            WORKSPACE,
            CASE,
            {
                "gap_id": "gap:decisive:request_damages_with_causation",
                "document_id": uploaded["document"]["id"],
                "kind": "asserted_fact",
                "fact_updates": {"causation_established": True, "loss_claimed": True},
            },
        )

    payload = failure.value.payload()
    assert payload["conflicts_ru"]
    assert "не выбирает версию" in payload["explanation_ru"]
    # Откат: запрос дела остался прежним, а закрытие не записано.
    assert session.request is before
    assert session.closures == []


def test_the_document_stays_attached_after_a_conflict(service) -> None:
    """Отказ пересчёта не должен терять приложенный файл."""
    session = service.session(WORKSPACE, CASE)

    assert session.documents
    assert all(document.case_id == CASE for document in session.documents)


def test_an_unknown_document_cannot_close_a_gap(service) -> None:
    with pytest.raises(KeyError, match="не приложен"):
        service.close_gap(
            WORKSPACE,
            CASE,
            {
                "gap_id": "gap:decisive:activate_valid_exception",
                "document_id": "doc:case-supply-1:0000000000000000",
                "kind": "asserted_fact",
                "fact_updates": {"valid_exception_applies": True},
            },
        )


def test_uploading_into_another_workspace_is_refused(service) -> None:
    """Изоляция проверяется до того, как файл где-либо сохранится."""
    with pytest.raises(PermissionError, match="ws-secret"):
        service.add_document(
            "ws-secret",
            CASE,
            {"filename": "чужое.pdf", "content_base64": base64.b64encode(b"x").decode()},
        )
