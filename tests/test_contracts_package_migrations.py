import json
from pathlib import Path

from causa.institutional.contracts.migrations import (
    MigrationDisposition,
    PackageArtifactEnvelope,
    PackageMigrationReport,
    build_contracts_package_migration_report,
)


def test_legacy_contracts_artifact_requires_replay_through_ordered_steps() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.1.0-benchmark-report.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert report.target_package_version == "0.4.0"
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.1.0", "0.2.0"),
        ("0.2.0", "0.3.0"),
        ("0.3.0", "0.4.0"),
    ]
    assert report.payload_preserved_without_interpretation is True


def test_current_contracts_artifact_does_not_require_migration() -> None:
    artifact = PackageArtifactEnvelope(
        id="current-report",
        artifact_type="benchmark_suite_report",
        package_id="contracts-ru-v0",
        package_version="0.4.0",
    )

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.NOT_REQUIRED
    assert report.steps == []


def test_exported_legacy_migration_report_fixture_is_valid() -> None:
    fixture_path = Path(
        "examples/migrations/contracts-ru-v0-0.1.0-to-0.4.0-migration-report.json"
    )
    report = PackageMigrationReport.model_validate(
        json.loads(fixture_path.read_text(encoding="utf-8"))
    )

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert len(report.steps) == 3


def test_0_3_trace_fixture_requires_reviewed_input_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.3.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(
        fixture_path.read_text(encoding="utf-8")
    )

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.3.0", "0.4.0")
    ]


def test_exported_0_3_migration_report_fixture_is_valid() -> None:
    fixture_path = Path(
        "examples/migrations/contracts-ru-v0-0.3.0-to-0.4.0-migration-report.json"
    )
    report = PackageMigrationReport.model_validate_json(
        fixture_path.read_text(encoding="utf-8")
    )

    assert report.source_package_version == "0.3.0"
    assert report.target_package_version == "0.4.0"
    assert len(report.steps) == 1
