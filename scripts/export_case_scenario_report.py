import json
from pathlib import Path

from causa.institutional.contracts.case_scenarios import run_case_scenario_suite


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "examples" / "case_scenario_report.json"
    report = run_case_scenario_suite()
    output_path.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output_path)


if __name__ == "__main__":
    main()
