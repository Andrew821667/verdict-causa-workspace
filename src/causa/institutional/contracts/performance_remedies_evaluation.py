from pydantic import BaseModel, Field

from causa.institutional.contracts.performance_remedies import (
    PerformanceRemediesEvaluation,
    PerformanceRemediesEvidenceMappingResult,
    PerformanceRemediesFactSet,
    build_performance_remedies_constraint_set,
    evaluate_performance_remedies_constraints,
)


class PerformanceRemediesEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: PerformanceRemediesFactSet
    expected_outcomes: dict[str, bool]


class PerformanceRemediesEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PerformanceRemediesBenchmarkReport(BaseModel):
    id: str = "performance-remedies-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[PerformanceRemediesEvaluationResult] = Field(default_factory=list)


class PerformanceRemediesRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: PerformanceRemediesFactSet
    forbidden_outcomes: dict[str, bool]


class PerformanceRemediesRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PerformanceRemediesRedTeamReport(BaseModel):
    id: str = "performance-remedies-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[PerformanceRemediesRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> PerformanceRemediesFactSet:
    values = {field_name: False for field_name in PerformanceRemediesFactSet.model_fields}
    values.update(obligation_exists=True, creditor_mitigation_taken=True)
    values.update(updates)
    return PerformanceRemediesFactSet(**values)


def _proper(**updates: bool) -> PerformanceRemediesFactSet:
    values = {
        "performance_tendered": True,
        "subject_conforms": True,
        "quality_quantity_conform": True,
        "performance_at_due_time": True,
        "performance_at_proper_place": True,
        "performance_to_proper_recipient": True,
    }
    values.update(updates)
    return _facts(**values)


def _damages(**updates: bool) -> PerformanceRemediesFactSet:
    values = {
        "breach_established": True,
        "loss_claimed": True,
        "actual_loss_proven": True,
        "causation_proven": True,
        "reasonable_amount_basis": True,
    }
    values.update(updates)
    return _facts(**values)


def _interest(**updates: bool) -> PerformanceRemediesFactSet:
    values = {
        "monetary_obligation": True,
        "monetary_delay": True,
        "article_395_claimed": True,
        "statutory_rate_basis_proven": True,
        "interest_period_proven": True,
    }
    values.update(updates)
    return _facts(**values)


