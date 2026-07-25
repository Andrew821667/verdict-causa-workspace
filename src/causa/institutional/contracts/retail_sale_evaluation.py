from pydantic import BaseModel, Field

from causa.institutional.contracts.retail_sale import (
    RetailSaleConstraintSet,
    RetailSaleEvaluation,
    RetailSaleEvidenceMappingResult,
    RetailSaleFactSet,
    build_retail_sale_constraint_set,
    evaluate_retail_sale_constraints,
)


class RetailSaleEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: RetailSaleFactSet
    expected_outcomes: dict[str, bool]


class RetailSaleEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class RetailSaleBenchmarkReport(BaseModel):
    id: str = "retail-sale-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[RetailSaleEvaluationResult] = Field(default_factory=list)


class RetailSaleRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: RetailSaleFactSet
    forbidden_outcomes: dict[str, bool]


class RetailSaleRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class RetailSaleRedTeamReport(BaseModel):
    id: str = "retail-sale-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[RetailSaleRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> RetailSaleFactSet:
    values = {field_name: False for field_name in RetailSaleFactSet.model_fields}
    values.update(updates)
    return RetailSaleFactSet(**values)


SYNTHETIC_RETAIL_SALE_BENCHMARKS = (
    RetailSaleEvaluationTask(
        id="retail-bench-public",
        title_ru="Розничная продажа с чеком и предоставленной информацией",
        facts=_facts(
            retail_consumer_sale=True,
            receipt_or_confirmation_issued=True,
            required_information_provided=True,
        ),
        expected_outcomes={
            "retail_contract_is_public": True,
            "form_confirmed_by_receipt": True,
            "information_duty_breached": False,
            "requires_human_retail_sale_assessment": False,
        },
    ),
    RetailSaleEvaluationTask(
        id="retail-bench-no-info",
        title_ru="Розничная продажа без предоставления информации о товаре",
        facts=_facts(retail_consumer_sale=True),
        expected_outcomes={
            "information_duty_breached": True,
            "requires_human_retail_sale_assessment": True,
        },
    ),
    RetailSaleEvaluationTask(
        id="retail-bench-defective-remedy",
        title_ru="Товар ненадлежащего качества, заявлено требование покупателя",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            goods_defective=True,
            buyer_quality_remedy_demanded=True,
        ),
        expected_outcomes={
            "quality_remedy_available": True,
            "requires_human_retail_sale_assessment": True,
        },
    ),
    RetailSaleEvaluationTask(
        id="retail-bench-defective-no-demand",
        title_ru="Недостаток товара без заявленного требования",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            goods_defective=True,
        ),
        expected_outcomes={
            "quality_remedy_available": False,
            "requires_human_retail_sale_assessment": False,
        },
    ),
    RetailSaleEvaluationTask(
        id="retail-bench-exchange",
        title_ru="Обмен товара надлежащего качества при наличии аналога",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            quality_exchange_demanded_in_term=True,
            goods_unused_and_documented=True,
            similar_goods_available=True,
        ),
        expected_outcomes={
            "quality_exchange_available": True,
            "exchange_refund_available": False,
            "requires_human_retail_sale_assessment": True,
        },
    ),
    RetailSaleEvaluationTask(
        id="retail-bench-exchange-refund",
        title_ru="Отсутствие аналога — возврат уплаченной суммы",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            quality_exchange_demanded_in_term=True,
            goods_unused_and_documented=True,
        ),
        expected_outcomes={
            "quality_exchange_available": False,
            "exchange_refund_available": True,
            "requires_human_retail_sale_assessment": True,
        },
    ),
    RetailSaleEvaluationTask(
        id="retail-bench-exchange-used",
        title_ru="Обмен невозможен: товар был в употреблении",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            quality_exchange_demanded_in_term=True,
            similar_goods_available=True,
        ),
        expected_outcomes={
            "quality_exchange_available": False,
            "exchange_refund_available": False,
        },
    ),
    RetailSaleEvaluationTask(
        id="retail-bench-price-difference",
        title_ru="Замена дефектного товара при возросшей цене",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            goods_defective=True,
            buyer_quality_remedy_demanded=True,
            price_increased_before_replacement=True,
        ),
        expected_outcomes={
            "price_difference_compensable": True,
            "quality_remedy_available": True,
            "requires_human_retail_sale_assessment": True,
        },
    ),
    RetailSaleEvaluationTask(
        id="retail-bench-not-retail",
        title_ru="Отношения не являются розничной куплей-продажей",
        facts=_facts(required_information_provided=True),
        expected_outcomes={
            "retail_contract_is_public": False,
            "information_duty_breached": False,
            "requires_human_retail_sale_assessment": False,
        },
    ),
    RetailSaleEvaluationTask(
        id="retail-bench-public-offer",
        title_ru="Публичная оферта: розница, чек и информация предоставлены",
        facts=_facts(
            retail_consumer_sale=True,
            public_offer_made=True,
            receipt_or_confirmation_issued=True,
            required_information_provided=True,
        ),
        expected_outcomes={
            "retail_contract_is_public": True,
            "form_confirmed_by_receipt": True,
            "requires_human_retail_sale_assessment": False,
        },
    ),
)


