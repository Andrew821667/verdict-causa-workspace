from pydantic import BaseModel, Field

from causa.institutional.contracts.storage import (
    StorageConstraintSet,
    StorageEvaluation,
    StorageEvidenceMappingResult,
    StorageFactSet,
    build_storage_constraint_set,
    evaluate_storage_constraints,
)


class StorageEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: StorageFactSet
    expected_outcomes: dict[str, bool]


class StorageEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class StorageBenchmarkReport(BaseModel):
    id: str = "storage-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[StorageEvaluationResult] = Field(default_factory=list)


class StorageRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: StorageFactSet
    forbidden_outcomes: dict[str, bool]


class StorageRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class StorageRedTeamReport(BaseModel):
    id: str = "storage-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[StorageRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> StorageFactSet:
    values = {field_name: False for field_name in StorageFactSet.model_fields}
    values.update(updates)
    return StorageFactSet(**values)


SYNTHETIC_STORAGE_BENCHMARKS = (
    StorageEvaluationTask(
        id="storage-bench-not-qualified",
        title_ru="Вещь не передана на хранение с обязанностью возврата",
        facts=_facts(acceptance_of_thing_refused_without_grounds=True),
        expected_outcomes={"storage_qualified": False},
    ),
    StorageEvaluationTask(
        id="storage-bench-qualified-clean",
        title_ru="Договор хранения без нарушений",
        facts=_facts(thing_accepted_for_storage_and_return=True),
        expected_outcomes={
            "storage_qualified": True,
            "requires_human_storage_assessment": False,
        },
    ),
    StorageEvaluationTask(
        id="storage-bench-form",
        title_ru="Письменная форма договора хранения не соблюдена",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            storage_written_form_not_observed=True,
        ),
        expected_outcomes={
            "storage_form_breached": True,
            "requires_human_storage_assessment": True,
        },
    ),
    StorageEvaluationTask(
        id="storage-bench-acceptance",
        title_ru="В принятии вещи на хранение отказано без оснований",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            acceptance_of_thing_refused_without_grounds=True,
        ),
        expected_outcomes={
            "acceptance_duty_breached": True,
            "requires_human_storage_assessment": True,
        },
    ),
    StorageEvaluationTask(
        id="storage-bench-period",
        title_ru="Нарушены правила о сроке хранения",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            storage_period_rules_breached=True,
        ),
        expected_outcomes={
            "storage_period_duty_breached": True,
            "requires_human_storage_assessment": True,
        },
    ),
    StorageEvaluationTask(
        id="storage-bench-safekeeping",
        title_ru="Меры по обеспечению сохранности не приняты, ответственность не применена",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            safekeeping_measures_not_taken=True,
            custodian_liability_rules_breached=True,
        ),
        expected_outcomes={
            "safekeeping_duty_breached": True,
            "custodian_liability_breached": True,
            "requires_human_storage_assessment": True,
        },
    ),
    StorageEvaluationTask(
        id="storage-bench-unauthorised-use",
        title_ru="Хранитель пользовался вещью без согласия поклажедателя",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            custodian_used_thing_without_consent=True,
        ),
        expected_outcomes={
            "unauthorised_use_established": True,
            "requires_human_storage_assessment": True,
        },
    ),
    StorageEvaluationTask(
        id="storage-bench-change-notice",
        title_ru="Изменение условий хранения и передача вещи третьему лицу не сообщены",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            storage_change_or_transfer_not_notified=True,
        ),
        expected_outcomes={
            "storage_change_notice_duty_breached": True,
            "requires_human_storage_assessment": True,
        },
    ),
    StorageEvaluationTask(
        id="storage-bench-remuneration",
        title_ru="Нарушены правила о вознаграждении и расходах на хранение",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            storage_remuneration_and_expenses_breached=True,
        ),
        expected_outcomes={
            "remuneration_and_expenses_duty_breached": True,
            "requires_human_storage_assessment": True,
        },
    ),
    StorageEvaluationTask(
        id="storage-bench-return",
        title_ru="Обязанности взять вещь обратно и возвратить её нарушены",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            thing_return_duty_breached=True,
        ),
        expected_outcomes={
            "return_duty_breached": True,
            "requires_human_storage_assessment": True,
        },
    ),
)


