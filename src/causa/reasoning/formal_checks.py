from z3 import And, Bool, Not, Solver, sat


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
