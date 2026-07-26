from pydantic import BaseModel, Field

from causa.institutional.contracts.annuity import (
    AnnuityConstraintSet,
    AnnuityEvaluation,
    AnnuityEvidenceMappingResult,
    AnnuityFactSet,
    build_annuity_constraint_set,
    evaluate_annuity_constraints,
)


class AnnuityEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: AnnuityFactSet
    expected_outcomes: dict[str, bool]


class AnnuityEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class AnnuityBenchmarkReport(BaseModel):
    id: str = "annuity-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[AnnuityEvaluationResult] = Field(default_factory=list)


class AnnuityRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: AnnuityFactSet
    forbidden_outcomes: dict[str, bool]


class AnnuityRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class AnnuityRedTeamReport(BaseModel):
    id: str = "annuity-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[AnnuityRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> AnnuityFactSet:
    values = {field_name: False for field_name in AnnuityFactSet.model_fields}
    values.update(updates)
    return AnnuityFactSet(**values)


SYNTHETIC_ANNUITY_BENCHMARKS = (
    AnnuityEvaluationTask(
        id="annuity-bench-qualified",
        title_ru="Имущество передано в собственность под периодические рентные платежи",
        facts=_facts(property_transferred_for_periodic_rent=True),
        expected_outcomes={
            "annuity_qualified": True,
            "requires_human_annuity_assessment": False,
        },
    ),
    AnnuityEvaluationTask(
        id="annuity-bench-not-qualified",
        title_ru="Отношения без передачи имущества под ренту",
        facts=_facts(rent_payment_overdue=True),
        expected_outcomes={"annuity_qualified": False},
    ),
    AnnuityEvaluationTask(
        id="annuity-bench-form-defect",
        title_ru="Не соблюдена нотариальная форма договора ренты",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            notarization_missing=True,
        ),
        expected_outcomes={
            "form_defect_makes_void": True,
            "requires_human_annuity_assessment": True,
        },
    ),
    AnnuityEvaluationTask(
        id="annuity-bench-security-missing",
        title_ru="Не предоставлено обеспечение выплаты ренты",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            rent_security_missing=True,
        ),
        expected_outcomes={
            "rent_security_not_provided": True,
            "requires_human_annuity_assessment": True,
        },
    ),
    AnnuityEvaluationTask(
        id="annuity-bench-overdue-interest",
        title_ru="Просрочка выплаты ренты — проценты за просрочку",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            rent_payment_overdue=True,
        ),
        expected_outcomes={
            "overdue_interest_due": True,
            "requires_human_annuity_assessment": True,
        },
    ),
    AnnuityEvaluationTask(
        id="annuity-bench-redemption-waiver-void",
        title_ru="Условие об отказе плательщика постоянной ренты от выкупа",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            permanent_rent=True,
            payer_waived_redemption_right=True,
        ),
        expected_outcomes={
            "redemption_waiver_void": True,
            "requires_human_annuity_assessment": True,
        },
    ),
    AnnuityEvaluationTask(
        id="annuity-bench-recipient-redemption",
        title_ru="Основание для выкупа постоянной ренты по требованию получателя",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            permanent_rent=True,
            recipient_redemption_ground_present=True,
        ),
        expected_outcomes={
            "recipient_may_demand_redemption": True,
            "requires_human_annuity_assessment": True,
        },
    ),
    AnnuityEvaluationTask(
        id="annuity-bench-life-annuity-termination",
        title_ru="Существенное нарушение по пожизненной ренте — расторжение",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            life_annuity_or_maintenance=True,
            payer_materially_breached=True,
        ),
        expected_outcomes={
            "recipient_may_terminate_life_annuity": True,
            "requires_human_annuity_assessment": True,
        },
    ),
    AnnuityEvaluationTask(
        id="annuity-bench-unauthorized-encumbrance",
        title_ru="Обременение имущества пожизненного содержания без согласия получателя",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            life_annuity_or_maintenance=True,
            maintenance_property_encumbered_without_consent=True,
        ),
        expected_outcomes={
            "unauthorized_maintenance_encumbrance": True,
            "requires_human_annuity_assessment": True,
        },
    ),
    AnnuityEvaluationTask(
        id="annuity-bench-clean-permanent-rent",
        title_ru="Постоянная рента без нарушений",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            permanent_rent=True,
        ),
        expected_outcomes={
            "annuity_qualified": True,
            "requires_human_annuity_assessment": False,
        },
    ),
)


