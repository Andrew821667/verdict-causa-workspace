from pydantic import BaseModel, Field

from causa.institutional.contracts.energy_supply import (
    EnergySupplyConstraintSet,
    EnergySupplyEvaluation,
    EnergySupplyEvidenceMappingResult,
    EnergySupplyFactSet,
    build_energy_supply_constraint_set,
    evaluate_energy_supply_constraints,
)


class EnergySupplyEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: EnergySupplyFactSet
    expected_outcomes: dict[str, bool]


class EnergySupplyEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class EnergySupplyBenchmarkReport(BaseModel):
    id: str = "energy-supply-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[EnergySupplyEvaluationResult] = Field(default_factory=list)


class EnergySupplyRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: EnergySupplyFactSet
    forbidden_outcomes: dict[str, bool]


class EnergySupplyRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class EnergySupplyRedTeamReport(BaseModel):
    id: str = "energy-supply-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[EnergySupplyRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> EnergySupplyFactSet:
    values = {field_name: False for field_name in EnergySupplyFactSet.model_fields}
    values.update(updates)
    return EnergySupplyFactSet(**values)


SYNTHETIC_ENERGY_SUPPLY_BENCHMARKS = (
    EnergySupplyEvaluationTask(
        id="energy-supply-bench-qualified",
        title_ru="Подача энергии через присоединённую сеть при исправном устройстве абонента",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
        ),
        expected_outcomes={
            "energy_supply_qualified": True,
            "requires_human_energy_supply_assessment": False,
        },
    ),
    EnergySupplyEvaluationTask(
        id="energy-supply-bench-not-qualified",
        title_ru="Нет отвечающего требованиям энергопринимающего устройства",
        facts=_facts(energy_supplied_through_attached_network=True),
        expected_outcomes={"energy_supply_qualified": False},
    ),
    EnergySupplyEvaluationTask(
        id="energy-supply-bench-conforms",
        title_ru="Энергия соответствует договору по количеству и качеству",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            energy_quantity_conforms_to_contract=True,
        ),
        expected_outcomes={
            "energy_conforms_to_contract": True,
            "requires_human_energy_supply_assessment": False,
        },
    ),
    EnergySupplyEvaluationTask(
        id="energy-supply-bench-defective-quality",
        title_ru="Энергия ненадлежащего качества — право абонента отказаться от оплаты",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            energy_quantity_conforms_to_contract=True,
            energy_quality_defective=True,
        ),
        expected_outcomes={
            "subscriber_may_refuse_defective_payment": True,
            "energy_conforms_to_contract": False,
            "requires_human_energy_supply_assessment": True,
        },
    ),
    EnergySupplyEvaluationTask(
        id="energy-supply-bench-household-duty",
        title_ru="Гражданин-бытовой потребитель: содержание сетей на организации",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            subscriber_is_household_consumer=True,
        ),
        expected_outcomes={
            "subscriber_network_duty_met": True,
            "requires_human_energy_supply_assessment": False,
        },
    ),
    EnergySupplyEvaluationTask(
        id="energy-supply-bench-maintained-duty",
        title_ru="Абонент обеспечил содержание сетей и режим потребления",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            subscriber_maintained_networks_and_regime=True,
        ),
        expected_outcomes={
            "subscriber_network_duty_met": True,
            "requires_human_energy_supply_assessment": False,
        },
    ),
    EnergySupplyEvaluationTask(
        id="energy-supply-bench-payment-met",
        title_ru="Оплата за фактически принятую по учёту энергию",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            subscriber_paid_for_metered_energy=True,
        ),
        expected_outcomes={
            "payment_duty_met": True,
            "requires_human_energy_supply_assessment": False,
        },
    ),
    EnergySupplyEvaluationTask(
        id="energy-supply-bench-unpaid",
        title_ru="Абонент не оплатил принятую энергию",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
        ),
        expected_outcomes={
            "payment_duty_met": False,
            "requires_human_energy_supply_assessment": False,
        },
    ),
    EnergySupplyEvaluationTask(
        id="energy-supply-bench-emergency-interruption",
        title_ru="Неотложное ограничение подачи при аварии с уведомлением абонента",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            supply_interrupted=True,
            unagreed_interruption_for_emergency_with_notice=True,
        ),
        expected_outcomes={
            "supply_interruption_lawful": True,
            "unlawful_supply_interruption": False,
            "requires_human_energy_supply_assessment": False,
        },
    ),
    EnergySupplyEvaluationTask(
        id="energy-supply-bench-unlawful-interruption",
        title_ru="Перерыв подачи без согласования и без неотложной необходимости",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            supply_interrupted=True,
        ),
        expected_outcomes={
            "unlawful_supply_interruption": True,
            "supply_interruption_lawful": False,
            "requires_human_energy_supply_assessment": True,
        },
    ),
)


