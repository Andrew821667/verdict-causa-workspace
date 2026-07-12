from pydantic import BaseModel, Field

from causa.institutional.contracts.obligation_dynamics import (
    ObligationDynamicsEvaluation,
    ObligationDynamicsEvidenceMappingResult,
    ObligationDynamicsFactSet,
    build_obligation_dynamics_constraint_set,
    evaluate_obligation_dynamics_constraints,
)


class ObligationDynamicsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ObligationDynamicsFactSet
    expected_outcomes: dict[str, bool]


class ObligationDynamicsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ObligationDynamicsBenchmarkReport(BaseModel):
    id: str = "obligation-dynamics-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ObligationDynamicsEvaluationResult] = Field(default_factory=list)


class ObligationDynamicsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ObligationDynamicsFactSet
    forbidden_outcomes: dict[str, bool]


class ObligationDynamicsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ObligationDynamicsRedTeamReport(BaseModel):
    id: str = "obligation-dynamics-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ObligationDynamicsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ObligationDynamicsFactSet:
    values = {field_name: False for field_name in ObligationDynamicsFactSet.model_fields}
    values["obligation_exists"] = True
    values.update(updates)
    return ObligationDynamicsFactSet(**values)


def _assignment(**updates: bool) -> ObligationDynamicsFactSet:
    return _facts(
        assignment_agreement_concluded=True,
        assignment_form_observed=True,
        assigned_claim_exists=True,
        assigned_claim_identified=True,
        cedent_transferred_documents=True,
        **updates,
    )


def _debt_transfer(**updates: bool) -> ObligationDynamicsFactSet:
    return _facts(
        debt_transfer_agreement_concluded=True,
        debt_transfer_form_observed=True,
        new_debtor_identified=True,
        creditor_consented_debt_transfer=True,
        **updates,
    )


def _setoff(**updates: bool) -> ObligationDynamicsFactSet:
    return _facts(
        set_off_declared=True,
        set_off_notice_delivered=True,
        counterclaims_mutual=True,
        counterclaims_homogeneous=True,
        active_claim_due=True,
        passive_claim_due_or_early_allowed=True,
        set_off_amount_proven=True,
        **updates,
    )


