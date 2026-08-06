from pydantic import BaseModel, Field

from causa.institutional.contracts.persons import (
    PersonsConstraintSet,
    PersonsEvaluation,
    PersonsEvidenceMappingResult,
    PersonsFactSet,
    build_persons_constraint_set,
    evaluate_persons_constraints,
)


class PersonsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: PersonsFactSet
    expected_outcomes: dict[str, bool]


class PersonsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PersonsBenchmarkReport(BaseModel):
    id: str = "persons-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[PersonsEvaluationResult] = Field(default_factory=list)


class PersonsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: PersonsFactSet
    forbidden_outcomes: dict[str, bool]


class PersonsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PersonsRedTeamReport(BaseModel):
    id: str = "persons-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[PersonsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> PersonsFactSet:
    values = {field_name: False for field_name in PersonsFactSet.model_fields}
    values.update(updates)
    return PersonsFactSet(**values)


SYNTHETIC_PERSONS_BENCHMARKS = (
    PersonsEvaluationTask(
        id="persons-bench-not-qualified",
        title_ru="Вопрос о правоспособности и дееспособности не заявлен",
        facts=_facts(entity_body_authority_breached=True),
        expected_outcomes={"persons_qualified": False},
    ),
    PersonsEvaluationTask(
        id="persons-bench-qualified-clean",
        title_ru="Правоспособность и дееспособность сторон не опорочены",
        facts=_facts(party_capacity_asserted=True),
        expected_outcomes={
            "persons_qualified": True,
            "requires_human_persons_assessment": False,
        },
    ),
    PersonsEvaluationTask(
        id="persons-bench-legal-capacity",
        title_ru="Нарушены правила о правоспособности гражданина",
        facts=_facts(party_capacity_asserted=True, legal_capacity_rules_breached=True),
        expected_outcomes={
            "legal_capacity_duty_breached": True,
            "requires_human_persons_assessment": True,
        },
    ),
    PersonsEvaluationTask(
        id="persons-bench-age-capacity",
        title_ru="Нарушены правила о дееспособности несовершеннолетнего",
        facts=_facts(party_capacity_asserted=True, active_capacity_age_rules_breached=True),
        expected_outcomes={
            "active_capacity_age_duty_breached": True,
            "requires_human_persons_assessment": True,
        },
    ),
    PersonsEvaluationTask(
        id="persons-bench-incapacity",
        title_ru="Сторона признана судом недееспособной",
        facts=_facts(party_capacity_asserted=True, incapacity_declared_by_court=True),
        expected_outcomes={
            "party_lacks_capacity": True,
            "requires_human_persons_assessment": True,
        },
    ),
    PersonsEvaluationTask(
        id="persons-bench-limited-capacity-without-consent",
        title_ru="Ограниченно дееспособный совершил сделку без согласия попечителя",
        facts=_facts(
            party_capacity_asserted=True,
            limited_capacity_rules_breached=True,
            guardianship_consent_missing=True,
        ),
        expected_outcomes={
            "limited_capacity_duty_breached": True,
            "guardianship_consent_duty_breached": True,
            "requires_human_persons_assessment": True,
        },
    ),
    PersonsEvaluationTask(
        id="persons-bench-capacity-restriction",
        title_ru="Сделка направлена на ограничение правоспособности или дееспособности",
        facts=_facts(party_capacity_asserted=True, capacity_restriction_by_agreement=True),
        expected_outcomes={
            "capacity_restriction_duty_breached": True,
            "requires_human_persons_assessment": True,
        },
    ),
    PersonsEvaluationTask(
        id="persons-bench-entity-scope",
        title_ru="Нарушены пределы правоспособности юридического лица и требования лицензии",
        facts=_facts(party_capacity_asserted=True, entity_capacity_scope_breached=True),
        expected_outcomes={
            "entity_capacity_scope_duty_breached": True,
            "requires_human_persons_assessment": True,
        },
    ),
    PersonsEvaluationTask(
        id="persons-bench-entity-registration",
        title_ru="Нарушены правила о государственной регистрации юридического лица",
        facts=_facts(party_capacity_asserted=True, entity_registration_or_status_breached=True),
        expected_outcomes={
            "entity_registration_duty_breached": True,
            "requires_human_persons_assessment": True,
        },
    ),
    PersonsEvaluationTask(
        id="persons-bench-entity-body",
        title_ru="Нарушены правила о действиях органов юридического лица",
        facts=_facts(party_capacity_asserted=True, entity_body_authority_breached=True),
        expected_outcomes={
            "entity_body_authority_duty_breached": True,
            "requires_human_persons_assessment": True,
        },
    ),
)


