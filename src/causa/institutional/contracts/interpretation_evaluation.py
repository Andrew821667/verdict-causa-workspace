from pydantic import BaseModel, Field

from causa.institutional.contracts.interpretation import (
    InterpretationConstraintSet,
    InterpretationEvaluation,
    InterpretationEvidenceMappingResult,
    InterpretationFactSet,
    build_interpretation_constraint_set,
    evaluate_interpretation_constraints,
)


class InterpretationEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: InterpretationFactSet
    expected_outcomes: dict[str, bool]


class InterpretationEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class InterpretationBenchmarkReport(BaseModel):
    id: str = "interpretation-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[InterpretationEvaluationResult] = Field(default_factory=list)


class InterpretationRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: InterpretationFactSet
    forbidden_outcomes: dict[str, bool]


class InterpretationRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class InterpretationRedTeamReport(BaseModel):
    id: str = "interpretation-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[InterpretationRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> InterpretationFactSet:
    values = {field_name: False for field_name in InterpretationFactSet.model_fields}
    # По умолчанию — заявлен спор о толковании условия договора (статья 431 ГК РФ).
    values.update(disputed_term_present=True)
    values.update(updates)
    return InterpretationFactSet(**values)


SYNTHETIC_INTERPRETATION_BENCHMARKS = (
    InterpretationEvaluationTask(
        id="interpretation-bench-literal",
        title_ru="Ясное и согласованное буквальное значение",
        facts=_facts(
            literal_meaning_clear=True,
            consistent_with_other_terms=True,
            consistent_with_whole_contract=True,
        ),
        expected_outcomes={
            "literal_interpretation_controls": True,
            "interpretation_resolved": True,
        },
    ),
    InterpretationEvaluationTask(
        id="interpretation-bench-systematic-other-terms",
        title_ru="Буквальное значение расходится с другими условиями",
        facts=_facts(literal_meaning_clear=True, consistent_with_whole_contract=True),
        expected_outcomes={
            "systematic_reading_required": True,
            "interpretation_resolved": False,
        },
    ),
    InterpretationEvaluationTask(
        id="interpretation-bench-systematic-whole",
        title_ru="Буквальное значение расходится со смыслом договора в целом",
        facts=_facts(literal_meaning_clear=True, consistent_with_other_terms=True),
        expected_outcomes={
            "systematic_reading_required": True,
            "interpretation_resolved": False,
        },
    ),
    InterpretationEvaluationTask(
        id="interpretation-bench-common-intent-purpose",
        title_ru="Действительная общая воля с учетом цели договора",
        facts=_facts(common_intent_established=True, purpose_considered=True),
        expected_outcomes={
            "common_intent_interpretation_controls": True,
            "interpretation_resolved": True,
        },
    ),
    InterpretationEvaluationTask(
        id="interpretation-bench-common-intent-negotiations",
        title_ru="Действительная общая воля с учетом переговоров",
        facts=_facts(common_intent_established=True, preliminary_negotiations_considered=True),
        expected_outcomes={
            "common_intent_interpretation_controls": True,
            "interpretation_resolved": True,
        },
    ),
    InterpretationEvaluationTask(
        id="interpretation-bench-common-intent-conduct",
        title_ru="Действительная общая воля с учетом последующего поведения",
        facts=_facts(common_intent_established=True, subsequent_conduct_considered=True),
        expected_outcomes={
            "common_intent_interpretation_controls": True,
            "interpretation_resolved": True,
        },
    ),
    InterpretationEvaluationTask(
        id="interpretation-bench-intent-no-circumstances",
        title_ru="Общая воля не установлена из обстоятельств",
        facts=_facts(common_intent_established=True),
        expected_outcomes={
            "common_intent_interpretation_controls": False,
            "requires_human_interpretation_assessment": True,
        },
    ),
    InterpretationEvaluationTask(
        id="interpretation-bench-contra-proferentem",
        title_ru="Неустраненная неясность в подготовленном одной стороной условии",
        facts=_facts(term_drafted_by_one_party=True),
        expected_outcomes={
            "interpretation_resolved": False,
            "contra_proferentem_available": True,
        },
    ),
    InterpretationEvaluationTask(
        id="interpretation-bench-no-dispute",
        title_ru="Спор о толковании не заявлен",
        facts=_facts(disputed_term_present=False),
        expected_outcomes={
            "interpretation_resolved": False,
            "requires_human_interpretation_assessment": False,
        },
    ),
    InterpretationEvaluationTask(
        id="interpretation-bench-literal-over-drafting",
        title_ru="Ясное буквальное значение исключает толкование против составителя",
        facts=_facts(
            literal_meaning_clear=True,
            consistent_with_other_terms=True,
            consistent_with_whole_contract=True,
            term_drafted_by_one_party=True,
        ),
        expected_outcomes={
            "literal_interpretation_controls": True,
            "contra_proferentem_available": False,
        },
    ),
)


