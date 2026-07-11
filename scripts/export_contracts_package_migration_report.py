import json
from pathlib import Path

from causa.institutional.contracts.migrations import (
    PackageArtifactEnvelope,
    build_contracts_package_migration_report,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    migrations_path = root / "examples" / "migrations"
    fixture_pairs = [
        (
            migrations_path / "contracts-ru-v0-0.1.0-benchmark-report.json",
            migrations_path / "contracts-ru-v0-0.1.0-to-0.8.0-migration-report.json",
        ),
        (
            migrations_path / "contracts-ru-v0-0.3.0-phase0-trace.json",
            migrations_path / "contracts-ru-v0-0.3.0-to-0.8.0-migration-report.json",
        ),
        (
            migrations_path / "contracts-ru-v0-0.4.0-reviewed-analysis.json",
            migrations_path / "contracts-ru-v0-0.4.0-to-0.8.0-migration-report.json",
        ),
        (
            migrations_path / "contracts-ru-v0-0.5.0-phase0-trace.json",
            migrations_path / "contracts-ru-v0-0.5.0-to-0.8.0-migration-report.json",
        ),
        (
            migrations_path / "contracts-ru-v0-0.6.0-phase0-trace.json",
            migrations_path / "contracts-ru-v0-0.6.0-to-0.8.0-migration-report.json",
        ),
        (
            migrations_path / "contracts-ru-v0-0.7.0-phase0-trace.json",
            migrations_path / "contracts-ru-v0-0.7.0-to-0.8.0-migration-report.json",
        ),
    ]
    for input_path, output_path in fixture_pairs:
        artifact = PackageArtifactEnvelope.model_validate_json(
            input_path.read_text(encoding="utf-8")
        )
        report = build_contracts_package_migration_report(artifact)
        output_path.write_text(
            json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(output_path)


if __name__ == "__main__":
    main()
