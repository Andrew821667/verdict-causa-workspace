"""Тесты модели очерёдности требований кредиторов гражданина (статья 213.27 127-ФЗ)."""

import pytest

from causa.institutional.contracts.bankruptcy_ranking import (
    BankruptcyRankingConstraintSet,
    BankruptcyRankingFactSet,
    evaluate_bankruptcy_ranking_constraints,
)
from causa.institutional.contracts.citizen_ranking import (
    CitizenRankingConstraintSet,
    CitizenRankingEvidenceMappingResult,
    CitizenRankingFactSet,
    build_citizen_ranking_constraint_set,
    evaluate_citizen_ranking_constraints,
)
from causa.institutional.contracts.citizen_ranking_evaluation import (
    run_citizen_ranking_benchmark_suite,
    run_citizen_ranking_red_team_suite,
)
from causa.institutional.contracts.synthetic_citizen_ranking import (
    build_synthetic_citizen_ranking_evaluation_artifact,
)


def _facts(**updates: bool) -> CitizenRankingFactSet:
    values = {name: False for name in CitizenRankingFactSet.model_fields}
    values["debtor_is_a_citizen_under_chapter_10"] = True
    values.update(updates)
    return CitizenRankingFactSet(**values)


def _evaluate(facts: CitizenRankingFactSet):
    return evaluate_citizen_ranking_constraints(CitizenRankingConstraintSet(id="test"), facts)


def _registry(**updates: bool) -> CitizenRankingFactSet:
    return _facts(claim_filed_in_bankruptcy_register=True, **updates)


def _current(**updates: bool) -> CitizenRankingFactSet:
    return _facts(is_current_payment_claim=True, **updates)


def _tier(evaluation, prefix: str) -> list[str]:
    names = ("first_tier", "second_tier", "third_tier", "fourth_tier")
    return [name for name in names if getattr(evaluation, f"{prefix}{name}", False)]


def test_maintenance_is_a_first_tier_registry_claim() -> None:
    """Ровно тот ответ, который статья 134 давала неверно.

    У пункта 4 статьи 134 категории алиментов нет вовсе, и требование падало в
    остаточную третью очередь. Пункт 3 статьи 213.27 ставит его в первую
    очередь наравне с вредом жизни и здоровью.
    """
    evaluation = _evaluate(_registry(is_maintenance_claim=True))

    assert _tier(evaluation, "registry_") == ["first_tier"]
    assert any("алимент" in reason for reason in evaluation.reasons_ru)


def test_the_three_registry_tiers_of_paragraph_three() -> None:
    harm = _evaluate(_registry(is_life_or_health_harm_claim=True))
    labour = _evaluate(_registry(is_labour_or_severance_claim=True))
    other = _evaluate(_registry())

    assert _tier(harm, "registry_") == ["first_tier"]
    assert _tier(labour, "registry_") == ["second_tier"]
    assert _tier(other, "registry_") == ["third_tier"]


def test_the_four_current_payment_tiers_of_paragraph_two() -> None:
    """Четыре очереди, а не пять: пункт 2 статьи 213.27 отличается от статьи 134."""
    maintenance = _evaluate(_current(is_maintenance_claim=True))
    costs = _evaluate(_current(is_proceeding_cost_or_manager_fee=True))
    labour = _evaluate(_current(is_labour_or_severance_claim=True))
    housing = _evaluate(_current(is_housing_or_utility_payment=True))
    other = _evaluate(_current())

    assert _tier(maintenance, "current_payment_") == ["first_tier"]
    assert _tier(costs, "current_payment_") == ["first_tier"]
    assert _tier(labour, "current_payment_") == ["second_tier"]
    assert _tier(housing, "current_payment_") == ["third_tier"]
    assert _tier(other, "current_payment_") == ["fourth_tier"]


def test_housing_charges_are_their_own_tier_not_the_residual_one() -> None:
    """У статьи 134 эксплуатационные платежи четвёртые, здесь ЖКУ — третьи."""
    evaluation = _evaluate(_current(is_housing_or_utility_payment=True))

    assert evaluation.current_payment_third_tier is True
    assert evaluation.current_payment_fourth_tier is False
    assert any("капитальный ремонт" in reason for reason in evaluation.reasons_ru)


