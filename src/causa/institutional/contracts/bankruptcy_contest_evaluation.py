from pydantic import BaseModel, Field

from causa.institutional.contracts.bankruptcy_contest import (
    BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS,
    BankruptcyContestConstraintSet,
    BankruptcyContestEvaluation,
    BankruptcyContestEvidenceMappingResult,
    BankruptcyContestFactSet,
    build_bankruptcy_contest_constraint_set,
    evaluate_bankruptcy_contest_constraints,
)


class BankruptcyContestEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: BankruptcyContestFactSet
    expected_outcomes: dict[str, bool]


class BankruptcyContestEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankruptcyContestBenchmarkReport(BaseModel):
    id: str = "bankruptcy-contest-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[BankruptcyContestEvaluationResult] = Field(default_factory=list)


class BankruptcyContestRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: BankruptcyContestFactSet
    forbidden_outcomes: dict[str, bool]


class BankruptcyContestRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankruptcyContestRedTeamReport(BaseModel):
    id: str = "bankruptcy-contest-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[BankruptcyContestRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> BankruptcyContestFactSet:
    values = {field_name: False for field_name in BankruptcyContestFactSet.model_fields}
    values.update(updates)
    return BankruptcyContestFactSet(**values)


SYNTHETIC_BANKRUPTCY_CONTEST_BENCHMARKS = (
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-unequal-consideration",
        title_ru="Неравноценное встречное исполнение в пределах года — подозрительная сделка",
        facts=_facts(
            transaction_within_one_year_before_or_after_petition=True,
            unequal_consideration=True,
            transaction_within_three_years_before_or_after_petition=True,
        ),
        expected_outcomes={
            "voidable_as_unequal_consideration": True,
            "transaction_voidable": True,
            "requires_human_bankruptcy_contest_assessment": True,
        },
    ),
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-outside-one-year-not-voidable",
        title_ru="Неравноценное исполнение вне годичного окна не даёт основания",
        facts=_facts(unequal_consideration=True),
        expected_outcomes={
            "voidable_as_unequal_consideration": False,
            "transaction_voidable": False,
        },
    ),
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-harm-to-creditors",
        title_ru="Вред кредиторам, три года, осведомлённость — подозрительная сделка",
        facts=_facts(
            transaction_within_three_years_before_or_after_petition=True,
            harm_to_creditors_caused=True,
            counterparty_knew_of_harmful_purpose=True,
        ),
        expected_outcomes={
            "voidable_as_harm_to_creditors": True,
            "transaction_voidable": True,
        },
    ),
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-harm-without-knowledge",
        title_ru="Вред кредиторам без осведомлённости контрагента — не основание",
        facts=_facts(
            transaction_within_three_years_before_or_after_petition=True,
            harm_to_creditors_caused=True,
        ),
        expected_outcomes={"voidable_as_harm_to_creditors": False},
    ),
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-preference-short-window",
        title_ru="Предпочтение после подачи заявления — недействительна без доп. условий",
        facts=_facts(
            transaction_after_petition_or_within_one_month_before=True,
            preference_ground_present=True,
        ),
        expected_outcomes={
            "voidable_as_preference_short_window": True,
            "transaction_voidable": True,
            "requires_human_bankruptcy_contest_assessment": False,
        },
    ),
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-preference-six-month-narrow",
        title_ru="Предпочтение за шесть месяцев с узким основанием",
        facts=_facts(
            transaction_within_six_months_before_petition=True,
            preference_ground_present=True,
            preference_narrow_ground_present=True,
        ),
        expected_outcomes={
            "voidable_as_preference_six_month_window": True,
            "transaction_voidable": True,
        },
    ),
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-preference-six-month-knowledge",
        title_ru="Предпочтение за шесть месяцев без узкого основания, но со знанием",
        facts=_facts(
            transaction_within_six_months_before_petition=True,
            preference_ground_present=True,
            counterparty_knew_of_insolvency_signs=True,
        ),
        expected_outcomes={"voidable_as_preference_six_month_window": True},
    ),
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-preference-six-month-neither",
        title_ru="Предпочтение за шесть месяцев без узкого основания и без знания",
        facts=_facts(
            transaction_within_six_months_before_petition=True,
            preference_ground_present=True,
        ),
        expected_outcomes={
            "voidable_as_preference_six_month_window": False,
            "transaction_voidable": False,
        },
    ),
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-standing-administrator",
        title_ru="Управляющий вправе подать заявление",
        facts=_facts(applicant_is_administrator=True),
        expected_outcomes={"standing_to_file": True},
    ),
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-standing-creditor-share",
        title_ru="Кредитор с долей свыше десяти процентов вправе подать заявление",
        facts=_facts(applicant_creditor_share_percent_exceeds_ten=True),
        expected_outcomes={"standing_to_file": True},
    ),
    BankruptcyContestEvaluationTask(
        id="bankruptcy-contest-bench-no-standing",
        title_ru="Ни управляющий, ни кредитор с достаточной долей — нет права на заявление",
        facts=_facts(),
        expected_outcomes={"standing_to_file": False},
    ),
)


