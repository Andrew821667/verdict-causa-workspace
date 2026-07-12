from pydantic import BaseModel, Field

from causa.institutional.contracts.formation import (
    FormationConstraintSet,
    FormationEvaluation,
    FormationEvidenceMappingResult,
    FormationFactSet,
    build_formation_constraint_set,
    evaluate_formation_constraints,
)


class FormationEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: FormationFactSet
    expected_outcomes: dict[str, bool]


class FormationEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FormationBenchmarkReport(BaseModel):
    id: str = "formation-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[FormationEvaluationResult] = Field(default_factory=list)


class FormationRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: FormationFactSet
    forbidden_outcomes: dict[str, bool]


class FormationRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FormationRedTeamReport(BaseModel):
    id: str = "formation-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[FormationRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> FormationFactSet:
    values = {field_name: False for field_name in FormationFactSet.model_fields}
    values.update(
        proposal_made=True,
        proposal_addressed_to_counterparty=True,
        intent_to_be_bound=True,
        subject_matter_defined_in_offer=True,
        statutory_essential_terms_defined_in_offer=True,
        party_declared_essential_terms_defined_in_offer=True,
        required_form_observed=True,
        acceptance_within_period=True,
    )
    values.update(updates)
    return FormationFactSet(**values)


SYNTHETIC_FORMATION_BENCHMARKS = (
    FormationEvaluationTask(
        id="formation-bench-express",
        title_ru="Полный безоговорочный акцепт",
        facts=_facts(acceptance_received=True, acceptance_full_and_unconditional=True),
        expected_outcomes={
            "contract_concluded_prerequisites": True,
            "express_acceptance_valid": True,
        },
    ),
    FormationEvaluationTask(
        id="formation-bench-conduct",
        title_ru="Акцепт действиями",
        facts=_facts(acceptance_by_conduct=True, performance_conduct_started_in_time=True),
        expected_outcomes={
            "contract_concluded_prerequisites": True,
            "conduct_acceptance_valid": True,
        },
    ),
    FormationEvaluationTask(
        id="formation-bench-silence-basis",
        title_ru="Молчание при наличии специального основания",
        facts=_facts(silence_only=True, silence_acceptance_basis_exists=True),
        expected_outcomes={
            "contract_concluded_prerequisites": True,
            "silence_acceptance_valid": True,
        },
    ),
    FormationEvaluationTask(
        id="formation-bench-silence-no-basis",
        title_ru="Молчание без специального основания",
        facts=_facts(silence_only=True),
        expected_outcomes={
            "contract_concluded_prerequisites": False,
            "silence_acceptance_valid": False,
        },
    ),
    FormationEvaluationTask(
        id="formation-bench-subject-gap",
        title_ru="Предмет не определен в оферте",
        facts=_facts(
            subject_matter_defined_in_offer=False,
            acceptance_received=True,
            acceptance_full_and_unconditional=True,
        ),
        expected_outcomes={"valid_offer": False, "contract_concluded_prerequisites": False},
    ),
    FormationEvaluationTask(
        id="formation-bench-declared-term-gap",
        title_ru="Заявленное существенное условие не определено в оферте",
        facts=_facts(
            party_declared_essential_terms_defined_in_offer=False,
            acceptance_received=True,
            acceptance_full_and_unconditional=True,
        ),
        expected_outcomes={
            "essential_terms_agreed": False,
            "contract_concluded_prerequisites": False,
        },
    ),
    FormationEvaluationTask(
        id="formation-bench-counteroffer",
        title_ru="Ответ на иных условиях",
        facts=_facts(acceptance_received=True, acceptance_on_other_terms=True),
        expected_outcomes={
            "counteroffer_detected": True,
            "contract_concluded_prerequisites": False,
        },
    ),
    FormationEvaluationTask(
        id="formation-bench-late",
        title_ru="Просроченный акцепт",
        facts=_facts(
            acceptance_received=True,
            acceptance_full_and_unconditional=True,
            acceptance_within_period=False,
        ),
        expected_outcomes={
            "express_acceptance_valid": False,
            "contract_concluded_prerequisites": False,
        },
    ),
    FormationEvaluationTask(
        id="formation-bench-form",
        title_ru="Не соблюдена требуемая форма",
        facts=_facts(
            required_form_observed=False,
            acceptance_received=True,
            acceptance_full_and_unconditional=True,
        ),
        expected_outcomes={
            "express_acceptance_valid": True,
            "contract_concluded_prerequisites": False,
        },
    ),
    FormationEvaluationTask(
        id="formation-bench-bad-faith-objection",
        title_ru="Принятое исполнение и недобросовестное возражение",
        facts=_facts(
            acceptance_by_conduct=True,
            performance_conduct_started_in_time=True,
            performance_accepted_without_objection=True,
            bad_faith_non_conclusion_objection=True,
        ),
        expected_outcomes={
            "contract_concluded_prerequisites": True,
            "non_conclusion_objection_barred": True,
            "requires_human_formation_assessment": True,
        },
    ),
)


