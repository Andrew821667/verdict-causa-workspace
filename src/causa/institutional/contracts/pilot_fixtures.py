import hashlib
from datetime import date

from causa.evaluation import PilotDataOrigin, PilotTaskCategory
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.pilot import (
    PilotDocumentKind,
    PilotDocumentManifestEntry,
    PilotIntakeRequest,
    PilotLawfulBasis,
    PilotPurpose,
    PilotReviewRole,
    PilotReviewSignoff,
)


PILOT_REHEARSAL_DATE = date(2026, 7, 23)


def _hash(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _signoffs() -> tuple[PilotReviewSignoff, ...]:
    return (
        PilotReviewSignoff(
            role=PilotReviewRole.PRIVACY,
            reviewer_ref="reviewer-5a1e0001",
            approved=True,
            signed_on=PILOT_REHEARSAL_DATE,
            record_ref="synthetic-privacy-review-2026-07-23",
        ),
        PilotReviewSignoff(
            role=PilotReviewRole.LEGAL_BASIS,
            reviewer_ref="reviewer-5a1e0002",
            approved=True,
            signed_on=PILOT_REHEARSAL_DATE,
            record_ref="synthetic-legal-basis-review-2026-07-23",
        ),
        PilotReviewSignoff(
            role=PilotReviewRole.INFORMATION_SECURITY,
            reviewer_ref="reviewer-5a1e0003",
            approved=True,
            signed_on=PILOT_REHEARSAL_DATE,
            record_ref="synthetic-security-review-2026-07-23",
        ),
        PilotReviewSignoff(
            role=PilotReviewRole.DOMAIN_OWNER,
            reviewer_ref="reviewer-5a1e0004",
            approved=True,
            signed_on=PILOT_REHEARSAL_DATE,
            record_ref="synthetic-domain-review-2026-07-23",
        ),
    )


def _documents(
    *,
    contains_personal_data: bool,
    contains_commercial_secret: bool = False,
) -> tuple[PilotDocumentManifestEntry, ...]:
    kinds = (
        PilotDocumentKind.CONTRACT,
        PilotDocumentKind.SPECIFICATION,
        PilotDocumentKind.DELIVERY_DOCUMENT,
        PilotDocumentKind.CLAIM,
        PilotDocumentKind.PAYMENT_DOCUMENT,
    )
    return tuple(
        PilotDocumentManifestEntry(
            id=f"pilot-doc-5a1e000{idx}",
            tenant_ref="tenant-5a1e0001",
            kind=kind,
            content_sha256=_hash(f"max-realistic-supply-pilot:{kind.value}:v1"),
            page_count=4 if kind == PilotDocumentKind.CONTRACT else 2,
            extracted_fact_count=12 if kind == PilotDocumentKind.CONTRACT else 5,
            contains_personal_data=contains_personal_data,
            contains_special_category_data=False,
            contains_biometric_data=False,
            contains_minor_data=False,
            contains_credentials=False,
            contains_state_secret=False,
            contains_commercial_secret=contains_commercial_secret,
            direct_identifiers_removed=True,
            quasi_identifiers_generalized=True,
            irrelevant_content_removed=True,
            commercial_secret_owner_approval_ref=(
                "synthetic-commercial-secret-owner-approval" if contains_commercial_secret else None
            ),
        )
        for idx, kind in enumerate(kinds, start=1)
    )


def build_maximally_realistic_pilot_intake() -> PilotIntakeRequest:
    return PilotIntakeRequest(
        id="pilot-intake-5a1e0001",
        case_ref="case-5a1e0001",
        tenant_ref="tenant-5a1e0001",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        institutional_package_version=CONTRACTS_PACKAGE_MANIFEST.version,
        data_origin=PilotDataOrigin.SYNTHETIC_SCHEMA_DEMO,
        task_category=PilotTaskCategory.SUPPLY_DELIVERY,
        purpose=PilotPurpose.CONTRACT_DISPUTE_EVALUATION,
        lawful_basis=PilotLawfulBasis.NOT_APPLICABLE,
        processor_engaged=False,
        local_storage_confirmed=True,
        cross_border_transfer_requested=False,
        external_model_access_requested=False,
        encryption_at_rest=True,
        encryption_in_transit=True,
        role_based_access=True,
        audit_log_enabled=True,
        deletion_plan_approved=True,
        raw_content_embedded=False,
        retention_until=date(2026, 9, 30),
        documents=_documents(contains_personal_data=False),
        signoffs=_signoffs(),
    )


def build_approved_anonymized_pilot_intake(
    *,
    lawful_basis: PilotLawfulBasis = PilotLawfulBasis.SUBJECT_CONSENT,
    contains_commercial_secret: bool = False,
) -> PilotIntakeRequest:
    return build_maximally_realistic_pilot_intake().model_copy(
        update={
            "id": "pilot-intake-5a1e0002",
            "case_ref": "case-5a1e0002",
            "data_origin": PilotDataOrigin.APPROVED_ANONYMIZED_PILOT,
            "lawful_basis": lawful_basis,
            "legal_basis_review_ref": "approved-legal-basis-review",
            "consent_ref": (
                "approved-subject-consent"
                if lawful_basis == PilotLawfulBasis.SUBJECT_CONSENT
                else None
            ),
            "documents": _documents(
                contains_personal_data=True,
                contains_commercial_secret=contains_commercial_secret,
            ),
        }
    )
