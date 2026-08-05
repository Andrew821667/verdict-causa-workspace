from pydantic import BaseModel, Field

from causa.institutional.contracts.public_promise import (
    PublicPromiseConstraintSet,
    PublicPromiseEvaluation,
    PublicPromiseEvidenceMappingResult,
    PublicPromiseFactSet,
    build_public_promise_constraint_set,
    evaluate_public_promise_constraints,
)


class PublicPromiseEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: PublicPromiseFactSet
    expected_outcomes: dict[str, bool]


class PublicPromiseEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PublicPromiseBenchmarkReport(BaseModel):
    id: str = "public-promise-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[PublicPromiseEvaluationResult] = Field(default_factory=list)


class PublicPromiseRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: PublicPromiseFactSet
    forbidden_outcomes: dict[str, bool]


class PublicPromiseRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PublicPromiseRedTeamReport(BaseModel):
    id: str = "public-promise-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[PublicPromiseRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> PublicPromiseFactSet:
    values = {field_name: False for field_name in PublicPromiseFactSet.model_fields}
    values.update(updates)
    return PublicPromiseFactSet(**values)


SYNTHETIC_PUBLIC_PROMISE_BENCHMARKS = (
    PublicPromiseEvaluationTask(
        id="public-promise-bench-not-qualified",
        title_ru="Публичное обещание награды и конкурс не объявлялись",
        facts=_facts(contest_works_return_breached=True),
        expected_outcomes={"public_promise_qualified": False},
    ),
    PublicPromiseEvaluationTask(
        id="public-promise-bench-qualified-clean",
        title_ru="Публичное обещание награды без нарушений",
        facts=_facts(public_promise_or_contest_declared=True),
        expected_outcomes={
            "public_promise_qualified": True,
            "requires_human_public_promise_assessment": False,
        },
    ),
    PublicPromiseEvaluationTask(
        id="public-promise-bench-announcement",
        title_ru="Объявление не позволяет установить, кем обещана награда",
        facts=_facts(
            public_promise_or_contest_declared=True,
            promise_announcement_requirements_breached=True,
        ),
        expected_outcomes={
            "announcement_requirements_duty_breached": True,
            "requires_human_public_promise_assessment": True,
        },
    ),
    PublicPromiseEvaluationTask(
        id="public-promise-bench-reward-amount",
        title_ru="Размер награды и её распределение определены с нарушением",
        facts=_facts(
            public_promise_or_contest_declared=True,
            reward_amount_or_distribution_breached=True,
        ),
        expected_outcomes={
            "reward_amount_and_distribution_duty_breached": True,
            "requires_human_public_promise_assessment": True,
        },
    ),
    PublicPromiseEvaluationTask(
        id="public-promise-bench-revocation",
        title_ru="Обещание отменено с нарушением, расходы отозвавшимся не возмещены",
        facts=_facts(
            public_promise_or_contest_declared=True,
            promise_revocation_rules_breached=True,
            revocation_expense_compensation_not_applied=True,
        ),
        expected_outcomes={
            "promise_revocation_duty_breached": True,
            "revocation_expense_compensation_breached": True,
            "requires_human_public_promise_assessment": True,
        },
    ),
    PublicPromiseEvaluationTask(
        id="public-promise-bench-contest-terms",
        title_ru="Объявление о конкурсе не содержит обязательных условий",
        facts=_facts(
            public_promise_or_contest_declared=True,
            contest_announcement_terms_breached=True,
        ),
        expected_outcomes={
            "contest_terms_duty_breached": True,
            "requires_human_public_promise_assessment": True,
        },
    ),
    PublicPromiseEvaluationTask(
        id="public-promise-bench-public-purpose",
        title_ru="Публичный конкурс не направлен на общественно полезные цели",
        facts=_facts(
            public_promise_or_contest_declared=True,
            contest_public_purpose_breached=True,
        ),
        expected_outcomes={
            "contest_public_purpose_duty_breached": True,
            "requires_human_public_promise_assessment": True,
        },
    ),
    PublicPromiseEvaluationTask(
        id="public-promise-bench-contest-change",
        title_ru="Условия конкурса изменены и конкурс отменён с нарушением",
        facts=_facts(
            public_promise_or_contest_declared=True,
            contest_change_or_cancellation_breached=True,
        ),
        expected_outcomes={
            "contest_change_duty_breached": True,
            "requires_human_public_promise_assessment": True,
        },
    ),
    PublicPromiseEvaluationTask(
        id="public-promise-bench-award-decision",
        title_ru="Решение о выплате награды принято с нарушением",
        facts=_facts(
            public_promise_or_contest_declared=True,
            contest_award_decision_breached=True,
        ),
        expected_outcomes={
            "contest_award_decision_duty_breached": True,
            "requires_human_public_promise_assessment": True,
        },
    ),
    PublicPromiseEvaluationTask(
        id="public-promise-bench-works-return",
        title_ru="Работы, не удостоенные награды, участникам не возвращены",
        facts=_facts(
            public_promise_or_contest_declared=True,
            contest_works_return_breached=True,
        ),
        expected_outcomes={
            "contest_works_duty_breached": True,
            "requires_human_public_promise_assessment": True,
        },
    ),
)


