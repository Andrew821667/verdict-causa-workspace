from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.institutional.contracts.pilot_evaluation import (
    PILOT_GATE_BENCHMARKS,
    PILOT_GATE_RED_TEAM_CASES,
    run_pilot_gate_benchmark_suite,
    run_pilot_gate_red_team_suite,
)
from causa.institutional.contracts.pilot_fixtures import (
    PILOT_REHEARSAL_DATE,
    build_approved_anonymized_pilot_intake,
    build_maximally_realistic_pilot_intake,
)
from causa.institutional.contracts.synthetic_pilot import (
    build_synthetic_pilot_rehearsal_artifact,
)
from causa.pilot import (
    PILOT_GATE_VERSION,
    PILOT_INTAKE_SCHEMA_VERSION,
    PILOT_REHEARSAL_SCHEMA_VERSION,
    PilotAdmissionStatus,
    PilotIntakeRequest,
    PilotLawfulBasis,
    PilotRehearsalArtifact,
    evaluate_pilot_intake,
)


def test_synthetic_pilot_rehearsal_is_linked_and_replayable() -> None:
    artifact = build_synthetic_pilot_rehearsal_artifact()

    assert artifact.schema_version == PILOT_REHEARSAL_SCHEMA_VERSION
    assert artifact.intake.schema_version == PILOT_INTAKE_SCHEMA_VERSION
    assert artifact.gate_decision.gate_version == PILOT_GATE_VERSION
    assert artifact.gate_decision.status == PilotAdmissionStatus.APPROVED
    assert artifact.gate_decision.execution_allowed is True
    assert artifact.run_manifest is not None
    assert artifact.run_manifest.human_review_required is True
    assert artifact.run_manifest.raw_content_retained is False
    assert artifact.run_manifest.institutional_package_version == "0.20.0"
    assert artifact.utility_report.schema_version == "privacy-safe-pilot-utility.v1"


def test_pilot_gate_benchmark_and_red_team_are_complete() -> None:
    benchmark = run_pilot_gate_benchmark_suite()
    red_team = run_pilot_gate_red_team_suite()

    assert benchmark.total == len(PILOT_GATE_BENCHMARKS) == 6
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(PILOT_GATE_RED_TEAM_CASES) == 32
    assert red_team.passed == red_team.total


@pytest.mark.parametrize(
    "lawful_basis",
    [
        PilotLawfulBasis.SUBJECT_CONSENT,
        PilotLawfulBasis.CONTRACT_WITH_SUBJECT,
        PilotLawfulBasis.STATUTORY_DUTY,
        PilotLawfulBasis.RIGHTS_AND_LEGITIMATE_INTERESTS,
    ],
)
def test_approved_anonymized_pilot_records_a_reviewed_lawful_basis(
    lawful_basis: PilotLawfulBasis,
) -> None:
    request = build_approved_anonymized_pilot_intake(lawful_basis=lawful_basis)
    decision = evaluate_pilot_intake(
        request,
        evaluated_on=PILOT_REHEARSAL_DATE,
        expected_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_package_version=CONTRACTS_PACKAGE_MANIFEST.version,
    )

    assert decision.status == PilotAdmissionStatus.APPROVED
    assert (request.consent_ref is not None) == (lawful_basis == PilotLawfulBasis.SUBJECT_CONSENT)


def test_pilot_intake_forbids_raw_free_text_fields() -> None:
    data = build_maximally_realistic_pilot_intake().model_dump(mode="json")
    data["document_text"] = "Иванов И.И., паспорт 00 00 000000"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PilotIntakeRequest.model_validate(data)


def test_pilot_gate_blocks_expired_retention() -> None:
    request = build_maximally_realistic_pilot_intake().model_copy(
        update={"retention_until": date(2026, 7, 23)}
    )
    decision = evaluate_pilot_intake(
        request,
        evaluated_on=PILOT_REHEARSAL_DATE,
        expected_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_package_version=CONTRACTS_PACKAGE_MANIFEST.version,
    )

    assert decision.status == PilotAdmissionStatus.BLOCKED
    assert any("Срок хранения" in reason for reason in decision.reasons_ru)


def test_pilot_artifact_rejects_stale_gate_fingerprint() -> None:
    artifact = build_synthetic_pilot_rehearsal_artifact()
    changed_intake = artifact.intake.model_copy(update={"retention_until": date(2026, 9, 29)})

    with pytest.raises(ValidationError, match="fingerprint is stale"):
        PilotRehearsalArtifact(
            **artifact.model_dump(exclude={"intake"}),
            intake=changed_intake,
        )


def test_exported_pilot_rehearsal_is_reproducible() -> None:
    fixture = PilotRehearsalArtifact.model_validate_json(
        Path("examples/synthetic_pilot_rehearsal_report.json").read_text(encoding="utf-8")
    )

    assert fixture == build_synthetic_pilot_rehearsal_artifact()
