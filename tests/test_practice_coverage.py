"""Тесты измерения покрытия реальной практики институтами пакета."""

import importlib

import pytest

from causa.institutional.contracts.practice_base import PRACTICE_BASE_PATH, load_practice_base
from causa.institutional.contracts.practice_coverage import (
    GAP_REASON_UNKNOWN_RU,
    INSTITUTE_ARTICLE_RANGES,
    KNOWN_GAPS_RU,
    article_sort_key,
    cover_case,
    institutes_for_article,
    measure_practice_coverage,
    uncovered_domain_ru,
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


def test_point_gaps_answer_for_articles_just_past_an_institute() -> None:
    """Статья с точкой сразу за границей института объяснена, а не покрыта.

    Ловушка здесь в том, что номер отличается от покрытого на долю: 53.1 стоит
    вплотную к модели лиц (17–53). Расширить диапазон на такую статью означало
    бы объявить покрытым то, чего в предикатах нет.

    Статья 449.1 была вторым таким случаем — вплотную к модели порядка
    заключения (445–449). В версии 1.9.0 она смоделирована, и диапазон расширен
    вместе с предикатами; поэтому она проверяется ниже как покрытая, а не как
    объяснённая.
    """
    for article in ("53.1",):
        assert institutes_for_article(article) == [], article
        assert article in KNOWN_GAPS_RU, article
        assert uncovered_domain_ru(article) != GAP_REASON_UNKNOWN_RU, article

    assert institutes_for_article("449.1") == ["procedure"]
    assert "449.1" not in KNOWN_GAPS_RU


def test_repository_export_has_no_unexplained_gaps() -> None:
    """Каждая непокрытая статья реальной практики либо закрыта, либо объяснена."""
    if not PRACTICE_BASE_PATH.exists():
        pytest.skip("Выгрузка ещё не получена.")

    report = measure_practice_coverage(load_practice_base())

    assert report.total_cases > 0
    assert report.unexplained_gaps == []
    # Причина спрашивается у `uncovered_domain_ru`, а не у одной из двух карт:
    # статью может объяснять и точечная запись KNOWN_GAPS_RU, и целая
    # непокрытая область UNCOVERED_DOMAINS_RU.
    for article in report.uncovered_articles:
        assert uncovered_domain_ru(article) != GAP_REASON_UNKNOWN_RU, article


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
        for article in entry.uncovered_articles:
            assert uncovered_domain_ru(article) != GAP_REASON_UNKNOWN_RU, article
