from pydantic import BaseModel, Field

from causa.institutional.contracts.gratuitous_use import (
    GratuitousUseConstraintSet,
    GratuitousUseEvaluation,
    GratuitousUseEvidenceMappingResult,
    GratuitousUseFactSet,
    build_gratuitous_use_constraint_set,
    evaluate_gratuitous_use_constraints,
)


class GratuitousUseEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: GratuitousUseFactSet
    expected_outcomes: dict[str, bool]


class GratuitousUseEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GratuitousUseBenchmarkReport(BaseModel):
    id: str = "gratuitous-use-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[GratuitousUseEvaluationResult] = Field(default_factory=list)


class GratuitousUseRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: GratuitousUseFactSet
    forbidden_outcomes: dict[str, bool]


class GratuitousUseRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GratuitousUseRedTeamReport(BaseModel):
    id: str = "gratuitous-use-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[GratuitousUseRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> GratuitousUseFactSet:
    values = {field_name: False for field_name in GratuitousUseFactSet.model_fields}
    values.update(updates)
    return GratuitousUseFactSet(**values)


SYNTHETIC_GRATUITOUS_USE_BENCHMARKS = (
    GratuitousUseEvaluationTask(
        id="gratuitous-use-bench-not-qualified",
        title_ru="Отношения без передачи вещи в безвозмездное временное пользование",
        facts=_facts(maintenance_duty_neglected=True),
        expected_outcomes={"gratuitous_use_qualified": False},
    ),
    GratuitousUseEvaluationTask(
        id="gratuitous-use-bench-qualified-clean",
        title_ru="Безвозмездное пользование без нарушений",
        facts=_facts(thing_provided_for_free_temporary_use=True),
        expected_outcomes={
            "gratuitous_use_qualified": True,
            "requires_human_gratuitous_use_assessment": False,
        },
    ),
    GratuitousUseEvaluationTask(
        id="gratuitous-use-bench-insider-transfer",
        title_ru="Коммерческая организация передала вещь своему руководителю",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            lender_is_organization_transferring_to_insider=True,
        ),
        expected_outcomes={
            "prohibited_transfer_to_insider": True,
            "requires_human_gratuitous_use_assessment": True,
        },
    ),
    GratuitousUseEvaluationTask(
        id="gratuitous-use-bench-delivery-breach",
        title_ru="Вещь не предоставлена или предоставлена без принадлежностей",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            thing_not_provided_or_incomplete=True,
        ),
        expected_outcomes={
            "delivery_obligation_breached": True,
            "requires_human_gratuitous_use_assessment": True,
        },
    ),
    GratuitousUseEvaluationTask(
        id="gratuitous-use-bench-concealed-defect",
        title_ru="Недостаток умышленно или по грубой неосторожности не оговорён",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            defect_intentionally_or_grossly_concealed=True,
        ),
        expected_outcomes={
            "lender_liable_for_concealed_defect": True,
            "requires_human_gratuitous_use_assessment": True,
        },
    ),
    GratuitousUseEvaluationTask(
        id="gratuitous-use-bench-third-party-rights",
        title_ru="Не раскрыты права третьих лиц на переданную вещь",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            third_party_rights_not_disclosed=True,
        ),
        expected_outcomes={
            "undisclosed_third_party_rights": True,
            "requires_human_gratuitous_use_assessment": True,
        },
    ),
    GratuitousUseEvaluationTask(
        id="gratuitous-use-bench-maintenance",
        title_ru="Ссудополучатель не поддерживает вещь в исправном состоянии",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            maintenance_duty_neglected=True,
        ),
        expected_outcomes={
            "maintenance_duty_breached": True,
            "requires_human_gratuitous_use_assessment": True,
        },
    ),
    GratuitousUseEvaluationTask(
        id="gratuitous-use-bench-risk-misallocation",
        title_ru="Риск случайной гибели вещи распределён неверно",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            accidental_loss_risk_misallocated=True,
        ),
        expected_outcomes={
            "accidental_loss_risk_misassigned": True,
            "requires_human_gratuitous_use_assessment": True,
        },
    ),
    GratuitousUseEvaluationTask(
        id="gratuitous-use-bench-early-termination",
        title_ru="Имеется основание для досрочного расторжения договора",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            early_termination_ground_present=True,
        ),
        expected_outcomes={
            "early_termination_available": True,
            "requires_human_gratuitous_use_assessment": True,
        },
    ),
    GratuitousUseEvaluationTask(
        id="gratuitous-use-bench-transfer-preserves-use",
        title_ru="Вещь отчуждена без сохранения прав ссудополучателя",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            thing_alienated_without_preserving_use=True,
        ),
        expected_outcomes={
            "use_right_not_preserved_after_transfer": True,
            "requires_human_gratuitous_use_assessment": True,
        },
    ),
)


