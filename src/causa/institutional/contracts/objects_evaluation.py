from pydantic import BaseModel, Field

from causa.institutional.contracts.objects import (
    ObjectsConstraintSet,
    ObjectsEvaluation,
    ObjectsEvidenceMappingResult,
    ObjectsFactSet,
    build_objects_constraint_set,
    evaluate_objects_constraints,
)


class ObjectsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ObjectsFactSet
    expected_outcomes: dict[str, bool]


class ObjectsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ObjectsBenchmarkReport(BaseModel):
    id: str = "objects-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ObjectsEvaluationResult] = Field(default_factory=list)


class ObjectsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ObjectsFactSet
    forbidden_outcomes: dict[str, bool]


class ObjectsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ObjectsRedTeamReport(BaseModel):
    id: str = "objects-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ObjectsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ObjectsFactSet:
    values = {field_name: False for field_name in ObjectsFactSet.model_fields}
    values.update(updates)
    return ObjectsFactSet(**values)


SYNTHETIC_OBJECTS_BENCHMARKS = (
    ObjectsEvaluationTask(
        id="objects-bench-not-qualified",
        title_ru="Спор об объекте гражданских прав не заявлен",
        facts=_facts(principal_and_appurtenance_breached=True),
        expected_outcomes={"objects_qualified": False},
    ),
    ObjectsEvaluationTask(
        id="objects-bench-qualified-clean",
        title_ru="Объект гражданских прав определён без нарушений",
        facts=_facts(object_of_rights_asserted=True),
        expected_outcomes={
            "objects_qualified": True,
            "requires_human_objects_assessment": False,
        },
    ),
    ObjectsEvaluationTask(
        id="objects-bench-classification",
        title_ru="Нарушен перечень объектов гражданских прав",
        facts=_facts(object_of_rights_asserted=True, object_classification_breached=True),
        expected_outcomes={
            "object_classification_duty_breached": True,
            "requires_human_objects_assessment": True,
        },
    ),
    ObjectsEvaluationTask(
        id="objects-bench-circulation",
        title_ru="Объект изъят из оборота",
        facts=_facts(object_of_rights_asserted=True, object_not_in_civil_circulation=True),
        expected_outcomes={
            "object_excluded_from_circulation": True,
            "requires_human_objects_assessment": True,
        },
    ),
    ObjectsEvaluationTask(
        id="objects-bench-immovable",
        title_ru="Нарушено деление вещей на недвижимые и движимые",
        facts=_facts(object_of_rights_asserted=True, immovable_classification_breached=True),
        expected_outcomes={
            "immovable_classification_duty_breached": True,
            "requires_human_objects_assessment": True,
        },
    ),
    ObjectsEvaluationTask(
        id="objects-bench-divisibility",
        title_ru="Нарушены правила о неделимой и сложной вещи",
        facts=_facts(object_of_rights_asserted=True, divisibility_or_complex_thing_breached=True),
        expected_outcomes={
            "divisibility_duty_breached": True,
            "requires_human_objects_assessment": True,
        },
    ),
    ObjectsEvaluationTask(
        id="objects-bench-appurtenance",
        title_ru="Принадлежность не последовала судьбе главной вещи",
        facts=_facts(object_of_rights_asserted=True, principal_and_appurtenance_breached=True),
        expected_outcomes={
            "principal_and_appurtenance_duty_breached": True,
            "requires_human_objects_assessment": True,
        },
    ),
    ObjectsEvaluationTask(
        id="objects-bench-fruits",
        title_ru="Нарушено правило о плодах, продукции и доходах",
        facts=_facts(object_of_rights_asserted=True, fruits_products_income_breached=True),
        expected_outcomes={
            "fruits_products_income_duty_breached": True,
            "requires_human_objects_assessment": True,
        },
    ),
    ObjectsEvaluationTask(
        id="objects-bench-money-securities",
        title_ru="Нарушены правила о деньгах и ценных бумагах",
        facts=_facts(object_of_rights_asserted=True, money_or_securities_rules_breached=True),
        expected_outcomes={
            "money_or_securities_duty_breached": True,
            "requires_human_objects_assessment": True,
        },
    ),
    ObjectsEvaluationTask(
        id="objects-bench-intangible-and-reputation",
        title_ru="Нарушены защита нематериальных благ и деловой репутации",
        facts=_facts(
            object_of_rights_asserted=True,
            intangible_benefits_protection_breached=True,
            honour_and_reputation_protection_breached=True,
        ),
        expected_outcomes={
            "intangible_benefits_duty_breached": True,
            "honour_and_reputation_duty_breached": True,
            "requires_human_objects_assessment": True,
        },
    ),
)


