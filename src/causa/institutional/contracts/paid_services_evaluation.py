from pydantic import BaseModel, Field

from causa.institutional.contracts.paid_services import (
    PaidServicesConstraintSet,
    PaidServicesEvaluation,
    PaidServicesEvidenceMappingResult,
    PaidServicesFactSet,
    build_paid_services_constraint_set,
    evaluate_paid_services_constraints,
)


class PaidServicesEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: PaidServicesFactSet
    expected_outcomes: dict[str, bool]


class PaidServicesEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PaidServicesBenchmarkReport(BaseModel):
    id: str = "paid-services-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[PaidServicesEvaluationResult] = Field(default_factory=list)


class PaidServicesRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: PaidServicesFactSet
    forbidden_outcomes: dict[str, bool]


class PaidServicesRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PaidServicesRedTeamReport(BaseModel):
    id: str = "paid-services-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[PaidServicesRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> PaidServicesFactSet:
    values = {field_name: False for field_name in PaidServicesFactSet.model_fields}
    values.update(updates)
    return PaidServicesFactSet(**values)


SYNTHETIC_PAID_SERVICES_BENCHMARKS = (
    PaidServicesEvaluationTask(
        id="paid-services-bench-not-qualified",
        title_ru="Услуги по заданию заказчика за плату не оказываются",
        facts=_facts(payment_terms_or_deadline_breached=True),
        expected_outcomes={"paid_services_qualified": False},
    ),
    PaidServicesEvaluationTask(
        id="paid-services-bench-qualified-clean",
        title_ru="Договор возмездного оказания услуг без нарушений",
        facts=_facts(services_rendered_for_fee_by_assignment=True),
        expected_outcomes={
            "paid_services_qualified": True,
            "requires_human_paid_services_assessment": False,
        },
    ),
    PaidServicesEvaluationTask(
        id="paid-services-bench-special-chapter",
        title_ru="Услуги оказываются по договору, предусмотренному отдельной главой Кодекса",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            contract_covered_by_special_chapter=True,
        ),
        expected_outcomes={
            "special_chapter_exclusion_applies": True,
            "requires_human_paid_services_assessment": True,
        },
    ),
    PaidServicesEvaluationTask(
        id="paid-services-bench-personal-performance",
        title_ru="Услуги оказаны третьим лицом вопреки условиям договора",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            third_party_performed_without_contract_permission=True,
        ),
        expected_outcomes={
            "personal_performance_duty_breached": True,
            "requires_human_paid_services_assessment": True,
        },
    ),
    PaidServicesEvaluationTask(
        id="paid-services-bench-payment",
        title_ru="Услуги не оплачены в сроки и порядке, указанные в договоре",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            payment_terms_or_deadline_breached=True,
        ),
        expected_outcomes={
            "payment_duty_breached": True,
            "requires_human_paid_services_assessment": True,
        },
    ),
    PaidServicesEvaluationTask(
        id="paid-services-bench-customer-fault",
        title_ru="Невозможность исполнения возникла по вине заказчика",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            impossibility_caused_by_customer=True,
        ),
        expected_outcomes={
            "customer_fault_full_payment_due": True,
            "requires_human_paid_services_assessment": True,
        },
    ),
    PaidServicesEvaluationTask(
        id="paid-services-bench-no-fault-expenses",
        title_ru="Расходы исполнителя не возмещены при невозможности без вины сторон",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            impossibility_without_party_fault=True,
            actual_expenses_not_reimbursed=True,
        ),
        expected_outcomes={
            "no_fault_impossibility_established": True,
            "actual_expenses_reimbursement_due": True,
            "requires_human_paid_services_assessment": True,
        },
    ),
    PaidServicesEvaluationTask(
        id="paid-services-bench-customer-withdrawal",
        title_ru="Заказчик отказался от договора без оплаты фактических расходов",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            customer_withdrew_without_covering_expenses=True,
        ),
        expected_outcomes={
            "customer_withdrawal_expenses_due": True,
            "requires_human_paid_services_assessment": True,
        },
    ),
    PaidServicesEvaluationTask(
        id="paid-services-bench-performer-withdrawal",
        title_ru="Исполнитель отказался от договора без полного возмещения убытков",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            performer_withdrew_without_full_compensation=True,
        ),
        expected_outcomes={
            "performer_withdrawal_compensation_due": True,
            "requires_human_paid_services_assessment": True,
        },
    ),
    PaidServicesEvaluationTask(
        id="paid-services-bench-communication",
        title_ru="Нарушены правила приостановления оказания услуг связи",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            communication_suspension_rules_breached=True,
        ),
        expected_outcomes={
            "communication_suspension_breached": True,
            "requires_human_paid_services_assessment": True,
        },
    ),
)


