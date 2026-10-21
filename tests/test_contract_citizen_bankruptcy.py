"""Тесты модели несостоятельности (банкротства) гражданина (статья 25 ГК РФ)."""

import pytest

from causa.institutional.contracts.bankruptcy_ranking import (
    BankruptcyRankingConstraintSet,
    BankruptcyRankingFactSet,
    evaluate_bankruptcy_ranking_constraints,
)
from causa.institutional.contracts.citizen_bankruptcy import (
    CitizenBankruptcyConstraintSet,
    CitizenBankruptcyEvidenceMappingResult,
    CitizenBankruptcyFactSet,
    build_citizen_bankruptcy_constraint_set,
    evaluate_citizen_bankruptcy_constraints,
)
from causa.institutional.contracts.citizen_bankruptcy_evaluation import (
    run_citizen_bankruptcy_benchmark_suite,
    run_citizen_bankruptcy_red_team_suite,
)
from causa.institutional.contracts.synthetic_citizen_bankruptcy import (
    build_synthetic_citizen_bankruptcy_evaluation_artifact,
)


def _facts(**updates: bool) -> CitizenBankruptcyFactSet:
    values = {name: False for name in CitizenBankruptcyFactSet.model_fields}
    values.update(updates)
    return CitizenBankruptcyFactSet(**values)


def _evaluate(facts: CitizenBankruptcyFactSet):
    return evaluate_citizen_bankruptcy_constraints(CitizenBankruptcyConstraintSet(id="test"), facts)


#: Условие пункта 1 выполнено по денежным обязательствам.
INSOLVENT = {
    "debtor_is_a_citizen": True,
    "unable_to_satisfy_monetary_obligations": True,
}

#: Тот же гражданин, признанный банкротом решением арбитражного суда.
DECLARED = dict(INSOLVENT, arbitration_court_declared_bankrupt=True)


def test_either_inability_of_paragraph_one_suffices() -> None:
    """Союз «и (или)» прочитан как ИЛИ, потому что так он и написан."""
    monetary = _evaluate(_facts(**INSOLVENT))
    obligatory = _evaluate(_facts(debtor_is_a_citizen=True, unable_to_pay_obligatory_payments=True))
    both = _evaluate(
        _facts(
            debtor_is_a_citizen=True,
            unable_to_satisfy_monetary_obligations=True,
            unable_to_pay_obligatory_payments=True,
        )
    )

    assert monetary.citizen_may_be_declared_bankrupt is True
    assert obligatory.citizen_may_be_declared_bankrupt is True
    assert both.citizen_may_be_declared_bankrupt is True


def test_inability_alone_does_not_make_anyone_bankrupt() -> None:
    """«Может быть признан» — возможность, а не следствие.

    Различие не формальное: последствия банкротства наступают от признания, и
    модель, выводившая признание из неспособности, переносила бы их на
    гражданина, которого банкротом никто не признавал.
    """
    evaluation = _evaluate(_facts(**INSOLVENT))

    assert evaluation.citizen_may_be_declared_bankrupt is True
    assert evaluation.citizen_declared_bankrupt is False
    assert any("остаётся возможностью" in reason for reason in evaluation.reasons_ru)


def test_only_a_court_decision_declares_a_citizen_bankrupt() -> None:
    """Заявление кредитора, признание должника, внесудебный порядок — не решение."""
    by_court = _evaluate(_facts(**DECLARED))
    by_assertion = _evaluate(
        _facts(
            debtor_is_a_citizen=True,
            unable_to_satisfy_monetary_obligations=True,
            bankruptcy_asserted_without_a_court_decision=True,
        )
    )

    assert by_court.citizen_declared_bankrupt is True
    assert by_court.bankruptcy_requires_a_court_decision is False
    assert by_assertion.citizen_declared_bankrupt is False
    assert by_assertion.bankruptcy_requires_a_court_decision is True


def test_a_citizen_without_the_test_met_gets_an_answer_not_silence() -> None:
    """Пустота читалась бы как отсутствие ответа, а ответ здесь есть."""
    evaluation = _evaluate(_facts(debtor_is_a_citizen=True))

    assert evaluation.insolvency_test_not_met is True
    assert evaluation.citizen_may_be_declared_bankrupt is False
    # Невыполненное условие — это ответ, а не затруднение.
    assert evaluation.requires_human_citizen_bankruptcy_assessment is False
    assert any("не выполнено" in reason for reason in evaluation.reasons_ru)


def test_an_entity_debtor_gets_nothing_from_article_25() -> None:
    """Условия банкротства юридического лица даёт статья 65, а не статья 25."""
    evaluation = _evaluate(_facts(creditor_ranking_question_raised=True))

    assert evaluation.citizen_may_be_declared_bankrupt is False
    assert evaluation.insolvency_test_not_met is False
    assert evaluation.citizen_bankruptcy_regime_applies is False
    assert evaluation.creditor_ranking_governed_by_bankruptcy_law is False
    assert evaluation.requires_human_citizen_bankruptcy_assessment is False


