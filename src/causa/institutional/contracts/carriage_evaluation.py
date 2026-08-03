from pydantic import BaseModel, Field

from causa.institutional.contracts.carriage import (
    CarriageConstraintSet,
    CarriageEvaluation,
    CarriageEvidenceMappingResult,
    CarriageFactSet,
    build_carriage_constraint_set,
    evaluate_carriage_constraints,
)


class CarriageEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: CarriageFactSet
    expected_outcomes: dict[str, bool]


class CarriageEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CarriageBenchmarkReport(BaseModel):
    id: str = "carriage-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[CarriageEvaluationResult] = Field(default_factory=list)


class CarriageRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: CarriageFactSet
    forbidden_outcomes: dict[str, bool]


class CarriageRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CarriageRedTeamReport(BaseModel):
    id: str = "carriage-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[CarriageRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> CarriageFactSet:
    values = {field_name: False for field_name in CarriageFactSet.model_fields}
    values.update(updates)
    return CarriageFactSet(**values)


SYNTHETIC_CARRIAGE_BENCHMARKS = (
    CarriageEvaluationTask(
        id="carriage-bench-not-qualified",
        title_ru="Перевозка груза или пассажира за плату не осуществляется",
        facts=_facts(cargo_lost_short_or_damaged=True),
        expected_outcomes={"carriage_qualified": False},
    ),
    CarriageEvaluationTask(
        id="carriage-bench-qualified-clean",
        title_ru="Договор перевозки без нарушений",
        facts=_facts(carriage_of_goods_or_passenger_for_fee=True),
        expected_outcomes={
            "carriage_qualified": True,
            "requires_human_carriage_assessment": False,
        },
    ),
    CarriageEvaluationTask(
        id="carriage-bench-transport-document",
        title_ru="Не оформлены транспортная накладная, билет или багажная квитанция",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            transport_document_not_issued=True,
        ),
        expected_outcomes={
            "transport_document_duty_breached": True,
            "requires_human_carriage_assessment": True,
        },
    ),
    CarriageEvaluationTask(
        id="carriage-bench-public-refusal",
        title_ru="Перевозчик транспортом общего пользования отказал без оснований",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            public_carrier_refused_without_grounds=True,
        ),
        expected_outcomes={
            "public_carriage_refusal_unlawful": True,
            "requires_human_carriage_assessment": True,
        },
    ),
    CarriageEvaluationTask(
        id="carriage-bench-charge-rules",
        title_ru="Нарушены правила о провозной плате или удержании груза",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            carriage_charge_or_retention_rules_breached=True,
        ),
        expected_outcomes={
            "charge_or_retention_rules_breached": True,
            "requires_human_carriage_assessment": True,
        },
    ),
    CarriageEvaluationTask(
        id="carriage-bench-vehicle-supply",
        title_ru="Транспортные средства не поданы либо не использованы",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            vehicle_not_supplied_or_not_used=True,
        ),
        expected_outcomes={
            "vehicle_supply_duty_breached": True,
            "requires_human_carriage_assessment": True,
        },
    ),
    CarriageEvaluationTask(
        id="carriage-bench-delivery-deadline",
        title_ru="Груз или багаж не доставлены в установленный срок",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            delivery_deadline_missed=True,
        ),
        expected_outcomes={
            "delivery_deadline_breached": True,
            "requires_human_carriage_assessment": True,
        },
    ),
    CarriageEvaluationTask(
        id="carriage-bench-passenger-delay",
        title_ru="Отправление транспортного средства с пассажиром задержано",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            passenger_departure_delayed=True,
        ),
        expected_outcomes={
            "passenger_delay_liability": True,
            "requires_human_carriage_assessment": True,
        },
    ),
    CarriageEvaluationTask(
        id="carriage-bench-cargo-loss",
        title_ru="Перевозчик не доказал отсутствие вины в утрате груза",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            cargo_lost_short_or_damaged=True,
            carrier_fault_not_disproved_for_cargo_loss=True,
        ),
        expected_outcomes={
            "cargo_damage_established": True,
            "carrier_liable_for_cargo_loss": True,
            "requires_human_carriage_assessment": True,
        },
    ),
    CarriageEvaluationTask(
        id="carriage-bench-liability-limitation",
        title_ru="Заключено соглашение об ограничении ответственности перевозчика",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            liability_limitation_agreement_present=True,
        ),
        expected_outcomes={
            "liability_limitation_void": True,
            "requires_human_carriage_assessment": True,
        },
    ),
)


