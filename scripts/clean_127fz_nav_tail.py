"""Чистка навигационного мусора в конце текста статей 127-ФЗ.

`data/laws/127fz_articles.jsonl` считался проверенным (565/565, 0 пустых),
но проверка на слив не покрывала один вид загрязнения: постраничный виджет
«предыдущая статья / следующая статья» КонсультантПлюс, сведённый в плоский
текст и приклеенный в конец `text_ru` через `\n\n`, без какого-либо отделяющего
маркера кроме двойного пробела между двумя заголовками
(«Статья N. Название  Статья M. Название» или «§ N. Название  Статья M. ...»).
Найдено в 518 из 565 статей.

В отличие от тултипов Пленума (см. `docs/legal-source-texts-spec.md`), этот
мусор не встроен в середину текста и не имеет произвольной вложенности — он
всегда является последним абзацем (разделён `\n\n` от остального текста) и
всегда состоит из одного-двух заголовков вида «Статья N.», «§ N.» или
«Глава N.». Проверено: для всех 518 случаев после отсечения последнего абзаца
внутри оставшегося текста не остаётся ни одного двойного пробела — признак,
что резка прошла по границе, а не разорвала реальный текст. Поэтому чистка
здесь безопасна детерминированным скриптом, без повторного запроса выгрузки.

Запуск: python scripts/clean_127fz_nav_tail.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "laws" / "127fz_articles.jsonl"

NUM = r"\d+(?:\.\d+)*(?:-\d+)*"
UNIT_HEAD = rf"(?:Статья\s+{NUM}\.|§\s*{NUM}\.|Глава\s+[IVXLCM\d]+(?:\.\d+)*\.)"
UNIT_RE = re.compile(rf"^{UNIT_HEAD}\s+.+$")
SPLIT_RE = re.compile(rf"\s{{2,}}(?={UNIT_HEAD})")


def strip_nav_tail(text: str) -> tuple[str, bool]:
    if not text.strip():
        return text, False
    paras = text.split("\n\n")
    last = paras[-1].strip()
    if not re.match(rf"^{UNIT_HEAD}\s+", last):
        return text, False
    segs = SPLIT_RE.split(last)
    if not (1 <= len(segs) <= 2 and all(UNIT_RE.match(s.strip()) for s in segs)):
        return text, False
    return "\n\n".join(paras[:-1]), True


def main() -> None:
    rows = [json.loads(line) for line in PATH.open(encoding="utf-8")]
    cleaned = 0
    for r in rows:
        new_text, changed = strip_nav_tail(r["text_ru"])
        if changed:
            r["text_ru"] = new_text
            cleaned += 1

    with PATH.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("статей всего:", len(rows))
    print("очищено от навигационного хвоста:", cleaned)
    empty = sum(1 for r in rows if not r["text_ru"].strip())
    print("пустых после чистки:", empty)


if __name__ == "__main__":
    main()
