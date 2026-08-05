from pydantic import BaseModel, Field

from causa.institutional.contracts.insurance_settlement import (
    InsuranceSettlementConstraintSet,
    InsuranceSettlementEvaluation,
    InsuranceSettlementEvidenceMappingResult,
    InsuranceSettlementFactSet,
    build_insurance_settlement_constraint_set,
    evaluate_insurance_settlement_constraints,
)


class InsuranceSettlementEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: InsuranceSettlementFactSet
    expected_outcomes: dict[str, bool]


class InsuranceSettlementEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class InsuranceSettlementBenchmarkReport(BaseModel):
    id: str = "insurance-settlement-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[InsuranceSettlementEvaluationResult] = Field(default_factory=list)


class InsuranceSettlementRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: InsuranceSettlementFactSet
    forbidden_outcomes: dict[str, bool]


class InsuranceSettlementRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class InsuranceSettlementRedTeamReport(BaseModel):
    id: str = "insurance-settlement-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[InsuranceSettlementRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> InsuranceSettlementFactSet:
    values = {field_name: False for field_name in InsuranceSettlementFactSet.model_fields}
    values.update(updates)
    return InsuranceSettlementFactSet(**values)


SYNTHETIC_INSURANCE_SETTLEMENT_BENCHMARKS = (
    InsuranceSettlementEvaluationTask(
        id="insurance-settlement-bench-not-qualified",
        title_ru="Исполнение страхового обязательства не установлено",
        facts=_facts(insured_sum_rules_breached=True),
        expected_outcomes={"insurance_settlement_qualified": False},
    ),
    InsuranceSettlementEvaluationTask(
        id="insurance-settlement-bench-qualified-clean",
        title_ru="Исполнение страхового обязательства без нарушений",
        facts=_facts(insured_event_settlement_started=True),
        expected_outcomes={
            "insurance_settlement_qualified": True,
            "requires_human_insurance_settlement_assessment": False,
        },
    ),
    InsuranceSettlementEvaluationTask(
        id="insurance-settlement-bench-disclosure",
        title_ru="Существенные сведения при заключении договора не сообщены",
        facts=_facts(
            insured_event_settlement_started=True,
            material_information_not_disclosed=True,
        ),
        expected_outcomes={
            "disclosure_duty_breached": True,
            "requires_human_insurance_settlement_assessment": True,
        },
    ),
    InsuranceSettlementEvaluationTask(
        id="insurance-settlement-bench-insured-sum",
        title_ru="Нарушены правила о страховой сумме и страховой стоимости",
        facts=_facts(
            insured_event_settlement_started=True,
            insured_sum_rules_breached=True,
        ),
        expected_outcomes={
            "insured_sum_duty_breached": True,
            "requires_human_insurance_settlement_assessment": True,
        },
    ),
    InsuranceSettlementEvaluationTask(
        id="insurance-settlement-bench-premium",
        title_ru="Нарушены порядок и сроки уплаты страховой премии",
        facts=_facts(
            insured_event_settlement_started=True,
            premium_payment_rules_breached=True,
        ),
        expected_outcomes={
            "premium_duty_breached": True,
            "requires_human_insurance_settlement_assessment": True,
        },
    ),
    InsuranceSettlementEvaluationTask(
        id="insurance-settlement-bench-risk-increase",
        title_ru="Нарушены правила об увеличении страхового риска и прекращении договора",
        facts=_facts(
            insured_event_settlement_started=True,
            risk_increase_or_early_termination_breached=True,
        ),
        expected_outcomes={
            "risk_and_termination_duty_breached": True,
            "requires_human_insurance_settlement_assessment": True,
        },
    ),
    InsuranceSettlementEvaluationTask(
        id="insurance-settlement-bench-notice",
        title_ru="Уведомление о страховом случае не дано, последствия не применены",
        facts=_facts(
            insured_event_settlement_started=True,
            insured_event_notice_not_given=True,
            notice_delay_consequences_not_applied=True,
        ),
        expected_outcomes={
            "insured_event_notice_duty_breached": True,
            "notice_delay_consequences_breached": True,
            "requires_human_insurance_settlement_assessment": True,
        },
    ),
    InsuranceSettlementEvaluationTask(
        id="insurance-settlement-bench-loss-mitigation",
        title_ru="Меры по уменьшению убытков от страхового случая не приняты",
        facts=_facts(
            insured_event_settlement_started=True,
            loss_mitigation_duty_breached=True,
        ),
        expected_outcomes={
            "loss_mitigation_breached": True,
            "requires_human_insurance_settlement_assessment": True,
        },
    ),
    InsuranceSettlementEvaluationTask(
        id="insurance-settlement-bench-insurer-release",
        title_ru="Основания освобождения страховщика применены неверно",
        facts=_facts(
            insured_event_settlement_started=True,
            insurer_release_grounds_misapplied=True,
        ),
        expected_outcomes={
            "insurer_release_duty_breached": True,
            "requires_human_insurance_settlement_assessment": True,
        },
    ),
    InsuranceSettlementEvaluationTask(
        id="insurance-settlement-bench-subrogation",
        title_ru="Нарушены правила о суброгации и исковой давности",
        facts=_facts(
            insured_event_settlement_started=True,
            subrogation_or_limitation_rules_breached=True,
        ),
        expected_outcomes={
            "subrogation_and_limitation_breached": True,
            "requires_human_insurance_settlement_assessment": True,
        },
    ),
)


