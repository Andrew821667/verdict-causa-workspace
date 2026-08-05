from pydantic import BaseModel, Field

from causa.institutional.contracts.games import (
    GamesConstraintSet,
    GamesEvaluation,
    GamesEvidenceMappingResult,
    GamesFactSet,
    build_games_constraint_set,
    evaluate_games_constraints,
)


class GamesEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: GamesFactSet
    expected_outcomes: dict[str, bool]


class GamesEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GamesBenchmarkReport(BaseModel):
    id: str = "games-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[GamesEvaluationResult] = Field(default_factory=list)


class GamesRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: GamesFactSet
    forbidden_outcomes: dict[str, bool]


class GamesRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GamesRedTeamReport(BaseModel):
    id: str = "games-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[GamesRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> GamesFactSet:
    values = {field_name: False for field_name in GamesFactSet.model_fields}
    values.update(updates)
    return GamesFactSet(**values)


SYNTHETIC_GAMES_BENCHMARKS = (
    GamesEvaluationTask(
        id="games-bench-not-qualified",
        title_ru="Отношения из игр и пари не установлены",
        facts=_facts(organizer_status_or_licence_breached=True),
        expected_outcomes={"games_qualified": False},
    ),
    GamesEvaluationTask(
        id="games-bench-qualified-clean",
        title_ru="Проведение игр без нарушений",
        facts=_facts(games_or_betting_relation_established=True),
        expected_outcomes={
            "games_qualified": True,
            "requires_human_games_assessment": False,
        },
    ),
    GamesEvaluationTask(
        id="games-bench-judicial-protection",
        title_ru="Нарушено правило об отказе в судебной защите требований из игр и пари",
        facts=_facts(
            games_or_betting_relation_established=True,
            judicial_protection_exclusion_breached=True,
        ),
        expected_outcomes={
            "judicial_protection_duty_breached": True,
            "requires_human_games_assessment": True,
        },
    ),
    GamesEvaluationTask(
        id="games-bench-coercion-exception",
        title_ru="Не учтено участие в игре под влиянием обмана или угрозы",
        facts=_facts(
            games_or_betting_relation_established=True,
            coercion_exception_disregarded=True,
        ),
        expected_outcomes={
            "coercion_exception_duty_breached": True,
            "requires_human_games_assessment": True,
        },
    ),
    GamesEvaluationTask(
        id="games-bench-derivative-transactions",
        title_ru="Нарушены условия судебной защиты требований из расчётных сделок",
        facts=_facts(
            games_or_betting_relation_established=True,
            derivative_transactions_protection_breached=True,
        ),
        expected_outcomes={
            "derivative_protection_duty_breached": True,
            "requires_human_games_assessment": True,
        },
    ),
    GamesEvaluationTask(
        id="games-bench-organizer-status",
        title_ru="Организатор игр не отвечает требованиям закона и не имеет разрешения",
        facts=_facts(
            games_or_betting_relation_established=True,
            organizer_status_or_licence_breached=True,
        ),
        expected_outcomes={
            "organizer_status_duty_breached": True,
            "requires_human_games_assessment": True,
        },
    ),
    GamesEvaluationTask(
        id="games-bench-contract-form",
        title_ru="Договор с участником игр не оформлен билетом или квитанцией",
        facts=_facts(
            games_or_betting_relation_established=True,
            game_contract_form_breached=True,
        ),
        expected_outcomes={
            "game_contract_form_duty_breached": True,
            "requires_human_games_assessment": True,
        },
    ),
    GamesEvaluationTask(
        id="games-bench-participation-rules",
        title_ru="Нарушены правила организации и проведения игр",
        facts=_facts(
            games_or_betting_relation_established=True,
            game_participation_rules_breached=True,
        ),
        expected_outcomes={
            "participation_rules_duty_breached": True,
            "requires_human_games_assessment": True,
        },
    ),
    GamesEvaluationTask(
        id="games-bench-prize-terms",
        title_ru="Условия о сроке игр и порядке определения выигрыша не объявлены",
        facts=_facts(
            games_or_betting_relation_established=True,
            prize_terms_announcement_breached=True,
        ),
        expected_outcomes={
            "prize_terms_duty_breached": True,
            "requires_human_games_assessment": True,
        },
    ),
    GamesEvaluationTask(
        id="games-bench-prize-payment",
        title_ru="Выигрыш не выплачен в срок, право на возмещение убытков не применено",
        facts=_facts(
            games_or_betting_relation_established=True,
            prize_payment_period_breached=True,
            payment_refusal_damages_not_applied=True,
        ),
        expected_outcomes={
            "prize_payment_duty_breached": True,
            "payment_refusal_damages_breached": True,
            "requires_human_games_assessment": True,
        },
    ),
)


