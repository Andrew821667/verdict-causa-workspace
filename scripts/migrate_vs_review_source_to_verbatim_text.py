"""Пересадить источник о недостатках товара на дословный текст обзора ВС РФ.

`synthetic-ru-vs-review2024-sale-quality-v1` был последним источником пакета,
несущим наш пересказ вместо текста первоисточника: 215 остальных дословных
источников пересажены на настоящий текст ещё раньше (190 статей ГК, 11 статей
127-ФЗ, 14 постановлений Пленума).

## Что было не так, кроме пересказа

Одна фраза источника склеивала две разные вещи, и только вторая требовала
выгрузки:

1. «гарантийный срок влияет на распределение бремени доказывания» — не
   позиция суда, а пункт 2 статьи 476 ГК РФ, уже лежащий дословно в
   `synthetic-ru-gk465-477-sale-conformity-v1`;
2. «безрезультатный гарантийный ремонт не прекращает предусмотренные законом
   требования покупателя» — действительно позиция ВС РФ.

Ссылка «Обзор № 2, 3 (2024), определение № 301-ЭС23-10631» называла сразу три
документа. Выгрузка сняла неоднозначность фактом: в КонсультантПлюс это один
объединённый документ «Обзор судебной практики ВС РФ N 2, 3 (2024)»
(`LAW:491650`, утверждён 27.11.2024), позиция изложена в пункте 17 раздела
«Споры, возникающие из обязательственных отношений», и определение
№ 301-ЭС23-10631 названо в тексте пункта прямо.

Поэтому `legal_reference` тоже переписывается: прежняя ссылка утверждала
разделение на обзоры № 2 и № 3, которого сам документ не подтверждает.
"""

from __future__ import annotations

import ast
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src/causa/institutional/contracts/synthetic_sources.py"
PARAGRAPHS_PATH = ROOT / "data/guidance/vs_review_paragraphs.jsonl"

SOURCE_ID = "synthetic-ru-vs-review2024-sale-quality-v1"
DOCUMENT_SLUG = "vs-review-2-3-2024"
PARAGRAPH = "17"

NEW_TITLE = (
    "Обзор судебной практики ВС РФ N 2, 3 (2024), пункт 17: недостатки после гарантийного ремонта"
)
NEW_REFERENCE = (
    "Обзор судебной практики Верховного Суда Российской Федерации N 2, 3 (2024), "
    "утверждён Президиумом ВС РФ 27.11.2024, пункт 17 (определение N 301-ЭС23-10631)"
)


def literal_lines(text: str, indent: str) -> list[str]:
    """Разбить текст на строковые литералы по абзацам, в стиле принятом в файле."""
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


def main() -> None:
    rows = [json.loads(line) for line in PARAGRAPHS_PATH.open(encoding="utf-8")]
    matches = [
        r for r in rows if r["document_slug"] == DOCUMENT_SLUG and r["paragraph"] == PARAGRAPH
    ]
    if len(matches) != 1:
        raise SystemExit(f"ожидался ровно один пункт {PARAGRAPH}, найдено {len(matches)}")
    paragraph = matches[0]
    verbatim = paragraph["text_ru"]

    # Пересадка имеет смысл только если текст действительно несёт нужную позицию.
    if "не должен лишаться прав" not in verbatim:
        raise SystemExit("в тексте пункта нет позиции о правах покупателя — пересадка отменена")
    if "301-ЭС23-10631" not in verbatim:
        raise SystemExit("в тексте пункта не назван определение № 301-ЭС23-10631")

    source_text = SRC_PATH.read_text(encoding="utf-8")
    source_bytes = source_text.encode("utf-8")
    line_byte_lengths = [len(line.encode("utf-8")) for line in source_text.split("\n")]

    def byte_offset(lineno: int, col: int) -> int:
        return sum(n + 1 for n in line_byte_lengths[: lineno - 1]) + col

    tree = ast.parse(source_text)
    target = None
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "LegalSource"
        ):
            continue
        kw = {k.arg: k.value for k in node.keywords}
        id_node = kw.get("id")
        if not (isinstance(id_node, ast.Constant) and id_node.value == SOURCE_ID):
            continue
        target = kw
        break
    if target is None:
        raise SystemExit(f"источник {SOURCE_ID} не найден")

    meta_node = target["metadata"]
    if any(isinstance(k, ast.Constant) and k.value == "text_verbatim" for k in meta_node.keys):
        print("источник уже пересажен")
        return

    ref_node = next(
        v
        for k, v in zip(meta_node.keys, meta_node.values)
        if isinstance(k, ast.Constant) and k.value == "legal_reference"
    )
    # Новые пометки встают перед ключом basis_url: у ключа-константы границы
    # чистые, а конец значения legal_reference лежит ВНУТРИ его скобок —
    # вставка туда однажды уже сломала файл.
    basis_key = next(
        k for k in meta_node.keys if isinstance(k, ast.Constant) and k.value == "basis_url"
    )

    replacements = []

    # Значения text и legal_reference уже обёрнуты скобками в исходном файле,
    # и границы узла AST лежат внутри них: свои скобки добавлять нельзя.
    joined = "\n".join(literal_lines(verbatim, "            "))
    text_node = target["text"]
    replacements.append(
        (
            byte_offset(text_node.lineno, text_node.col_offset),
            byte_offset(text_node.end_lineno, text_node.end_col_offset),
            joined.lstrip().encode(),
        )
    )

    title_node = target["title"]
    replacements.append(
        (
            byte_offset(title_node.lineno, title_node.col_offset),
            byte_offset(title_node.end_lineno, title_node.end_col_offset),
            json.dumps(NEW_TITLE, ensure_ascii=False).encode(),
        )
    )

    ref_joined = "\n".join(literal_lines(NEW_REFERENCE, "                "))
    replacements.append(
        (
            byte_offset(ref_node.lineno, ref_node.col_offset),
            byte_offset(ref_node.end_lineno, ref_node.end_col_offset),
            ref_joined.lstrip().encode(),
        )
    )

    insert_pos = byte_offset(basis_key.lineno, basis_key.col_offset)
    extra = (
        '"text_verbatim": True,'
        f'\n            "document_slug": "{DOCUMENT_SLUG}",'
        f'\n            "paragraph": "{PARAGRAPH}",'
        f'\n            "source_ref": "{paragraph["source_ref"]}",'
        "\n            "
    )
    replacements.append((insert_pos, insert_pos, extra.encode()))

    for start, end, payload in sorted(replacements, key=lambda item: item[0], reverse=True):
        source_bytes = source_bytes[:start] + payload + source_bytes[end:]

    SRC_PATH.write_bytes(source_bytes)
    print(f"пересажен {SOURCE_ID}: {len(verbatim)} символов дословного текста пункта {PARAGRAPH}")


if __name__ == "__main__":
    main()
