from pydantic import BaseModel, Field

from causa.institutional.contracts.forwarding import (
    ForwardingConstraintSet,
    ForwardingEvaluation,
    ForwardingEvidenceMappingResult,
    ForwardingFactSet,
    build_forwarding_constraint_set,
    evaluate_forwarding_constraints,
)


class ForwardingEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ForwardingFactSet
    expected_outcomes: dict[str, bool]


class ForwardingEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ForwardingBenchmarkReport(BaseModel):
    id: str = "forwarding-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ForwardingEvaluationResult] = Field(default_factory=list)


class ForwardingRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ForwardingFactSet
    forbidden_outcomes: dict[str, bool]


class ForwardingRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ForwardingRedTeamReport(BaseModel):
    id: str = "forwarding-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ForwardingRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ForwardingFactSet:
    values = {field_name: False for field_name in ForwardingFactSet.model_fields}
    values.update(updates)
    return ForwardingFactSet(**values)


SYNTHETIC_FORWARDING_BENCHMARKS = (
    ForwardingEvaluationTask(
        id="forwarding-bench-not-qualified",
        title_ru="Экспедиционные услуги за счёт клиента не оказываются",
        facts=_facts(written_form_or_power_of_attorney_missing=True),
        expected_outcomes={"forwarding_qualified": False},
    ),
    ForwardingEvaluationTask(
        id="forwarding-bench-qualified-clean",
        title_ru="Договор транспортной экспедиции без нарушений",
        facts=_facts(forwarding_services_for_fee_at_client_expense=True),
        expected_outcomes={
            "forwarding_qualified": True,
            "requires_human_forwarding_assessment": False,
        },
    ),
    ForwardingEvaluationTask(
        id="forwarding-bench-form",
        title_ru="Не соблюдена письменная форма или не выдана доверенность",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            written_form_or_power_of_attorney_missing=True,
        ),
        expected_outcomes={
            "form_or_authority_requirement_breached": True,
            "requires_human_forwarding_assessment": True,
        },
    ),
    ForwardingEvaluationTask(
        id="forwarding-bench-services-not-performed",
        title_ru="Экспедитор не выполнил и не организовал предусмотренные услуги",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            forwarder_failed_to_perform_agreed_services=True,
        ),
        expected_outcomes={
            "forwarding_services_not_performed": True,
            "requires_human_forwarding_assessment": True,
        },
    ),
    ForwardingEvaluationTask(
        id="forwarding-bench-carrier-linked",
        title_ru="Нарушение вызвано ненадлежащим исполнением договора перевозки",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            carrier_breach_caused_forwarder_liability=True,
        ),
        expected_outcomes={
            "carrier_linked_liability_applies": True,
            "requires_human_forwarding_assessment": True,
        },
    ),
    ForwardingEvaluationTask(
        id="forwarding-bench-client-information",
        title_ru="Клиент не предоставил документы и информацию о грузе",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            client_documents_or_information_not_provided=True,
        ),
        expected_outcomes={
            "client_information_duty_breached": True,
            "requires_human_forwarding_assessment": True,
        },
    ),
    ForwardingEvaluationTask(
        id="forwarding-bench-forwarder-notice",
        title_ru="Экспедитор не сообщил клиенту о неполноте полученной информации",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            client_documents_or_information_not_provided=True,
            forwarder_did_not_report_incomplete_information=True,
        ),
        expected_outcomes={
            "client_information_duty_breached": True,
            "forwarder_notice_duty_breached": True,
            "requires_human_forwarding_assessment": True,
        },
    ),
    ForwardingEvaluationTask(
        id="forwarding-bench-personal-performance",
        title_ru="Обязанности возложены на третье лицо вопреки условию о личном исполнении",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            third_party_engaged_despite_personal_duty=True,
        ),
        expected_outcomes={
            "personal_performance_duty_breached": True,
            "requires_human_forwarding_assessment": True,
        },
    ),
    ForwardingEvaluationTask(
        id="forwarding-bench-withdrawal",
        title_ru="Односторонний отказ без разумного предупреждения и без возмещения убытков",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            withdrawal_without_reasonable_notice=True,
            withdrawal_losses_not_compensated=True,
        ),
        expected_outcomes={
            "withdrawal_notice_duty_breached": True,
            "withdrawal_losses_compensation_due": True,
            "requires_human_forwarding_assessment": True,
        },
    ),
    ForwardingEvaluationTask(
        id="forwarding-bench-penalty",
        title_ru="Штраф при одностороннем отказе не уплачен",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            statutory_penalty_not_paid_on_withdrawal=True,
        ),
        expected_outcomes={
            "statutory_penalty_due": True,
            "requires_human_forwarding_assessment": True,
        },
    ),
)


