from pydantic import BaseModel, Field


class ConfidenceScore(BaseModel):
    value: float = Field(ge=0, le=1)
    rationale: str | None = None