SYNTHETIC_CARRIAGE_RED_TEAM_CASES = (
    CarriageRedTeamCase(
        id="carriage-red-qualify-without-carriage",
        title_ru="Квалифицировать перевозку без доставки груза или пассажира за плату",
        facts=_facts(cargo_lost_short_or_damaged=True),
        forbidden_outcomes={"carriage_qualified": True},
    ),
    CarriageRedTeamCase(
        id="carriage-red-ignore-transport-document",
        title_ru="Игнорировать отсутствие транспортного документа",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            transport_document_not_issued=True,
        ),
        forbidden_outcomes={"transport_document_duty_breached": False},
    ),
    CarriageRedTeamCase(
        id="carriage-red-allow-public-refusal",
        title_ru="Признать правомерным отказ перевозчика общего пользования",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            public_carrier_refused_without_grounds=True,
        ),
        forbidden_outcomes={"public_carriage_refusal_unlawful": False},
    ),
    CarriageRedTeamCase(
        id="carriage-red-ignore-charge-rules",
        title_ru="Игнорировать нарушение правил о провозной плате и удержании груза",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            carriage_charge_or_retention_rules_breached=True,
        ),
        forbidden_outcomes={"charge_or_retention_rules_breached": False},
    ),
    CarriageRedTeamCase(
        id="carriage-red-ignore-vehicle-supply",
        title_ru="Игнорировать неподачу транспортных средств",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            vehicle_not_supplied_or_not_used=True,
        ),
        forbidden_outcomes={"vehicle_supply_duty_breached": False},
    ),
    CarriageRedTeamCase(
        id="carriage-red-ignore-delivery-deadline",
        title_ru="Игнорировать нарушение срока доставки груза",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            delivery_deadline_missed=True,
        ),
        forbidden_outcomes={"delivery_deadline_breached": False},
    ),
    CarriageRedTeamCase(
        id="carriage-red-ignore-passenger-delay",
        title_ru="Игнорировать задержку отправления пассажира",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            passenger_departure_delayed=True,
        ),
        forbidden_outcomes={"passenger_delay_liability": False},
    ),
    CarriageRedTeamCase(
        id="carriage-red-liability-without-damage",
        title_ru="Возложить ответственность за груз без утраты или повреждения",
        facts=_facts(carriage_of_goods_or_passenger_for_fee=True),
        forbidden_outcomes={"carrier_liable_for_cargo_loss": True},
    ),
    CarriageRedTeamCase(
        id="carriage-red-uphold-liability-limitation",
        title_ru="Признать действительным соглашение об ограничении ответственности",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            liability_limitation_agreement_present=True,
        ),
        forbidden_outcomes={"liability_limitation_void": False},
    ),
    CarriageRedTeamCase(
        id="carriage-red-skip-human-on-cargo-damage",
        title_ru="Пропустить экспертизу при утрате или повреждении груза",
        facts=_facts(
            carriage_of_goods_or_passenger_for_fee=True,
            cargo_lost_short_or_damaged=True,
        ),
        forbidden_outcomes={"requires_human_carriage_assessment": False},
    ),
)


def _evaluate(facts: CarriageFactSet, artifact_id: str) -> CarriageEvaluation:
    mapping = CarriageEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-carriage-law"],
    )
    constraints: CarriageConstraintSet = build_carriage_constraint_set(mapping)
    return evaluate_carriage_constraints(constraints, facts)


def _outcomes(evaluation: CarriageEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_carriage_benchmark_suite() -> CarriageBenchmarkReport:
    results = []
    for task in SYNTHETIC_CARRIAGE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            CarriageEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return CarriageBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_carriage_red_team_suite() -> CarriageRedTeamReport:
    results = []
    for case in SYNTHETIC_CARRIAGE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            CarriageRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return CarriageRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