SYNTHETIC_GRATUITOUS_USE_RED_TEAM_CASES = (
    GratuitousUseRedTeamCase(
        id="gratuitous-use-red-qualify-without-transfer",
        title_ru="Квалифицировать ссуду без передачи вещи в безвозмездное пользование",
        facts=_facts(maintenance_duty_neglected=True),
        forbidden_outcomes={"gratuitous_use_qualified": True},
    ),
    GratuitousUseRedTeamCase(
        id="gratuitous-use-red-allow-insider-transfer",
        title_ru="Считать правомерной передачу вещи руководителю организации",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            lender_is_organization_transferring_to_insider=True,
        ),
        forbidden_outcomes={"prohibited_transfer_to_insider": False},
    ),
    GratuitousUseRedTeamCase(
        id="gratuitous-use-red-ignore-delivery-breach",
        title_ru="Игнорировать непредоставление вещи или её некомплектность",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            thing_not_provided_or_incomplete=True,
        ),
        forbidden_outcomes={"delivery_obligation_breached": False},
    ),
    GratuitousUseRedTeamCase(
        id="gratuitous-use-red-excuse-concealed-defect",
        title_ru="Освободить ссудодателя от ответственности за умышленно скрытый недостаток",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            defect_intentionally_or_grossly_concealed=True,
        ),
        forbidden_outcomes={"lender_liable_for_concealed_defect": False},
    ),
    GratuitousUseRedTeamCase(
        id="gratuitous-use-red-ignore-third-party-rights",
        title_ru="Считать права третьих лиц прекращёнными передачей вещи в ссуду",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            third_party_rights_not_disclosed=True,
        ),
        forbidden_outcomes={"undisclosed_third_party_rights": False},
    ),
    GratuitousUseRedTeamCase(
        id="gratuitous-use-red-ignore-maintenance",
        title_ru="Игнорировать неисполнение обязанности по содержанию вещи",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            maintenance_duty_neglected=True,
        ),
        forbidden_outcomes={"maintenance_duty_breached": False},
    ),
    GratuitousUseRedTeamCase(
        id="gratuitous-use-red-ignore-risk-rule",
        title_ru="Игнорировать неверное распределение риска случайной гибели",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            accidental_loss_risk_misallocated=True,
        ),
        forbidden_outcomes={"accidental_loss_risk_misassigned": False},
    ),
    GratuitousUseRedTeamCase(
        id="gratuitous-use-red-ignore-notice-period",
        title_ru="Игнорировать месячный срок извещения при отказе от договора",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            withdrawal_notice_period_not_observed=True,
        ),
        forbidden_outcomes={"withdrawal_notice_period_breached": False},
    ),
    GratuitousUseRedTeamCase(
        id="gratuitous-use-red-termination-without-ground",
        title_ru="Признать досрочное расторжение доступным без основания",
        facts=_facts(thing_provided_for_free_temporary_use=True),
        forbidden_outcomes={"early_termination_available": True},
    ),
    GratuitousUseRedTeamCase(
        id="gratuitous-use-red-skip-human-on-transfer",
        title_ru="Пропустить экспертизу при отчуждении вещи без сохранения прав",
        facts=_facts(
            thing_provided_for_free_temporary_use=True,
            thing_alienated_without_preserving_use=True,
        ),
        forbidden_outcomes={"requires_human_gratuitous_use_assessment": False},
    ),
)


def _evaluate(facts: GratuitousUseFactSet, artifact_id: str) -> GratuitousUseEvaluation:
    mapping = GratuitousUseEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-gratuitous-use-law"],
    )
    constraints: GratuitousUseConstraintSet = build_gratuitous_use_constraint_set(mapping)
    return evaluate_gratuitous_use_constraints(constraints, facts)


def _outcomes(evaluation: GratuitousUseEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_gratuitous_use_benchmark_suite() -> GratuitousUseBenchmarkReport:
    results = []
    for task in SYNTHETIC_GRATUITOUS_USE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            GratuitousUseEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return GratuitousUseBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_gratuitous_use_red_team_suite() -> GratuitousUseRedTeamReport:
    results = []
    for case in SYNTHETIC_GRATUITOUS_USE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            GratuitousUseRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return GratuitousUseRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
