from causa.institutional.contracts.temporal import (
    ContractTemporalFacts,
    evaluate_delivery_due_date,
)


def test_delivery_due_date_missed_when_performed_late() -> None:
    evaluation = evaluate_delivery_due_date(
        ContractTemporalFacts(
            agreed_due_date="2026-01-15",
            actual_performance_date="2026-01-20",
            evaluation_date="2026-01-21",
        )
    )

    assert evaluation.due_date_missed is True
    assert "later than the agreed due date" in evaluation.reasons[0]


def test_delivery_due_date_not_missed_when_performed_on_time() -> None:
    evaluation = evaluate_delivery_due_date(
        ContractTemporalFacts(
            agreed_due_date="2026-01-15",
            actual_performance_date="2026-01-15",
            evaluation_date="2026-01-21",
        )
    )

    assert evaluation.due_date_missed is False


def test_delivery_due_date_missed_when_no_performance_after_due_date() -> None:
    evaluation = evaluate_delivery_due_date(
        ContractTemporalFacts(
            agreed_due_date="2026-01-15",
            actual_performance_date=None,
            evaluation_date="2026-01-21",
        )
    )

    assert evaluation.due_date_missed is True


def test_delivery_due_date_not_missed_without_due_date() -> None:
    evaluation = evaluate_delivery_due_date(
        ContractTemporalFacts(
            agreed_due_date=None,
            actual_performance_date="2026-01-20",
            evaluation_date="2026-01-21",
        )
    )

    assert evaluation.due_date_missed is False
    assert "No agreed due date" in evaluation.reasons[0]
