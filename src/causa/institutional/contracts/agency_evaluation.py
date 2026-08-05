from pydantic import BaseModel, Field

from causa.institutional.contracts.agency import (
    AgencyConstraintSet,
    AgencyEvaluation,
    AgencyEvidenceMappingResult,
    AgencyFactSet,
    build_agency_constraint_set,
    evaluate_agency_constraints,
)


class AgencyEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: AgencyFactSet
    expected_outcomes: dict[str, bool]


class AgencyEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class AgencyBenchmarkReport(BaseModel):
    id: str = "agency-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[AgencyEvaluationResult] = Field(default_factory=list)


class AgencyRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: AgencyFactSet
    forbidden_outcomes: dict[str, bool]


class AgencyRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class AgencyRedTeamReport(BaseModel):
    id: str = "agency-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[AgencyRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> AgencyFactSet:
    values = {field_name: False for field_name in AgencyFactSet.model_fields}
    values.update(updates)
    return AgencyFactSet(**values)


SYNTHETIC_AGENCY_BENCHMARKS = (
    AgencyEvaluationTask(
        id="agency-bench-not-qualified",
        title_ru="Агентский договор не заключён",
        facts=_facts(subagency_rules_breached=True),
        expected_outcomes={"agency_qualified": False},
    ),
    AgencyEvaluationTask(
        id="agency-bench-qualified-clean",
        title_ru="Агентский договор без нарушений",
        facts=_facts(agency_contract_concluded=True),
        expected_outcomes={
            "agency_qualified": True,
            "requires_human_agency_assessment": False,
        },
    ),
    AgencyEvaluationTask(
        id="agency-bench-acting-capacity",
        title_ru="Сторона сделки, совершённой агентом, определена неверно",
        facts=_facts(
            agency_contract_concluded=True,
            agent_acting_capacity_misidentified=True,
        ),
        expected_outcomes={
            "acting_capacity_duty_breached": True,
            "requires_human_agency_assessment": True,
        },
    ),
    AgencyEvaluationTask(
        id="agency-bench-remuneration",
        title_ru="Нарушены правила об агентском вознаграждении",
        facts=_facts(
            agency_contract_concluded=True,
            agency_remuneration_rules_breached=True,
        ),
        expected_outcomes={
            "remuneration_duty_breached": True,
            "requires_human_agency_assessment": True,
        },
    ),
    AgencyEvaluationTask(
        id="agency-bench-exclusivity",
        title_ru="Нарушены ограничения прав принципала и агента, введены условия о покупателях",
        facts=_facts(
            agency_contract_concluded=True,
            agency_exclusivity_restrictions_breached=True,
            restrictions_against_consumers_imposed=True,
        ),
        expected_outcomes={
            "exclusivity_restrictions_duty_breached": True,
            "consumer_restrictions_void": True,
            "requires_human_agency_assessment": True,
        },
    ),
    AgencyEvaluationTask(
        id="agency-bench-report",
        title_ru="Отчёты агента принципалу не представлены",
        facts=_facts(
            agency_contract_concluded=True,
            agent_report_not_submitted=True,
        ),
        expected_outcomes={
            "report_duty_breached": True,
            "requires_human_agency_assessment": True,
        },
    ),
    AgencyEvaluationTask(
        id="agency-bench-report-objections",
        title_ru="Срок для возражений принципала по отчёту не соблюдён",
        facts=_facts(
            agency_contract_concluded=True,
            report_objections_period_disregarded=True,
        ),
        expected_outcomes={
            "report_objections_duty_breached": True,
            "requires_human_agency_assessment": True,
        },
    ),
    AgencyEvaluationTask(
        id="agency-bench-subagency",
        title_ru="Нарушены правила о субагентском договоре",
        facts=_facts(
            agency_contract_concluded=True,
            subagency_rules_breached=True,
        ),
        expected_outcomes={
            "subagency_duty_breached": True,
            "requires_human_agency_assessment": True,
        },
    ),
    AgencyEvaluationTask(
        id="agency-bench-termination",
        title_ru="Нарушены правила прекращения агентского договора",
        facts=_facts(
            agency_contract_concluded=True,
            agency_termination_rules_breached=True,
        ),
        expected_outcomes={
            "termination_duty_breached": True,
            "requires_human_agency_assessment": True,
        },
    ),
    AgencyEvaluationTask(
        id="agency-bench-applicable-rules",
        title_ru="Правила о поручении и комиссии применены неверно",
        facts=_facts(
            agency_contract_concluded=True,
            applicable_rules_selection_breached=True,
        ),
        expected_outcomes={
            "applicable_rules_duty_breached": True,
            "requires_human_agency_assessment": True,
        },
    ),
)


