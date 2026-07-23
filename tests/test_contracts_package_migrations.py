from pathlib import Path

import pytest

from causa.institutional.contracts.migrations import (
    CONTRACTS_PACKAGE_MIGRATION_STEPS,
    MigrationDisposition,
    PackageArtifactEnvelope,
    PackageMigrationReport,
    build_contracts_package_migration_report,
)


MIGRATION_FIXTURES = (
    ("0.1.0", "contracts-ru-v0-0.1.0-benchmark-report.json", None),
    ("0.3.0", "contracts-ru-v0-0.3.0-phase0-trace.json", None),
    ("0.4.0", "contracts-ru-v0-0.4.0-reviewed-analysis.json", "русские"),
    ("0.5.0", "contracts-ru-v0-0.5.0-phase0-trace.json", "снимка"),
    ("0.6.0", "contracts-ru-v0-0.6.0-phase0-trace.json", "Translation Layer"),
    ("0.7.0", "contracts-ru-v0-0.7.0-phase0-trace.json", "контрфактической"),
    ("0.8.0", "contracts-ru-v0-0.8.0-phase0-trace.json", "ответственности"),
    ("0.9.0", "contracts-ru-v0-0.9.0-phase0-trace.json", "заключении договора"),
    ("0.10.0", "contracts-ru-v0-0.10.0-phase0-trace.json", "изменении и расторжении"),
    ("0.11.0", "contracts-ru-v0-0.11.0-phase0-trace.json", "недействительности"),
    ("0.12.0", "contracts-ru-v0-0.12.0-phase0-trace.json", "обеспечении исполнения"),
    ("0.13.0", "contracts-ru-v0-0.13.0-phase0-trace.json", "перемене лиц"),
    ("0.14.0", "contracts-ru-v0-0.14.0-phase0-trace.json", "исполнении обязательств"),
    ("0.15.0", "contracts-ru-v0-0.15.0-phase0-trace.json", "поставке"),
    ("0.16.0", "contracts-ru-v0-0.16.0-phase0-trace.json", "купле-продаже"),
    ("0.17.0", "contracts-ru-v0-0.17.0-phase0-trace.json", "gate v1"),
)


def _expected_path(source_version: str) -> list[tuple[str, str]]:
    start = next(
        index
        for index, step in enumerate(CONTRACTS_PACKAGE_MIGRATION_STEPS)
        if step.from_version == source_version
    )
    return [
        (step.from_version, step.to_version) for step in CONTRACTS_PACKAGE_MIGRATION_STEPS[start:]
    ]


@pytest.mark.parametrize(
    ("source_version", "fixture_name", "reason_fragment"),
    MIGRATION_FIXTURES,
)
def test_legacy_artifact_requires_ordered_replay(
    source_version: str,
    fixture_name: str,
    reason_fragment: str | None,
) -> None:
    fixture_path = Path("examples/migrations") / fixture_name
    artifact = PackageArtifactEnvelope.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.REQUIRES_REGENERATION
    assert report.target_package_version == "0.18.0"
    assert [(step.from_version, step.to_version) for step in report.steps] == _expected_path(
        source_version
    )
    assert report.payload_preserved_without_interpretation is True
    assert report.reasons_ru
    assert all(step.reasons_ru for step in report.steps)
    if reason_fragment is not None:
        assert reason_fragment in report.steps[0].reasons_ru[0]


@pytest.mark.parametrize(
    ("source_version", "fixture_name"),
    [(item[0], item[1]) for item in MIGRATION_FIXTURES],
)
def test_exported_migration_report_is_valid(source_version: str, fixture_name: str) -> None:
    report_path = Path(
        f"examples/migrations/contracts-ru-v0-{source_version}-to-0.18.0-migration-report.json"
    )
    report = PackageMigrationReport.model_validate_json(report_path.read_text(encoding="utf-8"))
    artifact = PackageArtifactEnvelope.model_validate_json(
        (Path("examples/migrations") / fixture_name).read_text(encoding="utf-8")
    )
    regenerated_report = build_contracts_package_migration_report(artifact)

    assert report.source_package_version == source_version
    assert report.target_package_version == "0.18.0"
    assert report.disposition_label_ru == "Требуется повторное формирование"
    assert len(report.steps) == len(_expected_path(source_version))
    assert report == regenerated_report


def test_current_contracts_artifact_does_not_require_migration() -> None:
    artifact = PackageArtifactEnvelope(
        id="current-report",
        artifact_type="benchmark_suite_report",
        package_id="contracts-ru-v0",
        package_version="0.18.0",
    )

    report = build_contracts_package_migration_report(artifact)

    assert report.disposition == MigrationDisposition.NOT_REQUIRED
    assert report.steps == []