SYNTHETIC_INTERPRETATION_RED_TEAM_CASES = (
    InterpretationRedTeamCase(
        id="interpretation-red-literal-unclear",
        title_ru="Определить содержание буквально при неясном значении",
        facts=_facts(consistent_with_other_terms=True, consistent_with_whole_contract=True),
        forbidden_outcomes={"literal_interpretation_controls": True},
    ),
    InterpretationRedTeamCase(
        id="interpretation-red-literal-inconsistent",
        title_ru="Определить содержание буквально при несогласованности",
        facts=_facts(literal_meaning_clear=True, consistent_with_whole_contract=True),
        forbidden_outcomes={"literal_interpretation_controls": True},
    ),
    InterpretationRedTeamCase(
        id="interpretation-red-intent-no-circumstances",
        title_ru="Установить общую волю без учета обстоятельств",
        facts=_facts(common_intent_established=True),
        forbidden_outcomes={"common_intent_interpretation_controls": True},
    ),
    InterpretationRedTeamCase(
        id="interpretation-red-skip-systematic",
        title_ru="Пропустить сопоставление при несогласованности",
        facts=_facts(literal_meaning_clear=True, consistent_with_whole_contract=True),
        forbidden_outcomes={"systematic_reading_required": False},
    ),
    InterpretationRedTeamCase(
        id="interpretation-red-resolve-without-ground",
        title_ru="Признать толкование завершенным без основания",
        facts=_facts(),
        forbidden_outcomes={"interpretation_resolved": True},
    ),
    InterpretationRedTeamCase(
        id="interpretation-red-contra-when-resolved",
        title_ru="Толковать против составителя при разрешенном толковании",
        facts=_facts(
            literal_meaning_clear=True,
            consistent_with_other_terms=True,
            consistent_with_whole_contract=True,
            term_drafted_by_one_party=True,
        ),
        forbidden_outcomes={"contra_proferentem_available": True},
    ),
    InterpretationRedTeamCase(
        id="interpretation-red-interpret-absent-term",
        title_ru="Толковать несуществующее условие",
        facts=_facts(
            disputed_term_present=False,
            literal_meaning_clear=True,
            consistent_with_other_terms=True,
            consistent_with_whole_contract=True,
        ),
        forbidden_outcomes={"interpretation_resolved": True},
    ),
    InterpretationRedTeamCase(
        id="interpretation-red-intent-not-established",
        title_ru="Определить волю без ее установления",
        facts=_facts(purpose_considered=True, subsequent_conduct_considered=True),
        forbidden_outcomes={"common_intent_interpretation_controls": True},
    ),
    InterpretationRedTeamCase(
        id="interpretation-red-contra-without-drafting",
        title_ru="Толковать против составителя без его авторства условия",
        facts=_facts(),
        forbidden_outcomes={"contra_proferentem_available": True},
    ),
    InterpretationRedTeamCase(
        id="interpretation-red-human-when-resolved",
        title_ru="Требовать юриста при разрешенном буквальном толковании",
        facts=_facts(
            literal_meaning_clear=True,
            consistent_with_other_terms=True,
            consistent_with_whole_contract=True,
        ),
        forbidden_outcomes={"requires_human_interpretation_assessment": True},
    ),
)


def _evaluate(facts: InterpretationFactSet, artifact_id: str) -> InterpretationEvaluation:
    mapping = InterpretationEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-interpretation-law"],
    )
    constraints: InterpretationConstraintSet = build_interpretation_constraint_set(mapping)
    return evaluate_interpretation_constraints(constraints, facts)


def _outcomes(evaluation: InterpretationEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_interpretation_benchmark_suite() -> InterpretationBenchmarkReport:
    results = []
    for task in SYNTHETIC_INTERPRETATION_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            InterpretationEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return InterpretationBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_interpretation_red_team_suite() -> InterpretationRedTeamReport:
    results = []
    for case in SYNTHETIC_INTERPRETATION_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            InterpretationRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return InterpretationRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
