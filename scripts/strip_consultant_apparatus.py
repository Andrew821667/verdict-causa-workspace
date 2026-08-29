"""Снять редакционный аппарат КонсультантПлюс с дословных текстов источников.

## Что нашлось

Источники с `metadata["text_verbatim"] = True` обещают дословный текст нормы.
Проверка 215 таких источников показала, что 145 из них несут вперемешку с
текстом закона редакционный аппарат КонсультантПлюс — 16,6% всех абзацев:

- `Путеводитель по судебной практике (высшие суды и арбитражные суды округов)
  по ст. N ГК РФ` и следующий за ним список вопросов пунктами `- ...`
  (219 заголовков и 788 пунктов). Это отдельный коммерческий продукт
  КонсультантПлюс, вставленный между заголовком статьи и её первым пунктом.
  Юрист, открывший источник, читает «- Признается ли розничной куплей-продажей
  приобретение юрлицами товаров для собственных нужд» на том месте, где должен
  начинаться текст статьи 492.
- `(см. текст в предыдущей редакции)` (467 абзацев) — подпись гиперссылки. В
  отрыве от гиперссылки не значит ничего.

## Что этот скрипт НЕ трогает

Блоки `КонсультантПлюс: примечание.` вместе с их телом (66 штук) остаются.
Обрамление у них тоже редакционное, но содержание — настоящее и важное:
нормы, признанные не соответствующими Конституции РФ, переходные положения,
отсылки к постановлениям КС РФ. Снести их значило бы потерять правовую
информацию ради чистоты формы. Это осознанное решение, а не недосмотр:
запись о нём есть в `docs/legal-source-texts-spec.md`, чтобы «оставлено»
было отличимо от «не заметили».

Ровно тем же различением закрывалась предыдущая порча текстов: у Пленумов
неаккуратная чистка однажды уничтожила 65 настоящих пунктов, поэтому здесь
удаляется только то, у чего доказано нулевое правовое содержание.

## Почему это безопасно

Все три класса абзацев единообразны, и это проверено, а не предположено:
заголовок Путеводителя встречается ровно в одной форме (219 из 219), подпись
гиперссылки — ровно в одной (467 из 467). Главная опасность — пункты `- ...`:
если бы такой абзац встретился вне Путеводителя, он мог бы оказаться текстом
закона. Проверка показала 788 пунктов под заголовком Путеводителя и ноль вне
его; скрипт всё равно снимает пункт только тогда, когда идёт от заголовка, а
не по одному лишь виду абзаца.

Скрипт идемпотентен и проверяет себя: после правки он заново разбирает файл и
падает, если хоть в одном источнике остался аппарат либо если у источника
исчез весь текст.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src/causa/institutional/contracts/synthetic_sources.py"

GUIDE_HEADER = "Путеводитель по "
LINK_LABEL = "(см. текст в предыдущей редакции)"


def strip_apparatus(text: str) -> str:
    """Убрать блоки Путеводителя и подписи гиперссылок, сохранив всё остальное."""
    kept: list[str] = []
    under_guide = False
    for para in text.split("\n\n"):
        if para.startswith(GUIDE_HEADER):
            # Заголовок Путеводителя открывает блок вопросов.
            under_guide = True
            continue
        if under_guide and para.startswith("- "):
            # Пункт снимается только внутри уже открытого блока.
            continue
        under_guide = False
        if para.strip() == LINK_LABEL:
            continue
        kept.append(para)
    return "\n\n".join(kept)


def literal_lines(text: str, indent: str) -> list[str]:
    """Разбить текст на строковые литералы по абзацам, в стиле уже принятом в файле."""
    paragraphs = text.split("\n\n")
    lines = []
    for i, para in enumerate(paragraphs):
        suffix = "\n\n" if i < len(paragraphs) - 1 else ""
        wrapped = textwrap.wrap(para, width=96, break_long_words=False, break_on_hyphens=False) or [
            ""
        ]
        for j, chunk in enumerate(wrapped):
            piece = chunk
            if j < len(wrapped) - 1:
                piece += " "
            elif suffix:
                piece += suffix
            escaped = (
                piece.replace(chr(92), chr(92) * 2)
                .replace(chr(34), chr(92) + chr(34))
                .replace(chr(10), chr(92) + "n")
            )
            lines.append(f'{indent}"{escaped}"')
    return lines


def collect_targets(source_text: str) -> list[tuple[str, ast.AST, str, str]]:
    """Найти дословные источники, чей текст изменится после чистки."""
    tree = ast.parse(source_text)
    targets = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "LegalSource"
        ):
            continue
        kw = {k.arg: k.value for k in node.keywords}
        id_node, text_node, meta_node = kw.get("id"), kw.get("text"), kw.get("metadata")
        if not isinstance(id_node, ast.Constant) or not isinstance(meta_node, ast.Dict):
            continue
        verbatim = any(
            isinstance(k, ast.Constant)
            and k.value == "text_verbatim"
            and isinstance(v, ast.Constant)
            and v.value is True
            for k, v in zip(meta_node.keys, meta_node.values)
        )
        if not verbatim or text_node is None:
            continue
        current = ast.literal_eval(text_node)
        cleaned = strip_apparatus(current)
        if cleaned != current:
            targets.append((id_node.value, text_node, current, cleaned))
    return targets


def main() -> None:
    source_text = SRC_PATH.read_text(encoding="utf-8")
    source_bytes = source_text.encode("utf-8")
    line_byte_lengths = [len(line.encode("utf-8")) for line in source_text.split("\n")]

    def byte_offset(lineno: int, col: int) -> int:
        return sum(n + 1 for n in line_byte_lengths[: lineno - 1]) + col

    targets = collect_targets(source_text)
    if not targets:
        print("Аппарата не найдено — файл уже чист.")
        return

    replacements = []
    removed_chars = 0
    for sid, text_node, current, cleaned in targets:
        if not cleaned.strip():
            raise SystemExit(f"{sid}: после чистки не осталось текста — правка отменена")
        removed_chars += len(current) - len(cleaned)
        joined = "\n".join(literal_lines(cleaned, "            "))
        start = byte_offset(text_node.lineno, text_node.col_offset)
        end = byte_offset(text_node.end_lineno, text_node.end_col_offset)
        replacements.append((start, end, f"(\n{joined}\n        )".encode()))

    for start, end, payload in sorted(replacements, reverse=True):
        source_bytes = source_bytes[:start] + payload + source_bytes[end:]

    SRC_PATH.write_bytes(source_bytes)
    print(f"Очищено источников: {len(targets)}, снято символов: {removed_chars}")

    # Самопроверка: разбираем файл заново и убеждаемся, что аппарата не осталось.
    leftovers = collect_targets(SRC_PATH.read_text(encoding="utf-8"))
    if leftovers:
        raise SystemExit(f"аппарат остался в {len(leftovers)} источниках: {leftovers[0][0]}")
    print("Самопроверка: аппарата в дословных источниках не осталось.")


if __name__ == "__main__":
    main()