def test_the_referral_of_paragraph_two_forks_by_debtor_kind() -> None:
    """Статья 213.1 закона распределяет должников-граждан по режимам.

    Модель, сказавшая «гражданин — значит глава X», ошибалась бы на
    крестьянском хозяйстве: пункт 2 статьи 213.1 исключает его прямо. Поэтому
    исключение выведено отдельным выводом, а не спрятано в отрицании.
    """
    citizen = _evaluate(_facts(**DECLARED))
    entrepreneur = _evaluate(_facts(**DECLARED, debtor_is_an_individual_entrepreneur=True))
    farm = _evaluate(_facts(**DECLARED, debtor_is_a_peasant_farm_holding=True))

    assert citizen.citizen_bankruptcy_regime_applies is True
    assert citizen.entrepreneur_specifics_apply is False
    assert entrepreneur.citizen_bankruptcy_regime_applies is True
    assert entrepreneur.entrepreneur_specifics_apply is True
    assert farm.citizen_bankruptcy_regime_applies is False
    assert farm.citizen_regime_excluded_for_peasant_farm is True


def test_a_peasant_farm_blocks_the_entrepreneur_specifics_too() -> None:
    """Главу X исключает хозяйство, а особенности пункта 3 — часть этой главы."""
    evaluation = _evaluate(
        _facts(
            **DECLARED,
            debtor_is_an_individual_entrepreneur=True,
            debtor_is_a_peasant_farm_holding=True,
        )
    )

    assert evaluation.entrepreneur_specifics_apply is False
    assert evaluation.citizen_regime_excluded_for_peasant_farm is True


def test_the_ranking_question_is_answered_by_naming_the_rule_not_the_tier() -> None:
    """Статья 25 отвечает, чем определять очерёдность, а не какова она.

    В выпуске 1.25.0 статья 213.27 не была смоделирована, и вывод поднимал флаг
    юриста: «очередь не определена, и вот чем её определять». С выпуска 1.26.0
    очередь определяет институт статьи 213.27, и флаг здесь был бы ложной
    тревогой.
    """
    evaluation = _evaluate(_facts(**DECLARED, creditor_ranking_question_raised=True))

    assert evaluation.creditor_ranking_governed_by_bankruptcy_law is True
    assert evaluation.requires_human_citizen_bankruptcy_assessment is False
    assert any("213.27" in reason for reason in evaluation.reasons_ru)


def test_article_134_applied_to_a_citizen_is_named_as_displaced() -> None:
    """Расхождение статей 134 и 213.27 не редакционное, и модель называет его."""
    evaluation = _evaluate(
        _facts(
            **DECLARED,
            creditor_ranking_question_raised=True,
            liquidation_ranking_of_article_134_applied=True,
        )
    )

    assert evaluation.liquidation_ranking_wrongly_applied_to_a_citizen is True
    assert evaluation.requires_human_citizen_bankruptcy_assessment is True
    assert any("алимент" in reason for reason in evaluation.reasons_ru)


def test_a_peasant_farm_keeps_the_liquidation_ranking() -> None:
    """Вытеснение идёт от главы X, а к хозяйству она не применяется."""
    evaluation = _evaluate(
        _facts(
            **DECLARED,
            debtor_is_a_peasant_farm_holding=True,
            creditor_ranking_question_raised=True,
            liquidation_ranking_of_article_134_applied=True,
        )
    )

    assert evaluation.liquidation_ranking_wrongly_applied_to_a_citizen is False
    assert evaluation.creditor_ranking_governed_by_bankruptcy_law is False


def test_a_court_decision_presupposes_the_inability_it_rests_on() -> None:
    with pytest.raises(ValueError, match="беспредметно"):
        _facts(debtor_is_a_citizen=True, arbitration_court_declared_bankrupt=True)


def test_a_decision_and_an_out_of_court_assertion_exclude_each_other() -> None:
    with pytest.raises(ValueError, match="исключают друг друга"):
        _facts(
            **INSOLVENT,
            arbitration_court_declared_bankrupt=True,
            bankruptcy_asserted_without_a_court_decision=True,
        )


def test_every_predicate_of_article_25_presupposes_a_citizen() -> None:
    with pytest.raises(ValueError, match="не назван гражданином"):
        _facts(unable_to_satisfy_monetary_obligations=True)
    with pytest.raises(ValueError, match="не назван гражданином"):
        _facts(debtor_is_an_individual_entrepreneur=True)


def test_applying_a_ranking_presupposes_the_ranking_question() -> None:
    with pytest.raises(ValueError, match="вопрос об очерёдности"):
        _facts(**DECLARED, liquidation_ranking_of_article_134_applied=True)


def test_an_all_false_fact_set_yields_no_conclusion_and_no_human_flag() -> None:
    """Молчание на пустых фактах: дело о поставке не тянет за собой банкротство."""
    evaluation = _evaluate(_facts())

    assert evaluation.satisfiable is True
    assert evaluation.citizen_may_be_declared_bankrupt is False
    assert evaluation.citizen_declared_bankrupt is False
    assert evaluation.bankruptcy_requires_a_court_decision is False
    assert evaluation.insolvency_test_not_met is False
    assert evaluation.citizen_bankruptcy_regime_applies is False
    assert evaluation.entrepreneur_specifics_apply is False
    assert evaluation.citizen_regime_excluded_for_peasant_farm is False
    assert evaluation.creditor_ranking_governed_by_bankruptcy_law is False
    assert evaluation.liquidation_ranking_wrongly_applied_to_a_citizen is False
    assert evaluation.requires_human_citizen_bankruptcy_assessment is False
    assert evaluation.reasons_ru == []


