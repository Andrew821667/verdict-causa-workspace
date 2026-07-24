import json
from pathlib import Path

from causa.institutional.contracts.migrations import (
    PackageArtifactEnvelope,
    build_contracts_package_migration_report,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    migrations_path = root / "examples" / "migrations"
    input_versions = [
        ("contracts-ru-v0-0.1.0-benchmark-report.json", "0.1.0"),
        ("contracts-ru-v0-0.3.0-phase0-trace.json", "0.3.0"),
        ("contracts-ru-v0-0.4.0-reviewed-analysis.json", "0.4.0"),
        *(
            (f"contracts-ru-v0-0.{minor}.0-phase0-trace.json", f"0.{minor}.0")
            for minor in range(5, 19)
        ),
    ]
    fixture_pairs = [
        (
            migrations_path / input_name,
            migrations_path / f"contracts-ru-v0-{version}-to-0.19.0-migration-report.json",
        )
        for input_name, version in input_versions
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
