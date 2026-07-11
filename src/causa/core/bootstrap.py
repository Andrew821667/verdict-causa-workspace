from enum import Enum

from pydantic import BaseModel, Field


DEFAULT_BOOTSTRAP_SCHEMA_VERSION = "contracts.norm.v0"
DEFAULT_TRANSLATOR_VERSION = "contracts-json-to-formal-v0"


class BootstrapReviewStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_REVISION = "needs_revision"
    REVIEWED = "reviewed"
    REJECTED = "rejected"


class NormCondition(BaseModel):
    id: str
    text: str


class NormConsequence(BaseModel):
    id: str
    text: str


class FormalAtom(BaseModel):
    id: str
    text: str
    source_ref: str | None = None


class FormalObligationRule(BaseModel):
    id: str
    source_id: str
    debtor: str | None = None
    creditor: str | None = None
    action: str
    conditions: list[FormalAtom] = Field(default_factory=list)
    exceptions: list[FormalAtom] = Field(default_factory=list)
    consequences: list[FormalAtom] = Field(default_factory=list)


class ReviewedNormJSON(BaseModel):
    id: str
    schema_version: str = DEFAULT_BOOTSTRAP_SCHEMA_VERSION
    source_id: str
    subjects: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    conditions: list[NormCondition] = Field(default_factory=list)
    exceptions: list[NormCondition] = Field(default_factory=list)
    consequences: list[NormConsequence] = Field(default_factory=list)
    temporal_notes: list[str] = Field(default_factory=list)
    related_norms: list[str] = Field(default_factory=list)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @property
    def is_reviewed(self) -> bool:
        return self.review_status == BootstrapReviewStatus.REVIEWED


class FormalTranslationResult(BaseModel):
    norm_id: str
    source_id: str
    schema_version: str
    translator_version: str
    obligation_rule: FormalObligationRule


def _pick_party(subjects: list[str], expected: str, fallback_index: int) -> str | None:
    for subject in subjects:
        if expected in subject.lower():
            return subject
    if len(subjects) > fallback_index:
        return subjects[fallback_index]
    return None


def _to_formal_atoms(items: list[NormCondition] | list[NormConsequence], source_id: str) -> list[FormalAtom]:
    return [FormalAtom(id=item.id, text=item.text, source_ref=source_id) for item in items]


def translate_reviewed_norm(
    norm: ReviewedNormJSON,
    translator_version: str = DEFAULT_TRANSLATOR_VERSION,
) -> FormalTranslationResult:
    if not norm.is_reviewed:
        msg = "Only reviewed norm JSON can be translated."
        raise ValueError(msg)

    action = norm.actions[0] if norm.actions else "unspecified action"
    obligation_rule = FormalObligationRule(
        id=f"obligation-rule:{norm.id}",
        source_id=norm.source_id,
        debtor=_pick_party(norm.subjects, "supplier", 0),
        creditor=_pick_party(norm.subjects, "buyer", 1),
        action=action,
        conditions=_to_formal_atoms(norm.conditions, norm.source_id),
        exceptions=_to_formal_atoms(norm.exceptions, norm.source_id),
        consequences=_to_formal_atoms(norm.consequences, norm.source_id),
    )

    return FormalTranslationResult(
        norm_id=norm.id,
        source_id=norm.source_id,
        schema_version=norm.schema_version,
        translator_version=translator_version,
        obligation_rule=obligation_rule,
    )
