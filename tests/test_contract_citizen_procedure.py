"""Тесты модели обоснованности заявления и процедуры банкротства гражданина.

Статьи 213.2, 213.6 и 213.13 закона 127-ФЗ.
"""

import itertools

import pytest

from causa.institutional.contracts.case_scenarios import _flip
from causa.institutional.contracts.citizen_procedure import (
    CitizenProcedureConstraintSet,
    CitizenProcedureEvidenceMappingResult,
    CitizenProcedureFactSet,
    build_citizen_procedure_constraint_set,
    evaluate_citizen_procedure_constraints,
)
from causa.institutional.contracts.citizen_procedure_evaluation import (
    SYNTHETIC_CITIZEN_PROCEDURE_BENCHMARKS,
    run_citizen_procedure_benchmark_suite,
    run_citizen_procedure_red_team_suite,
)
from causa.institutional.contracts.fact_consistency import FactConsistencyError
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_citizen_procedure import (
    build_synthetic_citizen_procedure_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def _facts(**updates: bool) -> CitizenProcedureFactSet:
    values = {name: False for name in CitizenProcedureFactSet.model_fields}
    values["debtor_is_a_citizen_under_chapter_10"] = True
    values.update(updates)
    return CitizenProcedureFactSet(**values)


def _evaluate(facts: CitizenProcedureFactSet):
    return evaluate_citizen_procedure_constraints(CitizenProcedureConstraintSet(id="test"), facts)


CITIZEN_APPLICATION = {
    "application_by_the_citizen": True,
    "application_meets_articles_213_3_to_213_5": True,
}
CREDITOR_APPLICATION = {
    "application_by_creditor_or_authorised_body": True,
    "application_meets_articles_213_3_to_213_5": True,
    "creditor_claims_found_well_founded": True,
}
PRESUMED = {"citizen_stopped_payments_to_creditors": True}
PRESUMPTION_CIRCUMSTANCES = (
    "citizen_stopped_payments_to_creditors",
    "over_ten_percent_of_due_obligations_unpaid_for_over_a_month",
    "debt_exceeds_value_of_property",
    "enforcement_ended_for_lack_of_property",
)
PLAN_BARS = (
    "conviction_or_administrative_penalty_bars_plan",
    "declared_bankrupt_within_five_years",
    "restructuring_plan_approved_within_eight_years",
)


def _text(source_id: str) -> str:
    return get_synthetic_contract_source(source_id).text


# --- Текст, на котором стоит модель ------------------------------------------


def test_article_213_2_names_three_procedures_and_no_others() -> None:
    """Перечень процедур читается из источника, а не из памяти."""
    text = _text("synthetic-ru-127fz-213.2-citizen-bankruptcy-procedures-v1")

    for procedure in (
        "реструктуризация долгов гражданина",
        "реализация имущества гражданина",
        "мировое соглашение",
    ):
        assert procedure in text
    for corporate in (
        "наблюдение",
        "финансовое оздоровление",
        "внешнее управление",
        "конкурсное производство",
    ):
        assert corporate not in text


def test_the_citizens_insolvency_has_its_own_definition() -> None:
    """Неплатёжеспособность гражданина определяет пункт 3 статьи 213.6, а не статья 2."""
    text = _text("synthetic-ru-127fz-213.6-citizen-application-merits-v1")

    assert "Для целей настоящего параграфа под неплатежеспособностью гражданина понимается" in text


def test_article_213_6_checks_the_two_applications_against_different_articles() -> None:
    """Пункт 2: у кредитора — пункт 2 статьи 213.3 и статья 213.5, у гражданина — 213.4.

    На этой развилке стоит и прочтение института возбуждения дела: заявление
    гражданина проверяется без порога пункта 2 статьи 213.3.
    """
    paragraphs = _text("synthetic-ru-127fz-213.6-citizen-application-merits-v1").split("\n\n")
    creditor = next(p for p in paragraphs if "заявления конкурсного кредитора" in p)
    citizen = next(p for p in paragraphs if "заявления гражданина о признании его" in p)

    assert "пунктом 2 статьи 213.3 и статьей 213.5" in creditor
    assert "статьей 213.4" in citizen
    assert "213.3" not in citizen


# --- Неплатёжеспособность ----------------------------------------------------


@pytest.mark.parametrize("circumstance", PRESUMPTION_CIRCUMSTANCES)
def test_one_presumption_circumstance_is_enough(circumstance: str) -> None:
    evaluation = _evaluate(_facts(**CITIZEN_APPLICATION, **{circumstance: True}))

    assert evaluation.insolvency_presumed is True
    assert evaluation.insolvency_established is True
    assert evaluation.requires_human_citizen_procedure_assessment is False


@pytest.mark.parametrize(
    "route",
    [PRESUMED, {"inability_to_pay_in_full_shown_by_other_evidence": True}],
    ids=["презумпция", "иные доказательства"],
)
def test_expected_full_performance_closes_both_routes_to_insolvency(route: dict) -> None:
    """«Не может быть признан неплатёжеспособным» — без оговорки о способе доказывания."""
    evaluation = _evaluate(
        _facts(
            **CITIZEN_APPLICATION,
            **route,
            full_performance_expected_shortly_from_planned_receipts=True,
        )
    )

    assert evaluation.insolvency_established is False
    assert evaluation.application_well_founded is False
    assert evaluation.requires_human_citizen_procedure_assessment is True


def test_expected_full_performance_alone_raises_no_flag() -> None:
    """Без признаков неплатёжеспособности снимать нечего, и оценивать тоже."""
    evaluation = _evaluate(
        _facts(**CITIZEN_APPLICATION, full_performance_expected_shortly_from_planned_receipts=True)
    )

    assert evaluation.insolvency_established is False
    assert evaluation.requires_human_citizen_procedure_assessment is False


# --- Обоснованность ------------------------------------------------------------


def test_the_citizens_application_needs_no_creditor_conditions() -> None:
    evaluation = _evaluate(_facts(**CITIZEN_APPLICATION, **PRESUMED))

    assert evaluation.application_well_founded is True


@pytest.mark.parametrize(
    "missing",
    [
        {"creditor_claims_found_well_founded": False},
        {"creditor_claims_satisfied_by_hearing_date": True},
        {"dispute_about_the_right_for_action_proceedings": True},
        {"application_meets_articles_213_3_to_213_5": False},
    ],
    ids=["не признаны", "удовлетворены", "спор о праве", "статьи 213.3–213.5"],
)
def test_each_creditor_condition_is_necessary(missing: dict) -> None:
    evaluation = _evaluate(_facts(**{**CREDITOR_APPLICATION, **PRESUMED, **missing}))

    assert evaluation.application_well_founded is False
    assert evaluation.application_unfounded is True


def test_the_dispute_about_the_right_bars_only_an_unconfirmed_claim() -> None:
    disputed = dict(CREDITOR_APPLICATION, **PRESUMED)
    disputed["dispute_about_the_right_for_action_proceedings"] = True

    assert _evaluate(_facts(**disputed)).application_well_founded is False
    assert (
        _evaluate(
            _facts(**disputed, claim_confirmed_by_court_decision_in_force=True)
        ).application_well_founded
        is True
    )


@pytest.mark.parametrize(
    "facts",
    [
        CITIZEN_APPLICATION,
        {"application_by_the_citizen": True, **PRESUMED},
        {**CREDITOR_APPLICATION, "creditor_claims_satisfied_by_hearing_date": True},
    ],
    ids=["нет неплатёжеспособности", "нет статьи 213.4", "требования удовлетворены"],
)
@pytest.mark.parametrize("another", [False, True], ids=["одно заявление", "есть иное"])
def test_an_unfounded_application_gets_exactly_one_determination(
    facts: dict, another: bool
) -> None:
    """Пункт 1 закрывает перечень, и выбор между двумя решает только иное заявление."""
    evaluation = _evaluate(
        _facts(**facts, another_application_to_declare_the_citizen_bankrupt_pending=another)
    )

    assert evaluation.application_unfounded is True
    assert evaluation.application_left_without_consideration is another
    assert evaluation.bankruptcy_proceedings_terminated is (not another)
    assert evaluation.debt_restructuring_introduced is False


# --- Процедура -----------------------------------------------------------------


@pytest.mark.parametrize(("petition", "meets"), list(itertools.product([False, True], repeat=2)))
def test_immediate_realisation_needs_both_the_petition_and_non_compliance(
    petition: bool, meets: bool
) -> None:
    evaluation = _evaluate(
        _facts(
            **CITIZEN_APPLICATION,
            **PRESUMED,
            citizen_has_source_of_income=meets,
            citizen_petitions_for_immediate_realisation=petition,
        )
    )

    assert evaluation.citizen_meets_restructuring_plan_requirements is meets
    open_path = petition and not meets
    assert evaluation.realisation_may_be_introduced_without_restructuring is open_path
    assert evaluation.debt_restructuring_introduced is (not open_path)
    assert evaluation.requires_human_citizen_procedure_assessment is open_path


@pytest.mark.parametrize("bar", PLAN_BARS)
def test_each_plan_requirement_is_necessary(bar: str) -> None:
    evaluation = _evaluate(
        _facts(**CITIZEN_APPLICATION, **PRESUMED, citizen_has_source_of_income=True, **{bar: True})
    )

    assert evaluation.citizen_meets_restructuring_plan_requirements is False


def test_lack_of_property_changes_no_conclusion() -> None:
    """Абзац 2020 года: отсутствие имущества не препятствует реализации.

    Признак переключается на каждом наборе benchmark, где подано заявление, и
    меняться вправе только вывод, который его называет.
    """
    named = {"lack_of_property_disregarded", "reasons_ru", "constraint_set_id"}
    checked = 0
    for task in SYNTHETIC_CITIZEN_PROCEDURE_BENCHMARKS:
        facts = task.facts
        if not (
            facts.application_by_the_citizen or facts.application_by_creditor_or_authorised_body
        ):
            continue
        without = _evaluate(
            facts.model_copy(update={"no_property_left_for_creditors_after_procedure_costs": False})
        ).model_dump(exclude=named)
        with_ = _evaluate(
            facts.model_copy(update={"no_property_left_for_creditors_after_procedure_costs": True})
        ).model_dump(exclude=named)
        assert without == with_, task.id
        checked += 1
    assert checked >= 15


def test_the_guardianship_authority_joins_only_a_well_founded_application() -> None:
    minor = {"rights_of_minor_or_incapacitated_person_affected": True}

    assert _evaluate(
        _facts(**CITIZEN_APPLICATION, **PRESUMED, **minor)
    ).guardianship_authority_joins_the_case
    assert not _evaluate(
        _facts(**CITIZEN_APPLICATION, **minor)
    ).guardianship_authority_joins_the_case


# --- Контракт фактов -----------------------------------------------------------


def test_one_review_checks_one_application() -> None:
    with pytest.raises(ValueError, match="одно заявление"):
        _facts(application_by_the_citizen=True, application_by_creditor_or_authorised_body=True)


@pytest.mark.parametrize(
    "fact",
    [
        "creditor_claims_found_well_founded",
        "creditor_claims_found_unfounded",
        "creditor_claims_satisfied_by_hearing_date",
        "claim_confirmed_by_court_decision_in_force",
        "dispute_about_the_right_for_action_proceedings",
    ],
)
def test_creditor_conditions_presuppose_a_creditors_application(fact: str) -> None:
    with pytest.raises(ValueError, match="заявление подал не кредитор"):
        _facts(application_by_the_citizen=True, **{fact: True})


def test_a_claim_is_not_both_well_founded_and_unfounded() -> None:
    with pytest.raises(ValueError, match="одновременно обоснованным"):
        _facts(
            application_by_creditor_or_authorised_body=True,
            creditor_claims_found_well_founded=True,
            creditor_claims_found_unfounded=True,
        )


def test_a_rebuttal_presupposes_a_presumption() -> None:
    with pytest.raises(ValueError, match="опровергать нечего"):
        _facts(**CITIZEN_APPLICATION, insolvency_presumption_rebutted=True)


def test_a_rebuttal_excludes_proof_of_inability() -> None:
    with pytest.raises(ValueError, match="опровергнута"):
        _facts(
            **CITIZEN_APPLICATION,
            **PRESUMED,
            insolvency_presumption_rebutted=True,
            inability_to_pay_in_full_shown_by_other_evidence=True,
        )


def test_the_petition_presupposes_an_application() -> None:
    with pytest.raises(ValueError, match="без заявления"):
        _facts(citizen_petitions_for_immediate_realisation=True)


# --- Ворота и пустые факты -------------------------------------------------------


def test_outside_chapter_10_the_institute_is_silent() -> None:
    evaluation = _evaluate(
        _facts(debtor_is_a_citizen_under_chapter_10=False, **CITIZEN_APPLICATION, **PRESUMED)
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
    assert evaluation.requires_human_citizen_procedure_assessment is False
    assert evaluation.reasons_ru == []


# --- Наборы, артефакт, конвейер ----------------------------------------------------


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_citizen_procedure_benchmark_suite()
    red_team = run_citizen_procedure_red_team_suite()

    assert benchmark.failed == 0, [r.task_id for r in benchmark.results if not r.passed]
    assert benchmark.total >= 20
    assert red_team.unblocked == 0, [r.case_id for r in red_team.results if not r.blocked]
    assert red_team.total >= 16


def test_the_synthetic_artifact_replays_from_reviewed_evidence() -> None:
    artifact = build_synthetic_citizen_procedure_evaluation_artifact()

    assert artifact.reviewed_evaluation.satisfiable is True
    assert artifact.reviewed_evaluation.application_unfounded is False
    assert artifact.reviewed_evaluation.requires_human_citizen_procedure_assessment is False
    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0


def test_the_constraint_set_declares_what_it_executes() -> None:
    mapping = CitizenProcedureEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=_facts(**CITIZEN_APPLICATION, **PRESUMED),
        legal_source_refs=["test-law"],
    )
    expressions = build_citizen_procedure_constraint_set(mapping).expressions

    assert len(expressions) == 12
    assert any(
        line.startswith("realisation_may_be_introduced_without_restructuring ==")
        for line in expressions
    )


def test_the_procedure_block_cannot_describe_another_application() -> None:
    """Подлог: блок процедур говорит о заявлении, которого блок возбуждения не знает."""
    request = build_synthetic_supply_analysis_request()
    forged = request.model_copy(
        update={
            "citizen_procedure_evidence": _flip(
                request.citizen_procedure_evidence,
                {
                    "application_by_the_citizen": True,
                    "application_meets_articles_213_3_to_213_5": True,
                },
            )
        }
    )

    with pytest.raises(FactConsistencyError) as failure:
        run_reviewed_contract_analysis(forged, build_synthetic_supply_analysis_sources())

    assert "citizen_procedure_applicant_is_the_citizen" in failure.value.keys
    assert "citizen_procedure_application_requirements" in failure.value.keys
