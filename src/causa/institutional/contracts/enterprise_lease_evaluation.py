from pydantic import BaseModel, Field

from causa.institutional.contracts.enterprise_lease import (
    EnterpriseLeaseConstraintSet,
    EnterpriseLeaseEvaluation,
    EnterpriseLeaseEvidenceMappingResult,
    EnterpriseLeaseFactSet,
    build_enterprise_lease_constraint_set,
    evaluate_enterprise_lease_constraints,
)


class EnterpriseLeaseEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: EnterpriseLeaseFactSet
    expected_outcomes: dict[str, bool]


class EnterpriseLeaseEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class EnterpriseLeaseBenchmarkReport(BaseModel):
    id: str = "enterprise-lease-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[EnterpriseLeaseEvaluationResult] = Field(default_factory=list)


class EnterpriseLeaseRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: EnterpriseLeaseFactSet
    forbidden_outcomes: dict[str, bool]


class EnterpriseLeaseRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class EnterpriseLeaseRedTeamReport(BaseModel):
    id: str = "enterprise-lease-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[EnterpriseLeaseRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> EnterpriseLeaseFactSet:
    values = {field_name: False for field_name in EnterpriseLeaseFactSet.model_fields}
    values.update(updates)
    return EnterpriseLeaseFactSet(**values)


SYNTHETIC_ENTERPRISE_LEASE_BENCHMARKS = (
    EnterpriseLeaseEvaluationTask(
        id="enterprise-lease-bench-not-qualified",
        title_ru="Отношения без передачи предприятия как имущественного комплекса",
        facts=_facts(single_written_document_missing=True),
        expected_outcomes={"enterprise_lease_qualified": False},
    ),
    EnterpriseLeaseEvaluationTask(
        id="enterprise-lease-bench-qualified-clean",
        title_ru="Аренда предприятия без нарушений",
        facts=_facts(enterprise_leased_as_complex=True),
        expected_outcomes={
            "enterprise_lease_qualified": True,
            "requires_human_enterprise_lease_assessment": False,
        },
    ),
    EnterpriseLeaseEvaluationTask(
        id="enterprise-lease-bench-form-defect",
        title_ru="Договор не оформлен одним документом, подписанным сторонами",
        facts=_facts(
            enterprise_leased_as_complex=True,
            single_written_document_missing=True,
        ),
        expected_outcomes={
            "form_defect_makes_void": True,
            "requires_human_enterprise_lease_assessment": True,
        },
    ),
    EnterpriseLeaseEvaluationTask(
        id="enterprise-lease-bench-registration-missing",
        title_ru="Отсутствует государственная регистрация договора",
        facts=_facts(
            enterprise_leased_as_complex=True,
            state_registration_missing=True,
        ),
        expected_outcomes={
            "registration_required_and_missing": True,
            "requires_human_enterprise_lease_assessment": True,
        },
    ),
    EnterpriseLeaseEvaluationTask(
        id="enterprise-lease-bench-creditors-not-notified",
        title_ru="Кредиторы не уведомлены о передаче предприятия в аренду",
        facts=_facts(
            enterprise_leased_as_complex=True,
            creditors_not_notified=True,
        ),
        expected_outcomes={
            "creditor_notice_not_given": True,
            "requires_human_enterprise_lease_assessment": True,
        },
    ),
    EnterpriseLeaseEvaluationTask(
        id="enterprise-lease-bench-debt-without-consent",
        title_ru="Долги переведены на арендатора без согласия кредитора",
        facts=_facts(
            enterprise_leased_as_complex=True,
            debt_transferred_without_creditor_consent=True,
        ),
        expected_outcomes={
            "creditor_consent_missing_for_debt": True,
            "requires_human_enterprise_lease_assessment": True,
        },
    ),
    EnterpriseLeaseEvaluationTask(
        id="enterprise-lease-bench-transfer-deed",
        title_ru="Передача предприятия не оформлена передаточным актом",
        facts=_facts(
            enterprise_leased_as_complex=True,
            transfer_deed_missing=True,
        ),
        expected_outcomes={
            "transfer_not_documented": True,
            "requires_human_enterprise_lease_assessment": True,
        },
    ),
    EnterpriseLeaseEvaluationTask(
        id="enterprise-lease-bench-transfer-preparation",
        title_ru="Арендодатель не подготовил предприятие к передаче за свой счёт",
        facts=_facts(
            enterprise_leased_as_complex=True,
            lessor_failed_transfer_preparation=True,
        ),
        expected_outcomes={
            "transfer_preparation_breached": True,
            "requires_human_enterprise_lease_assessment": True,
        },
    ),
    EnterpriseLeaseEvaluationTask(
        id="enterprise-lease-bench-disposal-restriction",
        title_ru="Право арендатора распоряжаться материальными ценностями ограничено",
        facts=_facts(
            enterprise_leased_as_complex=True,
            tenant_disposal_right_wrongly_restricted=True,
        ),
        expected_outcomes={
            "disposal_right_wrongly_restricted": True,
            "requires_human_enterprise_lease_assessment": True,
        },
    ),
    EnterpriseLeaseEvaluationTask(
        id="enterprise-lease-bench-return-preparation",
        title_ru="Арендатор не подготовил предприятие к возврату за свой счёт",
        facts=_facts(
            enterprise_leased_as_complex=True,
            return_preparation_neglected=True,
        ),
        expected_outcomes={
            "return_preparation_breached": True,
            "requires_human_enterprise_lease_assessment": True,
        },
    ),
)


