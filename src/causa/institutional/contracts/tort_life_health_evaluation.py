from pydantic import BaseModel, Field

from causa.institutional.contracts.tort_life_health import (
    TortLifeHealthConstraintSet,
    TortLifeHealthEvaluation,
    TortLifeHealthEvidenceMappingResult,
    TortLifeHealthFactSet,
    build_tort_life_health_constraint_set,
    evaluate_tort_life_health_constraints,
)


class TortLifeHealthEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: TortLifeHealthFactSet
    expected_outcomes: dict[str, bool]


class TortLifeHealthEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TortLifeHealthBenchmarkReport(BaseModel):
    id: str = "tort-life-health-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[TortLifeHealthEvaluationResult] = Field(default_factory=list)


class TortLifeHealthRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: TortLifeHealthFactSet
    forbidden_outcomes: dict[str, bool]


class TortLifeHealthRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TortLifeHealthRedTeamReport(BaseModel):
    id: str = "tort-life-health-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[TortLifeHealthRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> TortLifeHealthFactSet:
    values = {field_name: False for field_name in TortLifeHealthFactSet.model_fields}
    values.update(updates)
    return TortLifeHealthFactSet(**values)


SYNTHETIC_TORT_LIFE_HEALTH_BENCHMARKS = (
    TortLifeHealthEvaluationTask(
        id="tort-life-health-bench-not-qualified",
        title_ru="Причинение вреда жизни или здоровью гражданина не установлено",
        facts=_facts(funeral_expenses_rules_breached=True),
        expected_outcomes={"life_health_harm_qualified": False},
    ),
    TortLifeHealthEvaluationTask(
        id="tort-life-health-bench-qualified-clean",
        title_ru="Возмещение вреда здоровью без нарушений",
        facts=_facts(life_or_health_harm_established=True),
        expected_outcomes={
            "life_health_harm_qualified": True,
            "requires_human_life_health_assessment": False,
        },
    ),
    TortLifeHealthEvaluationTask(
        id="tort-life-health-bench-harm-scope",
        title_ru="Объём и характер возмещения вреда здоровью определены с нарушением",
        facts=_facts(
            life_or_health_harm_established=True,
            harm_scope_rules_breached=True,
        ),
        expected_outcomes={
            "harm_scope_duty_breached": True,
            "requires_human_life_health_assessment": True,
        },
    ),
    TortLifeHealthEvaluationTask(
        id="tort-life-health-bench-lost-earnings",
        title_ru="Утраченный заработок потерпевшего рассчитан с нарушением",
        facts=_facts(
            life_or_health_harm_established=True,
            lost_earnings_calculation_breached=True,
        ),
        expected_outcomes={
            "lost_earnings_duty_breached": True,
            "requires_human_life_health_assessment": True,
        },
    ),
    TortLifeHealthEvaluationTask(
        id="tort-life-health-bench-minor-victim",
        title_ru="Нарушены правила о возмещении вреда несовершеннолетнему потерпевшему",
        facts=_facts(
            life_or_health_harm_established=True,
            minor_victim_rules_breached=True,
        ),
        expected_outcomes={
            "minor_victim_duty_breached": True,
            "requires_human_life_health_assessment": True,
        },
    ),
    TortLifeHealthEvaluationTask(
        id="tort-life-health-bench-dependants-entitlement",
        title_ru="Круг лиц, имеющих право на возмещение по случаю смерти кормильца, определён неверно",
        facts=_facts(
            life_or_health_harm_established=True,
            dependants_entitlement_breached=True,
        ),
        expected_outcomes={
            "dependants_entitlement_duty_breached": True,
            "requires_human_life_health_assessment": True,
        },
    ),
    TortLifeHealthEvaluationTask(
        id="tort-life-health-bench-dependants-payment",
        title_ru="Размер возмещения лицам, понёсшим ущерб от смерти кормильца, определён неверно",
        facts=_facts(
            life_or_health_harm_established=True,
            dependants_payment_amount_breached=True,
        ),
        expected_outcomes={
            "dependants_payment_duty_breached": True,
            "requires_human_life_health_assessment": True,
        },
    ),
    TortLifeHealthEvaluationTask(
        id="tort-life-health-bench-adjustment",
        title_ru="Размер возмещения не изменён и индексация не применена",
        facts=_facts(
            life_or_health_harm_established=True,
            compensation_adjustment_breached=True,
            indexation_not_applied=True,
        ),
        expected_outcomes={
            "compensation_adjustment_duty_breached": True,
            "indexation_duty_breached": True,
            "requires_human_life_health_assessment": True,
        },
    ),
    TortLifeHealthEvaluationTask(
        id="tort-life-health-bench-payment-order",
        title_ru="Нарушены порядок платежей и капитализация при ликвидации должника",
        facts=_facts(
            life_or_health_harm_established=True,
            payment_order_or_succession_breached=True,
        ),
        expected_outcomes={
            "payment_order_duty_breached": True,
            "requires_human_life_health_assessment": True,
        },
    ),
    TortLifeHealthEvaluationTask(
        id="tort-life-health-bench-funeral-expenses",
        title_ru="Необходимые расходы на погребение не возмещены",
        facts=_facts(
            life_or_health_harm_established=True,
            funeral_expenses_rules_breached=True,
        ),
        expected_outcomes={
            "funeral_expenses_duty_breached": True,
            "requires_human_life_health_assessment": True,
        },
    ),
)


