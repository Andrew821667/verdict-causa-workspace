from pydantic import BaseModel, Field

from causa.institutional.contracts.franchise import (
    FranchiseConstraintSet,
    FranchiseEvaluation,
    FranchiseEvidenceMappingResult,
    FranchiseFactSet,
    build_franchise_constraint_set,
    evaluate_franchise_constraints,
)


class FranchiseEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: FranchiseFactSet
    expected_outcomes: dict[str, bool]


class FranchiseEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FranchiseBenchmarkReport(BaseModel):
    id: str = "franchise-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[FranchiseEvaluationResult] = Field(default_factory=list)


class FranchiseRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: FranchiseFactSet
    forbidden_outcomes: dict[str, bool]


class FranchiseRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FranchiseRedTeamReport(BaseModel):
    id: str = "franchise-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[FranchiseRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> FranchiseFactSet:
    values = {field_name: False for field_name in FranchiseFactSet.model_fields}
    values.update(updates)
    return FranchiseFactSet(**values)


SYNTHETIC_FRANCHISE_BENCHMARKS = (
    FranchiseEvaluationTask(
        id="franchise-bench-not-qualified",
        title_ru="Договор коммерческой концессии не заключён",
        facts=_facts(franchise_remuneration_rules_breached=True),
        expected_outcomes={"franchise_qualified": False},
    ),
    FranchiseEvaluationTask(
        id="franchise-bench-qualified-clean",
        title_ru="Договор коммерческой концессии без нарушений",
        facts=_facts(franchise_contract_concluded=True),
        expected_outcomes={
            "franchise_qualified": True,
            "requires_human_franchise_assessment": False,
        },
    ),
    FranchiseEvaluationTask(
        id="franchise-bench-scope-and-parties",
        title_ru="Объём переданных прав и состав сторон определены с нарушением",
        facts=_facts(
            franchise_contract_concluded=True,
            franchise_scope_or_parties_breached=True,
        ),
        expected_outcomes={
            "scope_and_parties_duty_breached": True,
            "requires_human_franchise_assessment": True,
        },
    ),
    FranchiseEvaluationTask(
        id="franchise-bench-form-and-registration",
        title_ru="Форма и государственная регистрация нарушены, ничтожность не применена",
        facts=_facts(
            franchise_contract_concluded=True,
            franchise_form_or_registration_breached=True,
            form_invalidity_not_applied=True,
        ),
        expected_outcomes={
            "form_and_registration_duty_breached": True,
            "form_invalidity_breached": True,
            "requires_human_franchise_assessment": True,
        },
    ),
    FranchiseEvaluationTask(
        id="franchise-bench-subconcession",
        title_ru="Нарушены правила о коммерческой субконцессии",
        facts=_facts(
            franchise_contract_concluded=True,
            commercial_subconcession_rules_breached=True,
        ),
        expected_outcomes={
            "subconcession_duty_breached": True,
            "requires_human_franchise_assessment": True,
        },
    ),
    FranchiseEvaluationTask(
        id="franchise-bench-remuneration",
        title_ru="Нарушены правила о вознаграждении правообладателя",
        facts=_facts(
            franchise_contract_concluded=True,
            franchise_remuneration_rules_breached=True,
        ),
        expected_outcomes={
            "remuneration_duty_breached": True,
            "requires_human_franchise_assessment": True,
        },
    ),
    FranchiseEvaluationTask(
        id="franchise-bench-rightholder-obligations",
        title_ru="Правообладатель не исполнил обязанности по договору",
        facts=_facts(
            franchise_contract_concluded=True,
            rightholder_obligations_breached=True,
        ),
        expected_outcomes={
            "rightholder_obligations_duty_breached": True,
            "requires_human_franchise_assessment": True,
        },
    ),
    FranchiseEvaluationTask(
        id="franchise-bench-user-obligations",
        title_ru="Пользователь не исполнил обязанности по договору",
        facts=_facts(
            franchise_contract_concluded=True,
            user_obligations_breached=True,
        ),
        expected_outcomes={
            "user_obligations_duty_breached": True,
            "requires_human_franchise_assessment": True,
        },
    ),
    FranchiseEvaluationTask(
        id="franchise-bench-restrictions",
        title_ru="Ограничения прав сторон установлены с нарушением закона",
        facts=_facts(
            franchise_contract_concluded=True,
            franchise_restrictions_rules_breached=True,
        ),
        expected_outcomes={
            "restrictions_duty_breached": True,
            "requires_human_franchise_assessment": True,
        },
    ),
    FranchiseEvaluationTask(
        id="franchise-bench-liability-termination",
        title_ru="Нарушены ответственность правообладателя и прекращение договора",
        facts=_facts(
            franchise_contract_concluded=True,
            liability_or_termination_rules_breached=True,
        ),
        expected_outcomes={
            "liability_and_termination_duty_breached": True,
            "requires_human_franchise_assessment": True,
        },
    ),
)


