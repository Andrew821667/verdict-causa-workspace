from pydantic import BaseModel, Field

from causa.institutional.contracts.property_rights import (
    PropertyRightsConstraintSet,
    PropertyRightsEvaluation,
    PropertyRightsEvidenceMappingResult,
    PropertyRightsFactSet,
    build_property_rights_constraint_set,
    evaluate_property_rights_constraints,
)


class PropertyRightsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: PropertyRightsFactSet
    expected_outcomes: dict[str, bool]


class PropertyRightsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PropertyRightsBenchmarkReport(BaseModel):
    id: str = "property-rights-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[PropertyRightsEvaluationResult] = Field(default_factory=list)


class PropertyRightsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: PropertyRightsFactSet
    forbidden_outcomes: dict[str, bool]


class PropertyRightsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PropertyRightsRedTeamReport(BaseModel):
    id: str = "property-rights-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[PropertyRightsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> PropertyRightsFactSet:
    values = {field_name: False for field_name in PropertyRightsFactSet.model_fields}
    values.update(updates)
    return PropertyRightsFactSet(**values)


SYNTHETIC_PROPERTY_RIGHTS_BENCHMARKS = (
    PropertyRightsEvaluationTask(
        id="property-rights-bench-not-qualified",
        title_ru="Вещное право на спорное имущество не заявлено",
        facts=_facts(vindication_rules_breached=True),
        expected_outcomes={"property_rights_qualified": False},
    ),
    PropertyRightsEvaluationTask(
        id="property-rights-bench-qualified-clean",
        title_ru="Право собственности заявлено, нарушений нет",
        facts=_facts(property_right_asserted=True),
        expected_outcomes={
            "property_rights_qualified": True,
            "requires_human_property_rights_assessment": False,
        },
    ),
    PropertyRightsEvaluationTask(
        id="property-rights-bench-ownership-powers",
        title_ru="Нарушены правомочия владения, пользования и распоряжения",
        facts=_facts(property_right_asserted=True, ownership_powers_breached=True),
        expected_outcomes={
            "ownership_powers_duty_breached": True,
            "requires_human_property_rights_assessment": True,
        },
    ),
    PropertyRightsEvaluationTask(
        id="property-rights-bench-unauthorized-disposal",
        title_ru="Имуществом распорядилось неуправомоченное лицо",
        facts=_facts(property_right_asserted=True, disposal_by_non_owner_detected=True),
        expected_outcomes={
            "unauthorized_disposal_detected": True,
            "requires_human_property_rights_assessment": True,
        },
    ),
    PropertyRightsEvaluationTask(
        id="property-rights-bench-risk-and-burden",
        title_ru="Нарушены бремя содержания и риск случайной гибели",
        facts=_facts(property_right_asserted=True, risk_and_burden_rules_breached=True),
        expected_outcomes={
            "risk_and_burden_duty_breached": True,
            "requires_human_property_rights_assessment": True,
        },
    ),
    PropertyRightsEvaluationTask(
        id="property-rights-bench-acquisition-moment",
        title_ru="Момент возникновения права собственности определён неверно",
        facts=_facts(property_right_asserted=True, acquisition_moment_rules_breached=True),
        expected_outcomes={
            "acquisition_moment_duty_breached": True,
            "requires_human_property_rights_assessment": True,
        },
    ),
    PropertyRightsEvaluationTask(
        id="property-rights-bench-prescription",
        title_ru="Нарушены правила о приобретательной давности",
        facts=_facts(property_right_asserted=True, acquisitive_prescription_breached=True),
        expected_outcomes={
            "acquisitive_prescription_duty_breached": True,
            "requires_human_property_rights_assessment": True,
        },
    ),
    PropertyRightsEvaluationTask(
        id="property-rights-bench-common-property",
        title_ru="Нарушены правила о распоряжении общей собственностью",
        facts=_facts(property_right_asserted=True, common_property_rules_breached=True),
        expected_outcomes={
            "common_property_duty_breached": True,
            "requires_human_property_rights_assessment": True,
        },
    ),
    PropertyRightsEvaluationTask(
        id="property-rights-bench-negatory",
        title_ru="Нарушена защита прав владельца, не являющегося собственником",
        facts=_facts(property_right_asserted=True, negatory_or_possessor_claim_breached=True),
        expected_outcomes={
            "negatory_claim_duty_breached": True,
            "requires_human_property_rights_assessment": True,
        },
    ),
    PropertyRightsEvaluationTask(
        id="property-rights-bench-vindication",
        title_ru="Истребование нарушено, защита добросовестного приобретателя не учтена",
        facts=_facts(
            property_right_asserted=True,
            vindication_rules_breached=True,
            good_faith_purchaser_protection_disregarded=True,
        ),
        expected_outcomes={
            "vindication_duty_breached": True,
            "good_faith_purchaser_breached": True,
            "requires_human_property_rights_assessment": True,
        },
    ),
)


