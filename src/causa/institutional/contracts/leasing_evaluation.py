from pydantic import BaseModel, Field

from causa.institutional.contracts.leasing import (
    LeasingConstraintSet,
    LeasingEvaluation,
    LeasingEvidenceMappingResult,
    LeasingFactSet,
    build_leasing_constraint_set,
    evaluate_leasing_constraints,
)


class LeasingEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: LeasingFactSet
    expected_outcomes: dict[str, bool]


class LeasingEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class LeasingBenchmarkReport(BaseModel):
    id: str = "leasing-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[LeasingEvaluationResult] = Field(default_factory=list)


class LeasingRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: LeasingFactSet
    forbidden_outcomes: dict[str, bool]


class LeasingRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class LeasingRedTeamReport(BaseModel):
    id: str = "leasing-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[LeasingRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> LeasingFactSet:
    values = {field_name: False for field_name in LeasingFactSet.model_fields}
    values.update(updates)
    return LeasingFactSet(**values)


SYNTHETIC_LEASING_BENCHMARKS = (
    LeasingEvaluationTask(
        id="leasing-bench-not-qualified",
        title_ru="Отношения без приобретения имущества для арендатора",
        facts=_facts(seller_not_notified_of_leasing_purpose=True),
        expected_outcomes={"leasing_qualified": False},
    ),
    LeasingEvaluationTask(
        id="leasing-bench-qualified-clean",
        title_ru="Финансовая аренда непотребляемой вещи без нарушений",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            leased_object_is_non_consumable_thing=True,
        ),
        expected_outcomes={
            "leasing_qualified": True,
            "requires_human_leasing_assessment": False,
        },
    ),
    LeasingEvaluationTask(
        id="leasing-bench-object-excluded",
        title_ru="Предметом лизинга заявлен земельный участок или природный объект",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            object_excluded_from_leasing=True,
        ),
        expected_outcomes={
            "object_not_eligible_for_leasing": True,
            "requires_human_leasing_assessment": True,
        },
    ),
    LeasingEvaluationTask(
        id="leasing-bench-seller-not-notified",
        title_ru="Продавец не уведомлён о лизинговом назначении имущества",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            seller_not_notified_of_leasing_purpose=True,
        ),
        expected_outcomes={
            "seller_notice_not_given": True,
            "requires_human_leasing_assessment": True,
        },
    ),
    LeasingEvaluationTask(
        id="leasing-bench-delivery-default",
        title_ru="Предмет лизинга не передан в срок по вине лизингодателя",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            object_not_delivered_in_time=True,
            delay_attributable_to_lessor=True,
        ),
        expected_outcomes={
            "delivery_default_attributable_to_lessor": True,
            "requires_human_leasing_assessment": True,
        },
    ),
    LeasingEvaluationTask(
        id="leasing-bench-delay-not-attributable",
        title_ru="Просрочка передачи без обстоятельств, за которые отвечает лизингодатель",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            object_not_delivered_in_time=True,
        ),
        expected_outcomes={
            "delivery_default_attributable_to_lessor": False,
            "requires_human_leasing_assessment": False,
        },
    ),
    LeasingEvaluationTask(
        id="leasing-bench-risk-transfer",
        title_ru="Спор о распределении риска случайной гибели до передачи",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            risk_allocation_disputed_before_transfer=True,
        ),
        expected_outcomes={
            "risk_transfer_rule_applies": True,
            "requires_human_leasing_assessment": True,
        },
    ),
    LeasingEvaluationTask(
        id="leasing-bench-direct-claim-denied",
        title_ru="Арендатору отказано в прямом требовании к продавцу",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            lessee_denied_direct_claim_against_seller=True,
        ),
        expected_outcomes={
            "lessee_direct_claim_wrongly_denied": True,
            "requires_human_leasing_assessment": True,
        },
    ),
    LeasingEvaluationTask(
        id="leasing-bench-lessor-selected-seller",
        title_ru="Продавца выбрал лизингодатель, продавец нарушил обязательства",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            lessor_selected_seller=True,
            seller_breached_obligations=True,
        ),
        expected_outcomes={
            "lessor_solidarily_liable_for_seller": True,
            "requires_human_leasing_assessment": True,
        },
    ),
    LeasingEvaluationTask(
        id="leasing-bench-lessee-selected-seller",
        title_ru="Продавца выбрал арендатор: солидарной ответственности лизингодателя нет",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            seller_breached_obligations=True,
        ),
        expected_outcomes={
            "lessor_solidarily_liable_for_seller": False,
            "requires_human_leasing_assessment": False,
        },
    ),
)


