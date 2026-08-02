from pydantic import BaseModel, Field

from causa.institutional.contracts.state_work import (
    StateWorkConstraintSet,
    StateWorkEvaluation,
    StateWorkEvidenceMappingResult,
    StateWorkFactSet,
    build_state_work_constraint_set,
    evaluate_state_work_constraints,
)


class StateWorkEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: StateWorkFactSet
    expected_outcomes: dict[str, bool]


class StateWorkEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class StateWorkBenchmarkReport(BaseModel):
    id: str = "state-work-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[StateWorkEvaluationResult] = Field(default_factory=list)


class StateWorkRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: StateWorkFactSet
    forbidden_outcomes: dict[str, bool]


class StateWorkRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class StateWorkRedTeamReport(BaseModel):
    id: str = "state-work-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[StateWorkRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> StateWorkFactSet:
    values = {field_name: False for field_name in StateWorkFactSet.model_fields}
    values.update(updates)
    return StateWorkFactSet(**values)


SYNTHETIC_STATE_WORK_BENCHMARKS = (
    StateWorkEvaluationTask(
        id="state-work-bench-not-qualified",
        title_ru="Работы не предназначены для государственных или муниципальных нужд",
        facts=_facts(scope_or_cost_terms_not_agreed=True),
        expected_outcomes={"state_work_qualified": False},
    ),
    StateWorkEvaluationTask(
        id="state-work-bench-qualified-clean",
        title_ru="Государственный контракт на подрядные работы без нарушений",
        facts=_facts(work_for_state_or_municipal_needs=True),
        expected_outcomes={
            "state_work_qualified": True,
            "requires_human_state_work_assessment": False,
        },
    ),
    StateWorkEvaluationTask(
        id="state-work-bench-no-contract",
        title_ru="Работы выполняются без государственного или муниципального контракта",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            state_contract_not_concluded=True,
        ),
        expected_outcomes={
            "state_contract_requirement_breached": True,
            "requires_human_state_work_assessment": True,
        },
    ),
    StateWorkEvaluationTask(
        id="state-work-bench-customer-status",
        title_ru="Заказчик не является получателем бюджетных средств",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            customer_not_authorized_budget_recipient=True,
        ),
        expected_outcomes={
            "customer_status_invalid": True,
            "requires_human_state_work_assessment": True,
        },
    ),
    StateWorkEvaluationTask(
        id="state-work-bench-conclusion-procedure",
        title_ru="Нарушен порядок заключения государственного контракта",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            contract_conclusion_procedure_breached=True,
        ),
        expected_outcomes={
            "conclusion_procedure_breached": True,
            "requires_human_state_work_assessment": True,
        },
    ),
    StateWorkEvaluationTask(
        id="state-work-bench-scope-and-cost",
        title_ru="Не согласованы объём и стоимость подлежащей выполнению работы",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            scope_or_cost_terms_not_agreed=True,
        ),
        expected_outcomes={
            "scope_or_cost_terms_missing": True,
            "requires_human_state_work_assessment": True,
        },
    ),
    StateWorkEvaluationTask(
        id="state-work-bench-schedule",
        title_ru="Не согласованы сроки начала и окончания работы",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            start_or_completion_dates_not_agreed=True,
        ),
        expected_outcomes={
            "schedule_terms_missing": True,
            "requires_human_state_work_assessment": True,
        },
    ),
    StateWorkEvaluationTask(
        id="state-work-bench-funding",
        title_ru="Не определены размер и порядок финансирования и оплаты работ",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            funding_and_payment_terms_not_agreed=True,
        ),
        expected_outcomes={
            "funding_terms_missing": True,
            "requires_human_state_work_assessment": True,
        },
    ),
    StateWorkEvaluationTask(
        id="state-work-bench-security",
        title_ru="Не определены способы обеспечения исполнения обязательств сторон",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            performance_security_not_agreed=True,
        ),
        expected_outcomes={
            "performance_security_missing": True,
            "requires_human_state_work_assessment": True,
        },
    ),
    StateWorkEvaluationTask(
        id="state-work-bench-budget-reduction",
        title_ru="Бюджетные средства уменьшены без согласования новых условий и возмещения убытков",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            budget_reduced_without_agreed_new_terms=True,
            contractor_losses_from_changed_terms_not_compensated=True,
        ),
        expected_outcomes={
            "budget_reduction_terms_not_agreed": True,
            "contractor_losses_compensation_due": True,
            "requires_human_state_work_assessment": True,
        },
    ),
)


