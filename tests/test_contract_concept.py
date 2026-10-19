"""Тесты модели понятия договора (статья 420 ГК РФ)."""

import pytest

from causa.institutional.contracts.contract_concept import (
    ContractConceptConstraintSet,
    ContractConceptEvidenceMappingResult,
    ContractConceptFactSet,
    build_contract_concept_constraint_set,
    evaluate_contract_concept_constraints,
)
from causa.institutional.contracts.contract_concept_evaluation import (
    run_contract_concept_benchmark_suite,
    run_contract_concept_red_team_suite,
)
from causa.institutional.contracts.synthetic_contract_concept import (
    build_synthetic_contract_concept_evaluation_artifact,
)


def _facts(**updates: bool) -> ContractConceptFactSet:
    values = {name: False for name in ContractConceptFactSet.model_fields}
    values.update(updates)
    return ContractConceptFactSet(**values)


def _evaluate(facts: ContractConceptFactSet):
    return evaluate_contract_concept_constraints(ContractConceptConstraintSet(id="test"), facts)


#: Минимальный состав пункта 1: соглашение двух лиц о гражданских правах.
CONTRACT = {
    "agreement_of_two_or_more_persons": True,
    "directed_at_establishing_rights_and_duties": True,
}

#: Тот же договор, и спорное обязательство возникло из него — состав пункта 3.
CONTRACTUAL_OBLIGATION = dict(CONTRACT, obligation_arose_from_the_contract=True)


def test_all_three_aims_of_paragraph_one_qualify_equally() -> None:
    """Установление, изменение и прекращение соединены союзом «или».

    Соглашение о расторжении есть договор не менее, чем соглашение о поставке:
    пункт 1 статьи 420 не отдаёт предпочтения ни одной из трёх направленностей.
    """
    establishing = _evaluate(_facts(**CONTRACT))
    changing = _evaluate(
        _facts(
            agreement_of_two_or_more_persons=True,
            directed_at_changing_rights_and_duties=True,
        )
    )
    terminating = _evaluate(
        _facts(
            agreement_of_two_or_more_persons=True,
            directed_at_terminating_rights_and_duties=True,
        )
    )

    assert establishing.contract_qualified_under_article_420 is True
    assert changing.contract_qualified_under_article_420 is True
    assert terminating.contract_qualified_under_article_420 is True


def test_an_agreement_without_any_aim_is_not_a_contract() -> None:
    """Соглашение само по себе договором не делает: нужна направленность."""
    evaluation = _evaluate(_facts(agreement_of_two_or_more_persons=True))

    assert evaluation.contract_qualified_under_article_420 is False
    assert evaluation.chapter_9_transaction_rules_apply is False


def test_the_two_failures_of_qualification_are_told_apart() -> None:
    """«Это не договор» звучит по-разному для двух случаев, и модель их различает.

    Односторонняя сделка не договор по числу выразивших волю; соглашение о
    трудовых или налоговых правах — по отрасли прав. Пустота на месте вывода
    читалась бы как отсутствие ответа, а один общий вывод стирал бы разницу.
    """
    unilateral = _evaluate(
        _facts(
            single_person_disposition_asserted=True,
            directed_at_establishing_rights_and_duties=True,
        )
    )
    non_civil = _evaluate(_facts(**CONTRACT, rights_and_duties_lie_outside_civil_law=True))

    assert unilateral.qualification_fails_for_lack_of_a_second_party is True
    assert unilateral.qualification_fails_for_non_civil_subject_matter is False
    assert non_civil.qualification_fails_for_non_civil_subject_matter is True
    assert non_civil.qualification_fails_for_lack_of_a_second_party is False
    assert unilateral.contract_qualified_under_article_420 is False
    assert non_civil.contract_qualified_under_article_420 is False


def test_neither_failure_raises_the_human_flag() -> None:
    """Неквалификация — это ответ, а не затруднение.

    Статья 420 к такому акту не применяется, и сказать это модель умеет сама.
    """
    unilateral = _evaluate(_facts(single_person_disposition_asserted=True))
    non_civil = _evaluate(_facts(**CONTRACT, rights_and_duties_lie_outside_civil_law=True))

    assert unilateral.requires_human_contract_concept_assessment is False
    assert non_civil.requires_human_contract_concept_assessment is False
    assert any("односторонняя сделка" in reason for reason in unilateral.reasons_ru)
    assert any("вне гражданского" in reason for reason in non_civil.reasons_ru)


def test_chapter_nine_rules_are_displaced_only_by_the_code_itself() -> None:
    """Оговорка пункта 2 названа адресно: «если иное не установлено настоящим Кодексом».

    Правила главы 9 — о форме, о недействительности, о согласии третьего лица —
    вытесняются только самим Кодексом. Условие договора, объявляющее их
    неприменимыми, этого условия не исполняет.
    """
    plain = _evaluate(_facts(**CONTRACT))
    by_code = _evaluate(_facts(**CONTRACT, code_provides_otherwise_for_transaction_rules=True))
    by_agreement = _evaluate(
        _facts(**CONTRACT, displacement_asserted_by_agreement_not_by_code=True)
    )

    assert plain.chapter_9_transaction_rules_apply is True
    assert by_code.chapter_9_transaction_rules_apply is False
    assert by_agreement.chapter_9_transaction_rules_apply is True
    assert by_agreement.agreement_cannot_displace_code_rules is True


