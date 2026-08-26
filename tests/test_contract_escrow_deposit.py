"""Тесты модели условного депонирования (эскроу, статьи 926.1–926.8 ГК РФ)."""

import pytest

from causa.institutional.contracts.escrow_deposit import (
    EscrowDepositConstraintSet,
    EscrowDepositFactSet,
    build_escrow_deposit_constraint_set,
    evaluate_escrow_deposit_constraints,
)
from causa.institutional.contracts.escrow_deposit_evaluation import (
    run_escrow_deposit_benchmark_suite,
    run_escrow_deposit_red_team_suite,
)
from causa.institutional.contracts.synthetic_escrow_deposit import (
    build_synthetic_escrow_deposit_evaluation_artifact,
)


def _facts(**updates: bool) -> EscrowDepositFactSet:
    values = {name: False for name in EscrowDepositFactSet.model_fields}
    values.update(updates)
    return EscrowDepositFactSet(**values)


def _evaluate(facts: EscrowDepositFactSet):
    return evaluate_escrow_deposit_constraints(EscrowDepositConstraintSet(id="test"), facts)


THINGS = {"escrow_deposit_asserted": True, "deposited_things": True}
MONEY = {"escrow_deposit_asserted": True, "deposited_cashless_money": True}
SECURITIES = {"escrow_deposit_asserted": True, "deposited_uncertificated_securities": True}


def test_the_contract_has_three_parties_and_property_the_agent_does_not_own() -> None:
    """Депонент, бенефициар, эскроу-агент — три стороны одного договора.

    Пока основания передачи не наступили, имущество остаётся депонента; агент
    лишь обеспечивает его сохранность (статья 926.1 ГК РФ).
    """
    evaluation = _evaluate(_facts(**THINGS, notarization_performed=True))

    assert evaluation.escrow_deposit_qualified is True
    assert evaluation.depositor_retains_title is True
    assert evaluation.title_passed_to_beneficiary is False


def test_notarization_is_required_only_when_things_are_among_the_deposit() -> None:
    """Исключение из нотариальной формы — только для денег и бумаг, не для вещей.

    Если вещи входят в состав депонируемого имущества вместе с деньгами, форма
    всё равно обязательна: исключение не распространяется на смешанный состав.
    """
    money_only = _evaluate(_facts(**MONEY, escrow_agent_is_bank=True))
    securities_only = _evaluate(
        _facts(**SECURITIES, securities_exercise_permitted_by_contract=True)
    )
    things_and_money = _evaluate(
        _facts(**THINGS, deposited_cashless_money=True, notarization_performed=True)
    )

    assert money_only.notarization_required is False
    assert securities_only.notarization_required is False
    assert things_and_money.notarization_required is True


def test_missing_notarization_where_required_makes_the_contract_void() -> None:
    evaluation = _evaluate(_facts(**THINGS))

    assert evaluation.notarization_missing_makes_void is True
    assert evaluation.requires_human_escrow_deposit_assessment is True


def test_an_excessive_term_is_read_down_not_voided() -> None:
    """Превышение пяти лет — прямая подстановка кодекса, а не порок сделки.

    Иначе договор без указания срока или со сроком в десять лет считался бы
    несостоявшимся, хотя закон сам восполняет условие о сроке.
    """
    evaluation = _evaluate(
        _facts(**THINGS, notarization_performed=True, deposit_term_missing_or_excessive=True)
    )

    assert evaluation.deposit_term_deemed_five_years is True
    assert evaluation.requires_human_escrow_deposit_assessment is False


def test_a_non_bank_agent_deposits_cashless_money_through_a_nominal_account() -> None:
    """Статья 926.6 — стык с институтом специальных банковских счетов.

    Если эскроу-агент не банк, депонируемые деньги идут через его номинальный
    счёт, а не через счёт эскроу; банк же в этой роли использует счёт эскроу
    напрямую, и правило номинального счёта к нему не относится.
    """
    non_bank = _evaluate(_facts(**MONEY))
    bank = _evaluate(_facts(**MONEY, escrow_agent_is_bank=True))

    assert non_bank.cashless_money_requires_nominal_account is True
    assert bank.cashless_money_requires_nominal_account is False