SYNTHETIC_INSURANCE_SETTLEMENT_RED_TEAM_CASES = (
    InsuranceSettlementRedTeamCase(
        id="insurance-settlement-red-qualify-without-event",
        title_ru="Квалифицировать исполнение страхового обязательства без страхового случая",
        facts=_facts(insured_sum_rules_breached=True),
        forbidden_outcomes={"insurance_settlement_qualified": True},
    ),
    InsuranceSettlementRedTeamCase(
        id="insurance-settlement-red-ignore-disclosure",
        title_ru="Игнорировать несообщение существенных сведений страховщику",
        facts=_facts(
            insured_event_settlement_started=True,
            material_information_not_disclosed=True,
        ),
        forbidden_outcomes={"disclosure_duty_breached": False},
    ),
    InsuranceSettlementRedTeamCase(
        id="insurance-settlement-red-ignore-insured-sum",
        title_ru="Игнорировать превышение страховой суммы над страховой стоимостью",
        facts=_facts(
            insured_event_settlement_started=True,
            insured_sum_rules_breached=True,
        ),
        forbidden_outcomes={"insured_sum_duty_breached": False},
    ),
    InsuranceSettlementRedTeamCase(
        id="insurance-settlement-red-ignore-premium",
        title_ru="Игнорировать нарушение порядка уплаты страховой премии",
        facts=_facts(
            insured_event_settlement_started=True,
            premium_payment_rules_breached=True,
        ),
        forbidden_outcomes={"premium_duty_breached": False},
    ),
    InsuranceSettlementRedTeamCase(
        id="insurance-settlement-red-ignore-risk-increase",
        title_ru="Игнорировать несообщение об увеличении страхового риска",
        facts=_facts(
            insured_event_settlement_started=True,
            risk_increase_or_early_termination_breached=True,
        ),
        forbidden_outcomes={"risk_and_termination_duty_breached": False},
    ),
    InsuranceSettlementRedTeamCase(
        id="insurance-settlement-red-ignore-notice",
        title_ru="Игнорировать отсутствие уведомления о страховом случае",
        facts=_facts(
            insured_event_settlement_started=True,
            insured_event_notice_not_given=True,
        ),
        forbidden_outcomes={"insured_event_notice_duty_breached": False},
    ),
    InsuranceSettlementRedTeamCase(
        id="insurance-settlement-red-consequences-without-notice-breach",
        title_ru="Признать последствия просрочки уведомления без нарушения уведомления",
        facts=_facts(insured_event_settlement_started=True),
        forbidden_outcomes={"notice_delay_consequences_breached": True},
    ),
    InsuranceSettlementRedTeamCase(
        id="insurance-settlement-red-ignore-loss-mitigation",
        title_ru="Освободить страхователя от мер по уменьшению убытков",
        facts=_facts(
            insured_event_settlement_started=True,
            loss_mitigation_duty_breached=True,
        ),
        forbidden_outcomes={"loss_mitigation_breached": False},
    ),
    InsuranceSettlementRedTeamCase(
        id="insurance-settlement-red-ignore-insurer-release",
        title_ru="Игнорировать неверное применение оснований освобождения страховщика",
        facts=_facts(
            insured_event_settlement_started=True,
            insurer_release_grounds_misapplied=True,
        ),
        forbidden_outcomes={"insurer_release_duty_breached": False},
    ),
    InsuranceSettlementRedTeamCase(
        id="insurance-settlement-red-skip-human-on-subrogation",
        title_ru="Пропустить экспертизу при нарушении суброгации и исковой давности",
        facts=_facts(
            insured_event_settlement_started=True,
            subrogation_or_limitation_rules_breached=True,
        ),
        forbidden_outcomes={"requires_human_insurance_settlement_assessment": False},
    ),
)


def _evaluate(facts: InsuranceSettlementFactSet, artifact_id: str) -> InsuranceSettlementEvaluation:
    mapping = InsuranceSettlementEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-insurance-settlement-law"],
    )
    constraints: InsuranceSettlementConstraintSet = build_insurance_settlement_constraint_set(
        mapping
    )
    return evaluate_insurance_settlement_constraints(constraints, facts)


def _outcomes(evaluation: InsuranceSettlementEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_insurance_settlement_benchmark_suite() -> InsuranceSettlementBenchmarkReport:
    results = []
    for task in SYNTHETIC_INSURANCE_SETTLEMENT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            InsuranceSettlementEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return InsuranceSettlementBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_insurance_settlement_red_team_suite() -> InsuranceSettlementRedTeamReport:
    results = []
    for case in SYNTHETIC_INSURANCE_SETTLEMENT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            InsuranceSettlementRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return InsuranceSettlementRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
