"""Пересадка синтетических источников ГК на дословный текст статей.

Разбирает каждый `LegalSource` в `synthetic_sources.py`, чей
`metadata["legal_reference"]` начинается с «ГК РФ», разбирает номера статей
из ссылки (диапазоны, списки, составные ссылки через «;») и заменяет
поле `text` на дословный текст этих статей из `data/code/gk_article_texts.jsonl`,
собранный с заголовками «Статья N. Название.» для каждой статьи. Источники без
такой ссылки (абстрактные демонстрационные нормы Этапа 0, ссылки на
постановления Пленума и обзоры практики) не трогает — это отдельный охват.

Правка идёт по точным байтовым координатам узлов AST (`col_offset` в CPython
измеряется в байтах UTF-8 внутри строки, а не в символах — расхождение с этим
фактом уже один раз испортило файл при разработке скрипта, поэтому здесь оно
явно прокомментировано). Заменяется только литерал `text=(...)`; всё
остальное содержимое каждого `LegalSource` остаётся как было. В `metadata`
добавляется маркер `"text_verbatim": True", отличающий пересаженные источники
от source-заглушек.

Скрипт идемпотентен по содержимому текста (одна и та же ссылка всегда даёт
один и тот же собранный текст), но не идемпотентен по маркеру: повторный
запуск на уже пересаженном файле пропускает источники, где `text_verbatim`
уже стоит, — маркер служит одновременно признаком «уже сделано».

Запуск: python scripts/migrate_gk_sources_to_verbatim_text.py
"""

import ast
import json
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src" / "causa" / "institutional" / "contracts" / "synthetic_sources.py"

ARTICLE_SPAN = re.compile(r"стать[ьия]+\s+((?:\d+(?:\.\d+)*)(?:\s*(?:[–\-,]|и)\s*\d+(?:\.\d+)*)*)")


def article_sort_key(num: str) -> tuple:
    parts = re.split(r"[.\-]", num)
    key = []
    for p in parts:
        try:
            key.append((0, int(p)))
        except ValueError:
            key.append((1, p))
    return tuple(key)


def expand_range(a: str, b: str, all_numbers: list[str]) -> list[str]:
    ka, kb = article_sort_key(a), article_sort_key(b)
    return [n for n in all_numbers if ka <= article_sort_key(n) <= kb]


def parse_reference(ref: str, all_numbers: list[str]) -> list[str]:
    """«ГК РФ, статьи 429, пункты 4–6; статья 445, пункт 4» → ['429', '445'] и т.п."""
    ref = ref.replace("ГК РФ,", "").strip()
    result: list[str] = []
    for m in ARTICLE_SPAN.finditer(ref):
        span = m.group(1)
        range_m = re.fullmatch(r"(\d+(?:\.\d+)*)\s*[–\-]\s*(\d+(?:\.\d+)*)", span)
        if range_m:
            result.extend(expand_range(range_m.group(1), range_m.group(2), all_numbers))
            continue
        for item in re.split(r"\s*(?:,|и)\s*", span):
            sub = re.fullmatch(r"(\d+(?:\.\d+)*)\s*[–\-]\s*(\d+(?:\.\d+)*)", item)
            if sub:
                result.extend(expand_range(sub.group(1), sub.group(2), all_numbers))
            else:
                result.append(item)
    seen: set[str] = set()
    out: list[str] = []
    for n in result:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def build_combined_text(numbers: list[str], titles: dict[str, str], texts: dict[str, str]) -> str:
    parts = []
    for n in numbers:
        title = titles.get(n, "")
        body = texts.get(n, "").strip() or "Утратила силу."
        header = f"Статья {n}. {title}." if title else f"Статья {n}."
        parts.append(f"{header}\n\n{body}")
    return "\n\n".join(parts)


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


def main() -> None:
    structure = [
        json.loads(line) for line in (ROOT / "data/code/gk_articles.jsonl").open(encoding="utf-8")
    ]
    titles = {r["number"]: r["title_ru"] for r in structure}
    all_numbers = sorted({r["number"] for r in structure}, key=article_sort_key)
    texts = {
        r["number"]: r["text_ru"]
        for r in (
            json.loads(line)
            for line in (ROOT / "data/code/gk_article_texts.jsonl").open(encoding="utf-8")
        )
    }

    source_text = SRC_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source_text)

    # ast.col_offset/end_col_offset заданы в БАЙТАХ UTF-8 внутри строки, а не в
    # символах. С кириллическим текстом это расходится: работаем целиком в
    # байтах, чтобы срезы совпадали с координатами ast.
    source_bytes = source_text.encode("utf-8")
    line_byte_lengths = [len(line.encode("utf-8")) for line in source_text.split("\n")]

    def byte_offset(lineno: int, col: int) -> int:
        return sum(n + 1 for n in line_byte_lengths[: lineno - 1]) + col

    targets = {}
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "LegalSource"
        ):
            continue
        kw = {k.arg: k.value for k in node.keywords}
        id_node = kw.get("id")
        meta_node = kw.get("metadata")
        if not isinstance(id_node, ast.Constant) or not isinstance(meta_node, ast.Dict):
            continue
        ref_value = ref_node = None
        already_done = False
        for k, v in zip(meta_node.keys, meta_node.values):
            if not isinstance(k, ast.Constant):
                continue
            if k.value == "legal_reference" and isinstance(v, ast.Constant):
                ref_value, ref_node = v.value, v
            if k.value == "text_verbatim":
                already_done = True
        if ref_value is None or not ref_value.startswith("ГК РФ") or already_done:
            continue
        targets[id_node.value] = (kw.get("text"), ref_value, ref_node)

    print("целей для пересадки найдено:", len(targets))

    all_repl: list[tuple[int, int, bytes]] = []
    failed = []
    for sid, (text_node, ref, ref_node) in targets.items():
        numbers = parse_reference(ref, all_numbers)
        if not numbers:
            failed.append((sid, ref))
            continue
        combined = build_combined_text(numbers, titles, texts)
        joined = "\n".join(literal_lines(combined, "            "))
        new_text_src = joined[
            len("            ") :
        ]  # первая строка: отступ уже в исходнике до start

        start = byte_offset(text_node.lineno, text_node.col_offset)
        end = byte_offset(text_node.end_lineno, text_node.end_col_offset)
        all_repl.append((start, end, new_text_src.encode("utf-8")))

        insert_pos = byte_offset(ref_node.end_lineno, ref_node.end_col_offset)
        all_repl.append((insert_pos, insert_pos, b',\n            "text_verbatim": True'))

    if failed:
        print("!! не разобрались ссылки:", failed)

    all_repl.sort(key=lambda r: r[0], reverse=True)
    new_bytes = source_bytes
    for start, end, new_piece in all_repl:
        new_bytes = new_bytes[:start] + new_piece + new_bytes[end:]

    SRC_PATH.write_bytes(new_bytes)
    print("применено замен:", len(all_repl))


if __name__ == "__main__":
    main()
