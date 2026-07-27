from pydantic import BaseModel, Field

from causa.institutional.contracts.lease import (
    LeaseConstraintSet,
    LeaseEvaluation,
    LeaseEvidenceMappingResult,
    LeaseFactSet,
    build_lease_constraint_set,
    evaluate_lease_constraints,
)


class LeaseEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: LeaseFactSet
    expected_outcomes: dict[str, bool]


class LeaseEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class LeaseBenchmarkReport(BaseModel):
    id: str = "lease-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[LeaseEvaluationResult] = Field(default_factory=list)


class LeaseRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: LeaseFactSet
    forbidden_outcomes: dict[str, bool]


class LeaseRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class LeaseRedTeamReport(BaseModel):
    id: str = "lease-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[LeaseRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> LeaseFactSet:
    values = {field_name: False for field_name in LeaseFactSet.model_fields}
    values.update(updates)
    return LeaseFactSet(**values)


SYNTHETIC_LEASE_BENCHMARKS = (
    LeaseEvaluationTask(
        id="lease-bench-not-qualified",
        title_ru="Отношения без предоставления имущества во временное пользование",
        facts=_facts(sublease_without_lessor_consent=True),
        expected_outcomes={"lease_qualified": False},
    ),
    LeaseEvaluationTask(
        id="lease-bench-object-not-agreed",
        title_ru="В договоре не согласован предмет аренды",
        facts=_facts(
            property_leased_for_temporary_use=True,
            lease_object_not_identifiable=True,
        ),
        expected_outcomes={
            "object_terms_not_agreed": True,
            "requires_human_lease_assessment": True,
        },
    ),
    LeaseEvaluationTask(
        id="lease-bench-form-violation",
        title_ru="Не соблюдена форма или регистрация договора аренды",
        facts=_facts(
            property_leased_for_temporary_use=True,
            lease_form_or_registration_missing=True,
        ),
        expected_outcomes={
            "form_requirement_violated": True,
            "requires_human_lease_assessment": True,
        },
    ),
    LeaseEvaluationTask(
        id="lease-bench-defects",
        title_ru="Имущество предоставлено с недостатками или без принадлежностей",
        facts=_facts(
            property_leased_for_temporary_use=True,
            leased_property_defective_or_incomplete=True,
        ),
        expected_outcomes={
            "lessor_liable_for_defects": True,
            "requires_human_lease_assessment": True,
        },
    ),
    LeaseEvaluationTask(
        id="lease-bench-third-party-rights",
        title_ru="Не раскрыты права третьих лиц на арендованное имущество",
        facts=_facts(
            property_leased_for_temporary_use=True,
            third_party_rights_not_disclosed=True,
        ),
        expected_outcomes={
            "undisclosed_third_party_rights": True,
            "requires_human_lease_assessment": True,
        },
    ),
    LeaseEvaluationTask(
        id="lease-bench-sublease-without-consent",
        title_ru="Субаренда без согласия арендодателя",
        facts=_facts(
            property_leased_for_temporary_use=True,
            sublease_without_lessor_consent=True,
        ),
        expected_outcomes={
            "unauthorized_sublease": True,
            "requires_human_lease_assessment": True,
        },
    ),
    LeaseEvaluationTask(
        id="lease-bench-capital-repair",
        title_ru="Арендодатель не производит капитальный ремонт",
        facts=_facts(
            property_leased_for_temporary_use=True,
            lessor_failed_capital_repair=True,
        ),
        expected_outcomes={
            "lessor_neglected_capital_repair": True,
            "requires_human_lease_assessment": True,
        },
    ),
    LeaseEvaluationTask(
        id="lease-bench-termination-for-breach",
        title_ru="Существенное нарушение арендатором — досрочное расторжение",
        facts=_facts(
            property_leased_for_temporary_use=True,
            tenant_materially_breached=True,
        ),
        expected_outcomes={
            "lessor_may_terminate_for_breach": True,
            "requires_human_lease_assessment": True,
        },
    ),
    LeaseEvaluationTask(
        id="lease-bench-improvement-compensation",
        title_ru="Неотделимые улучшения с согласия арендодателя",
        facts=_facts(
            property_leased_for_temporary_use=True,
            inseparable_improvements_with_consent=True,
        ),
        expected_outcomes={
            "tenant_improvement_compensation_due": True,
            "requires_human_lease_assessment": True,
        },
    ),
    LeaseEvaluationTask(
        id="lease-bench-priority-renewal",
        title_ru="Надлежащее исполнение — преимущественное право на новый срок",
        facts=_facts(
            property_leased_for_temporary_use=True,
            tenant_seeks_renewal_with_priority=True,
        ),
        expected_outcomes={
            "lease_qualified": True,
            "tenant_has_priority_renewal": True,
            "requires_human_lease_assessment": False,
        },
    ),
)


