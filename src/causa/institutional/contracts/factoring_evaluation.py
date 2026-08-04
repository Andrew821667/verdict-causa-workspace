from pydantic import BaseModel, Field

from causa.institutional.contracts.factoring import (
    FactoringConstraintSet,
    FactoringEvaluation,
    FactoringEvidenceMappingResult,
    FactoringFactSet,
    build_factoring_constraint_set,
    evaluate_factoring_constraints,
)


class FactoringEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: FactoringFactSet
    expected_outcomes: dict[str, bool]


class FactoringEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FactoringBenchmarkReport(BaseModel):
    id: str = "factoring-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[FactoringEvaluationResult] = Field(default_factory=list)


class FactoringRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: FactoringFactSet
    forbidden_outcomes: dict[str, bool]


class FactoringRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FactoringRedTeamReport(BaseModel):
    id: str = "factoring-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[FactoringRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> FactoringFactSet:
    values = {field_name: False for field_name in FactoringFactSet.model_fields}
    values.update(updates)
    return FactoringFactSet(**values)


SYNTHETIC_FACTORING_BENCHMARKS = (
    FactoringEvaluationTask(
        id="factoring-bench-not-qualified",
        title_ru="Денежное требование под финансирование не уступается",
        facts=_facts(factor_not_entitled_to_act=True),
        expected_outcomes={"factoring_qualified": False},
    ),
    FactoringEvaluationTask(
        id="factoring-bench-qualified-clean",
        title_ru="Договор факторинга без нарушений",
        facts=_facts(monetary_claim_assigned_for_financing=True),
        expected_outcomes={
            "factoring_qualified": True,
            "requires_human_factoring_assessment": False,
        },
    ),
    FactoringEvaluationTask(
        id="factoring-bench-claim-identification",
        title_ru="Уступаемое денежное требование не определено в договоре",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            assigned_claim_not_identified=True,
        ),
        expected_outcomes={
            "claim_identification_breached": True,
            "requires_human_factoring_assessment": True,
        },
    ),
    FactoringEvaluationTask(
        id="factoring-bench-factor-status",
        title_ru="Финансовый агент не вправе осуществлять такую деятельность",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            factor_not_entitled_to_act=True,
        ),
        expected_outcomes={
            "factor_status_invalid": True,
            "requires_human_factoring_assessment": True,
        },
    ),
    FactoringEvaluationTask(
        id="factoring-bench-assignment-ban",
        title_ru="Против финансового агента заявлен договорный запрет уступки",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            contractual_assignment_ban_invoked_against_factor=True,
        ),
        expected_outcomes={
            "assignment_ban_ineffective_against_factor": True,
            "requires_human_factoring_assessment": True,
        },
    ),
    FactoringEvaluationTask(
        id="factoring-bench-client-warranty",
        title_ru="Клиент нарушил ответственность за действительность требования",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            client_claim_validity_warranty_breached=True,
        ),
        expected_outcomes={
            "client_warranty_breached": True,
            "requires_human_factoring_assessment": True,
        },
    ),
    FactoringEvaluationTask(
        id="factoring-bench-subsequent-assignment",
        title_ru="Последующая уступка совершена без разрешения договора",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            subsequent_assignment_made_without_permission=True,
        ),
        expected_outcomes={
            "subsequent_assignment_unauthorized": True,
            "requires_human_factoring_assessment": True,
        },
    ),
    FactoringEvaluationTask(
        id="factoring-bench-debtor-set-off",
        title_ru="Должник не уведомлен об уступке, его зачётные требования не учтены",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            debtor_not_notified_of_assignment=True,
            debtor_set_off_claims_disregarded=True,
        ),
        expected_outcomes={
            "debtor_notice_duty_breached": True,
            "debtor_set_off_right_available": True,
            "requires_human_factoring_assessment": True,
        },
    ),
    FactoringEvaluationTask(
        id="factoring-bench-settlement",
        title_ru="Расчёты финансового агента с клиентом произведены с нарушением",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            factor_settlement_with_client_breached=True,
        ),
        expected_outcomes={
            "settlement_duty_breached": True,
            "requires_human_factoring_assessment": True,
        },
    ),
    FactoringEvaluationTask(
        id="factoring-bench-refund-direction",
        title_ru="Требование должника о возврате сумм направлено ненадлежащей стороне",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            debtor_refund_claim_misdirected=True,
        ),
        expected_outcomes={
            "refund_claim_direction_breached": True,
            "requires_human_factoring_assessment": True,
        },
    ),
)


