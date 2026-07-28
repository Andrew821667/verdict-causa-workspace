from pydantic import BaseModel, Field

from causa.institutional.contracts.vehicle_lease import (
    VehicleLeaseConstraintSet,
    VehicleLeaseEvaluation,
    VehicleLeaseEvidenceMappingResult,
    VehicleLeaseFactSet,
    build_vehicle_lease_constraint_set,
    evaluate_vehicle_lease_constraints,
)


class VehicleLeaseEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: VehicleLeaseFactSet
    expected_outcomes: dict[str, bool]


class VehicleLeaseEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class VehicleLeaseBenchmarkReport(BaseModel):
    id: str = "vehicle-lease-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[VehicleLeaseEvaluationResult] = Field(default_factory=list)


class VehicleLeaseRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: VehicleLeaseFactSet
    forbidden_outcomes: dict[str, bool]


class VehicleLeaseRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class VehicleLeaseRedTeamReport(BaseModel):
    id: str = "vehicle-lease-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[VehicleLeaseRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> VehicleLeaseFactSet:
    values = {field_name: False for field_name in VehicleLeaseFactSet.model_fields}
    values.update(updates)
    return VehicleLeaseFactSet(**values)


SYNTHETIC_VEHICLE_LEASE_BENCHMARKS = (
    VehicleLeaseEvaluationTask(
        id="vehicle-lease-bench-not-qualified",
        title_ru="Отношения без предоставления транспортного средства во временное пользование",
        facts=_facts(written_form_missing=True),
        expected_outcomes={"vehicle_lease_qualified": False},
    ),
    VehicleLeaseEvaluationTask(
        id="vehicle-lease-bench-qualified-with-crew",
        title_ru="Аренда транспортного средства с экипажем без нарушений",
        facts=_facts(vehicle_leased_for_temporary_use=True, lease_with_crew=True),
        expected_outcomes={
            "vehicle_lease_qualified": True,
            "requires_human_vehicle_lease_assessment": False,
        },
    ),
    VehicleLeaseEvaluationTask(
        id="vehicle-lease-bench-form-violation",
        title_ru="Не соблюдена письменная форма договора аренды транспортного средства",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            written_form_missing=True,
        ),
        expected_outcomes={
            "form_requirement_violated": True,
            "requires_human_vehicle_lease_assessment": True,
        },
    ),
    VehicleLeaseEvaluationTask(
        id="vehicle-lease-bench-renewal-claim",
        title_ru="Заявлено преимущественное право на новый срок",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            renewal_or_priority_right_claimed=True,
        ),
        expected_outcomes={
            "renewal_right_not_available": True,
            "requires_human_vehicle_lease_assessment": True,
        },
    ),
    VehicleLeaseEvaluationTask(
        id="vehicle-lease-bench-maintenance",
        title_ru="Не исполнена обязанность по содержанию и ремонту",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            maintenance_or_repair_neglected=True,
        ),
        expected_outcomes={
            "maintenance_duty_breached": True,
            "requires_human_vehicle_lease_assessment": True,
        },
    ),
    VehicleLeaseEvaluationTask(
        id="vehicle-lease-bench-crew-shortfall",
        title_ru="При аренде с экипажем услуги экипажа не предоставлены",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            lease_with_crew=True,
            crew_service_not_provided=True,
        ),
        expected_outcomes={
            "crew_service_shortfall": True,
            "requires_human_vehicle_lease_assessment": True,
        },
    ),
    VehicleLeaseEvaluationTask(
        id="vehicle-lease-bench-operating-costs",
        title_ru="Расходы по эксплуатации распределены неверно",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            operating_costs_misallocated=True,
        ),
        expected_outcomes={
            "operating_cost_misallocation": True,
            "requires_human_vehicle_lease_assessment": True,
        },
    ),
    VehicleLeaseEvaluationTask(
        id="vehicle-lease-bench-insurance",
        title_ru="Не исполнена обязанность по страхованию",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            insurance_obligation_breached=True,
        ),
        expected_outcomes={
            "insurance_duty_breached": True,
            "requires_human_vehicle_lease_assessment": True,
        },
    ),
    VehicleLeaseEvaluationTask(
        id="vehicle-lease-bench-sublease-restriction",
        title_ru="Субаренда неправомерно ограничена согласием арендодателя",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            sublease_wrongly_restricted=True,
        ),
        expected_outcomes={
            "sublease_restriction_invalid": True,
            "requires_human_vehicle_lease_assessment": True,
        },
    ),
    VehicleLeaseEvaluationTask(
        id="vehicle-lease-bench-third-party-liability",
        title_ru="Ответственность за вред третьим лицам распределена неверно",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            third_party_harm_liability_misassigned=True,
        ),
        expected_outcomes={
            "third_party_liability_misassigned": True,
            "requires_human_vehicle_lease_assessment": True,
        },
    ),
)


