from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    STATUTE = "statute"
    CASE_LAW = "case_law"
    DOCTRINE = "doctrine"
    CONTRACT = "contract"
    FACT = "fact"


class LegalSource(BaseModel):
    id: str
    title: str
    source_type: SourceType
    jurisdiction: str = "RU"
    text: str
    valid_from: str | None = None
    valid_to: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LegalClaim(BaseModel):
    id: str
    text: str
    sources: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class CandidateHypothesis(BaseModel):
    id: str
    statement: str
    supporting_sources: list[str] = Field(default_factory=list)
    contradicting_sources: list[str] = Field(default_factory=list)
    risk_level: str = "medium"
    status: str = "proposed"
