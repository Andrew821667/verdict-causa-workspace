from pydantic import BaseModel, Field

from causa.institutional.contracts.temporal_effect import (
    TemporalEffectConstraintSet,
    TemporalEffectEvaluation,
    TemporalEffectEvidenceMappingResult,
    TemporalEffectFactSet,
    build_temporal_effect_constraint_set,
    evaluate_temporal_effect_constraints,
)


class TemporalEffectEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: TemporalEffectFactSet
    expected_outcomes: dict[str, bool]


class TemporalEffectEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TemporalEffectBenchmarkReport(BaseModel):
    id: str = "temporal-effect-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[TemporalEffectEvaluationResult] = Field(default_factory=list)


class TemporalEffectRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: TemporalEffectFactSet
    forbidden_outcomes: dict[str, bool]


class TemporalEffectRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TemporalEffectRedTeamReport(BaseModel):
    id: str = "temporal-effect-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[TemporalEffectRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> TemporalEffectFactSet:
    values = {field_name: False for field_name in TemporalEffectFactSet.model_fields}
    # По умолчанию — консенсуальный договор с полученным акцептом (статья 433 ГК РФ).
    values.update(acceptance_received_by_offeror=True)
    values.update(updates)
    return TemporalEffectFactSet(**values)


SYNTHETIC_TEMPORAL_EFFECT_BENCHMARKS = (
    TemporalEffectEvaluationTask(
        id="temporal-effect-bench-consensual",
        title_ru="Консенсуальный договор заключен и вступил в силу",
        facts=_facts(),
        expected_outcomes={
            "conclusion_moment_established": True,
            "contract_in_force": True,
        },
    ),
    TemporalEffectEvaluationTask(
        id="temporal-effect-bench-real-delivered",
        title_ru="Реальный договор с состоявшейся передачей имущества",
        facts=_facts(contract_requires_property_delivery=True, property_delivered=True),
        expected_outcomes={
            "conclusion_moment_established": True,
            "contract_in_force": True,
        },
    ),
    TemporalEffectEvaluationTask(
        id="temporal-effect-bench-real-not-delivered",
        title_ru="Реальный договор без передачи имущества",
        facts=_facts(contract_requires_property_delivery=True),
        expected_outcomes={
            "conclusion_moment_established": False,
            "contract_in_force": False,
        },
    ),
    TemporalEffectEvaluationTask(
        id="temporal-effect-bench-registered",
        title_ru="Регистрируемый договор с завершенной регистрацией",
        facts=_facts(contract_requires_state_registration=True, state_registration_completed=True),
        expected_outcomes={
            "conclusion_moment_established": True,
            "registration_pending": False,
        },
    ),
    TemporalEffectEvaluationTask(
        id="temporal-effect-bench-registration-pending",
        title_ru="Регистрируемый договор без регистрации",
        facts=_facts(contract_requires_state_registration=True),
        expected_outcomes={
            "conclusion_moment_established": False,
            "registration_pending": True,
            "requires_human_temporal_effect_assessment": True,
        },
    ),
    TemporalEffectEvaluationTask(
        id="temporal-effect-bench-deferred-met",
        title_ru="Отложенное вступление в силу при наступившем условии",
        facts=_facts(
            effectiveness_deferred_by_terms=True, deferred_effectiveness_condition_met=True
        ),
        expected_outcomes={"contract_in_force": True, "deferred_effect_pending": False},
    ),
    TemporalEffectEvaluationTask(
        id="temporal-effect-bench-deferred-pending",
        title_ru="Отложенное вступление в силу без наступления условия",
        facts=_facts(effectiveness_deferred_by_terms=True),
        expected_outcomes={
            "contract_in_force": False,
            "deferred_effect_pending": True,
        },
    ),
    TemporalEffectEvaluationTask(
        id="temporal-effect-bench-retroactive",
        title_ru="Распространение условий на отношения до заключения",
        facts=_facts(retroactive_application_agreed=True, prior_relations_exist=True),
        expected_outcomes={"retroactive_effect_applies": True},
    ),
    TemporalEffectEvaluationTask(
        id="temporal-effect-bench-term-discharge",
        title_ru="Истечение срока прекращает неисполненные обязательства",
        facts=_facts(
            term_end_defined=True,
            term_end_reached=True,
            terms_provide_obligations_end_on_term=True,
        ),
        expected_outcomes={
            "term_expired": True,
            "future_obligations_discharged_by_term_end": True,
        },
    ),
    TemporalEffectEvaluationTask(
        id="temporal-effect-bench-liability-survives",
        title_ru="Ответственность за нарушение сохраняется после истечения срока",
        facts=_facts(
            term_end_defined=True,
            term_end_reached=True,
            breach_committed_during_term=True,
        ),
        expected_outcomes={
            "term_expired": True,
            "liability_preserved_after_term": True,
        },
    ),
)


