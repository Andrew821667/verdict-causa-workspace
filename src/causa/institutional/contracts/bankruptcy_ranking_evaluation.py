from pydantic import BaseModel, Field

from causa.institutional.contracts.bankruptcy_ranking import (
    BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS,
    BankruptcyRankingConstraintSet,
    BankruptcyRankingEvaluation,
    BankruptcyRankingEvidenceMappingResult,
    BankruptcyRankingFactSet,
    build_bankruptcy_ranking_constraint_set,
    evaluate_bankruptcy_ranking_constraints,
)


class BankruptcyRankingEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: BankruptcyRankingFactSet
    expected_outcomes: dict[str, bool]


class BankruptcyRankingEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankruptcyRankingBenchmarkReport(BaseModel):
    id: str = "bankruptcy-ranking-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[BankruptcyRankingEvaluationResult] = Field(default_factory=list)


class BankruptcyRankingRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: BankruptcyRankingFactSet
    forbidden_outcomes: dict[str, bool]


class BankruptcyRankingRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankruptcyRankingRedTeamReport(BaseModel):
    id: str = "bankruptcy-ranking-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[BankruptcyRankingRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> BankruptcyRankingFactSet:
    """Факты по требованию, включённому в реестр требований кредиторов.

    `claim_filed_in_bankruptcy_register` по умолчанию истинно: все случаи ниже,
    кроме прямо проверяющих сами ворота, разбирают уже реестровое требование.
    """
    values = {field_name: False for field_name in BankruptcyRankingFactSet.model_fields}
    values["claim_filed_in_bankruptcy_register"] = True
    values.update(updates)
    return BankruptcyRankingFactSet(**values)


SYNTHETIC_BANKRUPTCY_RANKING_BENCHMARKS = (
    BankruptcyRankingEvaluationTask(
        id="bankruptcy-ranking-bench-first-tier",
        title_ru="Вред жизни или здоровью — первая очередь",
        facts=_facts(is_life_or_health_harm_claim=True),
        expected_outcomes={
            "first_tier": True,
            "third_tier": False,
            "requires_human_bankruptcy_ranking_assessment": True,
        },
    ),
    BankruptcyRankingEvaluationTask(
        id="bankruptcy-ranking-bench-second-tier",
        title_ru="Оплата труда — вторая очередь",
        facts=_facts(is_wage_severance_or_authorship_claim=True),
        expected_outcomes={"second_tier": True, "third_tier": False},
    ),
    BankruptcyRankingEvaluationTask(
        id="bankruptcy-ranking-bench-third-tier-default",
        title_ru="Обычное требование без особых признаков — третья очередь",
        facts=_facts(),
        expected_outcomes={
            "third_tier": True,
            "first_tier": False,
            "second_tier": False,
            "subordinated_after_third_tier": False,
        },
    ),
    BankruptcyRankingEvaluationTask(
        id="bankruptcy-ranking-bench-secured",
        title_ru="Залоговое требование удовлетворяется из предмета залога",
        facts=_facts(is_secured_by_pledge=True),
        expected_outcomes={
            "satisfied_from_pledge_proceeds": True,
            "third_tier": False,
            "requires_human_bankruptcy_ranking_assessment": True,
        },
    ),
    BankruptcyRankingEvaluationTask(
        id="bankruptcy-ranking-bench-avoided-transaction",
        title_ru="Требование из недействительной сделки — после третьей очереди",
        facts=_facts(is_claim_from_avoided_transaction=True),
        expected_outcomes={
            "subordinated_after_third_tier": True,
            "third_tier": False,
        },
    ),
    BankruptcyRankingEvaluationTask(
        id="bankruptcy-ranking-bench-perpetual-bond",
        title_ru="Облигации без срока погашения — после всех иных кредиторов",
        facts=_facts(is_perpetual_bond_claim=True),
        expected_outcomes={
            "satisfied_last_after_all_other_creditors": True,
            "third_tier": False,
        },
    ),
    BankruptcyRankingEvaluationTask(
        id="bankruptcy-ranking-bench-second-tier-no-human-flag",
        title_ru="Вторая очередь не требует расчёта капитализации или залога",
        facts=_facts(is_wage_severance_or_authorship_claim=True),
        expected_outcomes={"requires_human_bankruptcy_ranking_assessment": False},
    ),
    BankruptcyRankingEvaluationTask(
        id="bankruptcy-ranking-bench-not-in-register",
        title_ru="Требование не в реестре — очерёдность к нему не применяется",
        facts=_facts(claim_filed_in_bankruptcy_register=False),
        expected_outcomes={
            "first_tier": False,
            "second_tier": False,
            "third_tier": False,
            "subordinated_after_third_tier": False,
            "satisfied_from_pledge_proceeds": False,
            "satisfied_last_after_all_other_creditors": False,
            "requires_human_bankruptcy_ranking_assessment": False,
        },
    ),
)


