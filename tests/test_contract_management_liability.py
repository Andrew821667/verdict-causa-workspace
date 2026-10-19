"""Тесты модели ответственности управляющих лиц (статья 53.1 ГК РФ)."""

import pytest

from causa.institutional.contracts.management_liability import (
    ManagementLiabilityConstraintSet,
    ManagementLiabilityEvidenceMappingResult,
    ManagementLiabilityFactSet,
    build_management_liability_constraint_set,
    evaluate_management_liability_constraints,
)
from causa.institutional.contracts.management_liability_evaluation import (
    run_management_liability_benchmark_suite,
    run_management_liability_red_team_suite,
)
from causa.institutional.contracts.synthetic_management_liability import (
    build_synthetic_management_liability_evaluation_artifact,
)


def _facts(**updates: bool) -> ManagementLiabilityFactSet:
    values = {name: False for name in ManagementLiabilityFactSet.model_fields}
    values.update(updates)
    return ManagementLiabilityFactSet(**values)


def _evaluate(facts: ManagementLiabilityFactSet):
    return evaluate_management_liability_constraints(
        ManagementLiabilityConstraintSet(id="test"), facts
    )


#: Полный состав ответственности по пункту 1: субъект, требование, убытки,
#: вина и нарушенный стандарт поведения.
DIRECTOR = {
    "authorised_to_act_for_entity": True,
    "claim_brought_by_entity_or_participant": True,
    "losses_caused_to_entity": True,
    "fault_proven": True,
    "bad_faith_proven": True,
}

MEMBER = {
    "member_of_collegial_body": True,
    "claim_brought_by_entity_or_participant": True,
    "losses_caused_to_entity": True,
    "fault_proven": True,
    "bad_faith_proven": True,
}

CONTROLLING = {
    "has_actual_ability_to_determine_actions": True,
    "losses_caused_to_entity": True,
    "fault_proven": True,
    "bad_faith_proven": True,
}


def test_the_article_names_three_subjects_and_the_model_keeps_them_apart() -> None:
    """Три основания статьи 53.1 выводятся по отдельности, а не сводятся к одному.

    Директор, член коллегиального органа и лицо, определяющее действия, отвечают
    по разным пунктам с разными условиями. Общий вывод «лицо относится к
    субъектам статьи» верен для каждого из них, но ответственность у каждого
    своя.
    """
    director = _evaluate(_facts(**DIRECTOR))
    member = _evaluate(_facts(**MEMBER))
    controlling = _evaluate(_facts(**CONTROLLING))

    assert director.person_within_article_53_1 is True
    assert director.liability_of_authorised_person is True
    assert director.liability_of_collegial_member is False
    assert director.liability_of_controlling_person is False

    assert member.liability_of_collegial_member is True
    assert member.liability_of_authorised_person is False

    assert controlling.liability_of_controlling_person is True
    assert controlling.liability_of_authorised_person is False


def test_the_exemption_of_paragraph_two_removes_only_its_own_ground() -> None:
    """Директор, входящий в правление, отвечает по пункту 1 даже с исключением пункта 2.

    Ловушка здесь в том, что исключение выглядит как освобождение от
    ответственности вообще. Оно снимает основание пункта 2, но не основание
    пункта 1: голосование против решения правления не отменяет того, что лицо
    действовало недобросовестно, выступая от имени общества.
    """
    evaluation = _evaluate(
        _facts(**DIRECTOR, member_of_collegial_body=True, voted_against_the_harmful_decision=True)
    )

    assert evaluation.collegial_member_exempt is True
    assert evaluation.liability_of_collegial_member is False
    assert evaluation.liability_of_authorised_person is True


def test_both_exemptions_of_paragraph_two_work_and_only_for_members() -> None:
    voted = _evaluate(_facts(**MEMBER, voted_against_the_harmful_decision=True))
    abstained = _evaluate(_facts(**MEMBER, abstained_in_good_faith=True))

    assert voted.collegial_member_exempt is True
    assert voted.liability_of_collegial_member is False
    assert abstained.collegial_member_exempt is True
    assert abstained.liability_of_collegial_member is False
    # Добросовестность неучастия в голосовании устанавливает суд, не модель.
    assert abstained.requires_human_management_liability_assessment is True


def test_conduct_outside_the_ordinary_course_is_an_inclusion_not_a_fourth_ground() -> None:
    """Оборот «в том числе» пункта 1 абзаца 2 — частный случай, а не отдельное основание.

    Если читать его как четвёртое основание, несоответствие обычным условиям
    оборота давало бы ответственность само по себе, минуя недобросовестность и
    неразумность. Модель читает его как включение: признак нарушает тот же
    стандарт, что и два названных, и потому входит в них через ИЛИ.
    """
    unreasonable = _evaluate(
        _facts(
            authorised_to_act_for_entity=True,
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            unreasonableness_proven=True,
        )
    )
    outside_course = _evaluate(
        _facts(
            authorised_to_act_for_entity=True,
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            conduct_outside_ordinary_course_or_risk=True,
        )
    )

    assert unreasonable.standard_of_conduct_breached is True
    assert outside_course.standard_of_conduct_breached is True
    assert outside_course.liability_of_authorised_person is True
    # Что считать обычными условиями оборота — вопрос суда.
    assert outside_course.requires_human_management_liability_assessment is True


