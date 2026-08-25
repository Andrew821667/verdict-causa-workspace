"""Тесты закрытия вопросов сверки правил."""

import pytest

from causa.reasoning.rule_closure import (
    ABBREVIATION_MEANINGS,
    DECLARED_RULES,
    EXECUTED_RULE_OF,
    INSTITUTE_OF,
    OPEN_QUESTION_MEANINGS_RU,
    audit_rule_closure,
    close_rule,
)
from causa.reasoning.rule_parity import parse_expression, symbols_of


def test_every_declared_rule_is_implied_by_the_executed_one() -> None:
    """Ни одно объявленное условие не потеряно.

    Доказывается следование, а не равенство: исполняемое правило почти всегда
    строже объявленного, и требовать равенства значило бы объявить дефектом
    каждое уточнение, добавленное после того, как объявление написали.
    """
    report = audit_rule_closure()

    assert report.unproven == [], report.unproven
    assert len(report.rules) == len(DECLARED_RULES)
    for closure in report.rules:
        assert closure.implication_proven, closure.declared_rule


def test_all_forty_open_questions_are_answered() -> None:
    """Сверка оставила 40 имён без соответствия — все они закрыты."""
    report = audit_rule_closure()

    assert report.open_questions_closed == 50
    for closure in report.rules:
        for entry in closure.conditions:
            if entry.was_open_question:
                assert len(entry.reason_ru) > 80, (entry.declared_rule, entry.declared_name)


def test_no_declared_name_is_left_without_a_meaning() -> None:
    """Каждое имя объявленного правила имеет соответствие в модели.

    Без этого доказательство следования проходило бы на неразобранном имени:
    решатель считал бы его свободной переменной и находил бы модель, где оно
    истинно, — то есть доказывал бы не то.
    """
    for rule, text in DECLARED_RULES.items():
        table = set(OPEN_QUESTION_MEANINGS_RU.get(rule, {})) | set(
            ABBREVIATION_MEANINGS.get(rule, {})
        )
        institute_predicates = _input_predicates(INSTITUTE_OF[rule])
        for name in symbols_of(parse_expression(text)):
            assert name in table or name in institute_predicates, (rule, name)


def test_the_meaning_table_is_scoped_to_the_rule_not_to_the_name() -> None:
    """Одно слово в разных правилах означает разное.

    `delivered_notice` в отказе от договора купли-продажи — уведомление об
    одностороннем отказе, а в приостановлении встречного исполнения —
    уведомление о приостановлении. Таблица, привязанная к имени, слила бы их.
    """
    sale = _meanings("sale_refusal")
    suspension = _meanings("counterperformance_suspension")

    assert sale["delivered_notice"] != suspension["delivered_notice"]


def test_rule_names_are_not_unique_across_institutes() -> None:
    """Область видимости обязана учитываться, и это проверяется, а не помнится.

    Имя `quality_remedies_available` есть и в купле-продаже, и в поставке.
    Плоский поиск по всем модулям брал последний найденный и доказывал
    следование не тому правилу.
    """
    import ast
    from pathlib import Path

    from causa.reasoning.rule_parity import collect_executed

    root = Path("src/causa/institutional/contracts")
    if not root.exists():
        pytest.skip("Запуск не из корня репозитория.")

    owners: dict[str, set[str]] = {}
    for path in sorted(root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for _, (rules, _problems) in collect_executed(tree).items():
            for name in rules:
                owners.setdefault(name, set()).add(path.stem)

    assert owners["quality_remedies_available"] == {"sale", "supply"}
    assert INSTITUTE_OF["quality_remedy"] == "sale"


def test_the_executed_rule_is_named_for_every_renamed_rule() -> None:
    """Пятнадцать правил переименованы целиком, и соответствие ведётся вручную."""
    for declared, executed in EXECUTED_RULE_OF.items():
        assert declared in DECLARED_RULES, declared
        assert declared != executed, declared
        assert close_rule(declared).executed_rule == executed


def test_stricter_rules_are_measured_not_assumed() -> None:
    """Утверждение «исполняемое строже» проверяется решателем."""
    report = audit_rule_closure()

    stricter = [c for c in report.rules if c.stricter_than_declared]
    assert stricter, "Ни одно правило не оказалось строже — проверьте направление следования."
    for closure in stricter:
        assert closure.implication_proven


def _input_predicates(institute: str) -> set[str]:
    from causa.institutional.contracts.synthetic_reviewed_analysis import (
        build_synthetic_supply_analysis_request,
    )

    evidence = getattr(build_synthetic_supply_analysis_request(), f"{institute}_evidence")
    return {assertion.predicate.value for assertion in evidence.assertions}


def _meanings(rule: str) -> dict[str, str]:
    table = dict(ABBREVIATION_MEANINGS.get(rule, {}))
    for name, (expression, _reason) in OPEN_QUESTION_MEANINGS_RU.get(rule, {}).items():
        table[name] = expression
    return table
