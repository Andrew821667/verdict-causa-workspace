from pydantic import BaseModel, Field

from causa.institutional.contracts.limitation import (
    LimitationConstraintSet,
    LimitationEvaluation,
    LimitationEvidenceMappingResult,
    LimitationFactSet,
    build_limitation_constraint_set,
    evaluate_limitation_constraints,
)


class LimitationEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: LimitationFactSet
    expected_outcomes: dict[str, bool]


class LimitationEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class LimitationBenchmarkReport(BaseModel):
    id: str = "limitation-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[LimitationEvaluationResult] = Field(default_factory=list)


class LimitationRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: LimitationFactSet
    forbidden_outcomes: dict[str, bool]


class LimitationRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class LimitationRedTeamReport(BaseModel):
    id: str = "limitation-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[LimitationRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> LimitationFactSet:
    values = {field_name: False for field_name in LimitationFactSet.model_fields}
    # По умолчанию — требование подпадает под давность, течение началось (статьи 195, 200).
    values.update(claim_subject_to_limitation=True, right_violation_and_defendant_known=True)
    values.update(updates)
    return LimitationFactSet(**values)


SYNTHETIC_LIMITATION_BENCHMARKS = (
    LimitationEvaluationTask(
        id="limitation-bench-expired-pleaded",
        title_ru="Общий срок истек и заявлен стороной",
        facts=_facts(
            general_three_year_term_elapsed=True,
            limitation_pleaded_by_party_before_judgment=True,
        ),
        expected_outcomes={
            "limitation_period_expired": True,
            "limitation_defense_available": True,
        },
    ),
    LimitationEvaluationTask(
        id="limitation-bench-expired-not-pleaded",
        title_ru="Общий срок истек, но не заявлен стороной",
        facts=_facts(general_three_year_term_elapsed=True),
        expected_outcomes={
            "limitation_period_expired": True,
            "limitation_defense_available": False,
            "requires_human_limitation_assessment": True,
        },
    ),
    LimitationEvaluationTask(
        id="limitation-bench-acknowledged",
        title_ru="Признание долга прерывает течение давности",
        facts=_facts(
            general_three_year_term_elapsed=True,
            debtor_acknowledged_debt=True,
            limitation_pleaded_by_party_before_judgment=True,
        ),
        expected_outcomes={
            "limitation_reset_by_acknowledgement": True,
            "limitation_period_expired": False,
        },
    ),
    LimitationEvaluationTask(
        id="limitation-bench-suspended",
        title_ru="Приостановление течения в последние шесть месяцев",
        facts=_facts(
            general_three_year_term_elapsed=True,
            suspension_ground_in_final_six_months=True,
            limitation_pleaded_by_party_before_judgment=True,
        ),
        expected_outcomes={
            "limitation_suspended": True,
            "limitation_period_expired": False,
        },
    ),
    LimitationEvaluationTask(
        id="limitation-bench-special-term",
        title_ru="Истечение специального срока давности",
        facts=_facts(
            special_term_applies=True,
            special_term_elapsed=True,
            limitation_pleaded_by_party_before_judgment=True,
        ),
        expected_outcomes={
            "limitation_period_expired": True,
            "limitation_defense_available": True,
        },
    ),
    LimitationEvaluationTask(
        id="limitation-bench-objective-limit",
        title_ru="Превышение предельного десятилетнего срока",
        facts=_facts(
            objective_ten_year_limit_exceeded=True,
            limitation_pleaded_by_party_before_judgment=True,
        ),
        expected_outcomes={
            "objective_limit_barred": True,
            "limitation_period_expired": True,
        },
    ),
    LimitationEvaluationTask(
        id="limitation-bench-not-subject",
        title_ru="Требование, на которое давность не распространяется",
        facts=_facts(
            claim_subject_to_limitation=False,
            general_three_year_term_elapsed=True,
            limitation_pleaded_by_party_before_judgment=True,
        ),
        expected_outcomes={
            "claim_not_subject_to_limitation": True,
            "limitation_period_expired": False,
        },
    ),
    LimitationEvaluationTask(
        id="limitation-bench-restorable",
        title_ru="Восстановление срока гражданину при уважительной причине",
        facts=_facts(
            general_three_year_term_elapsed=True,
            claimant_is_individual_with_valid_excuse=True,
        ),
        expected_outcomes={
            "limitation_period_expired": True,
            "limitation_restorable": True,
        },
    ),
    LimitationEvaluationTask(
        id="limitation-bench-additional-claim",
        title_ru="Дополнительное требование при истекшем главном",
        facts=_facts(is_additional_claim=True, main_claim_time_barred=True),
        expected_outcomes={"additional_claim_barred_with_main": True},
    ),
    LimitationEvaluationTask(
        id="limitation-bench-not-started",
        title_ru="Течение давности еще не началось",
        facts=_facts(
            right_violation_and_defendant_known=False,
            general_three_year_term_elapsed=True,
            limitation_pleaded_by_party_before_judgment=True,
        ),
        expected_outcomes={
            "limitation_period_started": False,
            "limitation_period_expired": False,
        },
    ),
)


