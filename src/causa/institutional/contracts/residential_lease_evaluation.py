from pydantic import BaseModel, Field

from causa.institutional.contracts.residential_lease import (
    ResidentialLeaseConstraintSet,
    ResidentialLeaseEvaluation,
    ResidentialLeaseEvidenceMappingResult,
    ResidentialLeaseFactSet,
    build_residential_lease_constraint_set,
    evaluate_residential_lease_constraints,
)


class ResidentialLeaseEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ResidentialLeaseFactSet
    expected_outcomes: dict[str, bool]


class ResidentialLeaseEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ResidentialLeaseBenchmarkReport(BaseModel):
    id: str = "residential-lease-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ResidentialLeaseEvaluationResult] = Field(default_factory=list)


class ResidentialLeaseRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ResidentialLeaseFactSet
    forbidden_outcomes: dict[str, bool]


class ResidentialLeaseRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ResidentialLeaseRedTeamReport(BaseModel):
    id: str = "residential-lease-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ResidentialLeaseRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ResidentialLeaseFactSet:
    values = {field_name: False for field_name in ResidentialLeaseFactSet.model_fields}
    values.update(updates)
    return ResidentialLeaseFactSet(**values)


SYNTHETIC_RESIDENTIAL_LEASE_BENCHMARKS = (
    ResidentialLeaseEvaluationTask(
        id="residential-lease-bench-not-qualified",
        title_ru="Отношения без предоставления жилого помещения для проживания за плату",
        facts=_facts(written_form_missing=True),
        expected_outcomes={"residential_lease_qualified": False},
    ),
    ResidentialLeaseEvaluationTask(
        id="residential-lease-bench-qualified-clean",
        title_ru="Наём жилого помещения без нарушений",
        facts=_facts(dwelling_provided_for_residence_for_fee=True),
        expected_outcomes={
            "residential_lease_qualified": True,
            "requires_human_residential_lease_assessment": False,
        },
    ),
    ResidentialLeaseEvaluationTask(
        id="residential-lease-bench-form-violation",
        title_ru="Не соблюдена письменная форма договора найма",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            written_form_missing=True,
        ),
        expected_outcomes={
            "form_requirement_violated": True,
            "requires_human_residential_lease_assessment": True,
        },
    ),
    ResidentialLeaseEvaluationTask(
        id="residential-lease-bench-object-unfit",
        title_ru="Помещение не изолировано или непригодно для постоянного проживания",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            dwelling_not_isolated_or_unfit=True,
        ),
        expected_outcomes={
            "object_not_suitable_for_residence": True,
            "requires_human_residential_lease_assessment": True,
        },
    ),
    ResidentialLeaseEvaluationTask(
        id="residential-lease-bench-lessor-duties",
        title_ru="Наймодатель не обеспечивает эксплуатацию и коммунальные услуги",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            lessor_failed_operation_duties=True,
        ),
        expected_outcomes={
            "lessor_operation_duties_breached": True,
            "requires_human_residential_lease_assessment": True,
        },
    ),
    ResidentialLeaseEvaluationTask(
        id="residential-lease-bench-tenant-breach",
        title_ru="Наниматель нарушил условия пользования или внесения платы",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            tenant_breached_use_or_payment=True,
        ),
        expected_outcomes={
            "tenant_breach_established": True,
            "requires_human_residential_lease_assessment": True,
        },
    ),
    ResidentialLeaseEvaluationTask(
        id="residential-lease-bench-unilateral-rent-change",
        title_ru="Размер платы изменён в одностороннем порядке",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            rent_unilaterally_changed=True,
        ),
        expected_outcomes={
            "unilateral_rent_change_invalid": True,
            "requires_human_residential_lease_assessment": True,
        },
    ),
    ResidentialLeaseEvaluationTask(
        id="residential-lease-bench-renewal-priority",
        title_ru="Наймодатель не предложил продление за три месяца до истечения срока",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            renewal_offer_not_made_before_expiry=True,
        ),
        expected_outcomes={
            "renewal_priority_right_breached": True,
            "requires_human_residential_lease_assessment": True,
        },
    ),
    ResidentialLeaseEvaluationTask(
        id="residential-lease-bench-short-term-without-renewal",
        title_ru="Краткосрочный наём: правила о преимущественном праве не применяются",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            short_term_lease_up_to_one_year=True,
        ),
        expected_outcomes={
            "renewal_priority_right_breached": False,
            "requires_human_residential_lease_assessment": False,
        },
    ),
    ResidentialLeaseEvaluationTask(
        id="residential-lease-bench-extrajudicial-termination",
        title_ru="Наймодатель расторг договор во внесудебном порядке",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            lessor_terminated_without_court=True,
        ),
        expected_outcomes={
            "extrajudicial_termination_invalid": True,
            "requires_human_residential_lease_assessment": True,
        },
    ),
)


