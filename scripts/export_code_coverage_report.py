"""Выгрузить отчёт обхода кодекса."""

import json
from pathlib import Path

from causa.institutional.contracts.code_coverage import (
    code_coverage_payload,
    load_code_structure,
    measure_code_coverage,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "examples" / "code_coverage_report.json"
    payload = code_coverage_payload(measure_code_coverage(load_code_structure()))
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Отчёт обхода кодекса: {output_path}")


if __name__ == "__main__":
    main()
