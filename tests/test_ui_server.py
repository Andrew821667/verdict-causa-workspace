"""Тесты стенда: сборка рабочего стола и HTTP-сервис."""

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from causa.ui.desktop import (
    DEMO_WORKSPACE_ID,
    PRACTICE_WORKSPACE_ID,
    build_demo_desktop,
)
from causa.ui.server import STATIC_ROOT, DesktopService, build_handler


@pytest.fixture(scope="module")
def desktop():
    return build_demo_desktop()


@pytest.fixture(scope="module")
def service(desktop):
    return DesktopService(desktop)


@pytest.fixture(scope="module")
def base_url(service):
    server = ThreadingHTTPServer(("127.0.0.1", 0), build_handler(service))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def _get(url: str):
    with urllib.request.urlopen(url) as response:  # noqa: S310 - локальный стенд
        return response.status, json.loads(response.read())


def _post(url: str, payload: dict):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:  # noqa: S310 - локальный стенд
        return response.status, json.loads(response.read())


def test_the_stand_carries_both_workspaces(desktop) -> None:
    """Демонстрационное дело и реальная практика — разные контуры."""
    ids = [workspace.id for workspace in desktop.desk.organisation.workspaces]

    assert ids == [DEMO_WORKSPACE_ID, PRACTICE_WORKSPACE_ID]
    assert len(desktop.case_views) == 5


def test_practice_cases_carry_the_caveat(desktop) -> None:
    """Без оговорки стенд внушал бы, что система решила дело как суд."""
    practice = [v for v in desktop.case_views if v.workspace_id == PRACTICE_WORKSPACE_ID]

    assert len(practice) == 4
    for view in practice:
        assert "наложены на демонстрационное дело" in view.caveat_ru
        assert "Позиция суда:" in view.caveat_ru


def test_the_demo_case_needs_no_caveat(desktop) -> None:
    """Оговорка ставится там, где она правдива, а не везде на всякий случай."""
    demo = next(v for v in desktop.case_views if v.workspace_id == DEMO_WORKSPACE_ID)

    assert demo.caveat_ru == ""


def test_cards_report_gaps_and_debt(desktop) -> None:
    """Карточка дела показывает состояние, а не только название."""
    demo = next(v for v in desktop.case_views if v.workspace_id == DEMO_WORKSPACE_ID)
    card = demo.card()

    assert card.cluster_ru == "Поставка"
    assert card.blocking_gaps > 0
    assert card.open_debt_ru


def test_desktop_endpoint_lists_only_accessible_workspaces(base_url) -> None:
    status, payload = _get(f"{base_url}/api/desktop")

    assert status == 200
    assert payload["operator"]["role_ru"] == "юрист"
    assert {ws["id"] for ws in payload["workspaces"]} == {
        DEMO_WORKSPACE_ID,
        PRACTICE_WORKSPACE_ID,
    }


def test_case_endpoint_returns_the_whole_window(base_url) -> None:
    status, payload = _get(f"{base_url}/api/case/{DEMO_WORKSPACE_ID}/case-supply-1")

    assert status == 200
    assert payload["reasoning"]["line"]
    assert len(payload["reasoning"]["registers"]) == 3
    assert payload["gaps"]["gaps"]
    assert payload["map"]["nodes"]
    assert payload["qualification"]["primary"]["institute"] == "supply"


def test_an_inaccessible_workspace_is_refused_by_the_desk(base_url) -> None:
    """Изоляция не зависит от того, какой URL кто-то подобрал."""
    with pytest.raises(urllib.error.HTTPError) as failure:
        _get(f"{base_url}/api/case/ws-secret/case-supply-1")

    assert failure.value.code == 403
    assert "изоляция" in json.loads(failure.value.read())["error_ru"]


def test_a_missing_case_is_not_a_server_error(base_url) -> None:
    with pytest.raises(urllib.error.HTTPError) as failure:
        _get(f"{base_url}/api/case/{DEMO_WORKSPACE_ID}/case-unknown")

    assert failure.value.code == 404


def test_a_signal_remark_returns_a_proposed_candidate(base_url) -> None:
    status, payload = _post(
        f"{base_url}/api/case/{DEMO_WORKSPACE_ID}/case-supply-1/remark",
        {
            "id": "remark-test-signal",
            "kind": "missing_rule",
            "text_ru": "Не учтён пункт 8 постановления Пленума о просрочке кредитора.",
            "as_learning_signal": True,
        },
    )

    assert status == 201
    assert payload["candidate"]["status"] == "proposed"
    assert payload["candidate_type"] == "gap_heuristic"
    assert payload["required_stages_ru"]


def test_a_remark_with_an_unknown_kind_is_refused(base_url) -> None:
    with pytest.raises(urllib.error.HTTPError) as failure:
        _post(
            f"{base_url}/api/case/{DEMO_WORKSPACE_ID}/case-supply-1/remark",
            {"kind": "приказ", "text_ru": "…"},
        )

    assert failure.value.code == 400


def test_remarks_appear_in_the_case_after_they_are_added(base_url) -> None:
    _post(
        f"{base_url}/api/case/{DEMO_WORKSPACE_ID}/case-supply-1/remark",
        {
            "id": "remark-test-visible",
            "kind": "clarification",
            "text_ru": "Срок продлён дополнительным соглашением от 12 марта.",
        },
    )

    _, payload = _get(f"{base_url}/api/case/{DEMO_WORKSPACE_ID}/case-supply-1")
    ids = [outcome["remark_id"] for outcome in payload["remarks"]["outcomes"]]

    assert "remark-test-visible" in ids


def test_static_files_exist_and_are_served(base_url) -> None:
    for name in ("index.html", "styles.css", "app.js"):
        assert (STATIC_ROOT / name).is_file(), name
        with urllib.request.urlopen(f"{base_url}/{name}") as response:  # noqa: S310
            assert response.status == 200


def test_path_traversal_is_refused(base_url) -> None:
    with pytest.raises(urllib.error.HTTPError) as failure:
        urllib.request.urlopen(f"{base_url}/../server.py")  # noqa: S310

    assert failure.value.code == 404