SYNTHETIC_VEHICLE_LEASE_RED_TEAM_CASES = (
    VehicleLeaseRedTeamCase(
        id="vehicle-lease-red-qualify-without-lease",
        title_ru="Квалифицировать аренду транспортного средства без его предоставления",
        facts=_facts(written_form_missing=True),
        forbidden_outcomes={"vehicle_lease_qualified": True},
    ),
    VehicleLeaseRedTeamCase(
        id="vehicle-lease-red-ignore-form",
        title_ru="Игнорировать несоблюдение письменной формы независимо от срока",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            written_form_missing=True,
        ),
        forbidden_outcomes={"form_requirement_violated": False},
    ),
    VehicleLeaseRedTeamCase(
        id="vehicle-lease-red-grant-renewal",
        title_ru="Признать преимущественное право на новый срок при аренде транспорта",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            renewal_or_priority_right_claimed=True,
        ),
        forbidden_outcomes={"renewal_right_not_available": False},
    ),
    VehicleLeaseRedTeamCase(
        id="vehicle-lease-red-ignore-maintenance",
        title_ru="Игнорировать неисполнение обязанности по содержанию и ремонту",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            maintenance_or_repair_neglected=True,
        ),
        forbidden_outcomes={"maintenance_duty_breached": False},
    ),
    VehicleLeaseRedTeamCase(
        id="vehicle-lease-red-ignore-crew",
        title_ru="Игнорировать непредоставление услуг экипажа при аренде с экипажем",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            lease_with_crew=True,
            crew_service_not_provided=True,
        ),
        forbidden_outcomes={"crew_service_shortfall": False},
    ),
    VehicleLeaseRedTeamCase(
        id="vehicle-lease-red-crew-shortfall-without-crew-lease",
        title_ru="Признать недостаток услуг экипажа при аренде без экипажа",
        facts=_facts(vehicle_leased_for_temporary_use=True),
        forbidden_outcomes={"crew_service_shortfall": True},
    ),
    VehicleLeaseRedTeamCase(
        id="vehicle-lease-red-ignore-operating-costs",
        title_ru="Игнорировать неверное распределение расходов по эксплуатации",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            operating_costs_misallocated=True,
        ),
        forbidden_outcomes={"operating_cost_misallocation": False},
    ),
    VehicleLeaseRedTeamCase(
        id="vehicle-lease-red-ignore-insurance",
        title_ru="Игнорировать неисполнение обязанности по страхованию",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            insurance_obligation_breached=True,
        ),
        forbidden_outcomes={"insurance_duty_breached": False},
    ),
    VehicleLeaseRedTeamCase(
        id="vehicle-lease-red-uphold-sublease-restriction",
        title_ru="Считать правомерным запрет субаренды без оговорки в договоре",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            sublease_wrongly_restricted=True,
        ),
        forbidden_outcomes={"sublease_restriction_invalid": False},
    ),
    VehicleLeaseRedTeamCase(
        id="vehicle-lease-red-skip-human-on-liability",
        title_ru="Пропустить экспертизу при неверном распределении ответственности за вред",
        facts=_facts(
            vehicle_leased_for_temporary_use=True,
            third_party_harm_liability_misassigned=True,
        ),
        forbidden_outcomes={"requires_human_vehicle_lease_assessment": False},
    ),
)


def _evaluate(facts: VehicleLeaseFactSet, artifact_id: str) -> VehicleLeaseEvaluation:
    mapping = VehicleLeaseEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-vehicle-lease-law"],
    )
    constraints: VehicleLeaseConstraintSet = build_vehicle_lease_constraint_set(mapping)
    return evaluate_vehicle_lease_constraints(constraints, facts)


def _outcomes(evaluation: VehicleLeaseEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_vehicle_lease_benchmark_suite() -> VehicleLeaseBenchmarkReport:
    results = []
    for task in SYNTHETIC_VEHICLE_LEASE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            VehicleLeaseEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return VehicleLeaseBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_vehicle_lease_red_team_suite() -> VehicleLeaseRedTeamReport:
    results = []
    for case in SYNTHETIC_VEHICLE_LEASE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            VehicleLeaseRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return VehicleLeaseRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
