from pydantic import BaseModel, Field

from causa.institutional.contracts.unjust_enrichment import (
    UnjustEnrichmentConstraintSet,
    UnjustEnrichmentEvaluation,
    UnjustEnrichmentEvidenceMappingResult,
    UnjustEnrichmentFactSet,
    build_unjust_enrichment_constraint_set,
    evaluate_unjust_enrichment_constraints,
)


class UnjustEnrichmentEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: UnjustEnrichmentFactSet
    expected_outcomes: dict[str, bool]


class UnjustEnrichmentEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class UnjustEnrichmentBenchmarkReport(BaseModel):
    id: str = "unjust-enrichment-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[UnjustEnrichmentEvaluationResult] = Field(default_factory=list)


class UnjustEnrichmentRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: UnjustEnrichmentFactSet
    forbidden_outcomes: dict[str, bool]


class UnjustEnrichmentRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class UnjustEnrichmentRedTeamReport(BaseModel):
    id: str = "unjust-enrichment-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[UnjustEnrichmentRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> UnjustEnrichmentFactSet:
    values = {field_name: False for field_name in UnjustEnrichmentFactSet.model_fields}
    values.update(updates)
    return UnjustEnrichmentFactSet(**values)


SYNTHETIC_UNJUST_ENRICHMENT_BENCHMARKS = (
    UnjustEnrichmentEvaluationTask(
        id="unjust-enrichment-bench-not-qualified",
        title_ru="Неосновательное обогащение не установлено",
        facts=_facts(return_in_kind_rules_breached=True),
        expected_outcomes={"unjust_enrichment_qualified": False},
    ),
    UnjustEnrichmentEvaluationTask(
        id="unjust-enrichment-bench-qualified-clean",
        title_ru="Возврат неосновательного обогащения без нарушений",
        facts=_facts(unjust_enrichment_established=True),
        expected_outcomes={
            "unjust_enrichment_qualified": True,
            "requires_human_unjust_enrichment_assessment": False,
        },
    ),
    UnjustEnrichmentEvaluationTask(
        id="unjust-enrichment-bench-restitution",
        title_ru="Обязанность возвратить обогащение нарушена, исключения не применены",
        facts=_facts(
            unjust_enrichment_established=True,
            restitution_duty_breached=True,
            non_returnable_enrichment_not_applied=True,
        ),
        expected_outcomes={
            "restitution_duty_breach_established": True,
            "non_returnable_enrichment_breached": True,
            "requires_human_unjust_enrichment_assessment": True,
        },
    ),
    UnjustEnrichmentEvaluationTask(
        id="unjust-enrichment-bench-irrelevance-of-cause",
        title_ru="Независимость обязанности возврата от причин обогащения не учтена",
        facts=_facts(
            unjust_enrichment_established=True,
            irrelevance_of_cause_disregarded=True,
        ),
        expected_outcomes={
            "irrelevance_of_cause_duty_breached": True,
            "requires_human_unjust_enrichment_assessment": True,
        },
    ),
    UnjustEnrichmentEvaluationTask(
        id="unjust-enrichment-bench-subsidiary-application",
        title_ru="Соотношение с другими требованиями о защите прав нарушено",
        facts=_facts(
            unjust_enrichment_established=True,
            subsidiary_application_rules_breached=True,
        ),
        expected_outcomes={
            "subsidiary_application_duty_breached": True,
            "requires_human_unjust_enrichment_assessment": True,
        },
    ),
    UnjustEnrichmentEvaluationTask(
        id="unjust-enrichment-bench-return-in-kind",
        title_ru="Возврат обогащения в натуре и ответственность за ухудшение нарушены",
        facts=_facts(
            unjust_enrichment_established=True,
            return_in_kind_rules_breached=True,
        ),
        expected_outcomes={
            "return_in_kind_duty_breached": True,
            "requires_human_unjust_enrichment_assessment": True,
        },
    ),
    UnjustEnrichmentEvaluationTask(
        id="unjust-enrichment-bench-value-compensation",
        title_ru="Возмещение действительной стоимости имущества определено с нарушением",
        facts=_facts(
            unjust_enrichment_established=True,
            value_compensation_rules_breached=True,
        ),
        expected_outcomes={
            "value_compensation_duty_breached": True,
            "requires_human_unjust_enrichment_assessment": True,
        },
    ),
    UnjustEnrichmentEvaluationTask(
        id="unjust-enrichment-bench-transferred-right",
        title_ru="Восстановление прежнего положения при неосновательной передаче права нарушено",
        facts=_facts(
            unjust_enrichment_established=True,
            transferred_right_restoration_breached=True,
        ),
        expected_outcomes={
            "transferred_right_duty_breached": True,
            "requires_human_unjust_enrichment_assessment": True,
        },
    ),
    UnjustEnrichmentEvaluationTask(
        id="unjust-enrichment-bench-income-and-interest",
        title_ru="Возмещение доходов и начисление процентов нарушены",
        facts=_facts(
            unjust_enrichment_established=True,
            income_and_interest_rules_breached=True,
        ),
        expected_outcomes={
            "income_and_interest_duty_breached": True,
            "requires_human_unjust_enrichment_assessment": True,
        },
    ),
    UnjustEnrichmentEvaluationTask(
        id="unjust-enrichment-bench-maintenance-costs",
        title_ru="Возмещение затрат на содержание и сохранение имущества нарушено",
        facts=_facts(
            unjust_enrichment_established=True,
            maintenance_costs_reimbursement_breached=True,
        ),
        expected_outcomes={
            "maintenance_costs_duty_breached": True,
            "requires_human_unjust_enrichment_assessment": True,
        },
    ),
)


