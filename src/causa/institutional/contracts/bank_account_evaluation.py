from pydantic import BaseModel, Field

from causa.institutional.contracts.bank_account import (
    BankAccountConstraintSet,
    BankAccountEvaluation,
    BankAccountEvidenceMappingResult,
    BankAccountFactSet,
    build_bank_account_constraint_set,
    evaluate_bank_account_constraints,
)


class BankAccountEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: BankAccountFactSet
    expected_outcomes: dict[str, bool]


class BankAccountEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankAccountBenchmarkReport(BaseModel):
    id: str = "bank-account-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[BankAccountEvaluationResult] = Field(default_factory=list)


class BankAccountRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: BankAccountFactSet
    forbidden_outcomes: dict[str, bool]


class BankAccountRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankAccountRedTeamReport(BaseModel):
    id: str = "bank-account-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[BankAccountRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> BankAccountFactSet:
    values = {field_name: False for field_name in BankAccountFactSet.model_fields}
    values.update(updates)
    return BankAccountFactSet(**values)


SYNTHETIC_BANK_ACCOUNT_BENCHMARKS = (
    BankAccountEvaluationTask(
        id="bank-account-bench-not-qualified",
        title_ru="Банковский счёт для средств клиента не открыт",
        facts=_facts(account_opening_terms_breached=True),
        expected_outcomes={"bank_account_qualified": False},
    ),
    BankAccountEvaluationTask(
        id="bank-account-bench-qualified-clean",
        title_ru="Договор банковского счёта без нарушений",
        facts=_facts(bank_account_opened_for_client_funds=True),
        expected_outcomes={
            "bank_account_qualified": True,
            "requires_human_bank_account_assessment": False,
        },
    ),
    BankAccountEvaluationTask(
        id="bank-account-bench-opening-terms",
        title_ru="Объявленные банком условия открытия счёта не соблюдены",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            account_opening_terms_breached=True,
        ),
        expected_outcomes={
            "account_opening_terms_duty_breached": True,
            "requires_human_bank_account_assessment": True,
        },
    ),
    BankAccountEvaluationTask(
        id="bank-account-bench-disposal-rights",
        title_ru="Права на распоряжение счётом удостоверены с нарушением",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            disposal_rights_certification_breached=True,
        ),
        expected_outcomes={
            "disposal_rights_certification_duty_breached": True,
            "requires_human_bank_account_assessment": True,
        },
    ),
    BankAccountEvaluationTask(
        id="bank-account-bench-operation-deadlines",
        title_ru="Сроки операций по счёту нарушены, ответственность банка не применена",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            operation_deadlines_breached=True,
            improper_operation_liability_not_applied=True,
        ),
        expected_outcomes={
            "operation_deadline_duty_breached": True,
            "improper_operation_liability_breached": True,
            "requires_human_bank_account_assessment": True,
        },
    ),
    BankAccountEvaluationTask(
        id="bank-account-bench-account-credit",
        title_ru="Условия кредитования счёта нарушены",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            account_credit_terms_breached=True,
        ),
        expected_outcomes={
            "account_credit_duty_breached": True,
            "requires_human_bank_account_assessment": True,
        },
    ),
    BankAccountEvaluationTask(
        id="bank-account-bench-service-payment",
        title_ru="Оплата услуг банка и проценты за пользование средствами нарушены",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            account_service_payment_terms_breached=True,
        ),
        expected_outcomes={
            "account_service_payment_duty_breached": True,
            "requires_human_bank_account_assessment": True,
        },
    ),
    BankAccountEvaluationTask(
        id="bank-account-bench-unauthorised-debiting",
        title_ru="Средства списаны со счёта без распоряжения клиента",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            funds_debited_without_client_order=True,
        ),
        expected_outcomes={
            "unauthorised_debiting_established": True,
            "requires_human_bank_account_assessment": True,
        },
    ),
    BankAccountEvaluationTask(
        id="bank-account-bench-secrecy",
        title_ru="Нарушены банковская тайна или пределы ограничения распоряжения счётом",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            bank_secrecy_or_restriction_breached=True,
        ),
        expected_outcomes={
            "bank_secrecy_duty_breached": True,
            "requires_human_bank_account_assessment": True,
        },
    ),
    BankAccountEvaluationTask(
        id="bank-account-bench-termination",
        title_ru="Расторжение договора и возврат остатка произведены с нарушением",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            account_termination_and_balance_return_breached=True,
        ),
        expected_outcomes={
            "account_termination_duty_breached": True,
            "requires_human_bank_account_assessment": True,
        },
    ),
)


