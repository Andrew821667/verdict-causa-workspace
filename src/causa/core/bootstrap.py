from enum import Enum

from pydantic import BaseModel, Field


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


class ReviewedNormJSON(BaseModel):
    id: str
    schema_version: str = "contracts.norm.v0"
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
    formal_payload: dict[str, str]


def translate_reviewed_norm(
    norm: ReviewedNormJSON,
    translator_version: str = "json-to-z3-placeholder.v0",
) -> FormalTranslationResult:
    if not norm.is_reviewed:
        msg = "Only reviewed norm JSON can be translated."
        raise ValueError(msg)

    return FormalTranslationResult(
        norm_id=norm.id,
        source_id=norm.source_id,
        schema_version=norm.schema_version,
        translator_version=translator_version,
        formal_payload={"placeholder": f"formalized:{norm.id}"},
    )
