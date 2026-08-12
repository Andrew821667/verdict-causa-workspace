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

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from causa.ui.desktop import DesktopState, build_demo_desktop
from causa.ui.remarks import OperatorRemark, RemarkKind, apply_remark

SERVER_VERSION = "ui-server-v0"

STATIC_ROOT = Path(__file__).parent / "static"

MAX_REMARK_BODY_BYTES = 64 * 1024


class DesktopService:
    """Состояние стенда: собранный стол и замечания, добавленные в этой сессии."""

    def __init__(self, state: DesktopState | None = None) -> None:
        self.state = state if state is not None else build_demo_desktop()
        self._remarks: dict[str, list[OperatorRemark]] = {}

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
            relative = "index.html" if path in ("", "/") else path.lstrip("/")
            target = (STATIC_ROOT / relative).resolve()
            if not str(target).startswith(str(STATIC_ROOT.resolve())) or not target.is_file():
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
            if not path.startswith("/api/case/") or not path.endswith("/remark"):
                self._send_error_ru(404, "Маршрут не поддерживается.")
                return
            parts = [
                unquote(part)
                for part in path[len("/api/case/") : -len("/remark")].split("/")
                if part
            ]
            if len(parts) != 2:
                self._send_error_ru(404, "Ожидается /api/case/<пространство>/<дело>/remark.")
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_REMARK_BODY_BYTES:
                self._send_error_ru(413, "Замечание слишком большое для стенда.")
                return
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._send_error_ru(400, "Тело запроса не является JSON.")
                return
            try:
                self._send_json(service.add_remark(parts[0], parts[1], body), status=201)
            except PermissionError as error:
                self._send_error_ru(403, str(error))
            except KeyError as error:
                self._send_error_ru(400, f"В замечании не хватает поля: {error}.")
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