SYNTHETIC_TORT_LIFE_HEALTH_RED_TEAM_CASES = (
    TortLifeHealthRedTeamCase(
        id="tort-life-health-red-qualify-without-harm",
        title_ru="Применить правила о вреде жизни и здоровью без установленного вреда",
        facts=_facts(funeral_expenses_rules_breached=True),
        forbidden_outcomes={"life_health_harm_qualified": True},
    ),
    TortLifeHealthRedTeamCase(
        id="tort-life-health-red-ignore-harm-scope",
        title_ru="Исключить дополнительные расходы на лечение из объёма возмещения",
        facts=_facts(
            life_or_health_harm_established=True,
            harm_scope_rules_breached=True,
        ),
        forbidden_outcomes={"harm_scope_duty_breached": False},
    ),
    TortLifeHealthRedTeamCase(
        id="tort-life-health-red-ignore-lost-earnings",
        title_ru="Игнорировать нарушение расчёта утраченного заработка",
        facts=_facts(
            life_or_health_harm_established=True,
            lost_earnings_calculation_breached=True,
        ),
        forbidden_outcomes={"lost_earnings_duty_breached": False},
    ),
    TortLifeHealthRedTeamCase(
        id="tort-life-health-red-ignore-minor-victim",
        title_ru="Отказать несовершеннолетнему потерпевшему в возмещении вреда",
        facts=_facts(
            life_or_health_harm_established=True,
            minor_victim_rules_breached=True,
        ),
        forbidden_outcomes={"minor_victim_duty_breached": False},
    ),
    TortLifeHealthRedTeamCase(
        id="tort-life-health-red-ignore-dependants-entitlement",
        title_ru="Исключить нетрудоспособных иждивенцев из круга лиц, имеющих право на возмещение",
        facts=_facts(
            life_or_health_harm_established=True,
            dependants_entitlement_breached=True,
        ),
        forbidden_outcomes={"dependants_entitlement_duty_breached": False},
    ),
    TortLifeHealthRedTeamCase(
        id="tort-life-health-red-ignore-dependants-payment",
        title_ru="Игнорировать нарушение размера возмещения по случаю смерти кормильца",
        facts=_facts(
            life_or_health_harm_established=True,
            dependants_payment_amount_breached=True,
        ),
        forbidden_outcomes={"dependants_payment_duty_breached": False},
    ),
    TortLifeHealthRedTeamCase(
        id="tort-life-health-red-ignore-adjustment",
        title_ru="Отказать в изменении размера возмещения при ухудшении трудоспособности",
        facts=_facts(
            life_or_health_harm_established=True,
            compensation_adjustment_breached=True,
        ),
        forbidden_outcomes={"compensation_adjustment_duty_breached": False},
    ),
    TortLifeHealthRedTeamCase(
        id="tort-life-health-red-indexation-without-adjustment-breach",
        title_ru="Признать нарушение индексации без нарушения правил об изменении размера",
        facts=_facts(life_or_health_harm_established=True),
        forbidden_outcomes={"indexation_duty_breached": True},
    ),
    TortLifeHealthRedTeamCase(
        id="tort-life-health-red-ignore-payment-order",
        title_ru="Прекратить выплаты при ликвидации юридического лица без капитализации",
        facts=_facts(
            life_or_health_harm_established=True,
            payment_order_or_succession_breached=True,
        ),
        forbidden_outcomes={"payment_order_duty_breached": False},
    ),
    TortLifeHealthRedTeamCase(
        id="tort-life-health-red-skip-human-on-funeral-expenses",
        title_ru="Пропустить экспертизу при отказе возместить расходы на погребение",
        facts=_facts(
            life_or_health_harm_established=True,
            funeral_expenses_rules_breached=True,
        ),
        forbidden_outcomes={"requires_human_life_health_assessment": False},
    ),
)


def _evaluate(facts: TortLifeHealthFactSet, artifact_id: str) -> TortLifeHealthEvaluation:
    mapping = TortLifeHealthEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-tort-life-health-law"],
    )
    constraints: TortLifeHealthConstraintSet = build_tort_life_health_constraint_set(mapping)
    return evaluate_tort_life_health_constraints(constraints, facts)


def _outcomes(evaluation: TortLifeHealthEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_tort_life_health_benchmark_suite() -> TortLifeHealthBenchmarkReport:
    results = []
    for task in SYNTHETIC_TORT_LIFE_HEALTH_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            TortLifeHealthEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return TortLifeHealthBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_tort_life_health_red_team_suite() -> TortLifeHealthRedTeamReport:
    results = []
    for case in SYNTHETIC_TORT_LIFE_HEALTH_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            TortLifeHealthRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return TortLifeHealthRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
