"""HTTP-сервер стенда: JSON поверх собранного рабочего стола.

## Почему стандартная библиотека

Никаких новых зависимостей: интерфейс не должен тянуть за собой веб-фреймворк,
иначе установка стенда становится отдельной задачей. `http.server` для стенда,
на котором один юрист смотрит пять дел, достаточен.

## Что сервер отдаёт

| Маршрут | Что возвращает |
|---|---|
| `GET /api/desktop` | организация, роли, пространства и карточки дел |
| `GET /api/case/<пространство>/<дело>` | полное содержимое основного окна |
| `POST /api/case/<пространство>/<дело>/remark` | судьба замечания оператора |
| `GET /` и статические файлы | сам интерфейс |

## Границы

Замечания живут в памяти процесса. Стенд предназначен для самостоятельного
тестирования, а не для ведения дел: перезапуск их теряет, и это записано здесь,
а не выяснится потом.

Доступ к делу проверяется столом (`Desk.case`), а не маршрутом: изоляция
пространств не должна зависеть от того, какой URL кто-то подобрал.
"""

import base64
import binascii
import json
import mimetypes
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from causa.ui.desktop import DesktopState, build_demo_desktop, build_demo_sessions
from causa.ui.documents import (
    MAX_DOCUMENT_BYTES,
    ClosureKind,
    DocumentTooLargeError,
    GapClosure,
    build_document,
)
from causa.ui.session import (
    CaseSession,
    GapClosureBrokeInvariant,
    GapClosureConflict,
    GapClosureNotConverged,
    compare_views,
)
from causa.ui.remarks import OperatorRemark, RemarkKind, apply_remark

SERVER_VERSION = "ui-server-v0"

STATIC_ROOT = Path(__file__).parent / "static"

#: Собранный интерфейс на Next.js. Если он есть, стенд отдаёт его: тогда
#: загрузка документов работает с тем же адресом, что и API, и браузеру не
#: приходится ходить между двумя серверами.
WEB_ROOT = Path(__file__).resolve().parents[3] / "web" / "out"


def static_root() -> Path:
    return WEB_ROOT if (WEB_ROOT / "index.html").is_file() else STATIC_ROOT


MAX_REMARK_BODY_BYTES = 64 * 1024

#: Маршрут POST → метод сервиса и предел размера тела.
#:
#: Файл приходит в base64, поэтому его предел заметно больше замечания и
#: больше самого файла: кодирование добавляет треть.
_POST_ACTIONS: dict[str, tuple[str, int]] = {
    "remark": ("add_remark", MAX_REMARK_BODY_BYTES),
    "document": ("add_document", 2 * MAX_DOCUMENT_BYTES),
    "close-gap": ("close_gap", MAX_REMARK_BODY_BYTES),
}


