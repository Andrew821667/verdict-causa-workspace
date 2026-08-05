from pydantic import BaseModel, Field

from causa.institutional.contracts.mandate import (
    MandateConstraintSet,
    MandateEvaluation,
    MandateEvidenceMappingResult,
    MandateFactSet,
    build_mandate_constraint_set,
    evaluate_mandate_constraints,
)


class MandateEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: MandateFactSet
    expected_outcomes: dict[str, bool]


class MandateEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class MandateBenchmarkReport(BaseModel):
    id: str = "mandate-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[MandateEvaluationResult] = Field(default_factory=list)


class MandateRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: MandateFactSet
    forbidden_outcomes: dict[str, bool]


class MandateRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class MandateRedTeamReport(BaseModel):
    id: str = "mandate-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[MandateRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> MandateFactSet:
    values = {field_name: False for field_name in MandateFactSet.model_fields}
    values.update(updates)
    return MandateFactSet(**values)


SYNTHETIC_MANDATE_BENCHMARKS = (
    MandateEvaluationTask(
        id="mandate-bench-not-qualified",
        title_ru="Договор поручения не заключён",
        facts=_facts(principal_duties_breached=True),
        expected_outcomes={"mandate_qualified": False},
    ),
    MandateEvaluationTask(
        id="mandate-bench-qualified-clean",
        title_ru="Договор поручения без нарушений",
        facts=_facts(mandate_contract_concluded=True),
        expected_outcomes={
            "mandate_qualified": True,
            "requires_human_mandate_assessment": False,
        },
    ),
    MandateEvaluationTask(
        id="mandate-bench-remuneration",
        title_ru="Нарушены правила о вознаграждении поверенного",
        facts=_facts(
            mandate_contract_concluded=True,
            mandate_remuneration_rules_breached=True,
        ),
        expected_outcomes={
            "remuneration_duty_breached": True,
            "requires_human_mandate_assessment": True,
        },
    ),
    MandateEvaluationTask(
        id="mandate-bench-instructions",
        title_ru="Поверенный отступил от указаний и не уведомил доверителя",
        facts=_facts(
            mandate_contract_concluded=True,
            mandate_instructions_not_followed=True,
            deviation_notice_not_given=True,
        ),
        expected_outcomes={
            "instructions_duty_breached": True,
            "deviation_notice_duty_breached": True,
            "requires_human_mandate_assessment": True,
        },
    ),
    MandateEvaluationTask(
        id="mandate-bench-personal-performance",
        title_ru="Нарушены личное исполнение поручения и правила передоверия",
        facts=_facts(
            mandate_contract_concluded=True,
            attorney_personal_performance_breached=True,
        ),
        expected_outcomes={
            "personal_performance_duty_breached": True,
            "requires_human_mandate_assessment": True,
        },
    ),
    MandateEvaluationTask(
        id="mandate-bench-reporting",
        title_ru="Поверенный не сообщил сведения и не передал полученное",
        facts=_facts(
            mandate_contract_concluded=True,
            attorney_reporting_duty_breached=True,
        ),
        expected_outcomes={
            "reporting_duty_breached": True,
            "requires_human_mandate_assessment": True,
        },
    ),
    MandateEvaluationTask(
        id="mandate-bench-principal-duties",
        title_ru="Доверитель не выдал доверенность и не возместил издержки",
        facts=_facts(
            mandate_contract_concluded=True,
            principal_duties_breached=True,
        ),
        expected_outcomes={
            "principal_duty_breached": True,
            "requires_human_mandate_assessment": True,
        },
    ),
    MandateEvaluationTask(
        id="mandate-bench-termination",
        title_ru="Нарушены правила прекращения договора поручения",
        facts=_facts(
            mandate_contract_concluded=True,
            mandate_termination_rules_breached=True,
        ),
        expected_outcomes={
            "termination_duty_breached": True,
            "requires_human_mandate_assessment": True,
        },
    ),
    MandateEvaluationTask(
        id="mandate-bench-termination-consequences",
        title_ru="Последствия прекращения договора поручения не применены",
        facts=_facts(
            mandate_contract_concluded=True,
            termination_consequences_not_applied=True,
        ),
        expected_outcomes={
            "termination_consequences_breached": True,
            "requires_human_mandate_assessment": True,
        },
    ),
    MandateEvaluationTask(
        id="mandate-bench-successor",
        title_ru="Наследники поверенного не известили доверителя",
        facts=_facts(
            mandate_contract_concluded=True,
            successor_duties_breached=True,
        ),
        expected_outcomes={
            "successor_duty_breached": True,
            "requires_human_mandate_assessment": True,
        },
    ),
)


