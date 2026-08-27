"""Пересадка синтетических источников на постановления Пленума на дословный текст.

Разбирает 14 записей `LegalSource` в `synthetic_sources.py`, чей
`metadata["legal_reference"]` называет постановление Пленума, и заменяет
`text` на дословный текст соответствующих пунктов из
`data/guidance/plenum_paragraphs.jsonl` — чистой попунктной выгрузки,
независимо проверенной (нумерация 1..N без разрывов и повторов по каждому
из десяти документов, без остатков разметки) перед этим прогоном.

Соответствие «источник → документ (+ диапазон пунктов)» задано явной
таблицей, а не разобрано из текста ссылки: сама ссылка (например,
«Постановление Пленума ВС РФ от 22.11.2016 № 54») не называет документ
однозначно — тот же номер и близкий текст встречаются у постановления от
21.12.2017 № 54, различить их можно только по дате, которую свободный
текст ссылки передаёт непоследовательно. Диапазон пунктов задан только
там, где выгрузка сама разделена на два документа по одной ссылке
(постановление № 25/2015 разбито на пункты доставки сообщения 63-68 и
раздел о недействительности сделок 69-102); для остальных источников
пункт не назван — в текст идёт весь выгруженный документ целиком, тем же
принципом, каким при пересадке ГК источник без указания конкретного
пункта получал текст всей статьи.

Правка идёт тем же байтовым AST-механизмом, что и
`migrate_gk_sources_to_verbatim_text.py` (см. комментарий там о
`col_offset` в байтах UTF-8, а не в символах).

Запуск: python scripts/migrate_plenum_sources_to_verbatim_text.py
"""

import ast
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src" / "causa" / "institutional" / "contracts" / "synthetic_sources.py"

# source_id -> (document_slug, (первый_пункт, последний_пункт) | None)
SOURCE_TARGETS: dict[str, tuple[str, tuple[int, int] | None]] = {
    "synthetic-ru-plenum49-formation-guidance-v1": ("plenum-vs-49-2018", None),
    "synthetic-ru-plenum25-63-67-message-delivery-risk-v1": ("plenum-vs-25-2015", (63, 68)),
    "synthetic-ru-plenum25-invalidity-guidance-v1": ("plenum-vs-25-2015", (69, 102)),
    "synthetic-ru-plenum54-unilateral-guidance-v1": ("plenum-vs-54-2016", None),
    "synthetic-ru-plenum18-pretrial-guidance-v1": ("plenum-vs-18-2021", None),
    "synthetic-ru-plenum54-security-guidance-v1": ("plenum-vs-54-2016", None),
    "synthetic-ru-plenum23-pledge-guidance-v1": ("plenum-vs-23-2023", None),
    "synthetic-ru-plenum45-suretyship-guidance-v1": ("plenum-vs-45-2020", None),
    "synthetic-ru-plenum54-party-change-guidance-v1": ("plenum-vs-54-2017", None),
    "synthetic-ru-plenum6-discharge-guidance-v1": ("plenum-vs-6-2020", None),
    "synthetic-ru-plenum54-performance-guidance-v1": ("plenum-vs-54-2016", None),
    "synthetic-ru-plenum7-remedies-guidance-v1": ("plenum-vs-7-2016", None),
    "synthetic-ru-plenum18-supply-guidance-v1": ("plenum-vas-18-1997", None),
    "synthetic-ru-plenum7-liability-guidance-v1": ("plenum-vs-7-2016", None),
}


def literal_lines(text: str, indent: str) -> list[str]:
    """Разбить текст на строковые литералы по абзацам, в стиле уже принятом в файле."""
    paragraphs = text.split("\n\n")
    lines = []
    for i, para in enumerate(paragraphs):
        suffix = "\n\n" if i < len(paragraphs) - 1 else ""
        wrapped = textwrap.wrap(para, width=96, break_long_words=False, break_on_hyphens=False) or [""]
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


def build_combined_text(
    title_ru: str,
    paragraphs_by_number: dict[int, str],
    span: tuple[int, int] | None,
) -> str:
    numbers = sorted(paragraphs_by_number)
    if span is not None:
        low, high = span
        numbers = [n for n in numbers if low <= n <= high]
    body = "\n\n".join(paragraphs_by_number[n] for n in numbers)
    return f"{title_ru}\n\n{body}"


def main() -> None:
    index = {
        row["slug"]: row
        for row in (
            json.loads(line)
            for line in (ROOT / "data/guidance/index.jsonl").open(encoding="utf-8")
        )
    }
    paragraphs: dict[str, dict[int, str]] = {}
    for line in (ROOT / "data/guidance/plenum_paragraphs.jsonl").open(encoding="utf-8"):
        row = json.loads(line)
        paragraphs.setdefault(row["document_slug"], {})[int(row["paragraph"])] = row["text_ru"]

    source_text = SRC_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source_text)

    source_bytes = source_text.encode("utf-8")
    line_byte_lengths = [len(line.encode("utf-8")) for line in source_text.split("\n")]

    def byte_offset(lineno: int, col: int) -> int:
        return sum(n + 1 for n in line_byte_lengths[: lineno - 1]) + col

    targets = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "LegalSource"):
            continue
        kw = {k.arg: k.value for k in node.keywords}
        id_node = kw.get("id")
        meta_node = kw.get("metadata")
        if not isinstance(id_node, ast.Constant) or not isinstance(meta_node, ast.Dict):
            continue
        sid = id_node.value
        if sid not in SOURCE_TARGETS:
            continue
        already_done = any(
            isinstance(k, ast.Constant) and k.value == "text_verbatim" for k in meta_node.keys
        )
        ref_node = None
        for k, v in zip(meta_node.keys, meta_node.values):
            if isinstance(k, ast.Constant) and k.value == "legal_reference":
                ref_node = v
        if ref_node is None or already_done:
            continue
        targets[sid] = (kw.get("text"), ref_node)

    print("целей для пересадки найдено:", len(targets))
    missing = set(SOURCE_TARGETS) - set(targets)
    if missing:
        print("!! не найдены в файле или уже пересажены:", sorted(missing))

    all_repl: list[tuple[int, int, bytes]] = []
    for sid, (text_node, ref_node) in targets.items():
        doc_slug, span = SOURCE_TARGETS[sid]
        combined = build_combined_text(index[doc_slug]["title_ru"], paragraphs[doc_slug], span)
        joined = "\n".join(literal_lines(combined, "            "))
        new_text_src = joined[len("            ") :]

        start = byte_offset(text_node.lineno, text_node.col_offset)
        end = byte_offset(text_node.end_lineno, text_node.end_col_offset)
        all_repl.append((start, end, new_text_src.encode("utf-8")))

        insert_pos = byte_offset(ref_node.end_lineno, ref_node.end_col_offset)
        all_repl.append((insert_pos, insert_pos, b',\n            "text_verbatim": True'))

    all_repl.sort(key=lambda r: r[0], reverse=True)
    new_bytes = source_bytes
    for start, end, new_piece in all_repl:
        new_bytes = new_bytes[:start] + new_piece + new_bytes[end:]

    SRC_PATH.write_bytes(new_bytes)
    print("применено замен:", len(all_repl))


if __name__ == "__main__":
    main()
