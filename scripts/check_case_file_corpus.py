"""Проверка выгрузки материалов дел до отправки.

Скрипт для выгружающей стороны: он говорит, примет ли приёмная сторона файл, и
называет каждую претензию по-русски. Запускать до отправки ветки — тогда разбор
не превращается в переписку.

    .venv/bin/python scripts/check_case_file_corpus.py
"""

import sys
from pathlib import Path

from pydantic import ValidationError

from causa.ui.case_file_corpus import (
    CASE_FILE_CORPUS_PATH,
    CaseFile,
    CaseFileCorpus,
    describe_corpus_ru,
)

#: Сколько комплектов просит задание.
EXPECTED_CASE_FILES = 30


def main() -> int:
    path = Path(CASE_FILE_CORPUS_PATH)
    if not path.exists():
        print(f"Файла {path} нет. Выгрузка кладётся именно туда, по одному комплекту на строку.")
        return 1

    problems: list[str] = []
    case_files = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case_files.append(CaseFile.model_validate_json(line))
        except ValidationError as error:
            for issue in error.errors():
                problems.append(f"строка {number}: {issue.get('msg', issue)}")

    if not problems:
        try:
            corpus = CaseFileCorpus(case_files=tuple(case_files))
        except ValidationError as error:
            for issue in error.errors():
                problems.append(str(issue.get("msg", issue)))
        else:
            for line in describe_corpus_ru(corpus):
                print(line)
            if len(corpus.case_files) < EXPECTED_CASE_FILES:
                print(
                    f"Комплектов {len(corpus.case_files)}, задание просит {EXPECTED_CASE_FILES}. "
                    "Неполная выгрузка принимается, если в сопроводительном письме "
                    "сказано, чего найти не удалось и почему."
                )

    if problems:
        print(f"\nВыгрузка не принята. Претензий: {len(problems)}.")
        for problem in problems:
            print(f"  — {problem}")
        return 1
    print("\nВыгрузка принята: структура в порядке.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
