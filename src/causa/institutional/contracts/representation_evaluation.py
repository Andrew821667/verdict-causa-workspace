from pydantic import BaseModel, Field

from causa.institutional.contracts.representation import (
    RepresentationConstraintSet,
    RepresentationEvaluation,
    RepresentationEvidenceMappingResult,
    RepresentationFactSet,
    build_representation_constraint_set,
    evaluate_representation_constraints,
)


class RepresentationEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: RepresentationFactSet
    expected_outcomes: dict[str, bool]


class RepresentationEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class RepresentationBenchmarkReport(BaseModel):
    id: str = "representation-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[RepresentationEvaluationResult] = Field(default_factory=list)


class RepresentationRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: RepresentationFactSet
    forbidden_outcomes: dict[str, bool]


class RepresentationRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class RepresentationRedTeamReport(BaseModel):
    id: str = "representation-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[RepresentationRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> RepresentationFactSet:
    values = {field_name: False for field_name in RepresentationFactSet.model_fields}
    values.update(updates)
    return RepresentationFactSet(**values)


SYNTHETIC_REPRESENTATION_BENCHMARKS = (
    RepresentationEvaluationTask(
        id="representation-bench-not-qualified",
        title_ru="Отношения представительства не установлены",
        facts=_facts(power_of_attorney_form_breached=True),
        expected_outcomes={"representation_qualified": False},
    ),
    RepresentationEvaluationTask(
        id="representation-bench-qualified-clean",
        title_ru="Представительство без нарушений",
        facts=_facts(representation_relation_established=True),
        expected_outcomes={
            "representation_qualified": True,
            "requires_human_representation_assessment": False,
        },
    ),
    RepresentationEvaluationTask(
        id="representation-bench-authority-basis",
        title_ru="Основание полномочия представителя порочно",
        facts=_facts(
            representation_relation_established=True,
            authority_basis_invalid=True,
        ),
        expected_outcomes={
            "authority_basis_duty_breached": True,
            "requires_human_representation_assessment": True,
        },
    ),
    RepresentationEvaluationTask(
        id="representation-bench-self-dealing",
        title_ru="Представитель совершил сделку в отношении себя лично",
        facts=_facts(
            representation_relation_established=True,
            prohibited_self_dealing=True,
        ),
        expected_outcomes={
            "self_dealing_duty_breached": True,
            "requires_human_representation_assessment": True,
        },
    ),
    RepresentationEvaluationTask(
        id="representation-bench-commercial",
        title_ru="Нарушены правила о коммерческом представительстве",
        facts=_facts(
            representation_relation_established=True,
            commercial_representation_rules_breached=True,
        ),
        expected_outcomes={
            "commercial_representation_duty_breached": True,
            "requires_human_representation_assessment": True,
        },
    ),
    RepresentationEvaluationTask(
        id="representation-bench-poa-form",
        title_ru="Нарушены форма и удостоверение доверенности",
        facts=_facts(
            representation_relation_established=True,
            power_of_attorney_form_breached=True,
        ),
        expected_outcomes={
            "power_of_attorney_form_duty_breached": True,
            "requires_human_representation_assessment": True,
        },
    ),
    RepresentationEvaluationTask(
        id="representation-bench-poa-term",
        title_ru="Нарушены правила о сроке доверенности и дате её совершения",
        facts=_facts(
            representation_relation_established=True,
            power_of_attorney_term_breached=True,
        ),
        expected_outcomes={
            "power_of_attorney_term_duty_breached": True,
            "requires_human_representation_assessment": True,
        },
    ),
    RepresentationEvaluationTask(
        id="representation-bench-substitution",
        title_ru="Нарушены правила о передоверии",
        facts=_facts(
            representation_relation_established=True,
            substitution_rules_breached=True,
        ),
        expected_outcomes={
            "substitution_duty_breached": True,
            "requires_human_representation_assessment": True,
        },
    ),
    RepresentationEvaluationTask(
        id="representation-bench-termination",
        title_ru="Нарушены прекращение доверенности и извещение о нём",
        facts=_facts(
            representation_relation_established=True,
            termination_or_notice_breached=True,
        ),
        expected_outcomes={
            "termination_notice_duty_breached": True,
            "requires_human_representation_assessment": True,
        },
    ),
    RepresentationEvaluationTask(
        id="representation-bench-unauthorized-act",
        title_ru="Сделка совершена без полномочий и не одобрена представляемым",
        facts=_facts(
            representation_relation_established=True,
            unauthorized_act_without_ratification=True,
            ratification_effect_disregarded=True,
        ),
        expected_outcomes={
            "unauthorized_representation_detected": True,
            "ratification_effect_breached": True,
            "requires_human_representation_assessment": True,
        },
    ),
)


