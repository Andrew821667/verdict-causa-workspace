from pathlib import Path

from causa.institutional.contracts.synthetic_security import (
    build_synthetic_security_evaluation_artifact,
)


OUTPUT_PATH = Path("examples/synthetic_security_evaluation_report.json")


def main() -> None:
    artifact = build_synthetic_security_evaluation_artifact()
    OUTPUT_PATH.write_text(
        artifact.model_dump_json(indent=2),
        encoding="utf-8",
    )
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
