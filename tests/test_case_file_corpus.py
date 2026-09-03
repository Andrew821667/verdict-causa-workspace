"""Приёмная сторона корпуса материалов дел готова до прихода выгрузки.

Проверки здесь не о данных — их ещё нет, — а о том, что контракт данных
отвергает те выгрузки, ради отказа от которых он и написан.
"""

import pytest
from pydantic import ValidationError

from causa.ui.case_file_corpus import (
    DOCUMENT_KINDS_RU,
    MIN_DOCUMENT_CHARACTERS,
    SOURCE_KINDS_RU,
    CaseFile,
    CaseFileCorpus,
    CaseFileDocument,
    describe_corpus_ru,
    load_case_file_corpus,
)

CONTRACT = "Договор поставки. Поставщик обязуется передать товар. " * 20
CLAIM = "Претензия. Требуем оплатить задолженность и возместить убытки. " * 20


def _document(**overrides) -> CaseFileDocument:
    fields = {
        "id": "doc-1",
        "kind": "договор",
        "title_ru": "Договор поставки № 1",
        "text": CONTRACT,
        "source_ref": "0173100000123000001",
        "source_kind": "еис_закупки",
    }
    fields.update(overrides)
    return CaseFileDocument(**fields)


def _case_file(**overrides) -> CaseFile:
    fields = {
        "id": "case-1",
        "title_ru": "Поставка оборудования",
        "dispute_ru": "Поставщик поставил товар с просрочкой, заказчик требует неустойку.",
        "documents": (
            _document(),
            _document(id="doc-2", kind="претензия", title_ru="Претензия", text=CLAIM),
        ),
    }
    fields.update(overrides)
    return CaseFile(**fields)


def test_a_missing_export_is_an_empty_corpus_not_a_failure() -> None:
    """Приёмная сторона держится готовой до прихода данных."""
    corpus = load_case_file_corpus()

    assert isinstance(corpus, CaseFileCorpus)
    assert describe_corpus_ru(corpus) == ["Корпус материалов дел пуст: выгрузка ещё не пришла."]


def test_a_title_instead_of_a_document_is_rejected() -> None:
    """Выгрузка с названием вместо текста читается как непустая, но бесполезна."""
    with pytest.raises(ValidationError, match="вместо документа выгружено его название"):
        _document(text="Договор поставки № 1 от 15.12.2025")

    assert MIN_DOCUMENT_CHARACTERS > 100


def test_editorial_apparatus_is_rejected() -> None:
    """Аппарат базы — не часть документа и портит поиск по словам."""
    with pytest.raises(ValidationError, match="редакционный аппарат"):
        _document(text=CONTRACT + "\n\nПутеводитель по договорной работе. Поставка.")


def test_personal_data_is_refused_rather_than_anonymised() -> None:
    """Обезличивание чужого документа — интерпретация, за которую никто не отвечает."""
    with pytest.raises(ValidationError, match="персональные данные"):
        _document(contains_personal_data=True)


def test_unknown_kinds_and_sources_are_named_not_swallowed() -> None:
    """Открытый список превратил бы корпус в свалку из «прочего»."""
    with pytest.raises(ValidationError, match="не описан"):
        _document(kind="письмо")
    with pytest.raises(ValidationError, match="не описан"):
        _document(source_kind="от_знакомого_юриста")

    # Каждый допустимый вид обязан объяснять, что он способен установить.
    for kind, what in DOCUMENT_KINDS_RU.items():
        assert len(what) > 15, kind
    for source, why in SOURCE_KINDS_RU.items():
        assert len(why) > 30, source


def test_a_case_file_without_a_contract_is_rejected() -> None:
    """Без договора остальные документы не к чему отнести."""
    claim = _document(id="doc-2", kind="претензия", title_ru="Претензия", text=CLAIM)
    notice = _document(id="doc-3", kind="уведомление", title_ru="Уведомление", text=CLAIM)

    with pytest.raises(ValidationError, match="нет договора"):
        _case_file(documents=(claim, notice))


def test_a_single_document_is_not_a_case_file() -> None:
    """Один договор измерял бы три предиката из двенадцати."""
    with pytest.raises(ValidationError):
        _case_file(documents=(_document(),))


def test_duplicate_identifiers_are_rejected_across_the_corpus() -> None:
    """Повтор идентификатора делает ссылку на документ бессмысленной."""
    with pytest.raises(ValidationError, match="повторяющимися идентификаторами"):
        CaseFileCorpus(case_files=(_case_file(), _case_file()))


def test_the_description_names_what_the_corpus_cannot_measure() -> None:
    """Молчание о нехватке читалось бы как полнота корпуса."""
    corpus = CaseFileCorpus(case_files=(_case_file(),))

    lines = " ".join(describe_corpus_ru(corpus))

    assert "Комплектов: 1" in lines
    assert "Ни одного документа таких видов" in lines
    assert "товарная_накладная" in lines


def test_a_case_file_without_a_claim_letter_is_reported() -> None:
    """Претензия — единственный источник убытков, причинной связи и требования."""
    only_contract = _case_file(
        documents=(
            _document(),
            _document(id="doc-2", kind="акт_приёма_передачи", title_ru="Акт", text=CONTRACT),
        )
    )

    lines = " ".join(describe_corpus_ru(CaseFileCorpus(case_files=(only_contract,))))

    assert "Комплектов без претензии: 1 из 1" in lines
