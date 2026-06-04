import json
from pathlib import Path

from causa.phase0.pipeline import build_phase0_readiness_report


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "examples" / "phase0_readiness_report.json"
    report = build_phase0_readiness_report()
    output_path.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output_path)


if __name__ == "__main__":
    main()
