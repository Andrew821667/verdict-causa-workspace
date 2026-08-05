from pydantic import BaseModel, Field

from causa.institutional.contracts.negotiorum_gestio import (
    NegotiorumGestioConstraintSet,
    NegotiorumGestioEvaluation,
    NegotiorumGestioEvidenceMappingResult,
    NegotiorumGestioFactSet,
    build_negotiorum_gestio_constraint_set,
    evaluate_negotiorum_gestio_constraints,
)


class NegotiorumGestioEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: NegotiorumGestioFactSet
    expected_outcomes: dict[str, bool]


class NegotiorumGestioEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class NegotiorumGestioBenchmarkReport(BaseModel):
    id: str = "negotiorum-gestio-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[NegotiorumGestioEvaluationResult] = Field(default_factory=list)


class NegotiorumGestioRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: NegotiorumGestioFactSet
    forbidden_outcomes: dict[str, bool]


class NegotiorumGestioRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class NegotiorumGestioRedTeamReport(BaseModel):
    id: str = "negotiorum-gestio-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[NegotiorumGestioRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> NegotiorumGestioFactSet:
    values = {field_name: False for field_name in NegotiorumGestioFactSet.model_fields}
    values.update(updates)
    return NegotiorumGestioFactSet(**values)


SYNTHETIC_NEGOTIORUM_GESTIO_BENCHMARKS = (
    NegotiorumGestioEvaluationTask(
        id="negotiorum-gestio-bench-not-qualified",
        title_ru="Действия в чужом интересе без поручения не совершались",
        facts=_facts(necessary_expenses_not_reimbursed=True),
        expected_outcomes={"negotiorum_gestio_qualified": False},
    ),
    NegotiorumGestioEvaluationTask(
        id="negotiorum-gestio-bench-qualified-clean",
        title_ru="Действия в чужом интересе без нарушений",
        facts=_facts(action_in_another_interest_performed=True),
        expected_outcomes={
            "negotiorum_gestio_qualified": True,
            "requires_human_negotiorum_gestio_assessment": False,
        },
    ),
    NegotiorumGestioEvaluationTask(
        id="negotiorum-gestio-bench-conditions",
        title_ru="Нарушены условия совершения действий в чужом интересе",
        facts=_facts(
            action_in_another_interest_performed=True,
            action_conditions_breached=True,
        ),
        expected_outcomes={
            "action_conditions_duty_breached": True,
            "requires_human_negotiorum_gestio_assessment": True,
        },
    ),
    NegotiorumGestioEvaluationTask(
        id="negotiorum-gestio-bench-notice",
        title_ru="Заинтересованное лицо не уведомлено, решение не выждано",
        facts=_facts(
            action_in_another_interest_performed=True,
            interested_person_notice_not_given=True,
            notice_waiting_duty_breached=True,
        ),
        expected_outcomes={
            "notice_duty_breached": True,
            "waiting_duty_breached": True,
            "requires_human_negotiorum_gestio_assessment": True,
        },
    ),
    NegotiorumGestioEvaluationTask(
        id="negotiorum-gestio-bench-approval",
        title_ru="Последствия одобрения действий заинтересованным лицом не применены",
        facts=_facts(
            action_in_another_interest_performed=True,
            approval_effects_not_applied=True,
        ),
        expected_outcomes={
            "approval_effects_breached": True,
            "requires_human_negotiorum_gestio_assessment": True,
        },
    ),
    NegotiorumGestioEvaluationTask(
        id="negotiorum-gestio-bench-disapproval",
        title_ru="Действия продолжены после того, как стало известно о неодобрении",
        facts=_facts(
            action_in_another_interest_performed=True,
            disapproved_action_continued=True,
        ),
        expected_outcomes={
            "disapproval_effects_breached": True,
            "requires_human_negotiorum_gestio_assessment": True,
        },
    ),
    NegotiorumGestioEvaluationTask(
        id="negotiorum-gestio-bench-expenses",
        title_ru="Необходимые расходы и реальный ущерб не возмещены",
        facts=_facts(
            action_in_another_interest_performed=True,
            necessary_expenses_not_reimbursed=True,
        ),
        expected_outcomes={
            "expenses_reimbursement_breached": True,
            "requires_human_negotiorum_gestio_assessment": True,
        },
    ),
    NegotiorumGestioEvaluationTask(
        id="negotiorum-gestio-bench-remuneration",
        title_ru="Нарушены правила о вознаграждении за действия в чужом интересе",
        facts=_facts(
            action_in_another_interest_performed=True,
            remuneration_rules_breached=True,
        ),
        expected_outcomes={
            "remuneration_duty_breached": True,
            "requires_human_negotiorum_gestio_assessment": True,
        },
    ),
    NegotiorumGestioEvaluationTask(
        id="negotiorum-gestio-bench-transaction",
        title_ru="Последствия сделки, заключённой в чужом интересе, не перенесены",
        facts=_facts(
            action_in_another_interest_performed=True,
            transaction_consequences_transfer_breached=True,
        ),
        expected_outcomes={
            "transaction_consequences_breached": True,
            "requires_human_negotiorum_gestio_assessment": True,
        },
    ),
    NegotiorumGestioEvaluationTask(
        id="negotiorum-gestio-bench-reporting",
        title_ru="Отчёт заинтересованному лицу не представлен",
        facts=_facts(
            action_in_another_interest_performed=True,
            gestor_reporting_duty_breached=True,
        ),
        expected_outcomes={
            "reporting_duty_breached": True,
            "requires_human_negotiorum_gestio_assessment": True,
        },
    ),
)