SYNTHETIC_GAMES_RED_TEAM_CASES = (
    GamesRedTeamCase(
        id="games-red-qualify-without-relation",
        title_ru="Применить правила об играх и пари без соответствующих отношений",
        facts=_facts(organizer_status_or_licence_breached=True),
        forbidden_outcomes={"games_qualified": True},
    ),
    GamesRedTeamCase(
        id="games-red-ignore-judicial-protection",
        title_ru="Взыскать долг из пари вопреки отказу в судебной защите",
        facts=_facts(
            games_or_betting_relation_established=True,
            judicial_protection_exclusion_breached=True,
        ),
        forbidden_outcomes={"judicial_protection_duty_breached": False},
    ),
    GamesRedTeamCase(
        id="games-red-ignore-coercion-exception",
        title_ru="Отказать в защите лицу, участвовавшему в игре под влиянием обмана",
        facts=_facts(
            games_or_betting_relation_established=True,
            coercion_exception_disregarded=True,
        ),
        forbidden_outcomes={"coercion_exception_duty_breached": False},
    ),
    GamesRedTeamCase(
        id="games-red-ignore-derivative-protection",
        title_ru="Игнорировать условия судебной защиты требований из расчётных сделок",
        facts=_facts(
            games_or_betting_relation_established=True,
            derivative_transactions_protection_breached=True,
        ),
        forbidden_outcomes={"derivative_protection_duty_breached": False},
    ),
    GamesRedTeamCase(
        id="games-red-ignore-organizer-status",
        title_ru="Признать надлежащим организатора игр без разрешения (лицензии)",
        facts=_facts(
            games_or_betting_relation_established=True,
            organizer_status_or_licence_breached=True,
        ),
        forbidden_outcomes={"organizer_status_duty_breached": False},
    ),
    GamesRedTeamCase(
        id="games-red-ignore-contract-form",
        title_ru="Игнорировать отсутствие лотерейного билета или квитанции",
        facts=_facts(
            games_or_betting_relation_established=True,
            game_contract_form_breached=True,
        ),
        forbidden_outcomes={"game_contract_form_duty_breached": False},
    ),
    GamesRedTeamCase(
        id="games-red-ignore-participation-rules",
        title_ru="Игнорировать нарушение правил организации и проведения игр",
        facts=_facts(
            games_or_betting_relation_established=True,
            game_participation_rules_breached=True,
        ),
        forbidden_outcomes={"participation_rules_duty_breached": False},
    ),
    GamesRedTeamCase(
        id="games-red-ignore-prize-terms",
        title_ru="Признать игры проведёнными без объявления порядка определения выигрыша",
        facts=_facts(
            games_or_betting_relation_established=True,
            prize_terms_announcement_breached=True,
        ),
        forbidden_outcomes={"prize_terms_duty_breached": False},
    ),
    GamesRedTeamCase(
        id="games-red-damages-without-payment-breach",
        title_ru="Признать право на возмещение убытков без нарушения срока выплаты выигрыша",
        facts=_facts(games_or_betting_relation_established=True),
        forbidden_outcomes={"payment_refusal_damages_breached": True},
    ),
    GamesRedTeamCase(
        id="games-red-skip-human-on-prize-payment",
        title_ru="Пропустить экспертизу при невыплате выигрыша в установленный срок",
        facts=_facts(
            games_or_betting_relation_established=True,
            prize_payment_period_breached=True,
        ),
        forbidden_outcomes={"requires_human_games_assessment": False},
    ),
)


def _evaluate(facts: GamesFactSet, artifact_id: str) -> GamesEvaluation:
    mapping = GamesEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-games-law"],
    )
    constraints: GamesConstraintSet = build_games_constraint_set(mapping)
    return evaluate_games_constraints(constraints, facts)


def _outcomes(evaluation: GamesEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_games_benchmark_suite() -> GamesBenchmarkReport:
    results = []
    for task in SYNTHETIC_GAMES_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            GamesEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return GamesBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_games_red_team_suite() -> GamesRedTeamReport:
    results = []
    for case in SYNTHETIC_GAMES_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            GamesRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return GamesRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
