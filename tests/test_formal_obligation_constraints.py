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
    assert evaluation.late_performance_issue is True
    assert evaluation.defect_issue is False
    assert evaluation.payment_default_issue is False
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
    assert evaluation.late_performance_issue is False


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


def test_obligation_constraints_detect_confirmed_defect_issue() -> None:
    constraint_set = build_obligation_constraint_set(_rule())
    evaluation = evaluate_obligation_constraints(
        constraint_set,
        ObligationFactSet(
            duty_exists=True,
            due_date_missed=False,
            performance_completed=True,
            performance_nonconforming=True,
        ),
    )

    assert evaluation.breach_issue is True
    assert evaluation.late_performance_issue is False
    assert evaluation.defect_issue is True
    assert any("Defect issue" in reason for reason in evaluation.reasons)


def test_obligation_constraints_require_completed_nonconforming_performance_for_defect() -> None:
    constraint_set = build_obligation_constraint_set(_rule())
    evaluation = evaluate_obligation_constraints(
        constraint_set,
        ObligationFactSet(
            duty_exists=True,
            due_date_missed=False,
            performance_completed=False,
            performance_nonconforming=True,
        ),
    )

    assert evaluation.defect_issue is False
    assert evaluation.breach_issue is False


def test_obligation_constraints_detect_payment_default_and_respect_defense() -> None:
    constraint_set = build_obligation_constraint_set(_rule())
    default_evaluation = evaluate_obligation_constraints(
        constraint_set,
        ObligationFactSet(
            duty_exists=False,
            due_date_missed=False,
            payment_duty_exists=True,
            payment_due=True,
            payment_missed=True,
        ),
    )
    defended_evaluation = evaluate_obligation_constraints(
        constraint_set,
        ObligationFactSet(
            duty_exists=False,
            due_date_missed=False,
            payment_duty_exists=True,
            payment_due=True,
            payment_missed=True,
            payment_defense_applies=True,
        ),
    )

    assert default_evaluation.payment_default_issue is True
    assert default_evaluation.breach_issue is True
    assert defended_evaluation.payment_default_issue is False
    assert defended_evaluation.breach_issue is False


def test_obligation_constraints_make_damages_remedy_available_with_causation() -> None:
    constraint_set = build_obligation_constraint_set(_rule())
    evaluation = evaluate_obligation_constraints(
        constraint_set,
        ObligationFactSet(
            duty_exists=True,
            due_date_missed=True,
            loss_claimed=True,
            causation_established=True,
            remedy_requested=True,
        ),
    )

    assert evaluation.damages_remedy_available is True
    assert evaluation.causation_evidence_gap is False
    assert evaluation.limitation_bar is False


def test_obligation_constraints_expose_causation_gap_and_limitation_bar() -> None:
    constraint_set = build_obligation_constraint_set(_rule())
    causation_gap_evaluation = evaluate_obligation_constraints(
        constraint_set,
        ObligationFactSet(
            duty_exists=True,
            due_date_missed=True,
            loss_claimed=True,
            causation_established=False,
            remedy_requested=True,
        ),
    )
    limitation_evaluation = evaluate_obligation_constraints(
        constraint_set,
        ObligationFactSet(
            duty_exists=True,
            due_date_missed=True,
            loss_claimed=True,
            causation_established=True,
            remedy_requested=True,
            limitation_period_expired=True,
        ),
    )

    assert causation_gap_evaluation.damages_remedy_available is False
    assert causation_gap_evaluation.causation_evidence_gap is True
    assert limitation_evaluation.damages_remedy_available is False
    assert limitation_evaluation.limitation_bar is True