SYNTHETIC_FORMATION_RED_TEAM_CASES = (
    FormationRedTeamCase(
        id="formation-red-silence",
        title_ru="Принудительно признать обычное молчание акцептом",
        facts=_facts(silence_only=True),
        forbidden_outcomes={"contract_concluded_prerequisites": True},
    ),
    FormationRedTeamCase(
        id="formation-red-conditional",
        title_ru="Признать условный ответ полным акцептом",
        facts=_facts(acceptance_received=True),
        forbidden_outcomes={"express_acceptance_valid": True},
    ),
    FormationRedTeamCase(
        id="formation-red-other-terms",
        title_ru="Игнорировать встречную оферту",
        facts=_facts(acceptance_received=True, acceptance_on_other_terms=True),
        forbidden_outcomes={"contract_concluded_prerequisites": True},
    ),
    FormationRedTeamCase(
        id="formation-red-no-subject",
        title_ru="Заключить договор без предмета",
        facts=_facts(
            subject_matter_defined_in_offer=False,
            acceptance_received=True,
            acceptance_full_and_unconditional=True,
        ),
        forbidden_outcomes={"valid_offer": True},
    ),
    FormationRedTeamCase(
        id="formation-red-no-form",
        title_ru="Игнорировать обязательную форму",
        facts=_facts(
            required_form_observed=False,
            acceptance_received=True,
            acceptance_full_and_unconditional=True,
        ),
        forbidden_outcomes={"contract_concluded_prerequisites": True},
    ),
    FormationRedTeamCase(
        id="formation-red-no-intent",
        title_ru="Принять переговорное сообщение за оферту",
        facts=_facts(
            intent_to_be_bound=False,
            acceptance_received=True,
            acceptance_full_and_unconditional=True,
        ),
        forbidden_outcomes={"valid_offer": True},
    ),
    FormationRedTeamCase(
        id="formation-red-late-conduct",
        title_ru="Принять просроченные действия",
        facts=_facts(acceptance_by_conduct=True),
        forbidden_outcomes={"conduct_acceptance_valid": True},
    ),
    FormationRedTeamCase(
        id="formation-red-unaddressed",
        title_ru="Признать неадресованное предложение офертой",
        facts=_facts(
            proposal_addressed_to_counterparty=False,
            acceptance_received=True,
            acceptance_full_and_unconditional=True,
        ),
        forbidden_outcomes={"valid_offer": True},
    ),
    FormationRedTeamCase(
        id="formation-red-negotiations",
        title_ru="Вывести акцепт только из переговоров",
        facts=_facts(),
        forbidden_outcomes={"contract_concluded_prerequisites": True},
    ),
    FormationRedTeamCase(
        id="formation-red-bad-faith",
        title_ru="Пропустить недобросовестное возражение",
        facts=_facts(
            subject_matter_defined_in_offer=False,
            performance_accepted_without_objection=True,
            bad_faith_non_conclusion_objection=True,
        ),
        forbidden_outcomes={"non_conclusion_objection_barred": False},
    ),
)


def _evaluate(facts: FormationFactSet, artifact_id: str) -> FormationEvaluation:
    mapping = FormationEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-formation-law"],
    )
    constraints: FormationConstraintSet = build_formation_constraint_set(mapping)
    return evaluate_formation_constraints(constraints, facts)


def _outcomes(evaluation: FormationEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_formation_benchmark_suite() -> FormationBenchmarkReport:
    results = []
    for task in SYNTHETIC_FORMATION_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            FormationEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return FormationBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_formation_red_team_suite() -> FormationRedTeamReport:
    results = []
    for case in SYNTHETIC_FORMATION_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            FormationRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return FormationRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
