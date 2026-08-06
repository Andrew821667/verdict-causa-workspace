from pydantic import BaseModel, Field

from causa.institutional.contracts.terms import (
    TermsConstraintSet,
    TermsEvaluation,
    TermsEvidenceMappingResult,
    TermsFactSet,
    build_terms_constraint_set,
    evaluate_terms_constraints,
)


class TermsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: TermsFactSet
    expected_outcomes: dict[str, bool]


class TermsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TermsBenchmarkReport(BaseModel):
    id: str = "terms-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[TermsEvaluationResult] = Field(default_factory=list)


class TermsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: TermsFactSet
    forbidden_outcomes: dict[str, bool]


class TermsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TermsRedTeamReport(BaseModel):
    id: str = "terms-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[TermsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> TermsFactSet:
    values = {field_name: False for field_name in TermsFactSet.model_fields}
    values.update(updates)
    return TermsFactSet(**values)


SYNTHETIC_TERMS_BENCHMARKS = (
    TermsEvaluationTask(
        id="terms-bench-not-qualified",
        title_ru="Срок в деле не заявлен",
        facts=_facts(term_start_rules_breached=True),
        expected_outcomes={"terms_qualified": False},
    ),
    TermsEvaluationTask(
        id="terms-bench-qualified-clean",
        title_ru="Срок исчислен без нарушений",
        facts=_facts(term_asserted=True),
        expected_outcomes={
            "terms_qualified": True,
            "requires_human_terms_assessment": False,
        },
    ),
    TermsEvaluationTask(
        id="terms-bench-definition-and-event",
        title_ru="Срок определён указанием на событие, которое не является неизбежным",
        facts=_facts(
            term_asserted=True,
            term_definition_breached=True,
            term_event_certainty_breached=True,
        ),
        expected_outcomes={
            "term_definition_duty_breached": True,
            "term_event_certainty_duty_breached": True,
            "requires_human_terms_assessment": True,
        },
    ),
    TermsEvaluationTask(
        id="terms-bench-start",
        title_ru="Начало течения срока определено неверно",
        facts=_facts(term_asserted=True, term_start_rules_breached=True),
        expected_outcomes={
            "term_start_duty_breached": True,
            "requires_human_terms_assessment": True,
        },
    ),
    TermsEvaluationTask(
        id="terms-bench-end",
        title_ru="Окончание срока, исчисляемого месяцами, определено неверно",
        facts=_facts(term_asserted=True, term_end_rules_breached=True),
        expected_outcomes={
            "term_end_duty_breached": True,
            "requires_human_terms_assessment": True,
        },
    ),
    TermsEvaluationTask(
        id="terms-bench-non-working-day",
        title_ru="Не применён перенос окончания срока на ближайший рабочий день",
        facts=_facts(term_asserted=True, non_working_day_rule_breached=True),
        expected_outcomes={
            "non_working_day_duty_breached": True,
            "requires_human_terms_assessment": True,
        },
    ),
    TermsEvaluationTask(
        id="terms-bench-limitation-calculation",
        title_ru="Срок исковой давности исчислен с нарушением главы 11",
        facts=_facts(term_asserted=True, limitation_term_calculation_breached=True),
        expected_outcomes={
            "term_calculation_defective": True,
            "requires_human_terms_assessment": True,
        },
    ),
    TermsEvaluationTask(
        id="terms-bench-performance-deadline",
        title_ru="Действие в последний день срока признано просроченным до двадцати четырёх часов",
        facts=_facts(term_asserted=True, performance_deadline_breached=True),
        expected_outcomes={
            "performance_deadline_duty_breached": True,
            "requires_human_terms_assessment": True,
        },
    ),
    TermsEvaluationTask(
        id="terms-bench-operating-hours",
        title_ru="Не учтено прекращение соответствующих операций в организации",
        facts=_facts(term_asserted=True, organisation_operating_hours_breached=True),
        expected_outcomes={
            "organisation_operating_hours_duty_breached": True,
            "requires_human_terms_assessment": True,
        },
    ),
    TermsEvaluationTask(
        id="terms-bench-notice-dispatch",
        title_ru="Не учтена сдача письменного извещения в организацию связи в последний день",
        facts=_facts(term_asserted=True, written_notice_dispatch_breached=True),
        expected_outcomes={
            "written_notice_dispatch_duty_breached": True,
            "requires_human_terms_assessment": True,
        },
    ),
)


