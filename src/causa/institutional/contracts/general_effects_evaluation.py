from pydantic import BaseModel, Field

from causa.institutional.contracts.general_effects import (
    GeneralEffectsConstraintSet,
    GeneralEffectsEvaluation,
    GeneralEffectsInputs,
    build_general_effects_constraint_set,
    evaluate_general_effects_constraints,
)


class GeneralEffectsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    inputs: GeneralEffectsInputs
    expected_outcomes: dict[str, bool]


class GeneralEffectsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GeneralEffectsBenchmarkReport(BaseModel):
    id: str = "general-effects-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[GeneralEffectsEvaluationResult] = Field(default_factory=list)


class GeneralEffectsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    inputs: GeneralEffectsInputs
    forbidden_outcomes: dict[str, bool]


class GeneralEffectsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class GeneralEffectsRedTeamReport(BaseModel):
    id: str = "general-effects-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[GeneralEffectsRedTeamResult] = Field(default_factory=list)


def _inputs(**updates: bool) -> GeneralEffectsInputs:
    values = {field_name: False for field_name in GeneralEffectsInputs.model_fields}
    values.update(updates)
    return GeneralEffectsInputs(**values)


# Действующий договор без пороков: заключён, не оспорен, форма соблюдена,
# давность не заявлена.
_EFFECTIVE = {"contract_concluded_prerequisites": True}


SYNTHETIC_GENERAL_EFFECTS_BENCHMARKS = (
    GeneralEffectsEvaluationTask(
        id="general-effects-bench-effective-contract",
        title_ru="Договор заключён, действителен, давность не заявлена",
        inputs=_inputs(**_EFFECTIVE),
        expected_outcomes={
            "contract_legally_effective": True,
            "contractual_claims_enforceable": True,
            "institute_conclusions_displaced": False,
            "requires_human_general_effects_assessment": False,
        },
    ),
    GeneralEffectsEvaluationTask(
        id="general-effects-bench-not-concluded",
        title_ru="Договор не заключён — выводы специальных институтов лишены эффекта",
        inputs=_inputs(contract_concluded_prerequisites=False),
        expected_outcomes={
            "formation_defect_displaces_contract": True,
            "contract_legally_effective": False,
            "institute_conclusions_displaced": True,
            "contractual_claims_enforceable": False,
            "requires_human_general_effects_assessment": True,
        },
    ),
    GeneralEffectsEvaluationTask(
        id="general-effects-bench-invalid-contract",
        title_ru="Сделка недействительна — договорный эффект вытеснен",
        inputs=_inputs(**_EFFECTIVE, contractual_effect_displaced=True),
        expected_outcomes={
            "invalidity_displaces_contract": True,
            "contract_legally_effective": False,
            "institute_conclusions_displaced": True,
            "requires_human_general_effects_assessment": True,
        },
    ),
    GeneralEffectsEvaluationTask(
        id="general-effects-bench-void-for-form",
        title_ru="Сделка ничтожна вследствие порока формы",
        inputs=_inputs(**_EFFECTIVE, transaction_void_for_form=True),
        expected_outcomes={
            "form_defect_displaces_contract": True,
            "contract_legally_effective": False,
            "contractual_claims_enforceable": False,
            "requires_human_general_effects_assessment": True,
        },
    ),
    GeneralEffectsEvaluationTask(
        id="general-effects-bench-limitation-barred",
        title_ru="Давность истекла и заявлена — в иске отказано, договор действует",
        inputs=_inputs(**_EFFECTIVE, limitation_defense_available=True),
        expected_outcomes={
            "contract_legally_effective": True,
            "judicial_protection_available": False,
            "claims_barred_by_limitation": True,
            "contractual_claims_enforceable": False,
            "requires_human_general_effects_assessment": True,
        },
    ),
    GeneralEffectsEvaluationTask(
        id="general-effects-bench-limitation-not-applicable",
        title_ru="Требование не подлежит давности — защита доступна несмотря на заявление",
        inputs=_inputs(
            **_EFFECTIVE,
            limitation_defense_available=True,
            claim_not_subject_to_limitation=True,
        ),
        expected_outcomes={
            "judicial_protection_available": True,
            "claims_barred_by_limitation": False,
            "contractual_claims_enforceable": True,
            "requires_human_general_effects_assessment": False,
        },
    ),
    GeneralEffectsEvaluationTask(
        id="general-effects-bench-breach-without-effect",
        title_ru="Нарушение установлено, но договор не заключён — присуждение невозможно",
        inputs=_inputs(contract_concluded_prerequisites=False, breach_issue=True),
        expected_outcomes={
            "breach_findings_without_effect": True,
            "contractual_claims_enforceable": False,
            "requires_human_general_effects_assessment": True,
        },
    ),
    GeneralEffectsEvaluationTask(
        id="general-effects-bench-breach-barred-by-limitation",
        title_ru="Нарушение установлено, но в иске отказано по давности",
        inputs=_inputs(**_EFFECTIVE, breach_issue=True, limitation_defense_available=True),
        expected_outcomes={
            "breach_findings_without_effect": True,
            "claims_barred_by_limitation": True,
            "requires_human_general_effects_assessment": True,
        },
    ),
    GeneralEffectsEvaluationTask(
        id="general-effects-bench-breach-enforceable",
        title_ru="Нарушение установлено при действующем договоре — требования исполнимы",
        inputs=_inputs(**_EFFECTIVE, breach_issue=True),
        expected_outcomes={
            "breach_findings_without_effect": False,
            "contractual_claims_enforceable": True,
            "requires_human_general_effects_assessment": False,
        },
    ),
    GeneralEffectsEvaluationTask(
        id="general-effects-bench-restitution",
        title_ru="Сделка недействительна и требуется реституция",
        inputs=_inputs(**_EFFECTIVE, contractual_effect_displaced=True, restitution_required=True),
        expected_outcomes={
            "restitution_regime_applies": True,
            "institute_conclusions_displaced": True,
            "requires_human_general_effects_assessment": True,
        },
    ),
)


