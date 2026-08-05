from pydantic import BaseModel, Field

from causa.institutional.contracts.commission import (
    CommissionConstraintSet,
    CommissionEvaluation,
    CommissionEvidenceMappingResult,
    CommissionFactSet,
    build_commission_constraint_set,
    evaluate_commission_constraints,
)


class CommissionEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: CommissionFactSet
    expected_outcomes: dict[str, bool]


class CommissionEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CommissionBenchmarkReport(BaseModel):
    id: str = "commission-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[CommissionEvaluationResult] = Field(default_factory=list)


class CommissionRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: CommissionFactSet
    forbidden_outcomes: dict[str, bool]


class CommissionRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CommissionRedTeamReport(BaseModel):
    id: str = "commission-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[CommissionRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> CommissionFactSet:
    values = {field_name: False for field_name in CommissionFactSet.model_fields}
    values.update(updates)
    return CommissionFactSet(**values)


SYNTHETIC_COMMISSION_BENCHMARKS = (
    CommissionEvaluationTask(
        id="commission-bench-not-qualified",
        title_ru="Договор комиссии не заключён",
        facts=_facts(subcommission_rules_breached=True),
        expected_outcomes={"commission_qualified": False},
    ),
    CommissionEvaluationTask(
        id="commission-bench-qualified-clean",
        title_ru="Договор комиссии без нарушений",
        facts=_facts(commission_contract_concluded=True),
        expected_outcomes={
            "commission_qualified": True,
            "requires_human_commission_assessment": False,
        },
    ),
    CommissionEvaluationTask(
        id="commission-bench-remuneration",
        title_ru="Нарушены правила о комиссионном вознаграждении и делькредере",
        facts=_facts(
            commission_contract_concluded=True,
            commission_remuneration_rules_breached=True,
        ),
        expected_outcomes={
            "remuneration_duty_breached": True,
            "requires_human_commission_assessment": True,
        },
    ),
    CommissionEvaluationTask(
        id="commission-bench-instructions",
        title_ru="Комиссионер отступил от указаний и не уведомил комитента",
        facts=_facts(
            commission_contract_concluded=True,
            commission_instructions_not_followed=True,
            deviation_notice_not_given=True,
        ),
        expected_outcomes={
            "instructions_duty_breached": True,
            "deviation_notice_duty_breached": True,
            "requires_human_commission_assessment": True,
        },
    ),
    CommissionEvaluationTask(
        id="commission-bench-third-party",
        title_ru="Нарушены правила об ответственности за неисполнение сделки третьим лицом",
        facts=_facts(
            commission_contract_concluded=True,
            third_party_transaction_rules_breached=True,
        ),
        expected_outcomes={
            "third_party_transaction_duty_breached": True,
            "requires_human_commission_assessment": True,
        },
    ),
    CommissionEvaluationTask(
        id="commission-bench-subcommission",
        title_ru="Нарушены правила о субкомиссии",
        facts=_facts(
            commission_contract_concluded=True,
            subcommission_rules_breached=True,
        ),
        expected_outcomes={
            "subcommission_duty_breached": True,
            "requires_human_commission_assessment": True,
        },
    ),
    CommissionEvaluationTask(
        id="commission-bench-property-rights",
        title_ru="Права комитента на вещи и удержание комиссионера нарушены",
        facts=_facts(
            commission_contract_concluded=True,
            principal_property_rights_disregarded=True,
        ),
        expected_outcomes={
            "principal_property_rights_breached": True,
            "requires_human_commission_assessment": True,
        },
    ),
    CommissionEvaluationTask(
        id="commission-bench-report",
        title_ru="Отчёт комиссионера не представлен, полученное не передано",
        facts=_facts(
            commission_contract_concluded=True,
            commission_report_or_transfer_breached=True,
        ),
        expected_outcomes={
            "report_and_transfer_duty_breached": True,
            "requires_human_commission_assessment": True,
        },
    ),
    CommissionEvaluationTask(
        id="commission-bench-principal-acceptance",
        title_ru="Комитент не принял исполненное и не возместил расходы",
        facts=_facts(
            commission_contract_concluded=True,
            principal_acceptance_and_expenses_breached=True,
        ),
        expected_outcomes={
            "principal_acceptance_duty_breached": True,
            "requires_human_commission_assessment": True,
        },
    ),
    CommissionEvaluationTask(
        id="commission-bench-termination",
        title_ru="Нарушены правила прекращения договора комиссии",
        facts=_facts(
            commission_contract_concluded=True,
            commission_termination_rules_breached=True,
        ),
        expected_outcomes={
            "termination_duty_breached": True,
            "requires_human_commission_assessment": True,
        },
    ),
)