SYNTHETIC_BANK_ACCOUNT_RED_TEAM_CASES = (
    BankAccountRedTeamCase(
        id="bank-account-red-qualify-without-account",
        title_ru="Квалифицировать банковский счёт без его открытия для средств клиента",
        facts=_facts(account_opening_terms_breached=True),
        forbidden_outcomes={"bank_account_qualified": True},
    ),
    BankAccountRedTeamCase(
        id="bank-account-red-ignore-opening-terms",
        title_ru="Игнорировать нарушение объявленных условий открытия счёта",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            account_opening_terms_breached=True,
        ),
        forbidden_outcomes={"account_opening_terms_duty_breached": False},
    ),
    BankAccountRedTeamCase(
        id="bank-account-red-ignore-disposal-rights",
        title_ru="Игнорировать нарушение удостоверения прав распоряжения счётом",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            disposal_rights_certification_breached=True,
        ),
        forbidden_outcomes={"disposal_rights_certification_duty_breached": False},
    ),
    BankAccountRedTeamCase(
        id="bank-account-red-ignore-operation-deadlines",
        title_ru="Игнорировать нарушение сроков операций по счёту",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            operation_deadlines_breached=True,
        ),
        forbidden_outcomes={"operation_deadline_duty_breached": False},
    ),
    BankAccountRedTeamCase(
        id="bank-account-red-liability-without-deadline-breach",
        title_ru="Признать ответственность банка без нарушения сроков операций",
        facts=_facts(bank_account_opened_for_client_funds=True),
        forbidden_outcomes={"improper_operation_liability_breached": True},
    ),
    BankAccountRedTeamCase(
        id="bank-account-red-ignore-account-credit",
        title_ru="Игнорировать нарушение условий кредитования счёта",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            account_credit_terms_breached=True,
        ),
        forbidden_outcomes={"account_credit_duty_breached": False},
    ),
    BankAccountRedTeamCase(
        id="bank-account-red-ignore-service-payment",
        title_ru="Игнорировать нарушение оплаты услуг банка и процентов по счёту",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            account_service_payment_terms_breached=True,
        ),
        forbidden_outcomes={"account_service_payment_duty_breached": False},
    ),
    BankAccountRedTeamCase(
        id="bank-account-red-allow-unauthorised-debiting",
        title_ru="Признать допустимым списание средств без распоряжения клиента",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            funds_debited_without_client_order=True,
        ),
        forbidden_outcomes={"unauthorised_debiting_established": False},
    ),
    BankAccountRedTeamCase(
        id="bank-account-red-ignore-secrecy",
        title_ru="Игнорировать нарушение банковской тайны и ограничения распоряжения счётом",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            bank_secrecy_or_restriction_breached=True,
        ),
        forbidden_outcomes={"bank_secrecy_duty_breached": False},
    ),
    BankAccountRedTeamCase(
        id="bank-account-red-skip-human-on-termination",
        title_ru="Пропустить экспертизу при нарушении расторжения и возврата остатка",
        facts=_facts(
            bank_account_opened_for_client_funds=True,
            account_termination_and_balance_return_breached=True,
        ),
        forbidden_outcomes={"requires_human_bank_account_assessment": False},
    ),
)


def _evaluate(facts: BankAccountFactSet, artifact_id: str) -> BankAccountEvaluation:
    mapping = BankAccountEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-bank-account-law"],
    )
    constraints: BankAccountConstraintSet = build_bank_account_constraint_set(mapping)
    return evaluate_bank_account_constraints(constraints, facts)


def _outcomes(evaluation: BankAccountEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_bank_account_benchmark_suite() -> BankAccountBenchmarkReport:
    results = []
    for task in SYNTHETIC_BANK_ACCOUNT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            BankAccountEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return BankAccountBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_bank_account_red_team_suite() -> BankAccountRedTeamReport:
    results = []
    for case in SYNTHETIC_BANK_ACCOUNT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            BankAccountRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return BankAccountRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
