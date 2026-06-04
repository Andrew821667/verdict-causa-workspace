from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.institutional.package import InstitutionalPackageManifest


def test_contracts_package_manifest_has_required_sections() -> None:
    assert CONTRACTS_PACKAGE_MANIFEST.is_phase0_complete is True
    assert CONTRACTS_PACKAGE_MANIFEST.missing_required_sections() == []


def test_package_manifest_reports_missing_sections() -> None:
    manifest = InstitutionalPackageManifest(
        id="empty",
        legal_institute="Example institute",
        version="0.1.0",
        core_compatibility=">=0.1,<0.2",
    )

    assert "vocabulary_refs" in manifest.missing_required_sections()
    assert manifest.is_phase0_complete is False