SYNTHETIC_GENERAL_EFFECTS_RED_TEAM_CASES = (
    GeneralEffectsRedTeamCase(
        id="general-effects-red-enforce-unconcluded-contract",
        title_ru="Признать требования исполнимыми по незаключённому договору",
        inputs=_inputs(contract_concluded_prerequisites=False),
        forbidden_outcomes={"contractual_claims_enforceable": True},
    ),
    GeneralEffectsRedTeamCase(
        id="general-effects-red-enforce-invalid-contract",
        title_ru="Признать договор действующим при установленной недействительности",
        inputs=_inputs(**_EFFECTIVE, contractual_effect_displaced=True),
        forbidden_outcomes={"contract_legally_effective": True},
    ),
    GeneralEffectsRedTeamCase(
        id="general-effects-red-enforce-void-for-form",
        title_ru="Признать договор действующим при ничтожности из-за формы",
        inputs=_inputs(**_EFFECTIVE, transaction_void_for_form=True),
        forbidden_outcomes={"contract_legally_effective": True},
    ),
    GeneralEffectsRedTeamCase(
        id="general-effects-red-ignore-limitation-defense",
        title_ru="Удовлетворить требование вопреки заявленной исковой давности",
        inputs=_inputs(**_EFFECTIVE, limitation_defense_available=True),
        forbidden_outcomes={"contractual_claims_enforceable": True},
    ),
    GeneralEffectsRedTeamCase(
        id="general-effects-red-ignore-limitation-bar-flag",
        title_ru="Скрыть отказ в иске по давности от итогового вывода",
        inputs=_inputs(**_EFFECTIVE, limitation_defense_available=True),
        forbidden_outcomes={"claims_barred_by_limitation": False},
    ),
    GeneralEffectsRedTeamCase(
        id="general-effects-red-keep-breach-effect-without-contract",
        title_ru="Сохранить эффект вывода о нарушении при незаключённом договоре",
        inputs=_inputs(contract_concluded_prerequisites=False, breach_issue=True),
        forbidden_outcomes={"breach_findings_without_effect": False},
    ),
    GeneralEffectsRedTeamCase(
        id="general-effects-red-keep-institute-conclusions-on-invalidity",
        title_ru="Сохранить силу выводов институтов при недействительности сделки",
        inputs=_inputs(**_EFFECTIVE, contractual_effect_displaced=True),
        forbidden_outcomes={"institute_conclusions_displaced": False},
    ),
    GeneralEffectsRedTeamCase(
        id="general-effects-red-skip-restitution",
        title_ru="Не применить реституцию при недействительности с возвратом полученного",
        inputs=_inputs(**_EFFECTIVE, contractual_effect_displaced=True, restitution_required=True),
        forbidden_outcomes={"restitution_regime_applies": False},
    ),
    GeneralEffectsRedTeamCase(
        id="general-effects-red-displace-effective-contract",
        title_ru="Объявить выводы институтов лишёнными эффекта при действующем договоре",
        inputs=_inputs(**_EFFECTIVE),
        forbidden_outcomes={"institute_conclusions_displaced": True},
    ),
    GeneralEffectsRedTeamCase(
        id="general-effects-red-skip-human-on-displaced-contract",
        title_ru="Пропустить экспертизу при вытеснении договорного эффекта",
        inputs=_inputs(contract_concluded_prerequisites=False),
        forbidden_outcomes={"requires_human_general_effects_assessment": False},
    ),
)


def _evaluate(inputs: GeneralEffectsInputs, case_id: str) -> GeneralEffectsEvaluation:
    constraints: GeneralEffectsConstraintSet = build_general_effects_constraint_set(inputs, case_id)
    return evaluate_general_effects_constraints(constraints, inputs)


def _outcomes(evaluation: GeneralEffectsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_general_effects_benchmark_suite() -> GeneralEffectsBenchmarkReport:
    results = []
    for task in SYNTHETIC_GENERAL_EFFECTS_BENCHMARKS:
        evaluation = _evaluate(task.inputs, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            GeneralEffectsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return GeneralEffectsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_general_effects_red_team_suite() -> GeneralEffectsRedTeamReport:
    results = []
    for case in SYNTHETIC_GENERAL_EFFECTS_RED_TEAM_CASES:
        evaluation = _evaluate(case.inputs, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            GeneralEffectsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return GeneralEffectsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
