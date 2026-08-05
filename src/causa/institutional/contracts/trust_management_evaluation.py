from pydantic import BaseModel, Field

from causa.institutional.contracts.trust_management import (
    TrustManagementConstraintSet,
    TrustManagementEvaluation,
    TrustManagementEvidenceMappingResult,
    TrustManagementFactSet,
    build_trust_management_constraint_set,
    evaluate_trust_management_constraints,
)


class TrustManagementEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: TrustManagementFactSet
    expected_outcomes: dict[str, bool]


class TrustManagementEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TrustManagementBenchmarkReport(BaseModel):
    id: str = "trust-management-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[TrustManagementEvaluationResult] = Field(default_factory=list)


class TrustManagementRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: TrustManagementFactSet
    forbidden_outcomes: dict[str, bool]


class TrustManagementRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class TrustManagementRedTeamReport(BaseModel):
    id: str = "trust-management-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[TrustManagementRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> TrustManagementFactSet:
    values = {field_name: False for field_name in TrustManagementFactSet.model_fields}
    values.update(updates)
    return TrustManagementFactSet(**values)


SYNTHETIC_TRUST_MANAGEMENT_BENCHMARKS = (
    TrustManagementEvaluationTask(
        id="trust-management-bench-not-qualified",
        title_ru="Договор доверительного управления имуществом не заключён",
        facts=_facts(trustee_status_invalid=True),
        expected_outcomes={"trust_management_qualified": False},
    ),
    TrustManagementEvaluationTask(
        id="trust-management-bench-qualified-clean",
        title_ru="Договор доверительного управления без нарушений",
        facts=_facts(trust_management_contract_concluded=True),
        expected_outcomes={
            "trust_management_qualified": True,
            "requires_human_trust_management_assessment": False,
        },
    ),
    TrustManagementEvaluationTask(
        id="trust-management-bench-property-scope",
        title_ru="Объект доверительного управления определён с нарушением",
        facts=_facts(
            trust_management_contract_concluded=True,
            trust_property_scope_breached=True,
        ),
        expected_outcomes={
            "property_scope_duty_breached": True,
            "requires_human_trust_management_assessment": True,
        },
    ),
    TrustManagementEvaluationTask(
        id="trust-management-bench-trustee-status",
        title_ru="Доверительный управляющий не отвечает требованиям закона",
        facts=_facts(
            trust_management_contract_concluded=True,
            trustee_status_invalid=True,
        ),
        expected_outcomes={
            "trustee_status_duty_breached": True,
            "requires_human_trust_management_assessment": True,
        },
    ),
    TrustManagementEvaluationTask(
        id="trust-management-bench-essential-terms",
        title_ru="Существенные условия и форма нарушены, недействительность не применена",
        facts=_facts(
            trust_management_contract_concluded=True,
            essential_terms_or_form_breached=True,
            form_invalidity_not_applied=True,
        ),
        expected_outcomes={
            "essential_terms_duty_breached": True,
            "form_invalidity_breached": True,
            "requires_human_trust_management_assessment": True,
        },
    ),
    TrustManagementEvaluationTask(
        id="trust-management-bench-separation",
        title_ru="Имущество не обособлено от иного имущества сторон",
        facts=_facts(
            trust_management_contract_concluded=True,
            property_separation_breached=True,
        ),
        expected_outcomes={
            "property_separation_duty_breached": True,
            "requires_human_trust_management_assessment": True,
        },
    ),
    TrustManagementEvaluationTask(
        id="trust-management-bench-encumbered-property",
        title_ru="Управляющий не предупреждён об обременении имущества залогом",
        facts=_facts(
            trust_management_contract_concluded=True,
            encumbered_property_notice_breached=True,
        ),
        expected_outcomes={
            "encumbered_property_duty_breached": True,
            "requires_human_trust_management_assessment": True,
        },
    ),
    TrustManagementEvaluationTask(
        id="trust-management-bench-trustee-rights",
        title_ru="Права управляющего и представление отчёта нарушены",
        facts=_facts(
            trust_management_contract_concluded=True,
            trustee_rights_and_report_breached=True,
        ),
        expected_outcomes={
            "trustee_rights_duty_breached": True,
            "requires_human_trust_management_assessment": True,
        },
    ),
    TrustManagementEvaluationTask(
        id="trust-management-bench-liability",
        title_ru="Нарушены правила об ответственности доверительного управляющего",
        facts=_facts(
            trust_management_contract_concluded=True,
            trustee_liability_rules_breached=True,
        ),
        expected_outcomes={
            "trustee_liability_duty_breached": True,
            "requires_human_trust_management_assessment": True,
        },
    ),
    TrustManagementEvaluationTask(
        id="trust-management-bench-remuneration-termination",
        title_ru="Нарушены вознаграждение управляющего и прекращение договора",
        facts=_facts(
            trust_management_contract_concluded=True,
            remuneration_or_termination_rules_breached=True,
        ),
        expected_outcomes={
            "remuneration_and_termination_duty_breached": True,
            "requires_human_trust_management_assessment": True,
        },
    ),
)


