"""Тесты модели освобождения гражданина от обязательств (статья 213.28 127-ФЗ)."""

import pytest

from causa.institutional.contracts.citizen_release import (
    CitizenReleaseConstraintSet,
    CitizenReleaseEvidenceMappingResult,
    CitizenReleaseFactSet,
    build_citizen_release_constraint_set,
    evaluate_citizen_release_constraints,
)
from causa.institutional.contracts.citizen_release_evaluation import (
    run_citizen_release_benchmark_suite,
    run_citizen_release_red_team_suite,
)
from causa.institutional.contracts.synthetic_citizen_release import (
    build_synthetic_citizen_release_evaluation_artifact,
)


def _facts(**updates: bool) -> CitizenReleaseFactSet:
    values = {name: False for name in CitizenReleaseFactSet.model_fields}
    values.update(updates)
    return CitizenReleaseFactSet(**values)


def _completed(**updates: bool) -> CitizenReleaseFactSet:
    return _facts(
        citizen_declared_bankrupt=True,
        property_realisation_completed_by_court_ruling=True,
        **updates,
    )


def _evaluate(facts: CitizenReleaseFactSet):
    return evaluate_citizen_release_constraints(CitizenReleaseConstraintSet(id="test"), facts)


def test_release_requires_the_completion_ruling() -> None:
    """До определения о завершении реализации освобождать не от чего (пункт 2)."""
    before = _evaluate(_facts(citizen_declared_bankrupt=True))
    after = _evaluate(_completed())

    assert before.citizen_released_from_obligations is False
    assert before.claim_discharged is False
    assert after.citizen_released_from_obligations is True
    assert after.claim_discharged is True


def test_the_three_bars_of_paragraph_four_work_at_the_debtors_level() -> None:
    """Освобождение не применяется вовсе: гражданин не освобождён ни от чего."""
    offence = _evaluate(_completed(held_liable_for_bankruptcy_offence_in_this_case=True))
    information = _evaluate(_completed(withheld_or_falsified_information_established_by_court=True))
    unlawful = _evaluate(_completed(acted_unlawfully_in_the_obligation_relied_on=True))

    for evaluation in (offence, information, unlawful):
        assert evaluation.release_not_applied_at_all is True
        assert evaluation.citizen_released_from_obligations is False
        assert evaluation.claim_discharged is False
    assert offence.release_barred_by_bankruptcy_offence is True
    assert information.release_barred_by_withheld_information is True
    assert unlawful.release_barred_by_unlawful_conduct_in_the_obligation is True


def test_proven_unlawful_conduct_is_the_only_bar_that_needs_a_lawyer() -> None:
    """Два основания опираются на судебный акт, третье — на доказанность.

    «Доказано, что ... гражданин действовал незаконно» оценивает суд, а не
    модель; привлечение к ответственности и установление искажения сведений
    рецензент берёт из судебного акта.
    """
    offence = _evaluate(_completed(held_liable_for_bankruptcy_offence_in_this_case=True))
    unlawful = _evaluate(_completed(acted_unlawfully_in_the_obligation_relied_on=True))

    assert offence.requires_human_citizen_release_assessment is False
    assert unlawful.requires_human_citizen_release_assessment is True


def test_a_surviving_claim_does_not_bar_the_release_itself() -> None:
    """Самое дорогое смешение двух уровней статьи.

    Из сохранения силы одного требования нельзя выводить, что гражданин не
    освобождён ни от чего: освобождение состоялось, просто этого требования не
    достигло.
    """
    evaluation = _evaluate(_completed(is_claim_named_in_paragraph_five=True))

    assert evaluation.claim_survives_as_personally_bound is True
    assert evaluation.citizen_released_from_obligations is True
    assert evaluation.release_not_applied_at_all is False
    assert evaluation.claim_discharged is False


