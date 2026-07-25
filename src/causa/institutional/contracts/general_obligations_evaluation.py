from pydantic import BaseModel, Field

from causa.institutional.contracts.general_obligations import (
    GeneralObligationsConstraintSet,
    GeneralObligationsEvaluation,
    GeneralObligationsEvidenceMappingResult,
    GeneralObligationsFactSet,
    build_general_obligations_constraint_set,
    evaluate_general_obligations_constraints,
)


class GeneralObligationsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: GeneralObligationsFactSet
    expected_outcomes: dict[str, bool]


class GeneralObligationsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GeneralObligationsBenchmarkReport(BaseModel):
    id: str = "general-obligations-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[GeneralObligationsEvaluationResult] = Field(default_factory=list)


class GeneralObligationsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: GeneralObligationsFactSet
    forbidden_outcomes: dict[str, bool]


class GeneralObligationsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GeneralObligationsRedTeamReport(BaseModel):
    id: str = "general-obligations-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[GeneralObligationsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> GeneralObligationsFactSet:
    values = {field_name: False for field_name in GeneralObligationsFactSet.model_fields}
    values.update(updates)
    return GeneralObligationsFactSet(**values)


SYNTHETIC_GENERAL_OBLIGATIONS_BENCHMARKS = (
    GeneralObligationsEvaluationTask(
        id="genobl-bench-established",
        title_ru="Обязательство установлено, добросовестность соблюдена",
        facts=_facts(obligation_established=True, good_faith_observed=True),
        expected_outcomes={
            "creditor_may_demand_performance": True,
            "good_faith_breach_flagged": False,
            "requires_human_general_obligations_assessment": False,
        },
    ),
    GeneralObligationsEvaluationTask(
        id="genobl-bench-good-faith-breach",
        title_ru="Нарушение добросовестности при исполнении обязательства",
        facts=_facts(obligation_established=True),
        expected_outcomes={
            "good_faith_breach_flagged": True,
            "requires_human_general_obligations_assessment": True,
        },
    ),
    GeneralObligationsEvaluationTask(
        id="genobl-bench-third-party",
        title_ru="Заявлено связывание лица, не участвующего в обязательстве",
        facts=_facts(
            obligation_established=True,
            good_faith_observed=True,
            obligation_binds_third_party_claimed=True,
        ),
        expected_outcomes={
            "third_party_binding_rejected": True,
            "requires_human_general_obligations_assessment": True,
        },
    ),
    GeneralObligationsEvaluationTask(
        id="genobl-bench-alternative-fixed",
        title_ru="Альтернативное обязательство определено выбором предмета",
        facts=_facts(
            obligation_established=True,
            good_faith_observed=True,
            alternative_obligation=True,
            choice_made_in_alternative=True,
        ),
        expected_outcomes={
            "alternative_obligation_fixed": True,
            "requires_human_general_obligations_assessment": False,
        },
    ),
    GeneralObligationsEvaluationTask(
        id="genobl-bench-alternative-open",
        title_ru="Альтернативное обязательство без сделанного выбора",
        facts=_facts(
            obligation_established=True,
            good_faith_observed=True,
            alternative_obligation=True,
        ),
        expected_outcomes={
            "alternative_obligation_fixed": False,
            "requires_human_general_obligations_assessment": True,
        },
    ),
    GeneralObligationsEvaluationTask(
        id="genobl-bench-facultative-substituted",
        title_ru="Факультативное обязательство с предоставленной заменой",
        facts=_facts(
            obligation_established=True,
            good_faith_observed=True,
            facultative_obligation=True,
            facultative_substitution_provided=True,
        ),
        expected_outcomes={
            "creditor_limited_to_principal": False,
            "requires_human_general_obligations_assessment": False,
        },
    ),
    GeneralObligationsEvaluationTask(
        id="genobl-bench-facultative-not-substituted",
        title_ru="Факультативное обязательство без предоставления замены",
        facts=_facts(
            obligation_established=True,
            good_faith_observed=True,
            facultative_obligation=True,
        ),
        expected_outcomes={
            "creditor_limited_to_principal": True,
            "requires_human_general_obligations_assessment": True,
        },
    ),
    GeneralObligationsEvaluationTask(
        id="genobl-bench-specific-performance",
        title_ru="Требование исполнения в натуре при возможном исполнении",
        facts=_facts(
            obligation_established=True,
            good_faith_observed=True,
            specific_performance_demanded=True,
        ),
        expected_outcomes={
            "specific_performance_available": True,
            "requires_human_general_obligations_assessment": False,
        },
    ),
    GeneralObligationsEvaluationTask(
        id="genobl-bench-specific-performance-personal",
        title_ru="Исполнение неразрывно связано с личностью должника",
        facts=_facts(
            obligation_established=True,
            good_faith_observed=True,
            specific_performance_demanded=True,
            performance_uniquely_personal=True,
        ),
        expected_outcomes={
            "specific_performance_available": False,
            "requires_human_general_obligations_assessment": True,
        },
    ),
    GeneralObligationsEvaluationTask(
        id="genobl-bench-astreinte",
        title_ru="Неисполнение судебного акта — судебная неустойка",
        facts=_facts(
            obligation_established=True,
            good_faith_observed=True,
            judicial_act_non_compliance=True,
        ),
        expected_outcomes={
            "astreinte_available": True,
            "requires_human_general_obligations_assessment": True,
        },
    ),
)


