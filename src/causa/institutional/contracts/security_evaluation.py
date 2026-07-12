from pydantic import BaseModel, Field

from causa.institutional.contracts.security import (
    SecurityEvaluation,
    SecurityEvidenceMappingResult,
    SecurityFactSet,
    build_security_constraint_set,
    evaluate_security_constraints,
)


class SecurityEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: SecurityFactSet
    expected_outcomes: dict[str, bool]


class SecurityEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SecurityBenchmarkReport(BaseModel):
    id: str = "security-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[SecurityEvaluationResult] = Field(default_factory=list)


class SecurityRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: SecurityFactSet
    forbidden_outcomes: dict[str, bool]


class SecurityRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SecurityRedTeamReport(BaseModel):
    id: str = "security-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[SecurityRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> SecurityFactSet:
    values = {field_name: False for field_name in SecurityFactSet.model_fields}
    values.update(
        main_obligation_exists=True,
        creditor_good_faith=True,
        **updates,
    )
    return SecurityFactSet(**values)


def _pledge(**updates: bool) -> SecurityFactSet:
    return _facts(
        pledge_created=True,
        pledge_form_observed=True,
        pledged_asset_identified=True,
        pledgor_owns_or_authorized=True,
        **updates,
    )


def _surety(**updates: bool) -> SecurityFactSet:
    return _facts(
        main_obligation_breached=True,
        suretyship_created=True,
        suretyship_writing_observed=True,
        surety_scope_proven=True,
        **updates,
    )


def _guarantee(**updates: bool) -> SecurityFactSet:
    return _facts(
        independent_guarantee_issued=True,
        guarantor_eligible=True,
        guarantee_reproducible_form=True,
        guarantee_essential_terms_identifiable=True,
        **updates,
    )


