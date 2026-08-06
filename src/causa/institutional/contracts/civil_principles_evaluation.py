from pydantic import BaseModel, Field

from causa.institutional.contracts.civil_principles import (
    CivilPrinciplesConstraintSet,
    CivilPrinciplesEvaluation,
    CivilPrinciplesEvidenceMappingResult,
    CivilPrinciplesFactSet,
    build_civil_principles_constraint_set,
    evaluate_civil_principles_constraints,
)


class CivilPrinciplesEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: CivilPrinciplesFactSet
    expected_outcomes: dict[str, bool]


class CivilPrinciplesEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CivilPrinciplesBenchmarkReport(BaseModel):
    id: str = "civil-principles-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[CivilPrinciplesEvaluationResult] = Field(default_factory=list)


class CivilPrinciplesRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: CivilPrinciplesFactSet
    forbidden_outcomes: dict[str, bool]


class CivilPrinciplesRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CivilPrinciplesRedTeamReport(BaseModel):
    id: str = "civil-principles-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[CivilPrinciplesRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> CivilPrinciplesFactSet:
    values = {field_name: False for field_name in CivilPrinciplesFactSet.model_fields}
    values.update(updates)
    return CivilPrinciplesFactSet(**values)


SYNTHETIC_CIVIL_PRINCIPLES_BENCHMARKS = (
    CivilPrinciplesEvaluationTask(
        id="civil-principles-bench-not-qualified",
        title_ru="Осуществление или защита гражданского права не заявлены",
        facts=_facts(abuse_of_right_established=True),
        expected_outcomes={"civil_principles_qualified": False},
    ),
    CivilPrinciplesEvaluationTask(
        id="civil-principles-bench-qualified-clean",
        title_ru="Осуществление права без нарушения основных начал",
        facts=_facts(civil_rights_exercise_asserted=True),
        expected_outcomes={
            "civil_principles_qualified": True,
            "requires_human_civil_principles_assessment": False,
        },
    ),
    CivilPrinciplesEvaluationTask(
        id="civil-principles-bench-good-faith",
        title_ru="Нарушен принцип добросовестности участников оборота",
        facts=_facts(civil_rights_exercise_asserted=True, good_faith_principle_breached=True),
        expected_outcomes={
            "good_faith_duty_breached": True,
            "requires_human_civil_principles_assessment": True,
        },
    ),
    CivilPrinciplesEvaluationTask(
        id="civil-principles-bench-equality-freedom",
        title_ru="Нарушены равенство участников и свобода договора",
        facts=_facts(
            civil_rights_exercise_asserted=True, equality_or_freedom_principle_breached=True
        ),
        expected_outcomes={
            "equality_and_freedom_duty_breached": True,
            "requires_human_civil_principles_assessment": True,
        },
    ),
    CivilPrinciplesEvaluationTask(
        id="civil-principles-bench-rights-arising",
        title_ru="Основания возникновения гражданских прав определены неверно",
        facts=_facts(civil_rights_exercise_asserted=True, rights_arising_grounds_breached=True),
        expected_outcomes={
            "rights_arising_duty_breached": True,
            "requires_human_civil_principles_assessment": True,
        },
    ),
    CivilPrinciplesEvaluationTask(
        id="civil-principles-bench-protection-methods",
        title_ru="Способ защиты гражданского права избран с нарушением",
        facts=_facts(civil_rights_exercise_asserted=True, protection_methods_breached=True),
        expected_outcomes={
            "protection_methods_duty_breached": True,
            "requires_human_civil_principles_assessment": True,
        },
    ),
    CivilPrinciplesEvaluationTask(
        id="civil-principles-bench-self-help",
        title_ru="Самозащита несоразмерна нарушению",
        facts=_facts(civil_rights_exercise_asserted=True, self_help_limits_breached=True),
        expected_outcomes={
            "self_help_duty_breached": True,
            "requires_human_civil_principles_assessment": True,
        },
    ),
    CivilPrinciplesEvaluationTask(
        id="civil-principles-bench-damages",
        title_ru="Нарушены правила о полном возмещении убытков",
        facts=_facts(civil_rights_exercise_asserted=True, damages_compensation_rules_breached=True),
        expected_outcomes={
            "damages_compensation_duty_breached": True,
            "requires_human_civil_principles_assessment": True,
        },
    ),
    CivilPrinciplesEvaluationTask(
        id="civil-principles-bench-public-authority",
        title_ru="Нарушена ответственность публично-правового образования",
        facts=_facts(civil_rights_exercise_asserted=True, public_authority_liability_breached=True),
        expected_outcomes={
            "public_authority_liability_duty_breached": True,
            "requires_human_civil_principles_assessment": True,
        },
    ),
    CivilPrinciplesEvaluationTask(
        id="civil-principles-bench-abuse-of-right",
        title_ru="Установлено злоупотребление правом, отказ в защите не применён",
        facts=_facts(
            civil_rights_exercise_asserted=True,
            abuse_of_right_established=True,
            protection_refusal_not_applied=True,
        ),
        expected_outcomes={
            "abuse_of_right_detected": True,
            "protection_refusal_breached": True,
            "requires_human_civil_principles_assessment": True,
        },
    ),
)


