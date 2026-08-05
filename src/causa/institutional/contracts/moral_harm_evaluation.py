from pydantic import BaseModel, Field

from causa.institutional.contracts.moral_harm import (
    MoralHarmConstraintSet,
    MoralHarmEvaluation,
    MoralHarmEvidenceMappingResult,
    MoralHarmFactSet,
    build_moral_harm_constraint_set,
    evaluate_moral_harm_constraints,
)


class MoralHarmEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: MoralHarmFactSet
    expected_outcomes: dict[str, bool]


class MoralHarmEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class MoralHarmBenchmarkReport(BaseModel):
    id: str = "moral-harm-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[MoralHarmEvaluationResult] = Field(default_factory=list)


class MoralHarmRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: MoralHarmFactSet
    forbidden_outcomes: dict[str, bool]


class MoralHarmRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class MoralHarmRedTeamReport(BaseModel):
    id: str = "moral-harm-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[MoralHarmRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> MoralHarmFactSet:
    values = {field_name: False for field_name in MoralHarmFactSet.model_fields}
    values.update(updates)
    return MoralHarmFactSet(**values)


SYNTHETIC_MORAL_HARM_BENCHMARKS = (
    MoralHarmEvaluationTask(
        id="moral-harm-bench-not-qualified",
        title_ru="Причинение морального вреда не установлено",
        facts=_facts(defamation_ground_breached=True),
        expected_outcomes={"moral_harm_qualified": False},
    ),
    MoralHarmEvaluationTask(
        id="moral-harm-bench-qualified-clean",
        title_ru="Компенсация морального вреда без нарушений",
        facts=_facts(moral_harm_claim_established=True),
        expected_outcomes={
            "moral_harm_qualified": True,
            "requires_human_moral_harm_assessment": False,
        },
    ),
    MoralHarmEvaluationTask(
        id="moral-harm-bench-non-material-benefits",
        title_ru="Основания компенсации при посягательстве на нематериальные блага нарушены",
        facts=_facts(
            moral_harm_claim_established=True,
            non_material_benefits_scope_breached=True,
        ),
        expected_outcomes={
            "non_material_benefits_duty_breached": True,
            "requires_human_moral_harm_assessment": True,
        },
    ),
    MoralHarmEvaluationTask(
        id="moral-harm-bench-property-rights",
        title_ru="Компенсация при нарушении имущественных прав присуждена вне случаев закона",
        facts=_facts(
            moral_harm_claim_established=True,
            property_rights_compensation_limits_breached=True,
        ),
        expected_outcomes={
            "property_rights_limits_duty_breached": True,
            "requires_human_moral_harm_assessment": True,
        },
    ),
    MoralHarmEvaluationTask(
        id="moral-harm-bench-independence",
        title_ru="Компенсация поставлена в зависимость от возмещения имущественного вреда",
        facts=_facts(
            moral_harm_claim_established=True,
            independent_from_property_damage_breached=True,
        ),
        expected_outcomes={
            "independence_duty_breached": True,
            "requires_human_moral_harm_assessment": True,
        },
    ),
    MoralHarmEvaluationTask(
        id="moral-harm-bench-no-fault-grounds",
        title_ru="Основания компенсации независимо от вины причинителя не учтены",
        facts=_facts(
            moral_harm_claim_established=True,
            no_fault_grounds_disregarded=True,
        ),
        expected_outcomes={
            "no_fault_grounds_duty_breached": True,
            "requires_human_moral_harm_assessment": True,
        },
    ),
    MoralHarmEvaluationTask(
        id="moral-harm-bench-high-risk-source",
        title_ru="Не учтён вред, причинённый источником повышенной опасности",
        facts=_facts(
            moral_harm_claim_established=True,
            high_risk_source_ground_breached=True,
        ),
        expected_outcomes={
            "high_risk_source_ground_duty_breached": True,
            "requires_human_moral_harm_assessment": True,
        },
    ),
    MoralHarmEvaluationTask(
        id="moral-harm-bench-unlawful-prosecution",
        title_ru="Не учтено незаконное привлечение к ответственности как основание компенсации",
        facts=_facts(
            moral_harm_claim_established=True,
            unlawful_prosecution_ground_breached=True,
        ),
        expected_outcomes={
            "unlawful_prosecution_ground_duty_breached": True,
            "requires_human_moral_harm_assessment": True,
        },
    ),
    MoralHarmEvaluationTask(
        id="moral-harm-bench-defamation",
        title_ru="Не учтено распространение порочащих сведений как основание компенсации",
        facts=_facts(
            moral_harm_claim_established=True,
            defamation_ground_breached=True,
        ),
        expected_outcomes={
            "defamation_ground_duty_breached": True,
            "requires_human_moral_harm_assessment": True,
        },
    ),
    MoralHarmEvaluationTask(
        id="moral-harm-bench-compensation-form",
        title_ru="Форма и размер компенсации нарушены, особенности потерпевшего не учтены",
        facts=_facts(
            moral_harm_claim_established=True,
            compensation_form_or_amount_breached=True,
            victim_individual_features_disregarded=True,
        ),
        expected_outcomes={
            "compensation_form_duty_breached": True,
            "victim_features_breached": True,
            "requires_human_moral_harm_assessment": True,
        },
    ),
)


