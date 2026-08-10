"""Тесты измерения покрытия реальной практики институтами пакета."""

import importlib

import pytest

from causa.institutional.contracts.practice_base import PRACTICE_BASE_PATH, load_practice_base
from causa.institutional.contracts.practice_coverage import (
    INSTITUTE_ARTICLE_RANGES,
    KNOWN_GAPS_RU,
    article_sort_key,
    cover_case,
    institutes_for_article,
    measure_practice_coverage,
)


def test_point_articles_take_their_place_in_the_order() -> None:
    """Статья с точкой стоит после своей основной, а не после следующей."""
    ordered = ["157", "157.1", "158", "308", "308.3", "309", "429", "429.2", "430"]

    assert sorted(ordered, key=article_sort_key) == ordered


def test_every_named_institute_exists_as_a_module() -> None:
    """Карта покрытия не может ссылаться на институт, которого в пакете нет."""
    for name in INSTITUTE_ARTICLE_RANGES:
        importlib.import_module(f"causa.institutional.contracts.{name}")


def test_ranges_are_well_formed() -> None:
    """Нижняя граница диапазона не может быть выше верхней."""
    for name, ranges in INSTITUTE_ARTICLE_RANGES.items():
        for low, high in ranges:
            assert article_sort_key(low) <= article_sort_key(high), name


def test_liability_chapter_is_not_swallowed_by_obligation_dynamics() -> None:
    """Модель динамики обязательства не выдаётся за модель ответственности.

    Строка версии заявляет статьи 382–419, то есть вместе с главой 25. Предикаты
    разбирают перемену лиц и прекращение обязательства, но не ответственность.
    Пока карта покрытия повторяла заявленный диапазон, статьи 403 и 404
    считались покрытыми, хотя их не разбирал ни один институт. Пробел закрыт
    отдельным институтом, а не расширением этой модели.
    """
    assert institutes_for_article("407") == ["obligation_dynamics"]
    assert "obligation_dynamics" not in institutes_for_article("403")
    assert institutes_for_article("403") == ["attribution_delay"]
    assert institutes_for_article("404") == ["attribution_delay"]


def test_repository_export_has_no_unexplained_gaps() -> None:
    """Каждая непокрытая статья реальной практики либо закрыта, либо объяснена."""
    if not PRACTICE_BASE_PATH.exists():
        pytest.skip("Выгрузка ещё не получена.")

    report = measure_practice_coverage(load_practice_base())

    assert report.total_cases > 0
    assert report.unexplained_gaps == []
    assert all(article in KNOWN_GAPS_RU for article in report.uncovered_articles)


def test_case_coverage_names_the_missing_article() -> None:
    """Дело с непокрытой статьёй перестаёт считаться полностью покрытым."""
    inventory = load_practice_base()
    if not inventory.present:
        pytest.skip("Выгрузка ещё не получена.")

    with_gap = [cover_case(case) for case in inventory.cases]
    incomplete = [entry for entry in with_gap if not entry.fully_covered]

    assert incomplete, "В выгрузке нет ни одного дела с непокрытой статьёй — проверьте карту."
    for entry in incomplete:
        assert entry.uncovered_articles
        assert all(article in KNOWN_GAPS_RU for article in entry.uncovered_articles)
