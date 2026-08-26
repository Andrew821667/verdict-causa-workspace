"""Benchmark и red-team для модели условного депонирования (эскроу)."""

from pydantic import BaseModel, Field

from causa.institutional.contracts.escrow_deposit import (
    EscrowDepositConstraintSet,
    EscrowDepositEvaluation,
    EscrowDepositEvidenceMappingResult,
    EscrowDepositFactSet,
    build_escrow_deposit_constraint_set,
    evaluate_escrow_deposit_constraints,
)


class EscrowDepositEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: EscrowDepositFactSet
    expected_outcomes: dict[str, bool]


class EscrowDepositEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class EscrowDepositBenchmarkReport(BaseModel):
    id: str = "escrow-deposit-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[EscrowDepositEvaluationResult] = Field(default_factory=list)


class EscrowDepositRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: EscrowDepositFactSet
    forbidden_outcomes: dict[str, bool]


class EscrowDepositRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class EscrowDepositRedTeamReport(BaseModel):
    id: str = "escrow-deposit-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[EscrowDepositRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> EscrowDepositFactSet:
    values = {field_name: False for field_name in EscrowDepositFactSet.model_fields}
    values.update(updates)
    return EscrowDepositFactSet(**values)


_THINGS = {"escrow_deposit_asserted": True, "deposited_things": True}
_MONEY = {"escrow_deposit_asserted": True, "deposited_cashless_money": True}
_SECURITIES = {
    "escrow_deposit_asserted": True,
    "deposited_uncertificated_securities": True,
}
_GROUNDED = {"escrow_deposit_grounds_defined": True, "grounds_for_transfer_occurred": True}