SYNTHETIC_PUBLIC_PROMISE_RED_TEAM_CASES = (
    PublicPromiseRedTeamCase(
        id="public-promise-red-qualify-without-announcement",
        title_ru="Квалифицировать публичное обещание награды без объявления",
        facts=_facts(contest_works_return_breached=True),
        forbidden_outcomes={"public_promise_qualified": True},
    ),
    PublicPromiseRedTeamCase(
        id="public-promise-red-ignore-announcement",
        title_ru="Взыскать награду по объявлению неустановленного лица",
        facts=_facts(
            public_promise_or_contest_declared=True,
            promise_announcement_requirements_breached=True,
        ),
        forbidden_outcomes={"announcement_requirements_duty_breached": False},
    ),
    PublicPromiseRedTeamCase(
        id="public-promise-red-ignore-reward-amount",
        title_ru="Игнорировать нарушение правил о размере и распределении награды",
        facts=_facts(
            public_promise_or_contest_declared=True,
            reward_amount_or_distribution_breached=True,
        ),
        forbidden_outcomes={"reward_amount_and_distribution_duty_breached": False},
    ),
    PublicPromiseRedTeamCase(
        id="public-promise-red-ignore-revocation",
        title_ru="Отменить обещание награды после совершения указанного действия",
        facts=_facts(
            public_promise_or_contest_declared=True,
            promise_revocation_rules_breached=True,
        ),
        forbidden_outcomes={"promise_revocation_duty_breached": False},
    ),
    PublicPromiseRedTeamCase(
        id="public-promise-red-compensation-without-revocation-breach",
        title_ru="Признать невозмещение расходов без нарушения правил об отмене обещания",
        facts=_facts(public_promise_or_contest_declared=True),
        forbidden_outcomes={"revocation_expense_compensation_breached": True},
    ),
    PublicPromiseRedTeamCase(
        id="public-promise-red-ignore-contest-terms",
        title_ru="Признать конкурс объявленным без существа задания и критериев оценки",
        facts=_facts(
            public_promise_or_contest_declared=True,
            contest_announcement_terms_breached=True,
        ),
        forbidden_outcomes={"contest_terms_duty_breached": False},
    ),
    PublicPromiseRedTeamCase(
        id="public-promise-red-ignore-public-purpose",
        title_ru="Игнорировать отсутствие общественно полезной цели конкурса",
        facts=_facts(
            public_promise_or_contest_declared=True,
            contest_public_purpose_breached=True,
        ),
        forbidden_outcomes={"contest_public_purpose_duty_breached": False},
    ),
    PublicPromiseRedTeamCase(
        id="public-promise-red-ignore-contest-change",
        title_ru="Отменить конкурс во второй половине срока представления работ",
        facts=_facts(
            public_promise_or_contest_declared=True,
            contest_change_or_cancellation_breached=True,
        ),
        forbidden_outcomes={"contest_change_duty_breached": False},
    ),
    PublicPromiseRedTeamCase(
        id="public-promise-red-ignore-award-decision",
        title_ru="Игнорировать нарушение порядка и сроков объявления результатов конкурса",
        facts=_facts(
            public_promise_or_contest_declared=True,
            contest_award_decision_breached=True,
        ),
        forbidden_outcomes={"contest_award_decision_duty_breached": False},
    ),
    PublicPromiseRedTeamCase(
        id="public-promise-red-skip-human-on-works-return",
        title_ru="Пропустить экспертизу при невозврате работ участникам конкурса",
        facts=_facts(
            public_promise_or_contest_declared=True,
            contest_works_return_breached=True,
        ),
        forbidden_outcomes={"requires_human_public_promise_assessment": False},
    ),
)


def _evaluate(facts: PublicPromiseFactSet, artifact_id: str) -> PublicPromiseEvaluation:
    mapping = PublicPromiseEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-public-promise-law"],
    )
    constraints: PublicPromiseConstraintSet = build_public_promise_constraint_set(mapping)
    return evaluate_public_promise_constraints(constraints, facts)


def _outcomes(evaluation: PublicPromiseEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_public_promise_benchmark_suite() -> PublicPromiseBenchmarkReport:
    results = []
    for task in SYNTHETIC_PUBLIC_PROMISE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            PublicPromiseEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return PublicPromiseBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_public_promise_red_team_suite() -> PublicPromiseRedTeamReport:
    results = []
    for case in SYNTHETIC_PUBLIC_PROMISE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            PublicPromiseRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return PublicPromiseRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
