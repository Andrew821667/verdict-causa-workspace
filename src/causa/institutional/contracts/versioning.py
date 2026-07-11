from enum import Enum

from pydantic import BaseModel, Field

from causa import __version__ as CORE_VERSION
from causa.core.bootstrap import (
    DEFAULT_BOOTSTRAP_SCHEMA_VERSION,
    DEFAULT_TRANSLATOR_VERSION,
)
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST


class CompatibilityStatus(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


class PackageCompatibilityEntry(BaseModel):
    package_version: str
    core_version: str
    bootstrap_schema_versions: list[str] = Field(default_factory=list)
    translator_versions: list[str] = Field(default_factory=list)
    status: CompatibilityStatus
    notes: list[str] = Field(default_factory=list)


class PackageCompatibilityCheck(BaseModel):
    package_id: str
    package_version: str
    core_version: str
    bootstrap_schema_version: str
    translator_version: str
    supported: bool
    reasons: list[str] = Field(default_factory=list)


CONTRACTS_PACKAGE_COMPATIBILITY = [
    PackageCompatibilityEntry(
        package_version="0.2.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Synthetic Phase 0 authority policy adds constitutional and regulatory levels.",
            "No production or real-client-data compatibility claim is implied.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.1.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Phase 0 synthetic contractual package only.",
            "No production or real-client-data compatibility claim is implied.",
        ],
    )
]


def evaluate_contracts_package_compatibility(
    core_version: str = CORE_VERSION,
    bootstrap_schema_version: str = DEFAULT_BOOTSTRAP_SCHEMA_VERSION,
    translator_version: str = DEFAULT_TRANSLATOR_VERSION,
) -> PackageCompatibilityCheck:
    matching_entries = [
        entry
        for entry in CONTRACTS_PACKAGE_COMPATIBILITY
        if entry.package_version == CONTRACTS_PACKAGE_MANIFEST.version
        and entry.core_version == core_version
        and bootstrap_schema_version in entry.bootstrap_schema_versions
        and translator_version in entry.translator_versions
        and entry.status == CompatibilityStatus.SUPPORTED
    ]
    supported = bool(matching_entries)
    reasons = (
        ["Package, core, bootstrap schema, and translator coordinates are supported."]
        if supported
        else ["No supported compatibility entry matches the supplied coordinates."]
    )

    return PackageCompatibilityCheck(
        package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        package_version=CONTRACTS_PACKAGE_MANIFEST.version,
        core_version=core_version,
        bootstrap_schema_version=bootstrap_schema_version,
        translator_version=translator_version,
        supported=supported,
        reasons=reasons,
    )
