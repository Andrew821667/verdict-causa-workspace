from pydantic import BaseModel, Field

from causa.institutional.contracts.special_storage import (
    SpecialStorageConstraintSet,
    SpecialStorageEvaluation,
    SpecialStorageEvidenceMappingResult,
    SpecialStorageFactSet,
    build_special_storage_constraint_set,
    evaluate_special_storage_constraints,
)


class SpecialStorageEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: SpecialStorageFactSet
    expected_outcomes: dict[str, bool]


class SpecialStorageEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SpecialStorageBenchmarkReport(BaseModel):
    id: str = "special-storage-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[SpecialStorageEvaluationResult] = Field(default_factory=list)


class SpecialStorageRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: SpecialStorageFactSet
    forbidden_outcomes: dict[str, bool]


class SpecialStorageRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SpecialStorageRedTeamReport(BaseModel):
    id: str = "special-storage-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[SpecialStorageRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> SpecialStorageFactSet:
    values = {field_name: False for field_name in SpecialStorageFactSet.model_fields}
    values.update(updates)
    return SpecialStorageFactSet(**values)


SYNTHETIC_SPECIAL_STORAGE_BENCHMARKS = (
    SpecialStorageEvaluationTask(
        id="special-storage-bench-not-qualified",
        title_ru="Специальный вид хранения не установлен",
        facts=_facts(cloakroom_storage_rules_breached=True),
        expected_outcomes={"special_storage_qualified": False},
    ),
    SpecialStorageEvaluationTask(
        id="special-storage-bench-qualified-clean",
        title_ru="Специальный вид хранения без нарушений",
        facts=_facts(special_storage_service_provided=True),
        expected_outcomes={
            "special_storage_qualified": True,
            "requires_human_special_storage_assessment": False,
        },
    ),
    SpecialStorageEvaluationTask(
        id="special-storage-bench-pawnshop",
        title_ru="Нарушены правила хранения вещи в ломбарде",
        facts=_facts(
            special_storage_service_provided=True,
            pawnshop_storage_rules_breached=True,
        ),
        expected_outcomes={
            "pawnshop_duty_breached": True,
            "requires_human_special_storage_assessment": True,
        },
    ),
    SpecialStorageEvaluationTask(
        id="special-storage-bench-bank-valuables",
        title_ru="Нарушены правила хранения ценностей в банке",
        facts=_facts(
            special_storage_service_provided=True,
            bank_valuables_storage_rules_breached=True,
        ),
        expected_outcomes={
            "bank_valuables_duty_breached": True,
            "requires_human_special_storage_assessment": True,
        },
    ),
    SpecialStorageEvaluationTask(
        id="special-storage-bench-safe-deposit-box",
        title_ru="Нарушены правила хранения в индивидуальном банковском сейфе",
        facts=_facts(
            special_storage_service_provided=True,
            safe_deposit_box_rules_breached=True,
        ),
        expected_outcomes={
            "safe_deposit_box_duty_breached": True,
            "requires_human_special_storage_assessment": True,
        },
    ),
    SpecialStorageEvaluationTask(
        id="special-storage-bench-transport-locker",
        title_ru="Камера хранения нарушила хранение и правила о невостребованных вещах",
        facts=_facts(
            special_storage_service_provided=True,
            transport_locker_storage_rules_breached=True,
            locker_overdue_goods_rules_breached=True,
        ),
        expected_outcomes={
            "transport_locker_duty_breached": True,
            "locker_overdue_goods_duty_breached": True,
            "requires_human_special_storage_assessment": True,
        },
    ),
    SpecialStorageEvaluationTask(
        id="special-storage-bench-cloakroom",
        title_ru="Нарушены правила хранения в гардеробе организации",
        facts=_facts(
            special_storage_service_provided=True,
            cloakroom_storage_rules_breached=True,
        ),
        expected_outcomes={
            "cloakroom_duty_breached": True,
            "requires_human_special_storage_assessment": True,
        },
    ),
    SpecialStorageEvaluationTask(
        id="special-storage-bench-hotel",
        title_ru="Гостиница нарушила ответственность за вещи постояльца",
        facts=_facts(
            special_storage_service_provided=True,
            hotel_guest_property_rules_breached=True,
        ),
        expected_outcomes={
            "hotel_guest_property_duty_breached": True,
            "requires_human_special_storage_assessment": True,
        },
    ),
    SpecialStorageEvaluationTask(
        id="special-storage-bench-sequestration",
        title_ru="Нарушены правила о секвестре спорной вещи",
        facts=_facts(
            special_storage_service_provided=True,
            sequestration_rules_breached=True,
        ),
        expected_outcomes={
            "sequestration_duty_breached": True,
            "requires_human_special_storage_assessment": True,
        },
    ),
    SpecialStorageEvaluationTask(
        id="special-storage-bench-liability-limits",
        title_ru="Нарушены пределы ответственности по специальному виду хранения",
        facts=_facts(
            special_storage_service_provided=True,
            special_storage_liability_limits_breached=True,
        ),
        expected_outcomes={
            "liability_limits_duty_breached": True,
            "requires_human_special_storage_assessment": True,
        },
    ),
)


