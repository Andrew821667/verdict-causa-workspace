from pydantic import BaseModel, Field

from causa.institutional.contracts.building_lease import (
    BuildingLeaseConstraintSet,
    BuildingLeaseEvaluation,
    BuildingLeaseEvidenceMappingResult,
    BuildingLeaseFactSet,
    build_building_lease_constraint_set,
    evaluate_building_lease_constraints,
)


class BuildingLeaseEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: BuildingLeaseFactSet
    expected_outcomes: dict[str, bool]


class BuildingLeaseEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BuildingLeaseBenchmarkReport(BaseModel):
    id: str = "building-lease-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[BuildingLeaseEvaluationResult] = Field(default_factory=list)


class BuildingLeaseRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: BuildingLeaseFactSet
    forbidden_outcomes: dict[str, bool]


class BuildingLeaseRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BuildingLeaseRedTeamReport(BaseModel):
    id: str = "building-lease-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[BuildingLeaseRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> BuildingLeaseFactSet:
    values = {field_name: False for field_name in BuildingLeaseFactSet.model_fields}
    values.update(updates)
    return BuildingLeaseFactSet(**values)


SYNTHETIC_BUILDING_LEASE_BENCHMARKS = (
    BuildingLeaseEvaluationTask(
        id="building-lease-bench-not-qualified",
        title_ru="Отношения без передачи здания или сооружения во временное пользование",
        facts=_facts(single_written_document_missing=True),
        expected_outcomes={"building_lease_qualified": False},
    ),
    BuildingLeaseEvaluationTask(
        id="building-lease-bench-qualified-clean",
        title_ru="Аренда здания без нарушений",
        facts=_facts(building_leased_for_temporary_use=True),
        expected_outcomes={
            "building_lease_qualified": True,
            "requires_human_building_lease_assessment": False,
        },
    ),
    BuildingLeaseEvaluationTask(
        id="building-lease-bench-form-defect",
        title_ru="Договор не оформлен одним документом, подписанным сторонами",
        facts=_facts(
            building_leased_for_temporary_use=True,
            single_written_document_missing=True,
        ),
        expected_outcomes={
            "form_defect_makes_void": True,
            "requires_human_building_lease_assessment": True,
        },
    ),
    BuildingLeaseEvaluationTask(
        id="building-lease-bench-registration-missing",
        title_ru="Срок не менее года, государственная регистрация отсутствует",
        facts=_facts(
            building_leased_for_temporary_use=True,
            lease_term_at_least_one_year=True,
            state_registration_missing=True,
        ),
        expected_outcomes={
            "registration_required_and_missing": True,
            "requires_human_building_lease_assessment": True,
        },
    ),
    BuildingLeaseEvaluationTask(
        id="building-lease-bench-short-term-without-registration",
        title_ru="Срок менее года: регистрация не требуется",
        facts=_facts(
            building_leased_for_temporary_use=True,
            state_registration_missing=True,
        ),
        expected_outcomes={
            "registration_required_and_missing": False,
            "requires_human_building_lease_assessment": False,
        },
    ),
    BuildingLeaseEvaluationTask(
        id="building-lease-bench-land-rights",
        title_ru="Права на часть земельного участка не переданы арендатору",
        facts=_facts(
            building_leased_for_temporary_use=True,
            land_rights_not_transferred=True,
        ),
        expected_outcomes={
            "land_rights_not_conveyed": True,
            "requires_human_building_lease_assessment": True,
        },
    ),
    BuildingLeaseEvaluationTask(
        id="building-lease-bench-land-ownership-change",
        title_ru="Смена собственника участка и отказ в сохранении права пользования",
        facts=_facts(
            building_leased_for_temporary_use=True,
            land_ownership_changed=True,
            land_use_right_denied_after_change=True,
        ),
        expected_outcomes={
            "land_use_right_preserved": True,
            "requires_human_building_lease_assessment": True,
        },
    ),
    BuildingLeaseEvaluationTask(
        id="building-lease-bench-rent-not-agreed",
        title_ru="Не согласован размер арендной платы",
        facts=_facts(
            building_leased_for_temporary_use=True,
            agreed_rent_amount_missing=True,
        ),
        expected_outcomes={
            "rent_term_not_agreed": True,
            "requires_human_building_lease_assessment": True,
        },
    ),
    BuildingLeaseEvaluationTask(
        id="building-lease-bench-transfer-deed",
        title_ru="Передача здания не оформлена передаточным актом",
        facts=_facts(
            building_leased_for_temporary_use=True,
            transfer_deed_missing=True,
        ),
        expected_outcomes={
            "transfer_not_documented": True,
            "requires_human_building_lease_assessment": True,
        },
    ),
    BuildingLeaseEvaluationTask(
        id="building-lease-bench-return-deed",
        title_ru="Возврат здания не оформлен передаточным актом",
        facts=_facts(
            building_leased_for_temporary_use=True,
            return_deed_missing=True,
        ),
        expected_outcomes={
            "return_not_documented": True,
            "requires_human_building_lease_assessment": True,
        },
    ),
)


