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
    assert report.target_package_version == "0.16.0"
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.1.0", "0.2.0"),
        ("0.2.0", "0.3.0"),
        ("0.3.0", "0.4.0"),
        ("0.4.0", "0.5.0"),
        ("0.5.0", "0.6.0"),
        ("0.6.0", "0.7.0"),
        ("0.7.0", "0.8.0"),
        ("0.8.0", "0.9.0"),
        ("0.9.0", "0.10.0"),
        ("0.10.0", "0.11.0"),
        ("0.11.0", "0.12.0"),
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert report.payload_preserved_without_interpretation is True
    assert report.reasons_ru
    assert all(step.reasons_ru for step in report.steps)


def test_current_contracts_artifact_does_not_require_migration() -> None:
    artifact = PackageArtifactEnvelope(
        id="current-report",
        artifact_type="benchmark_suite_report",
        package_id="contracts-ru-v0",
        package_version="0.16.0",
    )

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.NOT_REQUIRED
    assert report.steps == []


def test_exported_legacy_migration_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.1.0-to-0.16.0-migration-report.json")
    report = PackageMigrationReport.model_validate(
        json.loads(fixture_path.read_text(encoding="utf-8"))
    )

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert len(report.steps) == 15


def test_0_3_trace_fixture_requires_reviewed_input_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.3.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.3.0", "0.4.0"),
        ("0.4.0", "0.5.0"),
        ("0.5.0", "0.6.0"),
        ("0.6.0", "0.7.0"),
        ("0.7.0", "0.8.0"),
        ("0.8.0", "0.9.0"),
        ("0.9.0", "0.10.0"),
        ("0.10.0", "0.11.0"),
        ("0.11.0", "0.12.0"),
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]


def test_exported_0_3_migration_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.3.0-to-0.16.0-migration-report.json")
    report = PackageMigrationReport.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    assert report.source_package_version == "0.3.0"
    assert report.target_package_version == "0.16.0"
    assert len(report.steps) == 13


def test_0_4_analysis_requires_russian_audit_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.4.0-reviewed-analysis.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.4.0", "0.5.0"),
        ("0.5.0", "0.6.0"),
        ("0.6.0", "0.7.0"),
        ("0.7.0", "0.8.0"),
        ("0.8.0", "0.9.0"),
        ("0.9.0", "0.10.0"),
        ("0.10.0", "0.11.0"),
        ("0.11.0", "0.12.0"),
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "русские" in report.steps[0].reasons_ru[0]


def test_exported_0_4_migration_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.4.0-to-0.16.0-migration-report.json")
    report = PackageMigrationReport.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    assert report.source_package_version == "0.4.0"
    assert report.target_package_version == "0.16.0"
    assert report.disposition_label_ru == "Требуется повторное формирование"


def test_0_5_trace_requires_policy_snapshot_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.5.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.5.0", "0.6.0"),
        ("0.6.0", "0.7.0"),
        ("0.7.0", "0.8.0"),
        ("0.8.0", "0.9.0"),
        ("0.9.0", "0.10.0"),
        ("0.10.0", "0.11.0"),
        ("0.11.0", "0.12.0"),
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "снимка" in report.steps[0].reasons_ru[0]


def test_exported_0_5_migration_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.5.0-to-0.16.0-migration-report.json")
    report = PackageMigrationReport.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    assert report.source_package_version == "0.5.0"
    assert report.target_package_version == "0.16.0"
    assert len(report.steps) == 11


def test_0_6_trace_requires_translation_bundle_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.6.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.6.0", "0.7.0"),
        ("0.7.0", "0.8.0"),
        ("0.8.0", "0.9.0"),
        ("0.9.0", "0.10.0"),
        ("0.10.0", "0.11.0"),
        ("0.11.0", "0.12.0"),
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "Translation Layer" in report.steps[0].reasons_ru[0]


def test_exported_0_6_migration_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.6.0-to-0.16.0-migration-report.json")
    report = PackageMigrationReport.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    assert report.source_package_version == "0.6.0"
    assert report.target_package_version == "0.16.0"
    assert len(report.steps) == 10


def test_0_7_trace_requires_counterfactual_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.7.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.7.0", "0.8.0"),
        ("0.8.0", "0.9.0"),
        ("0.9.0", "0.10.0"),
        ("0.10.0", "0.11.0"),
        ("0.11.0", "0.12.0"),
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "контрфактической" in report.steps[0].reasons_ru[0]


def test_exported_0_7_migration_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.7.0-to-0.16.0-migration-report.json")
    report = PackageMigrationReport.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    assert report.source_package_version == "0.7.0"
    assert report.target_package_version == "0.16.0"
    assert len(report.steps) == 9


def test_0_8_trace_requires_liability_evidence_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.8.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.8.0", "0.9.0"),
        ("0.9.0", "0.10.0"),
        ("0.10.0", "0.11.0"),
        ("0.11.0", "0.12.0"),
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "ответственности" in report.steps[0].reasons_ru[0]


def test_exported_0_8_migration_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.8.0-to-0.16.0-migration-report.json")
    report = PackageMigrationReport.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    assert report.source_package_version == "0.8.0"
    assert report.target_package_version == "0.16.0"
    assert len(report.steps) == 8


def test_0_9_trace_requires_formation_evidence_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.9.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.9.0", "0.10.0"),
        ("0.10.0", "0.11.0"),
        ("0.11.0", "0.12.0"),
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "заключении договора" in report.steps[0].reasons_ru[0]


def test_0_10_trace_requires_change_and_termination_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.10.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.10.0", "0.11.0"),
        ("0.11.0", "0.12.0"),
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "изменении и расторжении" in report.steps[0].reasons_ru[0]


def test_0_11_trace_requires_transaction_invalidity_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.11.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.11.0", "0.12.0"),
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "недействительности" in report.steps[0].reasons_ru[0]


def test_0_12_trace_requires_performance_security_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.12.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.12.0", "0.13.0"),
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "обеспечении исполнения" in report.steps[0].reasons_ru[0]


def test_0_13_trace_requires_obligation_dynamics_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.13.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.13.0", "0.14.0"),
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "перемене лиц" in report.steps[0].reasons_ru[0]


def test_0_14_trace_requires_performance_remedies_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.14.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [
        ("0.14.0", "0.15.0"),
        ("0.15.0", "0.16.0"),
    ]
    assert "исполнении обязательств" in report.steps[0].reasons_ru[0]


def test_0_15_artifact_requires_special_supply_replay() -> None:
    fixture_path = Path("examples/migrations/contracts-ru-v0-0.15.0-phase0-trace.json")
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert [(step.from_version, step.to_version) for step in report.steps] == [("0.15.0", "0.16.0")]
    assert "поставке" in report.steps[0].reasons_ru[0]


def test_exported_0_15_migration_report_fixture_is_valid() -> None:
    fixture_path = Path(
        "examples/migrations/contracts-ru-v0-0.15.0-to-0.16.0-migration-report.json"
    )
    report = PackageMigrationReport.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    assert report.source_package_version == "0.15.0"
    assert report.target_package_version == "0.16.0"
    assert len(report.steps) == 1
