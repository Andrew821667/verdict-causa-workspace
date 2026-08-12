"""Статический снимок стенда: один самодостаточный HTML-файл.

## Зачем

Стенд живёт на `127.0.0.1` и доступен только тому, у кого он запущен. Снимок
нужен, чтобы показать интерфейс тому, кто сервер не поднимал: один файл, всё
внутри, никаких обращений в сеть.

## Что в снимке настоящее, а что нет

Настоящее — **все данные**: рабочий стол, разборы всех дел и исходы замечаний
вычислены тем же кодом, что и на живом стенде, и вложены в файл как есть.
Переключение дел, вкладок и ролей работает.

Не настоящее — **вычисление на лету**. Снимок не может пересчитать дело: новых
фактов в нём взяться неоткуда. Поэтому исходы замечаний в него вкладываются
заранее — по одному на каждое сочетание вида замечания и режима отправки, —
а не пересчитываются в браузере. Логика не переписана на JavaScript: значения
приходят из `apply_remark`, и разойтись с сервером они не могут.

Снимок помечен на экране как снимок, чтобы его нельзя было принять за живой
стенд.
"""

import json
from pathlib import Path

from causa.ui.desktop import DesktopState, build_demo_desktop
from causa.ui.remarks import OperatorRemark, RemarkKind, apply_remark
from causa.ui.server import STATIC_ROOT, DesktopService

SNAPSHOT_VERSION = "ui-snapshot-v0"

#: Текст, который подставляется вместо написанного оператором при подготовке
#: исходов: сам текст в снимке подставляется уже в браузере.
_PLACEHOLDER = "%%REMARK_TEXT%%"


def build_remark_outcomes() -> dict[str, dict]:
    """Исходы замечаний для всех сочетаний вида и режима отправки."""
    outcomes: dict[str, dict] = {}
    for kind in RemarkKind:
        for as_signal in (False, True):
            remark = OperatorRemark(
                id="remark-snapshot",
                case_id="case-snapshot",
                operator_id="op-demo",
                kind=kind,
                text_ru=_PLACEHOLDER,
                as_learning_signal=as_signal,
            )
            outcomes[f"{kind.value}:{int(as_signal)}"] = apply_remark(remark).model_dump(
                mode="json"
            )
    return outcomes


def build_snapshot_payload(state: DesktopState | None = None) -> dict:
    """Все данные стенда одним объектом."""
    service = DesktopService(state if state is not None else build_demo_desktop())
    desktop = service.desktop_payload()
    cases = {
        f"{view.workspace_id}/{view.case_id}": service.case_payload(view.workspace_id, view.case_id)
        for view in service.state.case_views
    }
    return {
        "version": SNAPSHOT_VERSION,
        "desktop": desktop,
        "cases": cases,
        "remark_outcomes": build_remark_outcomes(),
        "placeholder": _PLACEHOLDER,
    }


def render_snapshot_html(state: DesktopState | None = None) -> str:
    """Собрать самодостаточный HTML: разметка, стили, скрипт и данные."""
    markup = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    styles = (STATIC_ROOT / "styles.css").read_text(encoding="utf-8")
    script = (STATIC_ROOT / "app.js").read_text(encoding="utf-8")
    payload = json.dumps(build_snapshot_payload(state), ensure_ascii=False)
    # Закрывающий тег внутри строки JSON завершил бы блок скрипта раньше времени.
    payload = payload.replace("</", "<\\/")

    markup = markup.replace(
        '<link rel="stylesheet" href="/styles.css">', f"<style>\n{styles}\n</style>"
    )
    markup = markup.replace(
        '<script src="/app.js"></script>',
        f"<script>\nwindow.CAUSA_SNAPSHOT = {payload};\n</script>\n<script>\n{script}\n</script>",
    )
    return markup


def render_snapshot_fragment(state: DesktopState | None = None) -> str:
    """То же самое без обёртки `html`/`head`/`body`.

    Нужно там, где страницу оборачивает чужой шаблон и собственные `<html>` и
    `<body>` привели бы к вложенным документам.
    """
    page = render_snapshot_html(state)
    head = page.split("<head>", 1)[1].split("</head>", 1)[0]
    body = page.split("<body>", 1)[1].split("</body>", 1)[0]
    title = head.split("<title>", 1)[1].split("</title>", 1)[0]
    styles = "<style>" + head.split("<style>", 1)[1].split("</style>", 1)[0] + "</style>"
    return f"<title>{title}</title>\n{styles}\n{body}"


def write_snapshot(path: Path, state: DesktopState | None = None) -> Path:
    path.write_text(render_snapshot_html(state), encoding="utf-8")
    return path


def write_dataset(path: Path, state: DesktopState | None = None) -> Path:
    """Только данные, без разметки: их читает интерфейс на Next.js.

    Набор собирается тем же кодом, что и живой стенд, поэтому фронтенд не
    повторяет ни одного правила: он показывает то, что вычислил Python.
    """
    payload = json.dumps(build_snapshot_payload(state), ensure_ascii=False, indent=1)
    path.write_text(payload + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    import sys

    arguments = sys.argv[1:]
    if arguments and arguments[0] == "--json":
        target = Path(arguments[1] if len(arguments) > 1 else "web/data/desktop.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        written = write_dataset(target)
        print(f"Данные стенда: {written} ({written.stat().st_size // 1024} КиБ)")
    else:
        target = Path(arguments[0] if arguments else "examples/ui_snapshot.html")
        target.parent.mkdir(parents=True, exist_ok=True)
        written = write_snapshot(target)
        print(f"Снимок стенда: {written} ({written.stat().st_size // 1024} КиБ)")