SYNTHETIC_FRANCHISE_RED_TEAM_CASES = (
    FranchiseRedTeamCase(
        id="franchise-red-qualify-without-contract",
        title_ru="Квалифицировать коммерческую концессию без заключения договора",
        facts=_facts(franchise_remuneration_rules_breached=True),
        forbidden_outcomes={"franchise_qualified": True},
    ),
    FranchiseRedTeamCase(
        id="franchise-red-ignore-scope-and-parties",
        title_ru="Игнорировать недопустимый состав сторон договора концессии",
        facts=_facts(
            franchise_contract_concluded=True,
            franchise_scope_or_parties_breached=True,
        ),
        forbidden_outcomes={"scope_and_parties_duty_breached": False},
    ),
    FranchiseRedTeamCase(
        id="franchise-red-ignore-registration",
        title_ru="Игнорировать отсутствие государственной регистрации предоставления права",
        facts=_facts(
            franchise_contract_concluded=True,
            franchise_form_or_registration_breached=True,
        ),
        forbidden_outcomes={"form_and_registration_duty_breached": False},
    ),
    FranchiseRedTeamCase(
        id="franchise-red-invalidity-without-form-breach",
        title_ru="Признать ничтожность договора без нарушения формы и регистрации",
        facts=_facts(franchise_contract_concluded=True),
        forbidden_outcomes={"form_invalidity_breached": True},
    ),
    FranchiseRedTeamCase(
        id="franchise-red-ignore-subconcession",
        title_ru="Разрешить субконцессию на срок дольше основного договора",
        facts=_facts(
            franchise_contract_concluded=True,
            commercial_subconcession_rules_breached=True,
        ),
        forbidden_outcomes={"subconcession_duty_breached": False},
    ),
    FranchiseRedTeamCase(
        id="franchise-red-ignore-remuneration",
        title_ru="Освободить пользователя от уплаты вознаграждения правообладателю",
        facts=_facts(
            franchise_contract_concluded=True,
            franchise_remuneration_rules_breached=True,
        ),
        forbidden_outcomes={"remuneration_duty_breached": False},
    ),
    FranchiseRedTeamCase(
        id="franchise-red-ignore-rightholder-obligations",
        title_ru="Освободить правообладателя от передачи документации и содействия",
        facts=_facts(
            franchise_contract_concluded=True,
            rightholder_obligations_breached=True,
        ),
        forbidden_outcomes={"rightholder_obligations_duty_breached": False},
    ),
    FranchiseRedTeamCase(
        id="franchise-red-ignore-user-obligations",
        title_ru="Освободить пользователя от информирования покупателей о концессии",
        facts=_facts(
            franchise_contract_concluded=True,
            user_obligations_breached=True,
        ),
        forbidden_outcomes={"user_obligations_duty_breached": False},
    ),
    FranchiseRedTeamCase(
        id="franchise-red-ignore-void-restrictions",
        title_ru="Признать действительными ничтожные ограничения прав пользователя",
        facts=_facts(
            franchise_contract_concluded=True,
            franchise_restrictions_rules_breached=True,
        ),
        forbidden_outcomes={"restrictions_duty_breached": False},
    ),
    FranchiseRedTeamCase(
        id="franchise-red-skip-human-on-liability",
        title_ru="Пропустить экспертизу при нарушении ответственности правообладателя",
        facts=_facts(
            franchise_contract_concluded=True,
            liability_or_termination_rules_breached=True,
        ),
        forbidden_outcomes={"requires_human_franchise_assessment": False},
    ),
)


def _evaluate(facts: FranchiseFactSet, artifact_id: str) -> FranchiseEvaluation:
    mapping = FranchiseEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-franchise-law"],
    )
    constraints: FranchiseConstraintSet = build_franchise_constraint_set(mapping)
    return evaluate_franchise_constraints(constraints, facts)


def _outcomes(evaluation: FranchiseEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_franchise_benchmark_suite() -> FranchiseBenchmarkReport:
    results = []
    for task in SYNTHETIC_FRANCHISE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            FranchiseEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return FranchiseBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_franchise_red_team_suite() -> FranchiseRedTeamReport:
    results = []
    for case in SYNTHETIC_FRANCHISE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            FranchiseRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return FranchiseRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