SYNTHETIC_PROPERTY_RIGHTS_RED_TEAM_CASES = (
    PropertyRightsRedTeamCase(
        id="property-rights-red-qualify-without-right",
        title_ru="Применить вещно-правовые правила без заявленного права",
        facts=_facts(vindication_rules_breached=True),
        forbidden_outcomes={"property_rights_qualified": True},
    ),
    PropertyRightsRedTeamCase(
        id="property-rights-red-ignore-ownership-powers",
        title_ru="Игнорировать нарушение правомочий собственника",
        facts=_facts(property_right_asserted=True, ownership_powers_breached=True),
        forbidden_outcomes={"ownership_powers_duty_breached": False},
    ),
    PropertyRightsRedTeamCase(
        id="property-rights-red-legitimise-non-owner-disposal",
        title_ru="Признать правомерным отчуждение имущества неуправомоченным лицом",
        facts=_facts(property_right_asserted=True, disposal_by_non_owner_detected=True),
        forbidden_outcomes={"unauthorized_disposal_detected": False},
    ),
    PropertyRightsRedTeamCase(
        id="property-rights-red-ignore-risk-and-burden",
        title_ru="Освободить собственника от бремени содержания имущества",
        facts=_facts(property_right_asserted=True, risk_and_burden_rules_breached=True),
        forbidden_outcomes={"risk_and_burden_duty_breached": False},
    ),
    PropertyRightsRedTeamCase(
        id="property-rights-red-ignore-acquisition-moment",
        title_ru="Признать право возникшим без передачи и регистрации",
        facts=_facts(property_right_asserted=True, acquisition_moment_rules_breached=True),
        forbidden_outcomes={"acquisition_moment_duty_breached": False},
    ),
    PropertyRightsRedTeamCase(
        id="property-rights-red-ignore-prescription",
        title_ru="Отказать давностному владельцу в приобретении права",
        facts=_facts(property_right_asserted=True, acquisitive_prescription_breached=True),
        forbidden_outcomes={"acquisitive_prescription_duty_breached": False},
    ),
    PropertyRightsRedTeamCase(
        id="property-rights-red-ignore-common-property",
        title_ru="Допустить распоряжение общей собственностью без согласия сособственников",
        facts=_facts(property_right_asserted=True, common_property_rules_breached=True),
        forbidden_outcomes={"common_property_duty_breached": False},
    ),
    PropertyRightsRedTeamCase(
        id="property-rights-red-ignore-vindication",
        title_ru="Отказать собственнику в истребовании имущества из чужого владения",
        facts=_facts(property_right_asserted=True, vindication_rules_breached=True),
        forbidden_outcomes={"vindication_duty_breached": False},
    ),
    PropertyRightsRedTeamCase(
        id="property-rights-red-good-faith-without-vindication-breach",
        title_ru="Признать неучёт добросовестности без нарушения правил истребования",
        facts=_facts(property_right_asserted=True),
        forbidden_outcomes={"good_faith_purchaser_breached": True},
    ),
    PropertyRightsRedTeamCase(
        id="property-rights-red-skip-human-on-negatory",
        title_ru="Пропустить экспертизу при нарушении негаторной защиты",
        facts=_facts(property_right_asserted=True, negatory_or_possessor_claim_breached=True),
        forbidden_outcomes={"requires_human_property_rights_assessment": False},
    ),
)


def _evaluate(facts: PropertyRightsFactSet, artifact_id: str) -> PropertyRightsEvaluation:
    mapping = PropertyRightsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-property-rights-law"],
    )
    constraints: PropertyRightsConstraintSet = build_property_rights_constraint_set(mapping)
    return evaluate_property_rights_constraints(constraints, facts)


def _outcomes(evaluation: PropertyRightsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_property_rights_benchmark_suite() -> PropertyRightsBenchmarkReport:
    results = []
    for task in SYNTHETIC_PROPERTY_RIGHTS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            PropertyRightsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return PropertyRightsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_property_rights_red_team_suite() -> PropertyRightsRedTeamReport:
    results = []
    for case in SYNTHETIC_PROPERTY_RIGHTS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            PropertyRightsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return PropertyRightsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
