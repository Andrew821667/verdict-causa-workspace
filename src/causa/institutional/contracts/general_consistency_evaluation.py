from pydantic import BaseModel, Field

from causa.institutional.contracts.general_consistency import (
    GeneralConsistencyEvaluation,
    GeneralConsistencyInputs,
    build_general_consistency_constraint_set,
    evaluate_general_consistency_constraints,
)


class GeneralConsistencyEvaluationTask(BaseModel):
    id: str
    title_ru: str
    inputs: GeneralConsistencyInputs
    expected_outcomes: dict[str, bool]


class GeneralConsistencyEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GeneralConsistencyBenchmarkReport(BaseModel):
    id: str = "general-consistency-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[GeneralConsistencyEvaluationResult] = Field(default_factory=list)


class GeneralConsistencyRedTeamCase(BaseModel):
    id: str
    title_ru: str
    inputs: GeneralConsistencyInputs
    forbidden_outcomes: dict[str, bool]


class GeneralConsistencyRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GeneralConsistencyRedTeamReport(BaseModel):
    id: str = "general-consistency-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[GeneralConsistencyRedTeamResult] = Field(default_factory=list)


def _inputs(**updates: bool) -> GeneralConsistencyInputs:
    values = {field_name: False for field_name in GeneralConsistencyInputs.model_fields}
    # Согласованное базовое состояние: договор заключён, форма не порочна.
    values.update(formation_contract_concluded=True)
    values.update(updates)
    return GeneralConsistencyInputs(**values)


# Согласованные пары: факт утверждён в обоих институтах.
_AGREED = dict(
    persons_incapacity_declared=True,
    invalidity_incapacitated_person_transaction=True,
)


SYNTHETIC_GENERAL_CONSISTENCY_BENCHMARKS = (
    GeneralConsistencyEvaluationTask(
        id="consistency-bench-no-conflicts",
        title_ru="Описания фактов в институтах совпадают",
        inputs=_inputs(),
        expected_outcomes={"contradictions_detected": False},
    ),
    GeneralConsistencyEvaluationTask(
        id="consistency-bench-agreed-facts-are-not-a-conflict",
        title_ru="Факт утверждён в обоих институтах — противоречия нет",
        inputs=_inputs(**_AGREED),
        expected_outcomes={
            "capacity_invalidity_conflict": False,
            "contradictions_detected": False,
        },
    ),
    GeneralConsistencyEvaluationTask(
        id="consistency-bench-capacity",
        title_ru="Недееспособность утверждена в модели лиц и отрицается в недействительности",
        inputs=_inputs(persons_incapacity_declared=True),
        expected_outcomes={
            "capacity_invalidity_conflict": True,
            "requires_human_consistency_assessment": True,
        },
    ),
    GeneralConsistencyEvaluationTask(
        id="consistency-bench-entity-capacity",
        title_ru="Выход за пределы правоспособности юридического лица описан по-разному",
        inputs=_inputs(persons_entity_capacity_breached=True),
        expected_outcomes={
            "entity_capacity_invalidity_conflict": True,
            "requires_human_consistency_assessment": True,
        },
    ),
    GeneralConsistencyEvaluationTask(
        id="consistency-bench-limited-capacity",
        title_ru="Сделка ограниченно дееспособного без согласия попечителя описана по-разному",
        inputs=_inputs(persons_limited_capacity_without_consent=True),
        expected_outcomes={
            "limited_capacity_invalidity_conflict": True,
            "requires_human_consistency_assessment": True,
        },
    ),
    GeneralConsistencyEvaluationTask(
        id="consistency-bench-minor",
        title_ru="Сделка малолетнего утверждена без нарушения правил о возрастной дееспособности",
        inputs=_inputs(invalidity_minor_under_14_transaction=True),
        expected_outcomes={
            "minor_capacity_invalidity_conflict": True,
            "requires_human_consistency_assessment": True,
        },
    ),
    GeneralConsistencyEvaluationTask(
        id="consistency-bench-consent",
        title_ru="Отсутствие необходимого согласия описано по-разному",
        inputs=_inputs(transactions_statutory_consent_absent=True),
        expected_outcomes={
            "consent_invalidity_conflict": True,
            "requires_human_consistency_assessment": True,
        },
    ),
    GeneralConsistencyEvaluationTask(
        id="consistency-bench-circulation",
        title_ru="Объект вне оборота, но нарушения закона и публичного интереса не заявлены",
        inputs=_inputs(objects_not_in_civil_circulation=True),
        expected_outcomes={
            "circulation_lawfulness_conflict": True,
            "circulation_public_interest_conflict": True,
            "requires_human_consistency_assessment": True,
        },
    ),
    GeneralConsistencyEvaluationTask(
        id="consistency-bench-formation-invalidity",
        title_ru="Договор не заключён, но недействительность оценивается",
        inputs=_inputs(formation_contract_concluded=False, invalidity_transaction_concluded=True),
        expected_outcomes={
            "formation_invalidity_conclusion_conflict": True,
            "requires_human_consistency_assessment": True,
        },
    ),
    GeneralConsistencyEvaluationTask(
        id="consistency-bench-form-observance",
        title_ru="Форма заявлена соблюдённой при несоблюдённой письменной форме",
        inputs=_inputs(
            formation_required_form_observed=True,
            form_written_form_required=True,
            form_written_form_observed=False,
        ),
        expected_outcomes={
            "formation_form_observance_conflict": True,
            "requires_human_consistency_assessment": True,
        },
    ),
)


