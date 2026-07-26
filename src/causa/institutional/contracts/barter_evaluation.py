from pydantic import BaseModel, Field

from causa.institutional.contracts.barter import (
    BarterConstraintSet,
    BarterEvaluation,
    BarterEvidenceMappingResult,
    BarterFactSet,
    build_barter_constraint_set,
    evaluate_barter_constraints,
)


class BarterEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: BarterFactSet
    expected_outcomes: dict[str, bool]


class BarterEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BarterBenchmarkReport(BaseModel):
    id: str = "barter-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[BarterEvaluationResult] = Field(default_factory=list)


class BarterRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: BarterFactSet
    forbidden_outcomes: dict[str, bool]


class BarterRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BarterRedTeamReport(BaseModel):
    id: str = "barter-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[BarterRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> BarterFactSet:
    values = {field_name: False for field_name in BarterFactSet.model_fields}
    values.update(updates)
    return BarterFactSet(**values)


SYNTHETIC_BARTER_BENCHMARKS = (
    BarterEvaluationTask(
        id="barter-bench-qualified",
        title_ru="Обмен одного товара на другой в собственность",
        facts=_facts(mutual_goods_for_goods_exchange=True),
        expected_outcomes={
            "barter_qualified": True,
            "sale_rules_apply": True,
            "requires_human_barter_assessment": False,
        },
    ),
    BarterEvaluationTask(
        id="barter-bench-not-qualified",
        title_ru="Отношения без встречной передачи товара за товар",
        facts=_facts(goods_treated_as_equal_value=True),
        expected_outcomes={"barter_qualified": False},
    ),
    BarterEvaluationTask(
        id="barter-bench-contrary-essence",
        title_ru="Применение правил о купле-продаже противоречит существу мены",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            contrary_to_barter_essence=True,
        ),
        expected_outcomes={
            "sale_rules_apply": False,
            "requires_human_barter_assessment": True,
        },
    ),
    BarterEvaluationTask(
        id="barter-bench-equal-value",
        title_ru="Товары признаются равноценными",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            goods_treated_as_equal_value=True,
        ),
        expected_outcomes={
            "equal_value_presumption_applies": True,
            "requires_human_barter_assessment": False,
        },
    ),
    BarterEvaluationTask(
        id="barter-bench-price-difference-unpaid",
        title_ru="Неравноценные товары, разница в цене не оплачена",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            goods_unequal_value=True,
        ),
        expected_outcomes={
            "price_difference_obligation": True,
            "requires_human_barter_assessment": True,
        },
    ),
    BarterEvaluationTask(
        id="barter-bench-price-difference-paid",
        title_ru="Неравноценные товары, разница в цене оплачена",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            goods_unequal_value=True,
            lower_price_party_paid_difference=True,
        ),
        expected_outcomes={
            "price_difference_obligation": False,
            "requires_human_barter_assessment": False,
        },
    ),
    BarterEvaluationTask(
        id="barter-bench-counter-performance-suspend",
        title_ru="Сроки передачи различаются, первая сторона не передала товар",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            transfer_deadlines_differ=True,
        ),
        expected_outcomes={
            "counter_performance_rules_apply": True,
            "second_party_may_suspend_transfer": True,
            "requires_human_barter_assessment": True,
        },
    ),
    BarterEvaluationTask(
        id="barter-bench-counter-performance-performed",
        title_ru="Сроки различаются, первая сторона исполнила передачу",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            transfer_deadlines_differ=True,
            first_party_performed_its_transfer=True,
        ),
        expected_outcomes={
            "counter_performance_rules_apply": True,
            "second_party_may_suspend_transfer": False,
            "requires_human_barter_assessment": False,
        },
    ),
    BarterEvaluationTask(
        id="barter-bench-ownership-simultaneous",
        title_ru="Обе стороны передали товары — одновременный переход права",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            both_parties_transferred_goods=True,
        ),
        expected_outcomes={
            "ownership_transfers_simultaneously": True,
            "requires_human_barter_assessment": False,
        },
    ),
    BarterEvaluationTask(
        id="barter-bench-eviction-remedy",
        title_ru="Изъятие товара третьим лицом по основанию до исполнения",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            received_good_evicted_by_third_party=True,
            eviction_ground_arose_before_performance=True,
        ),
        expected_outcomes={
            "eviction_remedy_available": True,
            "requires_human_barter_assessment": True,
        },
    ),
)


