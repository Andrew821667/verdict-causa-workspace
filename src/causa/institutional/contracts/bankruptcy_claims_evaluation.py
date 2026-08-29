from pydantic import BaseModel, Field

from causa.institutional.contracts.bankruptcy_claims import (
    BankruptcyClaimsConstraintSet,
    BankruptcyClaimsEvaluation,
    BankruptcyClaimsEvidenceMappingResult,
    BankruptcyClaimsFactSet,
    BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS,
    build_bankruptcy_claims_constraint_set,
    evaluate_bankruptcy_claims_constraints,
)


class BankruptcyClaimsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: BankruptcyClaimsFactSet
    expected_outcomes: dict[str, bool]


class BankruptcyClaimsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankruptcyClaimsBenchmarkReport(BaseModel):
    id: str = "bankruptcy-claims-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[BankruptcyClaimsEvaluationResult] = Field(default_factory=list)


class BankruptcyClaimsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: BankruptcyClaimsFactSet
    forbidden_outcomes: dict[str, bool]


class BankruptcyClaimsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class BankruptcyClaimsRedTeamReport(BaseModel):
    id: str = "bankruptcy-claims-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[BankruptcyClaimsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> BankruptcyClaimsFactSet:
    """Факты по требованию внутри возбуждённого дела о банкротстве.

    `bankruptcy_case_opened` по умолчанию истинно: все случаи ниже, кроме прямо
    проверяющих сами ворота, разбирают требование в уже открытом деле.
    """
    values = {field_name: False for field_name in BankruptcyClaimsFactSet.model_fields}
    values["bankruptcy_case_opened"] = True
    values.update(updates)
    return BankruptcyClaimsFactSet(**values)


SYNTHETIC_BANKRUPTCY_CLAIMS_BENCHMARKS = (
    BankruptcyClaimsEvaluationTask(
        id="bankruptcy-claims-bench-registered-basic",
        title_ru="Обязательство до заявления о банкротстве — требование реестровое",
        facts=_facts(obligation_arose_before_petition_accepted=True),
        expected_outcomes={
            "claim_is_current": False,
            "requires_human_bankruptcy_claims_assessment": False,
        },
    ),
    BankruptcyClaimsEvaluationTask(
        id="bankruptcy-claims-bench-current-basic",
        title_ru="Обязательство после заявления о банкротстве — требование текущее",
        facts=_facts(obligation_arose_before_petition_accepted=False),
        expected_outcomes={
            "claim_is_current": True,
            "requires_human_bankruptcy_claims_assessment": True,
        },
    ),
    BankruptcyClaimsEvaluationTask(
        id="bankruptcy-claims-bench-enforcement-suspended",
        title_ru="Наблюдение введено, реестровый кредитор пытается взыскать индивидуально",
        facts=_facts(
            obligation_arose_before_petition_accepted=True,
            observation_introduced=True,
            creditor_seeks_individual_enforcement=True,
        ),
        expected_outcomes={
            "individual_enforcement_suspended": True,
            "individual_enforcement_permitted_by_exception": False,
        },
    ),
    BankruptcyClaimsEvaluationTask(
        id="bankruptcy-claims-bench-exception-applies",
        title_ru="Исполнительный документ из перечня исключений сохраняет силу",
        facts=_facts(
            obligation_arose_before_petition_accepted=True,
            observation_introduced=True,
            creditor_seeks_individual_enforcement=True,
            enforcement_document_predates_observation_and_is_exempt_category=True,
        ),
        expected_outcomes={
            "individual_enforcement_suspended": False,
            "individual_enforcement_permitted_by_exception": True,
        },
    ),
    BankruptcyClaimsEvaluationTask(
        id="bankruptcy-claims-bench-no-observation-no-suspension",
        title_ru="Наблюдение не введено — приостановления взыскания ещё нет",
        facts=_facts(
            obligation_arose_before_petition_accepted=True,
            creditor_seeks_individual_enforcement=True,
        ),
        expected_outcomes={"individual_enforcement_suspended": False},
    ),
    BankruptcyClaimsEvaluationTask(
        id="bankruptcy-claims-bench-current-not-suspended",
        title_ru="Текущий платёж не подпадает под приостановление статьи 63",
        facts=_facts(
            obligation_arose_before_petition_accepted=False,
            observation_introduced=True,
            creditor_seeks_individual_enforcement=True,
        ),
        expected_outcomes={
            "claim_is_current": True,
            "individual_enforcement_suspended": False,
        },
    ),
    BankruptcyClaimsEvaluationTask(
        id="bankruptcy-claims-bench-registered-no-attempt",
        title_ru="Реестровое требование без попытки индивидуального взыскания",
        facts=_facts(
            obligation_arose_before_petition_accepted=True,
            observation_introduced=True,
        ),
        expected_outcomes={
            "individual_enforcement_suspended": False,
            "individual_enforcement_permitted_by_exception": False,
        },
    ),
    BankruptcyClaimsEvaluationTask(
        id="bankruptcy-claims-bench-no-bankruptcy-case",
        title_ru="Дело о банкротстве не возбуждено — статья 5 не применяется",
        facts=_facts(bankruptcy_case_opened=False),
        expected_outcomes={
            "claim_is_current": False,
            "individual_enforcement_suspended": False,
            "individual_enforcement_permitted_by_exception": False,
            "requires_human_bankruptcy_claims_assessment": False,
        },
    ),
)


