from pydantic import BaseModel, Field

from causa.institutional.contracts.credit import (
    CreditConstraintSet,
    CreditEvaluation,
    CreditEvidenceMappingResult,
    CreditFactSet,
    build_credit_constraint_set,
    evaluate_credit_constraints,
)


class CreditEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: CreditFactSet
    expected_outcomes: dict[str, bool]


class CreditEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CreditBenchmarkReport(BaseModel):
    id: str = "credit-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[CreditEvaluationResult] = Field(default_factory=list)


class CreditRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: CreditFactSet
    forbidden_outcomes: dict[str, bool]


class CreditRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CreditRedTeamReport(BaseModel):
    id: str = "credit-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[CreditRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> CreditFactSet:
    values = {field_name: False for field_name in CreditFactSet.model_fields}
    values.update(updates)
    return CreditFactSet(**values)


SYNTHETIC_CREDIT_BENCHMARKS = (
    CreditEvaluationTask(
        id="credit-bench-not-qualified",
        title_ru="Денежные средства с обязанностью возврата и уплаты процентов не предоставлены",
        facts=_facts(interest_or_other_payments_terms_breached=True),
        expected_outcomes={"credit_qualified": False},
    ),
    CreditEvaluationTask(
        id="credit-bench-qualified-clean",
        title_ru="Кредитный договор без нарушений",
        facts=_facts(credit_provided_for_return_with_interest=True),
        expected_outcomes={
            "credit_qualified": True,
            "requires_human_credit_assessment": False,
        },
    ),
    CreditEvaluationTask(
        id="credit-bench-lender-status",
        title_ru="Кредитором выступает лицо, не являющееся кредитной организацией",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            lender_not_a_credit_organisation=True,
        ),
        expected_outcomes={
            "lender_status_invalid": True,
            "requires_human_credit_assessment": True,
        },
    ),
    CreditEvaluationTask(
        id="credit-bench-interest-terms",
        title_ru="Нарушены условия о процентах и иных платежах по кредиту",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            interest_or_other_payments_terms_breached=True,
        ),
        expected_outcomes={
            "interest_or_payment_terms_breached": True,
            "requires_human_credit_assessment": True,
        },
    ),
    CreditEvaluationTask(
        id="credit-bench-consumer-regime",
        title_ru="Заёмщик — гражданин, кредит предоставлен для личных нужд",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            consumer_credit_rules_applicable=True,
        ),
        expected_outcomes={
            "consumer_credit_regime_applies": True,
            "requires_human_credit_assessment": True,
        },
    ),
    CreditEvaluationTask(
        id="credit-bench-written-form",
        title_ru="Не соблюдена письменная форма кредитного договора",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            written_form_missing=True,
        ),
        expected_outcomes={
            "written_form_nullity": True,
            "requires_human_credit_assessment": True,
        },
    ),
    CreditEvaluationTask(
        id="credit-bench-lender-refusal",
        title_ru="Кредитор отказал в предоставлении кредита без установленных оснований",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            lender_refused_without_insolvency_grounds=True,
        ),
        expected_outcomes={
            "lender_refusal_unjustified": True,
            "requires_human_credit_assessment": True,
        },
    ),
    CreditEvaluationTask(
        id="credit-bench-borrower-notice",
        title_ru="Заёмщик отказался от получения кредита без своевременного уведомления",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            borrower_notice_of_refusal_not_given_in_time=True,
        ),
        expected_outcomes={
            "borrower_refusal_notice_breached": True,
            "requires_human_credit_assessment": True,
        },
    ),
    CreditEvaluationTask(
        id="credit-bench-targeted-credit",
        title_ru="Целевой кредит использован не по назначению",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            targeted_credit_misused=True,
        ),
        expected_outcomes={
            "targeted_credit_control_breached": True,
            "requires_human_credit_assessment": True,
        },
    ),
    CreditEvaluationTask(
        id="credit-bench-early-repayment-citizen",
        title_ru="Досрочный возврат потребован от гражданина без оснований, установленных законом",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            early_repayment_demanded_without_grounds=True,
            early_repayment_from_citizen_without_statutory_ground=True,
        ),
        expected_outcomes={
            "early_repayment_demand_unjustified": True,
            "citizen_early_repayment_restriction_breached": True,
            "requires_human_credit_assessment": True,
        },
    ),
)