def test_the_release_does_not_discharge_every_claim() -> None:
    """Обратное смешение: из состоявшегося освобождения — погашение любого требования."""
    plain = _evaluate(_completed())
    surviving = _evaluate(_completed(is_subsidiary_liability_claim=True))

    assert plain.claim_discharged is True
    assert surviving.citizen_released_from_obligations is True
    assert surviving.claim_discharged is False


def test_paragraph_five_names_claims_and_leaves_one_category_open() -> None:
    """Названное требование модель квалифицирует сама, оценочное — оставляет суду."""
    named = _evaluate(_completed(is_claim_named_in_paragraph_five=True))
    current = _evaluate(_completed(is_current_payment_claim=True))
    other = _evaluate(_completed(is_other_claim_inseparable_from_the_creditors_person=True))

    assert named.claim_survives_as_personally_bound is True
    assert named.requires_human_citizen_release_assessment is False
    assert current.claim_survives_as_personally_bound is True
    assert other.claim_survives_as_personally_bound is True
    # «Иное требование, неразрывно связанное с личностью кредитора» — открытая
    # оценочная категория пункта 5.
    assert other.requires_human_citizen_release_assessment is True


def test_the_fault_clause_of_paragraph_six_reaches_three_categories_of_five() -> None:
    """Распространить оговорку на остальные две значило бы освободить от них зря."""
    subsidiary = _evaluate(_completed(is_subsidiary_liability_claim=True))
    avoidance = _evaluate(_completed(is_avoided_transaction_consequences_claim=True))
    damages_without_fault = _evaluate(_completed(is_damages_claim_under_articles_53_and_53_1=True))
    damages_with_fault = _evaluate(
        _completed(
            is_damages_claim_under_articles_53_and_53_1=True,
            caused_intentionally_or_by_gross_negligence=True,
        )
    )

    # Формы вины пункт 6 здесь не требует.
    assert subsidiary.claim_survives_under_paragraph_six is True
    assert avoidance.claim_survives_under_paragraph_six is True
    # А здесь требует.
    assert damages_without_fault.claim_survives_under_paragraph_six is False
    assert damages_without_fault.claim_discharged is True
    assert damages_with_fault.claim_survives_under_paragraph_six is True
    assert damages_with_fault.claim_discharged is False


def test_all_three_fault_requiring_categories_behave_alike() -> None:
    for field_name in (
        "is_damages_claim_under_articles_53_and_53_1",
        "is_manager_damages_claim",
        "is_property_damage_claim",
    ):
        without = _evaluate(_completed(**{field_name: True}))
        with_fault = _evaluate(
            _completed(**{field_name: True}, caused_intentionally_or_by_gross_negligence=True)
        )

        assert without.claim_survives_under_paragraph_six is False, field_name
        assert with_fault.claim_survives_under_paragraph_six is True, field_name


def test_the_second_paragraph_of_paragraph_three_adds_two_more_carve_outs() -> None:
    unknown = _evaluate(_completed(creditors_did_not_know_and_should_not_have_known=True))
    settlement = _evaluate(_completed(separate_settlement_under_article_213_10_1_approved=True))

    assert unknown.claim_survives_as_unknown_to_creditors is True
    assert unknown.claim_discharged is False
    # Что кредитор не должен был знать — оценочный стандарт.
    assert unknown.requires_human_citizen_release_assessment is True
    assert settlement.claim_survives_under_separate_settlement is True
    assert settlement.claim_discharged is False
    assert settlement.requires_human_citizen_release_assessment is False


def test_a_writ_of_execution_needs_a_surviving_registered_claim() -> None:
    """Абзац 2 пункта 5: лист — на реестровые сохранившие силу требования."""
    registered = _evaluate(
        _completed(is_claim_named_in_paragraph_five=True, claim_filed_in_bankruptcy_register=True)
    )
    current = _evaluate(_completed(is_current_payment_claim=True))
    discharged = _evaluate(_completed(claim_filed_in_bankruptcy_register=True))
    under_six = _evaluate(
        _completed(is_subsidiary_liability_claim=True, claim_filed_in_bankruptcy_register=True)
    )

    assert registered.writ_of_execution_issued_for_the_surviving_registered_claim is True
    # Текущий платёж в реестр не включается, поэтому листа не получает.
    assert current.writ_of_execution_issued_for_the_surviving_registered_claim is False
    # Погашенное требование тоже.
    assert discharged.writ_of_execution_issued_for_the_surviving_registered_claim is False
    # Отсылка пункта 6 достаёт и его категории.
    assert under_six.writ_of_execution_issued_for_the_surviving_registered_claim is True


