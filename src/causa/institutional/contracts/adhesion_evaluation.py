from pydantic import BaseModel, Field

from causa.institutional.contracts.adhesion import (
    AdhesionConstraintSet,
    AdhesionEvaluation,
    AdhesionEvidenceMappingResult,
    AdhesionFactSet,
    build_adhesion_constraint_set,
    evaluate_adhesion_constraints,
)


class AdhesionEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: AdhesionFactSet
    expected_outcomes: dict[str, bool]


class AdhesionEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class AdhesionBenchmarkReport(BaseModel):
    id: str = "adhesion-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[AdhesionEvaluationResult] = Field(default_factory=list)


class AdhesionRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: AdhesionFactSet
    forbidden_outcomes: dict[str, bool]


class AdhesionRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class AdhesionRedTeamReport(BaseModel):
    id: str = "adhesion-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[AdhesionRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> AdhesionFactSet:
    values = {field_name: False for field_name in AdhesionFactSet.model_fields}
    values.update(updates)
    return AdhesionFactSet(**values)


SYNTHETIC_ADHESION_BENCHMARKS = (
    AdhesionEvaluationTask(
        id="adhesion-bench-regime-no-grounds",
        title_ru="Договор присоединения без обременительных условий",
        facts=_facts(adhesion_contract=True),
        expected_outcomes={
            "adhesion_regime_applies": True,
            "grounds_for_relief_present": False,
            "relief_available": False,
            "requires_human_adhesion_assessment": False,
        },
    ),
    AdhesionEvaluationTask(
        id="adhesion-bench-onerous-relief",
        title_ru="Явно обременительные условия и заявленное требование",
        facts=_facts(
            adhesion_contract=True,
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
        ),
        expected_outcomes={
            "relief_available": True,
            "requires_human_adhesion_assessment": True,
        },
    ),
    AdhesionEvaluationTask(
        id="adhesion-bench-grounds-no-demand",
        title_ru="Основания есть, но требование не заявлено",
        facts=_facts(adhesion_contract=True, deprives_usual_rights=True),
        expected_outcomes={
            "grounds_for_relief_present": True,
            "relief_available": False,
        },
    ),
    AdhesionEvaluationTask(
        id="adhesion-bench-liability-exclusion",
        title_ru="Исключение ответственности другой стороны как основание",
        facts=_facts(
            adhesion_contract=True,
            excludes_or_limits_other_party_liability=True,
            modification_or_termination_demanded=True,
        ),
        expected_outcomes={"relief_available": True},
    ),
    AdhesionEvaluationTask(
        id="adhesion-bench-business-bar",
        title_ru="Предприниматель, знавший условия, лишён права требования",
        facts=_facts(
            adhesion_contract=True,
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
            adhering_party_business_actor=True,
            adhering_party_knew_terms=True,
        ),
        expected_outcomes={
            "business_actor_bar": True,
            "relief_available": False,
            "requires_human_adhesion_assessment": True,
        },
    ),
    AdhesionEvaluationTask(
        id="adhesion-bench-business-no-knowledge",
        title_ru="Предприниматель, не знавший условий, сохраняет право требования",
        facts=_facts(
            adhesion_contract=True,
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
            adhering_party_business_actor=True,
        ),
        expected_outcomes={
            "business_actor_bar": False,
            "relief_available": True,
        },
    ),
    AdhesionEvaluationTask(
        id="adhesion-bench-unequal-power",
        title_ru="Режим применён при явном неравенстве переговорных возможностей",
        facts=_facts(
            unequal_bargaining_power=True,
            deprives_usual_rights=True,
            modification_or_termination_demanded=True,
        ),
        expected_outcomes={
            "adhesion_regime_applies": True,
            "relief_available": True,
        },
    ),
    AdhesionEvaluationTask(
        id="adhesion-bench-individually-negotiated",
        title_ru="Условия согласованы индивидуально — режим не применяется",
        facts=_facts(
            unequal_bargaining_power=True,
            terms_individually_negotiated=True,
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
        ),
        expected_outcomes={
            "adhesion_regime_applies": False,
            "relief_available": False,
        },
    ),
    AdhesionEvaluationTask(
        id="adhesion-bench-not-adhesion",
        title_ru="Обычный договор без признаков присоединения",
        facts=_facts(
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
        ),
        expected_outcomes={
            "adhesion_regime_applies": False,
            "relief_available": False,
            "requires_human_adhesion_assessment": False,
        },
    ),
    AdhesionEvaluationTask(
        id="adhesion-bench-deprivation-demand",
        title_ru="Лишение обычных прав и заявленное требование",
        facts=_facts(
            adhesion_contract=True,
            deprives_usual_rights=True,
            modification_or_termination_demanded=True,
        ),
        expected_outcomes={
            "relief_available": True,
            "requires_human_adhesion_assessment": True,
        },
    ),
)


