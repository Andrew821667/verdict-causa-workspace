"""Тесты модели специальных видов банковских счетов (статьи 860.1–860.15 ГК РФ)."""

import pytest

from causa.institutional.contracts.special_accounts import (
    SpecialAccountsConstraintSet,
    SpecialAccountsFactSet,
    build_special_accounts_constraint_set,
    evaluate_special_accounts_constraints,
)
from causa.institutional.contracts.special_accounts_evaluation import (
    run_special_accounts_benchmark_suite,
    run_special_accounts_red_team_suite,
)
from causa.institutional.contracts.synthetic_special_accounts import (
    build_synthetic_special_accounts_evaluation_artifact,
)


def _facts(**updates: bool) -> SpecialAccountsFactSet:
    values = {name: False for name in SpecialAccountsFactSet.model_fields}
    values.update(updates)
    return SpecialAccountsFactSet(**values)


def _evaluate(facts: SpecialAccountsFactSet):
    return evaluate_special_accounts_constraints(SpecialAccountsConstraintSet(id="test"), facts)


NOMINAL = {
    "special_account_asserted": True,
    "nominal_account": True,
    "beneficiary_identified_or_determinable": True,
    "nominal_form_single_signed_document": True,
}
ESCROW = {
    "special_account_asserted": True,
    "escrow_account": True,
    "escrow_grounds_defined": True,
}
PUBLIC = {
    "special_account_asserted": True,
    "public_deposit_account": True,
    "holder_authorised_by_law": True,
    "bank_meets_capital_requirement": True,
}


def test_all_three_accounts_share_one_insulation() -> None:
    """Ради чего эти счета существуют: деньги на них владельцу не принадлежат.

    Номинальный счёт, счёт эскроу и публичный депозитный счёт построены на одном —
    права на деньги у другого лица. Отсюда общий вывод: арест и списание по
    обязательствам владельца счёта не допускаются (статьи 860.5, 860.8, 860.14).
    """
    for kind in (NOMINAL, ESCROW, PUBLIC):
        evaluation = _evaluate(_facts(**kind))

        assert evaluation.special_account_qualified is True
        assert evaluation.funds_insulated_from_holder_creditors is True


def test_the_public_deposit_account_is_protected_more_widely() -> None:
    """Статья 860.14 шире статьи 860.5, и модель эту разницу держит.

    По публичному депозитному счёту арест не допускается и по обязательствам
    бенефициара и депонента. У номинального счёта такой широты нет: статья 860.5
    прямо допускает арест по обязательствам бенефициара.
    """
    public = _evaluate(_facts(**PUBLIC, seizure_for_beneficiary_or_depositor_debt=True))
    nominal = _evaluate(_facts(**NOMINAL, seizure_for_beneficiary_or_depositor_debt=True))

    assert public.public_wider_insulation_breached is True
    assert nominal.public_wider_insulation_breached is False
    assert nominal.requires_human_special_accounts_assessment is False


def test_seizure_allowed_by_law_does_not_breach_the_insulation() -> None:
    """Защита не абсолютна: закон знает случаи, когда арест допустим."""
    evaluation = _evaluate(
        _facts(**NOMINAL, seizure_or_debit_for_holder_debt=True, seizure_permitted_by_law=True)
    )

    assert evaluation.funds_insulated_from_holder_creditors is True
    assert evaluation.insulation_breached is False


def test_the_escrow_duty_arises_only_when_the_grounds_occur() -> None:
    """До наступления оснований обязанности передать сумму нет, значит нет и просрочки.

    Иначе любое удержание суммы на счёте эскроу читалось бы как нарушение, тогда
    как блокировка — это и есть смысл договора (пункт 1 статьи 860.7).
    """
    before = _evaluate(_facts(**ESCROW, escrow_payment_to_beneficiary_delayed=True))
    after = _evaluate(
        _facts(
            **ESCROW,
            escrow_grounds_occurred=True,
            escrow_payment_to_beneficiary_delayed=True,
        )
    )

    assert before.escrow_payment_duty_arisen is False
    assert before.escrow_payment_duty_breached is False
    assert after.escrow_payment_duty_arisen is True
    assert after.escrow_payment_duty_breached is True


def test_disposal_before_the_grounds_is_a_breach_for_both_sides() -> None:
    """Пункт 1 статьи 860.8: до оснований не вправе распоряжаться ни депонент, ни бенефициар."""
    evaluation = _evaluate(_facts(**ESCROW, disposal_attempted_before_grounds=True))

    assert evaluation.escrow_disposal_restriction_breached is True
    assert evaluation.requires_human_special_accounts_assessment is True


def test_the_rules_of_one_account_kind_do_not_travel_to_another() -> None:
    """§ 2, 3 и 4 главы 45 — разные договоры, а не стороны одного.

    Форма единого документа под страхом ничтожности есть у номинального счёта
    (статья 860.2) и нет у счёта эскроу; требование к капиталу банка есть у
    публичного депозитного счёта (статья 860.11) и нет у номинального.
    """
    escrow = _evaluate(_facts(**ESCROW))
    nominal = _evaluate(_facts(**NOMINAL))

    assert escrow.nominal_form_defect_makes_void is False
    assert escrow.nominal_essential_term_missing is False
    assert nominal.public_bank_requirement_breached is False
    assert nominal.public_holder_not_authorised is False


def test_an_account_cannot_be_of_two_kinds_at_once() -> None:
    with pytest.raises(ValueError, match="одновременно номинальным"):
        _facts(special_account_asserted=True, nominal_account=True, escrow_account=True)


def test_the_grounds_cannot_occur_before_they_are_defined() -> None:
    """Основания передачи наступают только тогда, когда договор их определил."""
    with pytest.raises(ValueError, match="определены договором"):
        _facts(special_account_asserted=True, escrow_account=True, escrow_grounds_occurred=True)


def test_an_unnamed_kind_of_special_account_yields_no_conclusion() -> None:
    """Заявления о специальном счёте мало: без вида счёта выводов нет."""
    evaluation = _evaluate(_facts(special_account_asserted=True))

    assert evaluation.special_account_qualified is False
    assert evaluation.account_kind_undetermined is True
    assert evaluation.funds_insulated_from_holder_creditors is False
    assert evaluation.requires_human_special_accounts_assessment is True


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_special_accounts_benchmark_suite()
    red_team = run_special_accounts_red_team_suite()

    assert benchmark.failed == 0, [r.task_id for r in benchmark.results if not r.passed]
    assert benchmark.total >= 20
    assert red_team.unblocked == 0, [r.case_id for r in red_team.results if not r.blocked]
    assert red_team.total >= 6


def test_the_synthetic_artifact_replays_from_reviewed_evidence() -> None:
    artifact = build_synthetic_special_accounts_evaluation_artifact()

    assert artifact.reviewed_evaluation.satisfiable is True
    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0


def test_the_constraint_set_declares_what_it_executes() -> None:
    """Объявленный текст правил обязан совпасть с исполняемым."""
    from causa.institutional.contracts.special_accounts import (
        SpecialAccountsEvidenceMappingResult,
    )

    mapping = SpecialAccountsEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=_facts(**NOMINAL),
        legal_source_refs=["test-law"],
    )
    expressions = build_special_accounts_constraint_set(mapping).expressions

    assert len(expressions) == 20
    assert any(line.startswith("funds_insulated_from_holder_creditors ==") for line in expressions)
