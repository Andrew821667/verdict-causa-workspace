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
    reasons_ru: list[str] = Field(default_factory=list)


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
            reasons_ru=["Источник применим на дату оценки."],
        )

    if valid_from and moment < valid_from:
        reason = "Evaluation date is before source valid_from."
        reason_ru = "Дата оценки предшествует дате начала действия источника."
    elif valid_to and moment > valid_to:
        reason = "Evaluation date is after source valid_to."
        reason_ru = "Дата оценки наступила после окончания действия источника."
    else:
        reason = "Source is not applicable at the evaluation date."
        reason_ru = "Источник не применим на дату оценки."

    return SourceApplicabilityEvaluation(
        source_id=source.id,
        moment=moment,
        applicable=False,
        reasons=[reason],
        reasons_ru=[reason_ru],
    )
