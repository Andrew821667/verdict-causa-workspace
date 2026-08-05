from pydantic import BaseModel, Field

from causa.institutional.contracts.partnership import (
    PartnershipConstraintSet,
    PartnershipEvaluation,
    PartnershipEvidenceMappingResult,
    PartnershipFactSet,
    build_partnership_constraint_set,
    evaluate_partnership_constraints,
)


class PartnershipEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: PartnershipFactSet
    expected_outcomes: dict[str, bool]


class PartnershipEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PartnershipBenchmarkReport(BaseModel):
    id: str = "partnership-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[PartnershipEvaluationResult] = Field(default_factory=list)


class PartnershipRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: PartnershipFactSet
    forbidden_outcomes: dict[str, bool]


class PartnershipRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PartnershipRedTeamReport(BaseModel):
    id: str = "partnership-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[PartnershipRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> PartnershipFactSet:
    values = {field_name: False for field_name in PartnershipFactSet.model_fields}
    values.update(updates)
    return PartnershipFactSet(**values)


SYNTHETIC_PARTNERSHIP_BENCHMARKS = (
    PartnershipEvaluationTask(
        id="partnership-bench-not-qualified",
        title_ru="Договор простого товарищества не заключён",
        facts=_facts(common_affairs_conduct_breached=True),
        expected_outcomes={"partnership_qualified": False},
    ),
    PartnershipEvaluationTask(
        id="partnership-bench-qualified-clean",
        title_ru="Договор простого товарищества без нарушений",
        facts=_facts(partnership_contract_concluded=True),
        expected_outcomes={
            "partnership_qualified": True,
            "requires_human_partnership_assessment": False,
        },
    ),
    PartnershipEvaluationTask(
        id="partnership-bench-parties-and-purpose",
        title_ru="Состав сторон и цель совместной деятельности определены с нарушением",
        facts=_facts(
            partnership_contract_concluded=True,
            partnership_parties_or_purpose_breached=True,
        ),
        expected_outcomes={
            "parties_and_purpose_duty_breached": True,
            "requires_human_partnership_assessment": True,
        },
    ),
    PartnershipEvaluationTask(
        id="partnership-bench-contributions",
        title_ru="Нарушены правила о вкладах товарищей и общем имуществе",
        facts=_facts(
            partnership_contract_concluded=True,
            contributions_or_common_property_breached=True,
        ),
        expected_outcomes={
            "contributions_and_common_property_duty_breached": True,
            "requires_human_partnership_assessment": True,
        },
    ),
    PartnershipEvaluationTask(
        id="partnership-bench-common-affairs",
        title_ru="Нарушен порядок ведения общих дел товарищей",
        facts=_facts(
            partnership_contract_concluded=True,
            common_affairs_conduct_breached=True,
        ),
        expected_outcomes={
            "common_affairs_duty_breached": True,
            "requires_human_partnership_assessment": True,
        },
    ),
    PartnershipEvaluationTask(
        id="partnership-bench-information-and-expenses",
        title_ru="Нарушены право на информацию и распределение общих расходов",
        facts=_facts(
            partnership_contract_concluded=True,
            information_or_expense_sharing_breached=True,
        ),
        expected_outcomes={
            "information_and_expenses_duty_breached": True,
            "requires_human_partnership_assessment": True,
        },
    ),
    PartnershipEvaluationTask(
        id="partnership-bench-liability",
        title_ru="Нарушены правила об ответственности товарищей по общим обязательствам",
        facts=_facts(
            partnership_contract_concluded=True,
            partners_liability_rules_breached=True,
        ),
        expected_outcomes={
            "partners_liability_duty_breached": True,
            "requires_human_partnership_assessment": True,
        },
    ),
    PartnershipEvaluationTask(
        id="partnership-bench-profit-distribution",
        title_ru="Прибыль распределена с нарушением, ничтожность отстранения не применена",
        facts=_facts(
            partnership_contract_concluded=True,
            profit_distribution_rules_breached=True,
            profit_exclusion_void_not_applied=True,
        ),
        expected_outcomes={
            "profit_distribution_duty_breached": True,
            "profit_exclusion_void_breached": True,
            "requires_human_partnership_assessment": True,
        },
    ),
    PartnershipEvaluationTask(
        id="partnership-bench-termination",
        title_ru="Нарушены выдел доли, прекращение договора и выход товарища",
        facts=_facts(
            partnership_contract_concluded=True,
            termination_or_withdrawal_rules_breached=True,
        ),
        expected_outcomes={
            "termination_and_withdrawal_duty_breached": True,
            "requires_human_partnership_assessment": True,
        },
    ),
    PartnershipEvaluationTask(
        id="partnership-bench-undisclosed",
        title_ru="Нарушены правила о негласном товариществе",
        facts=_facts(
            partnership_contract_concluded=True,
            undisclosed_partnership_rules_breached=True,
        ),
        expected_outcomes={
            "undisclosed_partnership_duty_breached": True,
            "requires_human_partnership_assessment": True,
        },
    ),
)