# --- измеренный дефект института очерёдности --------------------------------


def _ranking(**updates: bool) -> BankruptcyRankingFactSet:
    values = {name: False for name in BankruptcyRankingFactSet.model_fields}
    values.update(updates)
    return BankruptcyRankingFactSet(**values)


def _rank(facts: BankruptcyRankingFactSet):
    return evaluate_bankruptcy_ranking_constraints(BankruptcyRankingConstraintSet(id="test"), facts)


def test_the_liquidation_ranking_is_withheld_from_a_citizens_claim() -> None:
    """Дефект, ради которого институт статьи 25 и доведён до института очерёдности.

    До ворот институт отвечал «третья очередь» на требование об алиментах
    гражданина-должника и не поднимал флага: предиката об алиментах у него нет,
    и требование падало в остаточную категорию. Пункт 3 статьи 213.27 относит
    его к **первой** очереди реестра. Это был неверный ответ, а не пробел.

    В версии 1.25.0 ворота снимали ответ и поднимали флаг юриста. В версии
    1.26.0 статья 213.27 смоделирована своим институтом, и флаг снят: вопрос не
    остаётся без ответа, а разбирается по применимому своду правил.
    """
    citizen = _rank(
        _ranking(
            claim_filed_in_bankruptcy_register=True,
            debtor_is_a_citizen_under_chapter_10=True,
        )
    )

    assert citizen.article_134_ranking_applies is False
    assert citizen.first_tier is False
    assert citizen.second_tier is False
    assert citizen.third_tier is False
    assert citizen.requires_human_bankruptcy_ranking_assessment is False
    assert any("213.27" in reason for reason in citizen.reasons_ru)


def test_the_gate_withholds_the_current_payment_tiers_too() -> None:
    """У текущих платежей гражданина свои четыре очереди (пункт 2 статьи 213.27)."""
    citizen = _rank(
        _ranking(
            is_current_payment_claim=True,
            is_utility_payment=True,
            debtor_is_a_citizen_under_chapter_10=True,
        )
    )

    assert citizen.current_payment_fourth_tier is False
    assert citizen.current_payment_fifth_tier is False
    # Флага нет с версии 1.26.0: очередь текущего платежа гражданина определяет
    # пункт 2 статьи 213.27, и его институт на этот вопрос отвечает.
    assert citizen.requires_human_bankruptcy_ranking_assessment is False


def test_the_gate_withholds_the_pledge_track_of_article_138() -> None:
    """Пункт 5 статьи 213.27 устанавливает для залога гражданина своё распределение."""
    citizen = _rank(
        _ranking(
            claim_filed_in_bankruptcy_register=True,
            is_secured_by_pledge=True,
            debtor_is_a_citizen_under_chapter_10=True,
        )
    )

    assert citizen.satisfied_from_pledge_proceeds is False


def test_an_entity_debtor_keeps_the_liquidation_ranking_unchanged() -> None:
    """Ворота не должны ничего менять там, где статья 134 и применяется."""
    entity = _rank(_ranking(claim_filed_in_bankruptcy_register=True))
    harm = _rank(
        _ranking(
            claim_filed_in_bankruptcy_register=True,
            is_life_or_health_harm_claim=True,
        )
    )

    assert entity.article_134_ranking_applies is True
    assert entity.third_tier is True
    assert harm.first_tier is True


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_citizen_bankruptcy_benchmark_suite()
    red_team = run_citizen_bankruptcy_red_team_suite()

    assert benchmark.failed == 0, [r.task_id for r in benchmark.results if not r.passed]
    assert benchmark.total >= 15
    assert red_team.unblocked == 0, [r.case_id for r in red_team.results if not r.blocked]
    assert red_team.total >= 14


def test_the_synthetic_artifact_replays_from_reviewed_evidence() -> None:
    artifact = build_synthetic_citizen_bankruptcy_evaluation_artifact()

    assert artifact.reviewed_evaluation.satisfiable is True
    # Демонстрационное дело о поставке: должник не гражданин, институт молчит.
    assert artifact.reviewed_evaluation.citizen_bankruptcy_regime_applies is False
    assert artifact.reviewed_evaluation.requires_human_citizen_bankruptcy_assessment is False
    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0


def test_the_constraint_set_declares_what_it_executes() -> None:
    """Объявленный текст правил обязан совпасть с исполняемым."""
    mapping = CitizenBankruptcyEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=_facts(**DECLARED),
        legal_source_refs=["test-law"],
    )
    expressions = build_citizen_bankruptcy_constraint_set(mapping).expressions

    assert len(expressions) == 10
    assert any(
        line.startswith("liquidation_ranking_wrongly_applied_to_a_citizen ==")
        for line in expressions
    )
