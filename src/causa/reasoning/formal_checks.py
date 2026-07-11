from pydantic import BaseModel, Field
from z3 import And, Bool, Implies, Not, Or, Solver, sat

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
    performance_completed: bool = False
    performance_nonconforming: bool = False
    payment_duty_exists: bool = False
    payment_due: bool = False
    payment_missed: bool = False
    payment_defense_applies: bool = False
    loss_claimed: bool = False
    causation_established: bool = False
    remedy_requested: bool = False
    limitation_period_expired: bool = False


class ConstraintSet(BaseModel):
    id: str
    rule_id: str
    source_id: str
    expressions: list[str] = Field(default_factory=list)


class ConstraintEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    breach_issue: bool
    late_performance_issue: bool = False
    defect_issue: bool = False
    payment_default_issue: bool = False
    damages_remedy_available: bool = False
    causation_evidence_gap: bool = False
    limitation_bar: bool = False
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
            "late_performance_issue == duty_exists AND due_date_missed AND NOT valid_exception_applies",
            "performance_completed",
            "performance_nonconforming",
            "defect_issue == duty_exists AND performance_completed AND performance_nonconforming",
            "payment_duty_exists",
            "payment_due",
            "payment_missed",
            "payment_defense_applies",
            "payment_default_issue == payment_duty_exists AND payment_due AND payment_missed AND NOT payment_defense_applies",
            "breach_issue == late_performance_issue OR defect_issue OR payment_default_issue",
            "loss_claimed",
            "causation_established",
            "remedy_requested",
            "limitation_period_expired",
            "causation_evidence_gap == remedy_requested AND loss_claimed AND NOT causation_established",
            "limitation_bar == remedy_requested AND limitation_period_expired",
            "damages_remedy_available == breach_issue AND remedy_requested AND loss_claimed AND causation_established AND NOT limitation_period_expired",
        ],
    )


def evaluate_obligation_constraints(
    constraint_set: ConstraintSet,
    facts: ObligationFactSet,
) -> ConstraintEvaluation:
    duty_exists = Bool("duty_exists")
    due_date_missed = Bool("due_date_missed")
    valid_exception_applies = Bool("valid_exception_applies")
    performance_completed = Bool("performance_completed")
    performance_nonconforming = Bool("performance_nonconforming")
    payment_duty_exists = Bool("payment_duty_exists")
    payment_due = Bool("payment_due")
    payment_missed = Bool("payment_missed")
    payment_defense_applies = Bool("payment_defense_applies")
    loss_claimed = Bool("loss_claimed")
    causation_established = Bool("causation_established")
    remedy_requested = Bool("remedy_requested")
    limitation_period_expired = Bool("limitation_period_expired")
    late_performance_issue = Bool("late_performance_issue")
    defect_issue = Bool("defect_issue")
    payment_default_issue = Bool("payment_default_issue")
    damages_remedy_available = Bool("damages_remedy_available")
    causation_evidence_gap = Bool("causation_evidence_gap")
    limitation_bar = Bool("limitation_bar")
    breach_issue = Bool("breach_issue")

    solver = Solver()
    solver.add(duty_exists == facts.duty_exists)
    solver.add(due_date_missed == facts.due_date_missed)
    solver.add(valid_exception_applies == facts.valid_exception_applies)
    solver.add(performance_completed == facts.performance_completed)
    solver.add(performance_nonconforming == facts.performance_nonconforming)
    solver.add(payment_duty_exists == facts.payment_duty_exists)
    solver.add(payment_due == facts.payment_due)
    solver.add(payment_missed == facts.payment_missed)
    solver.add(payment_defense_applies == facts.payment_defense_applies)
    solver.add(loss_claimed == facts.loss_claimed)
    solver.add(causation_established == facts.causation_established)
    solver.add(remedy_requested == facts.remedy_requested)
    solver.add(limitation_period_expired == facts.limitation_period_expired)
    solver.add(
        late_performance_issue
        == And(duty_exists, due_date_missed, Not(valid_exception_applies))
    )
    solver.add(
        defect_issue
        == And(duty_exists, performance_completed, performance_nonconforming)
    )
    solver.add(
        payment_default_issue
        == And(
            payment_duty_exists,
            payment_due,
            payment_missed,
            Not(payment_defense_applies),
        )
    )
    solver.add(
        breach_issue
        == Or(late_performance_issue, defect_issue, payment_default_issue)
    )
    solver.add(
        causation_evidence_gap
        == And(remedy_requested, loss_claimed, Not(causation_established))
    )
    solver.add(limitation_bar == And(remedy_requested, limitation_period_expired))
    solver.add(
        damages_remedy_available
        == And(
            breach_issue,
            remedy_requested,
            loss_claimed,
            causation_established,
            Not(limitation_period_expired),
        )
    )
    solver.add(Implies(Not(duty_exists), Not(late_performance_issue)))

    satisfiable = solver.check() == sat
    breach_detected = False
    late_performance_detected = False
    defect_detected = False
    payment_default_detected = False
    damages_remedy_detected = False
    causation_gap_detected = False
    limitation_bar_detected = False
    reasons: list[str] = []
    if satisfiable:
        model = solver.model()
        breach_detected = bool(model.eval(breach_issue))
        late_performance_detected = bool(model.eval(late_performance_issue))
        defect_detected = bool(model.eval(defect_issue))
        payment_default_detected = bool(model.eval(payment_default_issue))
        damages_remedy_detected = bool(model.eval(damages_remedy_available))
        causation_gap_detected = bool(model.eval(causation_evidence_gap))
        limitation_bar_detected = bool(model.eval(limitation_bar))
        if late_performance_detected:
            reasons.append(
                "Late performance issue: Duty exists, due date is missed, and no valid exception applies."
            )
        if defect_detected:
            reasons.append(
                "Defect issue: completed performance is confirmed nonconforming."
            )
        if payment_default_detected:
            reasons.append(
                "Payment default issue: payment duty is due, missed, and has no valid defense."
            )
        if damages_remedy_detected:
            reasons.append(
                "Damages remedy is available under the current narrow facts."
            )
        if causation_gap_detected:
            reasons.append(
                "Causation evidence gap: a remedy is requested for claimed loss without established causation."
            )
        if limitation_bar_detected:
            reasons.append("Limitation bar: the requested remedy is time-barred.")
        if not breach_detected:
            reasons.append("No contractual issue under the current narrow constraint set.")
    else:
        reasons.append("Constraint set is unsatisfiable.")

    return ConstraintEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=satisfiable,
        breach_issue=breach_detected,
        late_performance_issue=late_performance_detected,
        defect_issue=defect_detected,
        payment_default_issue=payment_default_detected,
        damages_remedy_available=damages_remedy_detected,
        causation_evidence_gap=causation_gap_detected,
        limitation_bar=limitation_bar_detected,
        reasons=reasons,
    )