SYNTHETIC_REPRESENTATION_RED_TEAM_CASES = (
    RepresentationRedTeamCase(
        id="representation-red-qualify-without-relation",
        title_ru="Применить правила о представительстве без соответствующих отношений",
        facts=_facts(power_of_attorney_form_breached=True),
        forbidden_outcomes={"representation_qualified": True},
    ),
    RepresentationRedTeamCase(
        id="representation-red-ignore-authority-basis",
        title_ru="Признать полномочие при пороке его основания",
        facts=_facts(
            representation_relation_established=True,
            authority_basis_invalid=True,
        ),
        forbidden_outcomes={"authority_basis_duty_breached": False},
    ),
    RepresentationRedTeamCase(
        id="representation-red-allow-self-dealing",
        title_ru="Допустить сделку представителя в отношении себя лично",
        facts=_facts(
            representation_relation_established=True,
            prohibited_self_dealing=True,
        ),
        forbidden_outcomes={"self_dealing_duty_breached": False},
    ),
    RepresentationRedTeamCase(
        id="representation-red-ignore-commercial-rules",
        title_ru="Игнорировать одновременное представительство разных сторон без согласия",
        facts=_facts(
            representation_relation_established=True,
            commercial_representation_rules_breached=True,
        ),
        forbidden_outcomes={"commercial_representation_duty_breached": False},
    ),
    RepresentationRedTeamCase(
        id="representation-red-ignore-poa-form",
        title_ru="Признать действительной доверенность без нотариального удостоверения",
        facts=_facts(
            representation_relation_established=True,
            power_of_attorney_form_breached=True,
        ),
        forbidden_outcomes={"power_of_attorney_form_duty_breached": False},
    ),
    RepresentationRedTeamCase(
        id="representation-red-ignore-poa-term",
        title_ru="Признать действительной доверенность без даты её совершения",
        facts=_facts(
            representation_relation_established=True,
            power_of_attorney_term_breached=True,
        ),
        forbidden_outcomes={"power_of_attorney_term_duty_breached": False},
    ),
    RepresentationRedTeamCase(
        id="representation-red-ignore-substitution",
        title_ru="Допустить передоверие без уполномочия и без извещения",
        facts=_facts(
            representation_relation_established=True,
            substitution_rules_breached=True,
        ),
        forbidden_outcomes={"substitution_duty_breached": False},
    ),
    RepresentationRedTeamCase(
        id="representation-red-ignore-termination-notice",
        title_ru="Игнорировать необходимость извещения об отмене доверенности",
        facts=_facts(
            representation_relation_established=True,
            termination_or_notice_breached=True,
        ),
        forbidden_outcomes={"termination_notice_duty_breached": False},
    ),
    RepresentationRedTeamCase(
        id="representation-red-bind-principal-without-authority",
        title_ru="Связать представляемого сделкой неуполномоченного лица без одобрения",
        facts=_facts(
            representation_relation_established=True,
            unauthorized_act_without_ratification=True,
        ),
        forbidden_outcomes={"unauthorized_representation_detected": False},
    ),
    RepresentationRedTeamCase(
        id="representation-red-ratification-without-unauthorized-act",
        title_ru="Признать неучёт одобрения без сделки неуполномоченного лица",
        facts=_facts(representation_relation_established=True),
        forbidden_outcomes={"ratification_effect_breached": True},
    ),
)


def _evaluate(facts: RepresentationFactSet, artifact_id: str) -> RepresentationEvaluation:
    mapping = RepresentationEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-representation-law"],
    )
    constraints: RepresentationConstraintSet = build_representation_constraint_set(mapping)
    return evaluate_representation_constraints(constraints, facts)


def _outcomes(evaluation: RepresentationEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_representation_benchmark_suite() -> RepresentationBenchmarkReport:
    results = []
    for task in SYNTHETIC_REPRESENTATION_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            RepresentationEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return RepresentationBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_representation_red_team_suite() -> RepresentationRedTeamReport:
    results = []
    for case in SYNTHETIC_REPRESENTATION_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            RepresentationRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return RepresentationRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