SYNTHETIC_MANDATE_RED_TEAM_CASES = (
    MandateRedTeamCase(
        id="mandate-red-qualify-without-contract",
        title_ru="Квалифицировать поручение без заключения договора",
        facts=_facts(principal_duties_breached=True),
        forbidden_outcomes={"mandate_qualified": True},
    ),
    MandateRedTeamCase(
        id="mandate-red-ignore-remuneration",
        title_ru="Игнорировать нарушение правил о вознаграждении поверенного",
        facts=_facts(
            mandate_contract_concluded=True,
            mandate_remuneration_rules_breached=True,
        ),
        forbidden_outcomes={"remuneration_duty_breached": False},
    ),
    MandateRedTeamCase(
        id="mandate-red-ignore-instructions",
        title_ru="Игнорировать отступление поверенного от указаний доверителя",
        facts=_facts(
            mandate_contract_concluded=True,
            mandate_instructions_not_followed=True,
        ),
        forbidden_outcomes={"instructions_duty_breached": False},
    ),
    MandateRedTeamCase(
        id="mandate-red-notice-without-deviation",
        title_ru="Признать нарушение уведомления без отступления от указаний",
        facts=_facts(mandate_contract_concluded=True),
        forbidden_outcomes={"deviation_notice_duty_breached": True},
    ),
    MandateRedTeamCase(
        id="mandate-red-ignore-personal-performance",
        title_ru="Освободить поверенного от личного исполнения поручения",
        facts=_facts(
            mandate_contract_concluded=True,
            attorney_personal_performance_breached=True,
        ),
        forbidden_outcomes={"personal_performance_duty_breached": False},
    ),
    MandateRedTeamCase(
        id="mandate-red-ignore-reporting",
        title_ru="Игнорировать непредставление отчёта и непередачу полученного",
        facts=_facts(
            mandate_contract_concluded=True,
            attorney_reporting_duty_breached=True,
        ),
        forbidden_outcomes={"reporting_duty_breached": False},
    ),
    MandateRedTeamCase(
        id="mandate-red-ignore-principal-duties",
        title_ru="Освободить доверителя от возмещения издержек поверенного",
        facts=_facts(
            mandate_contract_concluded=True,
            principal_duties_breached=True,
        ),
        forbidden_outcomes={"principal_duty_breached": False},
    ),
    MandateRedTeamCase(
        id="mandate-red-ignore-termination",
        title_ru="Признать действительным отказ от права отменить поручение",
        facts=_facts(
            mandate_contract_concluded=True,
            mandate_termination_rules_breached=True,
        ),
        forbidden_outcomes={"termination_duty_breached": False},
    ),
    MandateRedTeamCase(
        id="mandate-red-ignore-termination-consequences",
        title_ru="Игнорировать неприменение последствий прекращения поручения",
        facts=_facts(
            mandate_contract_concluded=True,
            termination_consequences_not_applied=True,
        ),
        forbidden_outcomes={"termination_consequences_breached": False},
    ),
    MandateRedTeamCase(
        id="mandate-red-skip-human-on-successor",
        title_ru="Пропустить экспертизу при нарушении обязанностей наследников поверенного",
        facts=_facts(
            mandate_contract_concluded=True,
            successor_duties_breached=True,
        ),
        forbidden_outcomes={"requires_human_mandate_assessment": False},
    ),
)


def _evaluate(facts: MandateFactSet, artifact_id: str) -> MandateEvaluation:
    mapping = MandateEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-mandate-law"],
    )
    constraints: MandateConstraintSet = build_mandate_constraint_set(mapping)
    return evaluate_mandate_constraints(constraints, facts)


def _outcomes(evaluation: MandateEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_mandate_benchmark_suite() -> MandateBenchmarkReport:
    results = []
    for task in SYNTHETIC_MANDATE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            MandateEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return MandateBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_mandate_red_team_suite() -> MandateRedTeamReport:
    results = []
    for case in SYNTHETIC_MANDATE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            MandateRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return MandateRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
