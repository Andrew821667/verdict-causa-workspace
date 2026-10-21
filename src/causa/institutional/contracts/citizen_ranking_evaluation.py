"""Бенчмарк и red-team для модели очерёдности требований кредиторов гражданина.

Бенчмарк проверяет, что модель ставит требование в ту очередь, которую называет
статья 213.27; red-team — что она не ставит его в чужую. Red-team здесь особенно
нагружен сравнением с очерёдностью конкурсного производства: институт появился
потому, что правила статьи 134 применялись к гражданину и давали неверный
ответ, и ни одно из трёх измеренных расхождений не должно вернуться.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.citizen_ranking import (
    CITIZEN_RANKING_LEGAL_SOURCE_REFS,
    CitizenRankingConstraintSet,
    CitizenRankingEvaluation,
    CitizenRankingEvidenceMappingResult,
    CitizenRankingFactSet,
    build_citizen_ranking_constraint_set,
    evaluate_citizen_ranking_constraints,
)


class CitizenRankingEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: CitizenRankingFactSet
    expected_outcomes: dict[str, bool]


class CitizenRankingEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CitizenRankingBenchmarkReport(BaseModel):
    id: str = "citizen-ranking-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[CitizenRankingEvaluationResult] = Field(default_factory=list)


class CitizenRankingRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: CitizenRankingFactSet
    forbidden_outcomes: dict[str, bool]


class CitizenRankingRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CitizenRankingRedTeamReport(BaseModel):
    id: str = "citizen-ranking-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[CitizenRankingRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> CitizenRankingFactSet:
    """Факты по требованию в деле о банкротстве гражданина.

    `debtor_is_a_citizen_under_chapter_10` по умолчанию истинно: все случаи
    ниже, кроме прямо проверяющих сами ворота, разбирают требование в деле
    гражданина. Остальное ложно.
    """
    values = {field_name: False for field_name in CitizenRankingFactSet.model_fields}
    values["debtor_is_a_citizen_under_chapter_10"] = True
    values.update(updates)
    return CitizenRankingFactSet(**values)


def _registry(**updates: bool) -> CitizenRankingFactSet:
    return _facts(claim_filed_in_bankruptcy_register=True, **updates)


def _current(**updates: bool) -> CitizenRankingFactSet:
    return _facts(is_current_payment_claim=True, **updates)


SYNTHETIC_CITIZEN_RANKING_BENCHMARKS = (
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-registry-maintenance-is-first",
        title_ru="Алименты — первая очередь реестра (пункт 3)",
        facts=_registry(is_maintenance_claim=True),
        expected_outcomes={
            "registry_first_tier": True,
            "registry_second_tier": False,
            "registry_third_tier": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-registry-harm-is-first",
        title_ru="Вред жизни или здоровью — первая очередь реестра (пункт 3)",
        facts=_registry(is_life_or_health_harm_claim=True),
        expected_outcomes={
            "registry_first_tier": True,
            "capitalisation_not_performed": True,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-registry-labour-is-second",
        title_ru="Выходные пособия и оплата труда — вторая очередь реестра (пункт 3)",
        facts=_registry(is_labour_or_severance_claim=True),
        expected_outcomes={
            "registry_second_tier": True,
            "registry_first_tier": False,
            "registry_third_tier": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-registry-other-is-third",
        title_ru="Другие кредиторы — третья очередь реестра (пункт 3)",
        facts=_registry(),
        expected_outcomes={
            "registry_third_tier": True,
            "registry_first_tier": False,
            "registry_second_tier": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-current-payments-go-ahead-of-registry",
        title_ru="Текущие платежи погашаются вне очереди (пункт 1)",
        facts=_current(),
        expected_outcomes={
            "current_payments_paid_ahead_of_registry_claims": True,
            "registry_third_tier": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-current-maintenance-is-first",
        title_ru="Алименты среди текущих — первая очередь (пункт 2)",
        facts=_current(is_maintenance_claim=True),
        expected_outcomes={
            "current_payment_first_tier": True,
            "current_payment_fourth_tier": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-current-proceeding-cost-is-first",
        title_ru="Судебные расходы и вознаграждение управляющего — первая очередь текущих",
        facts=_current(is_proceeding_cost_or_manager_fee=True),
        expected_outcomes={"current_payment_first_tier": True},
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-current-labour-is-second",
        title_ru="Оплата труда среди текущих — вторая очередь (пункт 2)",
        facts=_current(is_labour_or_severance_claim=True),
        expected_outcomes={
            "current_payment_second_tier": True,
            "current_payment_first_tier": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-current-housing-is-third",
        title_ru="Плата за жильё и ЖКУ — третья очередь текущих (пункт 2)",
        facts=_current(is_housing_or_utility_payment=True),
        expected_outcomes={
            "current_payment_third_tier": True,
            "current_payment_fourth_tier": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-current-other-is-fourth",
        title_ru="Иные текущие платежи — четвёртая очередь (пункт 2)",
        facts=_current(),
        expected_outcomes={
            "current_payment_fourth_tier": True,
            "current_payment_first_tier": False,
            "current_payment_second_tier": False,
            "current_payment_third_tier": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-pledge-takes-eighty-percent",
        title_ru="Залоговому кредитору — восемьдесят процентов выручки (пункт 5)",
        facts=_registry(is_secured_by_pledge=True),
        expected_outcomes={
            "secured_claim_takes_eighty_percent_of_pledge_proceeds": True,
            "registry_third_tier": False,
            "requires_human_citizen_ranking_assessment": True,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-pledge-remainder-reserved",
        title_ru="Десять процентов резервируются при недостаточности иного имущества",
        facts=_registry(
            is_secured_by_pledge=True,
            other_property_insufficient_for_first_and_second_tiers=True,
        ),
        expected_outcomes={"pledge_remainder_reserved_for_first_and_second_tiers": True},
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-pledge-shortfall-joins-the-third-tier",
        title_ru="Непогашенная часть залогового требования идёт в третью очередь (пункт 5)",
        facts=_registry(
            is_secured_by_pledge=True,
            pledge_proceeds_insufficient_for_the_secured_claim=True,
        ),
        expected_outcomes={
            "unsecured_remainder_of_the_pledge_claim_joins_the_third_tier": True,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-unsatisfied-claim-is-discharged",
        title_ru="Требование, не удовлетворённое за недостаточностью имущества, погашено",
        facts=_registry(claim_unsatisfied_for_want_of_property=True),
        expected_outcomes={
            "claim_deemed_discharged_for_want_of_property": True,
            "discharge_withheld_by_statutory_exception": False,
            "requires_human_citizen_ranking_assessment": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-statutory-exception-withholds-discharge",
        title_ru="Случай, предусмотренный законом, погашения не допускает (пункт 6)",
        facts=_registry(
            claim_unsatisfied_for_want_of_property=True,
            statutory_exception_to_discharge_applies=True,
        ),
        expected_outcomes={
            "claim_deemed_discharged_for_want_of_property": False,
            "discharge_withheld_by_statutory_exception": True,
            # Флага нет с выпуска 1.27.0: изъятие выводит институт статьи 213.28,
            # и признак сверяется с его выводом.
            "requires_human_citizen_ranking_assessment": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-entity-debtor-is-silent",
        title_ru="Должник не гражданин — институт молчит, отвечает статья 134",
        facts=_facts(
            debtor_is_a_citizen_under_chapter_10=False,
            claim_filed_in_bankruptcy_register=True,
            is_maintenance_claim=True,
        ),
        expected_outcomes={
            "registry_first_tier": False,
            "registry_third_tier": False,
            "requires_human_citizen_ranking_assessment": False,
        },
    ),
    CitizenRankingEvaluationTask(
        id="citizen-ranking-bench-empty-facts-say-nothing",
        title_ru="Пустой набор фактов не даёт ни одного вывода",
        facts=_facts(debtor_is_a_citizen_under_chapter_10=False),
        expected_outcomes={
            "current_payments_paid_ahead_of_registry_claims": False,
            "current_payment_first_tier": False,
            "current_payment_fourth_tier": False,
            "registry_first_tier": False,
            "registry_third_tier": False,
            "capitalisation_not_performed": False,
            "secured_claim_takes_eighty_percent_of_pledge_proceeds": False,
            "claim_deemed_discharged_for_want_of_property": False,
            "requires_human_citizen_ranking_assessment": False,
        },
    ),
)


SYNTHETIC_CITIZEN_RANKING_RED_TEAM_CASES = (
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-maintenance-as-third-tier",
        title_ru="Понизить алименты до третьей очереди, как это делала статья 134",
        facts=_registry(is_maintenance_claim=True),
        forbidden_outcomes={"registry_third_tier": True, "registry_first_tier": False},
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-housing-as-fourth-current-tier",
        title_ru="Понизить плату за ЖКУ до четвёртой очереди текущих, как в статье 134",
        facts=_current(is_housing_or_utility_payment=True),
        forbidden_outcomes={
            "current_payment_fourth_tier": True,
            "current_payment_third_tier": False,
        },
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-capitalisation-performed-for-a-citizen",
        title_ru="Применить капитализацию повременных платежей статьи 135 к гражданину",
        facts=_registry(is_life_or_health_harm_claim=True),
        forbidden_outcomes={"capitalisation_not_performed": False},
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-five-current-tiers",
        title_ru="Дать текущему платежу пятую очередь, которой у статьи 213.27 нет",
        facts=_current(),
        forbidden_outcomes={
            "current_payment_first_tier": True,
            "current_payment_second_tier": True,
            "current_payment_third_tier": True,
        },
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-registry-tier-for-a-current-payment",
        title_ru="Дать текущему платежу реестровую очередь",
        facts=_current(is_maintenance_claim=True),
        forbidden_outcomes={"registry_first_tier": True, "registry_third_tier": True},
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-current-tier-for-a-registry-claim",
        title_ru="Дать реестровому требованию очередь текущих платежей",
        facts=_registry(is_maintenance_claim=True),
        forbidden_outcomes={
            "current_payment_first_tier": True,
            "current_payment_fourth_tier": True,
            "current_payments_paid_ahead_of_registry_claims": True,
        },
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-pledge-claim-in-the-residual-third-tier",
        title_ru="Отнести залоговое требование к остаточной третьей очереди",
        facts=_registry(is_secured_by_pledge=True),
        forbidden_outcomes={"registry_third_tier": True},
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-pledge-keeps-priority-over-the-shortfall",
        title_ru="Сохранить залоговый приоритет за непогашенной частью требования",
        facts=_registry(
            is_secured_by_pledge=True,
            pledge_proceeds_insufficient_for_the_secured_claim=True,
        ),
        forbidden_outcomes={"unsecured_remainder_of_the_pledge_claim_joins_the_third_tier": False},
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-reserve-without-the-condition",
        title_ru="Зарезервировать десять процентов без недостаточности иного имущества",
        facts=_registry(is_secured_by_pledge=True),
        forbidden_outcomes={"pledge_remainder_reserved_for_first_and_second_tiers": True},
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-discharge-despite-the-exception",
        title_ru="Погасить требование, несмотря на заявленное исключение",
        facts=_registry(
            claim_unsatisfied_for_want_of_property=True,
            statutory_exception_to_discharge_applies=True,
        ),
        # Прежняя редакция требовала ещё и флага юриста. Он был правомерен, пока
        # статья 213.28 не была смоделирована; теперь изъятие выводит её институт.
        forbidden_outcomes={"claim_deemed_discharged_for_want_of_property": True},
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-discharge-without-insufficiency",
        title_ru="Погасить требование, не названное неудовлетворённым",
        facts=_registry(),
        forbidden_outcomes={"claim_deemed_discharged_for_want_of_property": True},
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-tier-without-a-claim",
        title_ru="Определить очередь требованию, ни реестровым, ни текущим не названному",
        facts=_facts(),
        forbidden_outcomes={
            "registry_third_tier": True,
            "current_payment_fourth_tier": True,
        },
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-entity-debtor-gets-citizen-tiers",
        title_ru="Применить очерёдность гражданина к должнику-организации",
        facts=_facts(
            debtor_is_a_citizen_under_chapter_10=False,
            claim_filed_in_bankruptcy_register=True,
            is_maintenance_claim=True,
        ),
        forbidden_outcomes={"registry_first_tier": True},
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-pledge-distribution-is-not-silent",
        title_ru="Назвать долю залогового кредитора, не подняв флага о распределении",
        facts=_registry(is_secured_by_pledge=True),
        forbidden_outcomes={"requires_human_citizen_ranking_assessment": False},
    ),
    CitizenRankingRedTeamCase(
        id="citizen-ranking-red-empty-facts-raise-no-flag",
        title_ru="Пустой набор фактов флага юриста не поднимает",
        facts=_facts(debtor_is_a_citizen_under_chapter_10=False),
        forbidden_outcomes={"requires_human_citizen_ranking_assessment": True},
    ),
)


def _evaluate(facts: CitizenRankingFactSet, artifact_id: str) -> CitizenRankingEvaluation:
    mapping = CitizenRankingEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(CITIZEN_RANKING_LEGAL_SOURCE_REFS),
    )
    constraints: CitizenRankingConstraintSet = build_citizen_ranking_constraint_set(mapping)
    return evaluate_citizen_ranking_constraints(constraints, facts)


def _outcomes(evaluation: CitizenRankingEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_citizen_ranking_benchmark_suite() -> CitizenRankingBenchmarkReport:
    results = []
    for task in SYNTHETIC_CITIZEN_RANKING_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            CitizenRankingEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return CitizenRankingBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_citizen_ranking_red_team_suite() -> CitizenRankingRedTeamReport:
    results = []
    for case in SYNTHETIC_CITIZEN_RANKING_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        results.append(
            CitizenRankingRedTeamResult(
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
    return CitizenRankingRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