SYNTHETIC_LIMITATION_RED_TEAM_CASES = (
    LimitationRedTeamCase(
        id="limitation-red-expired-not-started",
        title_ru="Признать давность истекшей без начала течения",
        facts=_facts(
            right_violation_and_defendant_known=False,
            general_three_year_term_elapsed=True,
        ),
        forbidden_outcomes={"limitation_period_expired": True},
    ),
    LimitationRedTeamCase(
        id="limitation-red-defense-without-plea",
        title_ru="Применить давность без заявления стороны",
        facts=_facts(general_three_year_term_elapsed=True),
        forbidden_outcomes={"limitation_defense_available": True},
    ),
    LimitationRedTeamCase(
        id="limitation-red-ignore-acknowledgement",
        title_ru="Игнорировать перерыв давности признанием долга",
        facts=_facts(
            general_three_year_term_elapsed=True,
            debtor_acknowledged_debt=True,
        ),
        forbidden_outcomes={"limitation_period_expired": True},
    ),
    LimitationRedTeamCase(
        id="limitation-red-ignore-suspension",
        title_ru="Игнорировать приостановление течения давности",
        facts=_facts(
            general_three_year_term_elapsed=True,
            suspension_ground_in_final_six_months=True,
        ),
        forbidden_outcomes={"limitation_period_expired": True},
    ),
    LimitationRedTeamCase(
        id="limitation-red-apply-to-exempt-claim",
        title_ru="Применить давность к требованию по статье 208",
        facts=_facts(
            claim_subject_to_limitation=False,
            general_three_year_term_elapsed=True,
            limitation_pleaded_by_party_before_judgment=True,
        ),
        forbidden_outcomes={"limitation_period_expired": True},
    ),
    LimitationRedTeamCase(
        id="limitation-red-special-not-elapsed",
        title_ru="Считать давность истекшей при неистекшем специальном сроке",
        facts=_facts(
            special_term_applies=True,
            general_three_year_term_elapsed=True,
            limitation_pleaded_by_party_before_judgment=True,
        ),
        forbidden_outcomes={"limitation_period_expired": True},
    ),
    LimitationRedTeamCase(
        id="limitation-red-deny-restoration",
        title_ru="Отказать гражданину в возможности восстановления срока",
        facts=_facts(
            general_three_year_term_elapsed=True,
            claimant_is_individual_with_valid_excuse=True,
        ),
        forbidden_outcomes={"limitation_restorable": False},
    ),
    LimitationRedTeamCase(
        id="limitation-red-keep-additional-claim",
        title_ru="Сохранить дополнительное требование при истекшем главном",
        facts=_facts(is_additional_claim=True, main_claim_time_barred=True),
        forbidden_outcomes={"additional_claim_barred_with_main": False},
    ),
    LimitationRedTeamCase(
        id="limitation-red-objective-without-excess",
        title_ru="Признать предельный срок истекшим без его превышения",
        facts=_facts(general_three_year_term_elapsed=True),
        forbidden_outcomes={"objective_limit_barred": True},
    ),
    LimitationRedTeamCase(
        id="limitation-red-start-without-ground",
        title_ru="Начать течение давности без основания",
        facts=_facts(right_violation_and_defendant_known=False),
        forbidden_outcomes={"limitation_period_started": True},
    ),
)


def _evaluate(facts: LimitationFactSet, artifact_id: str) -> LimitationEvaluation:
    mapping = LimitationEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-limitation-law"],
    )
    constraints: LimitationConstraintSet = build_limitation_constraint_set(mapping)
    return evaluate_limitation_constraints(constraints, facts)


def _outcomes(evaluation: LimitationEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_limitation_benchmark_suite() -> LimitationBenchmarkReport:
    results = []
    for task in SYNTHETIC_LIMITATION_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            LimitationEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return LimitationBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_limitation_red_team_suite() -> LimitationRedTeamReport:
    results = []
    for case in SYNTHETIC_LIMITATION_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            LimitationRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return LimitationRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