SYNTHETIC_BARTER_RED_TEAM_CASES = (
    BarterRedTeamCase(
        id="barter-red-qualify-without-exchange",
        title_ru="Квалифицировать мену без встречной передачи товара за товар",
        facts=_facts(goods_treated_as_equal_value=True),
        forbidden_outcomes={"barter_qualified": True},
    ),
    BarterRedTeamCase(
        id="barter-red-sale-rules-despite-contrary-essence",
        title_ru="Применять правила о купле-продаже вопреки существу мены",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            contrary_to_barter_essence=True,
        ),
        forbidden_outcomes={"sale_rules_apply": True},
    ),
    BarterRedTeamCase(
        id="barter-red-equal-value-without-qualification",
        title_ru="Применять презумпцию равноценности вне договора мены",
        facts=_facts(goods_treated_as_equal_value=True),
        forbidden_outcomes={"equal_value_presumption_applies": True},
    ),
    BarterRedTeamCase(
        id="barter-red-price-difference-despite-payment",
        title_ru="Сохранять обязанность доплаты после оплаты разницы в цене",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            goods_unequal_value=True,
            lower_price_party_paid_difference=True,
        ),
        forbidden_outcomes={"price_difference_obligation": True},
    ),
    BarterRedTeamCase(
        id="barter-red-skip-price-difference-when-unpaid",
        title_ru="Скрыть обязанность доплаты при неоплаченной разнице в цене",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            goods_unequal_value=True,
        ),
        forbidden_outcomes={"price_difference_obligation": False},
    ),
    BarterRedTeamCase(
        id="barter-red-suspend-despite-first-performed",
        title_ru="Признавать право приостановить передачу при исполнении первой стороной",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            transfer_deadlines_differ=True,
            first_party_performed_its_transfer=True,
        ),
        forbidden_outcomes={"second_party_may_suspend_transfer": True},
    ),
    BarterRedTeamCase(
        id="barter-red-ownership-without-both-transfers",
        title_ru="Считать переход права состоявшимся без передачи обеими сторонами",
        facts=_facts(mutual_goods_for_goods_exchange=True),
        forbidden_outcomes={"ownership_transfers_simultaneously": True},
    ),
    BarterRedTeamCase(
        id="barter-red-eviction-remedy-without-eviction",
        title_ru="Признать средство защиты при изъятии без самого изъятия",
        facts=_facts(mutual_goods_for_goods_exchange=True),
        forbidden_outcomes={"eviction_remedy_available": True},
    ),
    BarterRedTeamCase(
        id="barter-red-eviction-remedy-when-ground-after",
        title_ru="Признать средство защиты при основании изъятия после исполнения",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            received_good_evicted_by_third_party=True,
        ),
        forbidden_outcomes={"eviction_remedy_available": True},
    ),
    BarterRedTeamCase(
        id="barter-red-skip-human-on-eviction",
        title_ru="Пропустить экспертизу при изъятии товара третьим лицом",
        facts=_facts(
            mutual_goods_for_goods_exchange=True,
            received_good_evicted_by_third_party=True,
            eviction_ground_arose_before_performance=True,
        ),
        forbidden_outcomes={"requires_human_barter_assessment": False},
    ),
)


def _evaluate(facts: BarterFactSet, artifact_id: str) -> BarterEvaluation:
    mapping = BarterEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-barter-law"],
    )
    constraints: BarterConstraintSet = build_barter_constraint_set(mapping)
    return evaluate_barter_constraints(constraints, facts)


def _outcomes(evaluation: BarterEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_barter_benchmark_suite() -> BarterBenchmarkReport:
    results = []
    for task in SYNTHETIC_BARTER_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            BarterEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return BarterBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_barter_red_team_suite() -> BarterRedTeamReport:
    results = []
    for case in SYNTHETIC_BARTER_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            BarterRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return BarterRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
