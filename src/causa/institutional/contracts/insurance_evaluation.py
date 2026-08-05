from pydantic import BaseModel, Field

from causa.institutional.contracts.insurance import (
    InsuranceConstraintSet,
    InsuranceEvaluation,
    InsuranceEvidenceMappingResult,
    InsuranceFactSet,
    build_insurance_constraint_set,
    evaluate_insurance_constraints,
)


class InsuranceEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: InsuranceFactSet
    expected_outcomes: dict[str, bool]


class InsuranceEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class InsuranceBenchmarkReport(BaseModel):
    id: str = "insurance-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[InsuranceEvaluationResult] = Field(default_factory=list)


class InsuranceRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: InsuranceFactSet
    forbidden_outcomes: dict[str, bool]


class InsuranceRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class InsuranceRedTeamReport(BaseModel):
    id: str = "insurance-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[InsuranceRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> InsuranceFactSet:
    values = {field_name: False for field_name in InsuranceFactSet.model_fields}
    values.update(updates)
    return InsuranceFactSet(**values)


SYNTHETIC_INSURANCE_BENCHMARKS = (
    InsuranceEvaluationTask(
        id="insurance-bench-not-qualified",
        title_ru="Договор страхования не заключён",
        facts=_facts(insurer_not_entitled_to_act=True),
        expected_outcomes={"insurance_qualified": False},
    ),
    InsuranceEvaluationTask(
        id="insurance-bench-qualified-clean",
        title_ru="Договор страхования без нарушений",
        facts=_facts(insurance_contract_concluded=True),
        expected_outcomes={
            "insurance_qualified": True,
            "requires_human_insurance_assessment": False,
        },
    ),
    InsuranceEvaluationTask(
        id="insurance-bench-insurer-status",
        title_ru="Страховщик не вправе осуществлять страхование данного вида",
        facts=_facts(
            insurance_contract_concluded=True,
            insurer_not_entitled_to_act=True,
        ),
        expected_outcomes={
            "insurer_status_invalid": True,
            "requires_human_insurance_assessment": True,
        },
    ),
    InsuranceEvaluationTask(
        id="insurance-bench-interest",
        title_ru="Страховой интерес отсутствует или его страхование не допускается",
        facts=_facts(
            insurance_contract_concluded=True,
            insured_interest_absent_or_unlawful=True,
        ),
        expected_outcomes={
            "insured_interest_invalid": True,
            "requires_human_insurance_assessment": True,
        },
    ),
    InsuranceEvaluationTask(
        id="insurance-bench-form",
        title_ru="Письменная форма договора страхования не соблюдена",
        facts=_facts(
            insurance_contract_concluded=True,
            insurance_written_form_not_observed=True,
        ),
        expected_outcomes={
            "insurance_form_void": True,
            "requires_human_insurance_assessment": True,
        },
    ),
    InsuranceEvaluationTask(
        id="insurance-bench-essential-terms",
        title_ru="Существенные условия не согласованы, правила страхования не применены",
        facts=_facts(
            insurance_contract_concluded=True,
            essential_terms_not_agreed=True,
            insurance_rules_application_breached=True,
        ),
        expected_outcomes={
            "essential_terms_duty_breached": True,
            "insurance_rules_duty_breached": True,
            "requires_human_insurance_assessment": True,
        },
    ),
    InsuranceEvaluationTask(
        id="insurance-bench-property-scope",
        title_ru="Нарушены пределы имущественного страхования",
        facts=_facts(
            insurance_contract_concluded=True,
            property_insurance_scope_breached=True,
        ),
        expected_outcomes={
            "property_insurance_duty_breached": True,
            "requires_human_insurance_assessment": True,
        },
    ),
    InsuranceEvaluationTask(
        id="insurance-bench-personal-scope",
        title_ru="Нарушены пределы личного страхования",
        facts=_facts(
            insurance_contract_concluded=True,
            personal_insurance_scope_breached=True,
        ),
        expected_outcomes={
            "personal_insurance_duty_breached": True,
            "requires_human_insurance_assessment": True,
        },
    ),
    InsuranceEvaluationTask(
        id="insurance-bench-beneficiary",
        title_ru="Права выгодоприобретателя не учтены",
        facts=_facts(
            insurance_contract_concluded=True,
            beneficiary_rights_disregarded=True,
        ),
        expected_outcomes={
            "beneficiary_rights_breached": True,
            "requires_human_insurance_assessment": True,
        },
    ),
    InsuranceEvaluationTask(
        id="insurance-bench-compulsory",
        title_ru="Обязанность по обязательному страхованию не исполнена",
        facts=_facts(
            insurance_contract_concluded=True,
            compulsory_insurance_duty_breached=True,
        ),
        expected_outcomes={
            "compulsory_insurance_breached": True,
            "requires_human_insurance_assessment": True,
        },
    ),
)


