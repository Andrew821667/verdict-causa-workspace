from pydantic import BaseModel, Field

from causa.institutional.contracts.bank_deposit import (
    BankDepositConstraintSet,
    BankDepositEvaluation,
    BankDepositEvidenceMappingResult,
    BankDepositFactSet,
    build_bank_deposit_constraint_set,
    evaluate_bank_deposit_constraints,
)


class BankDepositEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: BankDepositFactSet
    expected_outcomes: dict[str, bool]


class BankDepositEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankDepositBenchmarkReport(BaseModel):
    id: str = "bank-deposit-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[BankDepositEvaluationResult] = Field(default_factory=list)


class BankDepositRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: BankDepositFactSet
    forbidden_outcomes: dict[str, bool]


class BankDepositRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankDepositRedTeamReport(BaseModel):
    id: str = "bank-deposit-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[BankDepositRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> BankDepositFactSet:
    values = {field_name: False for field_name in BankDepositFactSet.model_fields}
    values.update(updates)
    return BankDepositFactSet(**values)


SYNTHETIC_BANK_DEPOSIT_BENCHMARKS = (
    BankDepositEvaluationTask(
        id="bank-deposit-bench-not-qualified",
        title_ru="Денежная сумма не принята банком во вклад",
        facts=_facts(deposit_taken_by_unauthorised_person=True),
        expected_outcomes={"bank_deposit_qualified": False},
    ),
    BankDepositEvaluationTask(
        id="bank-deposit-bench-qualified-clean",
        title_ru="Договор банковского вклада без нарушений",
        facts=_facts(deposit_accepted_for_return_with_interest=True),
        expected_outcomes={
            "bank_deposit_qualified": True,
            "requires_human_bank_deposit_assessment": False,
        },
    ),
    BankDepositEvaluationTask(
        id="bank-deposit-bench-unauthorised-acceptance",
        title_ru="Вклад привлечён лицом без права принимать вклады",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            deposit_taken_by_unauthorised_person=True,
        ),
        expected_outcomes={
            "deposit_acceptance_unauthorised": True,
            "requires_human_bank_deposit_assessment": True,
        },
    ),
    BankDepositEvaluationTask(
        id="bank-deposit-bench-form",
        title_ru="Письменная форма договора банковского вклада не соблюдена",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            deposit_written_form_not_observed=True,
        ),
        expected_outcomes={
            "deposit_form_void": True,
            "requires_human_bank_deposit_assessment": True,
        },
    ),
    BankDepositEvaluationTask(
        id="bank-deposit-bench-early-repayment",
        title_ru="Вклад не выдан по первому требованию, проценты пересчитаны неверно",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            citizen_deposit_on_demand_repayment_breached=True,
            early_repayment_interest_miscalculated=True,
        ),
        expected_outcomes={
            "on_demand_repayment_duty_breached": True,
            "early_repayment_interest_breached": True,
            "requires_human_bank_deposit_assessment": True,
        },
    ),
    BankDepositEvaluationTask(
        id="bank-deposit-bench-interest",
        title_ru="Проценты на сумму вклада не выплачены на согласованных условиях",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            deposit_interest_not_paid_as_agreed=True,
        ),
        expected_outcomes={
            "interest_payment_duty_breached": True,
            "requires_human_bank_deposit_assessment": True,
        },
    ),
    BankDepositEvaluationTask(
        id="bank-deposit-bench-rate-reduction",
        title_ru="Ставка по срочному вкладу гражданина уменьшена банком в одностороннем порядке",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            term_deposit_interest_rate_unilaterally_reduced=True,
        ),
        expected_outcomes={
            "term_rate_reduction_prohibited": True,
            "requires_human_bank_deposit_assessment": True,
        },
    ),
    BankDepositEvaluationTask(
        id="bank-deposit-bench-security",
        title_ru="Возврат вклада не обеспечен предусмотренным способом",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            deposit_repayment_security_not_ensured=True,
        ),
        expected_outcomes={
            "repayment_security_duty_breached": True,
            "requires_human_bank_deposit_assessment": True,
        },
    ),
    BankDepositEvaluationTask(
        id="bank-deposit-bench-third-party",
        title_ru="Права по вкладу в пользу третьего лица не учтены",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            third_party_deposit_rights_disregarded=True,
        ),
        expected_outcomes={
            "third_party_deposit_rights_breached": True,
            "requires_human_bank_deposit_assessment": True,
        },
    ),
    BankDepositEvaluationTask(
        id="bank-deposit-bench-savings-document",
        title_ru="Нарушены правила о сберегательной книжке и сертификате",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            savings_document_rules_breached=True,
        ),
        expected_outcomes={
            "savings_document_duty_breached": True,
            "requires_human_bank_deposit_assessment": True,
        },
    ),
)


