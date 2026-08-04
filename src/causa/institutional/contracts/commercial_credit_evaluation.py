from pydantic import BaseModel, Field

from causa.institutional.contracts.commercial_credit import (
    CommercialCreditConstraintSet,
    CommercialCreditEvaluation,
    CommercialCreditEvidenceMappingResult,
    CommercialCreditFactSet,
    build_commercial_credit_constraint_set,
    evaluate_commercial_credit_constraints,
)


class CommercialCreditEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: CommercialCreditFactSet
    expected_outcomes: dict[str, bool]


class CommercialCreditEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CommercialCreditBenchmarkReport(BaseModel):
    id: str = "commercial-credit-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[CommercialCreditEvaluationResult] = Field(default_factory=list)


class CommercialCreditRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: CommercialCreditFactSet
    forbidden_outcomes: dict[str, bool]


class CommercialCreditRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CommercialCreditRedTeamReport(BaseModel):
    id: str = "commercial-credit-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[CommercialCreditRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> CommercialCreditFactSet:
    values = {field_name: False for field_name in CommercialCreditFactSet.model_fields}
    values.update(updates)
    return CommercialCreditFactSet(**values)


SYNTHETIC_COMMERCIAL_CREDIT_BENCHMARKS = (
    CommercialCreditEvaluationTask(
        id="commercial-credit-bench-not-qualified",
        title_ru="Ни товарный, ни коммерческий кредит не предоставляются",
        facts=_facts(),
        expected_outcomes={
            "goods_credit_qualified": False,
            "commercial_credit_qualified": False,
            "requires_human_commercial_credit_assessment": False,
        },
    ),
    CommercialCreditEvaluationTask(
        id="commercial-credit-bench-goods-credit-clean",
        title_ru="Договор товарного кредита без нарушений",
        facts=_facts(goods_credit_obligation_to_provide_fungibles=True),
        expected_outcomes={
            "goods_credit_qualified": True,
            "requires_human_commercial_credit_assessment": False,
        },
    ),
    CommercialCreditEvaluationTask(
        id="commercial-credit-bench-goods-not-provided",
        title_ru="Вещи по договору товарного кредита не предоставлены",
        facts=_facts(
            goods_credit_obligation_to_provide_fungibles=True,
            goods_credit_items_not_provided=True,
        ),
        expected_outcomes={
            "goods_credit_delivery_breached": True,
            "requires_human_commercial_credit_assessment": True,
        },
    ),
    CommercialCreditEvaluationTask(
        id="commercial-credit-bench-quantity",
        title_ru="Нарушены условия о количестве, ассортименте и комплектности вещей",
        facts=_facts(
            goods_credit_obligation_to_provide_fungibles=True,
            quantity_assortment_or_completeness_terms_breached=True,
        ),
        expected_outcomes={
            "quantity_terms_breached": True,
            "requires_human_commercial_credit_assessment": True,
        },
    ),
    CommercialCreditEvaluationTask(
        id="commercial-credit-bench-quality",
        title_ru="Нарушены условия о качестве, таре и упаковке вещей",
        facts=_facts(
            goods_credit_obligation_to_provide_fungibles=True,
            quality_packaging_or_container_terms_breached=True,
        ),
        expected_outcomes={
            "quality_terms_breached": True,
            "requires_human_commercial_credit_assessment": True,
        },
    ),
    CommercialCreditEvaluationTask(
        id="commercial-credit-bench-loan-rules",
        title_ru="Правила о займе не применены к товарному кредиту без основания",
        facts=_facts(
            goods_credit_obligation_to_provide_fungibles=True,
            loan_rules_application_excluded_without_ground=True,
        ),
        expected_outcomes={
            "loan_rules_exclusion_unjustified": True,
            "requires_human_commercial_credit_assessment": True,
        },
    ),
    CommercialCreditEvaluationTask(
        id="commercial-credit-bench-commercial-clean",
        title_ru="Коммерческий кредит предоставлен без нарушений",
        facts=_facts(commercial_credit_granted_in_main_contract=True),
        expected_outcomes={
            "commercial_credit_qualified": True,
            "requires_human_commercial_credit_assessment": False,
        },
    ),
    CommercialCreditEvaluationTask(
        id="commercial-credit-bench-terms-missing",
        title_ru="Условия коммерческого кредита не согласованы в основном договоре",
        facts=_facts(
            commercial_credit_granted_in_main_contract=True,
            commercial_credit_terms_not_agreed_in_main_contract=True,
        ),
        expected_outcomes={
            "commercial_credit_terms_missing": True,
            "requires_human_commercial_credit_assessment": True,
        },
    ),
    CommercialCreditEvaluationTask(
        id="commercial-credit-bench-interest",
        title_ru="Проценты за пользование коммерческим кредитом начислены с нарушением",
        facts=_facts(
            commercial_credit_granted_in_main_contract=True,
            commercial_credit_interest_terms_breached=True,
        ),
        expected_outcomes={
            "commercial_credit_interest_breached": True,
            "requires_human_commercial_credit_assessment": True,
        },
    ),
    CommercialCreditEvaluationTask(
        id="commercial-credit-bench-statutory-prohibition",
        title_ru="Законом установлен запрет предоставления коммерческого кредита",
        facts=_facts(
            commercial_credit_granted_in_main_contract=True,
            statutory_prohibition_on_commercial_credit=True,
        ),
        expected_outcomes={
            "statutory_prohibition_applies": True,
            "requires_human_commercial_credit_assessment": True,
        },
    ),
)


