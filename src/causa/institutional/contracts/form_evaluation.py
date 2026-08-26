from pydantic import BaseModel, Field

from causa.institutional.contracts.form import (
    FormConstraintSet,
    FormEvaluation,
    FormEvidenceMappingResult,
    FormFactSet,
    build_form_constraint_set,
    evaluate_form_constraints,
)


class FormEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: FormFactSet
    expected_outcomes: dict[str, bool]


class FormEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FormBenchmarkReport(BaseModel):
    id: str = "form-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[FormEvaluationResult] = Field(default_factory=list)


class FormRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: FormFactSet
    forbidden_outcomes: dict[str, bool]


class FormRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FormRedTeamReport(BaseModel):
    id: str = "form-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[FormRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> FormFactSet:
    values = {field_name: False for field_name in FormFactSet.model_fields}
    values.update(updates)
    return FormFactSet(**values)


SYNTHETIC_FORM_BENCHMARKS = (
    FormEvaluationTask(
        id="form-bench-written-signed",
        title_ru="Простая письменная форма соблюдена подписанным документом",
        facts=_facts(
            simple_written_form_required=True,
            simple_written_form_observed=True,
            document_signed_by_parties=True,
        ),
        expected_outcomes={
            "form_requirement_satisfied": True,
            "transaction_void_for_form": False,
        },
    ),
    FormEvaluationTask(
        id="form-bench-written-exchange",
        title_ru="Письменная форма соблюдена обменом документами",
        facts=_facts(
            simple_written_form_required=True,
            simple_written_form_observed=True,
            exchange_of_documents=True,
        ),
        expected_outcomes={"form_requirement_satisfied": True},
    ),
    FormEvaluationTask(
        id="form-bench-written-electronic",
        title_ru="Письменная форма соблюдена электронной подписью",
        facts=_facts(
            simple_written_form_required=True,
            simple_written_form_observed=True,
            electronic_signature_valid=True,
        ),
        expected_outcomes={"form_requirement_satisfied": True},
    ),
    FormEvaluationTask(
        id="form-bench-written-missing",
        title_ru="Письменная форма не соблюдена",
        facts=_facts(simple_written_form_required=True),
        expected_outcomes={
            "witness_testimony_barred": True,
            "transaction_void_for_form": False,
            "form_requirement_satisfied": False,
        },
    ),
    FormEvaluationTask(
        id="form-bench-written-void",
        title_ru="Несоблюдение письменной формы влечет недействительность по закону",
        facts=_facts(
            simple_written_form_required=True,
            written_noncompliance_invalidates_by_law_or_agreement=True,
        ),
        expected_outcomes={"transaction_void_for_form": True},
    ),
    FormEvaluationTask(
        id="form-bench-notarial-observed",
        title_ru="Нотариальная форма соблюдена",
        facts=_facts(
            simple_written_form_required=True,
            notarial_form_required=True,
            simple_written_form_observed=True,
            document_signed_by_parties=True,
            notarial_form_observed=True,
        ),
        expected_outcomes={"form_requirement_satisfied": True},
    ),
    FormEvaluationTask(
        id="form-bench-notarial-missing",
        title_ru="Нотариальная форма не соблюдена",
        facts=_facts(
            simple_written_form_required=True,
            notarial_form_required=True,
            simple_written_form_observed=True,
            document_signed_by_parties=True,
        ),
        expected_outcomes={"transaction_void_for_form": True},
    ),
    FormEvaluationTask(
        id="form-bench-oral",
        title_ru="Допустимая устная форма сделки",
        facts=_facts(oral_form_permitted=True),
        expected_outcomes={
            "oral_form_valid": True,
            "form_requirement_satisfied": True,
        },
    ),
    FormEvaluationTask(
        id="form-bench-written-no-method",
        title_ru="Письменная форма заявлена без действительного способа",
        facts=_facts(
            simple_written_form_required=True,
            simple_written_form_observed=True,
        ),
        expected_outcomes={
            "written_form_satisfied": False,
            "form_requirement_satisfied": False,
        },
    ),
    FormEvaluationTask(
        id="form-bench-written-proof",
        title_ru="Несоблюдение письменной формы при наличии письменных доказательств",
        facts=_facts(
            simple_written_form_required=True,
            performance_or_written_proof_available=True,
        ),
        expected_outcomes={
            "witness_testimony_barred": True,
            "requires_human_form_assessment": False,
        },
    ),
    FormEvaluationTask(
        id="form-bench-acceptance-by-conduct",
        title_ru="Письменная оферта принята действиями по выполнению её условий",
        facts=_facts(
            simple_written_form_required=True,
            written_offer_made=True,
            offer_terms_performed_as_acceptance=True,
        ),
        expected_outcomes={
            "acceptance_by_conduct_observes_written_form": True,
            "written_form_satisfied": True,
            "form_requirement_satisfied": True,
            "transaction_void_for_form": False,
        },
    ),
    FormEvaluationTask(
        id="form-bench-conduct-without-written-offer",
        title_ru="Действия совершены, но письменной оферты не было",
        facts=_facts(simple_written_form_required=True, written_offer_made=True),
        expected_outcomes={
            "acceptance_by_conduct_observes_written_form": False,
            "written_form_satisfied": False,
        },
    ),
)


