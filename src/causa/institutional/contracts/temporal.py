from datetime import date

from pydantic import BaseModel, Field


class ContractTemporalFacts(BaseModel):
    agreed_due_date: date | None = None
    actual_performance_date: date | None = None
    evaluation_date: date


class TemporalEvaluation(BaseModel):
    due_date_missed: bool
    reasons: list[str] = Field(default_factory=list)
    reasons_ru: list[str] = Field(default_factory=list)


def evaluate_delivery_due_date(facts: ContractTemporalFacts) -> TemporalEvaluation:
    if facts.agreed_due_date is None:
        return TemporalEvaluation(
            due_date_missed=False,
            reasons=["No agreed due date is available for temporal evaluation."],
            reasons_ru=["Согласованный срок исполнения не установлен."],
        )

    if facts.actual_performance_date is not None:
        if facts.actual_performance_date > facts.agreed_due_date:
            return TemporalEvaluation(
                due_date_missed=True,
                reasons=[
                    "Actual performance date is later than the agreed due date.",
                ],
                reasons_ru=[
                    "Фактическая дата исполнения наступила после согласованного срока."
                ],
            )
        return TemporalEvaluation(
            due_date_missed=False,
            reasons=["Actual performance date is on or before the agreed due date."],
            reasons_ru=[
                "Обязательство исполнено не позднее согласованного срока."
            ],
        )

    if facts.evaluation_date > facts.agreed_due_date:
        return TemporalEvaluation(
            due_date_missed=True,
            reasons=["No performance is recorded and evaluation date is after the agreed due date."],
            reasons_ru=[
                "Исполнение не зафиксировано, а дата оценки наступила после согласованного срока."
            ],
        )

    return TemporalEvaluation(
        due_date_missed=False,
        reasons=["No performance is recorded, but the agreed due date has not passed."],
        reasons_ru=[
            "Исполнение не зафиксировано, но согласованный срок еще не наступил."
        ],
    )
