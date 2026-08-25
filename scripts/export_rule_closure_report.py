"""Выгрузить отчёт о закрытии вопросов сверки правил."""

import json
from pathlib import Path

from causa.reasoning.rule_closure import audit_rule_closure, closure_payload


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "examples" / "rule_closure_report.json"
    payload = closure_payload(audit_rule_closure())
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Отчёт о закрытии: {output_path}")


if __name__ == "__main__":
    main()
