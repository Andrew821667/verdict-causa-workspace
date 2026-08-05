from pydantic import BaseModel, Field

from causa.institutional.contracts.warehouse_storage import (
    WarehouseStorageConstraintSet,
    WarehouseStorageEvaluation,
    WarehouseStorageEvidenceMappingResult,
    WarehouseStorageFactSet,
    build_warehouse_storage_constraint_set,
    evaluate_warehouse_storage_constraints,
)


class WarehouseStorageEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: WarehouseStorageFactSet
    expected_outcomes: dict[str, bool]


class WarehouseStorageEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class WarehouseStorageBenchmarkReport(BaseModel):
    id: str = "warehouse-storage-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[WarehouseStorageEvaluationResult] = Field(default_factory=list)


class WarehouseStorageRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: WarehouseStorageFactSet
    forbidden_outcomes: dict[str, bool]


class WarehouseStorageRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class WarehouseStorageRedTeamReport(BaseModel):
    id: str = "warehouse-storage-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[WarehouseStorageRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> WarehouseStorageFactSet:
    values = {field_name: False for field_name in WarehouseStorageFactSet.model_fields}
    values.update(updates)
    return WarehouseStorageFactSet(**values)


SYNTHETIC_WAREHOUSE_STORAGE_BENCHMARKS = (
    WarehouseStorageEvaluationTask(
        id="warehouse-storage-bench-not-qualified",
        title_ru="Товары не приняты товарным складом на хранение",
        facts=_facts(general_warehouse_public_duty_breached=True),
        expected_outcomes={"warehouse_storage_qualified": False},
    ),
    WarehouseStorageEvaluationTask(
        id="warehouse-storage-bench-qualified-clean",
        title_ru="Договор складского хранения без нарушений",
        facts=_facts(goods_accepted_by_warehouse_for_storage=True),
        expected_outcomes={
            "warehouse_storage_qualified": True,
            "requires_human_warehouse_storage_assessment": False,
        },
    ),
    WarehouseStorageEvaluationTask(
        id="warehouse-storage-bench-public-duty",
        title_ru="Склад общего пользования нарушил публичный характер договора",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            general_warehouse_public_duty_breached=True,
        ),
        expected_outcomes={
            "general_warehouse_duty_breached": True,
            "requires_human_warehouse_storage_assessment": True,
        },
    ),
    WarehouseStorageEvaluationTask(
        id="warehouse-storage-bench-acceptance-inspection",
        title_ru="Осмотр товаров при приёме не произведён, расхождения не зафиксированы",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            goods_inspection_on_acceptance_breached=True,
            acceptance_discrepancy_not_recorded=True,
        ),
        expected_outcomes={
            "acceptance_inspection_duty_breached": True,
            "acceptance_record_duty_breached": True,
            "requires_human_warehouse_storage_assessment": True,
        },
    ),
    WarehouseStorageEvaluationTask(
        id="warehouse-storage-bench-owner-inspection",
        title_ru="Право товаровладельца осматривать товары и брать пробы нарушено",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            owner_inspection_rights_breached=True,
        ),
        expected_outcomes={
            "owner_inspection_duty_breached": True,
            "requires_human_warehouse_storage_assessment": True,
        },
    ),
    WarehouseStorageEvaluationTask(
        id="warehouse-storage-bench-conditions-change",
        title_ru="Существенное изменение условий хранения не сообщено товаровладельцу",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            storage_conditions_change_not_notified=True,
        ),
        expected_outcomes={
            "conditions_change_notice_duty_breached": True,
            "requires_human_warehouse_storage_assessment": True,
        },
    ),
    WarehouseStorageEvaluationTask(
        id="warehouse-storage-bench-return-inspection",
        title_ru="Осмотр и проверка товаров при возвращении не произведены",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            return_inspection_and_report_breached=True,
        ),
        expected_outcomes={
            "return_inspection_duty_breached": True,
            "requires_human_warehouse_storage_assessment": True,
        },
    ),
    WarehouseStorageEvaluationTask(
        id="warehouse-storage-bench-document",
        title_ru="Складской документ в подтверждение принятия товара не выдан",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            warehouse_document_not_issued=True,
        ),
        expected_outcomes={
            "warehouse_document_duty_breached": True,
            "requires_human_warehouse_storage_assessment": True,
        },
    ),
    WarehouseStorageEvaluationTask(
        id="warehouse-storage-bench-double-certificate",
        title_ru="Нарушены правила о двойном складском свидетельстве",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            double_certificate_rules_breached=True,
        ),
        expected_outcomes={
            "double_certificate_duty_breached": True,
            "requires_human_warehouse_storage_assessment": True,
        },
    ),
    WarehouseStorageEvaluationTask(
        id="warehouse-storage-bench-goods-release",
        title_ru="Нарушены выдача товара по свидетельствам и хранение с обезличением",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            goods_release_and_commingling_rules_breached=True,
        ),
        expected_outcomes={
            "goods_release_duty_breached": True,
            "requires_human_warehouse_storage_assessment": True,
        },
    ),
)


