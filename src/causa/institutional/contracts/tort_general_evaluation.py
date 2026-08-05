from pydantic import BaseModel, Field

from causa.institutional.contracts.tort_general import (
    TortGeneralConstraintSet,
    TortGeneralEvaluation,
    TortGeneralEvidenceMappingResult,
    TortGeneralFactSet,
    build_tort_general_constraint_set,
    evaluate_tort_general_constraints,
)


class TortGeneralEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: TortGeneralFactSet
    expected_outcomes: dict[str, bool]


class TortGeneralEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TortGeneralBenchmarkReport(BaseModel):
    id: str = "tort-general-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[TortGeneralEvaluationResult] = Field(default_factory=list)


class TortGeneralRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: TortGeneralFactSet
    forbidden_outcomes: dict[str, bool]


class TortGeneralRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TortGeneralRedTeamReport(BaseModel):
    id: str = "tort-general-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[TortGeneralRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> TortGeneralFactSet:
    values = {field_name: False for field_name in TortGeneralFactSet.model_fields}
    values.update(updates)
    return TortGeneralFactSet(**values)


SYNTHETIC_TORT_GENERAL_BENCHMARKS = (
    TortGeneralEvaluationTask(
        id="tort-general-bench-not-qualified",
        title_ru="Причинение вреда не установлено",
        facts=_facts(high_risk_source_liability_breached=True),
        expected_outcomes={"tort_qualified": False},
    ),
    TortGeneralEvaluationTask(
        id="tort-general-bench-qualified-clean",
        title_ru="Возмещение причинённого вреда без нарушений",
        facts=_facts(harm_caused_established=True),
        expected_outcomes={
            "tort_qualified": True,
            "requires_human_tort_assessment": False,
        },
    ),
    TortGeneralEvaluationTask(
        id="tort-general-bench-full-compensation",
        title_ru="Нарушено правило о возмещении вреда в полном объёме",
        facts=_facts(
            harm_caused_established=True,
            full_compensation_rule_breached=True,
        ),
        expected_outcomes={
            "full_compensation_duty_breached": True,
            "requires_human_tort_assessment": True,
        },
    ),
    TortGeneralEvaluationTask(
        id="tort-general-bench-fault-presumption",
        title_ru="Нарушена презумпция вины причинителя вреда",
        facts=_facts(
            harm_caused_established=True,
            fault_presumption_breached=True,
        ),
        expected_outcomes={
            "fault_presumption_duty_breached": True,
            "requires_human_tort_assessment": True,
        },
    ),
    TortGeneralEvaluationTask(
        id="tort-general-bench-lawful-harm",
        title_ru="Нарушены правила о необходимой обороне и крайней необходимости",
        facts=_facts(
            harm_caused_established=True,
            lawful_or_defensive_harm_rules_breached=True,
        ),
        expected_outcomes={
            "lawful_harm_duty_breached": True,
            "requires_human_tort_assessment": True,
        },
    ),
    TortGeneralEvaluationTask(
        id="tort-general-bench-liability-for-others",
        title_ru="Нарушены правила об ответственности за вред, причинённый другими лицами",
        facts=_facts(
            harm_caused_established=True,
            liability_for_others_breached=True,
        ),
        expected_outcomes={
            "liability_for_others_duty_breached": True,
            "requires_human_tort_assessment": True,
        },
    ),
    TortGeneralEvaluationTask(
        id="tort-general-bench-high-risk-source",
        title_ru="Нарушены правила об источнике повышенной опасности",
        facts=_facts(
            harm_caused_established=True,
            high_risk_source_liability_breached=True,
        ),
        expected_outcomes={
            "high_risk_source_duty_breached": True,
            "requires_human_tort_assessment": True,
        },
    ),
    TortGeneralEvaluationTask(
        id="tort-general-bench-joint-liability",
        title_ru="Нарушены солидарная ответственность и право регресса",
        facts=_facts(
            harm_caused_established=True,
            joint_liability_and_recourse_breached=True,
        ),
        expected_outcomes={
            "joint_liability_duty_breached": True,
            "requires_human_tort_assessment": True,
        },
    ),
    TortGeneralEvaluationTask(
        id="tort-general-bench-compensation-method",
        title_ru="Способ и размер возмещения вреда определены с нарушением",
        facts=_facts(
            harm_caused_established=True,
            compensation_method_or_amount_breached=True,
        ),
        expected_outcomes={
            "compensation_method_duty_breached": True,
            "requires_human_tort_assessment": True,
        },
    ),
    TortGeneralEvaluationTask(
        id="tort-general-bench-victim-fault",
        title_ru="Вина потерпевшего не учтена, уменьшение размера возмещения не применено",
        facts=_facts(
            harm_caused_established=True,
            victim_fault_or_causer_means_disregarded=True,
            gross_negligence_reduction_not_applied=True,
        ),
        expected_outcomes={
            "victim_fault_duty_breached": True,
            "gross_negligence_reduction_breached": True,
            "requires_human_tort_assessment": True,
        },
    ),
)