def test_the_property_is_shielded_from_the_agents_and_depositors_creditors() -> None:
    """Ради чего институт защищает имущество: оно не принадлежит ни агенту, ни депоненту."""
    clean = _evaluate(_facts(**THINGS, notarization_performed=True))
    seized = _evaluate(
        _facts(
            **THINGS,
            notarization_performed=True,
            seizure_or_debit_for_agent_or_depositor_debt=True,
        )
    )

    assert clean.deposited_property_insulated_from_agent_or_depositor_creditors is True
    assert seized.insulation_breach is True


def test_the_beneficiarys_creditor_reaches_the_claim_right_not_the_property() -> None:
    """Статья 926.7 разделяет два требования, а не расширяет один запрет.

    По долгу бенефициара нельзя арестовать депонированное имущество — можно
    обратить взыскание на его право требования к агенту о передаче.
    """
    evaluation = _evaluate(_facts(**THINGS, seizure_for_beneficiary_debt=True))

    assert evaluation.beneficiary_creditor_may_reach_claim_right is True
    assert evaluation.insulation_breach is False


def test_termination_returns_to_depositor_or_transfers_to_beneficiary() -> None:
    """Статья 926.8: что происходит с имуществом зависит от того, наступили ли основания."""
    before_grounds = _evaluate(
        _facts(**THINGS, notarization_performed=True, agent_personal_termination_ground=True)
    )
    after_grounds = _evaluate(
        _facts(
            **THINGS,
            notarization_performed=True,
            escrow_deposit_grounds_defined=True,
            grounds_for_transfer_occurred=True,
            deposit_term_expired=True,
        )
    )

    assert before_grounds.return_to_depositor_due is True
    assert before_grounds.transfer_to_beneficiary_due_on_termination is False
    assert after_grounds.return_to_depositor_due is False
    assert after_grounds.transfer_to_beneficiary_due_on_termination is True


def test_transfer_of_the_contract_prevents_termination() -> None:
    """Договор, переданный другому лицу до обстоятельства, не прекращается (статья 392.3)."""
    evaluation = _evaluate(
        _facts(
            **THINGS,
            notarization_performed=True,
            agent_personal_termination_ground=True,
            contract_transferred_under_article_392_3=True,
        )
    )

    assert evaluation.contract_transferred_to_new_agent is True
    assert evaluation.return_to_depositor_due is False
    assert evaluation.transfer_to_beneficiary_due_on_termination is False


def test_grounds_cannot_occur_before_the_contract_defines_them() -> None:
    with pytest.raises(ValueError, match="определены договором эскроу"):
        _facts(escrow_deposit_asserted=True, deposited_things=True, grounds_for_transfer_occurred=True)


def test_a_defence_to_loss_requires_a_loss_to_defend_against() -> None:
    with pytest.raises(ValueError, match="имеет смысл лишь тогда"):
        _facts(**THINGS, agent_proved_force_majeure=True)


def test_an_unnamed_kind_of_deposit_yields_no_conclusion() -> None:
    evaluation = _evaluate(_facts(escrow_deposit_asserted=True))

    assert evaluation.escrow_deposit_qualified is False
    assert evaluation.escrow_deposit_kind_undetermined is True
    assert evaluation.requires_human_escrow_deposit_assessment is True


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_escrow_deposit_benchmark_suite()
    red_team = run_escrow_deposit_red_team_suite()

    assert benchmark.failed == 0, [r.task_id for r in benchmark.results if not r.passed]
    assert benchmark.total >= 25
    assert red_team.unblocked == 0, [r.case_id for r in red_team.results if not r.blocked]
    assert red_team.total >= 6


def test_the_synthetic_artifact_replays_from_reviewed_evidence() -> None:
    artifact = build_synthetic_escrow_deposit_evaluation_artifact()

    assert artifact.reviewed_evaluation.satisfiable is True
    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0


def test_the_constraint_set_declares_what_it_executes() -> None:
    """Объявленный текст правил обязан совпасть с исполняемым."""
    from causa.institutional.contracts.escrow_deposit import EscrowDepositEvidenceMappingResult

    mapping = EscrowDepositEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=_facts(**THINGS),
        legal_source_refs=["test-law"],
    )
    expressions = build_escrow_deposit_constraint_set(mapping).expressions

    assert len(expressions) == 25
    assert any(
        line.startswith("deposited_property_insulated_from_agent_or_depositor_creditors ==")
        for line in expressions
    )
