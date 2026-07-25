from pydantic import BaseModel, Field

from causa.institutional.contracts.third_party import (
    ThirdPartyConstraintSet,
    ThirdPartyEvaluation,
    ThirdPartyEvidenceMappingResult,
    ThirdPartyFactSet,
    build_third_party_constraint_set,
    evaluate_third_party_constraints,
)


class ThirdPartyEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ThirdPartyFactSet
    expected_outcomes: dict[str, bool]


class ThirdPartyEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ThirdPartyBenchmarkReport(BaseModel):
    id: str = "third-party-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ThirdPartyEvaluationResult] = Field(default_factory=list)


class ThirdPartyRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ThirdPartyFactSet
    forbidden_outcomes: dict[str, bool]


class ThirdPartyRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ThirdPartyRedTeamReport(BaseModel):
    id: str = "third-party-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ThirdPartyRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ThirdPartyFactSet:
    values = {field_name: False for field_name in ThirdPartyFactSet.model_fields}
    values.update(updates)
    return ThirdPartyFactSet(**values)


SYNTHETIC_THIRD_PARTY_BENCHMARKS = (
    ThirdPartyEvaluationTask(
        id="third-party-bench-valid-demand",
        title_ru="Действительный договор в пользу третьего лица с правом требования",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
        ),
        expected_outcomes={
            "beneficiary_contract_valid": True,
            "third_party_may_demand_performance": True,
            "requires_human_third_party_assessment": False,
        },
    ),
    ThirdPartyEvaluationTask(
        id="third-party-bench-not-identified",
        title_ru="Третье лицо не определено — договор недействителен как договор в его пользу",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_granted_right_to_demand=True,
        ),
        expected_outcomes={
            "beneficiary_contract_valid": False,
            "third_party_may_demand_performance": False,
        },
    ),
    ThirdPartyEvaluationTask(
        id="third-party-bench-no-demand-right",
        title_ru="Исполнение третьему лицу без предоставления права требования",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
        ),
        expected_outcomes={
            "beneficiary_contract_valid": True,
            "third_party_may_demand_performance": False,
        },
    ),
    ThirdPartyEvaluationTask(
        id="third-party-bench-change-blocked",
        title_ru="После намерения изменение без согласия третьего лица не допускается",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_intent_expressed=True,
            parties_seek_modification_or_termination=True,
        ),
        expected_outcomes={
            "change_requires_third_party_consent": True,
            "change_permitted": False,
            "requires_human_third_party_assessment": True,
        },
    ),
    ThirdPartyEvaluationTask(
        id="third-party-bench-change-with-consent",
        title_ru="Изменение допускается при согласии третьего лица",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_intent_expressed=True,
            parties_seek_modification_or_termination=True,
            third_party_consents_to_change=True,
        ),
        expected_outcomes={
            "change_permitted": True,
            "requires_human_third_party_assessment": False,
        },
    ),
    ThirdPartyEvaluationTask(
        id="third-party-bench-change-statute-exception",
        title_ru="Закон или договор допускают изменение без согласия третьего лица",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_intent_expressed=True,
            statute_or_contract_allows_change_without_consent=True,
            parties_seek_modification_or_termination=True,
        ),
        expected_outcomes={
            "change_requires_third_party_consent": False,
            "change_permitted": True,
        },
    ),
    ThirdPartyEvaluationTask(
        id="third-party-bench-change-before-intent",
        title_ru="До выражения намерения изменение договора допускается",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            parties_seek_modification_or_termination=True,
        ),
        expected_outcomes={
            "change_requires_third_party_consent": False,
            "change_permitted": True,
        },
    ),
    ThirdPartyEvaluationTask(
        id="third-party-bench-waiver-reclaim",
        title_ru="При отказе третьего лица кредитор может воспользоваться правом",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_waived_right=True,
            creditor_reclaims_right=True,
        ),
        expected_outcomes={
            "creditor_may_use_right": True,
            "third_party_may_demand_performance": False,
            "requires_human_third_party_assessment": True,
        },
    ),
    ThirdPartyEvaluationTask(
        id="third-party-bench-waiver-no-reclaim",
        title_ru="Отказ третьего лица без притязания кредитора",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_waived_right=True,
        ),
        expected_outcomes={
            "creditor_may_use_right": False,
            "third_party_may_demand_performance": False,
        },
    ),
    ThirdPartyEvaluationTask(
        id="third-party-bench-intent-no-change",
        title_ru="Намерение выражено, но стороны не изменяют договор",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_intent_expressed=True,
        ),
        expected_outcomes={
            "change_requires_third_party_consent": True,
            "change_permitted": False,
            "requires_human_third_party_assessment": False,
        },
    ),
)