SYNTHETIC_ADHESION_RED_TEAM_CASES = (
    AdhesionRedTeamCase(
        id="adhesion-red-relief-without-grounds",
        title_ru="Дать изменение или расторжение без обременительных условий",
        facts=_facts(
            adhesion_contract=True,
            modification_or_termination_demanded=True,
        ),
        forbidden_outcomes={"relief_available": True},
    ),
    AdhesionRedTeamCase(
        id="adhesion-red-relief-without-demand",
        title_ru="Дать изменение или расторжение без заявленного требования",
        facts=_facts(
            adhesion_contract=True,
            manifestly_onerous_terms=True,
        ),
        forbidden_outcomes={"relief_available": True},
    ),
    AdhesionRedTeamCase(
        id="adhesion-red-relief-when-negotiated",
        title_ru="Применить режим присоединения при индивидуальном согласовании",
        facts=_facts(
            unequal_bargaining_power=True,
            terms_individually_negotiated=True,
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
        ),
        forbidden_outcomes={"relief_available": True},
    ),
    AdhesionRedTeamCase(
        id="adhesion-red-ignore-business-bar",
        title_ru="Дать право требования предпринимателю, знавшему условия",
        facts=_facts(
            adhesion_contract=True,
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
            adhering_party_business_actor=True,
            adhering_party_knew_terms=True,
        ),
        forbidden_outcomes={"relief_available": True},
    ),
    AdhesionRedTeamCase(
        id="adhesion-red-bar-uninformed-business",
        title_ru="Лишить права требования предпринимателя, не знавшего условий",
        facts=_facts(
            adhesion_contract=True,
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
            adhering_party_business_actor=True,
        ),
        forbidden_outcomes={"business_actor_bar": True},
    ),
    AdhesionRedTeamCase(
        id="adhesion-red-regime-without-signs",
        title_ru="Применить режим присоединения без его признаков",
        facts=_facts(
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
        ),
        forbidden_outcomes={"adhesion_regime_applies": True},
    ),
    AdhesionRedTeamCase(
        id="adhesion-red-skip-human-on-relief",
        title_ru="Пропустить экспертную проверку при доступном изменении",
        facts=_facts(
            adhesion_contract=True,
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
        ),
        forbidden_outcomes={"requires_human_adhesion_assessment": False},
    ),
    AdhesionRedTeamCase(
        id="adhesion-red-ignore-liability-ground",
        title_ru="Игнорировать исключение ответственности как основание",
        facts=_facts(
            adhesion_contract=True,
            excludes_or_limits_other_party_liability=True,
        ),
        forbidden_outcomes={"grounds_for_relief_present": False},
    ),
    AdhesionRedTeamCase(
        id="adhesion-red-skip-human-on-business-bar",
        title_ru="Пропустить экспертную проверку при ограничении для предпринимателя",
        facts=_facts(
            adhesion_contract=True,
            manifestly_onerous_terms=True,
            modification_or_termination_demanded=True,
            adhering_party_business_actor=True,
            adhering_party_knew_terms=True,
        ),
        forbidden_outcomes={"requires_human_adhesion_assessment": False},
    ),
    AdhesionRedTeamCase(
        id="adhesion-red-block-unequal-power",
        title_ru="Отказать в режиме при явном неравенстве переговорных возможностей",
        facts=_facts(
            unequal_bargaining_power=True,
            deprives_usual_rights=True,
            modification_or_termination_demanded=True,
        ),
        forbidden_outcomes={"adhesion_regime_applies": False},
    ),
)


def _evaluate(facts: AdhesionFactSet, artifact_id: str) -> AdhesionEvaluation:
    mapping = AdhesionEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-adhesion-law"],
    )
    constraints: AdhesionConstraintSet = build_adhesion_constraint_set(mapping)
    return evaluate_adhesion_constraints(constraints, facts)


def _outcomes(evaluation: AdhesionEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_adhesion_benchmark_suite() -> AdhesionBenchmarkReport:
    results = []
    for task in SYNTHETIC_ADHESION_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            AdhesionEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return AdhesionBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_adhesion_red_team_suite() -> AdhesionRedTeamReport:
    results = []
    for case in SYNTHETIC_ADHESION_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            AdhesionRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return AdhesionRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
