"""Тесты обхода кодекса: измерение полноты, не зависящее от отбора дел."""

import pytest

from causa.institutional.contracts.code_coverage import (
    CODE_GAP_REASONS_RU,
    CODE_STRUCTURE_PATH,
    articles_beyond_declared_ranges,
    gap_reason_ru,
    load_code_structure,
    measure_code_coverage,
)
from causa.institutional.contracts.practice_base import normalize_article
from causa.institutional.contracts.practice_coverage import article_sort_key


def test_article_numbers_have_three_levels_not_two() -> None:
    """«123.20-4» — настоящий номер статьи, а не порча данных.

    Пакет отвергал такие номера как недопустимые, и держалось это потому, что
    практика в главу 4 не заходила. Выгрузка структуры кодекса нашла двенадцать
    таких статей.
    """
    assert normalize_article("123.20-4") == "123.20-4"
    assert article_sort_key("123.20") < article_sort_key("123.20-4")
    assert article_sort_key("123.20-4") < article_sort_key("123.21")
    # Номер не превращается в число: 123.7 идёт до 123.16, а не после.
    assert article_sort_key("123.7") < article_sort_key("123.16")


def test_the_export_is_contiguous_by_chapter_and_section() -> None:
    """Главы и разделы обязаны идти сплошняком, без разрывов и наложений.

    Разрыв означал бы, что выгрузка потеряла статьи, а наложение — что границы
    глав определены неверно. И то и другое сделало бы измерение ложным.
    """
    structure = load_code_structure()
    if not structure.present:
        pytest.skip("Выгрузка структуры кодекса ещё не получена.")

    for part in {item.part for item in structure.articles}:
        items = [item for item in structure.articles if item.part == part]
        for first, second in zip(items, items[1:]):
            assert article_sort_key(first.number) < article_sort_key(second.number)
        for field in ("chapter_number", "section_ru"):
            seen: set[str] = set()
            previous = None
            for item in items:
                value = getattr(item, field)
                if value != previous:
                    assert value not in seen, (part, field, value)
                    seen.add(value)
                    previous = value


def test_repealed_articles_are_not_counted_as_gaps() -> None:
    """Утратившей силу статье институт не нужен.

    Исключить их из выгрузки было бы хуже: в нумерации осталась бы дыра, и обход
    принял бы её за пробел.
    """
    structure = load_code_structure()
    if not structure.present:
        pytest.skip("Выгрузка структуры кодекса ещё не получена.")

    assert structure.repealed > 0
    report = measure_code_coverage(structure)
    repealed = {item.number for item in structure.articles if not item.in_force}
    for gap in report.gaps:
        assert not (set(gap.articles) & repealed), gap.span


def test_every_uncovered_article_is_explained() -> None:
    """Непокрытая статья обязана быть либо границей модели, либо пробелом."""
    report = measure_code_coverage(load_code_structure())
    if not report.present:
        pytest.skip("Выгрузка структуры кодекса ещё не получена.")

    assert report.unexplained == [], report.unexplained
    for gap in report.gaps:
        assert gap.kind_ru in {"граница", "пробел"}, gap.span
        assert len(gap.reason_ru) > 60, gap.span


def test_boundary_and_gap_are_kept_apart() -> None:
    """Граница и пробел — разные ответы, и один не выдаётся за другой.

    Граница говорит «эту часть кодекса пакет не моделирует и не собирается».
    Пробел говорит «эту статью следует смоделировать, её пропустили». Свести их
    в одну графу значило бы объявить любое отсутствие сознательным решением.
    """
    report = measure_code_coverage(load_code_structure())
    if not report.present:
        pytest.skip("Выгрузка структуры кодекса ещё не получена.")

    assert report.declared_boundaries > 0
    assert report.real_gaps > 0
    assert report.declared_boundaries + report.real_gaps == len(report.gaps)


def test_a_gap_inside_a_claimed_institute_is_named_as_such() -> None:
    """Пробел внутри объявленного института — не граница модели.

    Институт банковского вклада заявляет 834–844 и обрывается на статье 844.1:
    номер отличается на долю, и статья выпала незамеченной. Практика туда не
    заходила, и без обхода это не открылось бы.

    Самый крупный пробел такого рода — статьи 860.1–860.15 внутри главы 45,
    которую институт банковского счёта заявляет своей, — закрыт в версии 1.5.0.
    """
    report = measure_code_coverage(load_code_structure())
    if not report.present:
        pytest.skip("Выгрузка структуры кодекса ещё не получена.")

    inside = [gap for gap in report.gaps if gap.span == "844.1"]
    assert len(inside) == 1
    assert inside[0].kind_ru == "пробел"
    assert len(inside[0].articles) == 1


def test_a_reason_is_found_per_article_not_per_chapter() -> None:
    """В одной главе могут стоять рядом граница и пробел.

    Глава 27: статья 420 — объявленная граница, статьи 427 и 431.1 — пробелы.
    Поиск причины по участку, который вывела группировка, их не нашёл бы.
    """
    assert gap_reason_ru("420")[0] == "граница"
    assert gap_reason_ru("427")[0] == "пробел"
    assert gap_reason_ru("431.1")[0] == "пробел"
    # Диапазонный ключ отвечает за каждую статью внутри себя.
    assert gap_reason_ru("926.4")[0] == "пробел"
    assert gap_reason_ru("100")[0] == "граница"


def test_no_institute_claims_an_article_the_code_does_not_have() -> None:
    """Карта диапазонов не выдумывает статей.

    До выгрузки это утверждение проверить было нечем: пакет знал только границы,
    которые сам и объявил.
    """
    if not CODE_STRUCTURE_PATH.exists():
        pytest.skip("Выгрузка структуры кодекса ещё не получена.")

    assert articles_beyond_declared_ranges() == []


def test_the_gap_table_names_only_articles_that_are_actually_uncovered() -> None:
    """Запись о пробеле не должна объяснять несуществующее событие."""
    report = measure_code_coverage(load_code_structure())
    if not report.present:
        pytest.skip("Выгрузка структуры кодекса ещё не получена.")

    named = {gap.span for gap in report.gaps}
    for span in CODE_GAP_REASONS_RU:
        assert span in named, span