SYNTHETIC_THIRD_PARTY_RED_TEAM_CASES = (
    ThirdPartyRedTeamCase(
        id="third-party-red-valid-without-identification",
        title_ru="Признать договор в пользу третьего лица без его определения",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_granted_right_to_demand=True,
        ),
        forbidden_outcomes={"beneficiary_contract_valid": True},
    ),
    ThirdPartyRedTeamCase(
        id="third-party-red-demand-without-right",
        title_ru="Дать третьему лицу право требования без его предоставления договором",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
        ),
        forbidden_outcomes={"third_party_may_demand_performance": True},
    ),
    ThirdPartyRedTeamCase(
        id="third-party-red-demand-after-waiver",
        title_ru="Сохранить право требования третьего лица после его отказа",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_waived_right=True,
        ),
        forbidden_outcomes={"third_party_may_demand_performance": True},
    ),
    ThirdPartyRedTeamCase(
        id="third-party-red-change-without-consent",
        title_ru="Разрешить изменение договора без согласия третьего лица после намерения",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_intent_expressed=True,
            parties_seek_modification_or_termination=True,
        ),
        forbidden_outcomes={"change_permitted": True},
    ),
    ThirdPartyRedTeamCase(
        id="third-party-red-ignore-consent-requirement",
        title_ru="Игнорировать необходимость согласия третьего лица после намерения",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_intent_expressed=True,
        ),
        forbidden_outcomes={"change_requires_third_party_consent": False},
    ),
    ThirdPartyRedTeamCase(
        id="third-party-red-skip-human-on-blocked-change",
        title_ru="Пропустить экспертную проверку при заблокированном изменении",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_intent_expressed=True,
            parties_seek_modification_or_termination=True,
        ),
        forbidden_outcomes={"requires_human_third_party_assessment": False},
    ),
    ThirdPartyRedTeamCase(
        id="third-party-red-creditor-on-invalid-contract",
        title_ru="Позволить кредитору воспользоваться правом при недействительном договоре",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_granted_right_to_demand=True,
            third_party_waived_right=True,
            creditor_reclaims_right=True,
        ),
        forbidden_outcomes={"creditor_may_use_right": True},
    ),
    ThirdPartyRedTeamCase(
        id="third-party-red-skip-human-on-creditor-claim",
        title_ru="Пропустить экспертную проверку при переходе права к кредитору",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_waived_right=True,
            creditor_reclaims_right=True,
        ),
        forbidden_outcomes={"requires_human_third_party_assessment": False},
    ),
    ThirdPartyRedTeamCase(
        id="third-party-red-block-change-with-consent",
        title_ru="Запретить изменение при согласии третьего лица",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            third_party_intent_expressed=True,
            parties_seek_modification_or_termination=True,
            third_party_consents_to_change=True,
        ),
        forbidden_outcomes={"change_permitted": False},
    ),
    ThirdPartyRedTeamCase(
        id="third-party-red-block-change-before-intent",
        title_ru="Требовать согласие третьего лица до выражения им намерения",
        facts=_facts(
            third_party_beneficiary_contract=True,
            third_party_identified_or_determinable=True,
            third_party_granted_right_to_demand=True,
            parties_seek_modification_or_termination=True,
        ),
        forbidden_outcomes={"change_requires_third_party_consent": True},
    ),
)


def _evaluate(facts: ThirdPartyFactSet, artifact_id: str) -> ThirdPartyEvaluation:
    mapping = ThirdPartyEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-third-party-law"],
    )
    constraints: ThirdPartyConstraintSet = build_third_party_constraint_set(mapping)
    return evaluate_third_party_constraints(constraints, facts)


def _outcomes(evaluation: ThirdPartyEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_third_party_benchmark_suite() -> ThirdPartyBenchmarkReport:
    results = []
    for task in SYNTHETIC_THIRD_PARTY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ThirdPartyEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ThirdPartyBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_third_party_red_team_suite() -> ThirdPartyRedTeamReport:
    results = []
    for case in SYNTHETIC_THIRD_PARTY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ThirdPartyRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ThirdPartyRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
