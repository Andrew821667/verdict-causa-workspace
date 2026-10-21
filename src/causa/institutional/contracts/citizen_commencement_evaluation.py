"""Бенчмарк и red-team для модели возбуждения дела о банкротстве гражданина.

Red-team нагружен тремя ловушками чтения. Первая — «всякий кредитор вправе»:
статья 2 исключает из конкурсных кредиторов несколько категорий, и такой
кредитор права на заявление не имеет. Вторая — «порог для всех»: модель читает
основания статьи 213.4 как «иное» по отношению к порогу пункта 2 статьи 213.3,
но к заявлению кредитора порог применяется без изъятий. Третья — «уведомление
для всех»: требование об уведомлении предпринимателя адресовано не каждому
заявителю, и модель не расширяет текст.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.citizen_commencement import (
    CITIZEN_COMMENCEMENT_LEGAL_SOURCE_REFS,
    CitizenCommencementConstraintSet,
    CitizenCommencementEvaluation,
    CitizenCommencementEvidenceMappingResult,
    CitizenCommencementFactSet,
    build_citizen_commencement_constraint_set,
    evaluate_citizen_commencement_constraints,
)


class CitizenCommencementEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: CitizenCommencementFactSet
    expected_outcomes: dict[str, bool]


class CitizenCommencementEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CitizenCommencementBenchmarkReport(BaseModel):
    id: str = "citizen-commencement-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[CitizenCommencementEvaluationResult] = Field(default_factory=list)


class CitizenCommencementRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: CitizenCommencementFactSet
    forbidden_outcomes: dict[str, bool]


class CitizenCommencementRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CitizenCommencementRedTeamReport(BaseModel):
    id: str = "citizen-commencement-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[CitizenCommencementRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> CitizenCommencementFactSet:
    """Факты о заявлении о признании гражданина банкротом.

    `debtor_is_a_citizen_under_chapter_10` по умолчанию истинно: все случаи
    ниже, кроме прямо проверяющих сами ворота, разбирают заявление в режиме
    главы X. Остальное ложно.
    """
    values = {field_name: False for field_name in CitizenCommencementFactSet.model_fields}
    values["debtor_is_a_citizen_under_chapter_10"] = True
    values.update(updates)
    return CitizenCommencementFactSet(**values)


#: Порог пункта 2 статьи 213.3: пятьсот тысяч рублей и три месяца.
_THRESHOLD = dict(
    claims_against_the_citizen_at_least_500k=True,
    claims_unpaid_for_three_months_after_due=True,
)

#: Кредитор с вступившим в силу решением суда и выполненным порогом.
_CREDITOR_WITH_DECISION = dict(
    _THRESHOLD,
    applicant_is_a_monetary_creditor=True,
    claim_confirmed_by_court_decision_in_force=True,
)

#: Обязанность гражданина пункта 1 статьи 213.4, без трёх месяцев просрочки.
_DUTY = dict(
    applicant_is_the_citizen=True,
    claims_against_the_citizen_at_least_500k=True,
    paying_some_creditors_makes_full_performance_to_others_impossible=True,
)

#: Предвидение банкротства пункта 2 статьи 213.4.
_FORESEEN = dict(
    applicant_is_the_citizen=True,
    circumstances_obviously_show_inability_to_perform_on_time=True,
    signs_of_insolvency_or_insufficiency_of_property=True,
)


SYNTHETIC_CITIZEN_COMMENCEMENT_BENCHMARKS = (
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-creditor-with-court-decision",
        title_ru="Конкурсный кредитор с решением суда и порогом — заявление принимается",
        facts=_facts(**_CREDITOR_WITH_DECISION),
        expected_outcomes={
            "applicant_is_competitive_creditor_under_article_2": True,
            "applicant_has_standing": True,
            "creditor_claim_basis_sufficient": True,
            "creditors_application_admissible": True,
            "requires_human_citizen_commencement_assessment": False,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-bank-loan-without-decision",
        title_ru="Кредитный договор с банком — без решения суда (пункт 2 статьи 213.5)",
        facts=_facts(
            **_THRESHOLD,
            applicant_is_a_monetary_creditor=True,
            claim_listed_in_article_213_5_paragraph_2=True,
        ),
        expected_outcomes={
            "creditor_claim_basis_sufficient": True,
            "creditors_application_admissible": True,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-tax-authority-without-decision",
        title_ru="Уполномоченный орган по обязательным платежам — без решения суда",
        facts=_facts(
            **_THRESHOLD,
            applicant_is_authorised_body=True,
            claim_listed_in_article_213_5_paragraph_2=True,
        ),
        expected_outcomes={
            "applicant_has_standing": True,
            "creditors_application_admissible": True,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-creditor-without-any-basis",
        title_ru="Кредитор без решения суда и вне перечня — заявление не принимается",
        facts=_facts(**_THRESHOLD, applicant_is_a_monetary_creditor=True),
        expected_outcomes={
            "applicant_has_standing": True,
            "creditor_claim_basis_sufficient": False,
            "creditors_application_admissible": False,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-creditor-below-threshold",
        title_ru="Решение суда есть, но долг меньше пятисот тысяч — заявление не принимается",
        facts=_facts(
            applicant_is_a_monetary_creditor=True,
            claim_confirmed_by_court_decision_in_force=True,
            claims_unpaid_for_three_months_after_due=True,
        ),
        expected_outcomes={
            "statutory_threshold_met": False,
            "creditors_application_admissible": False,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-creditor-before-three-months",
        title_ru="Пятьсот тысяч есть, трёх месяцев просрочки нет — заявление не принимается",
        facts=_facts(
            applicant_is_a_monetary_creditor=True,
            claim_confirmed_by_court_decision_in_force=True,
            claims_against_the_citizen_at_least_500k=True,
        ),
        expected_outcomes={
            "statutory_threshold_met": False,
            "creditors_application_admissible": False,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-excluded-creditor-lacks-standing",
        title_ru="Кредитор по вреду жизни или здоровью не конкурсный — права нет (статья 2)",
        facts=_facts(
            **_CREDITOR_WITH_DECISION, creditor_claim_excluded_from_competitive_creditors=True
        ),
        expected_outcomes={
            "applicant_is_competitive_creditor_under_article_2": False,
            "applicant_lacks_standing": True,
            "creditors_application_admissible": False,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-another-person-lacks-standing",
        title_ru="Иное лицо права на заявление не имеет (пункт 1 статьи 213.3)",
        facts=_facts(**_THRESHOLD, applicant_is_another_person=True),
        expected_outcomes={
            "applicant_has_standing": False,
            "applicant_lacks_standing": True,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-citizen-with-threshold",
        title_ru="Гражданин при выполненном пороге — заявление принимается без флага",
        facts=_facts(**_THRESHOLD, applicant_is_the_citizen=True),
        expected_outcomes={
            "debtors_application_admissible": True,
            "threshold_displaced_for_the_debtors_own_application": False,
            "requires_human_citizen_commencement_assessment": False,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-debtor-duty",
        title_ru="Обязанность гражданина обратиться в суд (пункт 1 статьи 213.4)",
        facts=_facts(**_DUTY),
        expected_outcomes={
            "debtor_obliged_to_file": True,
            "debtors_application_admissible": True,
            "threshold_displaced_for_the_debtors_own_application": True,
            "requires_human_citizen_commencement_assessment": True,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-debtor-duty-breached",
        title_ru="Тридцать рабочих дней истекли — обязанность нарушена",
        facts=_facts(**_DUTY, duty_deadline_of_30_working_days_missed=True),
        expected_outcomes={
            "debtor_obliged_to_file": True,
            "debtor_duty_to_file_breached": True,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-foreseen-bankruptcy",
        title_ru="Предвидение банкротства — право гражданина (пункт 2 статьи 213.4)",
        facts=_facts(**_FORESEEN),
        expected_outcomes={
            "debtor_may_file_on_foreseen_bankruptcy": True,
            "debtors_application_admissible": True,
            "requires_human_citizen_commencement_assessment": True,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-citizen-without-any-ground",
        title_ru="Гражданин без порога и без оснований статьи 213.4 — не принимается",
        facts=_facts(applicant_is_the_citizen=True),
        expected_outcomes={
            "applicant_has_standing": True,
            "debtors_application_admissible": False,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-entrepreneur-without-notice",
        title_ru="Предприниматель без уведомления за пятнадцать дней — права ещё нет",
        facts=_facts(
            **_THRESHOLD, applicant_is_the_citizen=True, debtor_is_an_individual_entrepreneur=True
        ),
        expected_outcomes={
            "entrepreneur_notice_missing": True,
            "debtors_application_admissible": False,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-entrepreneur-with-notice",
        title_ru="Предприниматель с уведомлением — заявление принимается",
        facts=_facts(
            **_THRESHOLD,
            applicant_is_the_citizen=True,
            debtor_is_an_individual_entrepreneur=True,
            notice_of_intent_published_at_least_15_days_before=True,
        ),
        expected_outcomes={
            "entrepreneur_notice_missing": False,
            "debtors_application_admissible": True,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-entrepreneur-creditor-with-decision",
        title_ru="Кредитор предпринимателя с решением суда уведомления не публикует",
        facts=_facts(**_CREDITOR_WITH_DECISION, debtor_is_an_individual_entrepreneur=True),
        expected_outcomes={
            "entrepreneur_notice_missing": False,
            "creditors_application_admissible": True,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-outside-chapter-10-is-silent",
        title_ru="Вне режима главы X институт молчит",
        facts=_facts(debtor_is_a_citizen_under_chapter_10=False, **_CREDITOR_WITH_DECISION),
        expected_outcomes={
            "applicant_has_standing": False,
            "creditors_application_admissible": False,
            "requires_human_citizen_commencement_assessment": False,
        },
    ),
    CitizenCommencementEvaluationTask(
        id="citizen-commencement-bench-empty-facts-say-nothing",
        title_ru="Пустой набор фактов не даёт ни одного вывода",
        facts=_facts(debtor_is_a_citizen_under_chapter_10=False),
        expected_outcomes={
            "applicant_has_standing": False,
            "applicant_lacks_standing": False,
            "statutory_threshold_met": False,
            "debtor_obliged_to_file": False,
            "debtor_may_file_on_foreseen_bankruptcy": False,
            "debtors_application_admissible": False,
            "creditors_application_admissible": False,
            "requires_human_citizen_commencement_assessment": False,
        },
    ),
)


SYNTHETIC_CITIZEN_COMMENCEMENT_RED_TEAM_CASES = (
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-every-creditor-has-standing",
        title_ru="Признать конкурсным кредитора, исключённого статьёй 2",
        facts=_facts(
            **_CREDITOR_WITH_DECISION, creditor_claim_excluded_from_competitive_creditors=True
        ),
        forbidden_outcomes={
            "applicant_is_competitive_creditor_under_article_2": True,
            "applicant_has_standing": True,
            "creditors_application_admissible": True,
        },
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-another-person-files",
        title_ru="Принять заявление лица, которого пункт 1 статьи 213.3 не называет",
        facts=_facts(**_THRESHOLD, applicant_is_another_person=True),
        forbidden_outcomes={
            "applicant_has_standing": True,
            "creditors_application_admissible": True,
            "debtors_application_admissible": True,
        },
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-creditor-skips-the-threshold",
        title_ru="Распространить «иное» статьи 213.4 на заявление кредитора",
        facts=_facts(
            applicant_is_a_monetary_creditor=True,
            claim_confirmed_by_court_decision_in_force=True,
            circumstances_obviously_show_inability_to_perform_on_time=True,
            signs_of_insolvency_or_insufficiency_of_property=True,
        ),
        forbidden_outcomes={"creditors_application_admissible": True},
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-threshold-as-either-condition",
        title_ru="Прочитать «и» пункта 2 статьи 213.3 как «или»",
        facts=_facts(
            applicant_is_a_monetary_creditor=True,
            claim_confirmed_by_court_decision_in_force=True,
            claims_unpaid_for_three_months_after_due=True,
        ),
        forbidden_outcomes={"statutory_threshold_met": True},
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-creditor-without-basis",
        title_ru="Принять заявление кредитора без решения суда и вне перечня",
        facts=_facts(**_THRESHOLD, applicant_is_a_monetary_creditor=True),
        forbidden_outcomes={"creditors_application_admissible": True},
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-notice-for-every-applicant",
        title_ru="Потребовать уведомления от кредитора предпринимателя с решением суда",
        facts=_facts(**_CREDITOR_WITH_DECISION, debtor_is_an_individual_entrepreneur=True),
        forbidden_outcomes={
            "entrepreneur_notice_missing": True,
            "creditors_application_admissible": False,
        },
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-notice-for-the-authorised-body",
        title_ru="Потребовать уведомления от уполномоченного органа",
        facts=_facts(
            **_THRESHOLD,
            debtor_is_an_individual_entrepreneur=True,
            applicant_is_authorised_body=True,
            claim_listed_in_article_213_5_paragraph_2=True,
        ),
        forbidden_outcomes={"entrepreneur_notice_missing": True},
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-entrepreneur-skips-the-notice",
        title_ru="Принять заявление предпринимателя без уведомления",
        facts=_facts(
            **_THRESHOLD, applicant_is_the_citizen=True, debtor_is_an_individual_entrepreneur=True
        ),
        forbidden_outcomes={"debtors_application_admissible": True},
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-listed-creditor-of-entrepreneur-skips-notice",
        title_ru="Принять заявление кредитора предпринимателя по перечню без уведомления",
        facts=_facts(
            **_THRESHOLD,
            debtor_is_an_individual_entrepreneur=True,
            applicant_is_a_monetary_creditor=True,
            claim_listed_in_article_213_5_paragraph_2=True,
        ),
        forbidden_outcomes={"creditors_application_admissible": True},
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-displacement-is-not-silent",
        title_ru="Принять заявление гражданина без порога, не подняв флага юриста",
        facts=_facts(**_DUTY),
        forbidden_outcomes={"requires_human_citizen_commencement_assessment": False},
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-foreseen-bankruptcy-is-not-silent",
        title_ru="Признать «очевидность» неспособности исполнить без флага юриста",
        facts=_facts(**_FORESEEN, **_THRESHOLD),
        forbidden_outcomes={"requires_human_citizen_commencement_assessment": False},
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-duty-without-the-aggregate",
        title_ru="Вывести обязанность обратиться в суд без пятисот тысяч рублей",
        facts=_facts(
            applicant_is_the_citizen=True,
            paying_some_creditors_makes_full_performance_to_others_impossible=True,
        ),
        forbidden_outcomes={"debtor_obliged_to_file": True},
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-signs-without-obviousness",
        title_ru="Вывести право при предвидении банкротства из одних признаков",
        facts=_facts(
            applicant_is_the_citizen=True, signs_of_insolvency_or_insufficiency_of_property=True
        ),
        forbidden_outcomes={
            "debtor_may_file_on_foreseen_bankruptcy": True,
            "debtors_application_admissible": True,
        },
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-threshold-met-raises-a-spurious-flag",
        title_ru="Поднять флаг юриста на заявлении гражданина при выполненном пороге",
        facts=_facts(**_THRESHOLD, applicant_is_the_citizen=True),
        forbidden_outcomes={"requires_human_citizen_commencement_assessment": True},
    ),
    CitizenCommencementRedTeamCase(
        id="citizen-commencement-red-empty-facts-raise-no-flag",
        title_ru="Пустой набор фактов флага юриста не поднимает",
        facts=_facts(debtor_is_a_citizen_under_chapter_10=False),
        forbidden_outcomes={"requires_human_citizen_commencement_assessment": True},
    ),
)


def _evaluate(facts: CitizenCommencementFactSet, artifact_id: str) -> CitizenCommencementEvaluation:
    mapping = CitizenCommencementEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(CITIZEN_COMMENCEMENT_LEGAL_SOURCE_REFS),
    )
    constraints: CitizenCommencementConstraintSet = build_citizen_commencement_constraint_set(
        mapping
    )
    return evaluate_citizen_commencement_constraints(constraints, facts)


def _outcomes(evaluation: CitizenCommencementEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_citizen_commencement_benchmark_suite() -> CitizenCommencementBenchmarkReport:
    results = []
    for task in SYNTHETIC_CITIZEN_COMMENCEMENT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            CitizenCommencementEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return CitizenCommencementBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_citizen_commencement_red_team_suite() -> CitizenCommencementRedTeamReport:
    results = []
    for case in SYNTHETIC_CITIZEN_COMMENCEMENT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        results.append(
            CitizenCommencementRedTeamResult(
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
    return CitizenCommencementRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
