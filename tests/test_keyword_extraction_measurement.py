"""Измерение ошибки словарного извлекателя закреплено числами, а не оценкой.

О совпадении по словам в проекте было написано, что оно «ошибается
предсказуемо». Это оценка, а не измерение. Тесты ниже держат измерение живым:
эталон обязан покрывать ровно то, что извлекатель предлагает, и цифры обязаны
ломаться при изменении словаря, а не подстраиваться под него.
"""

import json
from pathlib import Path

from causa.ui.fact_extraction import KEYWORD_PRECISION, UNMEASURED_KEYWORD_CONFIDENCE
from causa.ui.extraction_evaluation import (
    MISS_KINDS_RU,
    KeywordExtractionReport,
    load_gold,
    run_keyword_extraction_evaluation,
)


def test_gold_covers_exactly_what_the_extractor_proposes() -> None:
    """Ни одного предложения без эталона и ни одной записи впустую.

    Это и есть защита от подгонки: расширить словарь и молча улучшить точность
    нельзя — новое предложение придёт неразмеченным и уронит проверку.
    """
    report = run_keyword_extraction_evaluation()

    assert report.unlabelled == [], report.unlabelled
    assert report.proposals == report.correct + report.wrong + report.undetermined
    # Эталон шире, чем нынешняя выдача: в нём остались подсказки, снятые
    # стоп-фразами. Это не мусор, а регрессия на сами правила.
    assert len(load_gold()) == report.proposals + len(report.suppressed_by_rules)


def test_the_stop_phrases_removed_only_wrong_proposals() -> None:
    """Правило, снимающее верную подсказку, отнимает больше, чем даёт.

    Стоп-фразы вводились ровно на этом условии: они убирают шум, а не полноту.
    Проверка держит условие, а не однажды измеренную цифру: расширить список
    оборотов и потерять верную подсказку молча нельзя.
    """
    report = run_keyword_extraction_evaluation()

    assert report.wrongly_suppressed == [], report.wrongly_suppressed
    assert len(report.suppressed_by_rules) == 24


def test_every_label_states_a_reason() -> None:
    """Разметка без причины неотличима от подгонки под желаемое число."""
    for label in load_gold():
        assert label.verdict in ("да", "нет", "не определено"), label
        assert len(label.reason_ru) > 20, label
        if label.verdict == "да":
            assert label.kind is None, label
        else:
            assert label.kind in MISS_KINDS_RU, label


def test_the_measured_numbers_are_pinned() -> None:
    """Числа закреплены: их изменение обязано быть замеченным и объяснённым."""
    report = run_keyword_extraction_evaluation()

    assert report.documents == 55
    # Предложений было 194 при точности 64 %; стоп-фразы сняли 24 подсказки,
    # все до одной ошибочные, и точность поднялась до 73 %.
    assert report.proposals == 170
    assert report.correct == 124
    assert 0.72 < report.precision < 0.74
    # Полнота измерена по одному предикату, где эталон известен без разметки:
    # все 55 записей — судебные акты по заявленным требованиям.
    assert 0.86 < report.recall_remedy_requested < 0.88


def test_the_worst_predicates_are_named_not_averaged() -> None:
    """Средняя точность прячет то, ради чего измерение и делалось.

    Причинная связь промахивается чаще всех: «вследствие» в русском юридическом
    тексте почти никогда не связывает нарушение с убытками. Стоп-фразы подняли
    её с 8 % до 20 %, и это по-прежнему худший предикат набора — списком слов
    отрицание и смежные понятия не берутся. Общая цифра это скрывает.
    """
    report = run_keyword_extraction_evaluation()
    scores = {item.predicate: item for item in report.per_predicate}

    assert scores["causation_established"].precision < 0.25
    # А там, где слово однозначно, поиск по словам работает хорошо.
    assert scores["remedy_requested"].precision > 0.95


def test_every_kind_of_miss_is_described_in_russian() -> None:
    """Промах без разбора причины не подсказывает, что чинить."""
    report = run_keyword_extraction_evaluation()

    assert report.miss_kinds
    for kind, count in report.miss_kinds.items():
        assert count > 0
        assert len(MISS_KINDS_RU[kind]) > 60, kind


def test_the_exported_report_matches_the_run() -> None:
    """Выгруженный отчёт обязан воспроизводиться, а не жить своей жизнью."""
    path = Path("examples/keyword_extraction_report.json")
    stored = KeywordExtractionReport.model_validate(json.loads(path.read_text(encoding="utf-8")))

    assert stored == run_keyword_extraction_evaluation()


def test_the_confidence_shown_to_the_lawyer_is_the_measured_one() -> None:
    """Уверенность подсказки обязана совпадать с измеренной точностью.

    Иначе таблица в извлекателе жила бы отдельно от измерения, и подправить
    число, не переразметив корпус, стало бы возможно.
    """
    report = run_keyword_extraction_evaluation()
    measured = {item.predicate: item.precision for item in report.per_predicate}

    assert set(KEYWORD_PRECISION) == set(measured), set(KEYWORD_PRECISION) ^ set(measured)
    for predicate, declared in KEYWORD_PRECISION.items():
        assert abs(declared - measured[predicate]) < 0.01, predicate

    # Неизмеренное не вправе выглядеть надёжнее самого ненадёжного измеренного.
    assert UNMEASURED_KEYWORD_CONFIDENCE < min(KEYWORD_PRECISION.values())
