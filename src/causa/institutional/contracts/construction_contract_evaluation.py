from pydantic import BaseModel, Field

from causa.institutional.contracts.construction_contract import (
    ConstructionContractConstraintSet,
    ConstructionContractEvaluation,
    ConstructionContractEvidenceMappingResult,
    ConstructionContractFactSet,
    build_construction_contract_constraint_set,
    evaluate_construction_contract_constraints,
)


class ConstructionContractEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ConstructionContractFactSet
    expected_outcomes: dict[str, bool]


class ConstructionContractEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ConstructionContractBenchmarkReport(BaseModel):
    id: str = "construction-contract-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ConstructionContractEvaluationResult] = Field(default_factory=list)


class ConstructionContractRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ConstructionContractFactSet
    forbidden_outcomes: dict[str, bool]


class ConstructionContractRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ConstructionContractRedTeamReport(BaseModel):
    id: str = "construction-contract-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ConstructionContractRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ConstructionContractFactSet:
    values = {field_name: False for field_name in ConstructionContractFactSet.model_fields}
    values.update(updates)
    return ConstructionContractFactSet(**values)


SYNTHETIC_CONSTRUCTION_CONTRACT_BENCHMARKS = (
    ConstructionContractEvaluationTask(
        id="construction-contract-bench-not-qualified",
        title_ru="Строительные работы по заданию заказчика не выполняются",
        facts=_facts(work_deviates_from_documentation_or_requirements=True),
        expected_outcomes={"construction_contract_qualified": False},
    ),
    ConstructionContractEvaluationTask(
        id="construction-contract-bench-qualified-clean",
        title_ru="Договор строительного подряда без нарушений",
        facts=_facts(construction_work_performed_and_accepted_for_price=True),
        expected_outcomes={
            "construction_contract_qualified": True,
            "requires_human_construction_contract_assessment": False,
        },
    ),
    ConstructionContractEvaluationTask(
        id="construction-contract-bench-insurance",
        title_ru="Не исполнена обязанность застраховать риск гибели объекта",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            risk_insurance_duty_unmet=True,
        ),
        expected_outcomes={
            "risk_insurance_duty_breached": True,
            "requires_human_construction_contract_assessment": True,
        },
    ),
    ConstructionContractEvaluationTask(
        id="construction-contract-bench-documentation",
        title_ru="Не согласованы техническая документация и смета",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            technical_documentation_or_estimate_not_agreed=True,
        ),
        expected_outcomes={
            "documentation_or_estimate_condition_missing": True,
            "requires_human_construction_contract_assessment": True,
        },
    ),
    ConstructionContractEvaluationTask(
        id="construction-contract-bench-additional-work",
        title_ru="Не учтённые в документации работы обнаружены без сообщения заказчику",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            additional_work_discovered_without_notice=True,
        ),
        expected_outcomes={
            "additional_work_notice_duty_breached": True,
            "requires_human_construction_contract_assessment": True,
        },
    ),
    ConstructionContractEvaluationTask(
        id="construction-contract-bench-customer-cooperation",
        title_ru="Заказчик не предоставил земельный участок и необходимые услуги",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            customer_failed_to_provide_site_or_services=True,
        ),
        expected_outcomes={
            "customer_cooperation_duty_breached": True,
            "requires_human_construction_contract_assessment": True,
        },
    ),
    ConstructionContractEvaluationTask(
        id="construction-contract-bench-supervision",
        title_ru="Заказчику воспрепятствовали в контроле и надзоре за работами",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            customer_supervision_obstructed=True,
        ),
        expected_outcomes={
            "supervision_right_obstructed": True,
            "requires_human_construction_contract_assessment": True,
        },
    ),
    ConstructionContractEvaluationTask(
        id="construction-contract-bench-conservation",
        title_ru="Строительство приостановлено и объект законсервирован",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            construction_suspended_and_conserved=True,
        ),
        expected_outcomes={
            "conservation_settlement_due": True,
            "requires_human_construction_contract_assessment": True,
        },
    ),
    ConstructionContractEvaluationTask(
        id="construction-contract-bench-acceptance-act",
        title_ru="Отказ от подписания акта приёмки без обоснованных мотивов",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            acceptance_act_signing_refused_without_grounds=True,
        ),
        expected_outcomes={
            "acceptance_act_dispute": True,
            "requires_human_construction_contract_assessment": True,
        },
    ),
    ConstructionContractEvaluationTask(
        id="construction-contract-bench-five-year-defect",
        title_ru="Недостаток обнаружен в пределах пятилетнего предельного срока",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            work_deviates_from_documentation_or_requirements=True,
            defect_found_within_five_year_period=True,
        ),
        expected_outcomes={
            "construction_quality_breached": True,
            "five_year_defect_claim_available": True,
            "requires_human_construction_contract_assessment": True,
        },
    ),
)