def test_the_two_orders_do_not_communicate() -> None:
    """Текущий платёж не встаёт в реестровую очередь, и наоборот (пункт 1)."""
    current = _evaluate(_current(is_maintenance_claim=True))
    registry = _evaluate(_registry(is_maintenance_claim=True))

    assert current.current_payments_paid_ahead_of_registry_claims is True
    assert _tier(current, "registry_") == []
    assert registry.current_payments_paid_ahead_of_registry_claims is False
    assert _tier(registry, "current_payment_") == []


def test_capitalisation_is_not_performed_for_a_citizen() -> None:
    """Вывод из отрицания назван прямо, потому что статья 135 говорит обратное.

    Для юридического лица капитализация повременных платежей производится.
    Перенос того правила на гражданина был бы ошибкой в пользу кредитора первой
    очереди за счёт остальных.
    """
    harm = _evaluate(_registry(is_life_or_health_harm_claim=True))
    other = _evaluate(_registry())

    assert harm.capitalisation_not_performed is True
    assert other.capitalisation_not_performed is False
    assert any("не производится" in reason for reason in harm.reasons_ru)


def test_the_pledge_track_of_paragraph_five_yields_three_consequences() -> None:
    """Восемьдесят процентов, условный резерв десяти и остаток в третью очередь."""
    plain = _evaluate(_registry(is_secured_by_pledge=True))
    reserved = _evaluate(
        _registry(
            is_secured_by_pledge=True,
            other_property_insufficient_for_first_and_second_tiers=True,
        )
    )
    shortfall = _evaluate(
        _registry(
            is_secured_by_pledge=True,
            pledge_proceeds_insufficient_for_the_secured_claim=True,
        )
    )

    assert plain.secured_claim_takes_eighty_percent_of_pledge_proceeds is True
    # Резерв условный: без недостаточности иного имущества его нет.
    assert plain.pledge_remainder_reserved_for_first_and_second_tiers is False
    assert reserved.pledge_remainder_reserved_for_first_and_second_tiers is True
    assert shortfall.unsecured_remainder_of_the_pledge_claim_joins_the_third_tier is True
    # Залоговое требование не попадает в остаточную третью очередь само.
    assert plain.registry_third_tier is False
    # Распределение выручки модель называет, но не считает.
    assert plain.requires_human_citizen_ranking_assessment is True


def test_an_unsatisfied_claim_is_discharged_unless_the_law_excepts_it() -> None:
    """Пункт 6: погашение — ответ, исключение — флаг.

    Перечень исключений даёт статья 213.28, и его пакет не моделирует: заявленное
    исключение снимает вывод о погашении, а не подменяется догадкой.
    """
    discharged = _evaluate(_registry(claim_unsatisfied_for_want_of_property=True))
    withheld = _evaluate(
        _registry(
            claim_unsatisfied_for_want_of_property=True,
            statutory_exception_to_discharge_applies=True,
        )
    )

    assert discharged.claim_deemed_discharged_for_want_of_property is True
    assert discharged.requires_human_citizen_ranking_assessment is False
    assert withheld.claim_deemed_discharged_for_want_of_property is False
    assert withheld.discharge_withheld_by_statutory_exception is True
    assert withheld.requires_human_citizen_ranking_assessment is True


def test_a_claim_with_no_place_in_either_order_is_told_so() -> None:
    """Пустой вывод читался бы как «очередь не определена», а ответ здесь есть."""
    evaluation = _evaluate(_facts())

    assert _tier(evaluation, "registry_") == []
    assert _tier(evaluation, "current_payment_") == []
    assert any("не применяется" in reason for reason in evaluation.reasons_ru)


def test_an_entity_debtor_gets_nothing_from_article_213_27() -> None:
    """Очерёдность статьи 213.27 существует только внутри режима главы X."""
    evaluation = _evaluate(
        _facts(
            debtor_is_a_citizen_under_chapter_10=False,
            claim_filed_in_bankruptcy_register=True,
            is_maintenance_claim=True,
        )
    )

    assert _tier(evaluation, "registry_") == []
    assert evaluation.requires_human_citizen_ranking_assessment is False
    assert evaluation.reasons_ru == []


def test_a_claim_cannot_be_both_in_the_register_and_current() -> None:
    with pytest.raises(ValueError, match="реестровым и текущим"):
        _facts(claim_filed_in_bankruptcy_register=True, is_current_payment_claim=True)


def test_the_categories_of_article_213_27_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="нескольким категориям"):
        _registry(is_maintenance_claim=True, is_life_or_health_harm_claim=True)


def test_a_category_presupposes_a_claim_in_the_case() -> None:
    with pytest.raises(ValueError, match="само требование ни реестровым"):
        _facts(is_maintenance_claim=True)


