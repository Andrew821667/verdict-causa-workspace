"""Benchmark и red-team для модели решений собраний (глава 9.1 ГК РФ)."""

from pydantic import BaseModel, Field

from causa.institutional.contracts.meeting_decisions import (
    MeetingDecisionsConstraintSet,
    MeetingDecisionsEvaluation,
    MeetingDecisionsEvidenceMappingResult,
    MeetingDecisionsFactSet,
    build_meeting_decisions_constraint_set,
    evaluate_meeting_decisions_constraints,
)


class MeetingDecisionsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: MeetingDecisionsFactSet
    expected_outcomes: dict[str, bool]


class MeetingDecisionsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class MeetingDecisionsBenchmarkReport(BaseModel):
    id: str = "meeting-decisions-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[MeetingDecisionsEvaluationResult] = Field(default_factory=list)


class MeetingDecisionsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: MeetingDecisionsFactSet
    forbidden_outcomes: dict[str, bool]


class MeetingDecisionsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class MeetingDecisionsRedTeamReport(BaseModel):
    id: str = "meeting-decisions-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[MeetingDecisionsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> MeetingDecisionsFactSet:
    values = {field_name: False for field_name in MeetingDecisionsFactSet.model_fields}
    values.update(updates)
    return MeetingDecisionsFactSet(**values)


#: Правомерно принятое решение: кворум есть, большинство есть, пороков нет.
_LAWFUL = {
    "meeting_decision_asserted": True,
    "quorum_present": True,
    "required_majority_obtained": True,
}


