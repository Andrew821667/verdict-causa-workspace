"""Сборка статического экспорта Next.js в один самодостаточный файл.

## Зачем

`next build` с `output: "export"` даёт папку: разметку, стили и десяток
скриптов. Открыть её можно только там, где эта папка лежит целиком. Чтобы
показать интерфейс одной ссылкой, всё нужно свести в один файл — без единого
внешнего запроса.

## Что делает сборщик

- заменяет ссылку на таблицу стилей содержимым файла;
- заменяет каждый `<script src=…>` содержимым чанка, сохраняя порядок;
- выбрасывает `<link rel="preload">` (предзагружать больше нечего) и скрипты
  с атрибутом `noModule` — это запасной путь для браузеров без модулей, а
  вложенный в файл он только дублировал бы работу.

## Границы

Сборщик ничего не переписывает внутри чанков. Если сборка начнёт подгружать
код на лету, один файл перестанет быть самодостаточным, и это обязано быть
заметно: `assert_self_contained` ищет оставшиеся ссылки на `/_next/` и
роняет сборку, а не выпускает файл, который где-то не откроется.
"""

import re
from pathlib import Path

WEB_BUNDLE_VERSION = "ui-web-bundle-v0"

_PRELOAD = re.compile(r'<link[^>]*rel="preload"[^>]*>')
_STYLESHEET = re.compile(r'<link[^>]*rel="stylesheet"[^>]*href="(?P<href>[^"]+)"[^>]*>')
_SCRIPT = re.compile(r'<script(?P<attrs>[^>]*?)src="(?P<src>[^"]+)"[^>]*>\s*</script>')


class ExportNotFoundError(FileNotFoundError):
    """Экспорт не собран. Ошибка отдельная, чтобы не путать с отсутствием файла."""


def _asset(out_dir: Path, url: str) -> Path:
    return out_dir / url.lstrip("/")


def inline_export(out_dir: Path, *, fragment: bool = False) -> str:
    """Собрать `out/index.html` вместе со всеми его ресурсами в одну строку.

    Обёртка снимается **до** вложения кода, а не после: в собранном файле
    строки вроде `<body` встречаются внутри чанков, и разбор по ним поехал бы.
    """
    index = out_dir / "index.html"
    if not index.is_file():
        raise ExportNotFoundError(
            f"Не найден {index}. Сначала соберите интерфейс: npm run build в каталоге web."
        )
    html = index.read_text(encoding="utf-8")
    html = _PRELOAD.sub("", html)
    if fragment:
        html = to_fragment(html)

    def replace_style(match: re.Match[str]) -> str:
        css = _asset(out_dir, match.group("href")).read_text(encoding="utf-8")
        return f"<style>{css}</style>"

    def replace_script(match: re.Match[str]) -> str:
        if "noModule" in match.group("attrs"):
            return ""
        code = _asset(out_dir, match.group("src")).read_text(encoding="utf-8")
        # Закрывающий тег внутри кода завершил бы блок скрипта раньше времени.
        code = code.replace("</script", "<\\/script")
        # U+FFFD в коде — это символ замены из полифилла разбора URI, а не
        # испорченная кодировка. Внутри строкового литерала JavaScript
        # экранированная запись ему равнозначна, а сырой символ принимают не
        # все приёмники: они видят в нём признак неверной перекодировки.
        code = code.replace("�", "\\uFFFD")
        return "<script>" + code + "</script>"

    html = _STYLESHEET.sub(replace_style, html)
    html = _SCRIPT.sub(replace_script, html)
    return html


def assert_self_contained(html: str) -> None:
    """Убедиться, что страница не тянет ничего снаружи.

    Проверяются атрибуты `src` и `href` — то, что браузер загрузит сам. Имена
    чанков внутри кода не считаются ссылками: сборщик Next регистрирует ими
    уже загруженные модули, и запроса за ними не происходит. Различать это
    важно: иначе проверка либо ругается всегда, либо не ругается никогда.
    """
    leftovers = sorted(set(re.findall(r'(?:src|href)="(/_next/[^"]+)"', html)))
    if leftovers:
        raise ValueError(
            "В собранном файле остались внешние ресурсы: "
            + ", ".join(leftovers[:5])
            + ". Такой файл откроется не везде."
        )


def to_fragment(html: str) -> str:
    """Убрать обёртку `html`/`head`/`body`, сохранив всё их содержимое.

    Нужно там, где страницу оборачивает чужой шаблон: вложенный документ
    внутри документа браузеры разбирают непредсказуемо. Содержимое `head`
    переносится целиком — стили и ссылки на скрипты живут именно там, и
    выборочный перенос молча потерял бы половину страницы.
    """
    head = html.split("<head>", 1)[1].split("</head>", 1)[0]
    body = html.split("<body", 1)[1].split(">", 1)[1].rsplit("</body>", 1)[0]
    return f"{head}\n{body}"


def build_single_file(out_dir: Path, target: Path, *, fragment: bool = False) -> Path:
    html = inline_export(out_dir, fragment=fragment)
    assert_self_contained(html)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    return target


if __name__ == "__main__":
    import sys

    arguments = sys.argv[1:]
    as_fragment = "--fragment" in arguments
    arguments = [argument for argument in arguments if argument != "--fragment"]
    source = Path(arguments[0] if arguments else "web/out")
    destination = Path(arguments[1] if len(arguments) > 1 else "examples/ui_web_snapshot.html")
    written = build_single_file(source, destination, fragment=as_fragment)
    print(f"Интерфейс одним файлом: {written} ({written.stat().st_size // 1024} КиБ)")
