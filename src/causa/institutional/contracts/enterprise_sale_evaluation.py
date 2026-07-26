from pydantic import BaseModel, Field

from causa.institutional.contracts.enterprise_sale import (
    EnterpriseSaleConstraintSet,
    EnterpriseSaleEvaluation,
    EnterpriseSaleEvidenceMappingResult,
    EnterpriseSaleFactSet,
    build_enterprise_sale_constraint_set,
    evaluate_enterprise_sale_constraints,
)


class EnterpriseSaleEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: EnterpriseSaleFactSet
    expected_outcomes: dict[str, bool]


class EnterpriseSaleEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class EnterpriseSaleBenchmarkReport(BaseModel):
    id: str = "enterprise-sale-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[EnterpriseSaleEvaluationResult] = Field(default_factory=list)


class EnterpriseSaleRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: EnterpriseSaleFactSet
    forbidden_outcomes: dict[str, bool]


class EnterpriseSaleRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class EnterpriseSaleRedTeamReport(BaseModel):
    id: str = "enterprise-sale-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[EnterpriseSaleRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> EnterpriseSaleFactSet:
    values = {field_name: False for field_name in EnterpriseSaleFactSet.model_fields}
    values.update(updates)
    return EnterpriseSaleFactSet(**values)


SYNTHETIC_ENTERPRISE_SALE_BENCHMARKS = (
    EnterpriseSaleEvaluationTask(
        id="enterprise-sale-bench-qualified",
        title_ru="Договор о передаче предприятия как имущественного комплекса",
        facts=_facts(enterprise_as_going_concern_contract=True),
        expected_outcomes={
            "enterprise_sale_qualified": True,
            "requires_human_enterprise_sale_assessment": False,
        },
    ),
    EnterpriseSaleEvaluationTask(
        id="enterprise-sale-bench-not-qualified",
        title_ru="Отношения без передачи предприятия в целом",
        facts=_facts(written_single_document_with_annexes=True),
        expected_outcomes={"enterprise_sale_qualified": False},
    ),
    EnterpriseSaleEvaluationTask(
        id="enterprise-sale-bench-written-form",
        title_ru="Письменная форма одним документом с обязательными приложениями",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            written_single_document_with_annexes=True,
        ),
        expected_outcomes={
            "written_form_satisfied": True,
            "requires_human_enterprise_sale_assessment": False,
        },
    ),
    EnterpriseSaleEvaluationTask(
        id="enterprise-sale-bench-concluded",
        title_ru="Договор продажи предприятия зарегистрирован и заключён",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            written_single_document_with_annexes=True,
            sale_contract_registered=True,
        ),
        expected_outcomes={
            "sale_contract_concluded": True,
            "requires_human_enterprise_sale_assessment": False,
        },
    ),
    EnterpriseSaleEvaluationTask(
        id="enterprise-sale-bench-creditor-protection",
        title_ru="Кредиторы письменно уведомлены, перевода долга без согласия нет",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            creditors_notified_in_writing=True,
        ),
        expected_outcomes={
            "creditor_protection_met": True,
            "requires_human_enterprise_sale_assessment": False,
        },
    ),
    EnterpriseSaleEvaluationTask(
        id="enterprise-sale-bench-joint-liability",
        title_ru="Долг переведён без согласия кредитора — солидарная ответственность",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            debt_transferred_without_creditor_consent=True,
        ),
        expected_outcomes={
            "joint_liability_for_unconsented_debt": True,
            "creditor_protection_met": False,
            "requires_human_enterprise_sale_assessment": True,
        },
    ),
    EnterpriseSaleEvaluationTask(
        id="enterprise-sale-bench-transfer-by-deed",
        title_ru="Предприятие передано по передаточному акту",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            enterprise_transferred_by_deed=True,
        ),
        expected_outcomes={
            "enterprise_transfer_effective": True,
            "requires_human_enterprise_sale_assessment": False,
        },
    ),
    EnterpriseSaleEvaluationTask(
        id="enterprise-sale-bench-ownership-registered",
        title_ru="Переход права собственности на предприятие зарегистрирован",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            ownership_transfer_registered=True,
        ),
        expected_outcomes={
            "ownership_transfer_effective": True,
            "requires_human_enterprise_sale_assessment": False,
        },
    ),
    EnterpriseSaleEvaluationTask(
        id="enterprise-sale-bench-price-reduction",
        title_ru="Выявлены неуказанные долги — право требовать уменьшения цены",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            enterprise_transferred_by_deed=True,
            undisclosed_debts_in_composition=True,
        ),
        expected_outcomes={
            "price_reduction_available": True,
            "requires_human_enterprise_sale_assessment": True,
        },
    ),
    EnterpriseSaleEvaluationTask(
        id="enterprise-sale-bench-rescission-restricted",
        title_ru="Расторжение существенно нарушает права кредиторов или публичные интересы",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            rescission_harms_creditors_or_public=True,
        ),
        expected_outcomes={
            "rescission_restricted_by_public_interest": True,
            "requires_human_enterprise_sale_assessment": True,
        },
    ),
)


