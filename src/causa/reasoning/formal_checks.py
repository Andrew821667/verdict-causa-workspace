from pydantic import BaseModel, Field
from z3 import And, Bool, Implies, Not, Solver, sat

from causa.core.bootstrap import FormalObligationRule


def check_basic_contradiction(statement_a: bool, statement_b: bool) -> bool:
    """
    Toy formal check.
    Returns True if two statements are contradictory.

    Placeholder for a future deterministic JSON -> Z3 legal translation layer.
    """
    a = Bool("a")
    b = Bool("b")
    solver = Solver()
    solver.add(a == statement_a)
    solver.add(b == statement_b)
    solver.add(And(a, Not(b)))
    return solver.check() == sat


class ObligationFactSet(BaseModel):
    duty_exists: bool
    due_date_missed: bool
    valid_exception_applies: bool = False


class ConstraintSet(BaseModel):
    id: str
    rule_id: str
    source_id: str
    expressions: list[str] = Field(default_factory=list)


class ConstraintEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    breach_issue: bool
    reasons: list[str] = Field(default_factory=list)


def build_obligation_constraint_set(rule: FormalObligationRule) -> ConstraintSet:
    return ConstraintSet(
        id=f"constraint-set:{rule.id}",
        rule_id=rule.id,
        source_id=rule.source_id,
        expressions=[
            "duty_exists",
            "due_date_missed",
            "valid_exception_applies",
            "breach_issue == duty_exists AND due_date_missed AND NOT valid_exception_applies",
        ],
    )


def evaluate_obligation_constraints(
    constraint_set: ConstraintSet,
    facts: ObligationFactSet,
) -> ConstraintEvaluation:
    duty_exists = Bool("duty_exists")
    due_date_missed = Bool("due_date_missed")
    valid_exception_applies = Bool("valid_exception_applies")
    breach_issue = Bool("breach_issue")

    solver = Solver()
    solver.add(duty_exists == facts.duty_exists)
    solver.add(due_date_missed == facts.due_date_missed)
    solver.add(valid_exception_applies == facts.valid_exception_applies)
    solver.add(breach_issue == And(duty_exists, due_date_missed, Not(valid_exception_applies)))
    solver.add(Implies(Not(duty_exists), Not(breach_issue)))

    satisfiable = solver.check() == sat
    breach_detected = False
    reasons: list[str] = []
    if satisfiable:
        model = solver.model()
        breach_detected = bool(model.eval(breach_issue))
        if breach_detected:
            reasons.append("Duty exists, due date is missed, and no valid exception applies.")
        else:
            reasons.append("No breach issue under the current narrow obligation constraints.")
    else:
        reasons.append("Constraint set is unsatisfiable.")

    return ConstraintEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=satisfiable,
        breach_issue=breach_detected,
        reasons=reasons,
    )