SYNTHETIC_ENERGY_SUPPLY_RED_TEAM_CASES = (
    EnergySupplyRedTeamCase(
        id="energy-supply-red-qualify-without-network",
        title_ru="Квалифицировать энергоснабжение без подачи через присоединённую сеть",
        facts=_facts(subscriber_has_compliant_receiving_device=True),
        forbidden_outcomes={"energy_supply_qualified": True},
    ),
    EnergySupplyRedTeamCase(
        id="energy-supply-red-qualify-without-device",
        title_ru="Квалифицировать энергоснабжение без исправного устройства абонента",
        facts=_facts(energy_supplied_through_attached_network=True),
        forbidden_outcomes={"energy_supply_qualified": True},
    ),
    EnergySupplyRedTeamCase(
        id="energy-supply-red-conforms-with-defect",
        title_ru="Считать энергию соответствующей договору при ненадлежащем качестве",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            energy_quantity_conforms_to_contract=True,
            energy_quality_defective=True,
        ),
        forbidden_outcomes={"energy_conforms_to_contract": True},
    ),
    EnergySupplyRedTeamCase(
        id="energy-supply-red-refuse-when-quality-ok",
        title_ru="Признать право на отказ от оплаты при надлежащем качестве энергии",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            energy_quantity_conforms_to_contract=True,
        ),
        forbidden_outcomes={"subscriber_may_refuse_defective_payment": True},
    ),
    EnergySupplyRedTeamCase(
        id="energy-supply-red-refuse-without-contract",
        title_ru="Признать право на отказ от оплаты вне договора энергоснабжения",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            energy_quality_defective=True,
        ),
        forbidden_outcomes={"subscriber_may_refuse_defective_payment": True},
    ),
    EnergySupplyRedTeamCase(
        id="energy-supply-red-network-duty-without-basis",
        title_ru="Считать обязанность по сетям исполненной без содержания и не для быта",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
        ),
        forbidden_outcomes={"subscriber_network_duty_met": True},
    ),
    EnergySupplyRedTeamCase(
        id="energy-supply-red-interruption-lawful-without-basis",
        title_ru="Считать перерыв подачи правомерным без согласования и неотложности",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            supply_interrupted=True,
        ),
        forbidden_outcomes={"supply_interruption_lawful": True},
    ),
    EnergySupplyRedTeamCase(
        id="energy-supply-red-hide-unlawful-interruption",
        title_ru="Скрыть неправомерный перерыв подачи энергии",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            supply_interrupted=True,
        ),
        forbidden_outcomes={"unlawful_supply_interruption": False},
    ),
    EnergySupplyRedTeamCase(
        id="energy-supply-red-skip-human-on-defect",
        title_ru="Пропустить экспертизу при энергии ненадлежащего качества",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            energy_quality_defective=True,
        ),
        forbidden_outcomes={"requires_human_energy_supply_assessment": False},
    ),
    EnergySupplyRedTeamCase(
        id="energy-supply-red-skip-human-on-unlawful-interruption",
        title_ru="Пропустить экспертизу при неправомерном перерыве подачи",
        facts=_facts(
            energy_supplied_through_attached_network=True,
            subscriber_has_compliant_receiving_device=True,
            supply_interrupted=True,
        ),
        forbidden_outcomes={"requires_human_energy_supply_assessment": False},
    ),
)


def _evaluate(facts: EnergySupplyFactSet, artifact_id: str) -> EnergySupplyEvaluation:
    mapping = EnergySupplyEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-energy-supply-law"],
    )
    constraints: EnergySupplyConstraintSet = build_energy_supply_constraint_set(mapping)
    return evaluate_energy_supply_constraints(constraints, facts)


def _outcomes(evaluation: EnergySupplyEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_energy_supply_benchmark_suite() -> EnergySupplyBenchmarkReport:
    results = []
    for task in SYNTHETIC_ENERGY_SUPPLY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            EnergySupplyEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return EnergySupplyBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_energy_supply_red_team_suite() -> EnergySupplyRedTeamReport:
    results = []
    for case in SYNTHETIC_ENERGY_SUPPLY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            EnergySupplyRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return EnergySupplyRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