SYNTHETIC_GENERAL_CONSISTENCY_RED_TEAM_CASES = (
    GeneralConsistencyRedTeamCase(
        id="consistency-red-hide-capacity-conflict",
        title_ru="Скрыть расхождение о недееспособности стороны",
        inputs=_inputs(persons_incapacity_declared=True),
        forbidden_outcomes={"capacity_invalidity_conflict": False},
    ),
    GeneralConsistencyRedTeamCase(
        id="consistency-red-hide-entity-capacity-conflict",
        title_ru="Скрыть расхождение о правоспособности юридического лица",
        inputs=_inputs(persons_entity_capacity_breached=True),
        forbidden_outcomes={"entity_capacity_invalidity_conflict": False},
    ),
    GeneralConsistencyRedTeamCase(
        id="consistency-red-hide-limited-capacity-conflict",
        title_ru="Скрыть расхождение об ограничении дееспособности",
        inputs=_inputs(persons_limited_capacity_without_consent=True),
        forbidden_outcomes={"limited_capacity_invalidity_conflict": False},
    ),
    GeneralConsistencyRedTeamCase(
        id="consistency-red-hide-minor-conflict",
        title_ru="Скрыть расхождение о сделке малолетнего",
        inputs=_inputs(invalidity_minor_under_14_transaction=True),
        forbidden_outcomes={"minor_capacity_invalidity_conflict": False},
    ),
    GeneralConsistencyRedTeamCase(
        id="consistency-red-hide-consent-conflict",
        title_ru="Скрыть расхождение об отсутствии необходимого согласия",
        inputs=_inputs(transactions_statutory_consent_absent=True),
        forbidden_outcomes={"consent_invalidity_conflict": False},
    ),
    GeneralConsistencyRedTeamCase(
        id="consistency-red-hide-circulation-conflict",
        title_ru="Скрыть расхождение об объекте, изъятом из оборота",
        inputs=_inputs(objects_not_in_civil_circulation=True),
        forbidden_outcomes={"circulation_lawfulness_conflict": False},
    ),
    GeneralConsistencyRedTeamCase(
        id="consistency-red-hide-formation-invalidity-conflict",
        title_ru="Оценивать недействительность незаключённого договора",
        inputs=_inputs(formation_contract_concluded=False, invalidity_transaction_concluded=True),
        forbidden_outcomes={"formation_invalidity_conclusion_conflict": False},
    ),
    GeneralConsistencyRedTeamCase(
        id="consistency-red-hide-formation-termination-conflict",
        title_ru="Расторгать незаключённый договор",
        inputs=_inputs(formation_contract_concluded=False, termination_contract_formed=True),
        forbidden_outcomes={"formation_termination_conclusion_conflict": False},
    ),
    GeneralConsistencyRedTeamCase(
        id="consistency-red-hide-form-conflict",
        title_ru="Признать форму соблюдённой вопреки модели формы сделки",
        inputs=_inputs(
            formation_required_form_observed=True,
            form_written_form_required=True,
            form_written_form_observed=False,
        ),
        forbidden_outcomes={"formation_form_observance_conflict": False},
    ),
    GeneralConsistencyRedTeamCase(
        id="consistency-red-invent-conflict-from-agreed-facts",
        title_ru="Объявить противоречие там, где институты согласны",
        inputs=_inputs(**_AGREED),
        forbidden_outcomes={"contradictions_detected": True},
    ),
)


def _evaluate(inputs: GeneralConsistencyInputs, case_id: str) -> GeneralConsistencyEvaluation:
    constraint_set = build_general_consistency_constraint_set(inputs, case_id)
    return evaluate_general_consistency_constraints(constraint_set, inputs)


def _outcomes(evaluation: GeneralConsistencyEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_general_consistency_benchmark_suite() -> GeneralConsistencyBenchmarkReport:
    results = []
    for task in SYNTHETIC_GENERAL_CONSISTENCY_BENCHMARKS:
        evaluation = _evaluate(task.inputs, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            GeneralConsistencyEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return GeneralConsistencyBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_general_consistency_red_team_suite() -> GeneralConsistencyRedTeamReport:
    results = []
    for case in SYNTHETIC_GENERAL_CONSISTENCY_RED_TEAM_CASES:
        evaluation = _evaluate(case.inputs, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            GeneralConsistencyRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return GeneralConsistencyRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