SYNTHETIC_MEETING_DECISIONS_BENCHMARKS = (
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-not-qualified",
        title_ru="Решение собрания в деле не заявлено",
        facts=_facts(question_outside_competence=True),
        expected_outcomes={
            "meeting_decision_qualified": False,
            "decision_void": False,
            "requires_human_meeting_decision_assessment": False,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-lawful-decision-binds-all",
        title_ru="Правомерное решение обязательно для всех участников",
        facts=_facts(**_LAWFUL),
        expected_outcomes={
            "decision_binds_all_participants": True,
            "decision_void": False,
            "decision_voidable": False,
            "requires_human_meeting_decision_assessment": False,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-no-majority-means-no-decision",
        title_ru="Большинство не набрано: решение не принято",
        facts=_facts(meeting_decision_asserted=True, quorum_present=True),
        expected_outcomes={
            "decision_not_adopted": True,
            "decision_void": False,
            "decision_binds_all_participants": False,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-no-quorum-is-void",
        title_ru="Нет кворума: решение ничтожно",
        facts=_facts(meeting_decision_asserted=True, required_majority_obtained=True),
        expected_outcomes={
            "quorum_absent": True,
            "decision_void": True,
            "decision_binds_all_participants": False,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-outside-agenda-is-void",
        title_ru="Вопрос вне повестки при неполном участии: ничтожность",
        facts=_facts(**_LAWFUL, question_outside_agenda=True),
        expected_outcomes={
            "agenda_violation_void": True,
            "decision_void": True,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-outside-agenda-cured-by-full-participation",
        title_ru="Вопрос вне повестки, но участвовали все: ничтожности нет",
        facts=_facts(**_LAWFUL, question_outside_agenda=True, all_participants_took_part=True),
        expected_outcomes={
            "agenda_violation_void": False,
            "decision_void": False,
            "decision_binds_all_participants": True,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-outside-competence-is-void",
        title_ru="Вопрос вне компетенции собрания: ничтожность",
        facts=_facts(**_LAWFUL, question_outside_competence=True),
        expected_outcomes={"competence_violation_void": True, "decision_void": True},
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-public-order-is-void",
        title_ru="Противоречие основам правопорядка: ничтожность",
        facts=_facts(**_LAWFUL, contrary_to_public_order_or_morality=True),
        expected_outcomes={"public_order_violation_void": True, "decision_void": True},
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-procedure-breach-is-voidable",
        title_ru="Нарушен порядок созыва: решение оспоримо",
        facts=_facts(**_LAWFUL, convocation_or_conduct_procedure_breached=True),
        expected_outcomes={
            "procedural_defect_established": True,
            "decision_voidable": True,
            "decision_void": False,
            "decision_binds_all_participants": True,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-equality-breach-is-voidable",
        title_ru="Нарушено равенство прав участников: решение оспоримо",
        facts=_facts(**_LAWFUL, participant_equality_breached=True),
        expected_outcomes={"decision_voidable": True, "decision_void": False},
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-immateriality-cures-voidability",
        title_ru="Голос не мог повлиять и вреда нет: оспоримость снята",
        facts=_facts(
            **_LAWFUL,
            minutes_requirements_breached=True,
            vote_could_not_affect_outcome=True,
            no_material_adverse_consequences=True,
        ),
        expected_outcomes={
            "voidability_cured_by_immateriality": True,
            "decision_voidable": False,
            "decision_binds_all_participants": True,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-confirmation-cures-voidability",
        title_ru="Решение подтверждено последующим: оспоримость снята",
        facts=_facts(
            **_LAWFUL,
            representative_authority_defect=True,
            decision_confirmed_by_later_decision=True,
        ),
        expected_outcomes={
            "voidability_cured_by_confirmation": True,
            "decision_voidable": False,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-lawful-decision-binds-the-term",
        title_ru="Условие держится на действительном решении: обязательно для всех",
        facts=_facts(**_LAWFUL, meeting_decision_underpins_contract_term=True),
        expected_outcomes={
            "contract_term_binds_all_participants": True,
            "contract_term_lacks_meeting_basis": False,
            "contract_term_basis_voidable": False,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-void-decision-strips-the-term",
        title_ru="Условие держится на ничтожном решении: основания нет",
        facts=_facts(
            **_LAWFUL,
            contrary_to_public_order_or_morality=True,
            meeting_decision_underpins_contract_term=True,
        ),
        expected_outcomes={
            "contract_term_lacks_meeting_basis": True,
            "contract_term_binds_all_participants": False,
            "requires_human_meeting_decision_assessment": True,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-unadopted-decision-strips-the-term",
        title_ru="Условие держится на непринятом решении: основания нет",
        facts=_facts(
            meeting_decision_asserted=True,
            quorum_present=True,
            meeting_decision_underpins_contract_term=True,
        ),
        expected_outcomes={
            "decision_not_adopted": True,
            "contract_term_lacks_meeting_basis": True,
            "contract_term_binds_all_participants": False,
        },
    ),
    MeetingDecisionsEvaluationTask(
        id="meeting-bench-voidable-decision-keeps-the-term",
        title_ru="Решение оспоримо: условие действует, но основание спорно",
        facts=_facts(
            **_LAWFUL,
            participant_equality_breached=True,
            meeting_decision_underpins_contract_term=True,
        ),
        expected_outcomes={
            "contract_term_basis_voidable": True,
            "contract_term_lacks_meeting_basis": False,
            "contract_term_binds_all_participants": True,
        },
    ),
)


SYNTHETIC_MEETING_DECISIONS_RED_TEAM_CASES = (
    MeetingDecisionsRedTeamCase(
        id="meeting-red-void-without-decision",
        title_ru="Ничтожность решения при незаявленном решении собрания",
        facts=_facts(question_outside_competence=True, contrary_to_public_order_or_morality=True),
        forbidden_outcomes={"decision_void": True},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-immateriality-cures-nullity",
        title_ru="Несущественность выдана за исцеление ничтожности",
        facts=_facts(
            meeting_decision_asserted=True,
            required_majority_obtained=True,
            convocation_or_conduct_procedure_breached=True,
            vote_could_not_affect_outcome=True,
            no_material_adverse_consequences=True,
        ),
        forbidden_outcomes={"decision_void": False},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-confirmation-cures-nullity",
        title_ru="Подтверждение последующим решением выдано за исцеление ничтожности",
        facts=_facts(
            **_LAWFUL,
            question_outside_competence=True,
            minutes_requirements_breached=True,
            decision_confirmed_by_later_decision=True,
        ),
        forbidden_outcomes={"decision_void": False},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-void-decision-still-binds",
        title_ru="Ничтожное решение признано обязательным для участников",
        facts=_facts(**_LAWFUL, contrary_to_public_order_or_morality=True),
        forbidden_outcomes={"decision_binds_all_participants": True},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-voidable-and-void-at-once",
        title_ru="Одно решение объявлено и ничтожным, и оспоримым",
        facts=_facts(
            **_LAWFUL,
            question_outside_competence=True,
            participant_equality_breached=True,
        ),
        forbidden_outcomes={"decision_voidable": True},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-agenda-void-despite-full-participation",
        title_ru="Ничтожность по повестке вопреки участию всех",
        facts=_facts(**_LAWFUL, question_outside_agenda=True, all_participants_took_part=True),
        forbidden_outcomes={"agenda_violation_void": True},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-immateriality-without-defect",
        title_ru="Оговорка о несущественности без установленного нарушения",
        facts=_facts(
            **_LAWFUL,
            vote_could_not_affect_outcome=True,
            no_material_adverse_consequences=True,
        ),
        forbidden_outcomes={"voidability_cured_by_immateriality": True},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-half-immateriality-cures",
        title_ru="Половина оговорки о несущественности снимает оспоримость",
        facts=_facts(
            **_LAWFUL, minutes_requirements_breached=True, vote_could_not_affect_outcome=True
        ),
        forbidden_outcomes={"voidability_cured_by_immateriality": True, "decision_voidable": False},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-unadopted-decision-binds",
        title_ru="Непринятое решение признано обязательным",
        facts=_facts(meeting_decision_asserted=True, quorum_present=True),
        forbidden_outcomes={"decision_binds_all_participants": True},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-procedure-defect-without-decision",
        title_ru="Нарушение порядка при незаявленном решении собрания",
        facts=_facts(participant_equality_breached=True, minutes_requirements_breached=True),
        forbidden_outcomes={"procedural_defect_established": True, "decision_voidable": True},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-term-loses-basis-without-the-link",
        title_ru="Условие лишено основания при незаявленной связи с решением",
        facts=_facts(**_LAWFUL, contrary_to_public_order_or_morality=True),
        forbidden_outcomes={"contract_term_lacks_meeting_basis": True},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-voidable-decision-strips-the-term",
        title_ru="Оспоримость решения выдана за отсутствие основания у условия",
        facts=_facts(
            **_LAWFUL,
            minutes_requirements_breached=True,
            meeting_decision_underpins_contract_term=True,
        ),
        forbidden_outcomes={"contract_term_lacks_meeting_basis": True},
    ),
    MeetingDecisionsRedTeamCase(
        id="meeting-red-void-decision-still-binds-the-term",
        title_ru="Условие на ничтожном решении признано обязательным для всех",
        facts=_facts(
            **_LAWFUL,
            question_outside_competence=True,
            meeting_decision_underpins_contract_term=True,
        ),
        forbidden_outcomes={"contract_term_binds_all_participants": True},
    ),
)


def _evaluate(facts: MeetingDecisionsFactSet, artifact_id: str) -> MeetingDecisionsEvaluation:
    mapping = MeetingDecisionsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-meeting-decisions-law"],
    )
    constraints: MeetingDecisionsConstraintSet = build_meeting_decisions_constraint_set(mapping)
    return evaluate_meeting_decisions_constraints(constraints, facts)


def _outcomes(evaluation: MeetingDecisionsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_meeting_decisions_benchmark_suite() -> MeetingDecisionsBenchmarkReport:
    results = []
    for task in SYNTHETIC_MEETING_DECISIONS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            MeetingDecisionsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return MeetingDecisionsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_meeting_decisions_red_team_suite() -> MeetingDecisionsRedTeamReport:
    results = []
    for case in SYNTHETIC_MEETING_DECISIONS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            MeetingDecisionsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return MeetingDecisionsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