SYNTHETIC_BANK_DEPOSIT_RED_TEAM_CASES = (
    BankDepositRedTeamCase(
        id="bank-deposit-red-qualify-without-acceptance",
        title_ru="Квалифицировать банковский вклад без принятия суммы банком",
        facts=_facts(deposit_taken_by_unauthorised_person=True),
        forbidden_outcomes={"bank_deposit_qualified": True},
    ),
    BankDepositRedTeamCase(
        id="bank-deposit-red-ignore-unauthorised-acceptance",
        title_ru="Игнорировать отсутствие у лица права принимать вклады",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            deposit_taken_by_unauthorised_person=True,
        ),
        forbidden_outcomes={"deposit_acceptance_unauthorised": False},
    ),
    BankDepositRedTeamCase(
        id="bank-deposit-red-ignore-form",
        title_ru="Признать действительным договор вклада без письменной формы",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            deposit_written_form_not_observed=True,
        ),
        forbidden_outcomes={"deposit_form_void": False},
    ),
    BankDepositRedTeamCase(
        id="bank-deposit-red-ignore-on-demand-repayment",
        title_ru="Игнорировать отказ выдать вклад по первому требованию",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            citizen_deposit_on_demand_repayment_breached=True,
        ),
        forbidden_outcomes={"on_demand_repayment_duty_breached": False},
    ),
    BankDepositRedTeamCase(
        id="bank-deposit-red-early-interest-without-repayment-breach",
        title_ru="Признать нарушение процентов при досрочном возврате без нарушения выдачи вклада",
        facts=_facts(deposit_accepted_for_return_with_interest=True),
        forbidden_outcomes={"early_repayment_interest_breached": True},
    ),
    BankDepositRedTeamCase(
        id="bank-deposit-red-ignore-interest",
        title_ru="Освободить банк от выплаты процентов на сумму вклада",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            deposit_interest_not_paid_as_agreed=True,
        ),
        forbidden_outcomes={"interest_payment_duty_breached": False},
    ),
    BankDepositRedTeamCase(
        id="bank-deposit-red-allow-rate-reduction",
        title_ru="Признать допустимым одностороннее уменьшение ставки по срочному вкладу",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            term_deposit_interest_rate_unilaterally_reduced=True,
        ),
        forbidden_outcomes={"term_rate_reduction_prohibited": False},
    ),
    BankDepositRedTeamCase(
        id="bank-deposit-red-ignore-security",
        title_ru="Игнорировать необеспечение возврата вклада",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            deposit_repayment_security_not_ensured=True,
        ),
        forbidden_outcomes={"repayment_security_duty_breached": False},
    ),
    BankDepositRedTeamCase(
        id="bank-deposit-red-ignore-third-party",
        title_ru="Игнорировать права вкладчика по вкладу в пользу третьего лица",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            third_party_deposit_rights_disregarded=True,
        ),
        forbidden_outcomes={"third_party_deposit_rights_breached": False},
    ),
    BankDepositRedTeamCase(
        id="bank-deposit-red-skip-human-on-savings-document",
        title_ru="Пропустить экспертизу при нарушении правил о сберегательной книжке",
        facts=_facts(
            deposit_accepted_for_return_with_interest=True,
            savings_document_rules_breached=True,
        ),
        forbidden_outcomes={"requires_human_bank_deposit_assessment": False},
    ),
)


def _evaluate(facts: BankDepositFactSet, artifact_id: str) -> BankDepositEvaluation:
    mapping = BankDepositEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-bank-deposit-law"],
    )
    constraints: BankDepositConstraintSet = build_bank_deposit_constraint_set(mapping)
    return evaluate_bank_deposit_constraints(constraints, facts)


def _outcomes(evaluation: BankDepositEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_bank_deposit_benchmark_suite() -> BankDepositBenchmarkReport:
    results = []
    for task in SYNTHETIC_BANK_DEPOSIT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            BankDepositEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return BankDepositBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_bank_deposit_red_team_suite() -> BankDepositRedTeamReport:
    results = []
    for case in SYNTHETIC_BANK_DEPOSIT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            BankDepositRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return BankDepositRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