SYNTHETIC_FACTORING_RED_TEAM_CASES = (
    FactoringRedTeamCase(
        id="factoring-red-qualify-without-assignment",
        title_ru="Квалифицировать факторинг без уступки денежного требования",
        facts=_facts(factor_not_entitled_to_act=True),
        forbidden_outcomes={"factoring_qualified": True},
    ),
    FactoringRedTeamCase(
        id="factoring-red-ignore-claim-identification",
        title_ru="Игнорировать неопределённость уступаемого требования",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            assigned_claim_not_identified=True,
        ),
        forbidden_outcomes={"claim_identification_breached": False},
    ),
    FactoringRedTeamCase(
        id="factoring-red-ignore-factor-status",
        title_ru="Игнорировать отсутствие у агента права осуществлять деятельность",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            factor_not_entitled_to_act=True,
        ),
        forbidden_outcomes={"factor_status_invalid": False},
    ),
    FactoringRedTeamCase(
        id="factoring-red-uphold-assignment-ban",
        title_ru="Признать договорный запрет уступки действующим против агента",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            contractual_assignment_ban_invoked_against_factor=True,
        ),
        forbidden_outcomes={"assignment_ban_ineffective_against_factor": False},
    ),
    FactoringRedTeamCase(
        id="factoring-red-ignore-client-warranty",
        title_ru="Освободить клиента от ответственности за действительность требования",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            client_claim_validity_warranty_breached=True,
        ),
        forbidden_outcomes={"client_warranty_breached": False},
    ),
    FactoringRedTeamCase(
        id="factoring-red-allow-subsequent-assignment",
        title_ru="Признать допустимой последующую уступку без разрешения договора",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            subsequent_assignment_made_without_permission=True,
        ),
        forbidden_outcomes={"subsequent_assignment_unauthorized": False},
    ),
    FactoringRedTeamCase(
        id="factoring-red-ignore-debtor-notice",
        title_ru="Игнорировать отсутствие уведомления должника об уступке",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            debtor_not_notified_of_assignment=True,
        ),
        forbidden_outcomes={"debtor_notice_duty_breached": False},
    ),
    FactoringRedTeamCase(
        id="factoring-red-set-off-without-notice-breach",
        title_ru="Признать право на зачёт без нарушения уведомления должника",
        facts=_facts(monetary_claim_assigned_for_financing=True),
        forbidden_outcomes={"debtor_set_off_right_available": True},
    ),
    FactoringRedTeamCase(
        id="factoring-red-ignore-settlement",
        title_ru="Игнорировать нарушение расчётов агента с клиентом",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            factor_settlement_with_client_breached=True,
        ),
        forbidden_outcomes={"settlement_duty_breached": False},
    ),
    FactoringRedTeamCase(
        id="factoring-red-skip-human-on-refund",
        title_ru="Пропустить экспертизу при неверном адресате требования о возврате",
        facts=_facts(
            monetary_claim_assigned_for_financing=True,
            debtor_refund_claim_misdirected=True,
        ),
        forbidden_outcomes={"requires_human_factoring_assessment": False},
    ),
)


def _evaluate(facts: FactoringFactSet, artifact_id: str) -> FactoringEvaluation:
    mapping = FactoringEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-factoring-law"],
    )
    constraints: FactoringConstraintSet = build_factoring_constraint_set(mapping)
    return evaluate_factoring_constraints(constraints, facts)


def _outcomes(evaluation: FactoringEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_factoring_benchmark_suite() -> FactoringBenchmarkReport:
    results = []
    for task in SYNTHETIC_FACTORING_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            FactoringEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return FactoringBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_factoring_red_team_suite() -> FactoringRedTeamReport:
    results = []
    for case in SYNTHETIC_FACTORING_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            FactoringRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return FactoringRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