SYNTHETIC_OBLIGATION_DYNAMICS_BENCHMARKS = (
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-continuing",
        title_ru="Обязательство продолжает действовать",
        facts=_facts(),
        expected_outcomes={
            "obligation_discharged_full": False,
            "parties_changed_not_discharged": False,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-assignment",
        title_ru="Уступка существующего требования с уведомлением",
        facts=_assignment(debtor_notified=True, proof_of_transfer_provided=True),
        expected_outcomes={
            "assignment_effective": True,
            "assignment_enforceable_against_debtor": True,
            "parties_changed_not_discharged": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-future-assignment",
        title_ru="Уступка определимого будущего требования",
        facts=_facts(
            assignment_agreement_concluded=True,
            assignment_form_observed=True,
            future_claim_determinable=True,
            cedent_transferred_documents=True,
        ),
        expected_outcomes={"assignment_effective": True},
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-assignment-restriction",
        title_ru="Действующая уступка при договорном ограничении",
        facts=_assignment(contract_restricts_assignment=True),
        expected_outcomes={
            "assignment_effective": True,
            "assignment_contract_breach_issue": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-original-performance",
        title_ru="Исполнение первоначальному кредитору до уведомления",
        facts=_assignment(debtor_performed_original_before_notice=True),
        expected_outcomes={"debtor_original_performance_discharges": True},
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-debt-release",
        title_ru="Перевод долга с освобождением первоначального должника",
        facts=_debt_transfer(original_debtor_released=True),
        expected_outcomes={
            "debt_transfer_effective": True,
            "original_debtor_released_effective": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-cumulative",
        title_ru="Кумулятивное принятие предпринимательского долга",
        facts=_debt_transfer(business_debt_assumption=True),
        expected_outcomes={"cumulative_debtors": True},
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-contract-transfer",
        title_ru="Передача договора с согласием всех сторон",
        facts=_facts(
            assignment_agreement_concluded=True,
            assignment_form_observed=True,
            debt_transfer_agreement_concluded=True,
            debt_transfer_form_observed=True,
            contract_transfer_agreed=True,
            all_parties_consented_contract_transfer=True,
        ),
        expected_outcomes={
            "contract_transfer_effective": True,
            "parties_changed_not_discharged": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-performance",
        title_ru="Надлежащее полное исполнение после просрочки",
        facts=_facts(
            obligation_breached=True,
            accrued_claims_exist=True,
            performance_rendered=True,
            performance_accepted_as_proper=True,
            creditor_issued_receipt=True,
        ),
        expected_outcomes={
            "proper_performance_discharge": True,
            "obligation_discharged_full": True,
            "accrued_claims_preserved": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-partial-performance",
        title_ru="Частичное надлежащее исполнение",
        facts=_facts(
            performance_rendered=True,
            performance_accepted_as_proper=True,
            performance_partial=True,
        ),
        expected_outcomes={
            "partial_performance_discharge": True,
            "obligation_partially_remaining": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-deposit",
        title_ru="Внесение долга в депозит нотариуса",
        facts=_facts(
            notary_or_court_deposit_made=True,
            deposit_ground_creditor_absent_or_evasive=True,
            deposit_notice_sent=True,
        ),
        expected_outcomes={
            "notary_deposit_discharge": True,
            "obligation_discharged_full": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-accord-pending",
        title_ru="Соглашение об отступном до предоставления",
        facts=_facts(accord_agreed=True, accord_form_observed=True),
        expected_outcomes={
            "accord_agreement_only": True,
            "accord_discharge": False,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-accord",
        title_ru="Предоставленное отступное",
        facts=_facts(
            accord_agreed=True,
            accord_form_observed=True,
            accord_performance_provided=True,
        ),
        expected_outcomes={
            "accord_discharge": True,
            "obligation_discharged_full": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-setoff-full",
        title_ru="Полный зачет равных встречных требований",
        facts=_setoff(claims_equal_amount=True),
        expected_outcomes={
            "setoff_effective": True,
            "setoff_full_discharge": True,
            "obligation_discharged_full": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-setoff-partial",
        title_ru="Частичный зачет неравных требований",
        facts=_setoff(),
        expected_outcomes={
            "setoff_partial_discharge": True,
            "obligation_partially_remaining": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-novation",
        title_ru="Новация с сохранением обеспечения третьего лица",
        facts=_facts(
            novation_agreed=True,
            novation_intent_clear=True,
            new_subject_or_basis=True,
            new_obligation_terms_agreed=True,
            novation_form_observed=True,
            third_party_security_exists=True,
            third_party_security_consented_novation=True,
        ),
        expected_outcomes={
            "novation_effective": True,
            "new_obligation_created_by_novation": True,
            "third_party_security_survives_novation": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-forgiveness",
        title_ru="Прощение долга без возражения должника",
        facts=_facts(
            debt_forgiveness_declared=True,
            debt_forgiveness_notice_delivered=True,
        ),
        expected_outcomes={
            "debt_forgiveness_effective": True,
            "obligation_discharged_full": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-merger",
        title_ru="Совпадение должника и кредитора",
        facts=_facts(merger_creditor_and_debtor=True),
        expected_outcomes={"merger_discharge": True},
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-impossibility",
        title_ru="Объективная постоянная невозможность исполнения",
        facts=_facts(objective_permanent_impossibility=True),
        expected_outcomes={"impossibility_discharge": True},
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-government-act",
        title_ru="Прекращение из-за акта органа власти",
        facts=_facts(government_act_prevents_performance=True),
        expected_outcomes={
            "government_act_discharge": True,
            "government_act_losses_issue": True,
        },
    ),
    ObligationDynamicsEvaluationTask(
        id="dynamics-bench-death-liquidation",
        title_ru="Личные обязательства умершего и ликвидация без правопреемника",
        facts=_facts(
            personal_debtor_died=True,
            obligation_personal_to_deceased=True,
            legal_entity_liquidated=True,
        ),
        expected_outcomes={
            "death_discharge": True,
            "liquidation_discharge": True,
            "competing_discharge_paths": True,
        },
    ),
)


SYNTHETIC_OBLIGATION_DYNAMICS_RED_TEAM_CASES = (
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-assignment-form",
        title_ru="Признать уступку без требуемой формы",
        facts=_facts(
            assignment_agreement_concluded=True,
            assigned_claim_exists=True,
            assigned_claim_identified=True,
        ),
        forbidden_outcomes={"assignment_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-personal-claim",
        title_ru="Уступить требование, неразрывно связанное с кредитором",
        facts=_assignment(claim_personal_to_creditor=True),
        forbidden_outcomes={"assignment_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-consent",
        title_ru="Уступить требование без обязательного согласия должника",
        facts=_assignment(debtor_consent_required=True),
        forbidden_outcomes={"assignment_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-notice",
        title_ru="Предъявить уступку должнику без уведомления и доказательства",
        facts=_assignment(),
        forbidden_outcomes={"assignment_enforceable_against_debtor": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-invalid-claim",
        title_ru="Перенести отсутствующее или недействительное требование",
        facts=_assignment(claim_invalid=True, cedent_knew_claim_invalid=True),
        forbidden_outcomes={"assignment_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-debt-consent",
        title_ru="Перевести долг без согласия кредитора",
        facts=_facts(
            debt_transfer_agreement_concluded=True,
            debt_transfer_form_observed=True,
            new_debtor_identified=True,
        ),
        forbidden_outcomes={"debt_transfer_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-contract-transfer",
        title_ru="Передать договор без согласия всех сторон",
        facts=_facts(
            assignment_agreement_concluded=True,
            assignment_form_observed=True,
            debt_transfer_agreement_concluded=True,
            debt_transfer_form_observed=True,
            contract_transfer_agreed=True,
        ),
        forbidden_outcomes={"contract_transfer_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-improper-performance",
        title_ru="Прекратить обязательство ненадлежащим исполнением",
        facts=_facts(performance_rendered=True),
        forbidden_outcomes={"proper_performance_discharge": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-deposit-ground",
        title_ru="Прекратить долг депозитом без предусмотренного основания",
        facts=_facts(notary_or_court_deposit_made=True),
        forbidden_outcomes={"notary_deposit_discharge": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-accord-agreement",
        title_ru="Считать соглашение об отступном уже состоявшимся исполнением",
        facts=_facts(accord_agreed=True, accord_form_observed=True),
        forbidden_outcomes={"accord_discharge": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-setoff-no-declaration",
        title_ru="Провести зачет без заявления",
        facts=_facts(
            counterclaims_mutual=True,
            counterclaims_homogeneous=True,
            active_claim_due=True,
            passive_claim_due_or_early_allowed=True,
            set_off_amount_proven=True,
        ),
        forbidden_outcomes={"setoff_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-setoff-mutual",
        title_ru="Зачесть невстречные требования",
        facts=_facts(
            set_off_declared=True,
            set_off_notice_delivered=True,
            counterclaims_homogeneous=True,
            active_claim_due=True,
            passive_claim_due_or_early_allowed=True,
            set_off_amount_proven=True,
        ),
        forbidden_outcomes={"setoff_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-setoff-limit",
        title_ru="Зачесть активное требование с истекшей давностью",
        facts=_setoff(active_claim_limitation_expired=True),
        forbidden_outcomes={"setoff_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-novation-intent",
        title_ru="Вывести новацию без ясной воли заменить обязательство",
        facts=_facts(
            novation_agreed=True,
            new_subject_or_basis=True,
            new_obligation_terms_agreed=True,
            novation_form_observed=True,
        ),
        forbidden_outcomes={"novation_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-novation-term",
        title_ru="Признать простое изменение срока новацией",
        facts=_facts(
            novation_agreed=True,
            novation_intent_clear=True,
            new_obligation_terms_agreed=True,
            novation_form_observed=True,
        ),
        forbidden_outcomes={"novation_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-forgiveness-objection",
        title_ru="Проигнорировать возражение должника против прощения долга",
        facts=_facts(
            debt_forgiveness_declared=True,
            debt_forgiveness_notice_delivered=True,
            debtor_objected_forgiveness=True,
        ),
        forbidden_outcomes={"debt_forgiveness_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-forgiveness-third",
        title_ru="Прощением долга нарушить права третьего лица",
        facts=_facts(
            debt_forgiveness_declared=True,
            debt_forgiveness_notice_delivered=True,
            third_party_rights_prejudiced=True,
        ),
        forbidden_outcomes={"debt_forgiveness_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-commercial-gift",
        title_ru="Обойти запрет дарения между коммерческими организациями",
        facts=_facts(
            debt_forgiveness_declared=True,
            debt_forgiveness_notice_delivered=True,
            forgiveness_gift_intent=True,
            commercial_parties=True,
        ),
        forbidden_outcomes={"debt_forgiveness_effective": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-impossibility-risk",
        title_ru="Прекратить обязательство при риске невозможности на должнике",
        facts=_facts(
            objective_permanent_impossibility=True,
            impossibility_risk_on_debtor=True,
        ),
        forbidden_outcomes={"impossibility_discharge": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-impossibility-delay",
        title_ru="Освободить просрочившего должника из-за последующей невозможности",
        facts=_facts(
            objective_permanent_impossibility=True,
            debtor_in_delay_at_impossibility=True,
        ),
        forbidden_outcomes={"impossibility_discharge": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-government-restored",
        title_ru="Считать обязательство окончательно прекращенным после отмены акта",
        facts=_facts(
            government_act_prevents_performance=True,
            government_act_invalidated=True,
        ),
        forbidden_outcomes={"government_act_discharge": True},
    ),
    ObligationDynamicsRedTeamCase(
        id="dynamics-red-liquidation-successor",
        title_ru="Прекратить обязательство при предусмотренном правопреемнике",
        facts=_facts(
            legal_entity_liquidated=True,
            statutory_successor_exists=True,
        ),
        forbidden_outcomes={"liquidation_discharge": True},
    ),
)


def _evaluate(
    facts: ObligationDynamicsFactSet,
    artifact_id: str,
) -> ObligationDynamicsEvaluation:
    mapping = ObligationDynamicsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-obligation-dynamics-law"],
    )
    constraint_set = build_obligation_dynamics_constraint_set(mapping)
    return evaluate_obligation_dynamics_constraints(constraint_set, facts)


def _outcomes(
    evaluation: ObligationDynamicsEvaluation,
    names: dict[str, bool],
) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_obligation_dynamics_benchmark_suite() -> ObligationDynamicsBenchmarkReport:
    results = []
    for task in SYNTHETIC_OBLIGATION_DYNAMICS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ObligationDynamicsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ObligationDynamicsBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_obligation_dynamics_red_team_suite() -> ObligationDynamicsRedTeamReport:
    results = []
    for case in SYNTHETIC_OBLIGATION_DYNAMICS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ObligationDynamicsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ObligationDynamicsRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
