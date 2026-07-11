from enum import Enum

from pydantic import BaseModel, Field

from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST


class MigrationDisposition(str, Enum):
    NOT_REQUIRED = "not_required"
    REQUIRES_REGENERATION = "requires_regeneration"
    UNSUPPORTED = "unsupported"


class PackageArtifactEnvelope(BaseModel):
    id: str
    artifact_type: str
    package_id: str
    package_version: str
    payload: dict[str, object] = Field(default_factory=dict)


class PackageMigrationStep(BaseModel):
    from_version: str
    to_version: str
    reasons: list[str] = Field(default_factory=list)
    replay_commands: list[str] = Field(default_factory=list)


class PackageMigrationReport(BaseModel):
    id: str
    artifact_id: str
    artifact_type: str
    source_package_version: str
    target_package_version: str
    disposition: MigrationDisposition
    steps: list[PackageMigrationStep] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    payload_preserved_without_interpretation: bool


CONTRACTS_PACKAGE_MIGRATION_STEPS = [
    PackageMigrationStep(
        from_version="0.1.0",
        to_version="0.2.0",
        reasons=[
            "Authority policy gained constitutional and regulatory levels.",
            "Authority outcomes must be replayed against the expanded candidate model.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_supply_benchmarks.py",
            "python scripts/export_synthetic_supply_red_team.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.2.0",
        to_version="0.3.0",
        reasons=[
            "Constraint results gained remedy, causation, and limitation fields.",
            "Formal outcomes must be regenerated instead of inferred from prior output.",
        ],
        replay_commands=[
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_synthetic_supply_benchmarks.py",
            "python scripts/export_synthetic_supply_red_team.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.3.0",
        to_version="0.4.0",
        reasons=[
            "Analysis inputs gained reviewed case, temporal, and authority contracts.",
            "Decision traces now retain fact provenance and the complete reviewed analysis result.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_reviewed_contract_analysis.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
        ],
    ),
]


def build_contracts_package_migration_report(
    artifact: PackageArtifactEnvelope,
) -> PackageMigrationReport:
    target_version = CONTRACTS_PACKAGE_MANIFEST.version
    if artifact.package_id != CONTRACTS_PACKAGE_MANIFEST.id:
        return PackageMigrationReport(
            id=f"migration:{artifact.id}:unsupported",
            artifact_id=artifact.id,
            artifact_type=artifact.artifact_type,
            source_package_version=artifact.package_version,
            target_package_version=target_version,
            disposition=MigrationDisposition.UNSUPPORTED,
            reasons=["Artifact package id does not match contracts-ru-v0."],
            payload_preserved_without_interpretation=True,
        )

    if artifact.package_version == target_version:
        return PackageMigrationReport(
            id=f"migration:{artifact.id}:current",
            artifact_id=artifact.id,
            artifact_type=artifact.artifact_type,
            source_package_version=artifact.package_version,
            target_package_version=target_version,
            disposition=MigrationDisposition.NOT_REQUIRED,
            reasons=["Artifact already uses the current package version."],
            payload_preserved_without_interpretation=True,
        )

    steps: list[PackageMigrationStep] = []
    current_version = artifact.package_version
    while current_version != target_version:
        step = next(
            (
                candidate
                for candidate in CONTRACTS_PACKAGE_MIGRATION_STEPS
                if candidate.from_version == current_version
            ),
            None,
        )
        if step is None:
            return PackageMigrationReport(
                id=f"migration:{artifact.id}:unsupported",
                artifact_id=artifact.id,
                artifact_type=artifact.artifact_type,
                source_package_version=artifact.package_version,
                target_package_version=target_version,
                disposition=MigrationDisposition.UNSUPPORTED,
                steps=steps,
                reasons=["No ordered migration path reaches the current package version."],
                payload_preserved_without_interpretation=True,
            )
        steps.append(step)
        current_version = step.to_version

    return PackageMigrationReport(
        id=f"migration:{artifact.id}:to-{target_version}",
        artifact_id=artifact.id,
        artifact_type=artifact.artifact_type,
        source_package_version=artifact.package_version,
        target_package_version=target_version,
        disposition=MigrationDisposition.REQUIRES_REGENERATION,
        steps=steps,
        reasons=[
            "Legacy artifact is retained as input evidence only.",
            "Replay is required because package analysis or artifact semantics changed.",
        ],
        payload_preserved_without_interpretation=True,
    )
