"""Тесты модели возбуждения дела о банкротстве гражданина (статьи 213.3–213.5 127-ФЗ)."""

import pytest

from causa.institutional.contracts.citizen_commencement import (
    CitizenCommencementConstraintSet,
    CitizenCommencementEvidenceMappingResult,
    CitizenCommencementFactSet,
    build_citizen_commencement_constraint_set,
    evaluate_citizen_commencement_constraints,
)
from causa.institutional.contracts.citizen_commencement_evaluation import (
    run_citizen_commencement_benchmark_suite,
    run_citizen_commencement_red_team_suite,
)
from causa.institutional.contracts.synthetic_citizen_commencement import (
    build_synthetic_citizen_commencement_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_sources import SYNTHETIC_CONTRACT_SOURCES


def _facts(**updates: bool) -> CitizenCommencementFactSet:
    values = {name: False for name in CitizenCommencementFactSet.model_fields}
    values["debtor_is_a_citizen_under_chapter_10"] = True
    values.update(updates)
    return CitizenCommencementFactSet(**values)


def _evaluate(facts: CitizenCommencementFactSet):
    return evaluate_citizen_commencement_constraints(
        CitizenCommencementConstraintSet(id="test"), facts
    )


THRESHOLD = {
    "claims_against_the_citizen_at_least_500k": True,
    "claims_unpaid_for_three_months_after_due": True,
}
CREDITOR_WITH_DECISION = dict(
    THRESHOLD,
    applicant_is_a_monetary_creditor=True,
    claim_confirmed_by_court_decision_in_force=True,
)


def test_only_three_kinds_of_applicant_have_standing() -> None:
    """Пункт 1 статьи 213.3: гражданин, конкурсный кредитор, уполномоченный орган."""
    for applicant in (
        "applicant_is_the_citizen",
        "applicant_is_a_monetary_creditor",
        "applicant_is_authorised_body",
    ):
        assert _evaluate(_facts(**{applicant: True})).applicant_has_standing is True, applicant
    other = _evaluate(_facts(applicant_is_another_person=True))
    assert other.applicant_has_standing is False
    assert other.applicant_lacks_standing is True


def test_a_creditor_excluded_by_article_2_is_not_competitive() -> None:
    """Не всякий кредитор по денежному обязательству конкурсный.

    Статья 2 исключает граждан, перед которыми должник отвечает за вред жизни
    или здоровью, авторов, лиц с компенсацией по Градостроительному кодексу и
    участников по обязательствам из участия. Такой кредитор права на заявление
    не имеет, даже с решением суда и при выполненном пороге.
    """
    evaluation = _evaluate(
        _facts(**CREDITOR_WITH_DECISION, creditor_claim_excluded_from_competitive_creditors=True)
    )

    assert evaluation.applicant_is_competitive_creditor_under_article_2 is False
    assert evaluation.applicant_lacks_standing is True
    assert evaluation.creditors_application_admissible is False
    assert any("статьёй 2" in reason for reason in evaluation.reasons_ru)


def test_the_wage_creditor_is_not_excluded_in_the_current_wording() -> None:
    """Модель следует действующей редакции статьи 2, а не памяти о прежней.

    Проверяется по тексту источника: перечень исключений из конкурсных
    кредиторов называет вред жизни или здоровью и вознаграждение авторам, но не
    оплату труда. Поэтому отдельного признака «кредитор по заработной плате» у
    модели нет, и такой кредитор идёт как обычный конкурсный.
    """
    article_2 = next(
        source.text
        for source in SYNTHETIC_CONTRACT_SOURCES
        if source.id == "synthetic-ru-127fz-2-basic-definitions-v1"
    )
    definition = next(
        paragraph
        for paragraph in article_2.split("\n\n")
        if paragraph.startswith("конкурсные кредиторы")
    )
    # Перечень исключений — внешние скобки «(за исключением …)», а внутри него
    # есть вложенные: уточнение о компенсации по Градостроительному кодексу.
    start = definition.index("(за исключением")
    depth = 0
    for position in range(start, len(definition)):
        depth += {"(": 1, ")": -1}.get(definition[position], 0)
        if depth == 0:
            break
    exclusions = definition[start : position + 1]

    assert "вреда жизни или здоровью" in exclusions
    assert "вознаграждения авторам" in exclusions
    assert "оплат" not in exclusions
    assert "заработн" not in exclusions


def test_the_threshold_needs_both_conditions() -> None:
    """Пятьсот тысяч рублей И три месяца — союз «и», а не «или»."""
    both = _evaluate(_facts(**THRESHOLD))
    amount_only = _evaluate(_facts(claims_against_the_citizen_at_least_500k=True))
    time_only = _evaluate(_facts(claims_unpaid_for_three_months_after_due=True))

    assert both.statutory_threshold_met is True
    assert amount_only.statutory_threshold_met is False
    assert time_only.statutory_threshold_met is False


def test_a_creditor_needs_a_court_decision_or_a_listed_claim() -> None:
    with_decision = _evaluate(_facts(**CREDITOR_WITH_DECISION))
    listed = _evaluate(
        _facts(
            **THRESHOLD,
            applicant_is_a_monetary_creditor=True,
            claim_listed_in_article_213_5_paragraph_2=True,
        )
    )
    neither = _evaluate(_facts(**THRESHOLD, applicant_is_a_monetary_creditor=True))

    assert with_decision.creditors_application_admissible is True
    assert listed.creditors_application_admissible is True
    assert neither.creditor_claim_basis_sufficient is False
    assert neither.creditors_application_admissible is False
    assert any("принятию не подлежит" in reason for reason in neither.reasons_ru)


def test_the_threshold_applies_to_a_creditor_without_exception() -> None:
    """Статья 213.5 не содержит ничего «иного» по отношению к порогу."""
    evaluation = _evaluate(
        _facts(
            applicant_is_a_monetary_creditor=True,
            claim_confirmed_by_court_decision_in_force=True,
            claims_against_the_citizen_at_least_500k=True,
        )
    )

    assert evaluation.statutory_threshold_met is False
    assert evaluation.creditors_application_admissible is False


def test_the_citizens_duty_and_its_breach() -> None:
    """Пункт 1 статьи 213.4: обязанность и тридцать рабочих дней."""
    duty = dict(
        applicant_is_the_citizen=True,
        claims_against_the_citizen_at_least_500k=True,
        paying_some_creditors_makes_full_performance_to_others_impossible=True,
    )
    in_time = _evaluate(_facts(**duty))
    late = _evaluate(_facts(**duty, duty_deadline_of_30_working_days_missed=True))

    assert in_time.debtor_obliged_to_file is True
    assert in_time.debtor_duty_to_file_breached is False
    assert late.debtor_duty_to_file_breached is True
    # Последствий нарушения статья 213.4 не называет.
    assert any("только само нарушение" in reason for reason in late.reasons_ru)


def test_the_citizens_own_application_without_the_threshold_is_flagged() -> None:
    """Вытеснение порога статьёй 213.4 — прочтение, и модель называет его прочтением.

    Обязанность пункта 1 надо исполнить в тридцать рабочих дней, предвидение
    банкротства пункта 2 предшествует просрочке: требование трёх месяцев
    сделало бы первое неисполнимым, а второе пустым. Прямой нормы, вытесняющей
    порог, нет, поэтому флаг.
    """
    duty = _evaluate(
        _facts(
            applicant_is_the_citizen=True,
            claims_against_the_citizen_at_least_500k=True,
            paying_some_creditors_makes_full_performance_to_others_impossible=True,
        )
    )
    with_threshold = _evaluate(_facts(**THRESHOLD, applicant_is_the_citizen=True))

    assert duty.debtors_application_admissible is True
    assert duty.threshold_displaced_for_the_debtors_own_application is True
    assert duty.requires_human_citizen_commencement_assessment is True
    assert any("прочтение структуры текста" in reason for reason in duty.reasons_ru)
    # При выполненном пороге прочтение не нужно, и флага нет.
    assert with_threshold.threshold_displaced_for_the_debtors_own_application is False
    assert with_threshold.requires_human_citizen_commencement_assessment is False


def test_foreseen_bankruptcy_needs_both_obviousness_and_the_signs() -> None:
    both = _evaluate(
        _facts(
            applicant_is_the_citizen=True,
            circumstances_obviously_show_inability_to_perform_on_time=True,
            signs_of_insolvency_or_insufficiency_of_property=True,
        )
    )
    signs_only = _evaluate(
        _facts(applicant_is_the_citizen=True, signs_of_insolvency_or_insufficiency_of_property=True)
    )

    assert both.debtor_may_file_on_foreseen_bankruptcy is True
    assert both.requires_human_citizen_commencement_assessment is True
    assert signs_only.debtor_may_file_on_foreseen_bankruptcy is False
    assert signs_only.debtors_application_admissible is False


def test_the_entrepreneur_notice_is_addressed_to_some_applicants_only() -> None:
    """Пункт 2.1 статьи 213.4 и пункт 2 статьи 213.5 — не ко всем заявителям."""
    entrepreneur = {"debtor_is_an_individual_entrepreneur": True}
    citizen = _evaluate(_facts(**THRESHOLD, **entrepreneur, applicant_is_the_citizen=True))
    listed_creditor = _evaluate(
        _facts(
            **THRESHOLD,
            **entrepreneur,
            applicant_is_a_monetary_creditor=True,
            claim_listed_in_article_213_5_paragraph_2=True,
        )
    )
    creditor_with_decision = _evaluate(_facts(**CREDITOR_WITH_DECISION, **entrepreneur))
    authorised_body = _evaluate(
        _facts(
            **THRESHOLD,
            **entrepreneur,
            applicant_is_authorised_body=True,
            claim_listed_in_article_213_5_paragraph_2=True,
        )
    )

    assert citizen.entrepreneur_notice_missing is True
    assert listed_creditor.entrepreneur_notice_missing is True
    assert creditor_with_decision.entrepreneur_notice_missing is False
    assert creditor_with_decision.creditors_application_admissible is True
    assert authorised_body.entrepreneur_notice_missing is False


def test_the_notice_restores_the_right() -> None:
    evaluation = _evaluate(
        _facts(
            **THRESHOLD,
            applicant_is_the_citizen=True,
            debtor_is_an_individual_entrepreneur=True,
            notice_of_intent_published_at_least_15_days_before=True,
        )
    )

    assert evaluation.entrepreneur_notice_missing is False
    assert evaluation.debtors_application_admissible is True


def test_one_application_has_one_applicant() -> None:
    with pytest.raises(ValueError, match="одно лицо"):
        _facts(applicant_is_the_citizen=True, applicant_is_a_monetary_creditor=True)


def test_the_article_2_exclusion_presupposes_a_creditor() -> None:
    with pytest.raises(ValueError, match="кредитором по денежному обязательству не назван"):
        _facts(
            applicant_is_the_citizen=True,
            creditor_claim_excluded_from_competitive_creditors=True,
        )


def test_the_notice_presupposes_an_entrepreneur() -> None:
    with pytest.raises(ValueError, match="индивидуальный предприниматель"):
        _facts(notice_of_intent_published_at_least_15_days_before=True)


def test_a_missed_deadline_presupposes_the_duty() -> None:
    with pytest.raises(ValueError, match="сама обязанность не"):
        _facts(applicant_is_the_citizen=True, duty_deadline_of_30_working_days_missed=True)


def test_the_claim_basis_presupposes_a_creditor() -> None:
    with pytest.raises(ValueError, match="заявитель не кредитор"):
        _facts(applicant_is_the_citizen=True, claim_confirmed_by_court_decision_in_force=True)


def test_outside_chapter_10_the_institute_is_silent() -> None:
    evaluation = _evaluate(
        _facts(debtor_is_a_citizen_under_chapter_10=False, **CREDITOR_WITH_DECISION)
    )

    affirmative = [
        name
        for name in type(evaluation).model_fields
        if getattr(evaluation, name) is True and name != "satisfiable"
    ]
    assert affirmative == []


def test_an_all_false_fact_set_yields_no_conclusion_and_no_human_flag() -> None:
    evaluation = _evaluate(_facts(debtor_is_a_citizen_under_chapter_10=False))

    assert evaluation.satisfiable is True
    assert evaluation.requires_human_citizen_commencement_assessment is False
    assert evaluation.reasons_ru == []


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_citizen_commencement_benchmark_suite()
    red_team = run_citizen_commencement_red_team_suite()

    assert benchmark.failed == 0, [r.task_id for r in benchmark.results if not r.passed]
    assert benchmark.total >= 18
    assert red_team.unblocked == 0, [r.case_id for r in red_team.results if not r.blocked]
    assert red_team.total >= 15


def test_the_synthetic_artifact_replays_from_reviewed_evidence() -> None:
    artifact = build_synthetic_citizen_commencement_evaluation_artifact()

    assert artifact.reviewed_evaluation.satisfiable is True
    assert artifact.reviewed_evaluation.applicant_has_standing is False
    assert artifact.reviewed_evaluation.requires_human_citizen_commencement_assessment is False
    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0


def test_the_constraint_set_declares_what_it_executes() -> None:
    mapping = CitizenCommencementEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=_facts(**CREDITOR_WITH_DECISION),
        legal_source_refs=["test-law"],
    )
    expressions = build_citizen_commencement_constraint_set(mapping).expressions

    assert len(expressions) == 13
    assert any(
        line.startswith("threshold_displaced_for_the_debtors_own_application ==")
        for line in expressions
    )
