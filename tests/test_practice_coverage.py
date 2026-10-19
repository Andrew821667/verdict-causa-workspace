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


def test_point_articles_are_not_swallowed_by_the_neighbouring_institute() -> None:
    """Статья с точкой за границей института покрыта своими предикатами, а не чужими.

    Ловушка здесь в том, что номер отличается от покрытого на долю: 53.1 стоит
    вплотную к модели лиц (17–53), 449.1 — вплотную к модели порядка заключения
    (445–449). Расширить соседний диапазон на такую статью означало бы объявить
    покрытым то, чего в его предикатах нет.

    Обе статьи прошли один путь: сначала точечный пробел с названной причиной,
    затем собственные предикаты. Статья 449.1 смоделирована в версии 1.9.0
    институтом порядка заключения, статья 53.1 — отдельным институтом
    ответственности управляющих лиц. Поэтому обе проверяются как покрытые,
    и проверяется именно то, кто их покрывает: не сосед по номеру.
    """
    assert institutes_for_article("53.1") == ["management_liability"]
    assert "53.1" not in KNOWN_GAPS_RU
    assert institutes_for_article("53") == ["persons"]

    assert institutes_for_article("449.1") == ["procedure"]
    assert "449.1" not in KNOWN_GAPS_RU


def test_bankruptcy_article_is_not_swallowed_by_persons_institute() -> None:
    """Статья 25 покрыта своим институтом, а не институтом лиц.

    Строка версии модели лиц заявляет статьи 17–53 целиком, но предикаты
    разбирают право- и дееспособность, а не банкротство, поэтому статья 25
    вырезана из диапазона. Карман держался записью о пробеле, пока запись не
    оказалась ложной во второй половине: она утверждала, что эту область пакет
    моделирует отдельным институтом банкротства, тогда как четыре института
    банкротства о должнике-гражданине не знают ничего.

    Проверяется теперь именно то, кто покрывает статью: не сосед по номеру.
    """
    assert institutes_for_article("25") == ["citizen_bankruptcy"]
    assert "25" not in KNOWN_GAPS_RU
    assert institutes_for_article("24") == ["persons"]
    assert institutes_for_article("26") == ["persons"]


def test_the_point_gap_map_is_empty_on_purpose() -> None:
    """Все три точечных пробела закрыты институтами, и карта оставлена пустой.

    Статья 449.1 закрыта в версии 1.9.0, статья 420 — в 1.24.0, статья 25 — в
    1.25.0. Карта остаётся на месте по той же причине, по которой оставлены
    опустевшие категории аудита связности: следующий пробел, найденный
    измерением, должен попасть в названное место, а не создавать его.
    """
    assert KNOWN_GAPS_RU == {}
    # Непокрытые статьи практики объясняются теперь только картой областей.
    assert uncovered_domain_ru("113") != GAP_REASON_UNKNOWN_RU


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