SYNTHETIC_RESIDENTIAL_LEASE_RED_TEAM_CASES = (
    ResidentialLeaseRedTeamCase(
        id="residential-lease-red-qualify-without-dwelling",
        title_ru="Квалифицировать наём жилья без предоставления помещения для проживания",
        facts=_facts(written_form_missing=True),
        forbidden_outcomes={"residential_lease_qualified": True},
    ),
    ResidentialLeaseRedTeamCase(
        id="residential-lease-red-ignore-form",
        title_ru="Игнорировать несоблюдение письменной формы договора найма",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            written_form_missing=True,
        ),
        forbidden_outcomes={"form_requirement_violated": False},
    ),
    ResidentialLeaseRedTeamCase(
        id="residential-lease-red-allow-unfit-object",
        title_ru="Допустить неизолированное или непригодное помещение как объект найма",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            dwelling_not_isolated_or_unfit=True,
        ),
        forbidden_outcomes={"object_not_suitable_for_residence": False},
    ),
    ResidentialLeaseRedTeamCase(
        id="residential-lease-red-ignore-lessor-duties",
        title_ru="Игнорировать неисполнение наймодателем обязанностей по эксплуатации",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            lessor_failed_operation_duties=True,
        ),
        forbidden_outcomes={"lessor_operation_duties_breached": False},
    ),
    ResidentialLeaseRedTeamCase(
        id="residential-lease-red-uphold-unilateral-rent-change",
        title_ru="Считать правомерным одностороннее изменение размера платы",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            rent_unilaterally_changed=True,
        ),
        forbidden_outcomes={"unilateral_rent_change_invalid": False},
    ),
    ResidentialLeaseRedTeamCase(
        id="residential-lease-red-ignore-renewal-duty",
        title_ru="Игнорировать обязанность предложить продление до истечения срока",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            renewal_offer_not_made_before_expiry=True,
        ),
        forbidden_outcomes={"renewal_priority_right_breached": False},
    ),
    ResidentialLeaseRedTeamCase(
        id="residential-lease-red-renewal-for-short-term",
        title_ru="Применить преимущественное право к краткосрочному найму",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            short_term_lease_up_to_one_year=True,
        ),
        forbidden_outcomes={"renewal_priority_right_breached": True},
    ),
    ResidentialLeaseRedTeamCase(
        id="residential-lease-red-allow-extrajudicial-termination",
        title_ru="Считать правомерным внесудебное расторжение по требованию наймодателя",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            lessor_terminated_without_court=True,
        ),
        forbidden_outcomes={"extrajudicial_termination_invalid": False},
    ),
    ResidentialLeaseRedTeamCase(
        id="residential-lease-red-remedy-denial-without-breach",
        title_ru="Признать отказ в сроке для устранения без нарушения нанимателя",
        facts=_facts(dwelling_provided_for_residence_for_fee=True),
        forbidden_outcomes={"remedy_period_wrongly_denied": True},
    ),
    ResidentialLeaseRedTeamCase(
        id="residential-lease-red-skip-human-on-tenant-breach",
        title_ru="Пропустить экспертизу при нарушении нанимателем условий пользования",
        facts=_facts(
            dwelling_provided_for_residence_for_fee=True,
            tenant_breached_use_or_payment=True,
        ),
        forbidden_outcomes={"requires_human_residential_lease_assessment": False},
    ),
)


def _evaluate(facts: ResidentialLeaseFactSet, artifact_id: str) -> ResidentialLeaseEvaluation:
    mapping = ResidentialLeaseEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-residential-lease-law"],
    )
    constraints: ResidentialLeaseConstraintSet = build_residential_lease_constraint_set(mapping)
    return evaluate_residential_lease_constraints(constraints, facts)


def _outcomes(evaluation: ResidentialLeaseEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_residential_lease_benchmark_suite() -> ResidentialLeaseBenchmarkReport:
    results = []
    for task in SYNTHETIC_RESIDENTIAL_LEASE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ResidentialLeaseEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ResidentialLeaseBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_residential_lease_red_team_suite() -> ResidentialLeaseRedTeamReport:
    results = []
    for case in SYNTHETIC_RESIDENTIAL_LEASE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ResidentialLeaseRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ResidentialLeaseRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