SYNTHETIC_BANKRUPTCY_RANKING_RED_TEAM_CASES = (
    BankruptcyRankingRedTeamCase(
        id="bankruptcy-ranking-red-harm-as-third-tier",
        title_ru="Понизить вред жизни или здоровью до третьей очереди",
        facts=_facts(is_life_or_health_harm_claim=True),
        forbidden_outcomes={"third_tier": True},
    ),
    BankruptcyRankingRedTeamCase(
        id="bankruptcy-ranking-red-wages-as-first-tier",
        title_ru="Повысить оплату труда до первой очереди",
        facts=_facts(is_wage_severance_or_authorship_claim=True),
        forbidden_outcomes={"first_tier": True},
    ),
    BankruptcyRankingRedTeamCase(
        id="bankruptcy-ranking-red-secured-in-tiers",
        title_ru="Провести залоговое требование через очереди пункта 4 статьи 134",
        facts=_facts(is_secured_by_pledge=True),
        forbidden_outcomes={"third_tier": True},
    ),
    BankruptcyRankingRedTeamCase(
        id="bankruptcy-ranking-red-avoided-as-ordinary-third-tier",
        title_ru="Уравнять требование из недействительной сделки с обычной третьей очередью",
        facts=_facts(is_claim_from_avoided_transaction=True),
        forbidden_outcomes={"third_tier": True},
    ),
    BankruptcyRankingRedTeamCase(
        id="bankruptcy-ranking-red-perpetual-bond-as-third-tier",
        title_ru="Уравнять облигации без срока погашения с третьей очередью",
        facts=_facts(is_perpetual_bond_claim=True),
        forbidden_outcomes={"third_tier": True},
    ),
    BankruptcyRankingRedTeamCase(
        id="bankruptcy-ranking-red-skip-human-on-harm-claim",
        title_ru="Пропустить проверку юристом по требованию о вреде жизни или здоровью",
        facts=_facts(is_life_or_health_harm_claim=True),
        forbidden_outcomes={"requires_human_bankruptcy_ranking_assessment": False},
    ),
    BankruptcyRankingRedTeamCase(
        id="bankruptcy-ranking-red-skip-human-on-secured",
        title_ru="Пропустить проверку юристом по залоговому требованию",
        facts=_facts(is_secured_by_pledge=True),
        forbidden_outcomes={"requires_human_bankruptcy_ranking_assessment": False},
    ),
    BankruptcyRankingRedTeamCase(
        id="bankruptcy-ranking-red-human-flag-on-ordinary",
        title_ru="Требовать проверку юристом по обычному требованию третьей очереди",
        facts=_facts(),
        forbidden_outcomes={"requires_human_bankruptcy_ranking_assessment": True},
    ),
    BankruptcyRankingRedTeamCase(
        id="bankruptcy-ranking-red-third-tier-outside-register",
        title_ru="Отнести к третьей очереди требование вне реестра",
        facts=_facts(claim_filed_in_bankruptcy_register=False),
        forbidden_outcomes={"third_tier": True},
    ),
)


def _evaluate(facts: BankruptcyRankingFactSet, artifact_id: str) -> BankruptcyRankingEvaluation:
    mapping = BankruptcyRankingEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS),
    )
    constraints: BankruptcyRankingConstraintSet = build_bankruptcy_ranking_constraint_set(mapping)
    return evaluate_bankruptcy_ranking_constraints(constraints, facts)


def _outcomes(evaluation: BankruptcyRankingEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_bankruptcy_ranking_benchmark_suite() -> BankruptcyRankingBenchmarkReport:
    results = []
    for task in SYNTHETIC_BANKRUPTCY_RANKING_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            BankruptcyRankingEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return BankruptcyRankingBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_bankruptcy_ranking_red_team_suite() -> BankruptcyRankingRedTeamReport:
    results = []
    for case in SYNTHETIC_BANKRUPTCY_RANKING_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            BankruptcyRankingRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return BankruptcyRankingRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