SYNTHETIC_TERMS_RED_TEAM_CASES = (
    TermsRedTeamCase(
        id="terms-red-qualify-without-term",
        title_ru="Применить правила об исчислении сроков без заявленного срока",
        facts=_facts(term_start_rules_breached=True),
        forbidden_outcomes={"terms_qualified": True},
    ),
    TermsRedTeamCase(
        id="terms-red-ignore-definition",
        title_ru="Признать срок определённым вопреки статье 190",
        facts=_facts(term_asserted=True, term_definition_breached=True),
        forbidden_outcomes={"term_definition_duty_breached": False},
    ),
    TermsRedTeamCase(
        id="terms-red-allow-uncertain-event",
        title_ru="Определить срок указанием на событие, наступление которого не является неизбежным",
        facts=_facts(
            term_asserted=True,
            term_definition_breached=True,
            term_event_certainty_breached=True,
        ),
        forbidden_outcomes={"term_event_certainty_duty_breached": False},
    ),
    TermsRedTeamCase(
        id="terms-red-ignore-start",
        title_ru="Начать течение срока в день наступления события",
        facts=_facts(term_asserted=True, term_start_rules_breached=True),
        forbidden_outcomes={"term_start_duty_breached": False},
    ),
    TermsRedTeamCase(
        id="terms-red-ignore-end",
        title_ru="Игнорировать правила окончания срока, исчисляемого годами и месяцами",
        facts=_facts(term_asserted=True, term_end_rules_breached=True),
        forbidden_outcomes={"term_end_duty_breached": False},
    ),
    TermsRedTeamCase(
        id="terms-red-ignore-non-working-day",
        title_ru="Считать срок истекшим в нерабочий день",
        facts=_facts(term_asserted=True, non_working_day_rule_breached=True),
        forbidden_outcomes={"non_working_day_duty_breached": False},
    ),
    TermsRedTeamCase(
        id="terms-red-ignore-limitation-calculation",
        title_ru="Считать давность истекшей при пороке исчисления срока",
        facts=_facts(term_asserted=True, limitation_term_calculation_breached=True),
        forbidden_outcomes={"term_calculation_defective": False},
    ),
    TermsRedTeamCase(
        id="terms-red-shorten-last-day",
        title_ru="Считать действие просроченным до истечения последнего дня срока",
        facts=_facts(term_asserted=True, performance_deadline_breached=True),
        forbidden_outcomes={"performance_deadline_duty_breached": False},
    ),
    TermsRedTeamCase(
        id="terms-red-ignore-operating-hours",
        title_ru="Игнорировать час прекращения операций в организации",
        facts=_facts(term_asserted=True, organisation_operating_hours_breached=True),
        forbidden_outcomes={"organisation_operating_hours_duty_breached": False},
    ),
    TermsRedTeamCase(
        id="terms-red-event-certainty-without-definition-defect",
        title_ru="Признать порок неизбежности события при верном определении срока",
        facts=_facts(term_asserted=True),
        forbidden_outcomes={"term_event_certainty_duty_breached": True},
    ),
)


def _evaluate(facts: TermsFactSet, artifact_id: str) -> TermsEvaluation:
    mapping = TermsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-terms-law"],
    )
    constraints: TermsConstraintSet = build_terms_constraint_set(mapping)
    return evaluate_terms_constraints(constraints, facts)


def _outcomes(evaluation: TermsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_terms_benchmark_suite() -> TermsBenchmarkReport:
    results = []
    for task in SYNTHETIC_TERMS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            TermsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return TermsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_terms_red_team_suite() -> TermsRedTeamReport:
    results = []
    for case in SYNTHETIC_TERMS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            TermsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return TermsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