SYNTHETIC_BANKRUPTCY_CONTEST_RED_TEAM_CASES = (
    BankruptcyContestRedTeamCase(
        id="bankruptcy-contest-red-void-without-time-window",
        title_ru="Признать сделку недействительной по неравноценности без годичного окна",
        facts=_facts(unequal_consideration=True),
        forbidden_outcomes={"voidable_as_unequal_consideration": True},
    ),
    BankruptcyContestRedTeamCase(
        id="bankruptcy-contest-red-harm-without-purpose-knowledge",
        title_ru="Признать вред кредиторам основанием без осведомлённости контрагента",
        facts=_facts(
            transaction_within_three_years_before_or_after_petition=True,
            harm_to_creditors_caused=True,
        ),
        forbidden_outcomes={"voidable_as_harm_to_creditors": True},
    ),
    BankruptcyContestRedTeamCase(
        id="bankruptcy-contest-red-six-month-without-narrow-or-knowledge",
        title_ru="Признать предпочтение за шесть месяцев без узкого основания и без знания",
        facts=_facts(
            transaction_within_six_months_before_petition=True,
            preference_ground_present=True,
        ),
        forbidden_outcomes={"voidable_as_preference_six_month_window": True},
    ),
    BankruptcyContestRedTeamCase(
        id="bankruptcy-contest-red-short-window-without-ground",
        title_ru="Признать сделку недействительной по предпочтению без самого основания",
        facts=_facts(transaction_after_petition_or_within_one_month_before=True),
        forbidden_outcomes={"voidable_as_preference_short_window": True},
    ),
    BankruptcyContestRedTeamCase(
        id="bankruptcy-contest-red-standing-without-grounds",
        title_ru="Признать право на заявление без управляющего и без достаточной доли",
        facts=_facts(),
        forbidden_outcomes={"standing_to_file": True},
    ),
    BankruptcyContestRedTeamCase(
        id="bankruptcy-contest-red-skip-human-on-unequal-consideration",
        title_ru="Пропустить проверку юристом по неравноценному встречному исполнению",
        facts=_facts(
            transaction_within_one_year_before_or_after_petition=True,
            unequal_consideration=True,
            transaction_within_three_years_before_or_after_petition=True,
        ),
        forbidden_outcomes={"requires_human_bankruptcy_contest_assessment": False},
    ),
    BankruptcyContestRedTeamCase(
        id="bankruptcy-contest-red-human-flag-on-short-window",
        title_ru="Требовать проверку юристом по предпочтению в коротком окне без доп. условий",
        facts=_facts(
            transaction_after_petition_or_within_one_month_before=True,
            preference_ground_present=True,
        ),
        forbidden_outcomes={"requires_human_bankruptcy_contest_assessment": True},
    ),
    BankruptcyContestRedTeamCase(
        id="bankruptcy-contest-red-not-voidable-as-voidable",
        title_ru="Признать сделку недействительной без единого основания",
        facts=_facts(),
        forbidden_outcomes={"transaction_voidable": True},
    ),
)


def _evaluate(facts: BankruptcyContestFactSet, artifact_id: str) -> BankruptcyContestEvaluation:
    mapping = BankruptcyContestEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS),
    )
    constraints: BankruptcyContestConstraintSet = build_bankruptcy_contest_constraint_set(mapping)
    return evaluate_bankruptcy_contest_constraints(constraints, facts)


def _outcomes(evaluation: BankruptcyContestEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_bankruptcy_contest_benchmark_suite() -> BankruptcyContestBenchmarkReport:
    results = []
    for task in SYNTHETIC_BANKRUPTCY_CONTEST_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            BankruptcyContestEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return BankruptcyContestBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_bankruptcy_contest_red_team_suite() -> BankruptcyContestRedTeamReport:
    results = []
    for case in SYNTHETIC_BANKRUPTCY_CONTEST_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            BankruptcyContestRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return BankruptcyContestRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