SYNTHETIC_FORM_RED_TEAM_CASES = (
    FormRedTeamCase(
        id="form-red-written-no-method",
        title_ru="Признать письменную форму соблюденной без действительного способа",
        facts=_facts(simple_written_form_required=True, simple_written_form_observed=True),
        forbidden_outcomes={"written_form_satisfied": True},
    ),
    FormRedTeamCase(
        id="form-red-electronic-invalid",
        title_ru="Признать письменную форму соблюденной при недействительной электронной подписи",
        facts=_facts(simple_written_form_required=True, simple_written_form_observed=True),
        forbidden_outcomes={"written_form_satisfied": True},
    ),
    FormRedTeamCase(
        id="form-red-ignore-notarial",
        title_ru="Признать форму соблюденной при несоблюдении нотариальной",
        facts=_facts(
            simple_written_form_required=True,
            notarial_form_required=True,
            simple_written_form_observed=True,
            document_signed_by_parties=True,
        ),
        forbidden_outcomes={"form_requirement_satisfied": True},
    ),
    FormRedTeamCase(
        id="form-red-notarial-not-void",
        title_ru="Не признать сделку ничтожной при несоблюдении нотариальной формы",
        facts=_facts(
            simple_written_form_required=True,
            notarial_form_required=True,
            simple_written_form_observed=True,
            document_signed_by_parties=True,
        ),
        forbidden_outcomes={"transaction_void_for_form": False},
    ),
    FormRedTeamCase(
        id="form-red-ignore-witness-bar",
        title_ru="Игнорировать запрет свидетельских показаний при несоблюдении письменной формы",
        facts=_facts(simple_written_form_required=True),
        forbidden_outcomes={"witness_testimony_barred": False},
    ),
    FormRedTeamCase(
        id="form-red-void-without-ground",
        title_ru="Признать простую письменную сделку ничтожной без указания закона",
        facts=_facts(simple_written_form_required=True),
        forbidden_outcomes={"transaction_void_for_form": True},
    ),
    FormRedTeamCase(
        id="form-red-satisfied-without-writing",
        title_ru="Признать форму соблюденной при несоблюдении письменной",
        facts=_facts(simple_written_form_required=True),
        forbidden_outcomes={"form_requirement_satisfied": True},
    ),
    FormRedTeamCase(
        id="form-red-skip-human-on-void",
        title_ru="Пропустить экспертную проверку при ничтожности формы",
        facts=_facts(
            simple_written_form_required=True,
            notarial_form_required=True,
            simple_written_form_observed=True,
            document_signed_by_parties=True,
        ),
        forbidden_outcomes={"requires_human_form_assessment": False},
    ),
    FormRedTeamCase(
        id="form-red-not-satisfied-without-requirement",
        title_ru="Не признать форму соблюденной при отсутствии требования к форме",
        facts=_facts(oral_form_permitted=True),
        forbidden_outcomes={"form_requirement_satisfied": False},
    ),
    FormRedTeamCase(
        id="form-red-oral-when-written-required",
        title_ru="Признать устную форму действительной при обязательной письменной",
        facts=_facts(simple_written_form_required=True),
        forbidden_outcomes={"oral_form_valid": True},
    ),
    FormRedTeamCase(
        id="form-red-conduct-without-offer",
        title_ru="Вывести соблюдение формы из действий без письменной оферты",
        facts=_facts(simple_written_form_required=True),
        forbidden_outcomes={"acceptance_by_conduct_observes_written_form": True},
    ),
)


def _evaluate(facts: FormFactSet, artifact_id: str) -> FormEvaluation:
    mapping = FormEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-form-law"],
    )
    constraints: FormConstraintSet = build_form_constraint_set(mapping)
    return evaluate_form_constraints(constraints, facts)


def _outcomes(evaluation: FormEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_form_benchmark_suite() -> FormBenchmarkReport:
    results = []
    for task in SYNTHETIC_FORM_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            FormEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return FormBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_form_red_team_suite() -> FormRedTeamReport:
    results = []
    for case in SYNTHETIC_FORM_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            FormRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return FormRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