SYNTHETIC_PAID_SERVICES_RED_TEAM_CASES = (
    PaidServicesRedTeamCase(
        id="paid-services-red-qualify-without-services",
        title_ru="Квалифицировать возмездное оказание услуг без оказания услуг за плату",
        facts=_facts(payment_terms_or_deadline_breached=True),
        forbidden_outcomes={"paid_services_qualified": True},
    ),
    PaidServicesRedTeamCase(
        id="paid-services-red-ignore-special-chapter",
        title_ru="Игнорировать исключение услуг, урегулированных отдельной главой",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            contract_covered_by_special_chapter=True,
        ),
        forbidden_outcomes={"special_chapter_exclusion_applies": False},
    ),
    PaidServicesRedTeamCase(
        id="paid-services-red-allow-third-party",
        title_ru="Признать допустимым оказание услуг третьим лицом вопреки договору",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            third_party_performed_without_contract_permission=True,
        ),
        forbidden_outcomes={"personal_performance_duty_breached": False},
    ),
    PaidServicesRedTeamCase(
        id="paid-services-red-ignore-payment",
        title_ru="Игнорировать нарушение сроков и порядка оплаты услуг",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            payment_terms_or_deadline_breached=True,
        ),
        forbidden_outcomes={"payment_duty_breached": False},
    ),
    PaidServicesRedTeamCase(
        id="paid-services-red-ignore-customer-fault",
        title_ru="Игнорировать вину заказчика в невозможности исполнения",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            impossibility_caused_by_customer=True,
        ),
        forbidden_outcomes={"customer_fault_full_payment_due": False},
    ),
    PaidServicesRedTeamCase(
        id="paid-services-red-expenses-without-impossibility",
        title_ru="Признать возмещение расходов без невозможности исполнения",
        facts=_facts(services_rendered_for_fee_by_assignment=True),
        forbidden_outcomes={"actual_expenses_reimbursement_due": True},
    ),
    PaidServicesRedTeamCase(
        id="paid-services-red-ignore-customer-withdrawal",
        title_ru="Игнорировать отказ заказчика без оплаты фактических расходов",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            customer_withdrew_without_covering_expenses=True,
        ),
        forbidden_outcomes={"customer_withdrawal_expenses_due": False},
    ),
    PaidServicesRedTeamCase(
        id="paid-services-red-ignore-performer-withdrawal",
        title_ru="Игнорировать отказ исполнителя без полного возмещения убытков",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            performer_withdrew_without_full_compensation=True,
        ),
        forbidden_outcomes={"performer_withdrawal_compensation_due": False},
    ),
    PaidServicesRedTeamCase(
        id="paid-services-red-ignore-communication-rules",
        title_ru="Игнорировать нарушение правил приостановления услуг связи",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            communication_suspension_rules_breached=True,
        ),
        forbidden_outcomes={"communication_suspension_breached": False},
    ),
    PaidServicesRedTeamCase(
        id="paid-services-red-skip-human-on-no-fault-impossibility",
        title_ru="Пропустить экспертизу при невозможности исполнения без вины сторон",
        facts=_facts(
            services_rendered_for_fee_by_assignment=True,
            impossibility_without_party_fault=True,
        ),
        forbidden_outcomes={"requires_human_paid_services_assessment": False},
    ),
)


def _evaluate(facts: PaidServicesFactSet, artifact_id: str) -> PaidServicesEvaluation:
    mapping = PaidServicesEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-paid-services-law"],
    )
    constraints: PaidServicesConstraintSet = build_paid_services_constraint_set(mapping)
    return evaluate_paid_services_constraints(constraints, facts)


def _outcomes(evaluation: PaidServicesEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_paid_services_benchmark_suite() -> PaidServicesBenchmarkReport:
    results = []
    for task in SYNTHETIC_PAID_SERVICES_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            PaidServicesEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return PaidServicesBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_paid_services_red_team_suite() -> PaidServicesRedTeamReport:
    results = []
    for case in SYNTHETIC_PAID_SERVICES_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            PaidServicesRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return PaidServicesRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