SYNTHETIC_CIVIL_PRINCIPLES_RED_TEAM_CASES = (
    CivilPrinciplesRedTeamCase(
        id="civil-principles-red-qualify-without-exercise",
        title_ru="Применить основные начала без заявленного осуществления права",
        facts=_facts(abuse_of_right_established=True),
        forbidden_outcomes={"civil_principles_qualified": True},
    ),
    CivilPrinciplesRedTeamCase(
        id="civil-principles-red-ignore-good-faith",
        title_ru="Позволить извлечь преимущество из недобросовестного поведения",
        facts=_facts(civil_rights_exercise_asserted=True, good_faith_principle_breached=True),
        forbidden_outcomes={"good_faith_duty_breached": False},
    ),
    CivilPrinciplesRedTeamCase(
        id="civil-principles-red-ignore-equality",
        title_ru="Игнорировать произвольное вмешательство в частные дела",
        facts=_facts(
            civil_rights_exercise_asserted=True, equality_or_freedom_principle_breached=True
        ),
        forbidden_outcomes={"equality_and_freedom_duty_breached": False},
    ),
    CivilPrinciplesRedTeamCase(
        id="civil-principles-red-ignore-rights-arising",
        title_ru="Признать право возникшим без предусмотренного законом основания",
        facts=_facts(civil_rights_exercise_asserted=True, rights_arising_grounds_breached=True),
        forbidden_outcomes={"rights_arising_duty_breached": False},
    ),
    CivilPrinciplesRedTeamCase(
        id="civil-principles-red-ignore-abuse",
        title_ru="Признать правомерным осуществление права с намерением причинить вред",
        facts=_facts(civil_rights_exercise_asserted=True, abuse_of_right_established=True),
        forbidden_outcomes={"abuse_of_right_detected": False},
    ),
    CivilPrinciplesRedTeamCase(
        id="civil-principles-red-refusal-without-abuse",
        title_ru="Признать неприменение отказа в защите без злоупотребления правом",
        facts=_facts(civil_rights_exercise_asserted=True),
        forbidden_outcomes={"protection_refusal_breached": True},
    ),
    CivilPrinciplesRedTeamCase(
        id="civil-principles-red-ignore-protection-methods",
        title_ru="Допустить способ защиты, не предусмотренный законом",
        facts=_facts(civil_rights_exercise_asserted=True, protection_methods_breached=True),
        forbidden_outcomes={"protection_methods_duty_breached": False},
    ),
    CivilPrinciplesRedTeamCase(
        id="civil-principles-red-ignore-self-help-limits",
        title_ru="Допустить самозащиту, выходящую за пределы необходимого",
        facts=_facts(civil_rights_exercise_asserted=True, self_help_limits_breached=True),
        forbidden_outcomes={"self_help_duty_breached": False},
    ),
    CivilPrinciplesRedTeamCase(
        id="civil-principles-red-ignore-damages",
        title_ru="Ограничить возмещение убытков вопреки закону и договору",
        facts=_facts(civil_rights_exercise_asserted=True, damages_compensation_rules_breached=True),
        forbidden_outcomes={"damages_compensation_duty_breached": False},
    ),
    CivilPrinciplesRedTeamCase(
        id="civil-principles-red-skip-human-on-public-authority",
        title_ru="Пропустить экспертизу при убытках от действий органов власти",
        facts=_facts(civil_rights_exercise_asserted=True, public_authority_liability_breached=True),
        forbidden_outcomes={"requires_human_civil_principles_assessment": False},
    ),
)


def _evaluate(facts: CivilPrinciplesFactSet, artifact_id: str) -> CivilPrinciplesEvaluation:
    mapping = CivilPrinciplesEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-civil-principles-law"],
    )
    constraints: CivilPrinciplesConstraintSet = build_civil_principles_constraint_set(mapping)
    return evaluate_civil_principles_constraints(constraints, facts)


def _outcomes(evaluation: CivilPrinciplesEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_civil_principles_benchmark_suite() -> CivilPrinciplesBenchmarkReport:
    results = []
    for task in SYNTHETIC_CIVIL_PRINCIPLES_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            CivilPrinciplesEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return CivilPrinciplesBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_civil_principles_red_team_suite() -> CivilPrinciplesRedTeamReport:
    results = []
    for case in SYNTHETIC_CIVIL_PRINCIPLES_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            CivilPrinciplesRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return CivilPrinciplesRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
