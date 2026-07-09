import json
from pathlib import Path

from causa.institutional.contracts.red_team_runner import run_synthetic_supply_red_team_suite


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "examples" / "synthetic_supply_red_team_report.json"
    report = run_synthetic_supply_red_team_suite()
    output_path.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output_path)


if __name__ == "__main__":
    main()
