from pydantic import BaseModel, Field

from causa.institutional.contracts.state_supply import (
    StateSupplyConstraintSet,
    StateSupplyEvaluation,
    StateSupplyEvidenceMappingResult,
    StateSupplyFactSet,
    build_state_supply_constraint_set,
    evaluate_state_supply_constraints,
)


class StateSupplyEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: StateSupplyFactSet
    expected_outcomes: dict[str, bool]


class StateSupplyEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class StateSupplyBenchmarkReport(BaseModel):
    id: str = "state-supply-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[StateSupplyEvaluationResult] = Field(default_factory=list)


class StateSupplyRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: StateSupplyFactSet
    forbidden_outcomes: dict[str, bool]


class StateSupplyRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class StateSupplyRedTeamReport(BaseModel):
    id: str = "state-supply-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[StateSupplyRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> StateSupplyFactSet:
    values = {field_name: False for field_name in StateSupplyFactSet.model_fields}
    values.update(updates)
    return StateSupplyFactSet(**values)


SYNTHETIC_STATE_SUPPLY_BENCHMARKS = (
    StateSupplyEvaluationTask(
        id="statesupply-bench-compel",
        title_ru="Обязанный поставщик уклоняется от заключения контракта",
        facts=_facts(
            conclusion_mandatory_for_supplier=True,
            order_placed_by_procedure=True,
            supplier_evaded_conclusion=True,
        ),
        expected_outcomes={
            "supplier_conclusion_compellable": True,
            "requires_human_state_supply_assessment": True,
        },
    ),
    StateSupplyEvaluationTask(
        id="statesupply-bench-loss-exception",
        title_ru="Обязательность заключения при убыточности контракта",
        facts=_facts(
            conclusion_mandatory_for_supplier=True,
            order_placed_by_procedure=True,
            supplier_evaded_conclusion=True,
            contract_causes_supplier_loss=True,
        ),
        expected_outcomes={
            "supplier_conclusion_compellable": False,
            "requires_human_state_supply_assessment": True,
        },
    ),
    StateSupplyEvaluationTask(
        id="statesupply-bench-attachment",
        title_ru="Прикрепление покупателя к поставщику на основании контракта",
        facts=_facts(
            state_contract_concluded=True,
            attachment_notice_issued=True,
        ),
        expected_outcomes={
            "buyer_attached_to_supplier": True,
            "requires_human_state_supply_assessment": False,
        },
    ),
    StateSupplyEvaluationTask(
        id="statesupply-bench-buyer-refusal",
        title_ru="Покупатель отказался от товаров — перекрепление",
        facts=_facts(
            state_contract_concluded=True,
            attachment_notice_issued=True,
            buyer_refused_goods=True,
        ),
        expected_outcomes={
            "supplier_may_seek_reattachment": True,
            "requires_human_state_supply_assessment": True,
        },
    ),
    StateSupplyEvaluationTask(
        id="statesupply-bench-buyer-payment",
        title_ru="Покупатель оплатил товары по ценам контракта",
        facts=_facts(
            state_contract_concluded=True,
            goods_delivered_to_buyer=True,
            buyer_paid_at_contract_price=True,
        ),
        expected_outcomes={
            "buyer_pays_at_contract_price": True,
            "customer_guarantees_buyer_payment": True,
            "requires_human_state_supply_assessment": False,
        },
    ),
    StateSupplyEvaluationTask(
        id="statesupply-bench-customer-guarantor",
        title_ru="Товары поставлены покупателю — заказчик как поручитель",
        facts=_facts(
            state_contract_concluded=True,
            goods_delivered_to_buyer=True,
        ),
        expected_outcomes={
            "customer_guarantees_buyer_payment": True,
            "buyer_pays_at_contract_price": False,
        },
    ),
    StateSupplyEvaluationTask(
        id="statesupply-bench-customer-refusal",
        title_ru="Заказчик отказался от товаров, поставщик понёс убытки",
        facts=_facts(
            state_contract_concluded=True,
            state_customer_refused_goods=True,
            supplier_incurred_losses=True,
        ),
        expected_outcomes={
            "customer_refusal_compensates_supplier": True,
            "supplier_losses_compensable": True,
            "requires_human_state_supply_assessment": True,
        },
    ),
    StateSupplyEvaluationTask(
        id="statesupply-bench-supplier-losses",
        title_ru="Убытки поставщика в связи с выполнением контракта",
        facts=_facts(
            state_contract_concluded=True,
            supplier_incurred_losses=True,
        ),
        expected_outcomes={
            "supplier_losses_compensable": True,
            "requires_human_state_supply_assessment": True,
        },
    ),
    StateSupplyEvaluationTask(
        id="statesupply-bench-not-mandatory",
        title_ru="Поставщик не обязан заключать контракт и уклоняется",
        facts=_facts(
            order_placed_by_procedure=True,
            supplier_evaded_conclusion=True,
        ),
        expected_outcomes={"supplier_conclusion_compellable": False},
    ),
    StateSupplyEvaluationTask(
        id="statesupply-bench-empty",
        title_ru="Государственный контракт отсутствует",
        facts=_facts(),
        expected_outcomes={
            "buyer_attached_to_supplier": False,
            "supplier_conclusion_compellable": False,
            "requires_human_state_supply_assessment": False,
        },
    ),
)


