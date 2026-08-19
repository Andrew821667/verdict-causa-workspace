"""Сверка объявленного правила с исполняемым.

Проверок здесь три вида, и третий важнее первых двух.

Первый — разбор: грамматика правил должна читаться так, как её читает человек,
и обязана отвергать строку, которая правилом не является.

Второй — сама сверка на заведомо известных случаях: честный модуль обязан
пройти, подложенное расхождение обязано быть найдено с контрпримером. Проверка,
неспособная провалиться, ничего не проверяет, и этот тест доказывает, что она
способна.

Третий — храповик. Расхождений сейчас 302 в девяти институтах из 88; это
измерение, а не приговор, и оно записано здесь числами. Тест не требует
исправить всё сразу — он требует, чтобы число не росло и чтобы чистый институт
не становился грязным. Один зафиксированный уровень честнее, чем красный тест,
который научатся не замечать.
"""

import ast

import pytest

from causa.reasoning.rule_parity import (
    DivergenceKind,
    ExpressionSyntaxError,
    audit_rule_parity,
    collect_declared,
    collect_executed,
    compare_institute,
    equivalent,
    parse_expression,
    parse_rule,
    render_report_ru,
    report_payload,
)

#: Расхождения на момент первой сверки. Число может только уменьшаться.
BASELINE_DIVERGENCES: dict[str, int] = {
    "sale": 70,
    "supply": 55,
    "performance_remedies": 51,
    "obligation_dynamics": 49,
    "security": 35,
    "invalidity": 19,
    "termination": 19,
    "formation": 2,
    "liability": 2,
}

#: Институтов без единого расхождения на момент первой сверки.
BASELINE_CLEAN_INSTITUTES = 79


@pytest.fixture(scope="module")
def report():
    return audit_rule_parity()


# --- Разбор -----------------------------------------------------------------


def test_precedence_is_read_the_way_a_human_reads_it() -> None:
    """NOT связывает крепче AND, AND крепче OR — иначе правило меняет смысл."""
    parsed = parse_expression("a AND NOT b OR c")

    assert parsed == ("or", [("and", [("var", "a"), ("not", ("var", "b"))]), ("var", "c")])


def test_parentheses_override_precedence() -> None:
    parsed = parse_expression("a AND (b OR c)")

    assert parsed == ("and", [("var", "a"), ("or", [("var", "b"), ("var", "c")])])


def test_a_bare_name_declares_an_input_and_not_a_rule() -> None:
    """`build_obligation_constraint_set` перечисляет входы теми же строками."""
    assert parse_rule("duty_exists") is None
    assert parse_rule("breach_issue == duty_exists") == ("breach_issue", ("var", "duty_exists"))


@pytest.mark.parametrize(
    "line",
    [
        "x == a AND",
        "x == (a AND b",
        "x == a AND OR b",
        "x == same-delay-penalty-conflict",
        "не имя == a",
    ],
)
def test_a_line_that_is_not_a_rule_is_rejected_loudly(line: str) -> None:
    """Молчаливый пропуск непонятой строки — худшее, что может сделать разборщик."""
    with pytest.raises(ExpressionSyntaxError):
        parse_rule(line)


# --- Сама сверка ------------------------------------------------------------


HONEST_MODULE = """
from z3 import And, Bool, Not, Or, Solver


def build_demo_constraint_set(inputs, case_id):
    return DemoConstraintSet(
        id="demo",
        expressions=[
            "breach == duty AND missed AND NOT excused",
        ],
    )


def evaluate_demo_constraints(constraint_set, facts):
    variables = {name: Bool(name) for name in DemoFactSet.model_fields}
    breach = Bool("breach")
    solver = Solver()
    for name, variable in variables.items():
        solver.add(variable == getattr(facts, name))
    solver.add(
        breach
        == And(variables["duty"], variables["missed"], Not(variables["excused"]))
    )
    return solver
"""

#: Тот же модуль, но объявленное правило потеряло отрицание. Это ровно тот
#: дефект, который сверка обязана ловить: юристу показывают одно, считают другое.
PLANTED_MODULE = HONEST_MODULE.replace(
    '"breach == duty AND missed AND NOT excused"',
    '"breach == duty AND missed AND excused"',
)


def _compare(source: str):
    tree = ast.parse(source)
    declared, declared_problems = collect_declared(tree)["demo"]
    executed, executed_problems = collect_executed(tree)["demo"]
    return compare_institute(
        institute="demo",
        module="demo.py",
        declared=declared,
        executed=executed,
        problems=declared_problems + executed_problems,
    )


def test_an_honest_module_passes() -> None:
    parity = _compare(HONEST_MODULE)

    assert parity.declared_rules == 1
    assert parity.executed_rules == 1
    assert parity.matched == 1
    assert parity.divergences == []


def test_the_check_would_notice_a_planted_divergence() -> None:
    """Проверка, неспособная провалиться, ничего не проверяет."""
    parity = _compare(PLANTED_MODULE)

    assert parity.matched == 0
    assert len(parity.divergences) == 1
    divergence = parity.divergences[0]
    assert divergence.kind is DivergenceKind.DIFFERENT_RULE
    assert divergence.output == "breach"
    # Контрпример — машинное доказательство дефекта, а не подозрение.
    assert divergence.counterexample
    assert set(divergence.counterexample) == {"duty", "missed", "excused"}


def test_the_input_binding_loop_is_not_mistaken_for_a_rule() -> None:
    """`variable == getattr(facts, name)` — привязка входа, а не правило."""
    executed, _ = collect_executed(ast.parse(HONEST_MODULE))["demo"]

    assert set(executed) == {"breach"}


def test_equivalence_is_proved_for_all_facts_and_not_only_the_checked_ones() -> None:
    """Перебор доказал бы совпадение на проверенных наборах; решатель — на всех."""
    same = equivalent(parse_expression("a AND b"), parse_expression("b AND a"))
    other = equivalent(parse_expression("a OR b"), parse_expression("a AND b"))

    assert same is None
    assert other == {"a": True, "b": False} or other == {"a": False, "b": True}


# --- Храповик ---------------------------------------------------------------


def test_divergences_do_not_grow(report) -> None:
    """Число расхождений может уменьшаться. Расти оно не имеет права."""
    current = {
        institute.institute: len(institute.divergences)
        for institute in report.institutes
        if institute.divergences
    }
    grown = {
        name: (count, BASELINE_DIVERGENCES.get(name, 0))
        for name, count in current.items()
        if count > BASELINE_DIVERGENCES.get(name, 0)
    }

    assert not grown, f"расхождений стало больше: {grown}"


def test_a_clean_institute_does_not_become_dirty(report) -> None:
    assert len(report.clean_institutes) >= BASELINE_CLEAN_INSTITUTES


def test_the_report_names_the_defect_and_not_only_its_count(report) -> None:
    """Отчёт «плохо» бесполезен: нужен институт, вывод и причина."""
    text = render_report_ru(report)

    assert "СВЕРКА ОБЪЯВЛЕННОГО ПРАВИЛА С ИСПОЛНЯЕМЫМ" in text
    for divergence in report.divergences[:20]:
        assert divergence.output in text


def test_the_payload_carries_every_divergence(report) -> None:
    payload = report_payload(report)
    counted = sum(len(item["divergences"]) for item in payload["institutes"])

    assert counted == payload["divergences_total"] == len(report.divergences)
