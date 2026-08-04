from pydantic import BaseModel, Field

from causa.institutional.contracts.settlements import (
    SettlementsConstraintSet,
    SettlementsEvaluation,
    SettlementsEvidenceMappingResult,
    SettlementsFactSet,
    build_settlements_constraint_set,
    evaluate_settlements_constraints,
)


class SettlementsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: SettlementsFactSet
    expected_outcomes: dict[str, bool]


class SettlementsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SettlementsBenchmarkReport(BaseModel):
    id: str = "settlements-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[SettlementsEvaluationResult] = Field(default_factory=list)


class SettlementsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: SettlementsFactSet
    forbidden_outcomes: dict[str, bool]


class SettlementsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SettlementsRedTeamReport(BaseModel):
    id: str = "settlements-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[SettlementsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> SettlementsFactSet:
    values = {field_name: False for field_name in SettlementsFactSet.model_fields}
    values.update(updates)
    return SettlementsFactSet(**values)


SYNTHETIC_SETTLEMENTS_BENCHMARKS = (
    SettlementsEvaluationTask(
        id="settlements-bench-not-qualified",
        title_ru="Безналичные расчёты по обязательству не осуществлялись",
        facts=_facts(cheque_requisites_breached=True),
        expected_outcomes={"cashless_settlements_qualified": False},
    ),
    SettlementsEvaluationTask(
        id="settlements-bench-qualified-clean",
        title_ru="Безналичные расчёты без нарушений",
        facts=_facts(cashless_settlements_performed=True),
        expected_outcomes={
            "cashless_settlements_qualified": True,
            "requires_human_settlements_assessment": False,
        },
    ),
    SettlementsEvaluationTask(
        id="settlements-bench-form-legality",
        title_ru="Использована форма расчётов, не предусмотренная законом",
        facts=_facts(
            cashless_settlements_performed=True,
            settlement_form_not_provided_by_law=True,
        ),
        expected_outcomes={
            "settlement_form_legality_breached": True,
            "requires_human_settlements_assessment": True,
        },
    ),
    SettlementsEvaluationTask(
        id="settlements-bench-payment-order",
        title_ru="Платёжное поручение не исполнено, ответственность банка не применена",
        facts=_facts(
            cashless_settlements_performed=True,
            payment_order_execution_breached=True,
            payment_order_liability_not_applied=True,
        ),
        expected_outcomes={
            "payment_order_execution_duty_breached": True,
            "payment_order_liability_breached": True,
            "requires_human_settlements_assessment": True,
        },
    ),
    SettlementsEvaluationTask(
        id="settlements-bench-letter-of-credit",
        title_ru="Условия аккредитива и порядок его исполнения нарушены",
        facts=_facts(
            cashless_settlements_performed=True,
            letter_of_credit_terms_breached=True,
        ),
        expected_outcomes={
            "letter_of_credit_duty_breached": True,
            "requires_human_settlements_assessment": True,
        },
    ),
    SettlementsEvaluationTask(
        id="settlements-bench-letter-of-credit-closure",
        title_ru="Правила закрытия аккредитива нарушены",
        facts=_facts(
            cashless_settlements_performed=True,
            letter_of_credit_closure_rules_breached=True,
        ),
        expected_outcomes={
            "letter_of_credit_closure_duty_breached": True,
            "requires_human_settlements_assessment": True,
        },
    ),
    SettlementsEvaluationTask(
        id="settlements-bench-collection",
        title_ru="Инкассовое поручение исполнено с нарушением",
        facts=_facts(
            cashless_settlements_performed=True,
            collection_order_execution_breached=True,
        ),
        expected_outcomes={
            "collection_execution_duty_breached": True,
            "requires_human_settlements_assessment": True,
        },
    ),
    SettlementsEvaluationTask(
        id="settlements-bench-cheque-requisites",
        title_ru="В документе отсутствуют обязательные реквизиты чека",
        facts=_facts(
            cashless_settlements_performed=True,
            cheque_requisites_breached=True,
        ),
        expected_outcomes={
            "cheque_requisites_duty_breached": True,
            "requires_human_settlements_assessment": True,
        },
    ),
    SettlementsEvaluationTask(
        id="settlements-bench-cheque-payment",
        title_ru="Нарушены порядок оплаты чека и гарантия платежа",
        facts=_facts(
            cashless_settlements_performed=True,
            cheque_payment_and_warranty_breached=True,
        ),
        expected_outcomes={
            "cheque_payment_duty_breached": True,
            "requires_human_settlements_assessment": True,
        },
    ),
    SettlementsEvaluationTask(
        id="settlements-bench-cheque-non-payment",
        title_ru="Отказ от оплаты чека удостоверен с нарушением",
        facts=_facts(
            cashless_settlements_performed=True,
            cheque_non_payment_certification_breached=True,
        ),
        expected_outcomes={
            "cheque_non_payment_certification_duty_breached": True,
            "requires_human_settlements_assessment": True,
        },
    ),
)


