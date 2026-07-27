from pydantic import BaseModel, Field

from causa.institutional.contracts.rental import (
    RentalConstraintSet,
    RentalEvaluation,
    RentalEvidenceMappingResult,
    RentalFactSet,
    build_rental_constraint_set,
    evaluate_rental_constraints,
)


class RentalEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: RentalFactSet
    expected_outcomes: dict[str, bool]


class RentalEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class RentalBenchmarkReport(BaseModel):
    id: str = "rental-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[RentalEvaluationResult] = Field(default_factory=list)


class RentalRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: RentalFactSet
    forbidden_outcomes: dict[str, bool]


class RentalRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class RentalRedTeamReport(BaseModel):
    id: str = "rental-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[RentalRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> RentalFactSet:
    values = {field_name: False for field_name in RentalFactSet.model_fields}
    values.update(updates)
    return RentalFactSet(**values)


SYNTHETIC_RENTAL_BENCHMARKS = (
    RentalEvaluationTask(
        id="rental-bench-not-qualified",
        title_ru="Отношения без предоставления движимого имущества профессиональным арендодателем",
        facts=_facts(written_form_missing=True),
        expected_outcomes={"rental_qualified": False},
    ),
    RentalEvaluationTask(
        id="rental-bench-qualified-clean",
        title_ru="Договор проката без нарушений",
        facts=_facts(movable_property_rented_by_professional_lessor=True),
        expected_outcomes={
            "rental_qualified": True,
            "requires_human_rental_assessment": False,
        },
    ),
    RentalEvaluationTask(
        id="rental-bench-form-violation",
        title_ru="Не соблюдена письменная форма договора проката",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            written_form_missing=True,
        ),
        expected_outcomes={
            "form_requirement_violated": True,
            "requires_human_rental_assessment": True,
        },
    ),
    RentalEvaluationTask(
        id="rental-bench-term-limit",
        title_ru="Срок проката превышает один год",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            lease_term_exceeds_one_year=True,
        ),
        expected_outcomes={
            "term_limit_exceeded": True,
            "requires_human_rental_assessment": True,
        },
    ),
    RentalEvaluationTask(
        id="rental-bench-renewal-claim",
        title_ru="Заявлено преимущественное право на возобновление проката",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            renewal_or_priority_right_claimed=True,
        ),
        expected_outcomes={
            "renewal_right_not_available": True,
            "requires_human_rental_assessment": True,
        },
    ),
    RentalEvaluationTask(
        id="rental-bench-tenant-defect-cost",
        title_ru="Недостатки из-за нарушения арендатором правил эксплуатации",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            defect_present=True,
            defect_from_tenant_misuse=True,
        ),
        expected_outcomes={
            "tenant_bears_defect_cost": True,
            "requires_human_rental_assessment": True,
        },
    ),
    RentalEvaluationTask(
        id="rental-bench-defect-remedy-overdue",
        title_ru="Арендодатель не устранил недостатки в десятидневный срок",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            defect_present=True,
            lessor_failed_to_remedy_defect=True,
        ),
        expected_outcomes={
            "defect_remedy_overdue": True,
            "requires_human_rental_assessment": True,
        },
    ),
    RentalEvaluationTask(
        id="rental-bench-early-return-refund",
        title_ru="Отказ в возврате части платы при досрочном возврате имущества",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            early_return_refund_denied=True,
        ),
        expected_outcomes={
            "early_return_refund_due": True,
            "requires_human_rental_assessment": True,
        },
    ),
    RentalEvaluationTask(
        id="rental-bench-repair-obligation",
        title_ru="Арендодатель не производит капитальный или текущий ремонт",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            repair_obligation_neglected=True,
        ),
        expected_outcomes={
            "repair_obligation_breached": True,
            "requires_human_rental_assessment": True,
        },
    ),
    RentalEvaluationTask(
        id="rental-bench-transfer-restriction",
        title_ru="Попытка субаренды или передачи прав по договору проката",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            sublease_or_rights_transfer_attempted=True,
        ),
        expected_outcomes={
            "transfer_restriction_violated": True,
            "requires_human_rental_assessment": True,
        },
    ),
)


