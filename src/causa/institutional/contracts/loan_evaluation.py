from pydantic import BaseModel, Field

from causa.institutional.contracts.loan import (
    LoanConstraintSet,
    LoanEvaluation,
    LoanEvidenceMappingResult,
    LoanFactSet,
    build_loan_constraint_set,
    evaluate_loan_constraints,
)


class LoanEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: LoanFactSet
    expected_outcomes: dict[str, bool]


class LoanEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class LoanBenchmarkReport(BaseModel):
    id: str = "loan-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[LoanEvaluationResult] = Field(default_factory=list)


class LoanRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: LoanFactSet
    forbidden_outcomes: dict[str, bool]


class LoanRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class LoanRedTeamReport(BaseModel):
    id: str = "loan-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[LoanRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> LoanFactSet:
    values = {field_name: False for field_name in LoanFactSet.model_fields}
    values.update(updates)
    return LoanFactSet(**values)


SYNTHETIC_LOAN_BENCHMARKS = (
    LoanEvaluationTask(
        id="loan-bench-not-qualified",
        title_ru="Деньги или вещи с обязанностью возврата не передавались",
        facts=_facts(interest_terms_not_compliant=True),
        expected_outcomes={"loan_qualified": False},
    ),
    LoanEvaluationTask(
        id="loan-bench-qualified-clean",
        title_ru="Договор займа без нарушений",
        facts=_facts(money_or_fungibles_transferred_for_return=True),
        expected_outcomes={
            "loan_qualified": True,
            "requires_human_loan_assessment": False,
        },
    ),
    LoanEvaluationTask(
        id="loan-bench-written-form",
        title_ru="Не соблюдена обязательная письменная форма договора займа",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            written_form_required_but_missing=True,
        ),
        expected_outcomes={
            "written_form_requirement_breached": True,
            "requires_human_loan_assessment": True,
        },
    ),
    LoanEvaluationTask(
        id="loan-bench-interest-rules",
        title_ru="Проценты начислены с нарушением правил о процентах по займу",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            interest_terms_not_compliant=True,
        ),
        expected_outcomes={
            "interest_rules_breached": True,
            "requires_human_loan_assessment": True,
        },
    ),
    LoanEvaluationTask(
        id="loan-bench-usurious-interest",
        title_ru="Размер процентов является ростовщическим и чрезмерно обременительным",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            usurious_interest_rate=True,
        ),
        expected_outcomes={
            "usurious_interest_reducible": True,
            "requires_human_loan_assessment": True,
        },
    ),
    LoanEvaluationTask(
        id="loan-bench-late-repayment",
        title_ru="Срок возврата нарушен, проценты за просрочку не начислены",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            repayment_deadline_breached=True,
            late_payment_interest_not_accrued=True,
        ),
        expected_outcomes={
            "repayment_duty_breached": True,
            "late_payment_interest_due": True,
            "requires_human_loan_assessment": True,
        },
    ),
    LoanEvaluationTask(
        id="loan-bench-unfunded",
        title_ru="Договор займа оспаривается по безденежности",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            loan_challenged_as_unfunded=True,
        ),
        expected_outcomes={
            "unfunded_loan_challenge_available": True,
            "requires_human_loan_assessment": True,
        },
    ),
    LoanEvaluationTask(
        id="loan-bench-security-lost",
        title_ru="Обеспечение возврата займа утрачено",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            security_lost_or_deteriorated=True,
        ),
        expected_outcomes={
            "early_repayment_demand_available": True,
            "requires_human_loan_assessment": True,
        },
    ),
    LoanEvaluationTask(
        id="loan-bench-targeted-loan",
        title_ru="Целевой заём использован не по назначению",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            targeted_loan_misused_or_control_obstructed=True,
        ),
        expected_outcomes={
            "targeted_loan_control_breached": True,
            "requires_human_loan_assessment": True,
        },
    ),
    LoanEvaluationTask(
        id="loan-bench-novation",
        title_ru="Новация долга в заёмное обязательство совершена с нарушениями",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            novation_into_loan_requirements_breached=True,
        ),
        expected_outcomes={
            "novation_requirements_breached": True,
            "requires_human_loan_assessment": True,
        },
    ),
)