SYNTHETIC_STATE_WORK_RED_TEAM_CASES = (
    StateWorkRedTeamCase(
        id="state-work-red-qualify-without-state-needs",
        title_ru="Квалифицировать подряд для госнужд без государственных или муниципальных нужд",
        facts=_facts(scope_or_cost_terms_not_agreed=True),
        forbidden_outcomes={"state_work_qualified": True},
    ),
    StateWorkRedTeamCase(
        id="state-work-red-allow-work-without-contract",
        title_ru="Признать допустимым выполнение работ без государственного контракта",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            state_contract_not_concluded=True,
        ),
        forbidden_outcomes={"state_contract_requirement_breached": False},
    ),
    StateWorkRedTeamCase(
        id="state-work-red-ignore-customer-status",
        title_ru="Игнорировать отсутствие у заказчика статуса получателя бюджетных средств",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            customer_not_authorized_budget_recipient=True,
        ),
        forbidden_outcomes={"customer_status_invalid": False},
    ),
    StateWorkRedTeamCase(
        id="state-work-red-ignore-procedure",
        title_ru="Игнорировать нарушение порядка заключения контракта",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            contract_conclusion_procedure_breached=True,
        ),
        forbidden_outcomes={"conclusion_procedure_breached": False},
    ),
    StateWorkRedTeamCase(
        id="state-work-red-ignore-scope-and-cost",
        title_ru="Игнорировать отсутствие условий об объёме и стоимости работ",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            scope_or_cost_terms_not_agreed=True,
        ),
        forbidden_outcomes={"scope_or_cost_terms_missing": False},
    ),
    StateWorkRedTeamCase(
        id="state-work-red-ignore-schedule",
        title_ru="Игнорировать отсутствие сроков начала и окончания работы",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            start_or_completion_dates_not_agreed=True,
        ),
        forbidden_outcomes={"schedule_terms_missing": False},
    ),
    StateWorkRedTeamCase(
        id="state-work-red-ignore-funding",
        title_ru="Игнорировать отсутствие условий о финансировании и оплате работ",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            funding_and_payment_terms_not_agreed=True,
        ),
        forbidden_outcomes={"funding_terms_missing": False},
    ),
    StateWorkRedTeamCase(
        id="state-work-red-ignore-security",
        title_ru="Игнорировать отсутствие способов обеспечения исполнения обязательств",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            performance_security_not_agreed=True,
        ),
        forbidden_outcomes={"performance_security_missing": False},
    ),
    StateWorkRedTeamCase(
        id="state-work-red-losses-without-budget-reduction",
        title_ru="Признать возмещение убытков без уменьшения бюджетных средств",
        facts=_facts(work_for_state_or_municipal_needs=True),
        forbidden_outcomes={"contractor_losses_compensation_due": True},
    ),
    StateWorkRedTeamCase(
        id="state-work-red-skip-human-on-budget-reduction",
        title_ru="Пропустить экспертизу при уменьшении бюджетного финансирования",
        facts=_facts(
            work_for_state_or_municipal_needs=True,
            budget_reduced_without_agreed_new_terms=True,
        ),
        forbidden_outcomes={"requires_human_state_work_assessment": False},
    ),
)


def _evaluate(facts: StateWorkFactSet, artifact_id: str) -> StateWorkEvaluation:
    mapping = StateWorkEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-state-work-law"],
    )
    constraints: StateWorkConstraintSet = build_state_work_constraint_set(mapping)
    return evaluate_state_work_constraints(constraints, facts)


def _outcomes(evaluation: StateWorkEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_state_work_benchmark_suite() -> StateWorkBenchmarkReport:
    results = []
    for task in SYNTHETIC_STATE_WORK_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            StateWorkEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return StateWorkBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_state_work_red_team_suite() -> StateWorkRedTeamReport:
    results = []
    for case in SYNTHETIC_STATE_WORK_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            StateWorkRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return StateWorkRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
