import json
from pathlib import Path

from causa.phase0.demo_trace import build_supply_dispute_demo_trace


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "examples" / "phase0_supply_dispute_trace.json"
    trace = build_supply_dispute_demo_trace()
    output_path.write_text(
        json.dumps(trace.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output_path)


if __name__ == "__main__":
    main()
