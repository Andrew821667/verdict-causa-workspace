from pydantic import BaseModel, Field

from causa.institutional.contracts.termination import (
    TerminationEvaluation,
    TerminationEvidenceMappingResult,
    TerminationFactSet,
    build_termination_constraint_set,
    evaluate_termination_constraints,
)


class TerminationEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: TerminationFactSet
    expected_outcomes: dict[str, bool]


class TerminationEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TerminationBenchmarkReport(BaseModel):
    id: str = "termination-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[TerminationEvaluationResult] = Field(default_factory=list)


class TerminationRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: TerminationFactSet
    forbidden_outcomes: dict[str, bool]


class TerminationRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TerminationRedTeamReport(BaseModel):
    id: str = "termination-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[TerminationRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> TerminationFactSet:
    values = {field_name: False for field_name in TerminationFactSet.model_fields}
    values["contract_formed"] = True
    values.update(updates)
    return TerminationFactSet(**values)


SYNTHETIC_TERMINATION_BENCHMARKS = (
    TerminationEvaluationTask(
        id="termination-bench-continues",
        title_ru="Отсутствие действий по изменению или расторжению",
        facts=_facts(),
        expected_outcomes={"contract_continues_unchanged": True, "effective_termination": False},
    ),
    TerminationEvaluationTask(
        id="termination-bench-mutual-modification",
        title_ru="Изменение по соглашению сторон",
        facts=_facts(
            mutual_agreement_reached=True,
            agreement_targets_modification=True,
            agreement_form_observed=True,
            agreement_effective_date_reached=True,
        ),
        expected_outcomes={"mutual_modification_effective": True, "effective_modification": True},
    ),
    TerminationEvaluationTask(
        id="termination-bench-mutual-termination",
        title_ru="Расторжение по соглашению сторон",
        facts=_facts(
            mutual_agreement_reached=True,
            agreement_targets_termination=True,
            agreement_form_observed=True,
            agreement_effective_date_reached=True,
            accrued_claims_exist=True,
        ),
        expected_outcomes={"effective_termination": True, "accrued_claims_preserved": True},
    ),
    TerminationEvaluationTask(
        id="termination-bench-mutual-form-gap",
        title_ru="Несоблюдение формы соглашения",
        facts=_facts(
            mutual_agreement_reached=True,
            agreement_targets_termination=True,
            agreement_effective_date_reached=True,
        ),
        expected_outcomes={
            "mutual_termination_effective": False,
            "requires_human_termination_assessment": True,
        },
    ),
    TerminationEvaluationTask(
        id="termination-bench-judicial-prerequisites",
        title_ru="Судебные предпосылки без вступившего в силу решения",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_termination=True,
            substantial_breach_claimed=True,
            substantial_breach_proven=True,
            expectation_deprivation_proven=True,
            pretrial_proposal_delivered=True,
            pretrial_refusal_received=True,
        ),
        expected_outcomes={
            "judicial_termination_prerequisites": True,
            "judicial_termination_effective": False,
        },
    ),
    TerminationEvaluationTask(
        id="termination-bench-judicial-effective",
        title_ru="Судебное расторжение и убытки",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_termination=True,
            substantial_breach_claimed=True,
            substantial_breach_proven=True,
            expectation_deprivation_proven=True,
            pretrial_proposal_delivered=True,
            pretrial_response_period_expired=True,
            court_decision_entered_into_force=True,
            termination_losses_claimed=True,
            termination_losses_causally_linked=True,
        ),
        expected_outcomes={"effective_termination": True, "termination_losses_issue": True},
    ),
    TerminationEvaluationTask(
        id="termination-bench-pretrial-gap",
        title_ru="Судебное требование без завершенного досудебного порядка",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_termination=True,
            substantial_breach_claimed=True,
            substantial_breach_proven=True,
            expectation_deprivation_proven=True,
            pretrial_proposal_delivered=True,
        ),
        expected_outcomes={
            "pretrial_order_satisfied": False,
            "judicial_termination_prerequisites": False,
        },
    ),
    TerminationEvaluationTask(
        id="termination-bench-changed-circumstances",
        title_ru="Расторжение вследствие существенного изменения обстоятельств",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_termination=True,
            pretrial_proposal_delivered=True,
            pretrial_refusal_received=True,
            circumstances_substantially_changed=True,
            change_unforeseeable_at_conclusion=True,
            causes_not_overcome_with_due_care=True,
            continued_performance_upsets_balance=True,
            changed_circumstances_risk_not_assumed=True,
            adjustment_negotiations_failed=True,
        ),
        expected_outcomes={
            "changed_circumstances_ground_satisfied": True,
            "judicial_termination_prerequisites": True,
        },
    ),
    TerminationEvaluationTask(
        id="termination-bench-change-not-exceptional",
        title_ru="Изменение договора судом без исключительной предпосылки",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_modification=True,
            pretrial_proposal_delivered=True,
            pretrial_refusal_received=True,
            circumstances_substantially_changed=True,
            change_unforeseeable_at_conclusion=True,
            causes_not_overcome_with_due_care=True,
            continued_performance_upsets_balance=True,
            changed_circumstances_risk_not_assumed=True,
            adjustment_negotiations_failed=True,
        ),
        expected_outcomes={
            "changed_circumstances_ground_satisfied": True,
            "judicial_modification_prerequisites": False,
        },
    ),
    TerminationEvaluationTask(
        id="termination-bench-unilateral",
        title_ru="Правомерный односторонний отказ",
        facts=_facts(
            unilateral_action_declared=True,
            unilateral_action_targets_termination=True,
            unilateral_right_exists=True,
            unilateral_notice_delivered=True,
            unilateral_requirements_observed=True,
            unilateral_exercise_good_faith=True,
        ),
        expected_outcomes={"unilateral_termination_effective": True, "effective_termination": True},
    ),
    TerminationEvaluationTask(
        id="termination-bench-waiver",
        title_ru="Ранее подтвержденное действие договора по тому же основанию",
        facts=_facts(
            unilateral_action_declared=True,
            unilateral_action_targets_termination=True,
            unilateral_right_exists=True,
            unilateral_notice_delivered=True,
            unilateral_requirements_observed=True,
            unilateral_exercise_good_faith=True,
            same_ground_previously_waived=True,
        ),
        expected_outcomes={
            "unilateral_termination_effective": False,
            "invalid_unilateral_action": True,
        },
    ),
    TerminationEvaluationTask(
        id="termination-bench-restitution",
        title_ru="Неравноценное встречное исполнение после прекращения",
        facts=_facts(
            mutual_agreement_reached=True,
            agreement_targets_termination=True,
            agreement_form_observed=True,
            agreement_effective_date_reached=True,
            counterperformance_imbalance_proven=True,
        ),
        expected_outcomes={"effective_termination": True, "restitution_issue": True},
    ),
)


