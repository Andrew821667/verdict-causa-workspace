"""Benchmark и red-team для модели специальных видов банковских счетов."""

from pydantic import BaseModel, Field

from causa.institutional.contracts.special_accounts import (
    SpecialAccountsConstraintSet,
    SpecialAccountsEvaluation,
    SpecialAccountsEvidenceMappingResult,
    SpecialAccountsFactSet,
    build_special_accounts_constraint_set,
    evaluate_special_accounts_constraints,
)


class SpecialAccountsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: SpecialAccountsFactSet
    expected_outcomes: dict[str, bool]


class SpecialAccountsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SpecialAccountsBenchmarkReport(BaseModel):
    id: str = "special-accounts-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[SpecialAccountsEvaluationResult] = Field(default_factory=list)


class SpecialAccountsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: SpecialAccountsFactSet
    forbidden_outcomes: dict[str, bool]


class SpecialAccountsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SpecialAccountsRedTeamReport(BaseModel):
    id: str = "special-accounts-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[SpecialAccountsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> SpecialAccountsFactSet:
    values = {field_name: False for field_name in SpecialAccountsFactSet.model_fields}
    values.update(updates)
    return SpecialAccountsFactSet(**values)


_NOMINAL = {
    "special_account_asserted": True,
    "nominal_account": True,
    "beneficiary_identified_or_determinable": True,
    "nominal_form_single_signed_document": True,
}
_ESCROW = {
    "special_account_asserted": True,
    "escrow_account": True,
    "escrow_grounds_defined": True,
}
_PUBLIC = {
    "special_account_asserted": True,
    "public_deposit_account": True,
    "holder_authorised_by_law": True,
    "bank_meets_capital_requirement": True,
}