SYNTHETIC_ENTERPRISE_SALE_RED_TEAM_CASES = (
    EnterpriseSaleRedTeamCase(
        id="enterprise-sale-red-qualify-without-going-concern",
        title_ru="Квалифицировать продажу предприятия без передачи комплекса в целом",
        facts=_facts(written_single_document_with_annexes=True),
        forbidden_outcomes={"enterprise_sale_qualified": True},
    ),
    EnterpriseSaleRedTeamCase(
        id="enterprise-sale-red-form-without-annexes",
        title_ru="Считать форму соблюдённой без обязательных приложений",
        facts=_facts(enterprise_as_going_concern_contract=True),
        forbidden_outcomes={"written_form_satisfied": True},
    ),
    EnterpriseSaleRedTeamCase(
        id="enterprise-sale-red-concluded-without-registration",
        title_ru="Считать договор заключённым без государственной регистрации",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            written_single_document_with_annexes=True,
        ),
        forbidden_outcomes={"sale_contract_concluded": True},
    ),
    EnterpriseSaleRedTeamCase(
        id="enterprise-sale-red-composition-without-documents",
        title_ru="Считать состав удостоверённым без акта, баланса и заключения аудитора",
        facts=_facts(enterprise_as_going_concern_contract=True),
        forbidden_outcomes={"composition_duly_certified": True},
    ),
    EnterpriseSaleRedTeamCase(
        id="enterprise-sale-red-protection-despite-unconsented-transfer",
        title_ru="Считать права кредиторов соблюдёнными при переводе долга без согласия",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            creditors_notified_in_writing=True,
            debt_transferred_without_creditor_consent=True,
        ),
        forbidden_outcomes={"creditor_protection_met": True},
    ),
    EnterpriseSaleRedTeamCase(
        id="enterprise-sale-red-hide-joint-liability",
        title_ru="Скрыть солидарную ответственность за перевод долга без согласия",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            debt_transferred_without_creditor_consent=True,
        ),
        forbidden_outcomes={"joint_liability_for_unconsented_debt": False},
    ),
    EnterpriseSaleRedTeamCase(
        id="enterprise-sale-red-transfer-without-deed",
        title_ru="Считать предприятие переданным без передаточного акта",
        facts=_facts(enterprise_as_going_concern_contract=True),
        forbidden_outcomes={"enterprise_transfer_effective": True},
    ),
    EnterpriseSaleRedTeamCase(
        id="enterprise-sale-red-ownership-without-registration",
        title_ru="Считать переход права состоявшимся без государственной регистрации",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            enterprise_transferred_by_deed=True,
        ),
        forbidden_outcomes={"ownership_transfer_effective": True},
    ),
    EnterpriseSaleRedTeamCase(
        id="enterprise-sale-red-price-reduction-without-debts",
        title_ru="Признать право на уменьшение цены без неуказанных долгов",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            enterprise_transferred_by_deed=True,
        ),
        forbidden_outcomes={"price_reduction_available": True},
    ),
    EnterpriseSaleRedTeamCase(
        id="enterprise-sale-red-ignore-public-interest",
        title_ru="Игнорировать ограничение последствий при нарушении публичных интересов",
        facts=_facts(
            enterprise_as_going_concern_contract=True,
            rescission_harms_creditors_or_public=True,
        ),
        forbidden_outcomes={"rescission_restricted_by_public_interest": False},
    ),
)


def _evaluate(facts: EnterpriseSaleFactSet, artifact_id: str) -> EnterpriseSaleEvaluation:
    mapping = EnterpriseSaleEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-enterprise-sale-law"],
    )
    constraints: EnterpriseSaleConstraintSet = build_enterprise_sale_constraint_set(mapping)
    return evaluate_enterprise_sale_constraints(constraints, facts)


def _outcomes(evaluation: EnterpriseSaleEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_enterprise_sale_benchmark_suite() -> EnterpriseSaleBenchmarkReport:
    results = []
    for task in SYNTHETIC_ENTERPRISE_SALE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            EnterpriseSaleEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return EnterpriseSaleBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_enterprise_sale_red_team_suite() -> EnterpriseSaleRedTeamReport:
    results = []
    for case in SYNTHETIC_ENTERPRISE_SALE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            EnterpriseSaleRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return EnterpriseSaleRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