SYNTHETIC_SECURITY_BENCHMARKS = (
    SecurityEvaluationTask(
        id="security-bench-none",
        title_ru="Обеспечение не согласовано и не возникло",
        facts=_facts(main_obligation_breached=True),
        expected_outcomes={
            "security_mechanism_detected": False,
            "security_enforcement_available": False,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-penalty",
        title_ru="Письменное соглашение о неустойке и нарушение",
        facts=_facts(
            main_obligation_breached=True,
            penalty_agreed=True,
            penalty_writing_observed=True,
            penalty_trigger_occurred=True,
        ),
        expected_outcomes={"penalty_security_enforceable": True},
    ),
    SecurityEvaluationTask(
        id="security-bench-penalty-form",
        title_ru="Неустойка без письменной формы",
        facts=_facts(
            main_obligation_breached=True,
            penalty_agreed=True,
            penalty_trigger_occurred=True,
        ),
        expected_outcomes={
            "penalty_security_enforceable": False,
            "main_obligation_unaffected_by_security_defect": True,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-pledge-parties",
        title_ru="Залог действует между сторонами",
        facts=_pledge(),
        expected_outcomes={
            "pledge_valid_between_parties": True,
            "pledge_opposable_to_third_parties": True,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-pledge-registration",
        title_ru="Незарегистрированный залог против третьего лица",
        facts=_pledge(pledge_registration_required=True),
        expected_outcomes={
            "pledge_valid_between_parties": True,
            "pledge_opposable_to_third_parties": False,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-pledge-judicial",
        title_ru="Судебное обращение взыскания",
        facts=_pledge(
            main_obligation_breached=True,
            foreclosure_ground_exists=True,
            secured_amount_proven=True,
            judicial_foreclosure_mandatory=True,
        ),
        expected_outcomes={
            "pledge_foreclosure_prerequisites": True,
            "pledge_judicial_route": True,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-pledge-extra",
        title_ru="Внесудебное обращение взыскания с уведомлением",
        facts=_pledge(
            main_obligation_breached=True,
            foreclosure_ground_exists=True,
            secured_amount_proven=True,
            extrajudicial_foreclosure_agreed=True,
            extrajudicial_form_observed=True,
            foreclosure_notice_delivered=True,
        ),
        expected_outcomes={
            "pledge_extrajudicial_route": True,
            "pledge_judicial_route": False,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-pledge-bar",
        title_ru="Незначительное и явно несоразмерное нарушение",
        facts=_pledge(
            main_obligation_breached=True,
            foreclosure_ground_exists=True,
            secured_amount_proven=True,
            breach_insignificant=True,
            secured_claim_manifestly_disproportionate=True,
        ),
        expected_outcomes={
            "pledge_foreclosure_bar": True,
            "pledge_foreclosure_prerequisites": False,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-retention",
        title_ru="Удержание вещи по связанному требованию",
        facts=_facts(
            asset_lawfully_in_creditor_possession=True,
            asset_return_due=True,
            retention_secured_claim_due=True,
            claim_related_to_asset=True,
            creditor_demand_made=True,
        ),
        expected_outcomes={
            "retention_available": True,
            "retention_enforcement_issue": True,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-surety-solidary",
        title_ru="Солидарная ответственность поручителя по умолчанию",
        facts=_surety(),
        expected_outcomes={
            "surety_enforceable": True,
            "surety_solidary_liability": True,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-surety-change",
        title_ru="Увеличение ответственности без согласия поручителя",
        facts=_surety(obligation_changed_increases_surety=True),
        expected_outcomes={
            "surety_enforceable": True,
            "surety_scope_change_excluded": True,
            "surety_terminated": False,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-surety-transfer",
        title_ru="Перевод долга без согласия поручителя",
        facts=_surety(debt_transferred=True),
        expected_outcomes={
            "surety_terminated": True,
            "surety_enforceable": False,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-guarantee-independent",
        title_ru="Независимая гарантия при недействительности основного обязательства",
        facts=_guarantee(
            main_obligation_invalid=True,
            creditor_demand_made=True,
            guarantee_demand_timely=True,
            guarantee_demand_complies=True,
        ),
        expected_outcomes={
            "guarantee_survives_main_invalidity": True,
            "guarantee_demand_payable": True,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-guarantee-refusal",
        title_ru="Несоответствующее требование по гарантии",
        facts=_guarantee(creditor_demand_made=True, guarantee_demand_timely=True),
        expected_outcomes={
            "guarantee_refusal_ground": True,
            "guarantee_demand_payable": False,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-deposit-double",
        title_ru="Двойной возврат задатка по ответственности получателя",
        facts=_facts(
            payment_transferred_at_conclusion=True,
            payment_identified_as_deposit_in_writing=True,
            deposit_recipient_responsible=True,
        ),
        expected_outcomes={
            "deposit_proven": True,
            "deposit_return_double": True,
            "deposit_losses_issue": True,
        },
    ),
    SecurityEvaluationTask(
        id="security-bench-security-payment",
        title_ru="Зачет обеспечительного платежа",
        facts=_facts(
            security_payment_agreed=True,
            security_payment_funded=True,
            secured_circumstance_occurred=True,
        ),
        expected_outcomes={
            "security_payment_active": True,
            "security_payment_credit_available": True,
        },
    ),
)


SYNTHETIC_SECURITY_RED_TEAM_CASES = (
    SecurityRedTeamCase(
        id="security-red-penalty-form",
        title_ru="Взыскать договорную неустойку без письменной формы",
        facts=_facts(
            main_obligation_breached=True,
            penalty_agreed=True,
            penalty_trigger_occurred=True,
        ),
        forbidden_outcomes={"penalty_security_enforceable": True},
    ),
    SecurityRedTeamCase(
        id="security-red-accessory-invalid",
        title_ru="Сохранить акцессорное обеспечение недействительного обязательства",
        facts=_facts(
            main_obligation_invalid=True,
            penalty_agreed=True,
            penalty_writing_observed=True,
            penalty_trigger_occurred=True,
            payment_transferred_at_conclusion=True,
            payment_identified_as_deposit_in_writing=True,
            deposit_recipient_responsible=True,
        ),
        forbidden_outcomes={
            "penalty_security_enforceable": True,
            "deposit_return_double": True,
        },
    ),
    SecurityRedTeamCase(
        id="security-red-pledge-authority",
        title_ru="Признать залог без права залогодателя на вещь",
        facts=_facts(
            pledge_created=True,
            pledge_form_observed=True,
            pledged_asset_identified=True,
        ),
        forbidden_outcomes={"pledge_valid_between_parties": True},
    ),
    SecurityRedTeamCase(
        id="security-red-pledge-third",
        title_ru="Противопоставить незарегистрированный залог третьему лицу",
        facts=_pledge(pledge_registration_required=True),
        forbidden_outcomes={"pledge_opposable_to_third_parties": True},
    ),
    SecurityRedTeamCase(
        id="security-red-pledge-no-breach",
        title_ru="Обратить взыскание без нарушения основного обязательства",
        facts=_pledge(foreclosure_ground_exists=True, secured_amount_proven=True),
        forbidden_outcomes={"pledge_foreclosure_prerequisites": True},
    ),
    SecurityRedTeamCase(
        id="security-red-pledge-insignificant",
        title_ru="Игнорировать запрет при незначительности и несоразмерности",
        facts=_pledge(
            main_obligation_breached=True,
            foreclosure_ground_exists=True,
            secured_amount_proven=True,
            breach_insignificant=True,
            secured_claim_manifestly_disproportionate=True,
        ),
        forbidden_outcomes={"pledge_foreclosure_prerequisites": True},
    ),
    SecurityRedTeamCase(
        id="security-red-extra-mandatory",
        title_ru="Использовать внесудебный порядок при обязательном судебном",
        facts=_pledge(
            main_obligation_breached=True,
            foreclosure_ground_exists=True,
            secured_amount_proven=True,
            extrajudicial_foreclosure_agreed=True,
            extrajudicial_form_observed=True,
            foreclosure_notice_delivered=True,
            judicial_foreclosure_mandatory=True,
        ),
        forbidden_outcomes={"pledge_extrajudicial_route": True},
    ),
    SecurityRedTeamCase(
        id="security-red-retention-unrelated",
        title_ru="Удерживать вещь по несвязанному непредпринимательскому требованию",
        facts=_facts(
            asset_lawfully_in_creditor_possession=True,
            asset_return_due=True,
            retention_secured_claim_due=True,
        ),
        forbidden_outcomes={"retention_available": True},
    ),
    SecurityRedTeamCase(
        id="security-red-surety-form",
        title_ru="Привлечь поручителя без письменной формы",
        facts=_facts(
            main_obligation_breached=True,
            suretyship_created=True,
            surety_scope_proven=True,
        ),
        forbidden_outcomes={"surety_enforceable": True},
    ),
    SecurityRedTeamCase(
        id="security-red-surety-expired",
        title_ru="Привлечь поручителя после прекращения срока",
        facts=_surety(surety_term_expired=True),
        forbidden_outcomes={"surety_enforceable": True},
    ),
    SecurityRedTeamCase(
        id="security-red-surety-change-termination",
        title_ru="Прекратить все поручительство из-за увеличения без согласия",
        facts=_surety(obligation_changed_increases_surety=True),
        forbidden_outcomes={"surety_terminated": True},
    ),
    SecurityRedTeamCase(
        id="security-red-guarantee-accessory",
        title_ru="Прекратить независимую гарантию вместе с основным обязательством",
        facts=_guarantee(main_obligation_invalid=True),
        forbidden_outcomes={"guarantee_survives_main_invalidity": False},
    ),
    SecurityRedTeamCase(
        id="security-red-guarantee-late",
        title_ru="Удовлетворить просроченное требование по гарантии",
        facts=_guarantee(
            creditor_demand_made=True,
            guarantee_demand_complies=True,
            guarantee_expired=True,
        ),
        forbidden_outcomes={"guarantee_demand_payable": True},
    ),
    SecurityRedTeamCase(
        id="security-red-guarantee-abuse",
        title_ru="Игнорировать доказанное злоупотребление бенефициара",
        facts=_guarantee(
            creditor_demand_made=True,
            guarantee_demand_timely=True,
            guarantee_demand_complies=True,
            beneficiary_abuse_proven=True,
        ),
        forbidden_outcomes={"guarantee_demand_payable": True},
    ),
    SecurityRedTeamCase(
        id="security-red-deposit-doubt",
        title_ru="Применить двойной задаток при сомнительной квалификации платежа",
        facts=_facts(
            payment_transferred_at_conclusion=True,
            payment_identified_as_deposit_in_writing=True,
            deposit_nature_doubtful=True,
            deposit_recipient_responsible=True,
        ),
        forbidden_outcomes={"deposit_return_double": True},
    ),
    SecurityRedTeamCase(
        id="security-red-payment-unfunded",
        title_ru="Зачесть неперечисленный обеспечительный платеж",
        facts=_facts(
            security_payment_agreed=True,
            secured_circumstance_occurred=True,
        ),
        forbidden_outcomes={"security_payment_credit_available": True},
    ),
)


def _evaluate(facts: SecurityFactSet, artifact_id: str) -> SecurityEvaluation:
    mapping = SecurityEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-security-law"],
    )
    constraint_set = build_security_constraint_set(mapping)
    return evaluate_security_constraints(constraint_set, facts)


def _outcomes(evaluation: SecurityEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_security_benchmark_suite() -> SecurityBenchmarkReport:
    results = []
    for task in SYNTHETIC_SECURITY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            SecurityEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return SecurityBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_security_red_team_suite() -> SecurityRedTeamReport:
    results = []
    for case in SYNTHETIC_SECURITY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            SecurityRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return SecurityRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