SYNTHETIC_BANKRUPTCY_CLAIMS_RED_TEAM_CASES = (
    BankruptcyClaimsRedTeamCase(
        id="bankruptcy-claims-red-current-as-registered",
        title_ru="Признать текущий платёж реестровым требованием",
        facts=_facts(obligation_arose_before_petition_accepted=False),
        forbidden_outcomes={"claim_is_current": False},
    ),
    BankruptcyClaimsRedTeamCase(
        id="bankruptcy-claims-red-skip-human-on-current",
        title_ru="Пропустить проверку юристом по текущему платежу",
        facts=_facts(obligation_arose_before_petition_accepted=False),
        forbidden_outcomes={"requires_human_bankruptcy_claims_assessment": False},
    ),
    BankruptcyClaimsRedTeamCase(
        id="bankruptcy-claims-red-suspend-without-observation",
        title_ru="Приостановить взыскание без введённого наблюдения",
        facts=_facts(
            obligation_arose_before_petition_accepted=True,
            creditor_seeks_individual_enforcement=True,
        ),
        forbidden_outcomes={"individual_enforcement_suspended": True},
    ),
    BankruptcyClaimsRedTeamCase(
        id="bankruptcy-claims-red-suspend-current-claim",
        title_ru="Приостановить взыскание текущего платежа",
        facts=_facts(
            obligation_arose_before_petition_accepted=False,
            observation_introduced=True,
            creditor_seeks_individual_enforcement=True,
        ),
        forbidden_outcomes={"individual_enforcement_suspended": True},
    ),
    BankruptcyClaimsRedTeamCase(
        id="bankruptcy-claims-red-exception-without-enforcement-attempt",
        title_ru="Признать исключение без попытки индивидуального взыскания",
        facts=_facts(
            obligation_arose_before_petition_accepted=True,
            observation_introduced=True,
        ),
        forbidden_outcomes={"individual_enforcement_permitted_by_exception": True},
    ),
    BankruptcyClaimsRedTeamCase(
        id="bankruptcy-claims-red-suspend-despite-exception",
        title_ru="Приостановить взыскание, несмотря на исключение пункта 1 статьи 63",
        facts=_facts(
            obligation_arose_before_petition_accepted=True,
            observation_introduced=True,
            creditor_seeks_individual_enforcement=True,
            enforcement_document_predates_observation_and_is_exempt_category=True,
        ),
        forbidden_outcomes={"individual_enforcement_suspended": True},
    ),
    BankruptcyClaimsRedTeamCase(
        id="bankruptcy-claims-red-human-flag-on-registered",
        title_ru="Требовать проверку юристом по обычному реестровому требованию",
        facts=_facts(obligation_arose_before_petition_accepted=True),
        forbidden_outcomes={"requires_human_bankruptcy_claims_assessment": True},
    ),
    BankruptcyClaimsRedTeamCase(
        id="bankruptcy-claims-red-current-without-bankruptcy-case",
        title_ru="Объявить требование текущим платежом там, где банкротства нет",
        facts=_facts(bankruptcy_case_opened=False),
        forbidden_outcomes={"claim_is_current": True},
    ),
    BankruptcyClaimsRedTeamCase(
        id="bankruptcy-claims-red-human-flag-without-bankruptcy-case",
        title_ru="Поднять флаг проверки юристом по делу без банкротства",
        facts=_facts(bankruptcy_case_opened=False),
        forbidden_outcomes={"requires_human_bankruptcy_claims_assessment": True},
    ),
)


def _evaluate(facts: BankruptcyClaimsFactSet, artifact_id: str) -> BankruptcyClaimsEvaluation:
    mapping = BankruptcyClaimsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS),
    )
    constraints: BankruptcyClaimsConstraintSet = build_bankruptcy_claims_constraint_set(mapping)
    return evaluate_bankruptcy_claims_constraints(constraints, facts)


def _outcomes(evaluation: BankruptcyClaimsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_bankruptcy_claims_benchmark_suite() -> BankruptcyClaimsBenchmarkReport:
    results = []
    for task in SYNTHETIC_BANKRUPTCY_CLAIMS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            BankruptcyClaimsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return BankruptcyClaimsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_bankruptcy_claims_red_team_suite() -> BankruptcyClaimsRedTeamReport:
    results = []
    for case in SYNTHETIC_BANKRUPTCY_CLAIMS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            BankruptcyClaimsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return BankruptcyClaimsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
