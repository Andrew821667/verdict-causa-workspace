"""Граница компетенции: где система обязана сказать «это не моё».

До этих проверок система на чужом деле не молчала — она уверенно ошибалась.
По делу о наследстве, где договора нет вовсе, вердикт заявлял: «Договор как
основание требований не действует: он не заключён, недействителен либо порочен
по форме», и предлагал разобрать основание недействительности.

Причина была в порядке проверок: «выводы не имеют эффекта» стояли первыми и не
отличали «договор порочен» от «договора в деле нет». Здесь закреплено, что
утверждение о собственной некомпетентности опережает любое утверждение о судьбе
сделки.
"""

import pytest

from causa.institutional.contracts.practice_coverage import (
    INSTITUTE_ARTICLE_RANGES,
    UNCOVERED_DOMAINS_RU,
    article_sort_key,
    institutes_for_article,
    uncovered_domain_ru,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.ui.gaps import build_gap_queue
from causa.ui.qualification import (
    SPECIALISATION,
    CaseScope,
    build_case_qualification,
    qualification_predicates,
)
from causa.ui.verdict import VerdictState, build_case_verdict


def _empty_request():
    """Дело, в котором не утверждено ни одного факта.

    Обнулить нужно все блоки доказательств разом: слой сверки отвергает набор,
    где один институт молчит, а соседний утверждает обратное, — и правильно
    делает.
    """
    request = build_synthetic_supply_analysis_request()
    updates = {}
    for field_name in type(request).model_fields:
        block = getattr(request, field_name)
        fields = getattr(type(block), "model_fields", None)
        if not fields:
            continue
        inner: dict[str, object] = {}
        if "assertions" in fields:
            inner["assertions"] = tuple(
                assertion.model_copy(update={"value": False}) for assertion in block.assertions
            )
        inner.update({name: False for name, spec in fields.items() if spec.annotation is bool})
        if field_name == "temporal_evidence":
            inner.update({"agreed_due_date": None, "actual_performance_date": None})
        if inner:
            updates[field_name] = block.model_copy(update=inner)
    return request.model_copy(update=updates)


@pytest.fixture(scope="module")
def empty_result():
    return run_reviewed_contract_analysis(
        _empty_request(), build_synthetic_supply_analysis_sources()
    )


@pytest.fixture(scope="module")
def supply_result():
    return run_reviewed_contract_analysis(
        build_synthetic_supply_analysis_request(), build_synthetic_supply_analysis_sources()
    )


def _verdict(result, articles=None):
    qualification = build_case_qualification(result, articles)
    return qualification, build_case_verdict(result, qualification, build_gap_queue(result))


def test_an_inheritance_case_is_refused_and_not_answered(empty_result) -> None:
    """Главная проверка: система больше не выдумывает недействительный договор."""
    qualification, verdict = _verdict(empty_result, ["1112", "1142"])

    assert qualification.scope is CaseScope.OUT_OF_SCOPE_SUSPECTED
    assert verdict.state is VerdictState.OUT_OF_SCOPE
    assert "недействителен" not in verdict.detail_ru
    assert "1112" in verdict.detail_ru
    assert "наследственное право" in " ".join(qualification.notes_ru).lower()


def test_an_empty_case_says_so_instead_of_ruling_on_the_contract(empty_result) -> None:
    """«Ничего не установлено» и «договор порочен» — разные утверждения."""
    qualification, verdict = _verdict(empty_result)

    assert qualification.scope is CaseScope.UNDETERMINED
    assert verdict.state is VerdictState.NOTHING_ESTABLISHED
    assert "недействителен" not in verdict.detail_ru


def test_a_covered_case_is_unaffected(supply_result) -> None:
    """Граница не имеет права мешать делу, которое система умеет разбирать."""
    qualification, verdict = _verdict(supply_result)

    assert qualification.scope is CaseScope.IN_SCOPE
    assert verdict.state is VerdictState.BREACH_ESTABLISHED


def test_a_covered_case_citing_uncovered_articles_is_warned_not_refused(supply_result) -> None:
    """Спор о поставке со ссылкой на часть четвёртую разбирается, но с оговоркой."""
    qualification, verdict = _verdict(supply_result, ["506", "1235"])

    assert qualification.scope is CaseScope.IN_SCOPE
    assert qualification.uncovered_articles == ["1235"]
    assert verdict.state is VerdictState.BREACH_ESTABLISHED
    assert any("1235" in line for line in verdict.qualifiers_ru)


def test_the_absence_of_a_cluster_is_shown_as_a_stop_and_not_a_remark(empty_result) -> None:
    _, verdict = _verdict(empty_result)
    metric = next(item for item in verdict.metrics if item.label_ru == "Тип договора")

    assert metric.value_ru == "не определён"
    assert metric.tone.value == "stop"


# --- карта непокрытых областей ----------------------------------------------


@pytest.mark.parametrize(
    ("article", "expected"),
    [
        ("1112", "наследственное"),
        ("1235", "интеллектуальной"),
        ("96", "юридические лица"),
        ("420", "понятие договора"),
    ],
)
def test_every_uncovered_area_carries_a_reason(article: str, expected: str) -> None:
    assert institutes_for_article(article) == []
    assert expected in uncovered_domain_ru(article).lower()


def test_uncovered_domains_do_not_overlap_the_covered_ones() -> None:
    """Область не может быть одновременно смоделированной и объявленной пробелом."""
    for low, high, _ in UNCOVERED_DOMAINS_RU:
        for name, ranges in INSTITUTE_ARTICLE_RANGES.items():
            for first, last in ranges:
                overlap = article_sort_key(first) <= article_sort_key(high) and article_sort_key(
                    low
                ) <= article_sort_key(last)
                assert not overlap, f"{name} {first}–{last} пересекается с пробелом {low}–{high}"


# --- мёртвые записи ---------------------------------------------------------


def test_every_specialisation_entry_can_actually_fire() -> None:
    """Запись о вытеснении без предиката квалификации — мёртвый код.

    Розничная купля-продажа и поставка для государственных нужд стояли в таблице
    вытеснения, не имея предиката вовсе: вытеснить они не могли никогда. Тест
    не даёт вернуть такую запись без предиката.
    """
    predicates = {key.split(":", 1)[0] for key in qualification_predicates()}
    dead = sorted(
        name for pair in SPECIALISATION.items() for name in pair if name not in predicates
    )

    assert not dead, f"в таблице вытеснения институты без предиката квалификации: {dead}"