SYNTHETIC_LEASE_RED_TEAM_CASES = (
    LeaseRedTeamCase(
        id="lease-red-qualify-without-lease",
        title_ru="Квалифицировать аренду без предоставления имущества во временное пользование",
        facts=_facts(sublease_without_lessor_consent=True),
        forbidden_outcomes={"lease_qualified": True},
    ),
    LeaseRedTeamCase(
        id="lease-red-ignore-object",
        title_ru="Игнорировать несогласованность предмета договора аренды",
        facts=_facts(
            property_leased_for_temporary_use=True,
            lease_object_not_identifiable=True,
        ),
        forbidden_outcomes={"object_terms_not_agreed": False},
    ),
    LeaseRedTeamCase(
        id="lease-red-ignore-form",
        title_ru="Игнорировать несоблюдение формы или регистрации аренды",
        facts=_facts(
            property_leased_for_temporary_use=True,
            lease_form_or_registration_missing=True,
        ),
        forbidden_outcomes={"form_requirement_violated": False},
    ),
    LeaseRedTeamCase(
        id="lease-red-ignore-defects",
        title_ru="Освободить арендодателя от ответственности за недостатки имущества",
        facts=_facts(
            property_leased_for_temporary_use=True,
            leased_property_defective_or_incomplete=True,
        ),
        forbidden_outcomes={"lessor_liable_for_defects": False},
    ),
    LeaseRedTeamCase(
        id="lease-red-ignore-third-party",
        title_ru="Игнорировать нераскрытые права третьих лиц на имущество",
        facts=_facts(
            property_leased_for_temporary_use=True,
            third_party_rights_not_disclosed=True,
        ),
        forbidden_outcomes={"undisclosed_third_party_rights": False},
    ),
    LeaseRedTeamCase(
        id="lease-red-allow-sublease",
        title_ru="Считать правомерной субаренду без согласия арендодателя",
        facts=_facts(
            property_leased_for_temporary_use=True,
            sublease_without_lessor_consent=True,
        ),
        forbidden_outcomes={"unauthorized_sublease": False},
    ),
    LeaseRedTeamCase(
        id="lease-red-ignore-capital-repair",
        title_ru="Игнорировать неисполнение обязанности по капитальному ремонту",
        facts=_facts(
            property_leased_for_temporary_use=True,
            lessor_failed_capital_repair=True,
        ),
        forbidden_outcomes={"lessor_neglected_capital_repair": False},
    ),
    LeaseRedTeamCase(
        id="lease-red-deny-termination",
        title_ru="Отказать в расторжении при существенном нарушении арендатором",
        facts=_facts(
            property_leased_for_temporary_use=True,
            tenant_materially_breached=True,
        ),
        forbidden_outcomes={"lessor_may_terminate_for_breach": False},
    ),
    LeaseRedTeamCase(
        id="lease-red-compensation-without-improvements",
        title_ru="Признать возмещение улучшений без самих улучшений",
        facts=_facts(property_leased_for_temporary_use=True),
        forbidden_outcomes={"tenant_improvement_compensation_due": True},
    ),
    LeaseRedTeamCase(
        id="lease-red-skip-human-on-breach",
        title_ru="Пропустить экспертизу при существенном нарушении арендатором",
        facts=_facts(
            property_leased_for_temporary_use=True,
            tenant_materially_breached=True,
        ),
        forbidden_outcomes={"requires_human_lease_assessment": False},
    ),
)


def _evaluate(facts: LeaseFactSet, artifact_id: str) -> LeaseEvaluation:
    mapping = LeaseEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-lease-law"],
    )
    constraints: LeaseConstraintSet = build_lease_constraint_set(mapping)
    return evaluate_lease_constraints(constraints, facts)


def _outcomes(evaluation: LeaseEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_lease_benchmark_suite() -> LeaseBenchmarkReport:
    results = []
    for task in SYNTHETIC_LEASE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            LeaseEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return LeaseBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_lease_red_team_suite() -> LeaseRedTeamReport:
    results = []
    for case in SYNTHETIC_LEASE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            LeaseRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return LeaseRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