SYNTHETIC_RENTAL_RED_TEAM_CASES = (
    RentalRedTeamCase(
        id="rental-red-qualify-without-rental",
        title_ru="Квалифицировать прокат без предоставления движимого имущества",
        facts=_facts(written_form_missing=True),
        forbidden_outcomes={"rental_qualified": True},
    ),
    RentalRedTeamCase(
        id="rental-red-ignore-form",
        title_ru="Игнорировать несоблюдение письменной формы проката",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            written_form_missing=True,
        ),
        forbidden_outcomes={"form_requirement_violated": False},
    ),
    RentalRedTeamCase(
        id="rental-red-ignore-term-limit",
        title_ru="Игнорировать превышение предельного срока проката",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            lease_term_exceeds_one_year=True,
        ),
        forbidden_outcomes={"term_limit_exceeded": False},
    ),
    RentalRedTeamCase(
        id="rental-red-grant-renewal",
        title_ru="Признать преимущественное право на возобновление проката",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            renewal_or_priority_right_claimed=True,
        ),
        forbidden_outcomes={"renewal_right_not_available": False},
    ),
    RentalRedTeamCase(
        id="rental-red-shift-defect-cost-to-lessor",
        title_ru="Возложить стоимость ремонта на арендодателя при вине арендатора",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            defect_present=True,
            defect_from_tenant_misuse=True,
        ),
        forbidden_outcomes={"tenant_bears_defect_cost": False},
    ),
    RentalRedTeamCase(
        id="rental-red-ignore-defect-remedy",
        title_ru="Игнорировать просрочку устранения недостатков арендодателем",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            defect_present=True,
            lessor_failed_to_remedy_defect=True,
        ),
        forbidden_outcomes={"defect_remedy_overdue": False},
    ),
    RentalRedTeamCase(
        id="rental-red-deny-early-return-refund",
        title_ru="Отказать в возврате части платы при досрочном возврате имущества",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            early_return_refund_denied=True,
        ),
        forbidden_outcomes={"early_return_refund_due": False},
    ),
    RentalRedTeamCase(
        id="rental-red-shift-repair-to-tenant",
        title_ru="Возложить капитальный и текущий ремонт на арендатора",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            repair_obligation_neglected=True,
        ),
        forbidden_outcomes={"repair_obligation_breached": False},
    ),
    RentalRedTeamCase(
        id="rental-red-allow-transfer",
        title_ru="Считать допустимой субаренду или передачу прав по прокату",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            sublease_or_rights_transfer_attempted=True,
        ),
        forbidden_outcomes={"transfer_restriction_violated": False},
    ),
    RentalRedTeamCase(
        id="rental-red-skip-human-on-defect",
        title_ru="Пропустить экспертизу при просрочке устранения недостатков",
        facts=_facts(
            movable_property_rented_by_professional_lessor=True,
            defect_present=True,
            lessor_failed_to_remedy_defect=True,
        ),
        forbidden_outcomes={"requires_human_rental_assessment": False},
    ),
)


def _evaluate(facts: RentalFactSet, artifact_id: str) -> RentalEvaluation:
    mapping = RentalEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-rental-law"],
    )
    constraints: RentalConstraintSet = build_rental_constraint_set(mapping)
    return evaluate_rental_constraints(constraints, facts)


def _outcomes(evaluation: RentalEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_rental_benchmark_suite() -> RentalBenchmarkReport:
    results = []
    for task in SYNTHETIC_RENTAL_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            RentalEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return RentalBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_rental_red_team_suite() -> RentalRedTeamReport:
    results = []
    for case in SYNTHETIC_RENTAL_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            RentalRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return RentalRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
