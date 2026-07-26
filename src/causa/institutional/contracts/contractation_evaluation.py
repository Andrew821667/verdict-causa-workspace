from pydantic import BaseModel, Field

from causa.institutional.contracts.contractation import (
    ContractationConstraintSet,
    ContractationEvaluation,
    ContractationEvidenceMappingResult,
    ContractationFactSet,
    build_contractation_constraint_set,
    evaluate_contractation_constraints,
)


class ContractationEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ContractationFactSet
    expected_outcomes: dict[str, bool]


class ContractationEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ContractationBenchmarkReport(BaseModel):
    id: str = "contractation-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ContractationEvaluationResult] = Field(default_factory=list)


class ContractationRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ContractationFactSet
    forbidden_outcomes: dict[str, bool]


class ContractationRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ContractationRedTeamReport(BaseModel):
    id: str = "contractation-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ContractationRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ContractationFactSet:
    values = {field_name: False for field_name in ContractationFactSet.model_fields}
    values.update(updates)
    return ContractationFactSet(**values)


SYNTHETIC_CONTRACTATION_BENCHMARKS = (
    ContractationEvaluationTask(
        id="contractation-bench-qualified",
        title_ru="Договор контрактации собственной продукции производителя",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
        ),
        expected_outcomes={
            "contractation_qualified": True,
            "requires_human_contractation_assessment": False,
        },
    ),
    ContractationEvaluationTask(
        id="contractation-bench-not-own",
        title_ru="Продукция не выращена (не произведена) самим производителем",
        facts=_facts(agricultural_producer_contract=True),
        expected_outcomes={"contractation_qualified": False},
    ),
    ContractationEvaluationTask(
        id="contractation-bench-procurer-accept",
        title_ru="Заготовитель принял продукцию по месту нахождения производителя",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            procurer_took_delivery_at_producer_location=True,
        ),
        expected_outcomes={
            "procurer_acceptance_duty_met": True,
            "requires_human_contractation_assessment": False,
        },
    ),
    ContractationEvaluationTask(
        id="contractation-bench-refusal",
        title_ru="Заготовитель отказался от соответствующей продукции",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            goods_conform_and_timely=True,
            procurer_refused_conforming_goods=True,
        ),
        expected_outcomes={
            "procurer_refusal_unlawful": True,
            "requires_human_contractation_assessment": True,
        },
    ),
    ContractationEvaluationTask(
        id="contractation-bench-refusal-nonconforming",
        title_ru="Отказ от несоответствующей или несвоевременной продукции",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            procurer_refused_conforming_goods=True,
        ),
        expected_outcomes={
            "procurer_refusal_unlawful": False,
            "requires_human_contractation_assessment": True,
        },
    ),
    ContractationEvaluationTask(
        id="contractation-bench-waste-return",
        title_ru="Возврат отходов переработки согласован и исполнен",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            processing_waste_return_agreed=True,
            procurer_returned_waste=True,
        ),
        expected_outcomes={
            "waste_return_obligation": True,
            "waste_return_performed": True,
            "requires_human_contractation_assessment": False,
        },
    ),
    ContractationEvaluationTask(
        id="contractation-bench-waste-not-returned",
        title_ru="Возврат отходов согласован, но не исполнен",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            processing_waste_return_agreed=True,
        ),
        expected_outcomes={
            "waste_return_obligation": True,
            "waste_return_performed": False,
            "requires_human_contractation_assessment": True,
        },
    ),
    ContractationEvaluationTask(
        id="contractation-bench-delivery",
        title_ru="Производитель передал продукцию в количестве и ассортименте",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            producer_delivered_quantity_and_assortment=True,
        ),
        expected_outcomes={
            "producer_delivery_duty_met": True,
            "requires_human_contractation_assessment": False,
        },
    ),
    ContractationEvaluationTask(
        id="contractation-bench-liable",
        title_ru="Производитель нарушил обязательство и виновен",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            producer_breached=True,
            producer_at_fault=True,
        ),
        expected_outcomes={
            "producer_liable_only_if_at_fault": True,
            "requires_human_contractation_assessment": True,
        },
    ),
    ContractationEvaluationTask(
        id="contractation-bench-not-liable",
        title_ru="Производитель нарушил обязательство без вины",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            producer_breached=True,
        ),
        expected_outcomes={
            "producer_liable_only_if_at_fault": False,
            "requires_human_contractation_assessment": True,
        },
    ),
)


