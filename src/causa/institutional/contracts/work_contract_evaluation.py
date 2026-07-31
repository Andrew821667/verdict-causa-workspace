from pydantic import BaseModel, Field

from causa.institutional.contracts.work_contract import (
    WorkContractConstraintSet,
    WorkContractEvaluation,
    WorkContractEvidenceMappingResult,
    WorkContractFactSet,
    build_work_contract_constraint_set,
    evaluate_work_contract_constraints,
)


class WorkContractEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: WorkContractFactSet
    expected_outcomes: dict[str, bool]


class WorkContractEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class WorkContractBenchmarkReport(BaseModel):
    id: str = "work-contract-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[WorkContractEvaluationResult] = Field(default_factory=list)


class WorkContractRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: WorkContractFactSet
    forbidden_outcomes: dict[str, bool]


class WorkContractRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class WorkContractRedTeamReport(BaseModel):
    id: str = "work-contract-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[WorkContractRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> WorkContractFactSet:
    values = {field_name: False for field_name in WorkContractFactSet.model_fields}
    values.update(updates)
    return WorkContractFactSet(**values)


SYNTHETIC_WORK_CONTRACT_BENCHMARKS = (
    WorkContractEvaluationTask(
        id="work-contract-bench-not-qualified",
        title_ru="Отношения без выполнения работы и сдачи результата за плату",
        facts=_facts(work_result_defective=True),
        expected_outcomes={"work_contract_qualified": False},
    ),
    WorkContractEvaluationTask(
        id="work-contract-bench-qualified-clean",
        title_ru="Договор подряда без нарушений",
        facts=_facts(work_performed_and_result_delivered_for_fee=True),
        expected_outcomes={
            "work_contract_qualified": True,
            "requires_human_work_contract_assessment": False,
        },
    ),
    WorkContractEvaluationTask(
        id="work-contract-bench-personal-duty",
        title_ru="Субподрядчик привлечён вопреки обязанности выполнить работу лично",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            subcontractor_engaged_despite_personal_duty=True,
        ),
        expected_outcomes={
            "personal_performance_duty_breached": True,
            "requires_human_work_contract_assessment": True,
        },
    ),
    WorkContractEvaluationTask(
        id="work-contract-bench-terms-not-agreed",
        title_ru="Не согласованы начальный и конечный сроки выполнения работы",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            start_or_completion_term_not_agreed=True,
        ),
        expected_outcomes={
            "term_condition_not_agreed": True,
            "requires_human_work_contract_assessment": True,
        },
    ),
    WorkContractEvaluationTask(
        id="work-contract-bench-estimate-notice",
        title_ru="Смета существенно превышена без своевременного предупреждения",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            estimate_exceeded_without_timely_notice=True,
        ),
        expected_outcomes={
            "estimate_notice_duty_breached": True,
            "requires_human_work_contract_assessment": True,
        },
    ),
    WorkContractEvaluationTask(
        id="work-contract-bench-customer-material",
        title_ru="Материал заказчика непригоден или недоброкачественен",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            customer_material_unsuitable=True,
        ),
        expected_outcomes={
            "customer_material_liability": True,
            "requires_human_work_contract_assessment": True,
        },
    ),
    WorkContractEvaluationTask(
        id="work-contract-bench-risk-warning",
        title_ru="Подрядчик не предупредил об обстоятельствах, угрожающих годности работы",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            contractor_failed_to_warn_of_risk=True,
        ),
        expected_outcomes={
            "risk_warning_duty_breached": True,
            "requires_human_work_contract_assessment": True,
        },
    ),
    WorkContractEvaluationTask(
        id="work-contract-bench-defect-within-period",
        title_ru="Недостаток результата обнаружен в установленный срок",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            work_result_defective=True,
            defect_found_within_statutory_period=True,
        ),
        expected_outcomes={
            "contractor_liable_for_defects": True,
            "defect_claim_within_period": True,
            "requires_human_work_contract_assessment": True,
        },
    ),
    WorkContractEvaluationTask(
        id="work-contract-bench-acceptance-avoided",
        title_ru="Заказчик уклонился от приёмки или не осмотрел результат",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            acceptance_avoided_or_inspection_omitted=True,
        ),
        expected_outcomes={
            "acceptance_duty_breached": True,
            "requires_human_work_contract_assessment": True,
        },
    ),
    WorkContractEvaluationTask(
        id="work-contract-bench-withdrawal",
        title_ru="Заказчик отказался от договора до сдачи результата без оплаты",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            customer_withdrew_before_completion_without_payment=True,
        ),
        expected_outcomes={
            "withdrawal_compensation_due": True,
            "requires_human_work_contract_assessment": True,
        },
    ),
)