SYNTHETIC_UNJUST_ENRICHMENT_RED_TEAM_CASES = (
    UnjustEnrichmentRedTeamCase(
        id="unjust-enrichment-red-qualify-without-enrichment",
        title_ru="Взыскать неосновательное обогащение без его установления",
        facts=_facts(return_in_kind_rules_breached=True),
        forbidden_outcomes={"unjust_enrichment_qualified": True},
    ),
    UnjustEnrichmentRedTeamCase(
        id="unjust-enrichment-red-ignore-restitution",
        title_ru="Освободить приобретателя от возврата неосновательного обогащения",
        facts=_facts(
            unjust_enrichment_established=True,
            restitution_duty_breached=True,
        ),
        forbidden_outcomes={"restitution_duty_breach_established": False},
    ),
    UnjustEnrichmentRedTeamCase(
        id="unjust-enrichment-red-ignore-irrelevance-of-cause",
        title_ru="Требовать вины приобретателя для возврата обогащения",
        facts=_facts(
            unjust_enrichment_established=True,
            irrelevance_of_cause_disregarded=True,
        ),
        forbidden_outcomes={"irrelevance_of_cause_duty_breached": False},
    ),
    UnjustEnrichmentRedTeamCase(
        id="unjust-enrichment-red-ignore-subsidiary-application",
        title_ru="Исключить применение правил к возврату исполненного по недействительной сделке",
        facts=_facts(
            unjust_enrichment_established=True,
            subsidiary_application_rules_breached=True,
        ),
        forbidden_outcomes={"subsidiary_application_duty_breached": False},
    ),
    UnjustEnrichmentRedTeamCase(
        id="unjust-enrichment-red-ignore-return-in-kind",
        title_ru="Освободить приобретателя от ответственности за ухудшение имущества",
        facts=_facts(
            unjust_enrichment_established=True,
            return_in_kind_rules_breached=True,
        ),
        forbidden_outcomes={"return_in_kind_duty_breached": False},
    ),
    UnjustEnrichmentRedTeamCase(
        id="unjust-enrichment-red-ignore-value-compensation",
        title_ru="Отказать в возмещении стоимости при невозможности возврата в натуре",
        facts=_facts(
            unjust_enrichment_established=True,
            value_compensation_rules_breached=True,
        ),
        forbidden_outcomes={"value_compensation_duty_breached": False},
    ),
    UnjustEnrichmentRedTeamCase(
        id="unjust-enrichment-red-ignore-transferred-right",
        title_ru="Отказать в восстановлении прав при уступке по недействительному обязательству",
        facts=_facts(
            unjust_enrichment_established=True,
            transferred_right_restoration_breached=True,
        ),
        forbidden_outcomes={"transferred_right_duty_breached": False},
    ),
    UnjustEnrichmentRedTeamCase(
        id="unjust-enrichment-red-ignore-income-and-interest",
        title_ru="Освободить приобретателя от возврата доходов и уплаты процентов",
        facts=_facts(
            unjust_enrichment_established=True,
            income_and_interest_rules_breached=True,
        ),
        forbidden_outcomes={"income_and_interest_duty_breached": False},
    ),
    UnjustEnrichmentRedTeamCase(
        id="unjust-enrichment-red-non-returnable-without-restitution-breach",
        title_ru="Применить правила о невозвратном обогащении без нарушения обязанности возврата",
        facts=_facts(unjust_enrichment_established=True),
        forbidden_outcomes={"non_returnable_enrichment_breached": True},
    ),
    UnjustEnrichmentRedTeamCase(
        id="unjust-enrichment-red-skip-human-on-maintenance-costs",
        title_ru="Пропустить экспертизу при отказе возместить затраты на содержание имущества",
        facts=_facts(
            unjust_enrichment_established=True,
            maintenance_costs_reimbursement_breached=True,
        ),
        forbidden_outcomes={"requires_human_unjust_enrichment_assessment": False},
    ),
)


def _evaluate(facts: UnjustEnrichmentFactSet, artifact_id: str) -> UnjustEnrichmentEvaluation:
    mapping = UnjustEnrichmentEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-unjust-enrichment-law"],
    )
    constraints: UnjustEnrichmentConstraintSet = build_unjust_enrichment_constraint_set(mapping)
    return evaluate_unjust_enrichment_constraints(constraints, facts)


def _outcomes(evaluation: UnjustEnrichmentEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_unjust_enrichment_benchmark_suite() -> UnjustEnrichmentBenchmarkReport:
    results = []
    for task in SYNTHETIC_UNJUST_ENRICHMENT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            UnjustEnrichmentEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return UnjustEnrichmentBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_unjust_enrichment_red_team_suite() -> UnjustEnrichmentRedTeamReport:
    results = []
    for case in SYNTHETIC_UNJUST_ENRICHMENT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            UnjustEnrichmentRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return UnjustEnrichmentRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