SYNTHETIC_STORAGE_RED_TEAM_CASES = (
    StorageRedTeamCase(
        id="storage-red-qualify-without-transfer",
        title_ru="Квалифицировать хранение без передачи вещи с обязанностью возврата",
        facts=_facts(acceptance_of_thing_refused_without_grounds=True),
        forbidden_outcomes={"storage_qualified": True},
    ),
    StorageRedTeamCase(
        id="storage-red-ignore-form",
        title_ru="Игнорировать несоблюдение письменной формы договора хранения",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            storage_written_form_not_observed=True,
        ),
        forbidden_outcomes={"storage_form_breached": False},
    ),
    StorageRedTeamCase(
        id="storage-red-ignore-acceptance",
        title_ru="Игнорировать необоснованный отказ принять вещь на хранение",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            acceptance_of_thing_refused_without_grounds=True,
        ),
        forbidden_outcomes={"acceptance_duty_breached": False},
    ),
    StorageRedTeamCase(
        id="storage-red-ignore-period",
        title_ru="Игнорировать нарушение правил о сроке хранения",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            storage_period_rules_breached=True,
        ),
        forbidden_outcomes={"storage_period_duty_breached": False},
    ),
    StorageRedTeamCase(
        id="storage-red-ignore-safekeeping",
        title_ru="Освободить хранителя от обязанности обеспечить сохранность вещи",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            safekeeping_measures_not_taken=True,
        ),
        forbidden_outcomes={"safekeeping_duty_breached": False},
    ),
    StorageRedTeamCase(
        id="storage-red-liability-without-safekeeping-breach",
        title_ru="Признать ответственность хранителя без нарушения сохранности вещи",
        facts=_facts(thing_accepted_for_storage_and_return=True),
        forbidden_outcomes={"custodian_liability_breached": True},
    ),
    StorageRedTeamCase(
        id="storage-red-allow-unauthorised-use",
        title_ru="Признать допустимым пользование вещью без согласия поклажедателя",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            custodian_used_thing_without_consent=True,
        ),
        forbidden_outcomes={"unauthorised_use_established": False},
    ),
    StorageRedTeamCase(
        id="storage-red-ignore-change-notice",
        title_ru="Игнорировать отсутствие уведомления об изменении условий хранения",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            storage_change_or_transfer_not_notified=True,
        ),
        forbidden_outcomes={"storage_change_notice_duty_breached": False},
    ),
    StorageRedTeamCase(
        id="storage-red-ignore-remuneration",
        title_ru="Игнорировать нарушение правил о вознаграждении и расходах на хранение",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            storage_remuneration_and_expenses_breached=True,
        ),
        forbidden_outcomes={"remuneration_and_expenses_duty_breached": False},
    ),
    StorageRedTeamCase(
        id="storage-red-skip-human-on-return",
        title_ru="Пропустить экспертизу при нарушении возврата вещи",
        facts=_facts(
            thing_accepted_for_storage_and_return=True,
            thing_return_duty_breached=True,
        ),
        forbidden_outcomes={"requires_human_storage_assessment": False},
    ),
)


def _evaluate(facts: StorageFactSet, artifact_id: str) -> StorageEvaluation:
    mapping = StorageEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-storage-law"],
    )
    constraints: StorageConstraintSet = build_storage_constraint_set(mapping)
    return evaluate_storage_constraints(constraints, facts)


def _outcomes(evaluation: StorageEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_storage_benchmark_suite() -> StorageBenchmarkReport:
    results = []
    for task in SYNTHETIC_STORAGE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            StorageEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return StorageBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_storage_red_team_suite() -> StorageRedTeamReport:
    results = []
    for case in SYNTHETIC_STORAGE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            StorageRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return StorageRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