def test_proceeding_costs_are_current_by_nature() -> None:
    with pytest.raises(ValueError, match="текущие платежи по своей природе"):
        _registry(is_proceeding_cost_or_manager_fee=True)


def test_the_pledge_track_presupposes_a_registry_claim() -> None:
    with pytest.raises(ValueError, match="включённого в реестр"):
        _current(is_secured_by_pledge=True)


def test_the_pledge_conditions_presuppose_a_pledge() -> None:
    with pytest.raises(ValueError, match="без залога беспредметен"):
        _registry(pledge_proceeds_insufficient_for_the_secured_claim=True)


def test_an_exception_to_discharge_presupposes_an_unsatisfied_claim() -> None:
    with pytest.raises(ValueError, match="исключение из погашения"):
        _registry(statutory_exception_to_discharge_applies=True)


def test_an_all_false_fact_set_yields_no_conclusion_and_no_human_flag() -> None:
    """Молчание на пустых фактах: дело о поставке не тянет за собой банкротство."""
    evaluation = _evaluate(_facts(debtor_is_a_citizen_under_chapter_10=False))

    assert evaluation.satisfiable is True
    affirmative = [
        name
        for name in type(evaluation).model_fields
        if getattr(evaluation, name) is True and name != "satisfiable"
    ]
    assert affirmative == []
    assert evaluation.reasons_ru == []


# --- стык с институтом очерёдности статьи 134 -------------------------------


def _rank(**updates: bool):
    values = {name: False for name in BankruptcyRankingFactSet.model_fields}
    values.update(updates)
    return evaluate_bankruptcy_ranking_constraints(
        BankruptcyRankingConstraintSet(id="test"), BankruptcyRankingFactSet(**values)
    )


def test_the_article_134_institute_no_longer_raises_a_flag_for_a_citizen() -> None:
    """Флаг был правомерен, пока статья 213.27 не была смоделирована.

    Теперь очередь определяет её институт, и флаг здесь был бы ложной тревогой:
    вопрос не остаётся без ответа, а разбирается по применимому своду правил.
    """
    citizen = _rank(
        claim_filed_in_bankruptcy_register=True,
        debtor_is_a_citizen_under_chapter_10=True,
    )

    assert citizen.article_134_ranking_applies is False
    assert citizen.third_tier is False
    assert citizen.requires_human_bankruptcy_ranking_assessment is False
    assert any("213.27" in reason for reason in citizen.reasons_ru)


def test_the_two_institutes_answer_the_same_claim_differently_by_design() -> None:
    """Требование об алиментах: статья 134 молчит, статья 213.27 ставит в первую."""
    by_article_134 = _rank(
        claim_filed_in_bankruptcy_register=True,
        debtor_is_a_citizen_under_chapter_10=True,
    )
    by_article_213_27 = _evaluate(_registry(is_maintenance_claim=True))

    assert by_article_134.first_tier is False
    assert by_article_134.third_tier is False
    assert by_article_213_27.registry_first_tier is True


def test_an_entity_debtor_still_goes_through_article_134() -> None:
    entity = _rank(claim_filed_in_bankruptcy_register=True)

    assert entity.article_134_ranking_applies is True
    assert entity.third_tier is True


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_citizen_ranking_benchmark_suite()
    red_team = run_citizen_ranking_red_team_suite()

    assert benchmark.failed == 0, [r.task_id for r in benchmark.results if not r.passed]
    assert benchmark.total >= 17
    assert red_team.unblocked == 0, [r.case_id for r in red_team.results if not r.blocked]
    assert red_team.total >= 15


def test_the_synthetic_artifact_replays_from_reviewed_evidence() -> None:
    artifact = build_synthetic_citizen_ranking_evaluation_artifact()

    assert artifact.reviewed_evaluation.satisfiable is True
    # Демонстрационное дело о поставке: дела о банкротстве гражданина нет.
    assert artifact.reviewed_evaluation.registry_third_tier is False
    assert artifact.reviewed_evaluation.requires_human_citizen_ranking_assessment is False
    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0


def test_the_constraint_set_declares_what_it_executes() -> None:
    """Объявленный текст правил обязан совпасть с исполняемым."""
    mapping = CitizenRankingEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=_registry(is_maintenance_claim=True),
        legal_source_refs=["test-law"],
    )
    expressions = build_citizen_ranking_constraint_set(mapping).expressions

    assert len(expressions) == 15
    assert any(line.startswith("capitalisation_not_performed ==") for line in expressions)
