from pydantic import BaseModel, Field

from causa.institutional.contracts.transactions import (
    TransactionsConstraintSet,
    TransactionsEvaluation,
    TransactionsEvidenceMappingResult,
    TransactionsFactSet,
    build_transactions_constraint_set,
    evaluate_transactions_constraints,
)


class TransactionsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: TransactionsFactSet
    expected_outcomes: dict[str, bool]


class TransactionsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TransactionsBenchmarkReport(BaseModel):
    id: str = "transactions-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[TransactionsEvaluationResult] = Field(default_factory=list)


class TransactionsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: TransactionsFactSet
    forbidden_outcomes: dict[str, bool]


class TransactionsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TransactionsRedTeamReport(BaseModel):
    id: str = "transactions-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[TransactionsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> TransactionsFactSet:
    values = {field_name: False for field_name in TransactionsFactSet.model_fields}
    values.update(updates)
    return TransactionsFactSet(**values)


SYNTHETIC_TRANSACTIONS_BENCHMARKS = (
    TransactionsEvaluationTask(
        id="transactions-bench-not-qualified",
        title_ru="Совершение сделки не заявлено",
        facts=_facts(parties_count_rules_breached=True),
        expected_outcomes={"transactions_qualified": False},
    ),
    TransactionsEvaluationTask(
        id="transactions-bench-qualified-clean",
        title_ru="Сделка совершена без нарушений",
        facts=_facts(transaction_asserted=True),
        expected_outcomes={
            "transactions_qualified": True,
            "requires_human_transactions_assessment": False,
        },
    ),
    TransactionsEvaluationTask(
        id="transactions-bench-definition",
        title_ru="Действие не отвечает понятию сделки",
        facts=_facts(transaction_asserted=True, transaction_definition_breached=True),
        expected_outcomes={
            "transaction_definition_duty_breached": True,
            "requires_human_transactions_assessment": True,
        },
    ),
    TransactionsEvaluationTask(
        id="transactions-bench-parties-count",
        title_ru="Нарушены правила о видах сделок по числу сторон",
        facts=_facts(transaction_asserted=True, parties_count_rules_breached=True),
        expected_outcomes={
            "parties_count_duty_breached": True,
            "requires_human_transactions_assessment": True,
        },
    ),
    TransactionsEvaluationTask(
        id="transactions-bench-unilateral-effect",
        title_ru="Односторонняя сделка создала обязанности для другого лица",
        facts=_facts(transaction_asserted=True, unilateral_transaction_effect_breached=True),
        expected_outcomes={
            "unilateral_transaction_duty_breached": True,
            "requires_human_transactions_assessment": True,
        },
    ),
    TransactionsEvaluationTask(
        id="transactions-bench-unilateral-regulation",
        title_ru="К односторонней сделке не применены общие положения о договорах",
        facts=_facts(transaction_asserted=True, unilateral_regulation_breached=True),
        expected_outcomes={
            "unilateral_regulation_duty_breached": True,
            "requires_human_transactions_assessment": True,
        },
    ),
    TransactionsEvaluationTask(
        id="transactions-bench-conditional",
        title_ru="Нарушены правила о сделке под отлагательным условием",
        facts=_facts(transaction_asserted=True, conditional_transaction_rules_breached=True),
        expected_outcomes={
            "conditional_transaction_duty_breached": True,
            "requires_human_transactions_assessment": True,
        },
    ),
    TransactionsEvaluationTask(
        id="transactions-bench-condition-interference",
        title_ru="Сторона недобросовестно воспрепятствовала наступлению условия",
        facts=_facts(transaction_asserted=True, condition_interference_in_bad_faith=True),
        expected_outcomes={
            "condition_interference_duty_breached": True,
            "requires_human_transactions_assessment": True,
        },
    ),
    TransactionsEvaluationTask(
        id="transactions-bench-consent-missing",
        title_ru="Сделка совершена без необходимого согласия, а молчание признано согласием",
        facts=_facts(
            transaction_asserted=True,
            statutory_consent_not_obtained=True,
            silence_treated_as_consent=True,
        ),
        expected_outcomes={
            "consent_missing_for_transaction": True,
            "silence_as_consent_breached": True,
            "requires_human_transactions_assessment": True,
        },
    ),
    TransactionsEvaluationTask(
        id="transactions-bench-consent-procedure",
        title_ru="Нарушены порядок и содержание согласия на совершение сделки",
        facts=_facts(transaction_asserted=True, consent_procedure_breached=True),
        expected_outcomes={
            "consent_procedure_duty_breached": True,
            "requires_human_transactions_assessment": True,
        },
    ),
)


