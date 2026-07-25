from pydantic import BaseModel, Field

from causa.institutional.contracts.preliminary import (
    PreliminaryConstraintSet,
    PreliminaryEvaluation,
    PreliminaryEvidenceMappingResult,
    PreliminaryFactSet,
    build_preliminary_constraint_set,
    evaluate_preliminary_constraints,
)


class PreliminaryEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: PreliminaryFactSet
    expected_outcomes: dict[str, bool]


class PreliminaryEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PreliminaryBenchmarkReport(BaseModel):
    id: str = "preliminary-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[PreliminaryEvaluationResult] = Field(default_factory=list)


class PreliminaryRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: PreliminaryFactSet
    forbidden_outcomes: dict[str, bool]


class PreliminaryRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PreliminaryRedTeamReport(BaseModel):
    id: str = "preliminary-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[PreliminaryRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> PreliminaryFactSet:
    values = {field_name: False for field_name in PreliminaryFactSet.model_fields}
    values.update(updates)
    return PreliminaryFactSet(**values)


SYNTHETIC_PRELIMINARY_BENCHMARKS = (
    PreliminaryEvaluationTask(
        id="preliminary-bench-valid-active",
        title_ru="Действительный предварительный договор, обязанность заключить сохраняется",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            within_conclusion_term=True,
        ),
        expected_outcomes={
            "preliminary_contract_valid": True,
            "conclusion_obligation_active": True,
            "requires_human_preliminary_assessment": False,
        },
    ),
    PreliminaryEvaluationTask(
        id="preliminary-bench-form-void",
        title_ru="Несоблюдение формы влечет ничтожность предварительного договора",
        facts=_facts(
            preliminary_contract_concluded=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
        ),
        expected_outcomes={
            "preliminary_form_void": True,
            "preliminary_contract_valid": False,
            "requires_human_preliminary_assessment": True,
        },
    ),
    PreliminaryEvaluationTask(
        id="preliminary-bench-subject-undefined",
        title_ru="Предмет основного договора не определен",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            disputed_terms_agreed=True,
            within_conclusion_term=True,
        ),
        expected_outcomes={"preliminary_contract_valid": False},
    ),
    PreliminaryEvaluationTask(
        id="preliminary-bench-disputed-terms-open",
        title_ru="Не согласованы условия, о которых заявлено требование стороны",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            within_conclusion_term=True,
        ),
        expected_outcomes={"preliminary_contract_valid": False},
    ),
    PreliminaryEvaluationTask(
        id="preliminary-bench-compulsion",
        title_ru="Уклонение и своевременное требование дают понуждение и убытки",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            within_conclusion_term=True,
            party_evades_conclusion=True,
            demand_to_conclude_made=True,
            demand_within_six_months=True,
        ),
        expected_outcomes={
            "compulsion_to_conclude_available": True,
            "damages_for_evasion_available": True,
        },
    ),
    PreliminaryEvaluationTask(
        id="preliminary-bench-demand-late",
        title_ru="Требование о понуждении заявлено за пределами шести месяцев",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            party_evades_conclusion=True,
            demand_to_conclude_made=True,
        ),
        expected_outcomes={
            "compulsion_to_conclude_available": False,
            "requires_human_preliminary_assessment": True,
        },
    ),
    PreliminaryEvaluationTask(
        id="preliminary-bench-terminated",
        title_ru="Обязательства прекращены истечением срока без заключения основного",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
        ),
        expected_outcomes={
            "preliminary_obligations_terminated": True,
            "conclusion_obligation_active": False,
        },
    ),
    PreliminaryEvaluationTask(
        id="preliminary-bench-main-concluded",
        title_ru="Основной договор заключен: обязанность исполнена, прекращения по сроку нет",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            within_conclusion_term=True,
            main_contract_concluded_or_proposal_made=True,
        ),
        expected_outcomes={
            "conclusion_obligation_active": False,
            "preliminary_obligations_terminated": False,
        },
    ),
    PreliminaryEvaluationTask(
        id="preliminary-bench-evasion-no-demand",
        title_ru="Уклонение без заявленного требования не дает понуждения",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            within_conclusion_term=True,
            party_evades_conclusion=True,
        ),
        expected_outcomes={
            "compulsion_to_conclude_available": False,
            "requires_human_preliminary_assessment": True,
        },
    ),
    PreliminaryEvaluationTask(
        id="preliminary-bench-valid-no-remedy",
        title_ru="Действительный договор без уклонения не порождает убытков",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            within_conclusion_term=True,
        ),
        expected_outcomes={
            "damages_for_evasion_available": False,
            "requires_human_preliminary_assessment": False,
        },
    ),
)


