from enum import Enum
from pydantic import BaseModel, Field


class TranslationLevel(str, Enum):
    EXECUTIVE = "executive"
    PROFESSIONAL = "professional"
    FORENSIC = "forensic"


class TranslationAssertionCode(str, Enum):
    SOURCE_APPLICABLE = "source_applicable"
    DUE_DATE_MISSED = "due_date_missed"
    BREACH_ISSUE = "breach_issue"
    LATE_PERFORMANCE_ISSUE = "late_performance_issue"
    DEFECT_ISSUE = "defect_issue"
    PAYMENT_DEFAULT_ISSUE = "payment_default_issue"
    DAMAGES_REMEDY_AVAILABLE = "damages_remedy_available"
    CAUSATION_EVIDENCE_GAP = "causation_evidence_gap"
    LIMITATION_BAR = "limitation_bar"
    AUTHORITY_WINNER = "authority_winner"
    HUMAN_RESOLUTION_REQUIRED = "human_resolution_required"
    COUNTERFACTUAL_SENSITIVITY = "counterfactual_sensitivity"
    FAULT_REBUTTED = "fault_rebutted"
    FORCE_MAJEURE_QUALIFIED = "force_majeure_qualified"
    LIABILITY_EXEMPTION_PREREQUISITES = "liability_exemption_prerequisites"
    LIABILITY_ISSUE = "liability_issue"
    PENALTY_REDUCTION_PREREQUISITES = "penalty_reduction_prerequisites"
    INTENTIONAL_EXCLUSION_INVALID = "intentional_exclusion_invalid"


class TranslationAssertion(BaseModel):
    code: TranslationAssertionCode
    value: bool | str
    text_ru: str
    source_refs: list[str] = Field(default_factory=list)


class TranslationArtifact(BaseModel):
    id: str
    trace_id: str
    level: TranslationLevel
    locale: str = "ru-RU"
    template_version: str
    template_content_hash: str | None = None
    policy_snapshot_id: str | None = None
    policy_content_hash: str | None = None
    text: str
    assertions: list[TranslationAssertion] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    faithfulness_checked: bool = False
    faithfulness_passed: bool = False
    usability_checked: bool = False
    usability_passed: bool = False