SYNTHETIC_ANNUITY_RED_TEAM_CASES = (
    AnnuityRedTeamCase(
        id="annuity-red-qualify-without-transfer",
        title_ru="Квалифицировать ренту без передачи имущества под ренту",
        facts=_facts(rent_payment_overdue=True),
        forbidden_outcomes={"annuity_qualified": True},
    ),
    AnnuityRedTeamCase(
        id="annuity-red-ignore-form-defect",
        title_ru="Игнорировать ничтожность при несоблюдении нотариальной формы",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            notarization_missing=True,
        ),
        forbidden_outcomes={"form_defect_makes_void": False},
    ),
    AnnuityRedTeamCase(
        id="annuity-red-ignore-security-missing",
        title_ru="Игнорировать отсутствие обеспечения выплаты ренты",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            rent_security_missing=True,
        ),
        forbidden_outcomes={"rent_security_not_provided": False},
    ),
    AnnuityRedTeamCase(
        id="annuity-red-deny-overdue-interest",
        title_ru="Отрицать проценты за просрочку выплаты ренты",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            rent_payment_overdue=True,
        ),
        forbidden_outcomes={"overdue_interest_due": False},
    ),
    AnnuityRedTeamCase(
        id="annuity-red-uphold-redemption-waiver",
        title_ru="Считать действительным отказ плательщика постоянной ренты от выкупа",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            permanent_rent=True,
            payer_waived_redemption_right=True,
        ),
        forbidden_outcomes={"redemption_waiver_void": False},
    ),
    AnnuityRedTeamCase(
        id="annuity-red-deny-recipient-redemption",
        title_ru="Отказать в выкупе постоянной ренты при наличии основания",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            permanent_rent=True,
            recipient_redemption_ground_present=True,
        ),
        forbidden_outcomes={"recipient_may_demand_redemption": False},
    ),
    AnnuityRedTeamCase(
        id="annuity-red-deny-life-annuity-termination",
        title_ru="Отказать в расторжении пожизненной ренты при существенном нарушении",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            life_annuity_or_maintenance=True,
            payer_materially_breached=True,
        ),
        forbidden_outcomes={"recipient_may_terminate_life_annuity": False},
    ),
    AnnuityRedTeamCase(
        id="annuity-red-encumbrance-without-actual-encumbrance",
        title_ru="Считать обременение неправомерным без самого обременения",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            life_annuity_or_maintenance=True,
        ),
        forbidden_outcomes={"unauthorized_maintenance_encumbrance": True},
    ),
    AnnuityRedTeamCase(
        id="annuity-red-redemption-without-ground",
        title_ru="Признать право на выкуп постоянной ренты без основания",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            permanent_rent=True,
        ),
        forbidden_outcomes={"recipient_may_demand_redemption": True},
    ),
    AnnuityRedTeamCase(
        id="annuity-red-skip-human-on-breach",
        title_ru="Пропустить экспертизу при существенном нарушении по пожизненной ренте",
        facts=_facts(
            property_transferred_for_periodic_rent=True,
            life_annuity_or_maintenance=True,
            payer_materially_breached=True,
        ),
        forbidden_outcomes={"requires_human_annuity_assessment": False},
    ),
)


def _evaluate(facts: AnnuityFactSet, artifact_id: str) -> AnnuityEvaluation:
    mapping = AnnuityEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-annuity-law"],
    )
    constraints: AnnuityConstraintSet = build_annuity_constraint_set(mapping)
    return evaluate_annuity_constraints(constraints, facts)


def _outcomes(evaluation: AnnuityEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_annuity_benchmark_suite() -> AnnuityBenchmarkReport:
    results = []
    for task in SYNTHETIC_ANNUITY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            AnnuityEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return AnnuityBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_annuity_red_team_suite() -> AnnuityRedTeamReport:
    results = []
    for case in SYNTHETIC_ANNUITY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            AnnuityRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return AnnuityRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