SYNTHETIC_MORAL_HARM_RED_TEAM_CASES = (
    MoralHarmRedTeamCase(
        id="moral-harm-red-qualify-without-harm",
        title_ru="Присудить компенсацию морального вреда без установленного вреда",
        facts=_facts(defamation_ground_breached=True),
        forbidden_outcomes={"moral_harm_qualified": True},
    ),
    MoralHarmRedTeamCase(
        id="moral-harm-red-ignore-non-material-benefits",
        title_ru="Отказать в компенсации при посягательстве на нематериальные блага",
        facts=_facts(
            moral_harm_claim_established=True,
            non_material_benefits_scope_breached=True,
        ),
        forbidden_outcomes={"non_material_benefits_duty_breached": False},
    ),
    MoralHarmRedTeamCase(
        id="moral-harm-red-ignore-property-rights-limits",
        title_ru="Присудить компенсацию за нарушение имущественных прав вне случаев закона",
        facts=_facts(
            moral_harm_claim_established=True,
            property_rights_compensation_limits_breached=True,
        ),
        forbidden_outcomes={"property_rights_limits_duty_breached": False},
    ),
    MoralHarmRedTeamCase(
        id="moral-harm-red-ignore-independence",
        title_ru="Зачесть компенсацию морального вреда в счёт имущественного возмещения",
        facts=_facts(
            moral_harm_claim_established=True,
            independent_from_property_damage_breached=True,
        ),
        forbidden_outcomes={"independence_duty_breached": False},
    ),
    MoralHarmRedTeamCase(
        id="moral-harm-red-ignore-no-fault-grounds",
        title_ru="Требовать вину причинителя во всех случаях компенсации морального вреда",
        facts=_facts(
            moral_harm_claim_established=True,
            no_fault_grounds_disregarded=True,
        ),
        forbidden_outcomes={"no_fault_grounds_duty_breached": False},
    ),
    MoralHarmRedTeamCase(
        id="moral-harm-red-ignore-high-risk-source",
        title_ru="Отказать в компенсации при вреде источником повышенной опасности",
        facts=_facts(
            moral_harm_claim_established=True,
            high_risk_source_ground_breached=True,
        ),
        forbidden_outcomes={"high_risk_source_ground_duty_breached": False},
    ),
    MoralHarmRedTeamCase(
        id="moral-harm-red-ignore-unlawful-prosecution",
        title_ru="Отказать в компенсации при незаконном привлечении к ответственности",
        facts=_facts(
            moral_harm_claim_established=True,
            unlawful_prosecution_ground_breached=True,
        ),
        forbidden_outcomes={"unlawful_prosecution_ground_duty_breached": False},
    ),
    MoralHarmRedTeamCase(
        id="moral-harm-red-ignore-defamation",
        title_ru="Отказать в компенсации при распространении порочащих сведений",
        facts=_facts(
            moral_harm_claim_established=True,
            defamation_ground_breached=True,
        ),
        forbidden_outcomes={"defamation_ground_duty_breached": False},
    ),
    MoralHarmRedTeamCase(
        id="moral-harm-red-features-without-form-breach",
        title_ru="Признать неучёт особенностей потерпевшего без нарушения размера компенсации",
        facts=_facts(moral_harm_claim_established=True),
        forbidden_outcomes={"victim_features_breached": True},
    ),
    MoralHarmRedTeamCase(
        id="moral-harm-red-skip-human-on-compensation-form",
        title_ru="Пропустить экспертизу при нарушении формы и размера компенсации",
        facts=_facts(
            moral_harm_claim_established=True,
            compensation_form_or_amount_breached=True,
        ),
        forbidden_outcomes={"requires_human_moral_harm_assessment": False},
    ),
)


def _evaluate(facts: MoralHarmFactSet, artifact_id: str) -> MoralHarmEvaluation:
    mapping = MoralHarmEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-moral-harm-law"],
    )
    constraints: MoralHarmConstraintSet = build_moral_harm_constraint_set(mapping)
    return evaluate_moral_harm_constraints(constraints, facts)


def _outcomes(evaluation: MoralHarmEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_moral_harm_benchmark_suite() -> MoralHarmBenchmarkReport:
    results = []
    for task in SYNTHETIC_MORAL_HARM_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            MoralHarmEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return MoralHarmBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_moral_harm_red_team_suite() -> MoralHarmRedTeamReport:
    results = []
    for case in SYNTHETIC_MORAL_HARM_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            MoralHarmRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return MoralHarmRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
