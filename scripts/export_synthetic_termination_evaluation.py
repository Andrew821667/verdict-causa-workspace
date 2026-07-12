import json
from pathlib import Path

from causa.institutional.contracts.synthetic_termination import (
    build_synthetic_termination_evaluation_artifact,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "examples" / "synthetic_termination_evaluation_report.json"
    artifact = build_synthetic_termination_evaluation_artifact()
    output_path.write_text(
        json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output_path)


if __name__ == "__main__":
    main()
