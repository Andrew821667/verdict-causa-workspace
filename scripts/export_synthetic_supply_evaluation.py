from pathlib import Path

from causa.institutional.contracts.synthetic_supply import (
    build_synthetic_supply_evaluation_artifact,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "examples" / "synthetic_supply_articles_506_524_report.json"
    artifact = build_synthetic_supply_evaluation_artifact()
    output_path.write_text(artifact.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