SYNTHETIC_FORWARDING_RED_TEAM_CASES = (
    ForwardingRedTeamCase(
        id="forwarding-red-qualify-without-services",
        title_ru="Квалифицировать экспедицию без оказания услуг за счёт клиента",
        facts=_facts(written_form_or_power_of_attorney_missing=True),
        forbidden_outcomes={"forwarding_qualified": True},
    ),
    ForwardingRedTeamCase(
        id="forwarding-red-ignore-form",
        title_ru="Игнорировать несоблюдение письменной формы договора",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            written_form_or_power_of_attorney_missing=True,
        ),
        forbidden_outcomes={"form_or_authority_requirement_breached": False},
    ),
    ForwardingRedTeamCase(
        id="forwarding-red-ignore-services",
        title_ru="Игнорировать невыполнение экспедиционных услуг",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            forwarder_failed_to_perform_agreed_services=True,
        ),
        forbidden_outcomes={"forwarding_services_not_performed": False},
    ),
    ForwardingRedTeamCase(
        id="forwarding-red-ignore-carrier-link",
        title_ru="Игнорировать связь ответственности с договором перевозки",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            carrier_breach_caused_forwarder_liability=True,
        ),
        forbidden_outcomes={"carrier_linked_liability_applies": False},
    ),
    ForwardingRedTeamCase(
        id="forwarding-red-ignore-client-information",
        title_ru="Игнорировать непредоставление клиентом документов о грузе",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            client_documents_or_information_not_provided=True,
        ),
        forbidden_outcomes={"client_information_duty_breached": False},
    ),
    ForwardingRedTeamCase(
        id="forwarding-red-notice-without-missing-information",
        title_ru="Признать нарушение обязанности сообщить без неполноты информации",
        facts=_facts(forwarding_services_for_fee_at_client_expense=True),
        forbidden_outcomes={"forwarder_notice_duty_breached": True},
    ),
    ForwardingRedTeamCase(
        id="forwarding-red-allow-third-party",
        title_ru="Признать допустимым возложение обязанностей вопреки личному исполнению",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            third_party_engaged_despite_personal_duty=True,
        ),
        forbidden_outcomes={"personal_performance_duty_breached": False},
    ),
    ForwardingRedTeamCase(
        id="forwarding-red-ignore-withdrawal-notice",
        title_ru="Игнорировать отказ без предупреждения в разумный срок",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            withdrawal_without_reasonable_notice=True,
        ),
        forbidden_outcomes={"withdrawal_notice_duty_breached": False},
    ),
    ForwardingRedTeamCase(
        id="forwarding-red-losses-without-withdrawal",
        title_ru="Признать возмещение убытков от расторжения без самого отказа",
        facts=_facts(forwarding_services_for_fee_at_client_expense=True),
        forbidden_outcomes={"withdrawal_losses_compensation_due": True},
    ),
    ForwardingRedTeamCase(
        id="forwarding-red-skip-human-on-penalty",
        title_ru="Пропустить экспертизу при неуплате штрафа за односторонний отказ",
        facts=_facts(
            forwarding_services_for_fee_at_client_expense=True,
            statutory_penalty_not_paid_on_withdrawal=True,
        ),
        forbidden_outcomes={"requires_human_forwarding_assessment": False},
    ),
)


def _evaluate(facts: ForwardingFactSet, artifact_id: str) -> ForwardingEvaluation:
    mapping = ForwardingEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-forwarding-law"],
    )
    constraints: ForwardingConstraintSet = build_forwarding_constraint_set(mapping)
    return evaluate_forwarding_constraints(constraints, facts)


def _outcomes(evaluation: ForwardingEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_forwarding_benchmark_suite() -> ForwardingBenchmarkReport:
    results = []
    for task in SYNTHETIC_FORWARDING_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ForwardingEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ForwardingBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_forwarding_red_team_suite() -> ForwardingRedTeamReport:
    results = []
    for case in SYNTHETIC_FORWARDING_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ForwardingRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ForwardingRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