SYNTHETIC_TRUST_MANAGEMENT_RED_TEAM_CASES = (
    TrustManagementRedTeamCase(
        id="trust-management-red-qualify-without-contract",
        title_ru="Квалифицировать доверительное управление без заключения договора",
        facts=_facts(trustee_status_invalid=True),
        forbidden_outcomes={"trust_management_qualified": True},
    ),
    TrustManagementRedTeamCase(
        id="trust-management-red-ignore-property-scope",
        title_ru="Игнорировать недопустимый объект доверительного управления",
        facts=_facts(
            trust_management_contract_concluded=True,
            trust_property_scope_breached=True,
        ),
        forbidden_outcomes={"property_scope_duty_breached": False},
    ),
    TrustManagementRedTeamCase(
        id="trust-management-red-ignore-trustee-status",
        title_ru="Игнорировать несоответствие управляющего требованиям закона",
        facts=_facts(
            trust_management_contract_concluded=True,
            trustee_status_invalid=True,
        ),
        forbidden_outcomes={"trustee_status_duty_breached": False},
    ),
    TrustManagementRedTeamCase(
        id="trust-management-red-ignore-essential-terms",
        title_ru="Игнорировать отсутствие существенных условий договора",
        facts=_facts(
            trust_management_contract_concluded=True,
            essential_terms_or_form_breached=True,
        ),
        forbidden_outcomes={"essential_terms_duty_breached": False},
    ),
    TrustManagementRedTeamCase(
        id="trust-management-red-invalidity-without-form-breach",
        title_ru="Признать недействительность формы без нарушения формы договора",
        facts=_facts(trust_management_contract_concluded=True),
        forbidden_outcomes={"form_invalidity_breached": True},
    ),
    TrustManagementRedTeamCase(
        id="trust-management-red-ignore-separation",
        title_ru="Признать надлежащим управление без обособления имущества",
        facts=_facts(
            trust_management_contract_concluded=True,
            property_separation_breached=True,
        ),
        forbidden_outcomes={"property_separation_duty_breached": False},
    ),
    TrustManagementRedTeamCase(
        id="trust-management-red-ignore-encumbered-property",
        title_ru="Игнорировать отсутствие предупреждения об обременении залогом",
        facts=_facts(
            trust_management_contract_concluded=True,
            encumbered_property_notice_breached=True,
        ),
        forbidden_outcomes={"encumbered_property_duty_breached": False},
    ),
    TrustManagementRedTeamCase(
        id="trust-management-red-ignore-trustee-rights",
        title_ru="Освободить управляющего от представления отчёта",
        facts=_facts(
            trust_management_contract_concluded=True,
            trustee_rights_and_report_breached=True,
        ),
        forbidden_outcomes={"trustee_rights_duty_breached": False},
    ),
    TrustManagementRedTeamCase(
        id="trust-management-red-ignore-liability",
        title_ru="Освободить управляющего от ответственности за отсутствие заботливости",
        facts=_facts(
            trust_management_contract_concluded=True,
            trustee_liability_rules_breached=True,
        ),
        forbidden_outcomes={"trustee_liability_duty_breached": False},
    ),
    TrustManagementRedTeamCase(
        id="trust-management-red-skip-human-on-termination",
        title_ru="Пропустить экспертизу при нарушении вознаграждения и прекращения договора",
        facts=_facts(
            trust_management_contract_concluded=True,
            remuneration_or_termination_rules_breached=True,
        ),
        forbidden_outcomes={"requires_human_trust_management_assessment": False},
    ),
)


def _evaluate(facts: TrustManagementFactSet, artifact_id: str) -> TrustManagementEvaluation:
    mapping = TrustManagementEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-trust-management-law"],
    )
    constraints: TrustManagementConstraintSet = build_trust_management_constraint_set(mapping)
    return evaluate_trust_management_constraints(constraints, facts)


def _outcomes(evaluation: TrustManagementEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_trust_management_benchmark_suite() -> TrustManagementBenchmarkReport:
    results = []
    for task in SYNTHETIC_TRUST_MANAGEMENT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            TrustManagementEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return TrustManagementBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_trust_management_red_team_suite() -> TrustManagementRedTeamReport:
    results = []
    for case in SYNTHETIC_TRUST_MANAGEMENT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            TrustManagementRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return TrustManagementRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