SYNTHETIC_NEGOTIORUM_GESTIO_RED_TEAM_CASES = (
    NegotiorumGestioRedTeamCase(
        id="negotiorum-gestio-red-qualify-without-action",
        title_ru="Квалифицировать действия в чужом интересе без их совершения",
        facts=_facts(necessary_expenses_not_reimbursed=True),
        forbidden_outcomes={"negotiorum_gestio_qualified": True},
    ),
    NegotiorumGestioRedTeamCase(
        id="negotiorum-gestio-red-ignore-conditions",
        title_ru="Игнорировать нарушение условий действий в чужом интересе",
        facts=_facts(
            action_in_another_interest_performed=True,
            action_conditions_breached=True,
        ),
        forbidden_outcomes={"action_conditions_duty_breached": False},
    ),
    NegotiorumGestioRedTeamCase(
        id="negotiorum-gestio-red-ignore-notice",
        title_ru="Игнорировать отсутствие сообщения заинтересованному лицу",
        facts=_facts(
            action_in_another_interest_performed=True,
            interested_person_notice_not_given=True,
        ),
        forbidden_outcomes={"notice_duty_breached": False},
    ),
    NegotiorumGestioRedTeamCase(
        id="negotiorum-gestio-red-waiting-without-notice-breach",
        title_ru="Признать нарушение ожидания решения без нарушения уведомления",
        facts=_facts(action_in_another_interest_performed=True),
        forbidden_outcomes={"waiting_duty_breached": True},
    ),
    NegotiorumGestioRedTeamCase(
        id="negotiorum-gestio-red-ignore-approval",
        title_ru="Игнорировать последствия одобрения действий заинтересованным лицом",
        facts=_facts(
            action_in_another_interest_performed=True,
            approval_effects_not_applied=True,
        ),
        forbidden_outcomes={"approval_effects_breached": False},
    ),
    NegotiorumGestioRedTeamCase(
        id="negotiorum-gestio-red-allow-disapproved-action",
        title_ru="Возложить обязанности на заинтересованное лицо после неодобрения",
        facts=_facts(
            action_in_another_interest_performed=True,
            disapproved_action_continued=True,
        ),
        forbidden_outcomes={"disapproval_effects_breached": False},
    ),
    NegotiorumGestioRedTeamCase(
        id="negotiorum-gestio-red-ignore-expenses",
        title_ru="Игнорировать невозмещение необходимых расходов",
        facts=_facts(
            action_in_another_interest_performed=True,
            necessary_expenses_not_reimbursed=True,
        ),
        forbidden_outcomes={"expenses_reimbursement_breached": False},
    ),
    NegotiorumGestioRedTeamCase(
        id="negotiorum-gestio-red-ignore-remuneration",
        title_ru="Игнорировать нарушение правил о вознаграждении",
        facts=_facts(
            action_in_another_interest_performed=True,
            remuneration_rules_breached=True,
        ),
        forbidden_outcomes={"remuneration_duty_breached": False},
    ),
    NegotiorumGestioRedTeamCase(
        id="negotiorum-gestio-red-ignore-transaction",
        title_ru="Игнорировать нарушение перехода последствий сделки в чужом интересе",
        facts=_facts(
            action_in_another_interest_performed=True,
            transaction_consequences_transfer_breached=True,
        ),
        forbidden_outcomes={"transaction_consequences_breached": False},
    ),
    NegotiorumGestioRedTeamCase(
        id="negotiorum-gestio-red-skip-human-on-reporting",
        title_ru="Пропустить экспертизу при непредставлении отчёта",
        facts=_facts(
            action_in_another_interest_performed=True,
            gestor_reporting_duty_breached=True,
        ),
        forbidden_outcomes={"requires_human_negotiorum_gestio_assessment": False},
    ),
)


def _evaluate(facts: NegotiorumGestioFactSet, artifact_id: str) -> NegotiorumGestioEvaluation:
    mapping = NegotiorumGestioEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-negotiorum-gestio-law"],
    )
    constraints: NegotiorumGestioConstraintSet = build_negotiorum_gestio_constraint_set(mapping)
    return evaluate_negotiorum_gestio_constraints(constraints, facts)


def _outcomes(evaluation: NegotiorumGestioEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_negotiorum_gestio_benchmark_suite() -> NegotiorumGestioBenchmarkReport:
    results = []
    for task in SYNTHETIC_NEGOTIORUM_GESTIO_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            NegotiorumGestioEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return NegotiorumGestioBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_negotiorum_gestio_red_team_suite() -> NegotiorumGestioRedTeamReport:
    results = []
    for case in SYNTHETIC_NEGOTIORUM_GESTIO_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            NegotiorumGestioRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return NegotiorumGestioRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
