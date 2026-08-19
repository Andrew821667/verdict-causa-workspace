"""Выгрузка сверки объявленного правила с исполняемым.

    .venv/bin/python scripts/export_rule_parity_report.py

Пишет `examples/rule_parity_report.json` и печатает отчёт по-русски.
Ничего не запускает из конвейера: сверка читает исходники и доказывает
совпадение решателем.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from causa.reasoning.rule_parity import (  # noqa: E402
    audit_rule_parity,
    render_report_ru,
    report_payload,
)


def main() -> int:
    report = audit_rule_parity()
    target = Path(__file__).resolve().parents[1] / "examples" / "rule_parity_report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report_payload(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(render_report_ru(report))
    print()
    print(f"Отчёт записан: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