SYNTHETIC_ENTERPRISE_LEASE_RED_TEAM_CASES = (
    EnterpriseLeaseRedTeamCase(
        id="enterprise-lease-red-qualify-without-complex",
        title_ru="Квалифицировать аренду предприятия без передачи имущественного комплекса",
        facts=_facts(single_written_document_missing=True),
        forbidden_outcomes={"enterprise_lease_qualified": True},
    ),
    EnterpriseLeaseRedTeamCase(
        id="enterprise-lease-red-ignore-form",
        title_ru="Игнорировать недействительность при несоблюдении формы одного документа",
        facts=_facts(
            enterprise_leased_as_complex=True,
            single_written_document_missing=True,
        ),
        forbidden_outcomes={"form_defect_makes_void": False},
    ),
    EnterpriseLeaseRedTeamCase(
        id="enterprise-lease-red-ignore-registration",
        title_ru="Игнорировать отсутствие государственной регистрации договора",
        facts=_facts(
            enterprise_leased_as_complex=True,
            state_registration_missing=True,
        ),
        forbidden_outcomes={"registration_required_and_missing": False},
    ),
    EnterpriseLeaseRedTeamCase(
        id="enterprise-lease-red-ignore-creditor-notice",
        title_ru="Игнорировать отсутствие уведомления кредиторов",
        facts=_facts(
            enterprise_leased_as_complex=True,
            creditors_not_notified=True,
        ),
        forbidden_outcomes={"creditor_notice_not_given": False},
    ),
    EnterpriseLeaseRedTeamCase(
        id="enterprise-lease-red-allow-debt-without-consent",
        title_ru="Считать правомерным перевод долгов без согласия кредитора",
        facts=_facts(
            enterprise_leased_as_complex=True,
            debt_transferred_without_creditor_consent=True,
        ),
        forbidden_outcomes={"creditor_consent_missing_for_debt": False},
    ),
    EnterpriseLeaseRedTeamCase(
        id="enterprise-lease-red-ignore-transfer-deed",
        title_ru="Игнорировать отсутствие передаточного акта при передаче предприятия",
        facts=_facts(
            enterprise_leased_as_complex=True,
            transfer_deed_missing=True,
        ),
        forbidden_outcomes={"transfer_not_documented": False},
    ),
    EnterpriseLeaseRedTeamCase(
        id="enterprise-lease-red-shift-preparation-to-tenant",
        title_ru="Возложить подготовку предприятия к передаче на арендатора",
        facts=_facts(
            enterprise_leased_as_complex=True,
            lessor_failed_transfer_preparation=True,
        ),
        forbidden_outcomes={"transfer_preparation_breached": False},
    ),
    EnterpriseLeaseRedTeamCase(
        id="enterprise-lease-red-uphold-disposal-restriction",
        title_ru="Считать правомерным ограничение распоряжения материальными ценностями",
        facts=_facts(
            enterprise_leased_as_complex=True,
            tenant_disposal_right_wrongly_restricted=True,
        ),
        forbidden_outcomes={"disposal_right_wrongly_restricted": False},
    ),
    EnterpriseLeaseRedTeamCase(
        id="enterprise-lease-red-creditor-consent-without-breach",
        title_ru="Признать отсутствие согласия кредитора без самого перевода долгов",
        facts=_facts(enterprise_leased_as_complex=True),
        forbidden_outcomes={"creditor_consent_missing_for_debt": True},
    ),
    EnterpriseLeaseRedTeamCase(
        id="enterprise-lease-red-skip-human-on-maintenance",
        title_ru="Пропустить экспертизу при неисполнении обязанности по содержанию предприятия",
        facts=_facts(
            enterprise_leased_as_complex=True,
            maintenance_or_repair_neglected=True,
        ),
        forbidden_outcomes={"requires_human_enterprise_lease_assessment": False},
    ),
)


def _evaluate(facts: EnterpriseLeaseFactSet, artifact_id: str) -> EnterpriseLeaseEvaluation:
    mapping = EnterpriseLeaseEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-enterprise-lease-law"],
    )
    constraints: EnterpriseLeaseConstraintSet = build_enterprise_lease_constraint_set(mapping)
    return evaluate_enterprise_lease_constraints(constraints, facts)


def _outcomes(evaluation: EnterpriseLeaseEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_enterprise_lease_benchmark_suite() -> EnterpriseLeaseBenchmarkReport:
    results = []
    for task in SYNTHETIC_ENTERPRISE_LEASE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            EnterpriseLeaseEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return EnterpriseLeaseBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_enterprise_lease_red_team_suite() -> EnterpriseLeaseRedTeamReport:
    results = []
    for case in SYNTHETIC_ENTERPRISE_LEASE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            EnterpriseLeaseRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return EnterpriseLeaseRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
