"""Бенчмарк и red-team для модели банкротства гражданина.

Бенчмарк проверяет, что модель отвечает то, что говорит статья 25; red-team —
что она не отвечает того, чего статья не говорит. Опасность здесь двойная.
Ошибка в сторону банкротства переносит на гражданина последствия, которых закон
не предусмотрел. Ошибка в сторону режима хуже: она отдаёт дело не тому своду
правил, и тогда неверен уже не один вывод, а всё, что из него следует.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.citizen_bankruptcy import (
    CITIZEN_BANKRUPTCY_LEGAL_SOURCE_REFS,
    CitizenBankruptcyConstraintSet,
    CitizenBankruptcyEvaluation,
    CitizenBankruptcyEvidenceMappingResult,
    CitizenBankruptcyFactSet,
    build_citizen_bankruptcy_constraint_set,
    evaluate_citizen_bankruptcy_constraints,
)


class CitizenBankruptcyEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: CitizenBankruptcyFactSet
    expected_outcomes: dict[str, bool]


class CitizenBankruptcyEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CitizenBankruptcyBenchmarkReport(BaseModel):
    id: str = "citizen-bankruptcy-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[CitizenBankruptcyEvaluationResult] = Field(default_factory=list)


class CitizenBankruptcyRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: CitizenBankruptcyFactSet
    forbidden_outcomes: dict[str, bool]


class CitizenBankruptcyRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CitizenBankruptcyRedTeamReport(BaseModel):
    id: str = "citizen-bankruptcy-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[CitizenBankruptcyRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> CitizenBankruptcyFactSet:
    """Факты о банкротстве гражданина.

    По умолчанию всё ложно: должник гражданином не назван, неспособности нет,
    вопрос об очерёдности не поставлен. Каждый случай ниже включает ровно те
    признаки, о которых он говорит.
    """
    values = {field_name: False for field_name in CitizenBankruptcyFactSet.model_fields}
    values.update(updates)
    return CitizenBankruptcyFactSet(**values)


#: Условие пункта 1 выполнено по денежным обязательствам.
_INSOLVENT_CITIZEN = dict(
    debtor_is_a_citizen=True,
    unable_to_satisfy_monetary_obligations=True,
)

#: Тот же гражданин, признанный банкротом решением арбитражного суда.
_DECLARED_BANKRUPT = dict(_INSOLVENT_CITIZEN, arbitration_court_declared_bankrupt=True)


SYNTHETIC_CITIZEN_BANKRUPTCY_BENCHMARKS = (
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-monetary-inability",
        title_ru="Неспособность по денежным обязательствам — условие выполнено (пункт 1)",
        facts=_facts(**_INSOLVENT_CITIZEN),
        expected_outcomes={
            "citizen_may_be_declared_bankrupt": True,
            "insolvency_test_not_met": False,
            "citizen_declared_bankrupt": False,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-obligatory-payments-inability",
        title_ru="Неспособность по обязательным платежам достаточна сама по себе",
        facts=_facts(debtor_is_a_citizen=True, unable_to_pay_obligatory_payments=True),
        expected_outcomes={
            "citizen_may_be_declared_bankrupt": True,
            "insolvency_test_not_met": False,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-both-inabilities",
        title_ru="Обе неспособности вместе — тот же вывод, союз «и (или)»",
        facts=_facts(
            debtor_is_a_citizen=True,
            unable_to_satisfy_monetary_obligations=True,
            unable_to_pay_obligatory_payments=True,
        ),
        expected_outcomes={"citizen_may_be_declared_bankrupt": True},
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-test-not-met",
        title_ru="Гражданин в деле есть, неспособность не установлена (пункт 1)",
        facts=_facts(debtor_is_a_citizen=True),
        expected_outcomes={
            "citizen_may_be_declared_bankrupt": False,
            "insolvency_test_not_met": True,
            "requires_human_citizen_bankruptcy_assessment": False,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-declared-by-court",
        title_ru="Банкротом гражданина делает решение арбитражного суда (пункт 1)",
        facts=_facts(**_DECLARED_BANKRUPT),
        expected_outcomes={
            "citizen_declared_bankrupt": True,
            "bankruptcy_requires_a_court_decision": False,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-assertion-is-not-a-decision",
        title_ru="Заявление о несостоятельности решением суда не является (пункт 1)",
        facts=_facts(debtor_is_a_citizen=True, bankruptcy_asserted_without_a_court_decision=True),
        expected_outcomes={
            "citizen_declared_bankrupt": False,
            "bankruptcy_requires_a_court_decision": True,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-chapter-10-regime",
        title_ru="К банкротству гражданина применяется глава X закона (статья 213.1)",
        facts=_facts(**_DECLARED_BANKRUPT),
        expected_outcomes={
            "citizen_bankruptcy_regime_applies": True,
            "citizen_regime_excluded_for_peasant_farm": False,
            "requires_human_citizen_bankruptcy_assessment": False,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-entrepreneur-specifics",
        title_ru="Предприниматель: глава X с особенностями (пункт 3 статьи 213.1)",
        facts=_facts(**_DECLARED_BANKRUPT, debtor_is_an_individual_entrepreneur=True),
        expected_outcomes={
            "citizen_bankruptcy_regime_applies": True,
            "entrepreneur_specifics_apply": True,
            "requires_human_citizen_bankruptcy_assessment": True,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-peasant-farm-excluded",
        title_ru="Крестьянское хозяйство: глава X не применяется (пункт 2 статьи 213.1)",
        facts=_facts(**_DECLARED_BANKRUPT, debtor_is_a_peasant_farm_holding=True),
        expected_outcomes={
            "citizen_bankruptcy_regime_applies": False,
            "citizen_regime_excluded_for_peasant_farm": True,
            "requires_human_citizen_bankruptcy_assessment": True,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-entrepreneur-of-a-peasant-farm",
        title_ru="Предприниматель во главе крестьянского хозяйства: особенности не включаются",
        facts=_facts(
            **_DECLARED_BANKRUPT,
            debtor_is_an_individual_entrepreneur=True,
            debtor_is_a_peasant_farm_holding=True,
        ),
        expected_outcomes={
            "entrepreneur_specifics_apply": False,
            "citizen_regime_excluded_for_peasant_farm": True,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-ranking-governed-by-the-law",
        title_ru="Очерёдность требований гражданина устанавливает закон (пункт 2)",
        facts=_facts(**_DECLARED_BANKRUPT, creditor_ranking_question_raised=True),
        expected_outcomes={
            "creditor_ranking_governed_by_bankruptcy_law": True,
            "liquidation_ranking_wrongly_applied_to_a_citizen": False,
            # Флага нет с выпуска 1.26.0: очередь определяет институт статьи 213.27.
            "requires_human_citizen_bankruptcy_assessment": False,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-article-134-displaced",
        title_ru="Очерёдность статьи 134 к требованию гражданина не применяется",
        facts=_facts(
            **_DECLARED_BANKRUPT,
            creditor_ranking_question_raised=True,
            liquidation_ranking_of_article_134_applied=True,
        ),
        expected_outcomes={
            "liquidation_ranking_wrongly_applied_to_a_citizen": True,
            "creditor_ranking_governed_by_bankruptcy_law": True,
            "requires_human_citizen_bankruptcy_assessment": True,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-peasant-farm-keeps-article-134",
        title_ru="У крестьянского хозяйства очерёдность статьи 134 не вытесняется главой X",
        facts=_facts(
            **_DECLARED_BANKRUPT,
            debtor_is_a_peasant_farm_holding=True,
            creditor_ranking_question_raised=True,
            liquidation_ranking_of_article_134_applied=True,
        ),
        expected_outcomes={
            "liquidation_ranking_wrongly_applied_to_a_citizen": False,
            "creditor_ranking_governed_by_bankruptcy_law": False,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-entity-debtor-is-silent",
        title_ru="Должник не гражданин — институт молчит (статья 65 ГК РФ)",
        facts=_facts(creditor_ranking_question_raised=True),
        expected_outcomes={
            "citizen_may_be_declared_bankrupt": False,
            "insolvency_test_not_met": False,
            "citizen_bankruptcy_regime_applies": False,
            "creditor_ranking_governed_by_bankruptcy_law": False,
            "requires_human_citizen_bankruptcy_assessment": False,
        },
    ),
    CitizenBankruptcyEvaluationTask(
        id="citizen-bankruptcy-bench-empty-facts-say-nothing",
        title_ru="Пустой набор фактов не даёт ни одного вывода",
        facts=_facts(),
        expected_outcomes={
            "citizen_may_be_declared_bankrupt": False,
            "citizen_declared_bankrupt": False,
            "bankruptcy_requires_a_court_decision": False,
            "insolvency_test_not_met": False,
            "citizen_bankruptcy_regime_applies": False,
            "entrepreneur_specifics_apply": False,
            "citizen_regime_excluded_for_peasant_farm": False,
            "creditor_ranking_governed_by_bankruptcy_law": False,
            "liquidation_ranking_wrongly_applied_to_a_citizen": False,
            "requires_human_citizen_bankruptcy_assessment": False,
        },
    ),
)


SYNTHETIC_CITIZEN_BANKRUPTCY_RED_TEAM_CASES = (
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-inability-alone-is-not-bankruptcy",
        title_ru="Неспособность сама по себе банкротом не делает: «может быть признан»",
        facts=_facts(**_INSOLVENT_CITIZEN),
        forbidden_outcomes={"citizen_declared_bankrupt": True},
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-assertion-is-not-a-declaration",
        title_ru="Заявление о несостоятельности не признаёт банкротом",
        facts=_facts(
            debtor_is_a_citizen=True,
            unable_to_satisfy_monetary_obligations=True,
            bankruptcy_asserted_without_a_court_decision=True,
        ),
        forbidden_outcomes={
            "citizen_declared_bankrupt": True,
            "bankruptcy_requires_a_court_decision": False,
        },
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-entity-debtor-gets-nothing",
        title_ru="Должнику-организации выводы статьи 25 не достаются",
        facts=_facts(creditor_ranking_question_raised=True),
        forbidden_outcomes={
            "citizen_bankruptcy_regime_applies": True,
            "citizen_may_be_declared_bankrupt": True,
            "insolvency_test_not_met": True,
            "creditor_ranking_governed_by_bankruptcy_law": True,
        },
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-test-not-met-is-not-a-difficulty",
        title_ru="Невыполненное условие пункта 1 флага юриста не поднимает",
        facts=_facts(debtor_is_a_citizen=True),
        forbidden_outcomes={"requires_human_citizen_bankruptcy_assessment": True},
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-peasant-farm-is-not-chapter-10",
        title_ru="Крестьянское хозяйство под главу X не подводится",
        facts=_facts(**_DECLARED_BANKRUPT, debtor_is_a_peasant_farm_holding=True),
        forbidden_outcomes={
            "citizen_bankruptcy_regime_applies": True,
            "citizen_regime_excluded_for_peasant_farm": False,
        },
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-peasant-farm-blocks-entrepreneur-specifics",
        title_ru="Особенности предпринимателя у крестьянского хозяйства не включаются",
        facts=_facts(
            **_DECLARED_BANKRUPT,
            debtor_is_an_individual_entrepreneur=True,
            debtor_is_a_peasant_farm_holding=True,
        ),
        forbidden_outcomes={"entrepreneur_specifics_apply": True},
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-ranking-needs-the-question",
        title_ru="Вывод об очерёдности без поставленного вопроса не возникает",
        facts=_facts(**_DECLARED_BANKRUPT),
        forbidden_outcomes={
            "creditor_ranking_governed_by_bankruptcy_law": True,
            "liquidation_ranking_wrongly_applied_to_a_citizen": True,
        },
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-article-134-on-a-citizen-is-not-silent",
        title_ru="Очерёдность статьи 134 у гражданина без флага юриста не проходит",
        facts=_facts(
            **_DECLARED_BANKRUPT,
            creditor_ranking_question_raised=True,
            liquidation_ranking_of_article_134_applied=True,
        ),
        forbidden_outcomes={
            "requires_human_citizen_bankruptcy_assessment": False,
            "liquidation_ranking_wrongly_applied_to_a_citizen": False,
        },
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-ranking-question-is-not-a-misapplication",
        title_ru="Поставленный вопрос об очерёдности не выдаётся за неверно применённую",
        # Прежний случай требовал флага юриста, пока статья 213.27 не была
        # смоделирована. Теперь проверяется другое: названное правило — не
        # обвинение в том, что применено чужое.
        facts=_facts(**_DECLARED_BANKRUPT, creditor_ranking_question_raised=True),
        forbidden_outcomes={"liquidation_ranking_wrongly_applied_to_a_citizen": True},
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-entrepreneur-specifics-are-not-silent",
        title_ru="Особенности предпринимателя без флага юриста не проходят",
        facts=_facts(**_DECLARED_BANKRUPT, debtor_is_an_individual_entrepreneur=True),
        forbidden_outcomes={"requires_human_citizen_bankruptcy_assessment": False},
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-peasant-farm-is-not-silent",
        title_ru="Исключение крестьянского хозяйства без флага юриста не проходит",
        facts=_facts(**_DECLARED_BANKRUPT, debtor_is_a_peasant_farm_holding=True),
        forbidden_outcomes={"requires_human_citizen_bankruptcy_assessment": False},
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-declaration-does-not-imply-the-wrong-ranking",
        title_ru="Признание банкротом само по себе вывода об очерёдности не даёт",
        facts=_facts(**_DECLARED_BANKRUPT),
        forbidden_outcomes={
            "liquidation_ranking_wrongly_applied_to_a_citizen": True,
            "requires_human_citizen_bankruptcy_assessment": True,
        },
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-test-met-is-not-a-declaration",
        title_ru="Выполненное условие и состоявшееся признание не смешиваются",
        facts=_facts(debtor_is_a_citizen=True, unable_to_pay_obligatory_payments=True),
        forbidden_outcomes={
            "citizen_declared_bankrupt": True,
            "insolvency_test_not_met": True,
        },
    ),
    CitizenBankruptcyRedTeamCase(
        id="citizen-bankruptcy-red-empty-facts-raise-no-flag",
        title_ru="Пустой набор фактов флага юриста не поднимает",
        facts=_facts(),
        forbidden_outcomes={"requires_human_citizen_bankruptcy_assessment": True},
    ),
)


def _evaluate(facts: CitizenBankruptcyFactSet, artifact_id: str) -> CitizenBankruptcyEvaluation:
    mapping = CitizenBankruptcyEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(CITIZEN_BANKRUPTCY_LEGAL_SOURCE_REFS),
    )
    constraints: CitizenBankruptcyConstraintSet = build_citizen_bankruptcy_constraint_set(mapping)
    return evaluate_citizen_bankruptcy_constraints(constraints, facts)


def _outcomes(evaluation: CitizenBankruptcyEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_citizen_bankruptcy_benchmark_suite() -> CitizenBankruptcyBenchmarkReport:
    results = []
    for task in SYNTHETIC_CITIZEN_BANKRUPTCY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            CitizenBankruptcyEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return CitizenBankruptcyBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_citizen_bankruptcy_red_team_suite() -> CitizenBankruptcyRedTeamReport:
    results = []
    for case in SYNTHETIC_CITIZEN_BANKRUPTCY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        results.append(
            CitizenBankruptcyRedTeamResult(
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
    return CitizenBankruptcyRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