SYNTHETIC_STATE_SUPPLY_RED_TEAM_CASES = (
    StateSupplyRedTeamCase(
        id="statesupply-red-compel-without-mandatory",
        title_ru="Понуждать поставщика к заключению без обязательности",
        facts=_facts(
            order_placed_by_procedure=True,
            supplier_evaded_conclusion=True,
        ),
        forbidden_outcomes={"supplier_conclusion_compellable": True},
    ),
    StateSupplyRedTeamCase(
        id="statesupply-red-compel-when-loss",
        title_ru="Понуждать к заключению убыточного контракта",
        facts=_facts(
            conclusion_mandatory_for_supplier=True,
            order_placed_by_procedure=True,
            supplier_evaded_conclusion=True,
            contract_causes_supplier_loss=True,
        ),
        forbidden_outcomes={"supplier_conclusion_compellable": True},
    ),
    StateSupplyRedTeamCase(
        id="statesupply-red-attach-without-contract",
        title_ru="Прикреплять покупателя без государственного контракта",
        facts=_facts(attachment_notice_issued=True),
        forbidden_outcomes={"buyer_attached_to_supplier": True},
    ),
    StateSupplyRedTeamCase(
        id="statesupply-red-reattach-without-refusal",
        title_ru="Требовать перекрепления без отказа покупателя",
        facts=_facts(
            state_contract_concluded=True,
            attachment_notice_issued=True,
        ),
        forbidden_outcomes={"supplier_may_seek_reattachment": True},
    ),
    StateSupplyRedTeamCase(
        id="statesupply-red-buyer-pays-without-delivery",
        title_ru="Считать оплату по ценам контракта без поставки покупателю",
        facts=_facts(
            state_contract_concluded=True,
            buyer_paid_at_contract_price=True,
        ),
        forbidden_outcomes={"buyer_pays_at_contract_price": True},
    ),
    StateSupplyRedTeamCase(
        id="statesupply-red-guarantor-without-delivery",
        title_ru="Признавать заказчика поручителем без поставки покупателю",
        facts=_facts(state_contract_concluded=True),
        forbidden_outcomes={"customer_guarantees_buyer_payment": True},
    ),
    StateSupplyRedTeamCase(
        id="statesupply-red-compensate-without-losses",
        title_ru="Возмещать при отказе заказчика без причинённых убытков",
        facts=_facts(
            state_contract_concluded=True,
            state_customer_refused_goods=True,
        ),
        forbidden_outcomes={"customer_refusal_compensates_supplier": True},
    ),
    StateSupplyRedTeamCase(
        id="statesupply-red-losses-without-contract",
        title_ru="Возмещать убытки поставщику без государственного контракта",
        facts=_facts(supplier_incurred_losses=True),
        forbidden_outcomes={"supplier_losses_compensable": True},
    ),
    StateSupplyRedTeamCase(
        id="statesupply-red-skip-human-on-customer-refusal",
        title_ru="Пропустить экспертизу при отказе заказчика от товаров",
        facts=_facts(
            state_contract_concluded=True,
            state_customer_refused_goods=True,
            supplier_incurred_losses=True,
        ),
        forbidden_outcomes={"requires_human_state_supply_assessment": False},
    ),
    StateSupplyRedTeamCase(
        id="statesupply-red-skip-human-on-buyer-refusal",
        title_ru="Пропустить экспертизу при отказе покупателя от товаров",
        facts=_facts(
            state_contract_concluded=True,
            attachment_notice_issued=True,
            buyer_refused_goods=True,
        ),
        forbidden_outcomes={"requires_human_state_supply_assessment": False},
    ),
)


def _evaluate(facts: StateSupplyFactSet, artifact_id: str) -> StateSupplyEvaluation:
    mapping = StateSupplyEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-state-supply-law"],
    )
    constraints: StateSupplyConstraintSet = build_state_supply_constraint_set(mapping)
    return evaluate_state_supply_constraints(constraints, facts)


def _outcomes(evaluation: StateSupplyEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_state_supply_benchmark_suite() -> StateSupplyBenchmarkReport:
    results = []
    for task in SYNTHETIC_STATE_SUPPLY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            StateSupplyEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return StateSupplyBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_state_supply_red_team_suite() -> StateSupplyRedTeamReport:
    results = []
    for case in SYNTHETIC_STATE_SUPPLY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            StateSupplyRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return StateSupplyRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