SYNTHETIC_SPECIAL_STORAGE_RED_TEAM_CASES = (
    SpecialStorageRedTeamCase(
        id="special-storage-red-qualify-without-service",
        title_ru="Квалифицировать специальный вид хранения без его предоставления",
        facts=_facts(cloakroom_storage_rules_breached=True),
        forbidden_outcomes={"special_storage_qualified": True},
    ),
    SpecialStorageRedTeamCase(
        id="special-storage-red-ignore-pawnshop",
        title_ru="Игнорировать нарушение правил хранения вещи в ломбарде",
        facts=_facts(
            special_storage_service_provided=True,
            pawnshop_storage_rules_breached=True,
        ),
        forbidden_outcomes={"pawnshop_duty_breached": False},
    ),
    SpecialStorageRedTeamCase(
        id="special-storage-red-ignore-bank-valuables",
        title_ru="Игнорировать нарушение правил хранения ценностей в банке",
        facts=_facts(
            special_storage_service_provided=True,
            bank_valuables_storage_rules_breached=True,
        ),
        forbidden_outcomes={"bank_valuables_duty_breached": False},
    ),
    SpecialStorageRedTeamCase(
        id="special-storage-red-ignore-safe-deposit-box",
        title_ru="Игнорировать нарушение правил хранения в индивидуальном сейфе",
        facts=_facts(
            special_storage_service_provided=True,
            safe_deposit_box_rules_breached=True,
        ),
        forbidden_outcomes={"safe_deposit_box_duty_breached": False},
    ),
    SpecialStorageRedTeamCase(
        id="special-storage-red-ignore-transport-locker",
        title_ru="Игнорировать нарушение хранения в камере хранения",
        facts=_facts(
            special_storage_service_provided=True,
            transport_locker_storage_rules_breached=True,
        ),
        forbidden_outcomes={"transport_locker_duty_breached": False},
    ),
    SpecialStorageRedTeamCase(
        id="special-storage-red-overdue-without-locker-breach",
        title_ru="Признать нарушение о невостребованных вещах без нарушения хранения в камере",
        facts=_facts(special_storage_service_provided=True),
        forbidden_outcomes={"locker_overdue_goods_duty_breached": True},
    ),
    SpecialStorageRedTeamCase(
        id="special-storage-red-ignore-cloakroom",
        title_ru="Освободить гардероб организации от обеспечения сохранности вещи",
        facts=_facts(
            special_storage_service_provided=True,
            cloakroom_storage_rules_breached=True,
        ),
        forbidden_outcomes={"cloakroom_duty_breached": False},
    ),
    SpecialStorageRedTeamCase(
        id="special-storage-red-ignore-hotel",
        title_ru="Освободить гостиницу от ответственности за вещи постояльца",
        facts=_facts(
            special_storage_service_provided=True,
            hotel_guest_property_rules_breached=True,
        ),
        forbidden_outcomes={"hotel_guest_property_duty_breached": False},
    ),
    SpecialStorageRedTeamCase(
        id="special-storage-red-ignore-sequestration",
        title_ru="Игнорировать нарушение правил о секвестре спорной вещи",
        facts=_facts(
            special_storage_service_provided=True,
            sequestration_rules_breached=True,
        ),
        forbidden_outcomes={"sequestration_duty_breached": False},
    ),
    SpecialStorageRedTeamCase(
        id="special-storage-red-skip-human-on-liability-limits",
        title_ru="Пропустить экспертизу при нарушении пределов ответственности хранителя",
        facts=_facts(
            special_storage_service_provided=True,
            special_storage_liability_limits_breached=True,
        ),
        forbidden_outcomes={"requires_human_special_storage_assessment": False},
    ),
)


def _evaluate(facts: SpecialStorageFactSet, artifact_id: str) -> SpecialStorageEvaluation:
    mapping = SpecialStorageEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-special-storage-law"],
    )
    constraints: SpecialStorageConstraintSet = build_special_storage_constraint_set(mapping)
    return evaluate_special_storage_constraints(constraints, facts)


def _outcomes(evaluation: SpecialStorageEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_special_storage_benchmark_suite() -> SpecialStorageBenchmarkReport:
    results = []
    for task in SYNTHETIC_SPECIAL_STORAGE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            SpecialStorageEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return SpecialStorageBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_special_storage_red_team_suite() -> SpecialStorageRedTeamReport:
    results = []
    for case in SYNTHETIC_SPECIAL_STORAGE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            SpecialStorageRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return SpecialStorageRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