def test_the_discharge_exception_collects_both_levels() -> None:
    """То самое изъятие, о котором говорит пункт 6 статьи 213.27.

    Вывод собирается и из недопустимости освобождения, и из сохранения силы
    требования: институт очерёдности сверяет с ним свой признак рецензента.
    """
    by_bar = _evaluate(_completed(held_liable_for_bankruptcy_offence_in_this_case=True))
    by_survival = _evaluate(_completed(is_claim_named_in_paragraph_five=True))
    neither = _evaluate(_completed())

    assert by_bar.discharge_exception_applies_to_this_claim is True
    assert by_survival.discharge_exception_applies_to_this_claim is True
    assert neither.discharge_exception_applies_to_this_claim is False


def test_the_bars_of_paragraph_four_presuppose_a_bankruptcy_case() -> None:
    with pytest.raises(ValueError, match="относится к делу о банкротстве"):
        _facts(held_liable_for_bankruptcy_offence_in_this_case=True)


def test_a_claim_cannot_be_both_in_the_register_and_current() -> None:
    with pytest.raises(ValueError, match="реестровым и текущим"):
        _completed(claim_filed_in_bankruptcy_register=True, is_current_payment_claim=True)


def test_the_claim_categories_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="нескольким категориям"):
        _completed(is_claim_named_in_paragraph_five=True, is_subsidiary_liability_claim=True)


def test_the_fault_clause_presupposes_a_category_that_requires_it() -> None:
    with pytest.raises(ValueError, match="эту форму вины требует"):
        _completed(
            is_subsidiary_liability_claim=True,
            caused_intentionally_or_by_gross_negligence=True,
        )


def test_a_registered_claim_was_known_to_its_creditor() -> None:
    with pytest.raises(ValueError, match="значит кредитор о"):
        _completed(
            claim_filed_in_bankruptcy_register=True,
            creditors_did_not_know_and_should_not_have_known=True,
        )


def test_an_all_false_fact_set_yields_no_conclusion_and_no_human_flag() -> None:
    evaluation = _evaluate(_facts())

    assert evaluation.satisfiable is True
    affirmative = [
        name
        for name in type(evaluation).model_fields
        if getattr(evaluation, name) is True and name != "satisfiable"
    ]
    assert affirmative == []
    assert evaluation.reasons_ru == []


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_citizen_release_benchmark_suite()
    red_team = run_citizen_release_red_team_suite()

    assert benchmark.failed == 0, [r.task_id for r in benchmark.results if not r.passed]
    assert benchmark.total >= 18
    assert red_team.unblocked == 0, [r.case_id for r in red_team.results if not r.blocked]
    assert red_team.total >= 16


def test_the_synthetic_artifact_replays_from_reviewed_evidence() -> None:
    artifact = build_synthetic_citizen_release_evaluation_artifact()

    assert artifact.reviewed_evaluation.satisfiable is True
    # Демонстрационное дело о поставке: гражданин банкротом не признавался.
    assert artifact.reviewed_evaluation.citizen_released_from_obligations is False
    assert artifact.reviewed_evaluation.requires_human_citizen_release_assessment is False
    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0


def test_the_constraint_set_declares_what_it_executes() -> None:
    mapping = CitizenReleaseEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=_completed(is_claim_named_in_paragraph_five=True),
        legal_source_refs=["test-law"],
    )
    expressions = build_citizen_release_constraint_set(mapping).expressions

    assert len(expressions) == 13
    assert any(
        line.startswith("discharge_exception_applies_to_this_claim ==") for line in expressions
    )