class DesktopService:
    """Состояние стенда: сессии дел и всё, что оператор к ним добавил.

    Сессии нужны потому, что дело обязано пересчитываться: приложенный документ
    меняет факты, а факты меняют вывод. Стол пересобирается из уже посчитанных
    окон — заново считается только изменившееся дело.
    """

    def __init__(
        self,
        state: DesktopState | None = None,
        sessions: list[CaseSession] | None = None,
    ) -> None:
        if sessions is None and state is None:
            sessions = build_demo_sessions()
        self._sessions = {session.inputs.key: session for session in (sessions or [])}
        if state is not None:
            self.state = state
        else:
            self.state = build_demo_desktop(
                [session.build_view() for session in self._sessions.values()]
            )
        self._remarks: dict[str, list[OperatorRemark]] = {}

    def session(self, workspace_id: str, case_id: str) -> CaseSession:
        # Доступ проверяется столом до того, как дело будет найдено.
        self.state.desk.case(workspace_id, case_id)
        key = f"{workspace_id}/{case_id}"
        session = self._sessions.get(key)
        if session is None:
            raise KeyError(f"Дело {case_id} открыто только на чтение: пересчёт для него не собран.")
        return session

    def _replace_view(self, view) -> None:
        views = [
            view
            if existing.workspace_id == view.workspace_id and existing.case_id == view.case_id
            else existing
            for existing in self.state.case_views
        ]
        self.state = build_demo_desktop(views)

    def desktop_payload(self) -> dict:
        desk = self.state.desk
        return {
            "version": self.state.version,
            "organisation": {
                "id": desk.organisation.id,
                "title_ru": desk.organisation.title_ru,
                "operators": [
                    {
                        "id": operator.id,
                        "display_name": operator.display_name,
                        "role": operator.role.value,
                        "role_ru": operator.role_ru,
                        "rights_ru": operator.rights_ru,
                    }
                    for operator in desk.organisation.operators
                ],
            },
            "operator": {
                "id": desk.operator.id,
                "display_name": desk.operator.display_name,
                "role_ru": desk.operator.role_ru,
                "rights_ru": desk.operator.rights_ru,
            },
            "workspaces": [
                {
                    "id": workspace.id,
                    "title_ru": workspace.title_ru,
                    "sla_mode_ru": workspace.sla_mode_ru,
                    "risk_tier_ru": workspace.risk_tier_ru,
                    "cases": [case.model_dump() for case in workspace.cases],
                }
                for workspace in desk.organisation.workspaces
                if workspace.id in desk.workspace_ids
            ],
        }

    def case_payload(self, workspace_id: str, case_id: str) -> dict:
        view = self.state.view(workspace_id, case_id)
        payload = view.model_dump(mode="json")
        payload["remarks"] = {
            "version": view.remarks.version,
            "case_id": view.remarks.case_id,
            "outcomes": [outcome.model_dump(mode="json") for outcome in view.remarks.outcomes]
            + [
                apply_remark(remark).model_dump(mode="json")
                for remark in self._remarks.get(case_id, [])
            ],
        }
        return payload

    def add_remark(self, workspace_id: str, case_id: str, body: dict) -> dict:
        # Доступ проверяется столом до того, как замечание где-либо сохранится.
        self.state.desk.case(workspace_id, case_id)
        remark = OperatorRemark(
            id=body.get("id") or f"remark-{len(self._remarks.get(case_id, [])) + 1}",
            case_id=case_id,
            operator_id=self.state.desk.operator.id,
            kind=RemarkKind(body["kind"]),
            text_ru=body["text_ru"],
            target=body.get("target", ""),
            as_learning_signal=bool(body.get("as_learning_signal", False)),
            source_refs=list(body.get("source_refs", [])),
        )
        self._remarks.setdefault(case_id, []).append(remark)
        return apply_remark(remark).model_dump(mode="json")

    def add_document(self, workspace_id: str, case_id: str, body: dict) -> dict:
        """Принять файл. Содержимое не разбирается — только считается отпечаток."""
        session = self.session(workspace_id, case_id)
        try:
            content = base64.b64decode(body["content_base64"], validate=True)
        except (KeyError, binascii.Error) as error:
            raise ValueError(f"Содержимое файла передано неверно: {error}.") from error
        document = session.add_document(
            build_document(
                case_id=case_id,
                filename=body["filename"],
                content=content,
                uploaded_by=self.state.desk.operator.id,
                media_type=body.get("media_type", "application/octet-stream"),
                uploaded_on=date.today(),
            )
        )
        return {
            "document": document.model_dump(mode="json"),
            "note_ru": (
                "Файл приобщён к делу. Система его не читает: чтобы он повлиял на "
                "вывод, укажите, какой пробел он закрывает."
            ),
        }

    def close_gap(self, workspace_id: str, case_id: str, body: dict) -> dict:
        """Закрыть пробел документом и пересчитать дело целиком."""
        session = self.session(workspace_id, case_id)
        before = self.state.view(workspace_id, case_id)
        closure = GapClosure(
            gap_id=body["gap_id"],
            document_id=body["document_id"],
            kind=ClosureKind(body.get("kind", ClosureKind.ASSERTED_FACT.value)),
            fact_updates=dict(body.get("fact_updates", {})),
            agreed_due_date=_optional_date(body.get("agreed_due_date")),
            actual_performance_date=_optional_date(body.get("actual_performance_date")),
            statement_ru=body.get("statement_ru", ""),
        )
        after, reconciliation = session.close_gap(
            closure,
            reconcile_dependents=bool(body.get("reconcile_dependents", False)),
        )
        self._replace_view(after)
        return {
            "closure": closure.model_dump(mode="json"),
            "change": compare_views(before, after).model_dump(mode="json"),
            "reconciliation": {
                **reconciliation.model_dump(mode="json"),
                "summary_ru": reconciliation.summary_ru,
                "lines_ru": [item.line_ru for item in reconciliation.alignments],
            },
            "case": self.case_payload(workspace_id, case_id),
        }


