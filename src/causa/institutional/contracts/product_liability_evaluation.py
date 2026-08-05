from pydantic import BaseModel, Field

from causa.institutional.contracts.product_liability import (
    ProductLiabilityConstraintSet,
    ProductLiabilityEvaluation,
    ProductLiabilityEvidenceMappingResult,
    ProductLiabilityFactSet,
    build_product_liability_constraint_set,
    evaluate_product_liability_constraints,
)


class ProductLiabilityEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ProductLiabilityFactSet
    expected_outcomes: dict[str, bool]


class ProductLiabilityEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ProductLiabilityBenchmarkReport(BaseModel):
    id: str = "product-liability-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ProductLiabilityEvaluationResult] = Field(default_factory=list)


class ProductLiabilityRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ProductLiabilityFactSet
    forbidden_outcomes: dict[str, bool]


class ProductLiabilityRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ProductLiabilityRedTeamReport(BaseModel):
    id: str = "product-liability-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ProductLiabilityRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ProductLiabilityFactSet:
    values = {field_name: False for field_name in ProductLiabilityFactSet.model_fields}
    values.update(updates)
    return ProductLiabilityFactSet(**values)


SYNTHETIC_PRODUCT_LIABILITY_BENCHMARKS = (
    ProductLiabilityEvaluationTask(
        id="product-liability-bench-not-qualified",
        title_ru="Вред вследствие недостатков товара, работы или услуги не установлен",
        facts=_facts(information_liability_breached=True),
        expected_outcomes={"product_liability_qualified": False},
    ),
    ProductLiabilityEvaluationTask(
        id="product-liability-bench-qualified-clean",
        title_ru="Возмещение вреда вследствие недостатков товара без нарушений",
        facts=_facts(product_or_service_defect_harm_established=True),
        expected_outcomes={
            "product_liability_qualified": True,
            "requires_human_product_liability_assessment": False,
        },
    ),
    ProductLiabilityEvaluationTask(
        id="product-liability-bench-no-fault",
        title_ru="Нарушено правило о возмещении вреда независимо от вины",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            compensation_regardless_of_fault_breached=True,
        ),
        expected_outcomes={
            "no_fault_compensation_duty_breached": True,
            "requires_human_product_liability_assessment": True,
        },
    ),
    ProductLiabilityEvaluationTask(
        id="product-liability-bench-consumer-purpose",
        title_ru="Требование о потребительской цели приобретения товара нарушено",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            consumer_purpose_requirement_breached=True,
        ),
        expected_outcomes={
            "consumer_purpose_duty_breached": True,
            "requires_human_product_liability_assessment": True,
        },
    ),
    ProductLiabilityEvaluationTask(
        id="product-liability-bench-liable-person",
        title_ru="Право потерпевшего выбрать продавца или изготовителя нарушено",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            liable_person_choice_breached=True,
        ),
        expected_outcomes={
            "liable_person_duty_breached": True,
            "requires_human_product_liability_assessment": True,
        },
    ),
    ProductLiabilityEvaluationTask(
        id="product-liability-bench-work-service",
        title_ru="Ответственность исполнителя работы или услуги определена неверно",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            work_or_service_provider_liability_breached=True,
        ),
        expected_outcomes={
            "work_service_liability_duty_breached": True,
            "requires_human_product_liability_assessment": True,
        },
    ),
    ProductLiabilityEvaluationTask(
        id="product-liability-bench-information",
        title_ru="Вред от непредоставления полной и достоверной информации не возмещён",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            information_liability_breached=True,
        ),
        expected_outcomes={
            "information_duty_breached": True,
            "requires_human_product_liability_assessment": True,
        },
    ),
    ProductLiabilityEvaluationTask(
        id="product-liability-bench-service-life",
        title_ru="Сроки возмещения вреда по сроку годности и службы нарушены",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            service_life_period_rules_breached=True,
        ),
        expected_outcomes={
            "service_life_duty_breached": True,
            "requires_human_product_liability_assessment": True,
        },
    ),
    ProductLiabilityEvaluationTask(
        id="product-liability-bench-service-life-exception",
        title_ru="Исключение при неустановленном сроке службы не учтено",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            service_life_absence_exception_disregarded=True,
        ),
        expected_outcomes={
            "service_life_exception_duty_breached": True,
            "requires_human_product_liability_assessment": True,
        },
    ),
    ProductLiabilityEvaluationTask(
        id="product-liability-bench-exculpation",
        title_ru="Основания освобождения нарушены, правила пользования потребителем не учтены",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            exculpation_grounds_breached=True,
            victim_rules_violation_not_applied=True,
        ),
        expected_outcomes={
            "exculpation_duty_breached": True,
            "victim_rules_violation_breached": True,
            "requires_human_product_liability_assessment": True,
        },
    ),
)


