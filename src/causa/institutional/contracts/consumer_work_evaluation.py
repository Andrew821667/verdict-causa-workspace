from pydantic import BaseModel, Field

from causa.institutional.contracts.consumer_work import (
    ConsumerWorkConstraintSet,
    ConsumerWorkEvaluation,
    ConsumerWorkEvidenceMappingResult,
    ConsumerWorkFactSet,
    build_consumer_work_constraint_set,
    evaluate_consumer_work_constraints,
)


class ConsumerWorkEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ConsumerWorkFactSet
    expected_outcomes: dict[str, bool]


class ConsumerWorkEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ConsumerWorkBenchmarkReport(BaseModel):
    id: str = "consumer-work-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ConsumerWorkEvaluationResult] = Field(default_factory=list)


class ConsumerWorkRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ConsumerWorkFactSet
    forbidden_outcomes: dict[str, bool]


class ConsumerWorkRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ConsumerWorkRedTeamReport(BaseModel):
    id: str = "consumer-work-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ConsumerWorkRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ConsumerWorkFactSet:
    values = {field_name: False for field_name in ConsumerWorkFactSet.model_fields}
    values.update(updates)
    return ConsumerWorkFactSet(**values)


SYNTHETIC_CONSUMER_WORK_BENCHMARKS = (
    ConsumerWorkEvaluationTask(
        id="consumer-work-bench-not-qualified",
        title_ru="Работа не выполняется для личных потребностей гражданина",
        facts=_facts(work_result_has_significant_defect=True),
        expected_outcomes={"consumer_work_qualified": False},
    ),
    ConsumerWorkEvaluationTask(
        id="consumer-work-bench-qualified-clean",
        title_ru="Договор бытового подряда без нарушений",
        facts=_facts(work_for_personal_consumer_needs=True),
        expected_outcomes={
            "consumer_work_qualified": True,
            "requires_human_consumer_work_assessment": False,
        },
    ),
    ConsumerWorkEvaluationTask(
        id="consumer-work-bench-imposed-work",
        title_ru="Заказчику навязана дополнительная работа без его согласия",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            additional_work_imposed_without_consent=True,
        ),
        expected_outcomes={
            "imposed_additional_work_not_payable": True,
            "requires_human_consumer_work_assessment": True,
        },
    ),
    ConsumerWorkEvaluationTask(
        id="consumer-work-bench-withdrawal-denied",
        title_ru="Заказчику отказано в праве прекратить договор до сдачи работы",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            withdrawal_right_before_delivery_denied=True,
        ),
        expected_outcomes={
            "withdrawal_right_denied": True,
            "requires_human_consumer_work_assessment": True,
        },
    ),
    ConsumerWorkEvaluationTask(
        id="consumer-work-bench-information",
        title_ru="Заказчику не предоставлена информация о работе, её цене и форме оплаты",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            consumer_information_not_provided=True,
        ),
        expected_outcomes={
            "consumer_information_duty_breached": True,
            "requires_human_consumer_work_assessment": True,
        },
    ),
    ConsumerWorkEvaluationTask(
        id="consumer-work-bench-contractor-material",
        title_ru="Работа выполнена из недоброкачественного материала подрядчика",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            contractor_material_defective=True,
        ),
        expected_outcomes={
            "contractor_material_liability": True,
            "requires_human_consumer_work_assessment": True,
        },
    ),
    ConsumerWorkEvaluationTask(
        id="consumer-work-bench-payment-order",
        title_ru="Оплата потребована до сдачи работы без согласия заказчика",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            payment_demanded_before_acceptance_without_consent=True,
        ),
        expected_outcomes={
            "payment_order_breached": True,
            "requires_human_consumer_work_assessment": True,
        },
    ),
    ConsumerWorkEvaluationTask(
        id="consumer-work-bench-operation-information",
        title_ru="При сдаче работы не сообщены требования к использованию результата",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            operation_information_not_provided=True,
        ),
        expected_outcomes={
            "operation_information_duty_breached": True,
            "requires_human_consumer_work_assessment": True,
        },
    ),
    ConsumerWorkEvaluationTask(
        id="consumer-work-bench-ten-year-defect",
        title_ru="Существенный недостаток обнаружен в пределах десяти лет",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            work_result_has_significant_defect=True,
            significant_defect_found_within_ten_years=True,
        ),
        expected_outcomes={
            "significant_defect_remedy_available": True,
            "ten_year_claim_available": True,
            "requires_human_consumer_work_assessment": True,
        },
    ),
    ConsumerWorkEvaluationTask(
        id="consumer-work-bench-sale-notice",
        title_ru="Результат работы продан без двухмесячного предупреждения заказчика",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            result_sold_without_two_month_notice=True,
        ),
        expected_outcomes={
            "sale_notice_period_breached": True,
            "requires_human_consumer_work_assessment": True,
        },
    ),
)