def test_paragraph_three_does_not_require_a_demand_while_paragraphs_one_and_two_do() -> None:
    """Разница в тексте, а не в толковании: пункт 3 требования не называет.

    Пункты 1 и 2 говорят «обязано возместить по требованию юридического лица,
    его учредителей (участников)». Пункт 3 говорит «несет ответственность за
    убытки, причиненные по его вине». Модель следует тексту, иначе два разных
    состава выглядели бы одинаково.
    """
    director_without_demand = _evaluate(
        _facts(
            authorised_to_act_for_entity=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            bad_faith_proven=True,
        )
    )
    controlling_without_demand = _evaluate(_facts(**CONTROLLING))

    assert director_without_demand.standard_of_conduct_breached is True
    assert director_without_demand.liability_of_authorised_person is False
    assert controlling_without_demand.liability_of_controlling_person is True


def test_joint_liability_needs_an_established_ground_not_merely_joint_losses() -> None:
    """Пункт 4 делает солидарной уже установленную ответственность.

    Совместное причинение убытков лицом, которое по статье 53.1 не отвечает,
    солидарности не создаёт: солидарной становится обязанность возместить, а не
    сам факт совместности.
    """
    liable = _evaluate(_facts(**DIRECTOR, losses_caused_jointly_with_others=True))
    not_liable = _evaluate(
        _facts(
            authorised_to_act_for_entity=True,
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            losses_caused_jointly_with_others=True,
        )
    )

    assert liable.joint_and_several_liability is True
    # Доли между солидарными должниками статья не устанавливает — нужен юрист.
    assert liable.requires_human_management_liability_assessment is True
    assert not_liable.liability_of_authorised_person is False
    assert not_liable.joint_and_several_liability is False


def test_paragraph_five_is_asymmetric_between_the_subjects() -> None:
    """Для лица пункта 3 ничтожно любое соглашение, для лиц пунктов 1 и 2 — не любое.

    Абзац 2 пункта 5 не повторяет абзац 1, а расширяет ничтожность: соглашение
    об устранении или ограничении ответственности лица, определяющего действия
    юридического лица, ничтожно независимо от того, что оно охватывает.
    """
    controlling_any_agreement = _evaluate(
        _facts(
            has_actual_ability_to_determine_actions=True,
            liability_limitation_agreement_made=True,
        )
    )
    director_unreasonable_only = _evaluate(
        _facts(
            authorised_to_act_for_entity=True,
            liability_limitation_agreement_made=True,
            agreement_covers_unreasonable_conduct=True,
        )
    )
    director_bad_faith = _evaluate(
        _facts(
            authorised_to_act_for_entity=True,
            liability_limitation_agreement_made=True,
            agreement_covers_bad_faith_conduct=True,
        )
    )

    assert controlling_any_agreement.liability_limitation_agreement_void is True
    assert director_bad_faith.liability_limitation_agreement_void is True
    assert director_unreasonable_only.liability_limitation_agreement_void is False


def test_a_public_company_cannot_limit_liability_for_unreasonable_conduct_either() -> None:
    """Публичность общества меняет исход при том же соглашении."""
    private = _evaluate(
        _facts(
            member_of_collegial_body=True,
            liability_limitation_agreement_made=True,
            agreement_covers_unreasonable_conduct=True,
        )
    )
    public = _evaluate(
        _facts(
            member_of_collegial_body=True,
            entity_is_public_company=True,
            liability_limitation_agreement_made=True,
            agreement_covers_unreasonable_conduct=True,
        )
    )

    assert private.liability_limitation_agreement_void is False
    assert public.liability_limitation_agreement_void is True


def test_the_permitted_limitation_is_stated_positively_not_left_to_subtraction() -> None:
    """Вывод из отрицания назван отдельным выводом, иначе он теряется.

    «Соглашение не ничтожно» и «ограничение допустимо» читаются по-разному:
    первое похоже на отсутствие ответа, второе отвечает. Непубличное общество,
    соглашение о неразумных, но добросовестных действиях — ровно тот случай,
    который пункт 5 оставляет действительным.
    """
    evaluation = _evaluate(
        _facts(
            authorised_to_act_for_entity=True,
            liability_limitation_agreement_made=True,
            agreement_covers_unreasonable_conduct=True,
        )
    )

    assert evaluation.limitation_of_unreasonable_conduct_permitted is True
    assert evaluation.liability_limitation_agreement_void is False
    assert any("легко теряется" in reason for reason in evaluation.reasons_ru)


