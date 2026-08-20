"""Спор двух миров и неустановленные факты — в окне дела, а не в библиотеке.

Модуль без потребителя — это объявленное без исполняемого, а проект уже пять раз
на этом обжигался. Здесь проверяется, что оба доходят до оператора и что
объявить факт неустановленным можно действием, а не правкой кода.
"""

import pytest

from causa.ui.desktop import build_demo_case_inputs, build_demo_case_view
from causa.ui.server import DesktopService
from causa.ui.session import CaseSession
from causa.reasoning.three_valued import OutcomeStatus, UnknownFactError

WORKSPACE = "ws-demo-supply"
CASE = "case-supply-1"


@pytest.fixture(scope="module")
def view():
    return build_demo_case_view()


def test_the_window_carries_both(view) -> None:
    assert view.worlds.conclusions
    assert view.uncertainty.outcomes


def test_facts_without_a_document_are_contested(view) -> None:
    """Пока факт держится на одном утверждении, его читают по-разному.

    К демонстрационному делу документов не приложено, поэтому спорны все факты,
    и это утверждение о деле, а не поломка.
    """
    assert len(view.worlds.contested) == 13
    assert any(item.switches for item in view.worlds.contested)


def test_the_dispute_shows_where_the_position_is_vulnerable(view) -> None:
    split = [
        item
        for item in view.worlds.conclusions
        if item.in_claimant_world != item.in_respondent_world
    ]

    assert split
    assert any(item.outcome == "breach_issue" for item in split)


def test_without_declared_unknowns_the_third_value_changes_nothing(view) -> None:
    assert view.uncertainty.unknown_facts == []
    assert all(item.status is not OutcomeStatus.DEPENDS for item in view.uncertainty.outcomes)


def test_declaring_a_fact_unknown_resolves_by_burden() -> None:
    """Действие оператора, а не правка кода."""
    session = CaseSession(build_demo_case_inputs())
    after = session.declare_unknown(["valid_exception_applies"])
    breach = after.uncertainty.outcome("breach_issue")

    assert after.uncertainty.unknown_facts == ["valid_exception_applies"]
    assert breach.status is OutcomeStatus.DEPENDS
    assert breach.resolved is True
    assert "ответчик" in breach.resolution_ru


def test_the_same_action_can_swing_the_other_way() -> None:
    session = CaseSession(build_demo_case_inputs())
    after = session.declare_unknown(["duty_exists"])
    breach = after.uncertainty.outcome("breach_issue")

    assert breach.resolved is False
    assert "истец" in breach.resolution_ru


def test_a_fact_outside_the_model_is_refused() -> None:
    session = CaseSession(build_demo_case_inputs())

    with pytest.raises(UnknownFactError):
        session.declare_unknown(["heir_accepted_inheritance"])


def test_the_endpoint_recomputes_the_case() -> None:
    service = DesktopService()
    payload = service.declare_unknown(WORKSPACE, CASE, {"facts": ["duty_exists"]})

    assert payload["unknown_facts"] == ["duty_exists"]
    assert "не считается опровергнутым" in payload["note_ru"]
    outcomes = payload["case"]["uncertainty"]["outcomes"]
    breach = next(item for item in outcomes if item["outcome"] == "breach_issue")
    assert breach["status"] == "depends"
    assert breach["resolved"] is False


def test_the_endpoint_refuses_a_malformed_body() -> None:
    service = DesktopService()

    with pytest.raises(ValueError):
        service.declare_unknown(WORKSPACE, CASE, {"facts": "duty_exists"})