SYNTHETIC_AGENCY_RED_TEAM_CASES = (
    AgencyRedTeamCase(
        id="agency-red-qualify-without-contract",
        title_ru="Квалифицировать агентирование без заключения договора",
        facts=_facts(subagency_rules_breached=True),
        forbidden_outcomes={"agency_qualified": True},
    ),
    AgencyRedTeamCase(
        id="agency-red-ignore-acting-capacity",
        title_ru="Игнорировать неверное определение стороны сделки агента",
        facts=_facts(
            agency_contract_concluded=True,
            agent_acting_capacity_misidentified=True,
        ),
        forbidden_outcomes={"acting_capacity_duty_breached": False},
    ),
    AgencyRedTeamCase(
        id="agency-red-ignore-remuneration",
        title_ru="Освободить принципала от уплаты агентского вознаграждения",
        facts=_facts(
            agency_contract_concluded=True,
            agency_remuneration_rules_breached=True,
        ),
        forbidden_outcomes={"remuneration_duty_breached": False},
    ),
    AgencyRedTeamCase(
        id="agency-red-ignore-exclusivity",
        title_ru="Игнорировать нарушение ограничений прав принципала и агента",
        facts=_facts(
            agency_contract_concluded=True,
            agency_exclusivity_restrictions_breached=True,
        ),
        forbidden_outcomes={"exclusivity_restrictions_duty_breached": False},
    ),
    AgencyRedTeamCase(
        id="agency-red-consumer-restrictions-without-exclusivity-breach",
        title_ru="Признать ничтожность условий о покупателях без нарушения ограничений",
        facts=_facts(agency_contract_concluded=True),
        forbidden_outcomes={"consumer_restrictions_void": True},
    ),
    AgencyRedTeamCase(
        id="agency-red-ignore-report",
        title_ru="Освободить агента от представления отчётов принципалу",
        facts=_facts(
            agency_contract_concluded=True,
            agent_report_not_submitted=True,
        ),
        forbidden_outcomes={"report_duty_breached": False},
    ),
    AgencyRedTeamCase(
        id="agency-red-ignore-report-objections",
        title_ru="Игнорировать несоблюдение срока для возражений по отчёту",
        facts=_facts(
            agency_contract_concluded=True,
            report_objections_period_disregarded=True,
        ),
        forbidden_outcomes={"report_objections_duty_breached": False},
    ),
    AgencyRedTeamCase(
        id="agency-red-ignore-subagency",
        title_ru="Игнорировать нарушение правил о субагентском договоре",
        facts=_facts(
            agency_contract_concluded=True,
            subagency_rules_breached=True,
        ),
        forbidden_outcomes={"subagency_duty_breached": False},
    ),
    AgencyRedTeamCase(
        id="agency-red-ignore-termination",
        title_ru="Игнорировать нарушение правил прекращения агентского договора",
        facts=_facts(
            agency_contract_concluded=True,
            agency_termination_rules_breached=True,
        ),
        forbidden_outcomes={"termination_duty_breached": False},
    ),
    AgencyRedTeamCase(
        id="agency-red-skip-human-on-applicable-rules",
        title_ru="Пропустить экспертизу при неверном выборе применимых правил",
        facts=_facts(
            agency_contract_concluded=True,
            applicable_rules_selection_breached=True,
        ),
        forbidden_outcomes={"requires_human_agency_assessment": False},
    ),
)


def _evaluate(facts: AgencyFactSet, artifact_id: str) -> AgencyEvaluation:
    mapping = AgencyEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-agency-law"],
    )
    constraints: AgencyConstraintSet = build_agency_constraint_set(mapping)
    return evaluate_agency_constraints(constraints, facts)


def _outcomes(evaluation: AgencyEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_agency_benchmark_suite() -> AgencyBenchmarkReport:
    results = []
    for task in SYNTHETIC_AGENCY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            AgencyEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return AgencyBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_agency_red_team_suite() -> AgencyRedTeamReport:
    results = []
    for case in SYNTHETIC_AGENCY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            AgencyRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return AgencyRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
