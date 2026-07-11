import json
from pathlib import Path

from causa.institutional.contracts.migrations import (
    PackageArtifactEnvelope,
    build_contracts_package_migration_report,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "examples" / "migrations" / "contracts-ru-v0-0.1.0-benchmark-report.json"
    output_path = (
        root / "examples" / "migrations" / "contracts-ru-v0-0.1.0-to-0.3.0-migration-report.json"
    )
    artifact = PackageArtifactEnvelope.model_validate_json(input_path.read_text(encoding="utf-8"))
    report = build_contracts_package_migration_report(artifact)
    output_path.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output_path)


if __name__ == "__main__":
    main()
