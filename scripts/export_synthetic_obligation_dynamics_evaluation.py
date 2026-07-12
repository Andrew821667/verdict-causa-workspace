from pathlib import Path

from causa.institutional.contracts.synthetic_obligation_dynamics import (
    build_synthetic_obligation_dynamics_evaluation_artifact,
)


OUTPUT_PATH = Path("examples/synthetic_obligation_dynamics_evaluation_report.json")


def main() -> None:
    artifact = build_synthetic_obligation_dynamics_evaluation_artifact()
    OUTPUT_PATH.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
