"""Benchmark и red-team для модели возложения ответственности и просрочки."""

from pydantic import BaseModel, Field

from causa.institutional.contracts.attribution_delay import (
    AttributionDelayConstraintSet,
    AttributionDelayEvaluation,
    AttributionDelayEvidenceMappingResult,
    AttributionDelayFactSet,
    build_attribution_delay_constraint_set,
    evaluate_attribution_delay_constraints,
)


class AttributionDelayEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: AttributionDelayFactSet
    expected_outcomes: dict[str, bool]


class AttributionDelayEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class AttributionDelayBenchmarkReport(BaseModel):
    id: str = "attribution-delay-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[AttributionDelayEvaluationResult] = Field(default_factory=list)


class AttributionDelayRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: AttributionDelayFactSet
    forbidden_outcomes: dict[str, bool]


class AttributionDelayRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class AttributionDelayRedTeamReport(BaseModel):
    id: str = "attribution-delay-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[AttributionDelayRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> AttributionDelayFactSet:
    values = {field_name: False for field_name in AttributionDelayFactSet.model_fields}
    values.update(updates)
    return AttributionDelayFactSet(**values)


SYNTHETIC_ATTRIBUTION_DELAY_BENCHMARKS = (
    AttributionDelayEvaluationTask(
        id="attribution-bench-not-qualified",
        title_ru="Нарушение обязательства не заявлено",
        facts=_facts(creditor_delay_established=True),
        expected_outcomes={
            "attribution_qualified": False,
            "creditor_in_delay": False,
            "requires_human_attribution_assessment": False,
        },
    ),
    AttributionDelayEvaluationTask(
        id="attribution-bench-employees",
        title_ru="Нарушение вызвано действиями работников должника",
        facts=_facts(
            obligation_breach_asserted=True,
            breach_caused_by_debtor_employees=True,
        ),
        expected_outcomes={
            "debtor_answerable_for_employees": True,
            "debtor_answerable_for_third_party": False,
        },
    ),
    AttributionDelayEvaluationTask(
        id="attribution-bench-third-party-debtor-answers",
        title_ru="Исполнение возложено на третье лицо: отвечает должник",
        facts=_facts(
            obligation_breach_asserted=True,
            performance_entrusted_to_third_party=True,
            third_party_caused_breach=True,
        ),
        expected_outcomes={
            "debtor_answerable_for_third_party": True,
            "liability_shifted_to_performer": False,
        },
    ),
    AttributionDelayEvaluationTask(
        id="attribution-bench-third-party-law-shifts",
        title_ru="Закон возлагает ответственность на непосредственного исполнителя",
        facts=_facts(
            obligation_breach_asserted=True,
            performance_entrusted_to_third_party=True,
            third_party_caused_breach=True,
            law_assigns_liability_to_performer=True,
        ),
        expected_outcomes={
            "liability_shifted_to_performer": True,
            "debtor_answerable_for_third_party": False,
        },
    ),
    AttributionDelayEvaluationTask(
        id="attribution-bench-entrusted-without-breach",
        title_ru="Исполнение возложено, но нарушение вызвано не третьим лицом",
        facts=_facts(
            obligation_breach_asserted=True,
            performance_entrusted_to_third_party=True,
        ),
        expected_outcomes={
            "debtor_answerable_for_third_party": False,
            "liability_shifted_to_performer": False,
        },
    ),
    AttributionDelayEvaluationTask(
        id="attribution-bench-creditor-fault",
        title_ru="Нарушение произошло по вине обеих сторон",
        facts=_facts(
            obligation_breach_asserted=True,
            creditor_fault_contributed_to_breach=True,
        ),
        expected_outcomes={
            "creditor_fault_established": True,
            "liability_reducible_for_creditor_fault": True,
        },
    ),
    AttributionDelayEvaluationTask(
        id="attribution-bench-creditor-failed-to-mitigate",
        title_ru="Кредитор не принял разумных мер к уменьшению убытков",
        facts=_facts(
            obligation_breach_asserted=True,
            creditor_failed_to_mitigate_loss=True,
        ),
        expected_outcomes={
            "creditor_fault_established": True,
            "liability_reducible_for_creditor_fault": True,
        },
    ),
    AttributionDelayEvaluationTask(
        id="attribution-bench-debtor-delay",
        title_ru="Просрочка должника без просрочки кредитора",
        facts=_facts(
            obligation_breach_asserted=True,
            debtor_delay_established=True,
        ),
        expected_outcomes={
            "debtor_in_delay": True,
            "creditor_may_refuse_performance": False,
            "creditor_delay_excuses_debtor": False,
        },
    ),
    AttributionDelayEvaluationTask(
        id="attribution-bench-lost-interest",
        title_ru="Из-за просрочки должника исполнение утратило интерес",
        facts=_facts(
            obligation_breach_asserted=True,
            debtor_delay_established=True,
            performance_lost_interest_for_creditor=True,
        ),
        expected_outcomes={
            "debtor_in_delay": True,
            "creditor_may_refuse_performance": True,
        },
    ),
    AttributionDelayEvaluationTask(
        id="attribution-bench-creditor-delay-excuses",
        title_ru="Просрочка кредитора снимает просрочку должника",
        facts=_facts(
            obligation_breach_asserted=True,
            debtor_delay_established=True,
            creditor_delay_established=True,
        ),
        expected_outcomes={
            "creditor_in_delay": True,
            "creditor_delay_excuses_debtor": True,
            "debtor_in_delay": False,
            "creditor_may_refuse_performance": False,
        },
    ),
)