SYNTHETIC_ESCROW_DEPOSIT_BENCHMARKS = (
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-kind-undetermined",
        title_ru="Договор эскроу заявлен, предмет депонирования не установлен",
        facts=_facts(escrow_deposit_asserted=True),
        expected_outcomes={
            "escrow_deposit_qualified": False,
            "escrow_deposit_kind_undetermined": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-not-asserted",
        title_ru="Договора эскроу в деле нет",
        facts=_facts(),
        expected_outcomes={
            "escrow_deposit_qualified": False,
            "escrow_deposit_kind_undetermined": False,
            "requires_human_escrow_deposit_assessment": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-things-notarized-clean",
        title_ru="Депонирование вещей, договор нотариально удостоверен, нарушений нет",
        facts=_facts(**_THINGS, notarization_performed=True),
        expected_outcomes={
            "escrow_deposit_qualified": True,
            "notarization_required": True,
            "notarization_missing_makes_void": False,
            "depositor_retains_title": True,
            "requires_human_escrow_deposit_assessment": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-things-not-notarized-void",
        title_ru="Депонирование вещей без нотариального удостоверения — ничтожность",
        facts=_facts(**_THINGS),
        expected_outcomes={
            "notarization_required": True,
            "notarization_missing_makes_void": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-money-only-no-notary",
        title_ru="Депонирование только безналичных денег — нотариус не нужен",
        facts=_facts(**_MONEY, escrow_agent_is_bank=True),
        expected_outcomes={
            "notarization_required": False,
            "notarization_missing_makes_void": False,
            "requires_human_escrow_deposit_assessment": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-securities-only-no-notary",
        title_ru="Депонирование только бездокументарных ценных бумаг — нотариус не нужен",
        facts=_facts(**_SECURITIES, securities_exercise_permitted_by_contract=True),
        expected_outcomes={
            "notarization_required": False,
            "requires_human_escrow_deposit_assessment": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-things-plus-money-needs-notary",
        title_ru="Вещи вместе с деньгами: нотариус нужен, потому что депонированы вещи",
        facts=_facts(**_THINGS, deposited_cashless_money=True, notarization_performed=True),
        expected_outcomes={
            "notarization_required": True,
            "notarization_missing_makes_void": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-term-deemed-five-years",
        title_ru="Срок не указан — закон подставляет пять лет, это не порок сделки",
        facts=_facts(**_THINGS, notarization_performed=True, deposit_term_missing_or_excessive=True),
        expected_outcomes={
            "deposit_term_deemed_five_years": True,
            "requires_human_escrow_deposit_assessment": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-remuneration-default",
        title_ru="Вознаграждение эскроу-агента причитается по умолчанию",
        facts=_facts(**_THINGS, notarization_performed=True),
        expected_outcomes={
            "remuneration_owed": True,
            "remuneration_liability_joint_and_several": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-remuneration-waived",
        title_ru="Договор исключил вознаграждение агента",
        facts=_facts(**_THINGS, notarization_performed=True, remuneration_waived_by_contract=True),
        expected_outcomes={"remuneration_owed": False},
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-setoff-breach",
        title_ru="Агент удержал имущество в счёт вознаграждения без разрешения договора",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            agent_withheld_or_setoff_deposited_property=True,
        ),
        expected_outcomes={
            "agent_setoff_breached": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-setoff-permitted",
        title_ru="Договор разрешил зачёт — нарушения нет",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            agent_setoff_permitted_by_contract=True,
            agent_withheld_or_setoff_deposited_property=True,
        ),
        expected_outcomes={
            "agent_setoff_breached": False,
            "requires_human_escrow_deposit_assessment": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-document-check-breach",
        title_ru="Агент передал имущество вопреки сомнительным документам",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            document_check_required_by_contract=True,
            documents_facially_doubtful=True,
            agent_transferred_property_despite_doubt=True,
        ),
        expected_outcomes={
            "document_check_breach": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-document-check-permitted",
        title_ru="Договор разрешил передачу вопреки сомнению — нарушения нет",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            document_check_required_by_contract=True,
            documents_facially_doubtful=True,
            transfer_despite_doubt_permitted_by_contract=True,
            agent_transferred_property_despite_doubt=True,
        ),
        expected_outcomes={"document_check_breach": False},
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-substantive-check-breach",
        title_ru="Договор возложил проверку оснований по существу, агент её не провёл",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            substantive_check_agreed_by_contract=True,
            agent_transferred_without_verifying_grounds=True,
        ),
        expected_outcomes={
            "substantive_check_breach": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-segregation-breach",
        title_ru="Депонированное имущество смешано с имуществом агента",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            deposited_property_commingled_with_agents_own=True,
        ),
        expected_outcomes={
            "segregation_breach": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-use-or-disposal-breach",
        title_ru="Агент использовал депонированное имущество без разрешения",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            agent_used_or_disposed_deposited_property=True,
        ),
        expected_outcomes={
            "use_or_disposal_breach": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-use-or-disposal-permitted",
        title_ru="Договор разрешил использование — нарушения нет",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            use_or_disposal_permitted_by_contract_or_nature=True,
            agent_used_or_disposed_deposited_property=True,
        ),
        expected_outcomes={"use_or_disposal_breach": False},
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-title-passes-on-grounds",
        title_ru="Право собственности на вещи переходит к бенефициару при наступлении оснований",
        facts=_facts(**_THINGS, notarization_performed=True, **_GROUNDED),
        expected_outcomes={
            "depositor_retains_title": False,
            "title_passed_to_beneficiary": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-agent-liability-for-loss",
        title_ru="Агент отвечает за утрату вещи без доказанных оснований освобождения",
        facts=_facts(
            **_THINGS, notarization_performed=True, thing_lost_damaged_or_short=True
        ),
        expected_outcomes={
            "agent_liability_for_things_breached": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-agent-liability-force-majeure",
        title_ru="Утрата вследствие непреодолимой силы — агент не отвечает",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            thing_lost_damaged_or_short=True,
            agent_proved_force_majeure=True,
        ),
        expected_outcomes={
            "agent_liability_for_things_breached": False,
            "requires_human_escrow_deposit_assessment": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-securities-disposal-breach",
        title_ru="Агент распорядился ценными бумагами без разрешения договора",
        facts=_facts(
            **_SECURITIES, agent_disposed_or_exercised_rights_on_securities=True
        ),
        expected_outcomes={
            "securities_disposal_breach": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-securities-disposal-permitted",
        title_ru="Договор разрешил осуществление прав по бумагам — нарушения нет",
        facts=_facts(
            **_SECURITIES,
            securities_exercise_permitted_by_contract=True,
            agent_disposed_or_exercised_rights_on_securities=True,
        ),
        expected_outcomes={"securities_disposal_breach": False},
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-money-agent-not-bank",
        title_ru="Агент не банк — безналичные деньги должны идти через номинальный счёт",
        facts=_facts(**_MONEY),
        expected_outcomes={
            "cashless_money_requires_nominal_account": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-money-agent-is-bank",
        title_ru="Агент банк — правило о номинальном счёте не применяется",
        facts=_facts(**_MONEY, escrow_agent_is_bank=True),
        expected_outcomes={
            "cashless_money_requires_nominal_account": False,
            "requires_human_escrow_deposit_assessment": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-insulation-clean",
        title_ru="Депонированное имущество недоступно кредиторам агента и депонента",
        facts=_facts(**_THINGS, notarization_performed=True),
        expected_outcomes={
            "deposited_property_insulated_from_agent_or_depositor_creditors": True,
            "insulation_breach": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-insulation-breached",
        title_ru="По долгу депонента обращено взыскание на депонированное имущество",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            seizure_or_debit_for_agent_or_depositor_debt=True,
        ),
        expected_outcomes={
            "insulation_breach": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-beneficiary-creditor-claim-right",
        title_ru="По долгу бенефициара взыскание обращено на его право требования",
        facts=_facts(
            **_THINGS, notarization_performed=True, seizure_for_beneficiary_debt=True
        ),
        expected_outcomes={
            "beneficiary_creditor_may_reach_claim_right": True,
            "insulation_breach": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-termination-return-to-depositor",
        title_ru="Прекращение по личному основанию агента без наступивших оснований передачи",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            agent_personal_termination_ground=True,
        ),
        expected_outcomes={
            "termination_ground_present": True,
            "return_to_depositor_due": True,
            "transfer_to_beneficiary_due_on_termination": False,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-termination-transfer-to-beneficiary",
        title_ru="Прекращение по истечении срока, основания передачи уже наступили",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            **_GROUNDED,
            deposit_term_expired=True,
        ),
        expected_outcomes={
            "termination_ground_present": True,
            "return_to_depositor_due": False,
            "transfer_to_beneficiary_due_on_termination": True,
        },
    ),
    EscrowDepositEvaluationTask(
        id="escrow-deposit-bench-termination-transferred-to-new-agent",
        title_ru="Договор передан новому лицу до наступления обстоятельства — не прекращается",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            agent_personal_termination_ground=True,
            contract_transferred_under_article_392_3=True,
        ),
        expected_outcomes={
            "contract_transferred_to_new_agent": True,
            "return_to_depositor_due": False,
            "transfer_to_beneficiary_due_on_termination": False,
        },
    ),
)


SYNTHETIC_ESCROW_DEPOSIT_RED_TEAM_CASES = (
    EscrowDepositRedTeamCase(
        id="escrow-deposit-red-kind-from-assertion",
        title_ru="Заявление о договоре эскроу без предмета депонирования не квалифицирует его",
        facts=_facts(escrow_deposit_asserted=True),
        forbidden_outcomes={"escrow_deposit_qualified": True},
    ),
    EscrowDepositRedTeamCase(
        id="escrow-deposit-red-money-does-not-need-notary",
        title_ru="Исключительно денежное депонирование не требует нотариуса даже без банка",
        facts=_facts(**_MONEY),
        forbidden_outcomes={"notarization_required": True},
    ),
    EscrowDepositRedTeamCase(
        id="escrow-deposit-red-excess-term-is-not-void",
        title_ru="Превышение пятилетнего срока — не порок сделки, а подстановка закона",
        facts=_facts(**_THINGS, notarization_performed=True, deposit_term_missing_or_excessive=True),
        forbidden_outcomes={
            "notarization_missing_makes_void": True,
            "requires_human_escrow_deposit_assessment": True,
        },
    ),
    EscrowDepositRedTeamCase(
        id="escrow-deposit-red-things-rules-to-securities",
        title_ru="Правила депонирования вещей не переносятся на ценные бумаги",
        facts=_facts(**_SECURITIES),
        forbidden_outcomes={
            "depositor_retains_title": True,
            "title_passed_to_beneficiary": True,
            "agent_liability_for_things_breached": True,
        },
    ),
    EscrowDepositRedTeamCase(
        id="escrow-deposit-red-beneficiary-seizure-is-not-a-breach",
        title_ru="Обращение взыскания по долгу бенефициара — не нарушение защиты имущества",
        facts=_facts(**_THINGS, seizure_for_beneficiary_debt=True),
        forbidden_outcomes={"insulation_breach": True},
    ),
    EscrowDepositRedTeamCase(
        id="escrow-deposit-red-bank-agent-does-not-need-nominal-account",
        title_ru="Если агент банк, требование о номинальном счёте не возникает",
        facts=_facts(**_MONEY, escrow_agent_is_bank=True),
        forbidden_outcomes={"cashless_money_requires_nominal_account": True},
    ),
    EscrowDepositRedTeamCase(
        id="escrow-deposit-red-commingling-does-not-discharge-agent",
        title_ru="Смешение имущества не прекращает обязательство агента, а нарушает его",
        facts=_facts(
            **_THINGS,
            notarization_performed=True,
            deposited_property_commingled_with_agents_own=True,
            **_GROUNDED,
        ),
        forbidden_outcomes={"title_passed_to_beneficiary": False},
    ),
    EscrowDepositRedTeamCase(
        id="escrow-deposit-red-no-breach-without-qualification",
        title_ru="Без заявленного и квалифицированного договора эскроу нарушений не выводится",
        facts=_facts(
            agent_withheld_or_setoff_deposited_property=True,
            deposited_property_commingled_with_agents_own=True,
            agent_used_or_disposed_deposited_property=True,
        ),
        forbidden_outcomes={
            "agent_setoff_breached": True,
            "segregation_breach": True,
            "use_or_disposal_breach": True,
        },
    ),
)


def _evaluate(facts: EscrowDepositFactSet, artifact_id: str) -> EscrowDepositEvaluation:
    mapping = EscrowDepositEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-escrow-deposit-law"],
    )
    constraints: EscrowDepositConstraintSet = build_escrow_deposit_constraint_set(mapping)
    return evaluate_escrow_deposit_constraints(constraints, facts)


def _outcomes(evaluation: EscrowDepositEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_escrow_deposit_benchmark_suite() -> EscrowDepositBenchmarkReport:
    results = []
    for task in SYNTHETIC_ESCROW_DEPOSIT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            EscrowDepositEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return EscrowDepositBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_escrow_deposit_red_team_suite() -> EscrowDepositRedTeamReport:
    results = []
    for case in SYNTHETIC_ESCROW_DEPOSIT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            EscrowDepositRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return EscrowDepositRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