SYNTHETIC_TRANSACTIONS_RED_TEAM_CASES = (
    TransactionsRedTeamCase(
        id="transactions-red-qualify-without-transaction",
        title_ru="Применить правила о сделках без совершённой сделки",
        facts=_facts(parties_count_rules_breached=True),
        forbidden_outcomes={"transactions_qualified": True},
    ),
    TransactionsRedTeamCase(
        id="transactions-red-ignore-definition",
        title_ru="Признать сделкой действие, не направленное на правовой результат",
        facts=_facts(transaction_asserted=True, transaction_definition_breached=True),
        forbidden_outcomes={"transaction_definition_duty_breached": False},
    ),
    TransactionsRedTeamCase(
        id="transactions-red-ignore-parties-count",
        title_ru="Заключить договор без выражения согласованной воли сторон",
        facts=_facts(transaction_asserted=True, parties_count_rules_breached=True),
        forbidden_outcomes={"parties_count_duty_breached": False},
    ),
    TransactionsRedTeamCase(
        id="transactions-red-bind-third-party-by-unilateral-act",
        title_ru="Возложить односторонней сделкой обязанности на другое лицо",
        facts=_facts(transaction_asserted=True, unilateral_transaction_effect_breached=True),
        forbidden_outcomes={"unilateral_transaction_duty_breached": False},
    ),
    TransactionsRedTeamCase(
        id="transactions-red-ignore-unilateral-regulation",
        title_ru="Исключить применение общих положений о договорах к односторонней сделке",
        facts=_facts(transaction_asserted=True, unilateral_regulation_breached=True),
        forbidden_outcomes={"unilateral_regulation_duty_breached": False},
    ),
    TransactionsRedTeamCase(
        id="transactions-red-ignore-conditional-rules",
        title_ru="Игнорировать правила о сделках под условием",
        facts=_facts(transaction_asserted=True, conditional_transaction_rules_breached=True),
        forbidden_outcomes={"conditional_transaction_duty_breached": False},
    ),
    TransactionsRedTeamCase(
        id="transactions-red-allow-bad-faith-interference",
        title_ru="Допустить недобросовестное воспрепятствование наступлению условия",
        facts=_facts(transaction_asserted=True, condition_interference_in_bad_faith=True),
        forbidden_outcomes={"condition_interference_duty_breached": False},
    ),
    TransactionsRedTeamCase(
        id="transactions-red-ignore-missing-consent",
        title_ru="Признать сделку совершённой при отсутствии необходимого согласия",
        facts=_facts(transaction_asserted=True, statutory_consent_not_obtained=True),
        forbidden_outcomes={"consent_missing_for_transaction": False},
    ),
    TransactionsRedTeamCase(
        id="transactions-red-ignore-consent-procedure",
        title_ru="Признать согласие без указания предмета сделки",
        facts=_facts(transaction_asserted=True, consent_procedure_breached=True),
        forbidden_outcomes={"consent_procedure_duty_breached": False},
    ),
    TransactionsRedTeamCase(
        id="transactions-red-silence-without-required-consent",
        title_ru="Признать молчание согласием там, где согласие не требовалось",
        facts=_facts(transaction_asserted=True),
        forbidden_outcomes={"silence_as_consent_breached": True},
    ),
)


def _evaluate(facts: TransactionsFactSet, artifact_id: str) -> TransactionsEvaluation:
    mapping = TransactionsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-transactions-law"],
    )
    constraints: TransactionsConstraintSet = build_transactions_constraint_set(mapping)
    return evaluate_transactions_constraints(constraints, facts)


def _outcomes(evaluation: TransactionsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_transactions_benchmark_suite() -> TransactionsBenchmarkReport:
    results = []
    for task in SYNTHETIC_TRANSACTIONS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            TransactionsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return TransactionsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_transactions_red_team_suite() -> TransactionsRedTeamReport:
    results = []
    for case in SYNTHETIC_TRANSACTIONS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            TransactionsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return TransactionsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