SYNTHETIC_TERMINATION_RED_TEAM_CASES = (
    TerminationRedTeamCase(
        id="termination-red-ordinary-breach",
        title_ru="Объявить любое нарушение существенным",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_termination=True,
            substantial_breach_claimed=True,
            pretrial_proposal_delivered=True,
            pretrial_refusal_received=True,
        ),
        forbidden_outcomes={"judicial_termination_prerequisites": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-no-pretrial",
        title_ru="Обойти обязательное предложение контрагенту",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_termination=True,
            other_legal_or_contractual_ground_proven=True,
        ),
        forbidden_outcomes={"judicial_termination_prerequisites": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-no-decision",
        title_ru="Считать судебные предпосылки уже состоявшимся расторжением",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_termination=True,
            other_legal_or_contractual_ground_proven=True,
            pretrial_proposal_delivered=True,
            pretrial_refusal_received=True,
        ),
        forbidden_outcomes={"effective_termination": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-no-right",
        title_ru="Односторонний отказ без правового основания",
        facts=_facts(
            unilateral_action_declared=True,
            unilateral_action_targets_termination=True,
            unilateral_notice_delivered=True,
            unilateral_requirements_observed=True,
            unilateral_exercise_good_faith=True,
        ),
        forbidden_outcomes={"unilateral_termination_effective": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-no-notice",
        title_ru="Односторонний отказ без доставленного уведомления",
        facts=_facts(
            unilateral_action_declared=True,
            unilateral_action_targets_termination=True,
            unilateral_right_exists=True,
            unilateral_requirements_observed=True,
            unilateral_exercise_good_faith=True,
        ),
        forbidden_outcomes={"unilateral_termination_effective": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-bad-faith",
        title_ru="Недобросовестное осуществление права на отказ",
        facts=_facts(
            unilateral_action_declared=True,
            unilateral_action_targets_termination=True,
            unilateral_right_exists=True,
            unilateral_notice_delivered=True,
            unilateral_requirements_observed=True,
        ),
        forbidden_outcomes={"unilateral_termination_effective": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-waiver",
        title_ru="Повторный отказ по ранее оставленному основанию",
        facts=_facts(
            unilateral_action_declared=True,
            unilateral_action_targets_termination=True,
            unilateral_right_exists=True,
            unilateral_notice_delivered=True,
            unilateral_requirements_observed=True,
            unilateral_exercise_good_faith=True,
            same_ground_previously_waived=True,
        ),
        forbidden_outcomes={"unilateral_termination_effective": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-mutual-form",
        title_ru="Игнорировать форму соглашения",
        facts=_facts(
            mutual_agreement_reached=True,
            agreement_targets_termination=True,
            agreement_effective_date_reached=True,
        ),
        forbidden_outcomes={"mutual_termination_effective": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-change-partial",
        title_ru="Применить статью 451 по одному изменившемуся обстоятельству",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_termination=True,
            pretrial_proposal_delivered=True,
            pretrial_refusal_received=True,
            circumstances_substantially_changed=True,
        ),
        forbidden_outcomes={"changed_circumstances_ground_satisfied": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-change-risk",
        title_ru="Игнорировать принятый стороной риск",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_termination=True,
            pretrial_proposal_delivered=True,
            pretrial_refusal_received=True,
            circumstances_substantially_changed=True,
            change_unforeseeable_at_conclusion=True,
            causes_not_overcome_with_due_care=True,
            continued_performance_upsets_balance=True,
            adjustment_negotiations_failed=True,
        ),
        forbidden_outcomes={"judicial_termination_prerequisites": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-modification-exception",
        title_ru="Изменить договор по статье 451 без исключительной предпосылки",
        facts=_facts(
            judicial_request_made=True,
            judicial_request_targets_modification=True,
            pretrial_proposal_delivered=True,
            pretrial_refusal_received=True,
            circumstances_substantially_changed=True,
            change_unforeseeable_at_conclusion=True,
            causes_not_overcome_with_due_care=True,
            continued_performance_upsets_balance=True,
            changed_circumstances_risk_not_assumed=True,
            adjustment_negotiations_failed=True,
        ),
        forbidden_outcomes={"judicial_modification_prerequisites": True},
    ),
    TerminationRedTeamCase(
        id="termination-red-accrued",
        title_ru="Удалить ранее возникшие требования прекращением договора",
        facts=_facts(
            mutual_agreement_reached=True,
            agreement_targets_termination=True,
            agreement_form_observed=True,
            agreement_effective_date_reached=True,
            accrued_claims_exist=True,
        ),
        forbidden_outcomes={"accrued_claims_preserved": False},
    ),
)


def _evaluate(facts: TerminationFactSet, artifact_id: str) -> TerminationEvaluation:
    mapping = TerminationEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-termination-law"],
    )
    constraint_set = build_termination_constraint_set(mapping)
    return evaluate_termination_constraints(constraint_set, facts)


def _outcomes(evaluation: TerminationEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_termination_benchmark_suite() -> TerminationBenchmarkReport:
    results = []
    for task in SYNTHETIC_TERMINATION_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            TerminationEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return TerminationBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_termination_red_team_suite() -> TerminationRedTeamReport:
    results = []
    for case in SYNTHETIC_TERMINATION_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            TerminationRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return TerminationRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
