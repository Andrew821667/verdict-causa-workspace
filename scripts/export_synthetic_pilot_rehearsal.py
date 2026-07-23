import json
from pathlib import Path

from causa.institutional.contracts.synthetic_pilot import (
    build_synthetic_pilot_rehearsal_artifact,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "examples" / "synthetic_pilot_rehearsal_report.json"
    artifact = build_synthetic_pilot_rehearsal_artifact()
    path.write_text(
        json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(path)


if __name__ == "__main__":
    main()