SYNTHETIC_CONSTRUCTION_CONTRACT_RED_TEAM_CASES = (
    ConstructionContractRedTeamCase(
        id="construction-contract-red-qualify-without-work",
        title_ru="Квалифицировать строительный подряд без выполнения строительных работ",
        facts=_facts(work_deviates_from_documentation_or_requirements=True),
        forbidden_outcomes={"construction_contract_qualified": True},
    ),
    ConstructionContractRedTeamCase(
        id="construction-contract-red-ignore-insurance",
        title_ru="Игнорировать неисполнение обязанности застраховать риск",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            risk_insurance_duty_unmet=True,
        ),
        forbidden_outcomes={"risk_insurance_duty_breached": False},
    ),
    ConstructionContractRedTeamCase(
        id="construction-contract-red-ignore-documentation",
        title_ru="Игнорировать отсутствие согласованной документации и сметы",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            technical_documentation_or_estimate_not_agreed=True,
        ),
        forbidden_outcomes={"documentation_or_estimate_condition_missing": False},
    ),
    ConstructionContractRedTeamCase(
        id="construction-contract-red-ignore-additional-work-notice",
        title_ru="Игнорировать несообщение заказчику о дополнительных работах",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            additional_work_discovered_without_notice=True,
        ),
        forbidden_outcomes={"additional_work_notice_duty_breached": False},
    ),
    ConstructionContractRedTeamCase(
        id="construction-contract-red-ignore-customer-duties",
        title_ru="Игнорировать непредоставление участка и услуг заказчиком",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            customer_failed_to_provide_site_or_services=True,
        ),
        forbidden_outcomes={"customer_cooperation_duty_breached": False},
    ),
    ConstructionContractRedTeamCase(
        id="construction-contract-red-ignore-supervision",
        title_ru="Признать допустимым воспрепятствование контролю заказчика",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            customer_supervision_obstructed=True,
        ),
        forbidden_outcomes={"supervision_right_obstructed": False},
    ),
    ConstructionContractRedTeamCase(
        id="construction-contract-red-ignore-conservation",
        title_ru="Отказать в расчётах при консервации строительства",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            construction_suspended_and_conserved=True,
        ),
        forbidden_outcomes={"conservation_settlement_due": False},
    ),
    ConstructionContractRedTeamCase(
        id="construction-contract-red-ignore-acceptance-act",
        title_ru="Игнорировать необоснованный отказ от подписания акта приёмки",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            acceptance_act_signing_refused_without_grounds=True,
        ),
        forbidden_outcomes={"acceptance_act_dispute": False},
    ),
    ConstructionContractRedTeamCase(
        id="construction-contract-red-claim-without-deviation",
        title_ru="Признать пятилетнее требование без отступления от документации",
        facts=_facts(construction_work_performed_and_accepted_for_price=True),
        forbidden_outcomes={"five_year_defect_claim_available": True},
    ),
    ConstructionContractRedTeamCase(
        id="construction-contract-red-skip-human-on-quality",
        title_ru="Пропустить экспертизу при отступлении от строительных норм",
        facts=_facts(
            construction_work_performed_and_accepted_for_price=True,
            work_deviates_from_documentation_or_requirements=True,
        ),
        forbidden_outcomes={"requires_human_construction_contract_assessment": False},
    ),
)


def _evaluate(
    facts: ConstructionContractFactSet, artifact_id: str
) -> ConstructionContractEvaluation:
    mapping = ConstructionContractEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-construction-contract-law"],
    )
    constraints: ConstructionContractConstraintSet = build_construction_contract_constraint_set(
        mapping
    )
    return evaluate_construction_contract_constraints(constraints, facts)


def _outcomes(
    evaluation: ConstructionContractEvaluation, names: dict[str, bool]
) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_construction_contract_benchmark_suite() -> ConstructionContractBenchmarkReport:
    results = []
    for task in SYNTHETIC_CONSTRUCTION_CONTRACT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ConstructionContractEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ConstructionContractBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_construction_contract_red_team_suite() -> ConstructionContractRedTeamReport:
    results = []
    for case in SYNTHETIC_CONSTRUCTION_CONTRACT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ConstructionContractRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ConstructionContractRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