SYNTHETIC_PERFORMANCE_REMEDIES_BENCHMARKS = (
    PerformanceRemediesEvaluationTask(
        id="performance-bench-proper",
        title_ru="Надлежащее исполнение",
        facts=_proper(),
        expected_outcomes={"proper_performance": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-partial-money",
        title_ru="Частичное исполнение денежного обязательства",
        facts=_facts(
            performance_tendered=True,
            partial_performance_tendered=True,
            monetary_obligation=True,
        ),
        expected_outcomes={"partial_performance_acceptance_required": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-partial-refusal",
        title_ru="Допустимый отказ от недоговоренного частичного исполнения",
        facts=_facts(performance_tendered=True, partial_performance_tendered=True),
        expected_outcomes={"partial_performance_refusal_available": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-authority-gap",
        title_ru="Приостановление до подтверждения полномочий получателя",
        facts=_facts(performance_tendered=True, debtor_requested_authority_proof=True),
        expected_outcomes={"recipient_authority_gap": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-early",
        title_ru="Досрочное исполнение вне общего предпринимательского режима",
        facts=_facts(performance_tendered=True, early_performance_tendered=True),
        expected_outcomes={"early_performance_permitted": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-third-party",
        title_ru="Исполнение возложено на третье лицо",
        facts=_facts(
            third_party_performance_tendered=True,
            debtor_assigned_third_party_performance=True,
        ),
        expected_outcomes={
            "third_party_performance_acceptance_required": True,
            "third_party_subrogation_issue": True,
        },
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-demand",
        title_ru="Наступление срока обязательства до востребования",
        facts=_facts(
            demand_obligation=True,
            creditor_demand_delivered=True,
            statutory_or_agreed_grace_elapsed=True,
        ),
        expected_outcomes={"demand_obligation_due": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-creditor-prerequisite",
        title_ru="Кредитор не совершил необходимое для исполнения действие",
        facts=_facts(creditor_prerequisite_action_required=True),
        expected_outcomes={
            "creditor_prerequisite_delay": True,
            "creditor_in_delay": True,
        },
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-bank-payment",
        title_ru="Безналичный платеж поступил банку кредитора",
        facts=_facts(monetary_obligation=True, payment_received_by_creditor_bank=True),
        expected_outcomes={"bank_payment_completed": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-allocation",
        title_ru="Должник указал погашаемое однородное обязательство",
        facts=_facts(
            multiple_homogeneous_debts=True,
            payment_insufficient=True,
            debtor_designated_debt=True,
            debt_designation_valid=True,
        ),
        expected_outcomes={"debtor_allocation_effective": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-default-allocation",
        title_ru="Очередность при отсутствии действительного указания должника",
        facts=_facts(multiple_homogeneous_debts=True, payment_insufficient=True),
        expected_outcomes={"default_payment_allocation_issue": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-alternative",
        title_ru="Выбор по альтернативному обязательству",
        facts=_facts(alternative_obligation=True, choice_holder_selected=True),
        expected_outcomes={"alternative_choice_effective": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-facultative",
        title_ru="Замена исполнения по факультативному обязательству",
        facts=_facts(facultative_obligation=True, facultative_substitute_tendered=True),
        expected_outcomes={"facultative_substitute_effective": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-solidary",
        title_ru="Полное исполнение солидарным должником и внутренний регресс",
        facts=_facts(
            multiple_debtors=True,
            solidarity_by_law_or_contract=True,
            one_solidary_debtor_performed_full=True,
            internal_recourse_shares_proven=True,
        ),
        expected_outcomes={
            "solidary_obligation": True,
            "solidary_external_discharge": True,
            "solidary_internal_recourse": True,
        },
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-counter-suspension",
        title_ru="Приостановление встречного исполнения",
        facts=_facts(
            reciprocal_obligations=True,
            counterperformance_due=True,
            clear_future_nonperformance=True,
            suspension_notice_delivered=True,
        ),
        expected_outcomes={"counterperformance_suspension_available": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-counter-refusal",
        title_ru="Отказ при непредоставлении встречного исполнения",
        facts=_facts(
            reciprocal_obligations=True,
            counterperformance_due=True,
            counterparty_failed_due_performance=True,
            refusal_notice_delivered=True,
        ),
        expected_outcomes={"counterperformance_refusal_available": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-damages",
        title_ru="Реальный ущерб с причинной связью",
        facts=_damages(),
        expected_outcomes={"damages_prerequisites_satisfied": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-lost-profit",
        title_ru="Упущенная выгода и предпринятые меры",
        facts=_damages(
            actual_loss_proven=False,
            lost_profit_claimed=True,
            lost_profit_measures_proven=True,
        ),
        expected_outcomes={
            "damages_prerequisites_satisfied": True,
            "lost_profit_supported": True,
        },
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-judicial-estimate",
        title_ru="Разумная основа убытков без точной суммы",
        facts=_damages(exact_amount_not_established=True),
        expected_outcomes={
            "damages_prerequisites_satisfied": True,
            "judicial_loss_estimation_required": True,
        },
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-replacement",
        title_ru="Разумная замещающая сделка",
        facts=_damages(
            replacement_transaction_made=True,
            replacement_transaction_reasonable=True,
        ),
        expected_outcomes={"replacement_transaction_damages": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-current-price",
        title_ru="Абстрактные убытки по текущей цене",
        facts=_damages(current_price_available=True),
        expected_outcomes={"current_price_damages": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-specific",
        title_ru="Исполнение обязательства в натуре",
        facts=_facts(
            specific_performance_claimed=True,
            performance_objectively_possible=True,
        ),
        expected_outcomes={"specific_performance_available": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-substitute",
        title_ru="Исполнение кредитором за счет должника",
        facts=_facts(
            breach_established=True,
            substitute_performance_by_creditor=True,
            substitute_costs_reasonable_documented=True,
        ),
        expected_outcomes={"substitute_performance_cost_recovery": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-individual-thing",
        title_ru="Истребование индивидуально-определенной вещи",
        facts=_facts(individual_specific_thing_due=True),
        expected_outcomes={"individual_thing_claim_available": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-interest",
        title_ru="Проценты за просрочку денежного обязательства",
        facts=_interest(),
        expected_outcomes={"article_395_interest_available": True},
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-creditor-delay",
        title_ru="Просрочка кредитора и вызванные ею убытки",
        facts=_facts(
            creditor_refused_proper_performance=True,
            creditor_delay_loss_proven=True,
            debtor_delay=True,
        ),
        expected_outcomes={
            "creditor_in_delay": True,
            "debtor_delay_excluded_by_creditor": True,
            "creditor_delay_damages_issue": True,
        },
    ),
    PerformanceRemediesEvaluationTask(
        id="performance-bench-indemnity",
        title_ru="Предпринимательское соглашение о возмещении потерь",
        facts=_facts(
            indemnity_agreement=True,
            indemnity_business_context=True,
            indemnity_clear=True,
            indemnity_trigger_unrelated_to_breach=True,
            indemnity_loss_occurred=True,
            indemnity_amount_or_method_agreed=True,
        ),
        expected_outcomes={"indemnity_prerequisites_satisfied": True},
    ),
)


SYNTHETIC_PERFORMANCE_REMEDIES_RED_TEAM_CASES = (
    PerformanceRemediesRedTeamCase(
        id="performance-red-improper",
        title_ru="Назвать ненадлежащее исполнение надлежащим",
        facts=_facts(performance_tendered=True, subject_conforms=True),
        forbidden_outcomes={"proper_performance": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-partial",
        title_ru="Обязать принять недоговоренное неденежное частичное исполнение",
        facts=_facts(performance_tendered=True, partial_performance_tendered=True),
        forbidden_outcomes={"partial_performance_acceptance_required": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-authority",
        title_ru="Игнорировать непредставленные полномочия получателя",
        facts=_facts(performance_tendered=True, debtor_requested_authority_proof=True),
        forbidden_outcomes={"recipient_authority_gap": False},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-early-business",
        title_ru="Навязать досрочное предпринимательское исполнение без основания",
        facts=_facts(
            performance_tendered=True,
            early_performance_tendered=True,
            all_parties_acting_in_business=True,
        ),
        forbidden_outcomes={"early_performance_permitted": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-third-personal",
        title_ru="Принять третьелицевое исполнение личной обязанности",
        facts=_facts(
            third_party_performance_tendered=True,
            debtor_assigned_third_party_performance=True,
            personal_performance_required=True,
        ),
        forbidden_outcomes={"third_party_performance_acceptance_required": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-demand",
        title_ru="Признать востребованный долг просроченным до истечения срока",
        facts=_facts(demand_obligation=True, creditor_demand_delivered=True),
        forbidden_outcomes={"demand_obligation_due": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-bank",
        title_ru="Считать платеж исполненным до поступления банку кредитора",
        facts=_facts(monetary_obligation=True),
        forbidden_outcomes={"bank_payment_completed": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-allocation",
        title_ru="Принять недействительное указание о погашаемом долге",
        facts=_facts(
            multiple_homogeneous_debts=True,
            payment_insufficient=True,
            debtor_designated_debt=True,
        ),
        forbidden_outcomes={"debtor_allocation_effective": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-solidary",
        title_ru="Презюмировать солидарность вне предусмотренных оснований",
        facts=_facts(multiple_debtors=True),
        forbidden_outcomes={"solidary_obligation": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-suspension-notice",
        title_ru="Приостановить встречное исполнение без уведомления",
        facts=_facts(
            reciprocal_obligations=True,
            counterperformance_due=True,
            clear_future_nonperformance=True,
        ),
        forbidden_outcomes={"counterperformance_suspension_available": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-refusal-future",
        title_ru="Окончательно отказаться только по прогнозу будущего неисполнения",
        facts=_facts(
            reciprocal_obligations=True,
            counterperformance_due=True,
            clear_future_nonperformance=True,
            refusal_notice_delivered=True,
        ),
        forbidden_outcomes={"counterperformance_refusal_available": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-specific-counterclaim",
        title_ru="Требовать встречное исполнение без собственного",
        facts=_facts(reciprocal_obligations=True),
        forbidden_outcomes={"counterparty_specific_claim_barred": False},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-damages-causation",
        title_ru="Взыскать убытки без причинной связи",
        facts=_damages(causation_proven=False),
        forbidden_outcomes={"damages_prerequisites_satisfied": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-damages-loss",
        title_ru="Взыскать убытки без доказанного вида потерь",
        facts=_damages(actual_loss_proven=False),
        forbidden_outcomes={"damages_prerequisites_satisfied": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-judicial-estimate",
        title_ru="Передать расчет суду без разумной основы размера",
        facts=_damages(
            reasonable_amount_basis=False,
            exact_amount_not_established=True,
        ),
        forbidden_outcomes={"judicial_loss_estimation_required": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-lost-profit",
        title_ru="Считать упущенную выгоду поддержанной без предпринятых мер",
        facts=_damages(actual_loss_proven=False, lost_profit_claimed=True),
        forbidden_outcomes={"lost_profit_supported": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-replacement",
        title_ru="Принять неразумную замещающую сделку",
        facts=_damages(replacement_transaction_made=True),
        forbidden_outcomes={"replacement_transaction_damages": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-specific-impossible",
        title_ru="Присудить объективно невозможное исполнение в натуре",
        facts=_facts(specific_performance_claimed=True),
        forbidden_outcomes={"specific_performance_available": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-specific-interest",
        title_ru="Присудить исполнение после утраты интереса из-за просрочки",
        facts=_facts(
            specific_performance_claimed=True,
            performance_objectively_possible=True,
            creditor_lost_interest_due_delay=True,
        ),
        forbidden_outcomes={"specific_performance_available": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-substitute-cost",
        title_ru="Взыскать неподтвержденные замещающие расходы",
        facts=_facts(breach_established=True, substitute_performance_by_creditor=True),
        forbidden_outcomes={"substitute_performance_cost_recovery": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-third-party-thing",
        title_ru="Истребовать вещь у защищенного третьего лица",
        facts=_facts(
            individual_specific_thing_due=True,
            thing_transferred_to_protected_third_party=True,
        ),
        forbidden_outcomes={"individual_thing_claim_available": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-interest-penalty",
        title_ru="Начислить статью 395 поверх неустойки за то же нарушение",
        facts=_interest(penalty_for_same_monetary_delay=True),
        forbidden_outcomes={"article_395_interest_available": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-interest-rate",
        title_ru="Начислить проценты без подтвержденной ставки",
        facts=_interest(statutory_rate_basis_proven=False),
        forbidden_outcomes={"article_395_interest_available": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-excess-loss",
        title_ru="Взыскать превышение убытков над процентами без доказательств",
        facts=_interest(damages_above_interest_claimed=True),
        forbidden_outcomes={"excess_monetary_damages_available": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-third-party-liability",
        title_ru="Возложить на должника неустановленную ответственность за третье лицо",
        facts=_facts(third_party_caused_breach=True),
        forbidden_outcomes={"debtor_answers_for_third_party": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-subsidiary",
        title_ru="Обратиться к субсидиарному должнику до основного",
        facts=_facts(subsidiary_debtor_claimed=True),
        forbidden_outcomes={"subsidiary_liability_prerequisites": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-intentional-limit",
        title_ru="Признать заранее исключенной ответственность за умышленное нарушение",
        facts=_facts(
            breach_established=True,
            intentional_breach=True,
            liability_limit_clause_or_law=True,
            advance_intentional_liability_exclusion=True,
        ),
        forbidden_outcomes={"intentional_liability_exclusion_invalid": False},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-creditor-delay",
        title_ru="Сохранить просрочку должника при препятствии кредитора",
        facts=_facts(debtor_delay=True, creditor_omitted_required_action=True),
        forbidden_outcomes={"debtor_in_delay": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-indemnity-consumer",
        title_ru="Применить предпринимательское возмещение потерь вне допустимого круга",
        facts=_facts(
            indemnity_agreement=True,
            indemnity_clear=True,
            indemnity_trigger_unrelated_to_breach=True,
            indemnity_loss_occurred=True,
            indemnity_amount_or_method_agreed=True,
        ),
        forbidden_outcomes={"indemnity_prerequisites_satisfied": True},
    ),
    PerformanceRemediesRedTeamCase(
        id="performance-red-indemnity-bad-faith",
        title_ru="Возместить потери, недобросовестно вызванные получателем",
        facts=_facts(
            indemnity_agreement=True,
            indemnity_business_context=True,
            indemnity_clear=True,
            indemnity_trigger_unrelated_to_breach=True,
            indemnity_loss_occurred=True,
            indemnity_amount_or_method_agreed=True,
            indemnity_bad_faith_event_caused=True,
        ),
        forbidden_outcomes={"indemnity_prerequisites_satisfied": True},
    ),
)


def _evaluate(
    facts: PerformanceRemediesFactSet,
    artifact_id: str,
) -> PerformanceRemediesEvaluation:
    mapping = PerformanceRemediesEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-performance-remedies-law"],
    )
    constraint_set = build_performance_remedies_constraint_set(mapping)
    return evaluate_performance_remedies_constraints(constraint_set, facts)


def _outcomes(
    evaluation: PerformanceRemediesEvaluation,
    names: dict[str, bool],
) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_performance_remedies_benchmark_suite() -> PerformanceRemediesBenchmarkReport:
    results = []
    for task in SYNTHETIC_PERFORMANCE_REMEDIES_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            PerformanceRemediesEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return PerformanceRemediesBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_performance_remedies_red_team_suite() -> PerformanceRemediesRedTeamReport:
    results = []
    for case in SYNTHETIC_PERFORMANCE_REMEDIES_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            PerformanceRemediesRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return PerformanceRemediesRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