SYNTHETIC_TORT_GENERAL_RED_TEAM_CASES = (
    TortGeneralRedTeamCase(
        id="tort-general-red-qualify-without-harm",
        title_ru="Возложить обязанность возмещения без установленного причинения вреда",
        facts=_facts(high_risk_source_liability_breached=True),
        forbidden_outcomes={"tort_qualified": True},
    ),
    TortGeneralRedTeamCase(
        id="tort-general-red-ignore-full-compensation",
        title_ru="Возместить вред не в полном объёме вопреки закону",
        facts=_facts(
            harm_caused_established=True,
            full_compensation_rule_breached=True,
        ),
        forbidden_outcomes={"full_compensation_duty_breached": False},
    ),
    TortGeneralRedTeamCase(
        id="tort-general-red-ignore-fault-presumption",
        title_ru="Возложить на потерпевшего бремя доказывания вины причинителя",
        facts=_facts(
            harm_caused_established=True,
            fault_presumption_breached=True,
        ),
        forbidden_outcomes={"fault_presumption_duty_breached": False},
    ),
    TortGeneralRedTeamCase(
        id="tort-general-red-ignore-lawful-harm",
        title_ru="Взыскать вред, причинённый в состоянии необходимой обороны",
        facts=_facts(
            harm_caused_established=True,
            lawful_or_defensive_harm_rules_breached=True,
        ),
        forbidden_outcomes={"lawful_harm_duty_breached": False},
    ),
    TortGeneralRedTeamCase(
        id="tort-general-red-ignore-liability-for-others",
        title_ru="Освободить работодателя от ответственности за вред, причинённый работником",
        facts=_facts(
            harm_caused_established=True,
            liability_for_others_breached=True,
        ),
        forbidden_outcomes={"liability_for_others_duty_breached": False},
    ),
    TortGeneralRedTeamCase(
        id="tort-general-red-ignore-high-risk-source",
        title_ru="Освободить владельца источника повышенной опасности при отсутствии вины",
        facts=_facts(
            harm_caused_established=True,
            high_risk_source_liability_breached=True,
        ),
        forbidden_outcomes={"high_risk_source_duty_breached": False},
    ),
    TortGeneralRedTeamCase(
        id="tort-general-red-ignore-joint-liability",
        title_ru="Отказать потерпевшему в солидарном взыскании с сопричинителей",
        facts=_facts(
            harm_caused_established=True,
            joint_liability_and_recourse_breached=True,
        ),
        forbidden_outcomes={"joint_liability_duty_breached": False},
    ),
    TortGeneralRedTeamCase(
        id="tort-general-red-ignore-compensation-method",
        title_ru="Игнорировать нарушение способа и размера возмещения вреда",
        facts=_facts(
            harm_caused_established=True,
            compensation_method_or_amount_breached=True,
        ),
        forbidden_outcomes={"compensation_method_duty_breached": False},
    ),
    TortGeneralRedTeamCase(
        id="tort-general-red-reduction-without-victim-fault-breach",
        title_ru="Уменьшить возмещение без установленного нарушения учёта вины потерпевшего",
        facts=_facts(harm_caused_established=True),
        forbidden_outcomes={"gross_negligence_reduction_breached": True},
    ),
    TortGeneralRedTeamCase(
        id="tort-general-red-skip-human-on-victim-fault",
        title_ru="Пропустить экспертизу при неучёте умысла потерпевшего",
        facts=_facts(
            harm_caused_established=True,
            victim_fault_or_causer_means_disregarded=True,
        ),
        forbidden_outcomes={"requires_human_tort_assessment": False},
    ),
)


def _evaluate(facts: TortGeneralFactSet, artifact_id: str) -> TortGeneralEvaluation:
    mapping = TortGeneralEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-tort-general-law"],
    )
    constraints: TortGeneralConstraintSet = build_tort_general_constraint_set(mapping)
    return evaluate_tort_general_constraints(constraints, facts)


def _outcomes(evaluation: TortGeneralEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_tort_general_benchmark_suite() -> TortGeneralBenchmarkReport:
    results = []
    for task in SYNTHETIC_TORT_GENERAL_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            TortGeneralEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return TortGeneralBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_tort_general_red_team_suite() -> TortGeneralRedTeamReport:
    results = []
    for case in SYNTHETIC_TORT_GENERAL_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            TortGeneralRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return TortGeneralRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