SYNTHETIC_SETTLEMENTS_RED_TEAM_CASES = (
    SettlementsRedTeamCase(
        id="settlements-red-qualify-without-cashless",
        title_ru="Квалифицировать безналичные расчёты без их осуществления",
        facts=_facts(cheque_requisites_breached=True),
        forbidden_outcomes={"cashless_settlements_qualified": True},
    ),
    SettlementsRedTeamCase(
        id="settlements-red-ignore-form-legality",
        title_ru="Признать допустимой форму расчётов, не предусмотренную законом",
        facts=_facts(
            cashless_settlements_performed=True,
            settlement_form_not_provided_by_law=True,
        ),
        forbidden_outcomes={"settlement_form_legality_breached": False},
    ),
    SettlementsRedTeamCase(
        id="settlements-red-ignore-payment-order",
        title_ru="Игнорировать неисполнение платёжного поручения",
        facts=_facts(
            cashless_settlements_performed=True,
            payment_order_execution_breached=True,
        ),
        forbidden_outcomes={"payment_order_execution_duty_breached": False},
    ),
    SettlementsRedTeamCase(
        id="settlements-red-liability-without-execution-breach",
        title_ru="Признать ответственность банка без нарушения исполнения поручения",
        facts=_facts(cashless_settlements_performed=True),
        forbidden_outcomes={"payment_order_liability_breached": True},
    ),
    SettlementsRedTeamCase(
        id="settlements-red-ignore-letter-of-credit",
        title_ru="Игнорировать нарушение условий аккредитива",
        facts=_facts(
            cashless_settlements_performed=True,
            letter_of_credit_terms_breached=True,
        ),
        forbidden_outcomes={"letter_of_credit_duty_breached": False},
    ),
    SettlementsRedTeamCase(
        id="settlements-red-ignore-letter-of-credit-closure",
        title_ru="Игнорировать нарушение правил закрытия аккредитива",
        facts=_facts(
            cashless_settlements_performed=True,
            letter_of_credit_closure_rules_breached=True,
        ),
        forbidden_outcomes={"letter_of_credit_closure_duty_breached": False},
    ),
    SettlementsRedTeamCase(
        id="settlements-red-ignore-collection",
        title_ru="Игнорировать нарушение исполнения инкассового поручения",
        facts=_facts(
            cashless_settlements_performed=True,
            collection_order_execution_breached=True,
        ),
        forbidden_outcomes={"collection_execution_duty_breached": False},
    ),
    SettlementsRedTeamCase(
        id="settlements-red-uphold-cheque-without-requisites",
        title_ru="Признать силу чека при отсутствии обязательных реквизитов",
        facts=_facts(
            cashless_settlements_performed=True,
            cheque_requisites_breached=True,
        ),
        forbidden_outcomes={"cheque_requisites_duty_breached": False},
    ),
    SettlementsRedTeamCase(
        id="settlements-red-ignore-cheque-payment",
        title_ru="Игнорировать нарушение порядка оплаты чека и гарантии платежа",
        facts=_facts(
            cashless_settlements_performed=True,
            cheque_payment_and_warranty_breached=True,
        ),
        forbidden_outcomes={"cheque_payment_duty_breached": False},
    ),
    SettlementsRedTeamCase(
        id="settlements-red-skip-human-on-cheque-non-payment",
        title_ru="Пропустить экспертизу при нарушении удостоверения отказа от оплаты чека",
        facts=_facts(
            cashless_settlements_performed=True,
            cheque_non_payment_certification_breached=True,
        ),
        forbidden_outcomes={"requires_human_settlements_assessment": False},
    ),
)


def _evaluate(facts: SettlementsFactSet, artifact_id: str) -> SettlementsEvaluation:
    mapping = SettlementsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-settlements-law"],
    )
    constraints: SettlementsConstraintSet = build_settlements_constraint_set(mapping)
    return evaluate_settlements_constraints(constraints, facts)


def _outcomes(evaluation: SettlementsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_settlements_benchmark_suite() -> SettlementsBenchmarkReport:
    results = []
    for task in SYNTHETIC_SETTLEMENTS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            SettlementsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return SettlementsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_settlements_red_team_suite() -> SettlementsRedTeamReport:
    results = []
    for case in SYNTHETIC_SETTLEMENTS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            SettlementsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return SettlementsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