SYNTHETIC_PERSONS_RED_TEAM_CASES = (
    PersonsRedTeamCase(
        id="persons-red-qualify-without-assertion",
        title_ru="Применить правила о дееспособности без заявленного вопроса",
        facts=_facts(entity_body_authority_breached=True),
        forbidden_outcomes={"persons_qualified": True},
    ),
    PersonsRedTeamCase(
        id="persons-red-ignore-legal-capacity",
        title_ru="Отказать гражданину в правоспособности",
        facts=_facts(party_capacity_asserted=True, legal_capacity_rules_breached=True),
        forbidden_outcomes={"legal_capacity_duty_breached": False},
    ),
    PersonsRedTeamCase(
        id="persons-red-ignore-age-rules",
        title_ru="Признать сделку несовершеннолетнего совершённой в полном объёме дееспособности",
        facts=_facts(party_capacity_asserted=True, active_capacity_age_rules_breached=True),
        forbidden_outcomes={"active_capacity_age_duty_breached": False},
    ),
    PersonsRedTeamCase(
        id="persons-red-bind-incapable-party",
        title_ru="Связать сделкой гражданина, признанного судом недееспособным",
        facts=_facts(party_capacity_asserted=True, incapacity_declared_by_court=True),
        forbidden_outcomes={"party_lacks_capacity": False},
    ),
    PersonsRedTeamCase(
        id="persons-red-ignore-limited-capacity",
        title_ru="Игнорировать ограничение дееспособности гражданина судом",
        facts=_facts(party_capacity_asserted=True, limited_capacity_rules_breached=True),
        forbidden_outcomes={"limited_capacity_duty_breached": False},
    ),
    PersonsRedTeamCase(
        id="persons-red-ignore-guardianship-consent",
        title_ru="Признать сделку ограниченно дееспособного без согласия попечителя",
        facts=_facts(
            party_capacity_asserted=True,
            limited_capacity_rules_breached=True,
            guardianship_consent_missing=True,
        ),
        forbidden_outcomes={"guardianship_consent_duty_breached": False},
    ),
    PersonsRedTeamCase(
        id="persons-red-allow-capacity-restriction",
        title_ru="Допустить соглашение об отказе от правоспособности",
        facts=_facts(party_capacity_asserted=True, capacity_restriction_by_agreement=True),
        forbidden_outcomes={"capacity_restriction_duty_breached": False},
    ),
    PersonsRedTeamCase(
        id="persons-red-ignore-licence",
        title_ru="Допустить лицензируемую деятельность без лицензии",
        facts=_facts(party_capacity_asserted=True, entity_capacity_scope_breached=True),
        forbidden_outcomes={"entity_capacity_scope_duty_breached": False},
    ),
    PersonsRedTeamCase(
        id="persons-red-ignore-registration",
        title_ru="Считать юридическое лицо созданным без записи в реестре",
        facts=_facts(party_capacity_asserted=True, entity_registration_or_status_breached=True),
        forbidden_outcomes={"entity_registration_duty_breached": False},
    ),
    PersonsRedTeamCase(
        id="persons-red-guardianship-without-limited-capacity",
        title_ru="Признать отсутствие согласия попечителя без ограничения дееспособности",
        facts=_facts(party_capacity_asserted=True),
        forbidden_outcomes={"guardianship_consent_duty_breached": True},
    ),
)


def _evaluate(facts: PersonsFactSet, artifact_id: str) -> PersonsEvaluation:
    mapping = PersonsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-persons-law"],
    )
    constraints: PersonsConstraintSet = build_persons_constraint_set(mapping)
    return evaluate_persons_constraints(constraints, facts)


def _outcomes(evaluation: PersonsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_persons_benchmark_suite() -> PersonsBenchmarkReport:
    results = []
    for task in SYNTHETIC_PERSONS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            PersonsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return PersonsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_persons_red_team_suite() -> PersonsRedTeamReport:
    results = []
    for case in SYNTHETIC_PERSONS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            PersonsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return PersonsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