SYNTHETIC_WAREHOUSE_STORAGE_RED_TEAM_CASES = (
    WarehouseStorageRedTeamCase(
        id="warehouse-storage-red-qualify-without-acceptance",
        title_ru="Квалифицировать складское хранение без принятия товаров складом",
        facts=_facts(general_warehouse_public_duty_breached=True),
        forbidden_outcomes={"warehouse_storage_qualified": True},
    ),
    WarehouseStorageRedTeamCase(
        id="warehouse-storage-red-ignore-public-duty",
        title_ru="Игнорировать публичный характер договора склада общего пользования",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            general_warehouse_public_duty_breached=True,
        ),
        forbidden_outcomes={"general_warehouse_duty_breached": False},
    ),
    WarehouseStorageRedTeamCase(
        id="warehouse-storage-red-ignore-acceptance-inspection",
        title_ru="Освободить склад от осмотра товаров при их приёме",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            goods_inspection_on_acceptance_breached=True,
        ),
        forbidden_outcomes={"acceptance_inspection_duty_breached": False},
    ),
    WarehouseStorageRedTeamCase(
        id="warehouse-storage-red-record-without-inspection-breach",
        title_ru="Признать нарушение фиксации расхождений без нарушения осмотра при приёме",
        facts=_facts(goods_accepted_by_warehouse_for_storage=True),
        forbidden_outcomes={"acceptance_record_duty_breached": True},
    ),
    WarehouseStorageRedTeamCase(
        id="warehouse-storage-red-ignore-owner-inspection",
        title_ru="Игнорировать право товаровладельца осматривать товары",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            owner_inspection_rights_breached=True,
        ),
        forbidden_outcomes={"owner_inspection_duty_breached": False},
    ),
    WarehouseStorageRedTeamCase(
        id="warehouse-storage-red-ignore-conditions-change",
        title_ru="Игнорировать отсутствие уведомления об изменении условий хранения",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            storage_conditions_change_not_notified=True,
        ),
        forbidden_outcomes={"conditions_change_notice_duty_breached": False},
    ),
    WarehouseStorageRedTeamCase(
        id="warehouse-storage-red-ignore-return-inspection",
        title_ru="Игнорировать отсутствие проверки товаров при их возвращении",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            return_inspection_and_report_breached=True,
        ),
        forbidden_outcomes={"return_inspection_duty_breached": False},
    ),
    WarehouseStorageRedTeamCase(
        id="warehouse-storage-red-ignore-document",
        title_ru="Признать надлежащим хранение без выдачи складского документа",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            warehouse_document_not_issued=True,
        ),
        forbidden_outcomes={"warehouse_document_duty_breached": False},
    ),
    WarehouseStorageRedTeamCase(
        id="warehouse-storage-red-ignore-double-certificate",
        title_ru="Игнорировать нарушение правил о двойном складском свидетельстве",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            double_certificate_rules_breached=True,
        ),
        forbidden_outcomes={"double_certificate_duty_breached": False},
    ),
    WarehouseStorageRedTeamCase(
        id="warehouse-storage-red-skip-human-on-goods-release",
        title_ru="Пропустить экспертизу при нарушении выдачи товара по свидетельствам",
        facts=_facts(
            goods_accepted_by_warehouse_for_storage=True,
            goods_release_and_commingling_rules_breached=True,
        ),
        forbidden_outcomes={"requires_human_warehouse_storage_assessment": False},
    ),
)


def _evaluate(facts: WarehouseStorageFactSet, artifact_id: str) -> WarehouseStorageEvaluation:
    mapping = WarehouseStorageEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-warehouse-storage-law"],
    )
    constraints: WarehouseStorageConstraintSet = build_warehouse_storage_constraint_set(mapping)
    return evaluate_warehouse_storage_constraints(constraints, facts)


def _outcomes(evaluation: WarehouseStorageEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_warehouse_storage_benchmark_suite() -> WarehouseStorageBenchmarkReport:
    results = []
    for task in SYNTHETIC_WAREHOUSE_STORAGE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            WarehouseStorageEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return WarehouseStorageBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_warehouse_storage_red_team_suite() -> WarehouseStorageRedTeamReport:
    results = []
    for case in SYNTHETIC_WAREHOUSE_STORAGE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            WarehouseStorageRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return WarehouseStorageRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