SYNTHETIC_INSURANCE_RED_TEAM_CASES = (
    InsuranceRedTeamCase(
        id="insurance-red-qualify-without-contract",
        title_ru="Квалифицировать страхование без заключения договора",
        facts=_facts(insurer_not_entitled_to_act=True),
        forbidden_outcomes={"insurance_qualified": True},
    ),
    InsuranceRedTeamCase(
        id="insurance-red-ignore-insurer-status",
        title_ru="Игнорировать отсутствие у страховщика права осуществлять страхование",
        facts=_facts(
            insurance_contract_concluded=True,
            insurer_not_entitled_to_act=True,
        ),
        forbidden_outcomes={"insurer_status_invalid": False},
    ),
    InsuranceRedTeamCase(
        id="insurance-red-ignore-interest",
        title_ru="Признать действительным страхование без страхового интереса",
        facts=_facts(
            insurance_contract_concluded=True,
            insured_interest_absent_or_unlawful=True,
        ),
        forbidden_outcomes={"insured_interest_invalid": False},
    ),
    InsuranceRedTeamCase(
        id="insurance-red-ignore-form",
        title_ru="Признать действительным договор страхования без письменной формы",
        facts=_facts(
            insurance_contract_concluded=True,
            insurance_written_form_not_observed=True,
        ),
        forbidden_outcomes={"insurance_form_void": False},
    ),
    InsuranceRedTeamCase(
        id="insurance-red-ignore-essential-terms",
        title_ru="Игнорировать несогласование существенных условий страхования",
        facts=_facts(
            insurance_contract_concluded=True,
            essential_terms_not_agreed=True,
        ),
        forbidden_outcomes={"essential_terms_duty_breached": False},
    ),
    InsuranceRedTeamCase(
        id="insurance-red-rules-without-terms-breach",
        title_ru="Признать нарушение правил страхования без несогласования условий договора",
        facts=_facts(insurance_contract_concluded=True),
        forbidden_outcomes={"insurance_rules_duty_breached": True},
    ),
    InsuranceRedTeamCase(
        id="insurance-red-ignore-property-scope",
        title_ru="Игнорировать выход за пределы имущественного страхования",
        facts=_facts(
            insurance_contract_concluded=True,
            property_insurance_scope_breached=True,
        ),
        forbidden_outcomes={"property_insurance_duty_breached": False},
    ),
    InsuranceRedTeamCase(
        id="insurance-red-ignore-personal-scope",
        title_ru="Игнорировать выход за пределы личного страхования",
        facts=_facts(
            insurance_contract_concluded=True,
            personal_insurance_scope_breached=True,
        ),
        forbidden_outcomes={"personal_insurance_duty_breached": False},
    ),
    InsuranceRedTeamCase(
        id="insurance-red-ignore-beneficiary",
        title_ru="Игнорировать права выгодоприобретателя по договору страхования",
        facts=_facts(
            insurance_contract_concluded=True,
            beneficiary_rights_disregarded=True,
        ),
        forbidden_outcomes={"beneficiary_rights_breached": False},
    ),
    InsuranceRedTeamCase(
        id="insurance-red-skip-human-on-compulsory",
        title_ru="Пропустить экспертизу при неисполнении обязательного страхования",
        facts=_facts(
            insurance_contract_concluded=True,
            compulsory_insurance_duty_breached=True,
        ),
        forbidden_outcomes={"requires_human_insurance_assessment": False},
    ),
)


def _evaluate(facts: InsuranceFactSet, artifact_id: str) -> InsuranceEvaluation:
    mapping = InsuranceEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-insurance-law"],
    )
    constraints: InsuranceConstraintSet = build_insurance_constraint_set(mapping)
    return evaluate_insurance_constraints(constraints, facts)


def _outcomes(evaluation: InsuranceEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_insurance_benchmark_suite() -> InsuranceBenchmarkReport:
    results = []
    for task in SYNTHETIC_INSURANCE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            InsuranceEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return InsuranceBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_insurance_red_team_suite() -> InsuranceRedTeamReport:
    results = []
    for case in SYNTHETIC_INSURANCE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            InsuranceRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return InsuranceRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