SYNTHETIC_TEMPORAL_EFFECT_RED_TEAM_CASES = (
    TemporalEffectRedTeamCase(
        id="temporal-effect-red-real-no-delivery",
        title_ru="Признать реальный договор заключенным без передачи",
        facts=_facts(contract_requires_property_delivery=True),
        forbidden_outcomes={"conclusion_moment_established": True},
    ),
    TemporalEffectRedTeamCase(
        id="temporal-effect-red-no-registration",
        title_ru="Признать регистрируемый договор заключенным без регистрации",
        facts=_facts(contract_requires_state_registration=True),
        forbidden_outcomes={"conclusion_moment_established": True},
    ),
    TemporalEffectRedTeamCase(
        id="temporal-effect-red-deferred",
        title_ru="Считать договор действующим при ненаступившем отлагательном условии",
        facts=_facts(effectiveness_deferred_by_terms=True),
        forbidden_outcomes={"contract_in_force": True},
    ),
    TemporalEffectRedTeamCase(
        id="temporal-effect-red-retroactive-no-prior",
        title_ru="Применить обратное действие без предшествующих отношений",
        facts=_facts(retroactive_application_agreed=True),
        forbidden_outcomes={"retroactive_effect_applies": True},
    ),
    TemporalEffectRedTeamCase(
        id="temporal-effect-red-discharge-not-provided",
        title_ru="Прекратить обязательства окончанием срока без такого условия",
        facts=_facts(term_end_defined=True, term_end_reached=True),
        forbidden_outcomes={"future_obligations_discharged_by_term_end": True},
    ),
    TemporalEffectRedTeamCase(
        id="temporal-effect-red-discharge-term-not-expired",
        title_ru="Прекратить обязательства при неистекшем сроке",
        facts=_facts(term_end_defined=True, terms_provide_obligations_end_on_term=True),
        forbidden_outcomes={"future_obligations_discharged_by_term_end": True},
    ),
    TemporalEffectRedTeamCase(
        id="temporal-effect-red-liability-waived",
        title_ru="Освободить от ответственности за нарушение после истечения срока",
        facts=_facts(
            term_end_defined=True,
            term_end_reached=True,
            breach_committed_during_term=True,
        ),
        forbidden_outcomes={"liability_preserved_after_term": False},
    ),
    TemporalEffectRedTeamCase(
        id="temporal-effect-red-no-acceptance",
        title_ru="Признать договор заключенным без получения акцепта",
        facts=_facts(acceptance_received_by_offeror=False),
        forbidden_outcomes={"conclusion_moment_established": True},
    ),
    TemporalEffectRedTeamCase(
        id="temporal-effect-red-term-without-end",
        title_ru="Признать срок истекшим без определенного момента окончания",
        facts=_facts(terms_provide_obligations_end_on_term=True),
        forbidden_outcomes={"term_expired": True},
    ),
    TemporalEffectRedTeamCase(
        id="temporal-effect-red-registration-gap",
        title_ru="Пропустить незавершенную государственную регистрацию",
        facts=_facts(contract_requires_state_registration=True),
        forbidden_outcomes={"registration_pending": False},
    ),
)


def _evaluate(facts: TemporalEffectFactSet, artifact_id: str) -> TemporalEffectEvaluation:
    mapping = TemporalEffectEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-temporal-effect-law"],
    )
    constraints: TemporalEffectConstraintSet = build_temporal_effect_constraint_set(mapping)
    return evaluate_temporal_effect_constraints(constraints, facts)


def _outcomes(evaluation: TemporalEffectEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_temporal_effect_benchmark_suite() -> TemporalEffectBenchmarkReport:
    results = []
    for task in SYNTHETIC_TEMPORAL_EFFECT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            TemporalEffectEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return TemporalEffectBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_temporal_effect_red_team_suite() -> TemporalEffectRedTeamReport:
    results = []
    for case in SYNTHETIC_TEMPORAL_EFFECT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            TemporalEffectRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return TemporalEffectRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
