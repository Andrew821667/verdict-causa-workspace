from causa.core.bootstrap import FormalObligationRule
from causa.reasoning.formal_checks import (
    ObligationFactSet,
    build_obligation_constraint_set,
    evaluate_obligation_constraints,
)


def _rule() -> FormalObligationRule:
    return FormalObligationRule(
        id="rule-1",
        source_id="source-1",
        debtor="supplier",
        creditor="buyer",
        action="deliver goods",
    )


def test_obligation_constraints_detect_breach_issue() -> None:
    constraint_set = build_obligation_constraint_set(_rule())
    evaluation = evaluate_obligation_constraints(
        constraint_set,
        ObligationFactSet(
            duty_exists=True,
            due_date_missed=True,
            valid_exception_applies=False,
        ),
    )

    assert evaluation.satisfiable is True
    assert evaluation.breach_issue is True
    assert "Duty exists" in evaluation.reasons[0]


def test_obligation_constraints_respect_valid_exception() -> None:
    constraint_set = build_obligation_constraint_set(_rule())
    evaluation = evaluate_obligation_constraints(
        constraint_set,
        ObligationFactSet(
            duty_exists=True,
            due_date_missed=True,
            valid_exception_applies=True,
        ),
    )

    assert evaluation.satisfiable is True
    assert evaluation.breach_issue is False


def test_obligation_constraints_require_existing_duty() -> None:
    constraint_set = build_obligation_constraint_set(_rule())
    evaluation = evaluate_obligation_constraints(
        constraint_set,
        ObligationFactSet(
            duty_exists=False,
            due_date_missed=True,
            valid_exception_applies=False,
        ),
    )

    assert evaluation.satisfiable is True
    assert evaluation.breach_issue is False