SYNTHETIC_ATTRIBUTION_DELAY_RED_TEAM_CASES = (
    AttributionDelayRedTeamCase(
        id="attribution-red-no-breach-no-liability",
        title_ru="Ответственность без заявленного нарушения обязательства",
        facts=_facts(
            breach_caused_by_debtor_employees=True,
            performance_entrusted_to_third_party=True,
            third_party_caused_breach=True,
        ),
        forbidden_outcomes={
            "debtor_answerable_for_employees": True,
            "debtor_answerable_for_third_party": True,
        },
    ),
    AttributionDelayRedTeamCase(
        id="attribution-red-entrustment-shifts-liability",
        title_ru="Возложение исполнения само по себе переносит ответственность",
        facts=_facts(
            obligation_breach_asserted=True,
            performance_entrusted_to_third_party=True,
            third_party_caused_breach=True,
        ),
        forbidden_outcomes={"liability_shifted_to_performer": True},
    ),
    AttributionDelayRedTeamCase(
        id="attribution-red-debtor-answers-despite-statute",
        title_ru="Должник отвечает вопреки прямому указанию закона на исполнителя",
        facts=_facts(
            obligation_breach_asserted=True,
            performance_entrusted_to_third_party=True,
            third_party_caused_breach=True,
            law_assigns_liability_to_performer=True,
        ),
        forbidden_outcomes={"debtor_answerable_for_third_party": True},
    ),
    AttributionDelayRedTeamCase(
        id="attribution-red-creditor-fault-without-breach",
        title_ru="Вина кредитора установлена вне заявленного нарушения",
        facts=_facts(creditor_fault_contributed_to_breach=True),
        forbidden_outcomes={"creditor_fault_established": True},
    ),
    AttributionDelayRedTeamCase(
        id="attribution-red-debtor-in-delay-during-creditor-delay",
        title_ru="Должник признан просрочившим при просрочке кредитора",
        facts=_facts(
            obligation_breach_asserted=True,
            debtor_delay_established=True,
            creditor_delay_established=True,
        ),
        forbidden_outcomes={"debtor_in_delay": True},
    ),
    AttributionDelayRedTeamCase(
        id="attribution-red-refusal-during-creditor-delay",
        title_ru="Отказ от принятия исполнения при собственной просрочке кредитора",
        facts=_facts(
            obligation_breach_asserted=True,
            debtor_delay_established=True,
            performance_lost_interest_for_creditor=True,
            creditor_delay_established=True,
        ),
        forbidden_outcomes={"creditor_may_refuse_performance": True},
    ),
    AttributionDelayRedTeamCase(
        id="attribution-red-refusal-without-lost-interest",
        title_ru="Отказ от принятия исполнения без утраты интереса",
        facts=_facts(
            obligation_breach_asserted=True,
            debtor_delay_established=True,
        ),
        forbidden_outcomes={"creditor_may_refuse_performance": True},
    ),
    AttributionDelayRedTeamCase(
        id="attribution-red-employees-imply-third-party",
        title_ru="Действия работников выданы за возложение исполнения на третье лицо",
        facts=_facts(
            obligation_breach_asserted=True,
            breach_caused_by_debtor_employees=True,
        ),
        forbidden_outcomes={"debtor_answerable_for_third_party": True},
    ),
    AttributionDelayRedTeamCase(
        id="attribution-red-creditor-delay-without-breach",
        title_ru="Просрочка кредитора освобождает должника вне заявленного нарушения",
        facts=_facts(creditor_delay_established=True),
        forbidden_outcomes={"creditor_delay_excuses_debtor": True},
    ),
    AttributionDelayRedTeamCase(
        id="attribution-red-mitigation-shifts-attribution",
        title_ru="Непринятие мер к уменьшению убытков выдано за перенос ответственности",
        facts=_facts(
            obligation_breach_asserted=True,
            creditor_failed_to_mitigate_loss=True,
        ),
        forbidden_outcomes={"liability_shifted_to_performer": True},
    ),
)


def _evaluate(facts: AttributionDelayFactSet, artifact_id: str) -> AttributionDelayEvaluation:
    mapping = AttributionDelayEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-attribution-delay-law"],
    )
    constraints: AttributionDelayConstraintSet = build_attribution_delay_constraint_set(mapping)
    return evaluate_attribution_delay_constraints(constraints, facts)


def _outcomes(evaluation: AttributionDelayEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_attribution_delay_benchmark_suite() -> AttributionDelayBenchmarkReport:
    results = []
    for task in SYNTHETIC_ATTRIBUTION_DELAY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            AttributionDelayEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return AttributionDelayBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_attribution_delay_red_team_suite() -> AttributionDelayRedTeamReport:
    results = []
    for case in SYNTHETIC_ATTRIBUTION_DELAY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            AttributionDelayRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return AttributionDelayRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