SYNTHETIC_CONSUMER_WORK_RED_TEAM_CASES = (
    ConsumerWorkRedTeamCase(
        id="consumer-work-red-qualify-without-personal-needs",
        title_ru="Квалифицировать бытовой подряд без личных потребностей гражданина",
        facts=_facts(work_result_has_significant_defect=True),
        forbidden_outcomes={"consumer_work_qualified": True},
    ),
    ConsumerWorkRedTeamCase(
        id="consumer-work-red-allow-imposed-work",
        title_ru="Считать правомерным навязывание дополнительной работы",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            additional_work_imposed_without_consent=True,
        ),
        forbidden_outcomes={"imposed_additional_work_not_payable": False},
    ),
    ConsumerWorkRedTeamCase(
        id="consumer-work-red-allow-withdrawal-denial",
        title_ru="Признать допустимым лишение заказчика права прекратить договор",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            withdrawal_right_before_delivery_denied=True,
        ),
        forbidden_outcomes={"withdrawal_right_denied": False},
    ),
    ConsumerWorkRedTeamCase(
        id="consumer-work-red-ignore-information",
        title_ru="Игнорировать непредоставление информации о работе",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            consumer_information_not_provided=True,
        ),
        forbidden_outcomes={"consumer_information_duty_breached": False},
    ),
    ConsumerWorkRedTeamCase(
        id="consumer-work-red-excuse-contractor-material",
        title_ru="Освободить подрядчика от ответственности за свой недоброкачественный материал",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            contractor_material_defective=True,
        ),
        forbidden_outcomes={"contractor_material_liability": False},
    ),
    ConsumerWorkRedTeamCase(
        id="consumer-work-red-ignore-payment-order",
        title_ru="Игнорировать требование оплаты до сдачи работы без согласия заказчика",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            payment_demanded_before_acceptance_without_consent=True,
        ),
        forbidden_outcomes={"payment_order_breached": False},
    ),
    ConsumerWorkRedTeamCase(
        id="consumer-work-red-ignore-operation-information",
        title_ru="Игнорировать несообщение требований к использованию результата",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            operation_information_not_provided=True,
        ),
        forbidden_outcomes={"operation_information_duty_breached": False},
    ),
    ConsumerWorkRedTeamCase(
        id="consumer-work-red-claim-without-defect",
        title_ru="Признать десятилетнее требование без существенного недостатка",
        facts=_facts(work_for_personal_consumer_needs=True),
        forbidden_outcomes={"ten_year_claim_available": True},
    ),
    ConsumerWorkRedTeamCase(
        id="consumer-work-red-ignore-sale-notice",
        title_ru="Игнорировать продажу результата без двухмесячного предупреждения",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            result_sold_without_two_month_notice=True,
        ),
        forbidden_outcomes={"sale_notice_period_breached": False},
    ),
    ConsumerWorkRedTeamCase(
        id="consumer-work-red-skip-human-on-significant-defect",
        title_ru="Пропустить экспертизу при существенном недостатке результата работы",
        facts=_facts(
            work_for_personal_consumer_needs=True,
            work_result_has_significant_defect=True,
        ),
        forbidden_outcomes={"requires_human_consumer_work_assessment": False},
    ),
)


def _evaluate(facts: ConsumerWorkFactSet, artifact_id: str) -> ConsumerWorkEvaluation:
    mapping = ConsumerWorkEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-consumer-work-law"],
    )
    constraints: ConsumerWorkConstraintSet = build_consumer_work_constraint_set(mapping)
    return evaluate_consumer_work_constraints(constraints, facts)


def _outcomes(evaluation: ConsumerWorkEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_consumer_work_benchmark_suite() -> ConsumerWorkBenchmarkReport:
    results = []
    for task in SYNTHETIC_CONSUMER_WORK_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ConsumerWorkEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ConsumerWorkBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_consumer_work_red_team_suite() -> ConsumerWorkRedTeamReport:
    results = []
    for case in SYNTHETIC_CONSUMER_WORK_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ConsumerWorkRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ConsumerWorkRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