SYNTHETIC_BUILDING_LEASE_RED_TEAM_CASES = (
    BuildingLeaseRedTeamCase(
        id="building-lease-red-qualify-without-lease",
        title_ru="Квалифицировать аренду здания без его передачи",
        facts=_facts(single_written_document_missing=True),
        forbidden_outcomes={"building_lease_qualified": True},
    ),
    BuildingLeaseRedTeamCase(
        id="building-lease-red-ignore-form",
        title_ru="Игнорировать недействительность при несоблюдении формы одного документа",
        facts=_facts(
            building_leased_for_temporary_use=True,
            single_written_document_missing=True,
        ),
        forbidden_outcomes={"form_defect_makes_void": False},
    ),
    BuildingLeaseRedTeamCase(
        id="building-lease-red-ignore-registration",
        title_ru="Игнорировать отсутствие регистрации при сроке не менее года",
        facts=_facts(
            building_leased_for_temporary_use=True,
            lease_term_at_least_one_year=True,
            state_registration_missing=True,
        ),
        forbidden_outcomes={"registration_required_and_missing": False},
    ),
    BuildingLeaseRedTeamCase(
        id="building-lease-red-registration-for-short-term",
        title_ru="Требовать регистрацию при сроке менее года",
        facts=_facts(
            building_leased_for_temporary_use=True,
            state_registration_missing=True,
        ),
        forbidden_outcomes={"registration_required_and_missing": True},
    ),
    BuildingLeaseRedTeamCase(
        id="building-lease-red-ignore-land-rights",
        title_ru="Игнорировать непередачу прав на часть земельного участка",
        facts=_facts(
            building_leased_for_temporary_use=True,
            land_rights_not_transferred=True,
        ),
        forbidden_outcomes={"land_rights_not_conveyed": False},
    ),
    BuildingLeaseRedTeamCase(
        id="building-lease-red-deny-land-use-after-change",
        title_ru="Отказать в сохранении права пользования участком при смене собственника",
        facts=_facts(
            building_leased_for_temporary_use=True,
            land_ownership_changed=True,
            land_use_right_denied_after_change=True,
        ),
        forbidden_outcomes={"land_use_right_preserved": False},
    ),
    BuildingLeaseRedTeamCase(
        id="building-lease-red-fill-rent-by-comparable-price",
        title_ru="Восполнить отсутствующий размер платы правилами о сравнимой цене",
        facts=_facts(
            building_leased_for_temporary_use=True,
            agreed_rent_amount_missing=True,
        ),
        forbidden_outcomes={"rent_term_not_agreed": False},
    ),
    BuildingLeaseRedTeamCase(
        id="building-lease-red-ignore-transfer-deed",
        title_ru="Игнорировать отсутствие передаточного акта при передаче здания",
        facts=_facts(
            building_leased_for_temporary_use=True,
            transfer_deed_missing=True,
        ),
        forbidden_outcomes={"transfer_not_documented": False},
    ),
    BuildingLeaseRedTeamCase(
        id="building-lease-red-land-use-without-ownership-change",
        title_ru="Признать нарушение права пользования участком без смены собственника",
        facts=_facts(building_leased_for_temporary_use=True),
        forbidden_outcomes={"land_use_right_preserved": True},
    ),
    BuildingLeaseRedTeamCase(
        id="building-lease-red-skip-human-on-return-deed",
        title_ru="Пропустить экспертизу при отсутствии акта возврата здания",
        facts=_facts(
            building_leased_for_temporary_use=True,
            return_deed_missing=True,
        ),
        forbidden_outcomes={"requires_human_building_lease_assessment": False},
    ),
)


def _evaluate(facts: BuildingLeaseFactSet, artifact_id: str) -> BuildingLeaseEvaluation:
    mapping = BuildingLeaseEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-building-lease-law"],
    )
    constraints: BuildingLeaseConstraintSet = build_building_lease_constraint_set(mapping)
    return evaluate_building_lease_constraints(constraints, facts)


def _outcomes(evaluation: BuildingLeaseEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_building_lease_benchmark_suite() -> BuildingLeaseBenchmarkReport:
    results = []
    for task in SYNTHETIC_BUILDING_LEASE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            BuildingLeaseEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return BuildingLeaseBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_building_lease_red_team_suite() -> BuildingLeaseRedTeamReport:
    results = []
    for case in SYNTHETIC_BUILDING_LEASE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            BuildingLeaseRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return BuildingLeaseRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