def _optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def build_handler(service: DesktopService) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = f"causa-ui/{SERVER_VERSION}"

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            # Тишина по умолчанию: стенд запускают, чтобы смотреть на дела.
            return

        def _send_json(self, payload: dict, status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_error_ru(self, status: int, message_ru: str) -> None:
            self._send_json({"error_ru": message_ru}, status=status)

        def _serve_static(self, path: str) -> None:
            root = static_root()
            relative = "index.html" if path in ("", "/") else path.lstrip("/")
            target = (root / relative).resolve()
            if not str(target).startswith(str(root.resolve())) or not target.is_file():
                self._send_error_ru(404, f"Файл не найден: {relative}")
                return
            content_type, _ = mimetypes.guess_type(target.name)
            body = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type or 'text/plain'}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - имя задано базовым классом
            path = urlparse(self.path).path
            if path == "/api/desktop":
                self._send_json(service.desktop_payload())
                return
            if path.startswith("/api/case/"):
                parts = [unquote(part) for part in path[len("/api/case/") :].split("/") if part]
                if len(parts) != 2:
                    self._send_error_ru(404, "Ожидается /api/case/<пространство>/<дело>.")
                    return
                self._handle_case(parts[0], parts[1])
                return
            self._serve_static(path)

        def _handle_case(self, workspace_id: str, case_id: str) -> None:
            try:
                self._send_json(service.case_payload(workspace_id, case_id))
            except PermissionError as error:
                self._send_error_ru(403, str(error))
            except (KeyError, StopIteration):
                self._send_error_ru(
                    404, f"Дело {case_id} в пространстве {workspace_id} не найдено."
                )

        def do_POST(self) -> None:  # noqa: N802 - имя задано базовым классом
            path = urlparse(self.path).path
            action = next((name for name in _POST_ACTIONS if path.endswith("/" + name)), None)
            if not path.startswith("/api/case/") or action is None:
                self._send_error_ru(404, "Маршрут не поддерживается.")
                return
            parts = [
                unquote(part)
                for part in path[len("/api/case/") : -len("/" + action)].split("/")
                if part
            ]
            if len(parts) != 2:
                self._send_error_ru(404, f"Ожидается /api/case/<пространство>/<дело>/{action}.")
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length > _POST_ACTIONS[action][1]:
                self._send_error_ru(413, "Тело запроса слишком велико для стенда.")
                return
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._send_error_ru(400, "Тело запроса не является JSON.")
                return
            handler = getattr(service, _POST_ACTIONS[action][0])
            try:
                self._send_json(handler(parts[0], parts[1], body), status=201)
            except PermissionError as error:
                self._send_error_ru(403, str(error))
            except DocumentTooLargeError as error:
                self._send_error_ru(413, str(error))
            except (
                GapClosureConflict,
                GapClosureNotConverged,
                GapClosureBrokeInvariant,
            ) as conflict:
                # Не ошибка запроса, а отказ слоя сверки: он несёт разбор.
                self._send_json(conflict.payload(), status=409)
            except KeyError as error:
                self._send_error_ru(400, f"В запросе не хватает поля или объекта: {error}.")
            except ValueError as error:
                self._send_error_ru(400, str(error))

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Запустить стенд. Сборка стола выполняется один раз до старта."""
    service = DesktopService()
    server = ThreadingHTTPServer((host, port), build_handler(service))
    print(f"Стенд Verdict Causa: http://{host}:{port}")
    print(f"Дел на стенде: {len(service.state.case_views)}. Остановка — Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