def test_a_limitation_covering_bad_faith_is_never_permitted() -> None:
    evaluation = _evaluate(
        _facts(
            authorised_to_act_for_entity=True,
            liability_limitation_agreement_made=True,
            agreement_covers_unreasonable_conduct=True,
            agreement_covers_bad_faith_conduct=True,
        )
    )

    assert evaluation.liability_limitation_agreement_void is True
    assert evaluation.limitation_of_unreasonable_conduct_permitted is False


def test_a_person_outside_the_article_is_told_so_rather_than_left_silent() -> None:
    """Пустой вывод читался бы как «ответственности нет», а верно другое.

    Статья 53.1 к такому лицу не применяется — это не то же самое, что отказ в
    иске по ней. Модель называет причину прямо.
    """
    evaluation = _evaluate(
        _facts(
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            bad_faith_proven=True,
        )
    )

    assert evaluation.person_within_article_53_1 is False
    assert evaluation.liability_of_authorised_person is False
    assert evaluation.liability_of_collegial_member is False
    assert evaluation.liability_of_controlling_person is False
    assert any("не применяется" in reason for reason in evaluation.reasons_ru)


def test_voting_against_and_abstaining_are_two_different_exemptions() -> None:
    with pytest.raises(ValueError, match="двумя разными исключениями"):
        _facts(
            member_of_collegial_body=True,
            voted_against_the_harmful_decision=True,
            abstained_in_good_faith=True,
        )


def test_the_exemptions_are_meaningless_outside_a_collegial_body() -> None:
    with pytest.raises(ValueError, match="членам коллегиальных"):
        _facts(authorised_to_act_for_entity=True, voted_against_the_harmful_decision=True)


def test_fault_without_losses_has_nothing_to_attach_to() -> None:
    with pytest.raises(ValueError, match="беспредметна"):
        _facts(authorised_to_act_for_entity=True, fault_proven=True)


def test_joint_causation_presupposes_losses() -> None:
    with pytest.raises(ValueError, match="предполагает убытки"):
        _facts(authorised_to_act_for_entity=True, losses_caused_jointly_with_others=True)


def test_the_coverage_of_an_agreement_presupposes_the_agreement() -> None:
    with pytest.raises(ValueError, match="самого соглашения нет"):
        _facts(authorised_to_act_for_entity=True, agreement_covers_bad_faith_conduct=True)


def test_an_all_false_fact_set_yields_no_conclusion_and_no_human_flag() -> None:
    """Молчание на пустых фактах — обязательное свойство института.

    Дело, в котором требований к управляющему лицу нет, обязано пройти конвейер
    без единого вывода этого института и без флага «нужен юрист»: иначе каждое
    дело о поставке тянуло бы за собой проверку ответственности директора.
    """
    evaluation = _evaluate(_facts())

    assert evaluation.satisfiable is True
    assert evaluation.person_within_article_53_1 is False
    assert evaluation.standard_of_conduct_breached is False
    assert evaluation.liability_of_authorised_person is False
    assert evaluation.liability_of_collegial_member is False
    assert evaluation.liability_of_controlling_person is False
    assert evaluation.joint_and_several_liability is False
    assert evaluation.liability_limitation_agreement_void is False
    assert evaluation.limitation_of_unreasonable_conduct_permitted is False
    assert evaluation.requires_human_management_liability_assessment is False


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_management_liability_benchmark_suite()
    red_team = run_management_liability_red_team_suite()

    assert benchmark.failed == 0, [r.task_id for r in benchmark.results if not r.passed]
    assert benchmark.total >= 15
    assert red_team.unblocked == 0, [r.case_id for r in red_team.results if not r.blocked]
    assert red_team.total >= 14


def test_the_synthetic_artifact_replays_from_reviewed_evidence() -> None:
    artifact = build_synthetic_management_liability_evaluation_artifact()

    assert artifact.reviewed_evaluation.satisfiable is True
    # Демонстрационное дело о поставке: институт обязан промолчать.
    assert artifact.reviewed_evaluation.person_within_article_53_1 is False
    assert artifact.reviewed_evaluation.requires_human_management_liability_assessment is False
    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0


def test_the_constraint_set_declares_what_it_executes() -> None:
    """Объявленный текст правил обязан совпасть с исполняемым."""
    mapping = ManagementLiabilityEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=_facts(**DIRECTOR),
        legal_source_refs=["test-law"],
    )
    expressions = build_management_liability_constraint_set(mapping).expressions

    assert len(expressions) == 10
    assert any(
        line.startswith("limitation_of_unreasonable_conduct_permitted ==") for line in expressions
    )