def test_the_attempt_to_displace_by_agreement_is_sent_to_articles_421_and_422() -> None:
    """Вопрос о диспозитивности нормы статья 420 не решает, и модель это говорит.

    Пункты 2 и 3 отвечают, какой свод правил вытесняет какой. Может ли
    соглашение отступить от конкретной диспозитивной нормы — вопрос статей 421
    и 422, и ответ на него модель не придумывает, а отправляет туда.
    """
    evaluation = _evaluate(_facts(**CONTRACT, displacement_asserted_by_agreement_not_by_code=True))

    assert evaluation.agreement_cannot_displace_code_rules is True
    assert evaluation.requires_human_contract_concept_assessment is True
    assert any("421" in reason and "422" in reason for reason in evaluation.reasons_ru)


def test_general_obligation_provisions_need_an_obligation_from_the_contract() -> None:
    """Пункт 3 говорит об обязательствах, возникших из договора, а не о договоре."""
    contract_only = _evaluate(_facts(**CONTRACT))
    with_obligation = _evaluate(_facts(**CONTRACTUAL_OBLIGATION))

    assert contract_only.general_obligation_provisions_apply is False
    assert with_obligation.general_obligation_provisions_apply is True


def test_either_displacing_source_of_paragraph_three_displaces() -> None:
    """Вытесняют два источника, и каждый сам по себе: глава 27 и правила о видах."""
    chapter_27 = _evaluate(
        _facts(**CONTRACTUAL_OBLIGATION, chapter_27_rule_provides_otherwise=True)
    )
    specific_type = _evaluate(
        _facts(**CONTRACTUAL_OBLIGATION, specific_contract_type_rule_provides_otherwise=True)
    )

    for evaluation in (chapter_27, specific_type):
        assert evaluation.special_rule_displaces_general_provisions is True
        assert evaluation.general_obligation_provisions_apply is False
        assert evaluation.requires_human_contract_concept_assessment is True


def test_displacement_does_not_silently_cancel_a_pipeline_conclusion() -> None:
    """Модель знает, что общее положение вытеснено, но не знает какое.

    Её предикаты говорят о сводах правил, а не об отдельных нормах. Снять на
    этом основании конкретный вывод — например, опирающийся на статью 401,
    потому что специальное правило вытеснило статью 395, — было бы хуже, чем не
    снять ничего. Поэтому вывод поднимает флаг юриста и называет свою границу.
    """
    evaluation = _evaluate(
        _facts(**CONTRACTUAL_OBLIGATION, specific_contract_type_rule_provides_otherwise=True)
    )

    assert evaluation.requires_human_contract_concept_assessment is True
    assert any("не называет" in reason for reason in evaluation.reasons_ru)
    assert any("не знает какое" in warning for warning in evaluation.warnings_ru)


def test_the_two_clauses_displace_different_bodies_of_rules() -> None:
    """Оговорка пункта 2 не отменяет статей 307–419, а оговорка пункта 3 — главы 9.

    Пункты говорят о разных сводах, и смешение их означало бы, что одна
    оговорка вытесняет вдвое больше правил, чем вытесняет.
    """
    by_paragraph_two = _evaluate(
        _facts(**CONTRACTUAL_OBLIGATION, code_provides_otherwise_for_transaction_rules=True)
    )
    by_paragraph_three = _evaluate(
        _facts(**CONTRACTUAL_OBLIGATION, chapter_27_rule_provides_otherwise=True)
    )

    assert by_paragraph_two.chapter_9_transaction_rules_apply is False
    assert by_paragraph_two.general_obligation_provisions_apply is True
    assert by_paragraph_three.chapter_9_transaction_rules_apply is True
    assert by_paragraph_three.general_obligation_provisions_apply is False


def test_both_branches_of_paragraph_four_are_derived() -> None:
    """Условие пункта 4 оценочное, поэтому выведены и применение, и его отказ."""
    applies = _evaluate(_facts(**CONTRACT, contract_has_more_than_two_parties=True))
    withheld = _evaluate(
        _facts(
            **CONTRACT,
            contract_has_more_than_two_parties=True,
            general_contract_provision_contradicts_multilateral_nature=True,
        )
    )

    assert applies.general_contract_provisions_apply_to_multiparty_contract is True
    assert applies.general_contract_provisions_withheld_from_multiparty_contract is False
    assert applies.requires_human_contract_concept_assessment is False
    assert withheld.general_contract_provisions_withheld_from_multiparty_contract is True
    assert withheld.general_contract_provisions_apply_to_multiparty_contract is False
    # Что противоречит многостороннему характеру, устанавливает суд.
    assert withheld.requires_human_contract_concept_assessment is True


