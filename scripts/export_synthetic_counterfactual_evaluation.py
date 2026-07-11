import json
from pathlib import Path

from causa.institutional.contracts.synthetic_counterfactual import (
    build_synthetic_counterfactual_evaluation_artifact,
)


OUTPUT_PATH = Path("examples/synthetic_counterfactual_evaluation_report.json")


def main() -> None:
    artifact = build_synthetic_counterfactual_evaluation_artifact()
    OUTPUT_PATH.write_text(
        json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