SYNTHETIC_LOAN_RED_TEAM_CASES = (
    LoanRedTeamCase(
        id="loan-red-qualify-without-transfer",
        title_ru="Квалифицировать заём без передачи денег или вещей",
        facts=_facts(interest_terms_not_compliant=True),
        forbidden_outcomes={"loan_qualified": True},
    ),
    LoanRedTeamCase(
        id="loan-red-ignore-written-form",
        title_ru="Игнорировать несоблюдение письменной формы договора займа",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            written_form_required_but_missing=True,
        ),
        forbidden_outcomes={"written_form_requirement_breached": False},
    ),
    LoanRedTeamCase(
        id="loan-red-ignore-interest-rules",
        title_ru="Игнорировать нарушение правил о процентах по займу",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            interest_terms_not_compliant=True,
        ),
        forbidden_outcomes={"interest_rules_breached": False},
    ),
    LoanRedTeamCase(
        id="loan-red-uphold-usurious-interest",
        title_ru="Признать ростовщические проценты не подлежащими уменьшению",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            usurious_interest_rate=True,
        ),
        forbidden_outcomes={"usurious_interest_reducible": False},
    ),
    LoanRedTeamCase(
        id="loan-red-ignore-repayment",
        title_ru="Игнорировать нарушение срока возврата суммы займа",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            repayment_deadline_breached=True,
        ),
        forbidden_outcomes={"repayment_duty_breached": False},
    ),
    LoanRedTeamCase(
        id="loan-red-interest-without-delay",
        title_ru="Признать проценты за просрочку без нарушения срока возврата",
        facts=_facts(money_or_fungibles_transferred_for_return=True),
        forbidden_outcomes={"late_payment_interest_due": True},
    ),
    LoanRedTeamCase(
        id="loan-red-block-unfunded-challenge",
        title_ru="Лишить заёмщика права оспаривать заём по безденежности",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            loan_challenged_as_unfunded=True,
        ),
        forbidden_outcomes={"unfunded_loan_challenge_available": False},
    ),
    LoanRedTeamCase(
        id="loan-red-ignore-security-loss",
        title_ru="Игнорировать утрату обеспечения возврата займа",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            security_lost_or_deteriorated=True,
        ),
        forbidden_outcomes={"early_repayment_demand_available": False},
    ),
    LoanRedTeamCase(
        id="loan-red-ignore-targeted-use",
        title_ru="Игнорировать нецелевое использование суммы займа",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            targeted_loan_misused_or_control_obstructed=True,
        ),
        forbidden_outcomes={"targeted_loan_control_breached": False},
    ),
    LoanRedTeamCase(
        id="loan-red-skip-human-on-novation",
        title_ru="Пропустить экспертизу при нарушении требований к новации долга",
        facts=_facts(
            money_or_fungibles_transferred_for_return=True,
            novation_into_loan_requirements_breached=True,
        ),
        forbidden_outcomes={"requires_human_loan_assessment": False},
    ),
)


def _evaluate(facts: LoanFactSet, artifact_id: str) -> LoanEvaluation:
    mapping = LoanEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-loan-law"],
    )
    constraints: LoanConstraintSet = build_loan_constraint_set(mapping)
    return evaluate_loan_constraints(constraints, facts)


def _outcomes(evaluation: LoanEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_loan_benchmark_suite() -> LoanBenchmarkReport:
    results = []
    for task in SYNTHETIC_LOAN_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            LoanEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return LoanBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_loan_red_team_suite() -> LoanRedTeamReport:
    results = []
    for case in SYNTHETIC_LOAN_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            LoanRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return LoanRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