SYNTHETIC_SPECIAL_ACCOUNTS_BENCHMARKS = (
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-kind-undetermined",
        title_ru="Специальный счёт заявлен, но вид счёта не установлен",
        facts=_facts(special_account_asserted=True),
        expected_outcomes={
            "special_account_qualified": False,
            "account_kind_undetermined": True,
            "funds_insulated_from_holder_creditors": False,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-no-special-account",
        title_ru="Обычный банковский счёт: специальный вид в деле не заявлен",
        facts=_facts(),
        expected_outcomes={
            "special_account_qualified": False,
            "account_kind_undetermined": False,
            "funds_insulated_from_holder_creditors": False,
            "requires_human_special_accounts_assessment": False,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-nominal-clean",
        title_ru="Номинальный счёт открыт правильно, нарушений нет",
        facts=_facts(**_NOMINAL),
        expected_outcomes={
            "special_account_qualified": True,
            "funds_insulated_from_holder_creditors": True,
            "nominal_essential_term_missing": False,
            "nominal_form_defect_makes_void": False,
            "insulation_breached": False,
            "requires_human_special_accounts_assessment": False,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-nominal-no-beneficiary",
        title_ru="В договоре номинального счёта бенефициар не указан и не определим",
        facts=_facts(**{**_NOMINAL, "beneficiary_identified_or_determinable": False}),
        expected_outcomes={
            "special_account_qualified": True,
            "nominal_essential_term_missing": True,
            "nominal_form_defect_makes_void": False,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-nominal-form-void",
        title_ru="Договор номинального счёта заключён не единым подписанным документом",
        facts=_facts(**{**_NOMINAL, "nominal_form_single_signed_document": False}),
        expected_outcomes={
            "special_account_qualified": True,
            "nominal_form_defect_makes_void": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-nominal-control-breach",
        title_ru="Банк принял на себя контроль по номинальному счёту и не исполнил его",
        facts=_facts(
            **{
                **_NOMINAL,
                "bank_control_duty_agreed": True,
                "bank_control_duty_not_performed": True,
            }
        ),
        expected_outcomes={
            "nominal_control_duty_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-nominal-no-control-agreed",
        title_ru="Контроль банка договором не предусмотрен — упрёка в его отсутствии нет",
        facts=_facts(**{**_NOMINAL, "bank_control_duty_not_performed": True}),
        expected_outcomes={
            "nominal_control_duty_breached": False,
            "requires_human_special_accounts_assessment": False,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-nominal-change-without-consent",
        title_ru="Номинальный счёт с участием бенефициара изменён без его согласия",
        facts=_facts(**{**_NOMINAL, "nominal_change_without_beneficiary_consent": True}),
        expected_outcomes={
            "nominal_change_duty_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-nominal-information-denied",
        title_ru="Бенефициару номинального счёта отказано в сведениях по счёту",
        facts=_facts(**{**_NOMINAL, "beneficiary_denied_account_information": True}),
        expected_outcomes={
            "nominal_information_duty_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-escrow-grounds-not-occurred",
        title_ru="Счёт эскроу открыт, основания передачи ещё не наступили",
        facts=_facts(**_ESCROW),
        expected_outcomes={
            "special_account_qualified": True,
            "funds_insulated_from_holder_creditors": True,
            "escrow_payment_duty_arisen": False,
            "escrow_payment_duty_breached": False,
            "requires_human_special_accounts_assessment": False,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-escrow-duty-arisen",
        title_ru="Основания передачи наступили, банк передал сумму бенефициару",
        facts=_facts(**{**_ESCROW, "escrow_grounds_occurred": True}),
        expected_outcomes={
            "escrow_payment_duty_arisen": True,
            "escrow_payment_duty_breached": False,
            "requires_human_special_accounts_assessment": False,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-escrow-payment-delayed",
        title_ru="Основания наступили, но передача бенефициару просрочена",
        facts=_facts(
            **{
                **_ESCROW,
                "escrow_grounds_occurred": True,
                "escrow_payment_to_beneficiary_delayed": True,
            }
        ),
        expected_outcomes={
            "escrow_payment_duty_arisen": True,
            "escrow_payment_duty_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-escrow-disposal-before-grounds",
        title_ru="Депонент попытался распорядиться суммой до наступления оснований",
        facts=_facts(**{**_ESCROW, "disposal_attempted_before_grounds": True}),
        expected_outcomes={
            "escrow_disposal_restriction_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-escrow-extra-funds",
        title_ru="На счёт эскроу зачислены иные деньги помимо депонируемой суммы",
        facts=_facts(**{**_ESCROW, "extra_funds_credited_to_escrow": True}),
        expected_outcomes={
            "escrow_extra_funds_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-escrow-balance-withheld",
        title_ru="Срок договора эскроу истёк без оснований, остаток депоненту не возвращён",
        facts=_facts(
            **{
                **_ESCROW,
                "escrow_term_expired_without_grounds": True,
                "escrow_balance_withheld_from_depositor": True,
            }
        ),
        expected_outcomes={
            "escrow_return_duty_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-public-clean",
        title_ru="Публичный депозитный счёт нотариуса открыт правильно",
        facts=_facts(**_PUBLIC),
        expected_outcomes={
            "special_account_qualified": True,
            "funds_insulated_from_holder_creditors": True,
            "public_holder_not_authorised": False,
            "public_bank_requirement_breached": False,
            "requires_human_special_accounts_assessment": False,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-public-holder-not-authorised",
        title_ru="Публичный депозитный счёт открыт лицом, которому закон этого не разрешает",
        facts=_facts(**{**_PUBLIC, "holder_authorised_by_law": False}),
        expected_outcomes={
            "public_holder_not_authorised": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-public-bank-capital",
        title_ru="Публичный депозитный счёт открыт в банке без требуемого капитала",
        facts=_facts(**{**_PUBLIC, "bank_meets_capital_requirement": False}),
        expected_outcomes={
            "public_bank_requirement_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-public-own-funds",
        title_ru="На публичный депозитный счёт зачислены собственные деньги владельца",
        facts=_facts(**{**_PUBLIC, "own_funds_credited_to_public_account": True}),
        expected_outcomes={
            "public_own_funds_prohibition_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-public-interest-withheld",
        title_ru="Проценты на депонированную сумму бенефициару не выплачены",
        facts=_facts(**{**_PUBLIC, "interest_withheld_from_beneficiary": True}),
        expected_outcomes={
            "public_interest_duty_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-insulation-breached",
        title_ru="По долгу владельца номинального счёта списаны деньги бенефициара",
        facts=_facts(**{**_NOMINAL, "seizure_or_debit_for_holder_debt": True}),
        expected_outcomes={
            "funds_insulated_from_holder_creditors": True,
            "insulation_breached": True,
            "requires_human_special_accounts_assessment": True,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-seizure-permitted",
        title_ru="Арест по обязательствам владельца счёта допущен законом",
        facts=_facts(
            **{
                **_NOMINAL,
                "seizure_or_debit_for_holder_debt": True,
                "seizure_permitted_by_law": True,
            }
        ),
        expected_outcomes={
            "funds_insulated_from_holder_creditors": True,
            "insulation_breached": False,
            "requires_human_special_accounts_assessment": False,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-nominal-beneficiary-seizure-allowed",
        title_ru="Арест по долгу бенефициара номинального счёта: статья 860.5 его допускает",
        facts=_facts(**{**_NOMINAL, "seizure_for_beneficiary_or_depositor_debt": True}),
        expected_outcomes={
            "insulation_breached": False,
            "public_wider_insulation_breached": False,
            "requires_human_special_accounts_assessment": False,
        },
    ),
    SpecialAccountsEvaluationTask(
        id="special-accounts-bench-public-wider-insulation",
        title_ru="Арест на публичном депозитном счёте по долгу депонента запрещён",
        facts=_facts(**{**_PUBLIC, "seizure_for_beneficiary_or_depositor_debt": True}),
        expected_outcomes={
            "public_wider_insulation_breached": True,
            "insulation_breached": False,
            "requires_human_special_accounts_assessment": True,
        },
    ),
)


SYNTHETIC_SPECIAL_ACCOUNTS_RED_TEAM_CASES = (
    SpecialAccountsRedTeamCase(
        id="special-accounts-red-kind-from-assertion",
        title_ru="Заявление о специальном счёте без указания вида не даёт квалификации",
        facts=_facts(special_account_asserted=True),
        forbidden_outcomes={
            "special_account_qualified": True,
            "funds_insulated_from_holder_creditors": True,
        },
    ),
    SpecialAccountsRedTeamCase(
        id="special-accounts-red-escrow-duty-without-grounds",
        title_ru="Просрочка передачи без наступления оснований не создаёт нарушения",
        facts=_facts(**{**_ESCROW, "escrow_payment_to_beneficiary_delayed": True}),
        forbidden_outcomes={
            "escrow_payment_duty_arisen": True,
            "escrow_payment_duty_breached": True,
        },
    ),
    SpecialAccountsRedTeamCase(
        id="special-accounts-red-nominal-rules-to-escrow",
        title_ru="Правила номинального счёта не переносятся на счёт эскроу",
        facts=_facts(**_ESCROW),
        forbidden_outcomes={
            "nominal_essential_term_missing": True,
            "nominal_form_defect_makes_void": True,
        },
    ),
    SpecialAccountsRedTeamCase(
        id="special-accounts-red-public-rules-to-nominal",
        title_ru="Требования к публичному депозитному счёту не переносятся на номинальный",
        facts=_facts(**_NOMINAL),
        forbidden_outcomes={
            "public_holder_not_authorised": True,
            "public_bank_requirement_breached": True,
        },
    ),
    SpecialAccountsRedTeamCase(
        id="special-accounts-red-wider-insulation-to-escrow",
        title_ru="Широкая защита статьи 860.14 не переносится на счёт эскроу",
        facts=_facts(**{**_ESCROW, "seizure_for_beneficiary_or_depositor_debt": True}),
        forbidden_outcomes={"public_wider_insulation_breached": True},
    ),
    SpecialAccountsRedTeamCase(
        id="special-accounts-red-insulation-without-special-account",
        title_ru="Без специального счёта защита от кредиторов владельца не возникает",
        facts=_facts(seizure_or_debit_for_holder_debt=True),
        forbidden_outcomes={
            "funds_insulated_from_holder_creditors": True,
            "insulation_breached": True,
        },
    ),
    SpecialAccountsRedTeamCase(
        id="special-accounts-red-return-without-expiry",
        title_ru="Удержание остатка до истечения срока договора эскроу не нарушение",
        facts=_facts(**{**_ESCROW, "escrow_balance_withheld_from_depositor": True}),
        forbidden_outcomes={"escrow_return_duty_breached": True},
    ),
    SpecialAccountsRedTeamCase(
        id="special-accounts-red-breach-without-qualification",
        title_ru="Нарушения без заявленного специального счёта не выводятся",
        facts=_facts(
            beneficiary_denied_account_information=True,
            extra_funds_credited_to_escrow=True,
            own_funds_credited_to_public_account=True,
            interest_withheld_from_beneficiary=True,
        ),
        forbidden_outcomes={
            "nominal_information_duty_breached": True,
            "escrow_extra_funds_breached": True,
            "public_own_funds_prohibition_breached": True,
            "public_interest_duty_breached": True,
        },
    ),
)


def _evaluate(facts: SpecialAccountsFactSet, artifact_id: str) -> SpecialAccountsEvaluation:
    mapping = SpecialAccountsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-special-accounts-law"],
    )
    constraints: SpecialAccountsConstraintSet = build_special_accounts_constraint_set(mapping)
    return evaluate_special_accounts_constraints(constraints, facts)


def _outcomes(evaluation: SpecialAccountsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_special_accounts_benchmark_suite() -> SpecialAccountsBenchmarkReport:
    results = []
    for task in SYNTHETIC_SPECIAL_ACCOUNTS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            SpecialAccountsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return SpecialAccountsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_special_accounts_red_team_suite() -> SpecialAccountsRedTeamReport:
    results = []
    for case in SYNTHETIC_SPECIAL_ACCOUNTS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            SpecialAccountsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return SpecialAccountsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