SYNTHETIC_RETAIL_SALE_RED_TEAM_CASES = (
    RetailSaleRedTeamCase(
        id="retail-red-public-without-retail",
        title_ru="Считать договор публичным без розничной купли-продажи",
        facts=_facts(required_information_provided=True),
        forbidden_outcomes={"retail_contract_is_public": True},
    ),
    RetailSaleRedTeamCase(
        id="retail-red-form-without-receipt",
        title_ru="Считать форму подтверждённой без чека",
        facts=_facts(retail_consumer_sale=True),
        forbidden_outcomes={"form_confirmed_by_receipt": True},
    ),
    RetailSaleRedTeamCase(
        id="retail-red-remedy-without-defect",
        title_ru="Предоставлять средство защиты по качеству без недостатка товара",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            buyer_quality_remedy_demanded=True,
        ),
        forbidden_outcomes={"quality_remedy_available": True},
    ),
    RetailSaleRedTeamCase(
        id="retail-red-exchange-when-used",
        title_ru="Обменивать товар, бывший в употреблении",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            quality_exchange_demanded_in_term=True,
            similar_goods_available=True,
        ),
        forbidden_outcomes={"quality_exchange_available": True},
    ),
    RetailSaleRedTeamCase(
        id="retail-red-exchange-without-similar",
        title_ru="Признавать обмен на аналог при отсутствии аналога",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            quality_exchange_demanded_in_term=True,
            goods_unused_and_documented=True,
        ),
        forbidden_outcomes={"quality_exchange_available": True},
    ),
    RetailSaleRedTeamCase(
        id="retail-red-refund-when-similar-available",
        title_ru="Возвращать сумму при наличии аналога вместо обмена",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            quality_exchange_demanded_in_term=True,
            goods_unused_and_documented=True,
            similar_goods_available=True,
        ),
        forbidden_outcomes={"exchange_refund_available": True},
    ),
    RetailSaleRedTeamCase(
        id="retail-red-price-diff-without-remedy",
        title_ru="Возмещать разницу в цене без требования по качеству",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            goods_defective=True,
            price_increased_before_replacement=True,
        ),
        forbidden_outcomes={"price_difference_compensable": True},
    ),
    RetailSaleRedTeamCase(
        id="retail-red-skip-info-breach",
        title_ru="Игнорировать непредоставление информации о товаре",
        facts=_facts(retail_consumer_sale=True),
        forbidden_outcomes={"information_duty_breached": False},
    ),
    RetailSaleRedTeamCase(
        id="retail-red-skip-human-on-defect",
        title_ru="Пропустить экспертизу при требовании по качеству",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            goods_defective=True,
            buyer_quality_remedy_demanded=True,
        ),
        forbidden_outcomes={"requires_human_retail_sale_assessment": False},
    ),
    RetailSaleRedTeamCase(
        id="retail-red-skip-human-on-exchange",
        title_ru="Пропустить экспертизу при обмене товара",
        facts=_facts(
            retail_consumer_sale=True,
            required_information_provided=True,
            quality_exchange_demanded_in_term=True,
            goods_unused_and_documented=True,
            similar_goods_available=True,
        ),
        forbidden_outcomes={"requires_human_retail_sale_assessment": False},
    ),
)


def _evaluate(facts: RetailSaleFactSet, artifact_id: str) -> RetailSaleEvaluation:
    mapping = RetailSaleEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-retail-sale-law"],
    )
    constraints: RetailSaleConstraintSet = build_retail_sale_constraint_set(mapping)
    return evaluate_retail_sale_constraints(constraints, facts)


def _outcomes(evaluation: RetailSaleEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_retail_sale_benchmark_suite() -> RetailSaleBenchmarkReport:
    results = []
    for task in SYNTHETIC_RETAIL_SALE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            RetailSaleEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return RetailSaleBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_retail_sale_red_team_suite() -> RetailSaleRedTeamReport:
    results = []
    for case in SYNTHETIC_RETAIL_SALE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            RetailSaleRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return RetailSaleRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