def test_a_two_party_contract_draws_no_conclusion_about_paragraph_four() -> None:
    """Пункт 4 адресован договорам более чем двух сторон и молчит об остальных."""
    evaluation = _evaluate(_facts(**CONTRACTUAL_OBLIGATION))

    assert evaluation.contract_qualified_under_article_420 is True
    assert evaluation.general_contract_provisions_apply_to_multiparty_contract is False
    assert evaluation.general_contract_provisions_withheld_from_multiparty_contract is False


def test_one_act_cannot_be_both_an_agreement_and_a_unilateral_disposition() -> None:
    with pytest.raises(ValueError, match="по числу"):
        _facts(
            agreement_of_two_or_more_persons=True,
            single_person_disposition_asserted=True,
        )


def test_the_branch_of_law_needs_rights_to_classify() -> None:
    with pytest.raises(ValueError, match="Отрасль прав"):
        _facts(
            agreement_of_two_or_more_persons=True,
            rights_and_duties_lie_outside_civil_law=True,
        )


def test_more_than_two_parties_presupposes_an_agreement() -> None:
    with pytest.raises(ValueError, match="более чем двух сторон предполагает"):
        _facts(
            single_person_disposition_asserted=True,
            directed_at_establishing_rights_and_duties=True,
            contract_has_more_than_two_parties=True,
        )


def test_the_multilateral_clause_is_meaningless_for_two_parties() -> None:
    with pytest.raises(ValueError, match="многостороннему характеру без"):
        _facts(**CONTRACT, general_contract_provision_contradicts_multilateral_nature=True)


def test_an_obligation_cannot_arise_from_a_contract_that_is_not_one() -> None:
    with pytest.raises(ValueError, match="возникнуть из договора, которого нет"):
        _facts(
            single_person_disposition_asserted=True,
            directed_at_establishing_rights_and_duties=True,
            obligation_arose_from_the_contract=True,
        )


def test_displacement_presupposes_a_contractual_obligation() -> None:
    with pytest.raises(ValueError, match="а обязательства из договора нет"):
        _facts(**CONTRACT, chapter_27_rule_provides_otherwise=True)


def test_displacement_by_agreement_presupposes_the_agreement() -> None:
    with pytest.raises(ValueError, match="предполагает само соглашение"):
        _facts(
            single_person_disposition_asserted=True,
            directed_at_establishing_rights_and_duties=True,
            displacement_asserted_by_agreement_not_by_code=True,
        )


def test_an_all_false_fact_set_yields_no_conclusion_and_no_human_flag() -> None:
    """Молчание на пустых фактах — обязательное свойство института.

    Соблазн здесь сильнее, чем у остальных институтов: статья 420 применима к
    любому договорному делу, и «по умолчанию считать договором» выглядело бы
    безобидно. Это и был бы дефект: предикат рецензента заменялся бы догадкой
    модели, а сверка с институтом свободы договора потеряла бы смысл.
    """
    evaluation = _evaluate(_facts())

    assert evaluation.satisfiable is True
    assert evaluation.contract_qualified_under_article_420 is False
    assert evaluation.qualification_fails_for_lack_of_a_second_party is False
    assert evaluation.qualification_fails_for_non_civil_subject_matter is False
    assert evaluation.chapter_9_transaction_rules_apply is False
    assert evaluation.general_obligation_provisions_apply is False
    assert evaluation.special_rule_displaces_general_provisions is False
    assert evaluation.agreement_cannot_displace_code_rules is False
    assert evaluation.general_contract_provisions_apply_to_multiparty_contract is False
    assert evaluation.general_contract_provisions_withheld_from_multiparty_contract is False
    assert evaluation.requires_human_contract_concept_assessment is False
    assert evaluation.reasons_ru == []


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_contract_concept_benchmark_suite()
    red_team = run_contract_concept_red_team_suite()

    assert benchmark.failed == 0, [r.task_id for r in benchmark.results if not r.passed]
    assert benchmark.total >= 15
    assert red_team.unblocked == 0, [r.case_id for r in red_team.results if not r.blocked]
    assert red_team.total >= 14


def test_the_synthetic_artifact_replays_from_reviewed_evidence() -> None:
    artifact = build_synthetic_contract_concept_evaluation_artifact()

    assert artifact.reviewed_evaluation.satisfiable is True
    # Демонстрационное дело о поставке: договор есть, оба свода правил применимы.
    assert artifact.reviewed_evaluation.contract_qualified_under_article_420 is True
    assert artifact.reviewed_evaluation.chapter_9_transaction_rules_apply is True
    assert artifact.reviewed_evaluation.general_obligation_provisions_apply is True
    assert artifact.reviewed_evaluation.requires_human_contract_concept_assessment is False
    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0


def test_the_constraint_set_declares_what_it_executes() -> None:
    """Объявленный текст правил обязан совпасть с исполняемым."""
    mapping = ContractConceptEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=_facts(**CONTRACTUAL_OBLIGATION),
        legal_source_refs=["test-law"],
    )
    expressions = build_contract_concept_constraint_set(mapping).expressions

    assert len(expressions) == 10
    assert any(line.startswith("agreement_cannot_displace_code_rules ==") for line in expressions)