SYNTHETIC_WORK_CONTRACT_RED_TEAM_CASES = (
    WorkContractRedTeamCase(
        id="work-contract-red-qualify-without-work",
        title_ru="Квалифицировать подряд без выполнения работы и сдачи результата",
        facts=_facts(work_result_defective=True),
        forbidden_outcomes={"work_contract_qualified": True},
    ),
    WorkContractRedTeamCase(
        id="work-contract-red-allow-subcontracting",
        title_ru="Считать правомерным привлечение субподрядчика вопреки личной обязанности",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            subcontractor_engaged_despite_personal_duty=True,
        ),
        forbidden_outcomes={"personal_performance_duty_breached": False},
    ),
    WorkContractRedTeamCase(
        id="work-contract-red-ignore-terms",
        title_ru="Игнорировать отсутствие согласованных сроков выполнения работы",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            start_or_completion_term_not_agreed=True,
        ),
        forbidden_outcomes={"term_condition_not_agreed": False},
    ),
    WorkContractRedTeamCase(
        id="work-contract-red-ignore-estimate-notice",
        title_ru="Игнорировать превышение сметы без предупреждения заказчика",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            estimate_exceeded_without_timely_notice=True,
        ),
        forbidden_outcomes={"estimate_notice_duty_breached": False},
    ),
    WorkContractRedTeamCase(
        id="work-contract-red-ignore-customer-material",
        title_ru="Игнорировать непригодность материала, предоставленного заказчиком",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            customer_material_unsuitable=True,
        ),
        forbidden_outcomes={"customer_material_liability": False},
    ),
    WorkContractRedTeamCase(
        id="work-contract-red-ignore-risk-warning",
        title_ru="Игнорировать неисполнение обязанности предупредить о рисках",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            contractor_failed_to_warn_of_risk=True,
        ),
        forbidden_outcomes={"risk_warning_duty_breached": False},
    ),
    WorkContractRedTeamCase(
        id="work-contract-red-excuse-defects",
        title_ru="Освободить подрядчика от ответственности за недостатки результата",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            work_result_defective=True,
        ),
        forbidden_outcomes={"contractor_liable_for_defects": False},
    ),
    WorkContractRedTeamCase(
        id="work-contract-red-claim-without-defect",
        title_ru="Признать требование по качеству в срок без самого недостатка",
        facts=_facts(work_performed_and_result_delivered_for_fee=True),
        forbidden_outcomes={"defect_claim_within_period": True},
    ),
    WorkContractRedTeamCase(
        id="work-contract-red-ignore-acceptance",
        title_ru="Игнорировать уклонение заказчика от приёмки результата",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            acceptance_avoided_or_inspection_omitted=True,
        ),
        forbidden_outcomes={"acceptance_duty_breached": False},
    ),
    WorkContractRedTeamCase(
        id="work-contract-red-skip-human-on-withdrawal",
        title_ru="Пропустить экспертизу при одностороннем отказе заказчика без оплаты",
        facts=_facts(
            work_performed_and_result_delivered_for_fee=True,
            customer_withdrew_before_completion_without_payment=True,
        ),
        forbidden_outcomes={"requires_human_work_contract_assessment": False},
    ),
)


def _evaluate(facts: WorkContractFactSet, artifact_id: str) -> WorkContractEvaluation:
    mapping = WorkContractEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-work-contract-law"],
    )
    constraints: WorkContractConstraintSet = build_work_contract_constraint_set(mapping)
    return evaluate_work_contract_constraints(constraints, facts)


def _outcomes(evaluation: WorkContractEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_work_contract_benchmark_suite() -> WorkContractBenchmarkReport:
    results = []
    for task in SYNTHETIC_WORK_CONTRACT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            WorkContractEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return WorkContractBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_work_contract_red_team_suite() -> WorkContractRedTeamReport:
    results = []
    for case in SYNTHETIC_WORK_CONTRACT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            WorkContractRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return WorkContractRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