SYNTHETIC_PARTNERSHIP_RED_TEAM_CASES = (
    PartnershipRedTeamCase(
        id="partnership-red-qualify-without-contract",
        title_ru="Квалифицировать простое товарищество без заключения договора",
        facts=_facts(common_affairs_conduct_breached=True),
        forbidden_outcomes={"partnership_qualified": True},
    ),
    PartnershipRedTeamCase(
        id="partnership-red-ignore-parties-and-purpose",
        title_ru="Игнорировать недопустимый состав сторон товарищества",
        facts=_facts(
            partnership_contract_concluded=True,
            partnership_parties_or_purpose_breached=True,
        ),
        forbidden_outcomes={"parties_and_purpose_duty_breached": False},
    ),
    PartnershipRedTeamCase(
        id="partnership-red-ignore-contributions",
        title_ru="Игнорировать нарушение правил о вкладах и общем имуществе",
        facts=_facts(
            partnership_contract_concluded=True,
            contributions_or_common_property_breached=True,
        ),
        forbidden_outcomes={"contributions_and_common_property_duty_breached": False},
    ),
    PartnershipRedTeamCase(
        id="partnership-red-ignore-common-affairs",
        title_ru="Противопоставить третьему лицу неизвестные ему ограничения полномочий",
        facts=_facts(
            partnership_contract_concluded=True,
            common_affairs_conduct_breached=True,
        ),
        forbidden_outcomes={"common_affairs_duty_breached": False},
    ),
    PartnershipRedTeamCase(
        id="partnership-red-ignore-information-right",
        title_ru="Ограничить право товарища знакомиться с документацией по ведению дел",
        facts=_facts(
            partnership_contract_concluded=True,
            information_or_expense_sharing_breached=True,
        ),
        forbidden_outcomes={"information_and_expenses_duty_breached": False},
    ),
    PartnershipRedTeamCase(
        id="partnership-red-ignore-liability",
        title_ru="Освободить товарищей от солидарной ответственности по общим обязательствам",
        facts=_facts(
            partnership_contract_concluded=True,
            partners_liability_rules_breached=True,
        ),
        forbidden_outcomes={"partners_liability_duty_breached": False},
    ),
    PartnershipRedTeamCase(
        id="partnership-red-ignore-profit-distribution",
        title_ru="Игнорировать нарушение правил о распределении прибыли",
        facts=_facts(
            partnership_contract_concluded=True,
            profit_distribution_rules_breached=True,
        ),
        forbidden_outcomes={"profit_distribution_duty_breached": False},
    ),
    PartnershipRedTeamCase(
        id="partnership-red-void-exclusion-without-profit-breach",
        title_ru="Признать ничтожность отстранения от прибыли без нарушения её распределения",
        facts=_facts(partnership_contract_concluded=True),
        forbidden_outcomes={"profit_exclusion_void_breached": True},
    ),
    PartnershipRedTeamCase(
        id="partnership-red-ignore-termination",
        title_ru="Игнорировать нарушение порядка прекращения договора и выхода товарища",
        facts=_facts(
            partnership_contract_concluded=True,
            termination_or_withdrawal_rules_breached=True,
        ),
        forbidden_outcomes={"termination_and_withdrawal_duty_breached": False},
    ),
    PartnershipRedTeamCase(
        id="partnership-red-skip-human-on-undisclosed",
        title_ru="Пропустить экспертизу при нарушении правил о негласном товариществе",
        facts=_facts(
            partnership_contract_concluded=True,
            undisclosed_partnership_rules_breached=True,
        ),
        forbidden_outcomes={"requires_human_partnership_assessment": False},
    ),
)


def _evaluate(facts: PartnershipFactSet, artifact_id: str) -> PartnershipEvaluation:
    mapping = PartnershipEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-partnership-law"],
    )
    constraints: PartnershipConstraintSet = build_partnership_constraint_set(mapping)
    return evaluate_partnership_constraints(constraints, facts)


def _outcomes(evaluation: PartnershipEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_partnership_benchmark_suite() -> PartnershipBenchmarkReport:
    results = []
    for task in SYNTHETIC_PARTNERSHIP_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            PartnershipEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return PartnershipBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_partnership_red_team_suite() -> PartnershipRedTeamReport:
    results = []
    for case in SYNTHETIC_PARTNERSHIP_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            PartnershipRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return PartnershipRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
