from pydantic import BaseModel, Field

from causa.institutional.contracts.gift import (
    GiftConstraintSet,
    GiftEvaluation,
    GiftEvidenceMappingResult,
    GiftFactSet,
    build_gift_constraint_set,
    evaluate_gift_constraints,
)


class GiftEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: GiftFactSet
    expected_outcomes: dict[str, bool]


class GiftEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GiftBenchmarkReport(BaseModel):
    id: str = "gift-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[GiftEvaluationResult] = Field(default_factory=list)


class GiftRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: GiftFactSet
    forbidden_outcomes: dict[str, bool]


class GiftRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GiftRedTeamReport(BaseModel):
    id: str = "gift-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[GiftRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> GiftFactSet:
    values = {field_name: False for field_name in GiftFactSet.model_fields}
    values.update(updates)
    return GiftFactSet(**values)


SYNTHETIC_GIFT_BENCHMARKS = (
    GiftEvaluationTask(
        id="gift-bench-qualified",
        title_ru="Безвозмездная передача вещи в собственность без встречного предоставления",
        facts=_facts(gratuitous_transfer_or_promise=True),
        expected_outcomes={
            "gift_qualified": True,
            "requires_human_gift_assessment": False,
        },
    ),
    GiftEvaluationTask(
        id="gift-bench-sham",
        title_ru="Наличие встречного обязательства — притворная сделка",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            counter_obligation_present=True,
        ),
        expected_outcomes={
            "sham_due_to_counter_obligation": True,
            "gift_qualified": False,
            "requires_human_gift_assessment": True,
        },
    ),
    GiftEvaluationTask(
        id="gift-bench-form-defect",
        title_ru="Требуется письменная форма, но она не соблюдена",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            written_form_required=True,
        ),
        expected_outcomes={
            "form_defect_makes_void": True,
            "requires_human_gift_assessment": True,
        },
    ),
    GiftEvaluationTask(
        id="gift-bench-form-satisfied",
        title_ru="Требуемая письменная форма соблюдена",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            written_form_required=True,
            written_form_satisfied=True,
        ),
        expected_outcomes={
            "form_defect_makes_void": False,
            "requires_human_gift_assessment": False,
        },
    ),
    GiftEvaluationTask(
        id="gift-bench-prohibited",
        title_ru="Дарение подпадает под запрет статьи 575",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            donation_statutorily_prohibited=True,
        ),
        expected_outcomes={
            "donation_prohibited": True,
            "requires_human_gift_assessment": True,
        },
    ),
    GiftEvaluationTask(
        id="gift-bench-ordinary-small-gift",
        title_ru="Обычный подарок небольшой стоимости — запрет не применяется",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            donation_statutorily_prohibited=True,
            ordinary_low_value_gift=True,
        ),
        expected_outcomes={
            "donation_prohibited": False,
            "requires_human_gift_assessment": False,
        },
    ),
    GiftEvaluationTask(
        id="gift-bench-restriction-violated",
        title_ru="Не получено необходимое согласие при ограничении дарения",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            restriction_consent_missing=True,
        ),
        expected_outcomes={
            "restriction_violated": True,
            "requires_human_gift_assessment": True,
        },
    ),
    GiftEvaluationTask(
        id="gift-bench-donee-refusal",
        title_ru="Одаряемый отказался от дара до передачи",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            donee_refused_before_delivery=True,
        ),
        expected_outcomes={
            "donee_refusal_terminates": True,
            "requires_human_gift_assessment": False,
        },
    ),
    GiftEvaluationTask(
        id="gift-bench-revocation",
        title_ru="Имеется основание для отмены дарения",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            donor_revocation_ground_present=True,
        ),
        expected_outcomes={
            "revocation_available": True,
            "requires_human_gift_assessment": True,
        },
    ),
    GiftEvaluationTask(
        id="gift-bench-charitable-revocation",
        title_ru="Пожертвование использовано не по назначению",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            charitable_donation_purpose_violated=True,
        ),
        expected_outcomes={
            "charitable_revocation_available": True,
            "requires_human_gift_assessment": True,
        },
    ),
)


SYNTHETIC_GIFT_RED_TEAM_CASES = (
    GiftRedTeamCase(
        id="gift-red-qualify-with-counter-obligation",
        title_ru="Квалифицировать дарение при встречном обязательстве",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            counter_obligation_present=True,
        ),
        forbidden_outcomes={"gift_qualified": True},
    ),
    GiftRedTeamCase(
        id="gift-red-deny-sham-with-counter-obligation",
        title_ru="Отрицать притворность при встречном обязательстве",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            counter_obligation_present=True,
        ),
        forbidden_outcomes={"sham_due_to_counter_obligation": False},
    ),
    GiftRedTeamCase(
        id="gift-red-ignore-form-defect",
        title_ru="Игнорировать ничтожность при несоблюдении требуемой формы",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            written_form_required=True,
        ),
        forbidden_outcomes={"form_defect_makes_void": False},
    ),
    GiftRedTeamCase(
        id="gift-red-form-defect-when-satisfied",
        title_ru="Считать форму нарушенной при её соблюдении",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            written_form_required=True,
            written_form_satisfied=True,
        ),
        forbidden_outcomes={"form_defect_makes_void": True},
    ),
    GiftRedTeamCase(
        id="gift-red-prohibit-ordinary-small-gift",
        title_ru="Запрещать обычный подарок небольшой стоимости",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            donation_statutorily_prohibited=True,
            ordinary_low_value_gift=True,
        ),
        forbidden_outcomes={"donation_prohibited": True},
    ),
    GiftRedTeamCase(
        id="gift-red-skip-prohibition",
        title_ru="Пропустить запрет дарения по статье 575",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            donation_statutorily_prohibited=True,
        ),
        forbidden_outcomes={"donation_prohibited": False},
    ),
    GiftRedTeamCase(
        id="gift-red-ignore-restriction-violation",
        title_ru="Игнорировать нарушение ограничения дарения",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            restriction_consent_missing=True,
        ),
        forbidden_outcomes={"restriction_violated": False},
    ),
    GiftRedTeamCase(
        id="gift-red-revocation-for-ordinary-gift",
        title_ru="Признавать отмену для обычного подарка небольшой стоимости",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            donor_revocation_ground_present=True,
            ordinary_low_value_gift=True,
        ),
        forbidden_outcomes={"revocation_available": True},
    ),
    GiftRedTeamCase(
        id="gift-red-charitable-revocation-without-violation",
        title_ru="Признавать отмену пожертвования без нарушения назначения",
        facts=_facts(gratuitous_transfer_or_promise=True),
        forbidden_outcomes={"charitable_revocation_available": True},
    ),
    GiftRedTeamCase(
        id="gift-red-skip-human-on-revocation",
        title_ru="Пропустить экспертизу при наличии основания отмены дарения",
        facts=_facts(
            gratuitous_transfer_or_promise=True,
            donor_revocation_ground_present=True,
        ),
        forbidden_outcomes={"requires_human_gift_assessment": False},
    ),
)


def _evaluate(facts: GiftFactSet, artifact_id: str) -> GiftEvaluation:
    mapping = GiftEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-gift-law"],
    )
    constraints: GiftConstraintSet = build_gift_constraint_set(mapping)
    return evaluate_gift_constraints(constraints, facts)


def _outcomes(evaluation: GiftEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_gift_benchmark_suite() -> GiftBenchmarkReport:
    results = []
    for task in SYNTHETIC_GIFT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            GiftEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return GiftBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_gift_red_team_suite() -> GiftRedTeamReport:
    results = []
    for case in SYNTHETIC_GIFT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            GiftRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return GiftRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