SYNTHETIC_LEASING_RED_TEAM_CASES = (
    LeasingRedTeamCase(
        id="leasing-red-qualify-without-acquisition",
        title_ru="Квалифицировать лизинг без приобретения имущества для арендатора",
        facts=_facts(seller_not_notified_of_leasing_purpose=True),
        forbidden_outcomes={"leasing_qualified": True},
    ),
    LeasingRedTeamCase(
        id="leasing-red-allow-excluded-object",
        title_ru="Допустить земельный участок в качестве предмета лизинга",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            object_excluded_from_leasing=True,
        ),
        forbidden_outcomes={"object_not_eligible_for_leasing": False},
    ),
    LeasingRedTeamCase(
        id="leasing-red-ignore-seller-notice",
        title_ru="Игнорировать отсутствие уведомления продавца о лизинге",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            seller_not_notified_of_leasing_purpose=True,
        ),
        forbidden_outcomes={"seller_notice_not_given": False},
    ),
    LeasingRedTeamCase(
        id="leasing-red-ignore-delivery-default",
        title_ru="Игнорировать непередачу предмета лизинга по вине лизингодателя",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            object_not_delivered_in_time=True,
            delay_attributable_to_lessor=True,
        ),
        forbidden_outcomes={"delivery_default_attributable_to_lessor": False},
    ),
    LeasingRedTeamCase(
        id="leasing-red-blame-lessor-without-attribution",
        title_ru="Возложить ответственность на лизингодателя без его вины в просрочке",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            object_not_delivered_in_time=True,
        ),
        forbidden_outcomes={"delivery_default_attributable_to_lessor": True},
    ),
    LeasingRedTeamCase(
        id="leasing-red-ignore-risk-rule",
        title_ru="Игнорировать правило о переходе риска в момент передачи",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            risk_allocation_disputed_before_transfer=True,
        ),
        forbidden_outcomes={"risk_transfer_rule_applies": False},
    ),
    LeasingRedTeamCase(
        id="leasing-red-deny-direct-claim",
        title_ru="Отказать арендатору в прямом требовании к продавцу",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            lessee_denied_direct_claim_against_seller=True,
        ),
        forbidden_outcomes={"lessee_direct_claim_wrongly_denied": False},
    ),
    LeasingRedTeamCase(
        id="leasing-red-deny-solidary-liability",
        title_ru="Отрицать солидарную ответственность при выборе продавца лизингодателем",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            lessor_selected_seller=True,
            seller_breached_obligations=True,
        ),
        forbidden_outcomes={"lessor_solidarily_liable_for_seller": False},
    ),
    LeasingRedTeamCase(
        id="leasing-red-solidary-without-lessor-selection",
        title_ru="Признать солидарную ответственность при выборе продавца арендатором",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            seller_breached_obligations=True,
        ),
        forbidden_outcomes={"lessor_solidarily_liable_for_seller": True},
    ),
    LeasingRedTeamCase(
        id="leasing-red-skip-human-on-excluded-object",
        title_ru="Пропустить экспертизу при недопустимом предмете лизинга",
        facts=_facts(
            property_acquired_for_lessee_and_leased=True,
            object_excluded_from_leasing=True,
        ),
        forbidden_outcomes={"requires_human_leasing_assessment": False},
    ),
)


def _evaluate(facts: LeasingFactSet, artifact_id: str) -> LeasingEvaluation:
    mapping = LeasingEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-leasing-law"],
    )
    constraints: LeasingConstraintSet = build_leasing_constraint_set(mapping)
    return evaluate_leasing_constraints(constraints, facts)


def _outcomes(evaluation: LeasingEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_leasing_benchmark_suite() -> LeasingBenchmarkReport:
    results = []
    for task in SYNTHETIC_LEASING_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            LeasingEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return LeasingBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_leasing_red_team_suite() -> LeasingRedTeamReport:
    results = []
    for case in SYNTHETIC_LEASING_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            LeasingRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return LeasingRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
