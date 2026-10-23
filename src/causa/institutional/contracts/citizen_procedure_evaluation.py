"""Бенчмарк и red-team для модели обоснованности заявления и процедуры банкротства гражданина.

Red-team нагружен тремя ловушками. Первая — «реализация по желанию»: сразу
ввести реализацию имущества пункт 8 статьи 213.6 позволяет только по
ходатайству гражданина, который не соответствует требованиям к плану
реструктуризации, — не по ходатайству кредитора, не при одном отсутствии
дохода и не гражданину, который требованиям соответствует. Вторая — «условия
кредитора для всех»: признание требований обоснованными и их неудовлетворение
пункт 2 ставит заявлению кредитора, а не заявлению самого гражданина. Третья —
«презумпция как приговор»: неплатёжеспособность предполагается, пока не
доказано иное, и не может быть признана при достаточных основаниях ожидать
скорого исполнения. Отдельный случай закрывает старую ошибку практики —
прекращение дела из-за отсутствия у гражданина имущества.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.citizen_procedure import (
    CITIZEN_PROCEDURE_LEGAL_SOURCE_REFS,
    CitizenProcedureConstraintSet,
    CitizenProcedureEvaluation,
    CitizenProcedureEvidenceMappingResult,
    CitizenProcedureFactSet,
    build_citizen_procedure_constraint_set,
    evaluate_citizen_procedure_constraints,
)


class CitizenProcedureEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: CitizenProcedureFactSet
    expected_outcomes: dict[str, bool]


class CitizenProcedureEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CitizenProcedureBenchmarkReport(BaseModel):
    id: str = "citizen-procedure-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[CitizenProcedureEvaluationResult] = Field(default_factory=list)


class CitizenProcedureRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: CitizenProcedureFactSet
    forbidden_outcomes: dict[str, bool]


class CitizenProcedureRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CitizenProcedureRedTeamReport(BaseModel):
    id: str = "citizen-procedure-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[CitizenProcedureRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> CitizenProcedureFactSet:
    """Факты о проверке обоснованности заявления о признании гражданина банкротом.

    `debtor_is_a_citizen_under_chapter_10` по умолчанию истинно: все случаи
    ниже, кроме прямо проверяющих сами ворота, разбирают заявление в режиме
    главы X. Остальное ложно.
    """
    values = {field_name: False for field_name in CitizenProcedureFactSet.model_fields}
    values["debtor_is_a_citizen_under_chapter_10"] = True
    values.update(updates)
    return CitizenProcedureFactSet(**values)


#: Заявление самого гражданина, соответствующее статье 213.4.
_CITIZEN_APPLICATION = dict(
    application_by_the_citizen=True,
    application_meets_articles_213_3_to_213_5=True,
)

#: Заявление кредитора, соответствующее пункту 2 статьи 213.3 и статье 213.5, с
#: требованиями, признанными обоснованными.
_CREDITOR_APPLICATION = dict(
    application_by_creditor_or_authorised_body=True,
    application_meets_articles_213_3_to_213_5=True,
    creditor_claims_found_well_founded=True,
)

#: Одно обстоятельство презумпции пункта 3 статьи 213.6: прекращение расчётов.
_PRESUMED = dict(citizen_stopped_payments_to_creditors=True)


SYNTHETIC_CITIZEN_PROCEDURE_BENCHMARKS = (
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-citizen-application-restructuring",
        title_ru="Заявление гражданина с доходом и прекращёнными расчётами — реструктуризация",
        facts=_facts(**_CITIZEN_APPLICATION, **_PRESUMED, citizen_has_source_of_income=True),
        expected_outcomes={
            "insolvency_presumed": True,
            "insolvency_established": True,
            "application_well_founded": True,
            "citizen_meets_restructuring_plan_requirements": True,
            "debt_restructuring_introduced": True,
            "realisation_may_be_introduced_without_restructuring": False,
            "requires_human_citizen_procedure_assessment": False,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-creditor-application-restructuring",
        title_ru="Заявление кредитора с решением суда, задолженность выше имущества — реструктуризация",
        facts=_facts(
            **_CREDITOR_APPLICATION,
            claim_confirmed_by_court_decision_in_force=True,
            debt_exceeds_value_of_property=True,
        ),
        expected_outcomes={
            "application_well_founded": True,
            "debt_restructuring_introduced": True,
            "application_unfounded": False,
            "requires_human_citizen_procedure_assessment": False,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-claims-satisfied-proceedings-terminated",
        title_ru="Требования удовлетворены к заседанию, иных заявлений нет — прекращение",
        facts=_facts(
            **_CREDITOR_APPLICATION, **_PRESUMED, creditor_claims_satisfied_by_hearing_date=True
        ),
        expected_outcomes={
            "application_well_founded": False,
            "application_unfounded": True,
            "bankruptcy_proceedings_terminated": True,
            "application_left_without_consideration": False,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-claims-satisfied-another-application-pending",
        title_ru="Требования удовлетворены, но есть иное заявление — без рассмотрения",
        facts=_facts(
            **_CREDITOR_APPLICATION,
            **_PRESUMED,
            creditor_claims_satisfied_by_hearing_date=True,
            another_application_to_declare_the_citizen_bankrupt_pending=True,
        ),
        expected_outcomes={
            "application_unfounded": True,
            "application_left_without_consideration": True,
            "bankruptcy_proceedings_terminated": False,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-claims-found-unfounded",
        title_ru="Требования кредитора признаны необоснованными — заявление необоснованно",
        facts=_facts(
            application_by_creditor_or_authorised_body=True,
            application_meets_articles_213_3_to_213_5=True,
            creditor_claims_found_unfounded=True,
            **_PRESUMED,
        ),
        expected_outcomes={"application_well_founded": False, "application_unfounded": True},
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-listed-claim-with-dispute-about-the-right",
        title_ru="Требование из перечня без решения суда, гражданин спорит о праве",
        facts=_facts(
            **_CREDITOR_APPLICATION,
            **_PRESUMED,
            dispute_about_the_right_for_action_proceedings=True,
        ),
        expected_outcomes={"application_well_founded": False, "application_unfounded": True},
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-dispute-irrelevant-with-court-decision",
        title_ru="Спор о праве при требовании, подтверждённом решением суда, — не препятствие",
        facts=_facts(
            **_CREDITOR_APPLICATION,
            **_PRESUMED,
            claim_confirmed_by_court_decision_in_force=True,
            dispute_about_the_right_for_action_proceedings=True,
        ),
        expected_outcomes={"application_well_founded": True},
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-insolvency-not-proven",
        title_ru="Ни одного обстоятельства презумпции и иных доказательств — необоснованно",
        facts=_facts(**_CITIZEN_APPLICATION),
        expected_outcomes={
            "insolvency_presumed": False,
            "insolvency_established": False,
            "application_unfounded": True,
            "bankruptcy_proceedings_terminated": True,
            "requires_human_citizen_procedure_assessment": False,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-presumption-rebutted",
        title_ru="Презумпция опровергнута — неплатёжеспособность не доказана, флаг юриста",
        facts=_facts(**_CITIZEN_APPLICATION, **_PRESUMED, insolvency_presumption_rebutted=True),
        expected_outcomes={
            "insolvency_presumed": True,
            "insolvency_established": False,
            "application_unfounded": True,
            "requires_human_citizen_procedure_assessment": True,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-insolvency-shown-by-other-evidence",
        title_ru="Неплатёжеспособность доказана иначе, чем презумпцией, — флаг юриста",
        facts=_facts(**_CITIZEN_APPLICATION, inability_to_pay_in_full_shown_by_other_evidence=True),
        expected_outcomes={
            "insolvency_presumed": False,
            "insolvency_established": True,
            "application_well_founded": True,
            "requires_human_citizen_procedure_assessment": True,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-full-performance-expected-shortly",
        title_ru="Скорое исполнение ожидается — не может быть признан неплатёжеспособным",
        facts=_facts(
            **_CITIZEN_APPLICATION,
            **_PRESUMED,
            full_performance_expected_shortly_from_planned_receipts=True,
        ),
        expected_outcomes={
            "insolvency_established": False,
            "application_unfounded": True,
            "requires_human_citizen_procedure_assessment": True,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-application-fails-requirements",
        title_ru="Заявление не соответствует статьям 213.3–213.5 — необоснованно",
        facts=_facts(application_by_the_citizen=True, **_PRESUMED),
        expected_outcomes={
            "insolvency_established": True,
            "application_well_founded": False,
            "application_unfounded": True,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-realisation-on-the-citizens-petition",
        title_ru="Без дохода и по ходатайству гражданина — суд вправе ввести реализацию",
        facts=_facts(
            **_CITIZEN_APPLICATION, **_PRESUMED, citizen_petitions_for_immediate_realisation=True
        ),
        expected_outcomes={
            "citizen_meets_restructuring_plan_requirements": False,
            "realisation_may_be_introduced_without_restructuring": True,
            "debt_restructuring_introduced": False,
            "requires_human_citizen_procedure_assessment": True,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-petition-of-a-citizen-meeting-the-requirements",
        title_ru="Ходатайство гражданина, соответствующего требованиям к плану, — реструктуризация",
        facts=_facts(
            **_CITIZEN_APPLICATION,
            **_PRESUMED,
            citizen_has_source_of_income=True,
            citizen_petitions_for_immediate_realisation=True,
        ),
        expected_outcomes={
            "citizen_meets_restructuring_plan_requirements": True,
            "realisation_may_be_introduced_without_restructuring": False,
            "debt_restructuring_introduced": True,
            "requires_human_citizen_procedure_assessment": False,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-no-income-without-petition",
        title_ru="Дохода нет, ходатайства нет — реструктуризация",
        facts=_facts(**_CITIZEN_APPLICATION, **_PRESUMED),
        expected_outcomes={
            "citizen_meets_restructuring_plan_requirements": False,
            "realisation_may_be_introduced_without_restructuring": False,
            "debt_restructuring_introduced": True,
            "requires_human_citizen_procedure_assessment": False,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-recent-bankruptcy-on-a-creditors-application",
        title_ru="Заявление кредитора, банкротство в пять лет и ходатайство гражданина",
        facts=_facts(
            **_CREDITOR_APPLICATION,
            **_PRESUMED,
            citizen_has_source_of_income=True,
            declared_bankrupt_within_five_years=True,
            citizen_petitions_for_immediate_realisation=True,
        ),
        expected_outcomes={
            "citizen_meets_restructuring_plan_requirements": False,
            "realisation_may_be_introduced_without_restructuring": True,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-guardianship-authority",
        title_ru="Затронуты права несовершеннолетнего — привлекается орган опеки",
        facts=_facts(
            **_CITIZEN_APPLICATION,
            **_PRESUMED,
            rights_of_minor_or_incapacitated_person_affected=True,
        ),
        expected_outcomes={"guardianship_authority_joins_the_case": True},
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-lack-of-property-disregarded",
        title_ru="Имущества для кредиторов нет — заявление всё равно обоснованно",
        facts=_facts(
            **_CITIZEN_APPLICATION,
            **_PRESUMED,
            no_property_left_for_creditors_after_procedure_costs=True,
        ),
        expected_outcomes={
            "lack_of_property_disregarded": True,
            "application_well_founded": True,
            "bankruptcy_proceedings_terminated": False,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-outside-chapter-10-is-silent",
        title_ru="Вне режима главы X институт молчит",
        facts=_facts(
            **_CITIZEN_APPLICATION, **_PRESUMED, debtor_is_a_citizen_under_chapter_10=False
        ),
        expected_outcomes={
            "insolvency_presumed": False,
            "application_well_founded": False,
            "application_unfounded": False,
            "bankruptcy_proceedings_terminated": False,
            "debt_restructuring_introduced": False,
            "requires_human_citizen_procedure_assessment": False,
        },
    ),
    CitizenProcedureEvaluationTask(
        id="citizen-procedure-bench-empty-facts-say-nothing",
        title_ru="Пустой набор фактов не даёт ни одного вывода",
        facts=_facts(debtor_is_a_citizen_under_chapter_10=False),
        expected_outcomes={
            "application_unfounded": False,
            "bankruptcy_proceedings_terminated": False,
            "citizen_meets_restructuring_plan_requirements": False,
            "lack_of_property_disregarded": False,
            "requires_human_citizen_procedure_assessment": False,
        },
    ),
)


SYNTHETIC_CITIZEN_PROCEDURE_RED_TEAM_CASES = (
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-realisation-on-a-creditors-request",
        title_ru="Ввести реализацию по заявлению кредитора без ходатайства гражданина",
        facts=_facts(**_CREDITOR_APPLICATION, **_PRESUMED),
        forbidden_outcomes={
            "realisation_may_be_introduced_without_restructuring": True,
            "debt_restructuring_introduced": False,
        },
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-realisation-for-a-citizen-meeting-the-requirements",
        title_ru="Ввести реализацию гражданину, который соответствует требованиям к плану",
        facts=_facts(
            **_CITIZEN_APPLICATION,
            **_PRESUMED,
            citizen_has_source_of_income=True,
            citizen_petitions_for_immediate_realisation=True,
        ),
        forbidden_outcomes={"realisation_may_be_introduced_without_restructuring": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-realisation-on-an-unfounded-application",
        title_ru="Ввести реализацию по ходатайству при необоснованном заявлении",
        facts=_facts(
            application_by_the_citizen=True, citizen_petitions_for_immediate_realisation=True
        ),
        forbidden_outcomes={"realisation_may_be_introduced_without_restructuring": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-terminate-for-lack-of-property",
        title_ru="Прекратить дело из-за отсутствия у гражданина имущества",
        facts=_facts(
            **_CITIZEN_APPLICATION,
            **_PRESUMED,
            no_property_left_for_creditors_after_procedure_costs=True,
        ),
        forbidden_outcomes={
            "bankruptcy_proceedings_terminated": True,
            "application_well_founded": False,
        },
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-presumption-as-conclusive",
        title_ru="Счесть презумпцию неопровержимой",
        facts=_facts(**_CITIZEN_APPLICATION, **_PRESUMED, insolvency_presumption_rebutted=True),
        forbidden_outcomes={"insolvency_established": True, "application_well_founded": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-expected-full-performance-ignored",
        title_ru="Признать неплатёжеспособным, несмотря на ожидаемое скорое исполнение",
        facts=_facts(
            **_CREDITOR_APPLICATION,
            claim_confirmed_by_court_decision_in_force=True,
            inability_to_pay_in_full_shown_by_other_evidence=True,
            full_performance_expected_shortly_from_planned_receipts=True,
        ),
        forbidden_outcomes={"insolvency_established": True, "application_well_founded": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-creditor-without-recognised-claims",
        title_ru="Признать обоснованным заявление кредитора, чьи требования не признаны",
        facts=_facts(
            application_by_creditor_or_authorised_body=True,
            application_meets_articles_213_3_to_213_5=True,
            **_PRESUMED,
        ),
        forbidden_outcomes={"application_well_founded": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-satisfied-claims-still-found",
        title_ru="Признать обоснованным заявление по требованиям, удовлетворённым к заседанию",
        facts=_facts(
            **_CREDITOR_APPLICATION, **_PRESUMED, creditor_claims_satisfied_by_hearing_date=True
        ),
        forbidden_outcomes={"application_well_founded": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-listed-claim-despite-dispute",
        title_ru="Признать обоснованным заявление по оспариваемому требованию без решения суда",
        facts=_facts(
            **_CREDITOR_APPLICATION,
            **_PRESUMED,
            dispute_about_the_right_for_action_proceedings=True,
        ),
        forbidden_outcomes={"application_well_founded": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-creditor-conditions-for-the-citizen",
        title_ru="Потребовать от заявления гражданина условий заявления кредитора",
        facts=_facts(**_CITIZEN_APPLICATION, **_PRESUMED),
        forbidden_outcomes={"application_well_founded": False, "application_unfounded": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-terminate-despite-another-application",
        title_ru="Прекратить производство, когда есть иное заявление",
        facts=_facts(
            **_CITIZEN_APPLICATION,
            another_application_to_declare_the_citizen_bankrupt_pending=True,
        ),
        forbidden_outcomes={
            "bankruptcy_proceedings_terminated": True,
            "application_left_without_consideration": False,
        },
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-leave-without-consideration-alone",
        title_ru="Оставить без рассмотрения единственное заявление",
        facts=_facts(**_CITIZEN_APPLICATION),
        forbidden_outcomes={
            "application_left_without_consideration": True,
            "bankruptcy_proceedings_terminated": False,
        },
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-procedure-on-an-unfounded-application",
        title_ru="Ввести реструктуризацию по необоснованному заявлению",
        facts=_facts(
            application_by_the_citizen=True, **_PRESUMED, citizen_has_source_of_income=True
        ),
        forbidden_outcomes={"debt_restructuring_introduced": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-plan-requirements-as-either",
        title_ru="Счесть требования к плану выполненными при одном доходе",
        facts=_facts(
            **_CITIZEN_APPLICATION,
            **_PRESUMED,
            citizen_has_source_of_income=True,
            restructuring_plan_approved_within_eight_years=True,
        ),
        forbidden_outcomes={"citizen_meets_restructuring_plan_requirements": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-presumption-raises-a-spurious-flag",
        title_ru="Поднять флаг юриста на неплатёжеспособности по неопровергнутой презумпции",
        facts=_facts(**_CITIZEN_APPLICATION, **_PRESUMED, citizen_has_source_of_income=True),
        forbidden_outcomes={"requires_human_citizen_procedure_assessment": True},
    ),
    CitizenProcedureRedTeamCase(
        id="citizen-procedure-red-empty-facts-raise-no-flag",
        title_ru="Пустой набор фактов флага юриста не поднимает",
        facts=_facts(debtor_is_a_citizen_under_chapter_10=False),
        forbidden_outcomes={"requires_human_citizen_procedure_assessment": True},
    ),
)


def _evaluate(facts: CitizenProcedureFactSet, artifact_id: str) -> CitizenProcedureEvaluation:
    mapping = CitizenProcedureEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(CITIZEN_PROCEDURE_LEGAL_SOURCE_REFS),
    )
    constraints: CitizenProcedureConstraintSet = build_citizen_procedure_constraint_set(mapping)
    return evaluate_citizen_procedure_constraints(constraints, facts)


def _outcomes(evaluation: CitizenProcedureEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_citizen_procedure_benchmark_suite() -> CitizenProcedureBenchmarkReport:
    results = []
    for task in SYNTHETIC_CITIZEN_PROCEDURE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            CitizenProcedureEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return CitizenProcedureBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_citizen_procedure_red_team_suite() -> CitizenProcedureRedTeamReport:
    results = []
    for case in SYNTHETIC_CITIZEN_PROCEDURE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        results.append(
            CitizenProcedureRedTeamResult(
                case_id=case.id,
                blocked=all(
                    observed[name] != forbidden
                    for name, forbidden in case.forbidden_outcomes.items()
                ),
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return CitizenProcedureRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
