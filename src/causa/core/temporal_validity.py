from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, Field

from causa.core.models import LegalSource


@dataclass(frozen=True)
class ValidityWindow:
    valid_from: date | None = None
    valid_to: date | None = None

    def includes(self, moment: date) -> bool:
        if self.valid_from and moment < self.valid_from:
            return False
        if self.valid_to and moment > self.valid_to:
            return False
        return True


class SourceApplicabilityEvaluation(BaseModel):
    source_id: str
    moment: date
    applicable: bool
    reasons: list[str] = Field(default_factory=list)


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def evaluate_source_applicability(
    source: LegalSource,
    moment: date,
) -> SourceApplicabilityEvaluation:
    valid_from = _parse_date(source.valid_from)
    valid_to = _parse_date(source.valid_to)
    window = ValidityWindow(valid_from=valid_from, valid_to=valid_to)

    if window.includes(moment):
        return SourceApplicabilityEvaluation(
            source_id=source.id,
            moment=moment,
            applicable=True,
            reasons=["Source is applicable at the evaluation date."],
        )

    if valid_from and moment < valid_from:
        reason = "Evaluation date is before source valid_from."
    elif valid_to and moment > valid_to:
        reason = "Evaluation date is after source valid_to."
    else:
        reason = "Source is not applicable at the evaluation date."

    return SourceApplicabilityEvaluation(
        source_id=source.id,
        moment=moment,
        applicable=False,
        reasons=[reason],
    )