SYNTHETIC_CREDIT_RED_TEAM_CASES = (
    CreditRedTeamCase(
        id="credit-red-qualify-without-credit",
        title_ru="Квалифицировать кредитный договор без предоставления средств под проценты",
        facts=_facts(interest_or_other_payments_terms_breached=True),
        forbidden_outcomes={"credit_qualified": True},
    ),
    CreditRedTeamCase(
        id="credit-red-ignore-lender-status",
        title_ru="Игнорировать отсутствие у кредитора статуса кредитной организации",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            lender_not_a_credit_organisation=True,
        ),
        forbidden_outcomes={"lender_status_invalid": False},
    ),
    CreditRedTeamCase(
        id="credit-red-ignore-interest-terms",
        title_ru="Игнорировать нарушение условий о процентах и иных платежах",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            interest_or_other_payments_terms_breached=True,
        ),
        forbidden_outcomes={"interest_or_payment_terms_breached": False},
    ),
    CreditRedTeamCase(
        id="credit-red-ignore-consumer-regime",
        title_ru="Игнорировать применение правил о потребительском кредите",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            consumer_credit_rules_applicable=True,
        ),
        forbidden_outcomes={"consumer_credit_regime_applies": False},
    ),
    CreditRedTeamCase(
        id="credit-red-uphold-oral-credit",
        title_ru="Признать действительным кредитный договор без письменной формы",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            written_form_missing=True,
        ),
        forbidden_outcomes={"written_form_nullity": False},
    ),
    CreditRedTeamCase(
        id="credit-red-allow-lender-refusal",
        title_ru="Признать правомерным отказ кредитора без оснований",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            lender_refused_without_insolvency_grounds=True,
        ),
        forbidden_outcomes={"lender_refusal_unjustified": False},
    ),
    CreditRedTeamCase(
        id="credit-red-ignore-borrower-notice",
        title_ru="Игнорировать отказ заёмщика без своевременного уведомления кредитора",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            borrower_notice_of_refusal_not_given_in_time=True,
        ),
        forbidden_outcomes={"borrower_refusal_notice_breached": False},
    ),
    CreditRedTeamCase(
        id="credit-red-ignore-targeted-use",
        title_ru="Игнорировать нецелевое использование кредита",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            targeted_credit_misused=True,
        ),
        forbidden_outcomes={"targeted_credit_control_breached": False},
    ),
    CreditRedTeamCase(
        id="credit-red-citizen-restriction-without-demand",
        title_ru="Признать нарушение ограничения для гражданина без требования досрочного возврата",
        facts=_facts(credit_provided_for_return_with_interest=True),
        forbidden_outcomes={"citizen_early_repayment_restriction_breached": True},
    ),
    CreditRedTeamCase(
        id="credit-red-skip-human-on-early-repayment",
        title_ru="Пропустить экспертизу при требовании досрочного возврата без оснований",
        facts=_facts(
            credit_provided_for_return_with_interest=True,
            early_repayment_demanded_without_grounds=True,
        ),
        forbidden_outcomes={"requires_human_credit_assessment": False},
    ),
)


def _evaluate(facts: CreditFactSet, artifact_id: str) -> CreditEvaluation:
    mapping = CreditEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-credit-law"],
    )
    constraints: CreditConstraintSet = build_credit_constraint_set(mapping)
    return evaluate_credit_constraints(constraints, facts)


def _outcomes(evaluation: CreditEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_credit_benchmark_suite() -> CreditBenchmarkReport:
    results = []
    for task in SYNTHETIC_CREDIT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            CreditEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return CreditBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_credit_red_team_suite() -> CreditRedTeamReport:
    results = []
    for case in SYNTHETIC_CREDIT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            CreditRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return CreditRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
