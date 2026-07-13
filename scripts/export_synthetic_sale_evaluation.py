from pathlib import Path

from causa.institutional.contracts.synthetic_sale import (
    build_synthetic_sale_evaluation_artifact,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "examples" / "synthetic_sale_articles_454_491_report.json"
    artifact = build_synthetic_sale_evaluation_artifact()
    output_path.write_text(artifact.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