SYNTHETIC_OBJECTS_RED_TEAM_CASES = (
    ObjectsRedTeamCase(
        id="objects-red-qualify-without-object",
        title_ru="Применить правила об объектах без заявленного объекта",
        facts=_facts(principal_and_appurtenance_breached=True),
        forbidden_outcomes={"objects_qualified": True},
    ),
    ObjectsRedTeamCase(
        id="objects-red-ignore-classification",
        title_ru="Смешать нематериальные блага с имущественными правами",
        facts=_facts(object_of_rights_asserted=True, object_classification_breached=True),
        forbidden_outcomes={"object_classification_duty_breached": False},
    ),
    ObjectsRedTeamCase(
        id="objects-red-transfer-excluded-object",
        title_ru="Допустить отчуждение объекта, изъятого из оборота",
        facts=_facts(object_of_rights_asserted=True, object_not_in_civil_circulation=True),
        forbidden_outcomes={"object_excluded_from_circulation": False},
    ),
    ObjectsRedTeamCase(
        id="objects-red-ignore-immovable-rules",
        title_ru="Признать движимой вещь, прочно связанную с землёй",
        facts=_facts(object_of_rights_asserted=True, immovable_classification_breached=True),
        forbidden_outcomes={"immovable_classification_duty_breached": False},
    ),
    ObjectsRedTeamCase(
        id="objects-red-divide-indivisible-thing",
        title_ru="Разделить в натуре неделимую вещь",
        facts=_facts(object_of_rights_asserted=True, divisibility_or_complex_thing_breached=True),
        forbidden_outcomes={"divisibility_duty_breached": False},
    ),
    ObjectsRedTeamCase(
        id="objects-red-separate-appurtenance",
        title_ru="Отделить принадлежность от главной вещи вопреки статье 135",
        facts=_facts(object_of_rights_asserted=True, principal_and_appurtenance_breached=True),
        forbidden_outcomes={"principal_and_appurtenance_duty_breached": False},
    ),
    ObjectsRedTeamCase(
        id="objects-red-ignore-fruits",
        title_ru="Присвоить плоды и доходы вопреки принадлежности вещи",
        facts=_facts(object_of_rights_asserted=True, fruits_products_income_breached=True),
        forbidden_outcomes={"fruits_products_income_duty_breached": False},
    ),
    ObjectsRedTeamCase(
        id="objects-red-ignore-money-rules",
        title_ru="Отказать в приёме рубля как законного платёжного средства",
        facts=_facts(object_of_rights_asserted=True, money_or_securities_rules_breached=True),
        forbidden_outcomes={"money_or_securities_duty_breached": False},
    ),
    ObjectsRedTeamCase(
        id="objects-red-alienate-intangible-benefit",
        title_ru="Допустить отчуждение нематериального блага",
        facts=_facts(object_of_rights_asserted=True, intangible_benefits_protection_breached=True),
        forbidden_outcomes={"intangible_benefits_duty_breached": False},
    ),
    ObjectsRedTeamCase(
        id="objects-red-reputation-without-intangible-benefit",
        title_ru="Признать нарушение защиты репутации вне защиты нематериальных благ",
        facts=_facts(object_of_rights_asserted=True),
        forbidden_outcomes={"honour_and_reputation_duty_breached": True},
    ),
)


def _evaluate(facts: ObjectsFactSet, artifact_id: str) -> ObjectsEvaluation:
    mapping = ObjectsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-objects-law"],
    )
    constraints: ObjectsConstraintSet = build_objects_constraint_set(mapping)
    return evaluate_objects_constraints(constraints, facts)


def _outcomes(evaluation: ObjectsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_objects_benchmark_suite() -> ObjectsBenchmarkReport:
    results = []
    for task in SYNTHETIC_OBJECTS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ObjectsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ObjectsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_objects_red_team_suite() -> ObjectsRedTeamReport:
    results = []
    for case in SYNTHETIC_OBJECTS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ObjectsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ObjectsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
