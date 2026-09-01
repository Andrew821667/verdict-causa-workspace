"""Тесты стенда: сборка рабочего стола и HTTP-сервис."""

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from causa.ui.desktop import (
    BANKRUPTCY_WORKSPACE_ID,
    DEMO_WORKSPACE_ID,
    PRACTICE_WORKSPACE_ID,
    build_demo_desktop,
)
from causa.ui.server import (
    STATIC_ROOT,
    WEB_ROOT,
    DesktopService,
    build_handler,
    static_root,
)


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


def test_the_stand_carries_all_three_workspaces(desktop) -> None:
    """Демонстрация, реальная практика и карта банкротства — разные контуры."""
    ids = [workspace.id for workspace in desktop.desk.organisation.workspaces]

    assert ids == [DEMO_WORKSPACE_ID, PRACTICE_WORKSPACE_ID, BANKRUPTCY_WORKSPACE_ID]
    assert len(desktop.case_views) == 56


def test_only_the_bankruptcy_case_carries_a_case_map(desktop) -> None:
    """Пустая вкладка обещала бы то, чего в деле нет.

    Карта дела приходит входом, а не выводится конвейером, поэтому у спора о
    поставке и у дел практики её нет — и быть не должно.
    """
    with_map = [view.case_id for view in desktop.case_views if view.bankruptcy_map is not None]

    assert len(with_map) == 1
    case = next(view for view in desktop.case_views if view.bankruptcy_map is not None)
    assert case.workspace_id == BANKRUPTCY_WORKSPACE_ID
    assert len(case.bankruptcy_map.claims) == 6
    # Оговорка обязана сказать, что остальные вкладки — про другое дело.
    assert "поставке" in case.caveat_ru


def test_the_practice_workspace_is_named_after_what_it_actually_holds(desktop) -> None:
    """Название пространства обязано сходиться с составом дел.

    Пространство называлось «Практика Верховного Суда» и после второй выгрузки
    стало обещать не тот источник: из сорока дел стенда актов Верховного Суда
    четыре, остальные тридцать шесть — кассационные. Ошибка держалась потому,
    что название ничем не было связано с данными: строку правил человек, а дела
    менялись сами.
    """
    from causa.institutional.contracts.practice_base import load_practice_base
    from causa.ui.desktop import build_practice_case_inputs

    workspace = next(
        w for w in desktop.desk.organisation.workspaces if w.id == PRACTICE_WORKSPACE_ID
    )
    base = {case.id: case for case in load_practice_base().cases}
    instances = [base[inputs.case_id].instance for inputs in build_practice_case_inputs()]

    supreme = sum(instance == "ВС РФ" for instance in instances)
    if supreme * 2 <= len(instances):
        assert "Верховного Суда" not in workspace.title_ru, workspace.title_ru


def test_practice_cases_carry_the_caveat(desktop) -> None:
    """Без оговорки стенд внушал бы, что система решила дело как суд."""
    practice = [v for v in desktop.case_views if v.workspace_id == PRACTICE_WORKSPACE_ID]

    # Дел в наборе пятьдесят четыре, и окон столько же. Раньше их было сорок:
    # четырнадцать дел о незаключённости, недействительности, прекращении
    # обязательства и убытках конвейер отвергал на сверке входов. Теперь каждое
    # такое дело объявляет следствия позиции суда за пределами своего института,
    # и окно строится для всех. Расхождение этих двух чисел означало бы, что
    # стенд снова молча теряет дела.
    assert len(practice) == 54
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
    # Долгов связности на этом деле не осталось: оба сработавших института
    # проведены в слой выпусками 1.0.0 и 1.1.0.
    assert card.open_debt_ru == []


def test_desktop_endpoint_lists_only_accessible_workspaces(base_url) -> None:
    status, payload = _get(f"{base_url}/api/desktop")

    assert status == 200
    assert payload["operator"]["role_ru"] == "юрист"
    assert {ws["id"] for ws in payload["workspaces"]} == {
        DEMO_WORKSPACE_ID,
        PRACTICE_WORKSPACE_ID,
        BANKRUPTCY_WORKSPACE_ID,
    }


def test_case_endpoint_returns_the_whole_window(base_url) -> None:
    status, payload = _get(f"{base_url}/api/case/{DEMO_WORKSPACE_ID}/case-supply-1")

    assert status == 200
    assert payload["reasoning"]["line"]
    # Два уровня изложения, а не три: машинная трассировка ушла в отдельное
    # поле и в служебный раздел — по вкладке «Изложение» работает юрист.
    assert len(payload["reasoning"]["registers"]) == 2
    assert payload["reasoning"]["trace"]["level"] == "forensic"
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


def test_the_served_interface_is_the_built_one_when_it_exists(base_url) -> None:
    """Стенд отдаёт сборку Next.js, если она есть, и свой запасной вид, если нет.

    Это важно не для красоты: загрузка документа обращается к API по тому же
    адресу, и разводить интерфейс и API по разным серверам значило бы чинить
    CORS вместо того, чтобы проверять разбор.
    """
    root = static_root()

    assert (root / "index.html").is_file()
    assert root in (WEB_ROOT, STATIC_ROOT)
    with urllib.request.urlopen(f"{base_url}/index.html") as response:  # noqa: S310
        assert response.status == 200


def test_path_traversal_is_refused(base_url) -> None:
    with pytest.raises(urllib.error.HTTPError) as failure:
        urllib.request.urlopen(f"{base_url}/../server.py")  # noqa: S310

    assert failure.value.code == 404
