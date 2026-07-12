from pathlib import Path

from causa.institutional.contracts.synthetic_performance_remedies import (
    build_synthetic_performance_remedies_evaluation_artifact,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "examples" / "synthetic_performance_remedies_evaluation_report.json"
    artifact = build_synthetic_performance_remedies_evaluation_artifact()
    output_path.write_text(artifact.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