SYNTHETIC_COMMISSION_RED_TEAM_CASES = (
    CommissionRedTeamCase(
        id="commission-red-qualify-without-contract",
        title_ru="Квалифицировать комиссию без заключения договора",
        facts=_facts(subcommission_rules_breached=True),
        forbidden_outcomes={"commission_qualified": True},
    ),
    CommissionRedTeamCase(
        id="commission-red-ignore-remuneration",
        title_ru="Освободить комитента от уплаты комиссионного вознаграждения",
        facts=_facts(
            commission_contract_concluded=True,
            commission_remuneration_rules_breached=True,
        ),
        forbidden_outcomes={"remuneration_duty_breached": False},
    ),
    CommissionRedTeamCase(
        id="commission-red-ignore-instructions",
        title_ru="Игнорировать отступление комиссионера от указаний комитента",
        facts=_facts(
            commission_contract_concluded=True,
            commission_instructions_not_followed=True,
        ),
        forbidden_outcomes={"instructions_duty_breached": False},
    ),
    CommissionRedTeamCase(
        id="commission-red-notice-without-deviation",
        title_ru="Признать нарушение уведомления без отступления от указаний",
        facts=_facts(commission_contract_concluded=True),
        forbidden_outcomes={"deviation_notice_duty_breached": True},
    ),
    CommissionRedTeamCase(
        id="commission-red-ignore-third-party",
        title_ru="Игнорировать правила об ответственности за третье лицо",
        facts=_facts(
            commission_contract_concluded=True,
            third_party_transaction_rules_breached=True,
        ),
        forbidden_outcomes={"third_party_transaction_duty_breached": False},
    ),
    CommissionRedTeamCase(
        id="commission-red-ignore-subcommission",
        title_ru="Игнорировать нарушение правил о субкомиссии",
        facts=_facts(
            commission_contract_concluded=True,
            subcommission_rules_breached=True,
        ),
        forbidden_outcomes={"subcommission_duty_breached": False},
    ),
    CommissionRedTeamCase(
        id="commission-red-ignore-property-rights",
        title_ru="Признать вещи комитента собственностью комиссионера",
        facts=_facts(
            commission_contract_concluded=True,
            principal_property_rights_disregarded=True,
        ),
        forbidden_outcomes={"principal_property_rights_breached": False},
    ),
    CommissionRedTeamCase(
        id="commission-red-ignore-report",
        title_ru="Освободить комиссионера от представления отчёта комитенту",
        facts=_facts(
            commission_contract_concluded=True,
            commission_report_or_transfer_breached=True,
        ),
        forbidden_outcomes={"report_and_transfer_duty_breached": False},
    ),
    CommissionRedTeamCase(
        id="commission-red-ignore-principal-acceptance",
        title_ru="Освободить комитента от принятия исполненного и возмещения расходов",
        facts=_facts(
            commission_contract_concluded=True,
            principal_acceptance_and_expenses_breached=True,
        ),
        forbidden_outcomes={"principal_acceptance_duty_breached": False},
    ),
    CommissionRedTeamCase(
        id="commission-red-skip-human-on-termination",
        title_ru="Пропустить экспертизу при нарушении прекращения договора комиссии",
        facts=_facts(
            commission_contract_concluded=True,
            commission_termination_rules_breached=True,
        ),
        forbidden_outcomes={"requires_human_commission_assessment": False},
    ),
)


def _evaluate(facts: CommissionFactSet, artifact_id: str) -> CommissionEvaluation:
    mapping = CommissionEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-commission-law"],
    )
    constraints: CommissionConstraintSet = build_commission_constraint_set(mapping)
    return evaluate_commission_constraints(constraints, facts)


def _outcomes(evaluation: CommissionEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_commission_benchmark_suite() -> CommissionBenchmarkReport:
    results = []
    for task in SYNTHETIC_COMMISSION_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            CommissionEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return CommissionBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_commission_red_team_suite() -> CommissionRedTeamReport:
    results = []
    for case in SYNTHETIC_COMMISSION_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            CommissionRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return CommissionRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