SYNTHETIC_CONTRACTATION_RED_TEAM_CASES = (
    ContractationRedTeamCase(
        id="contractation-red-qualify-without-contract",
        title_ru="Квалифицировать контрактацию без договора с производителем",
        facts=_facts(goods_are_own_grown_produce=True),
        forbidden_outcomes={"contractation_qualified": True},
    ),
    ContractationRedTeamCase(
        id="contractation-red-qualify-without-own-produce",
        title_ru="Квалифицировать контрактацию без собственной продукции",
        facts=_facts(agricultural_producer_contract=True),
        forbidden_outcomes={"contractation_qualified": True},
    ),
    ContractationRedTeamCase(
        id="contractation-red-refusal-lawful-when-conforming",
        title_ru="Считать отказ правомерным при соответствующей продукции",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            goods_conform_and_timely=True,
            procurer_refused_conforming_goods=True,
        ),
        forbidden_outcomes={"procurer_refusal_unlawful": False},
    ),
    ContractationRedTeamCase(
        id="contractation-red-refusal-unlawful-when-nonconforming",
        title_ru="Считать отказ неправомерным при несоответствующей продукции",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            procurer_refused_conforming_goods=True,
        ),
        forbidden_outcomes={"procurer_refusal_unlawful": True},
    ),
    ContractationRedTeamCase(
        id="contractation-red-waste-performed-without-agreement",
        title_ru="Считать возврат отходов исполненным без согласования",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            procurer_returned_waste=True,
        ),
        forbidden_outcomes={"waste_return_performed": True},
    ),
    ContractationRedTeamCase(
        id="contractation-red-liable-without-fault",
        title_ru="Возлагать ответственность на производителя без вины",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            producer_breached=True,
        ),
        forbidden_outcomes={"producer_liable_only_if_at_fault": True},
    ),
    ContractationRedTeamCase(
        id="contractation-red-delivery-met-without-delivery",
        title_ru="Считать обязанность производителя исполненной без передачи",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
        ),
        forbidden_outcomes={"producer_delivery_duty_met": True},
    ),
    ContractationRedTeamCase(
        id="contractation-red-acceptance-without-delivery",
        title_ru="Считать обязанность приёмки исполненной без принятия продукции",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
        ),
        forbidden_outcomes={"procurer_acceptance_duty_met": True},
    ),
    ContractationRedTeamCase(
        id="contractation-red-skip-human-on-breach",
        title_ru="Пропустить экспертизу при нарушении производителя",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            producer_breached=True,
        ),
        forbidden_outcomes={"requires_human_contractation_assessment": False},
    ),
    ContractationRedTeamCase(
        id="contractation-red-skip-human-on-refusal",
        title_ru="Пропустить экспертизу при отказе заготовителя",
        facts=_facts(
            agricultural_producer_contract=True,
            goods_are_own_grown_produce=True,
            procurer_refused_conforming_goods=True,
        ),
        forbidden_outcomes={"requires_human_contractation_assessment": False},
    ),
)


def _evaluate(facts: ContractationFactSet, artifact_id: str) -> ContractationEvaluation:
    mapping = ContractationEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-contractation-law"],
    )
    constraints: ContractationConstraintSet = build_contractation_constraint_set(mapping)
    return evaluate_contractation_constraints(constraints, facts)


def _outcomes(evaluation: ContractationEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_contractation_benchmark_suite() -> ContractationBenchmarkReport:
    results = []
    for task in SYNTHETIC_CONTRACTATION_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ContractationEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ContractationBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_contractation_red_team_suite() -> ContractationRedTeamReport:
    results = []
    for case in SYNTHETIC_CONTRACTATION_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ContractationRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ContractationRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