SYNTHETIC_PRELIMINARY_RED_TEAM_CASES = (
    PreliminaryRedTeamCase(
        id="preliminary-red-void-as-valid",
        title_ru="Признать предварительный договор действительным при несоблюдении формы",
        facts=_facts(
            preliminary_contract_concluded=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
        ),
        forbidden_outcomes={"preliminary_contract_valid": True},
    ),
    PreliminaryRedTeamCase(
        id="preliminary-red-skip-human-on-void",
        title_ru="Пропустить экспертную проверку при ничтожности формы",
        facts=_facts(
            preliminary_contract_concluded=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
        ),
        forbidden_outcomes={"requires_human_preliminary_assessment": False},
    ),
    PreliminaryRedTeamCase(
        id="preliminary-red-compulsion-late-demand",
        title_ru="Дать понуждение при требовании за пределами шести месяцев",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            party_evades_conclusion=True,
            demand_to_conclude_made=True,
        ),
        forbidden_outcomes={"compulsion_to_conclude_available": True},
    ),
    PreliminaryRedTeamCase(
        id="preliminary-red-compulsion-no-demand",
        title_ru="Дать понуждение без заявленного требования",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            party_evades_conclusion=True,
        ),
        forbidden_outcomes={"compulsion_to_conclude_available": True},
    ),
    PreliminaryRedTeamCase(
        id="preliminary-red-damages-without-evasion",
        title_ru="Взыскать убытки за уклонение при отсутствии уклонения",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            within_conclusion_term=True,
        ),
        forbidden_outcomes={"damages_for_evasion_available": True},
    ),
    PreliminaryRedTeamCase(
        id="preliminary-red-obligation-after-expiry",
        title_ru="Сохранить обязанность заключить основной договор после истечения срока",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
        ),
        forbidden_outcomes={"conclusion_obligation_active": True},
    ),
    PreliminaryRedTeamCase(
        id="preliminary-red-terminate-with-main",
        title_ru="Считать обязательства прекращенными при заключенном основном договоре",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            main_contract_concluded_or_proposal_made=True,
        ),
        forbidden_outcomes={"preliminary_obligations_terminated": True},
    ),
    PreliminaryRedTeamCase(
        id="preliminary-red-valid-without-subject",
        title_ru="Признать договор действительным без определенного предмета",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            disputed_terms_agreed=True,
            within_conclusion_term=True,
        ),
        forbidden_outcomes={"preliminary_contract_valid": True},
    ),
    PreliminaryRedTeamCase(
        id="preliminary-red-compulsion-on-void",
        title_ru="Дать понуждение при ничтожном предварительном договоре",
        facts=_facts(
            preliminary_contract_concluded=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            party_evades_conclusion=True,
            demand_to_conclude_made=True,
            demand_within_six_months=True,
        ),
        forbidden_outcomes={"compulsion_to_conclude_available": True},
    ),
    PreliminaryRedTeamCase(
        id="preliminary-red-skip-human-late-demand",
        title_ru="Пропустить экспертную проверку при уклонении и пропущенном сроке требования",
        facts=_facts(
            preliminary_contract_concluded=True,
            form_requirement_observed=True,
            main_contract_subject_defined=True,
            disputed_terms_agreed=True,
            party_evades_conclusion=True,
            demand_to_conclude_made=True,
        ),
        forbidden_outcomes={"requires_human_preliminary_assessment": False},
    ),
)


def _evaluate(facts: PreliminaryFactSet, artifact_id: str) -> PreliminaryEvaluation:
    mapping = PreliminaryEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-preliminary-law"],
    )
    constraints: PreliminaryConstraintSet = build_preliminary_constraint_set(mapping)
    return evaluate_preliminary_constraints(constraints, facts)


def _outcomes(evaluation: PreliminaryEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_preliminary_benchmark_suite() -> PreliminaryBenchmarkReport:
    results = []
    for task in SYNTHETIC_PRELIMINARY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            PreliminaryEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return PreliminaryBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_preliminary_red_team_suite() -> PreliminaryRedTeamReport:
    results = []
    for case in SYNTHETIC_PRELIMINARY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            PreliminaryRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return PreliminaryRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
