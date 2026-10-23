"""Бенчмарк и red-team для модели зачёта и сальдирования в деле о банкротстве.

Случаи сальдо нагружены тремя ловушками, на которых суды ошибались в делах,
разобранных Верховным Судом. Первая — «название решает»: заказчик направил
«уведомление о зачёте», а по содержанию это сальдо (пункт 4 Обзора ВС РФ по
банкротству за 2023 год). Вторая — «судебные акты мешают»: взыскание встречных
требований судом сальдированию не препятствует (пункт 17 Обзора за 2022 год).
Третья — «неустойка порочит»: учёт неустойки в сальдо не делает его сделкой с
предпочтением, а против явной несоразмерности защищает статья 333 ГК РФ.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.bankruptcy_setoff import (
    BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS,
    BankruptcySetoffConstraintSet,
    BankruptcySetoffEvaluation,
    BankruptcySetoffEvidenceMappingResult,
    BankruptcySetoffFactSet,
    build_bankruptcy_setoff_constraint_set,
    evaluate_bankruptcy_setoff_constraints,
)


class BankruptcySetoffEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: BankruptcySetoffFactSet
    expected_outcomes: dict[str, bool]


class BankruptcySetoffEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankruptcySetoffBenchmarkReport(BaseModel):
    id: str = "bankruptcy-setoff-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[BankruptcySetoffEvaluationResult] = Field(default_factory=list)


class BankruptcySetoffRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: BankruptcySetoffFactSet
    forbidden_outcomes: dict[str, bool]


class BankruptcySetoffRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankruptcySetoffRedTeamReport(BaseModel):
    id: str = "bankruptcy-setoff-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[BankruptcySetoffRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> BankruptcySetoffFactSet:
    values = {field_name: False for field_name in BankruptcySetoffFactSet.model_fields}
    values.update(updates)
    return BankruptcySetoffFactSet(**values)


#: Зачёт в наблюдении, который нарушил бы очерёдность, — если бы был зачётом.
_PRIORITY_VIOLATING_SETOFF = dict(
    observation_introduced=True,
    setoff_of_mutual_homogeneous_claims_asserted=True,
    setoff_would_violate_priority_order=True,
)

#: Сальдо по одному договору: пункт 17 Обзора ВС РФ по банкротству за 2022 год.
_SALDO_ONE_CONTRACT = dict(
    counter_obligations_arise_from_one_contract=True,
    operation_determines_final_obligation_by_comparing_performances=True,
)


SYNTHETIC_BANKRUPTCY_SETOFF_BENCHMARKS = (
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-prohibited",
        title_ru="Зачёт, нарушающий очерёдность, в наблюдении — запрещён",
        facts=_facts(
            observation_introduced=True,
            setoff_of_mutual_homogeneous_claims_asserted=True,
            setoff_would_violate_priority_order=True,
        ),
        expected_outcomes={
            "setoff_prohibited": True,
            "setoff_permitted_as_priority_neutral": False,
            "requires_human_bankruptcy_setoff_assessment": True,
        },
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-priority-neutral",
        title_ru="Зачёт, не нарушающий очерёдность, — допустим",
        facts=_facts(
            observation_introduced=True,
            setoff_of_mutual_homogeneous_claims_asserted=True,
        ),
        expected_outcomes={
            "setoff_prohibited": False,
            "setoff_permitted_as_priority_neutral": True,
        },
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-netting-exception",
        title_ru="Нетто-обязательство по финансовым договорам — исключение из запрета",
        facts=_facts(
            observation_introduced=True,
            arises_from_financial_contract_netting_under_article_4_1=True,
        ),
        expected_outcomes={
            "setoff_prohibited": False,
            "netting_permitted_by_financial_contract_exception": True,
            "requires_human_bankruptcy_setoff_assessment": False,
        },
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-no-observation-no-prohibition",
        title_ru="Наблюдение не введено — запрет статьи 63 ещё не действует",
        facts=_facts(
            setoff_of_mutual_homogeneous_claims_asserted=True,
            setoff_would_violate_priority_order=True,
        ),
        expected_outcomes={"setoff_prohibited": False},
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-nothing-asserted",
        title_ru="Ни зачёт, ни нетто-обязательство не заявлены",
        facts=_facts(observation_introduced=True),
        expected_outcomes={
            "setoff_prohibited": False,
            "setoff_permitted_as_priority_neutral": False,
            "netting_permitted_by_financial_contract_exception": False,
            "requires_human_bankruptcy_setoff_assessment": False,
        },
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-saldo-one-contract",
        title_ru="Сальдо по одному договору вместо зачёта, нарушающего очерёдность",
        facts=_facts(**_PRIORITY_VIOLATING_SETOFF, **_SALDO_ONE_CONTRACT),
        expected_outcomes={
            "operation_is_saldo_not_setoff": True,
            "setoff_prohibited": False,
            "setoff_permitted_as_priority_neutral": False,
            "requires_human_bankruptcy_setoff_assessment": False,
        },
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-saldo-linked-contracts",
        title_ru="Сальдо по взаимосвязанным договорам — флаг юриста",
        facts=_facts(
            **_PRIORITY_VIOLATING_SETOFF,
            counter_obligations_arise_from_linked_contracts=True,
            operation_determines_final_obligation_by_comparing_performances=True,
        ),
        expected_outcomes={
            "operation_is_saldo_not_setoff": True,
            "setoff_prohibited": False,
            "requires_human_bankruptcy_setoff_assessment": True,
        },
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-one-contract-without-final-obligation",
        title_ru="Один договор, но завершающая обязанность не определяется — зачёт",
        facts=_facts(
            **_PRIORITY_VIOLATING_SETOFF, counter_obligations_arise_from_one_contract=True
        ),
        expected_outcomes={
            "operation_is_saldo_not_setoff": False,
            "setoff_prohibited": True,
            "requires_human_bankruptcy_setoff_assessment": True,
        },
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-saldo-before-observation",
        title_ru="Сальдо до введения наблюдения — не оспаривается как предпочтение",
        facts=_facts(**_SALDO_ONE_CONTRACT),
        expected_outcomes={
            "operation_is_saldo_not_setoff": True,
            "setoff_prohibited": False,
            "requires_human_bankruptcy_setoff_assessment": False,
        },
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-saldo-after-judgments",
        title_ru="Встречные требования взысканы судом — сальдо всё равно возможно",
        facts=_facts(**_SALDO_ONE_CONTRACT, counter_claims_already_awarded_by_court=True),
        expected_outcomes={
            "operation_is_saldo_not_setoff": True,
            "prior_judgments_do_not_bar_saldo": True,
        },
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-penalty-in-saldo",
        title_ru="Соразмерная неустойка в сальдо — сальдо, без флага",
        facts=_facts(
            **_PRIORITY_VIOLATING_SETOFF, **_SALDO_ONE_CONTRACT, penalty_counted_in_saldo=True
        ),
        expected_outcomes={
            "operation_is_saldo_not_setoff": True,
            "penalty_disproportion_remedied_by_article_333": False,
            "requires_human_bankruptcy_setoff_assessment": False,
        },
    ),
    BankruptcySetoffEvaluationTask(
        id="bankruptcy-setoff-bench-disproportionate-penalty-in-saldo",
        title_ru="Явно несоразмерная неустойка в сальдо — статья 333, флаг юриста",
        facts=_facts(
            **_SALDO_ONE_CONTRACT,
            penalty_counted_in_saldo=True,
            penalty_clearly_disproportionate_to_breach=True,
        ),
        expected_outcomes={
            "operation_is_saldo_not_setoff": True,
            "penalty_disproportion_remedied_by_article_333": True,
            "requires_human_bankruptcy_setoff_assessment": True,
        },
    ),
)


SYNTHETIC_BANKRUPTCY_SETOFF_RED_TEAM_CASES = (
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-permit-priority-violating",
        title_ru="Разрешить зачёт, нарушающий очерёдность",
        facts=_facts(
            observation_introduced=True,
            setoff_of_mutual_homogeneous_claims_asserted=True,
            setoff_would_violate_priority_order=True,
        ),
        forbidden_outcomes={"setoff_permitted_as_priority_neutral": True},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-prohibit-neutral",
        title_ru="Запретить зачёт, не нарушающий очерёдность",
        facts=_facts(
            observation_introduced=True,
            setoff_of_mutual_homogeneous_claims_asserted=True,
        ),
        forbidden_outcomes={"setoff_prohibited": True},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-prohibit-netting",
        title_ru="Запретить прекращение через нетто-обязательство по статье 4.1",
        facts=_facts(
            observation_introduced=True,
            arises_from_financial_contract_netting_under_article_4_1=True,
        ),
        forbidden_outcomes={"setoff_prohibited": True},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-prohibit-without-observation",
        title_ru="Запретить зачёт без введённого наблюдения",
        facts=_facts(
            setoff_of_mutual_homogeneous_claims_asserted=True,
            setoff_would_violate_priority_order=True,
        ),
        forbidden_outcomes={"setoff_prohibited": True},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-skip-human-on-prohibited",
        title_ru="Пропустить проверку юристом при запрещённом зачёте",
        facts=_facts(
            observation_introduced=True,
            setoff_of_mutual_homogeneous_claims_asserted=True,
            setoff_would_violate_priority_order=True,
        ),
        forbidden_outcomes={"requires_human_bankruptcy_setoff_assessment": False},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-human-flag-on-netting",
        title_ru="Требовать проверку юристом по исключению для нетто-обязательств",
        facts=_facts(
            observation_introduced=True,
            arises_from_financial_contract_netting_under_article_4_1=True,
        ),
        forbidden_outcomes={"requires_human_bankruptcy_setoff_assessment": True},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-prohibit-saldo-as-setoff",
        title_ru="Запретить сальдо по одному договору как зачёт, нарушающий очерёдность",
        facts=_facts(**_PRIORITY_VIOLATING_SETOFF, **_SALDO_ONE_CONTRACT),
        forbidden_outcomes={"setoff_prohibited": True},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-the-name-decides",
        title_ru="Счесть зачётом операцию, которую сторона назвала зачётом",
        facts=_facts(setoff_of_mutual_homogeneous_claims_asserted=True, **_SALDO_ONE_CONTRACT),
        forbidden_outcomes={"operation_is_saldo_not_setoff": False},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-one-contract-is-not-yet-saldo",
        title_ru="Признать сальдо по одному признаку единого договора",
        facts=_facts(
            **_PRIORITY_VIOLATING_SETOFF, counter_obligations_arise_from_one_contract=True
        ),
        forbidden_outcomes={"operation_is_saldo_not_setoff": True},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-judgments-bar-saldo",
        title_ru="Отказать в сальдо, потому что встречные требования взысканы судом",
        facts=_facts(**_SALDO_ONE_CONTRACT, counter_claims_already_awarded_by_court=True),
        forbidden_outcomes={"operation_is_saldo_not_setoff": False},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-penalty-voids-saldo",
        title_ru="Счесть сальдо с явно несоразмерной неустойкой запрещённым зачётом",
        facts=_facts(
            **_PRIORITY_VIOLATING_SETOFF,
            **_SALDO_ONE_CONTRACT,
            penalty_counted_in_saldo=True,
            penalty_clearly_disproportionate_to_breach=True,
        ),
        forbidden_outcomes={"setoff_prohibited": True, "operation_is_saldo_not_setoff": False},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-linked-contracts-without-flag",
        title_ru="Признать сальдо по взаимосвязанным договорам без проверки юристом",
        facts=_facts(
            counter_obligations_arise_from_linked_contracts=True,
            operation_determines_final_obligation_by_comparing_performances=True,
        ),
        forbidden_outcomes={"requires_human_bankruptcy_setoff_assessment": False},
    ),
    BankruptcySetoffRedTeamCase(
        id="bankruptcy-setoff-red-spurious-flag-on-one-contract-saldo",
        title_ru="Поднять флаг юриста на сальдо по одному договору",
        facts=_facts(**_PRIORITY_VIOLATING_SETOFF, **_SALDO_ONE_CONTRACT),
        forbidden_outcomes={"requires_human_bankruptcy_setoff_assessment": True},
    ),
)


def _evaluate(facts: BankruptcySetoffFactSet, artifact_id: str) -> BankruptcySetoffEvaluation:
    mapping = BankruptcySetoffEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS),
    )
    constraints: BankruptcySetoffConstraintSet = build_bankruptcy_setoff_constraint_set(mapping)
    return evaluate_bankruptcy_setoff_constraints(constraints, facts)


def _outcomes(evaluation: BankruptcySetoffEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_bankruptcy_setoff_benchmark_suite() -> BankruptcySetoffBenchmarkReport:
    results = []
    for task in SYNTHETIC_BANKRUPTCY_SETOFF_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            BankruptcySetoffEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return BankruptcySetoffBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_bankruptcy_setoff_red_team_suite() -> BankruptcySetoffRedTeamReport:
    results = []
    for case in SYNTHETIC_BANKRUPTCY_SETOFF_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = all(
            observed[name] != forbidden for name, forbidden in case.forbidden_outcomes.items()
        )
        results.append(
            BankruptcySetoffRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return BankruptcySetoffRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