SYNTHETIC_COMMERCIAL_CREDIT_RED_TEAM_CASES = (
    CommercialCreditRedTeamCase(
        id="commercial-credit-red-qualify-goods-without-obligation",
        title_ru="Квалифицировать товарный кредит без обязанности предоставить вещи",
        facts=_facts(commercial_credit_granted_in_main_contract=True),
        forbidden_outcomes={"goods_credit_qualified": True},
    ),
    CommercialCreditRedTeamCase(
        id="commercial-credit-red-qualify-commercial-without-grant",
        title_ru="Квалифицировать коммерческий кредит без его предоставления по договору",
        facts=_facts(goods_credit_obligation_to_provide_fungibles=True),
        forbidden_outcomes={"commercial_credit_qualified": True},
    ),
    CommercialCreditRedTeamCase(
        id="commercial-credit-red-ignore-goods-delivery",
        title_ru="Игнорировать непредоставление вещей по товарному кредиту",
        facts=_facts(
            goods_credit_obligation_to_provide_fungibles=True,
            goods_credit_items_not_provided=True,
        ),
        forbidden_outcomes={"goods_credit_delivery_breached": False},
    ),
    CommercialCreditRedTeamCase(
        id="commercial-credit-red-ignore-quantity",
        title_ru="Игнорировать нарушение условий о количестве и комплектности",
        facts=_facts(
            goods_credit_obligation_to_provide_fungibles=True,
            quantity_assortment_or_completeness_terms_breached=True,
        ),
        forbidden_outcomes={"quantity_terms_breached": False},
    ),
    CommercialCreditRedTeamCase(
        id="commercial-credit-red-ignore-quality",
        title_ru="Игнорировать нарушение условий о качестве, таре и упаковке",
        facts=_facts(
            goods_credit_obligation_to_provide_fungibles=True,
            quality_packaging_or_container_terms_breached=True,
        ),
        forbidden_outcomes={"quality_terms_breached": False},
    ),
    CommercialCreditRedTeamCase(
        id="commercial-credit-red-ignore-loan-rules",
        title_ru="Игнорировать неприменение правил о займе к товарному кредиту",
        facts=_facts(
            goods_credit_obligation_to_provide_fungibles=True,
            loan_rules_application_excluded_without_ground=True,
        ),
        forbidden_outcomes={"loan_rules_exclusion_unjustified": False},
    ),
    CommercialCreditRedTeamCase(
        id="commercial-credit-red-terms-without-grant",
        title_ru="Признать несогласование условий без предоставления коммерческого кредита",
        facts=_facts(goods_credit_obligation_to_provide_fungibles=True),
        forbidden_outcomes={"commercial_credit_terms_missing": True},
    ),
    CommercialCreditRedTeamCase(
        id="commercial-credit-red-ignore-interest",
        title_ru="Игнорировать нарушение условий о процентах по коммерческому кредиту",
        facts=_facts(
            commercial_credit_granted_in_main_contract=True,
            commercial_credit_interest_terms_breached=True,
        ),
        forbidden_outcomes={"commercial_credit_interest_breached": False},
    ),
    CommercialCreditRedTeamCase(
        id="commercial-credit-red-ignore-application-conflict",
        title_ru="Применить правила главы вопреки правилам основного договора",
        facts=_facts(
            commercial_credit_granted_in_main_contract=True,
            chapter_rules_applied_contrary_to_main_contract=True,
        ),
        forbidden_outcomes={"chapter_rules_application_conflict": False},
    ),
    CommercialCreditRedTeamCase(
        id="commercial-credit-red-skip-human-on-prohibition",
        title_ru="Пропустить экспертизу при установленном законом запрете",
        facts=_facts(
            commercial_credit_granted_in_main_contract=True,
            statutory_prohibition_on_commercial_credit=True,
        ),
        forbidden_outcomes={"requires_human_commercial_credit_assessment": False},
    ),
)


def _evaluate(facts: CommercialCreditFactSet, artifact_id: str) -> CommercialCreditEvaluation:
    mapping = CommercialCreditEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-commercial-credit-law"],
    )
    constraints: CommercialCreditConstraintSet = build_commercial_credit_constraint_set(mapping)
    return evaluate_commercial_credit_constraints(constraints, facts)


def _outcomes(evaluation: CommercialCreditEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_commercial_credit_benchmark_suite() -> CommercialCreditBenchmarkReport:
    results = []
    for task in SYNTHETIC_COMMERCIAL_CREDIT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            CommercialCreditEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return CommercialCreditBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_commercial_credit_red_team_suite() -> CommercialCreditRedTeamReport:
    results = []
    for case in SYNTHETIC_COMMERCIAL_CREDIT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            CommercialCreditRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return CommercialCreditRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