SYNTHETIC_PRODUCT_LIABILITY_RED_TEAM_CASES = (
    ProductLiabilityRedTeamCase(
        id="product-liability-red-qualify-without-defect-harm",
        title_ru="Применить правила о недостатках товара без установленного вреда",
        facts=_facts(information_liability_breached=True),
        forbidden_outcomes={"product_liability_qualified": True},
    ),
    ProductLiabilityRedTeamCase(
        id="product-liability-red-ignore-no-fault",
        title_ru="Освободить изготовителя от возмещения при отсутствии его вины",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            compensation_regardless_of_fault_breached=True,
        ),
        forbidden_outcomes={"no_fault_compensation_duty_breached": False},
    ),
    ProductLiabilityRedTeamCase(
        id="product-liability-red-ignore-consumer-purpose",
        title_ru="Применить правила о недостатках к предпринимательскому использованию",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            consumer_purpose_requirement_breached=True,
        ),
        forbidden_outcomes={"consumer_purpose_duty_breached": False},
    ),
    ProductLiabilityRedTeamCase(
        id="product-liability-red-ignore-liable-person",
        title_ru="Лишить потерпевшего выбора между продавцом и изготовителем",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            liable_person_choice_breached=True,
        ),
        forbidden_outcomes={"liable_person_duty_breached": False},
    ),
    ProductLiabilityRedTeamCase(
        id="product-liability-red-ignore-work-service",
        title_ru="Освободить исполнителя работы от ответственности за её недостатки",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            work_or_service_provider_liability_breached=True,
        ),
        forbidden_outcomes={"work_service_liability_duty_breached": False},
    ),
    ProductLiabilityRedTeamCase(
        id="product-liability-red-ignore-information",
        title_ru="Игнорировать вред от недостоверной информации о товаре",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            information_liability_breached=True,
        ),
        forbidden_outcomes={"information_duty_breached": False},
    ),
    ProductLiabilityRedTeamCase(
        id="product-liability-red-ignore-service-life",
        title_ru="Отказать в возмещении в пределах срока службы товара",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            service_life_period_rules_breached=True,
        ),
        forbidden_outcomes={"service_life_duty_breached": False},
    ),
    ProductLiabilityRedTeamCase(
        id="product-liability-red-ignore-service-life-exception",
        title_ru="Отказать в возмещении при неустановленном сроке службы товара",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            service_life_absence_exception_disregarded=True,
        ),
        forbidden_outcomes={"service_life_exception_duty_breached": False},
    ),
    ProductLiabilityRedTeamCase(
        id="product-liability-red-victim-rules-without-exculpation-breach",
        title_ru="Сослаться на нарушение правил пользования без нарушения оснований освобождения",
        facts=_facts(product_or_service_defect_harm_established=True),
        forbidden_outcomes={"victim_rules_violation_breached": True},
    ),
    ProductLiabilityRedTeamCase(
        id="product-liability-red-skip-human-on-exculpation",
        title_ru="Пропустить экспертизу при нарушении оснований освобождения от ответственности",
        facts=_facts(
            product_or_service_defect_harm_established=True,
            exculpation_grounds_breached=True,
        ),
        forbidden_outcomes={"requires_human_product_liability_assessment": False},
    ),
)


def _evaluate(facts: ProductLiabilityFactSet, artifact_id: str) -> ProductLiabilityEvaluation:
    mapping = ProductLiabilityEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-product-liability-law"],
    )
    constraints: ProductLiabilityConstraintSet = build_product_liability_constraint_set(mapping)
    return evaluate_product_liability_constraints(constraints, facts)


def _outcomes(evaluation: ProductLiabilityEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_product_liability_benchmark_suite() -> ProductLiabilityBenchmarkReport:
    results = []
    for task in SYNTHETIC_PRODUCT_LIABILITY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ProductLiabilityEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ProductLiabilityBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_product_liability_red_team_suite() -> ProductLiabilityRedTeamReport:
    results = []
    for case in SYNTHETIC_PRODUCT_LIABILITY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ProductLiabilityRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ProductLiabilityRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