SYNTHETIC_GENERAL_OBLIGATIONS_RED_TEAM_CASES = (
    GeneralObligationsRedTeamCase(
        id="genobl-red-demand-without-obligation",
        title_ru="Признать право требовать исполнения без установленного обязательства",
        facts=_facts(good_faith_observed=True),
        forbidden_outcomes={"creditor_may_demand_performance": True},
    ),
    GeneralObligationsRedTeamCase(
        id="genobl-red-bind-third-party",
        title_ru="Не отклонять связывание лица, не участвующего в обязательстве",
        facts=_facts(
            obligation_established=True,
            obligation_binds_third_party_claimed=True,
        ),
        forbidden_outcomes={"third_party_binding_rejected": False},
    ),
    GeneralObligationsRedTeamCase(
        id="genobl-red-alt-fixed-without-choice",
        title_ru="Считать альтернативное обязательство определённым без выбора",
        facts=_facts(
            obligation_established=True,
            alternative_obligation=True,
        ),
        forbidden_outcomes={"alternative_obligation_fixed": True},
    ),
    GeneralObligationsRedTeamCase(
        id="genobl-red-limit-when-substituted",
        title_ru="Ограничивать кредитора основным при предоставленной замене",
        facts=_facts(
            obligation_established=True,
            facultative_obligation=True,
            facultative_substitution_provided=True,
        ),
        forbidden_outcomes={"creditor_limited_to_principal": True},
    ),
    GeneralObligationsRedTeamCase(
        id="genobl-red-specific-without-obligation",
        title_ru="Присуждать исполнение в натуре без установленного обязательства",
        facts=_facts(specific_performance_demanded=True),
        forbidden_outcomes={"specific_performance_available": True},
    ),
    GeneralObligationsRedTeamCase(
        id="genobl-red-specific-when-personal",
        title_ru="Присуждать натуру при неразрывной связи с личностью должника",
        facts=_facts(
            obligation_established=True,
            specific_performance_demanded=True,
            performance_uniquely_personal=True,
        ),
        forbidden_outcomes={"specific_performance_available": True},
    ),
    GeneralObligationsRedTeamCase(
        id="genobl-red-astreinte-without-noncompliance",
        title_ru="Присуждать судебную неустойку без неисполнения судебного акта",
        facts=_facts(obligation_established=True),
        forbidden_outcomes={"astreinte_available": True},
    ),
    GeneralObligationsRedTeamCase(
        id="genobl-red-skip-good-faith",
        title_ru="Игнорировать нарушение добросовестности",
        facts=_facts(obligation_established=True),
        forbidden_outcomes={"good_faith_breach_flagged": False},
    ),
    GeneralObligationsRedTeamCase(
        id="genobl-red-skip-human-on-third-party",
        title_ru="Пропустить экспертизу при заявлении о связывании третьего лица",
        facts=_facts(
            obligation_established=True,
            obligation_binds_third_party_claimed=True,
        ),
        forbidden_outcomes={"requires_human_general_obligations_assessment": False},
    ),
    GeneralObligationsRedTeamCase(
        id="genobl-red-skip-human-on-astreinte",
        title_ru="Пропустить экспертизу при судебной неустойке",
        facts=_facts(
            obligation_established=True,
            judicial_act_non_compliance=True,
        ),
        forbidden_outcomes={"requires_human_general_obligations_assessment": False},
    ),
)


def _evaluate(facts: GeneralObligationsFactSet, artifact_id: str) -> GeneralObligationsEvaluation:
    mapping = GeneralObligationsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-general-obligations-law"],
    )
    constraints: GeneralObligationsConstraintSet = build_general_obligations_constraint_set(mapping)
    return evaluate_general_obligations_constraints(constraints, facts)


def _outcomes(evaluation: GeneralObligationsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_general_obligations_benchmark_suite() -> GeneralObligationsBenchmarkReport:
    results = []
    for task in SYNTHETIC_GENERAL_OBLIGATIONS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            GeneralObligationsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return GeneralObligationsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_general_obligations_red_team_suite() -> GeneralObligationsRedTeamReport:
    results = []
    for case in SYNTHETIC_GENERAL_OBLIGATIONS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            GeneralObligationsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return GeneralObligationsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
