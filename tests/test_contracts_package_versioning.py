from causa.institutional.contracts.versioning import (
    CONTRACTS_PACKAGE_COMPATIBILITY,
    CompatibilityStatus,
    evaluate_contracts_package_compatibility,
)


def test_current_contracts_package_coordinates_are_supported() -> None:
    check = evaluate_contracts_package_compatibility()

    assert check.supported is True
    assert "supported" in check.reasons[0]
    assert "поддерживаются" in check.reasons_ru[0]


def test_unknown_core_version_is_not_supported() -> None:
    check = evaluate_contracts_package_compatibility(core_version="0.2.0")

    assert check.supported is False
    assert "No supported compatibility entry" in check.reasons[0]
    assert "отсутствует" in check.reasons_ru[0]


def test_compatibility_matrix_marks_current_entry_supported() -> None:
    assert len(CONTRACTS_PACKAGE_COMPATIBILITY) == 20
    assert CONTRACTS_PACKAGE_COMPATIBILITY[0].status == CompatibilityStatus.SUPPORTED
    assert CONTRACTS_PACKAGE_COMPATIBILITY[0].package_version == "0.20.0"
    assert CONTRACTS_PACKAGE_COMPATIBILITY[0].case_evidence_schema_versions == [
        "contracts.case-evidence.v9"
    ]
    assert CONTRACTS_PACKAGE_COMPATIBILITY[0].notes_ru


def test_unknown_analysis_pipeline_version_is_not_supported() -> None:
    check = evaluate_contracts_package_compatibility(
        analysis_pipeline_version="contracts-reviewed-analysis-v999"
    )

    assert check.supported is False
