from pydantic import BaseModel, Field

from causa.institutional.contracts.representations import (
    RepresentationsConstraintSet,
    RepresentationsEvaluation,
    RepresentationsEvidenceMappingResult,
    RepresentationsFactSet,
    build_representations_constraint_set,
    evaluate_representations_constraints,
)


class RepresentationsEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: RepresentationsFactSet
    expected_outcomes: dict[str, bool]


class RepresentationsEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class RepresentationsBenchmarkReport(BaseModel):
    id: str = "representations-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[RepresentationsEvaluationResult] = Field(default_factory=list)


class RepresentationsRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: RepresentationsFactSet
    forbidden_outcomes: dict[str, bool]


class RepresentationsRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class RepresentationsRedTeamReport(BaseModel):
    id: str = "representations-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[RepresentationsRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> RepresentationsFactSet:
    values = {field_name: False for field_name in RepresentationsFactSet.model_fields}
    values.update(updates)
    return RepresentationsFactSet(**values)


SYNTHETIC_REPRESENTATIONS_BENCHMARKS = (
    RepresentationsEvaluationTask(
        id="representations-bench-business-liability",
        title_ru="Недостоверное заверение в предпринимательском контексте влечёт ответственность",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
            damages_or_penalty_claimed=True,
        ),
        expected_outcomes={
            "material_false_representation": True,
            "liability_basis_present": True,
            "damages_or_penalty_available": True,
            "requires_human_representations_assessment": True,
        },
    ),
    RepresentationsEvaluationTask(
        id="representations-bench-true-representation",
        title_ru="Достоверное заверение не влечёт ответственности",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
        ),
        expected_outcomes={
            "material_false_representation": False,
            "liability_basis_present": False,
        },
    ),
    RepresentationsEvaluationTask(
        id="representations-bench-no-reliance",
        title_ru="Отсутствие доверия к заверению исключает ответственность",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            given_in_business_or_corporate_context=True,
            damages_or_penalty_claimed=True,
        ),
        expected_outcomes={
            "material_false_representation": True,
            "liability_basis_present": False,
        },
    ),
    RepresentationsEvaluationTask(
        id="representations-bench-nonbusiness-unaware",
        title_ru="Непредпринимательский контекст без знания о недостоверности",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            damages_or_penalty_claimed=True,
        ),
        expected_outcomes={
            "liability_basis_present": False,
            "damages_or_penalty_available": False,
        },
    ),
    RepresentationsEvaluationTask(
        id="representations-bench-nonbusiness-aware",
        title_ru="Непредпринимательский контекст со знанием о недостоверности",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            representor_knew_or_should_have_known=True,
            damages_or_penalty_claimed=True,
        ),
        expected_outcomes={
            "liability_basis_present": True,
            "damages_or_penalty_available": True,
        },
    ),
    RepresentationsEvaluationTask(
        id="representations-bench-rescission",
        title_ru="Существенное значение заверения даёт право на отказ от договора",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
            representation_significant=True,
        ),
        expected_outcomes={
            "right_to_rescind": True,
            "requires_human_representations_assessment": True,
        },
    ),
    RepresentationsEvaluationTask(
        id="representations-bench-deception",
        title_ru="Недостоверное заверение как обман даёт основание для оспаривания",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            deception_by_false_representation=True,
        ),
        expected_outcomes={
            "avoidance_for_deception_available": True,
            "requires_human_representations_assessment": True,
        },
    ),
    RepresentationsEvaluationTask(
        id="representations-bench-liability-no-claim",
        title_ru="Основание ответственности есть, но требование не заявлено",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
        ),
        expected_outcomes={
            "liability_basis_present": True,
            "damages_or_penalty_available": False,
        },
    ),
    RepresentationsEvaluationTask(
        id="representations-bench-immaterial",
        title_ru="Недостоверное заверение без значения для договора",
        facts=_facts(
            representation_given=True,
            representation_false=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
            damages_or_penalty_claimed=True,
        ),
        expected_outcomes={
            "material_false_representation": False,
            "liability_basis_present": False,
        },
    ),
    RepresentationsEvaluationTask(
        id="representations-bench-no-representation",
        title_ru="Заверение не давалось",
        facts=_facts(
            given_in_business_or_corporate_context=True,
            damages_or_penalty_claimed=True,
        ),
        expected_outcomes={
            "material_false_representation": False,
            "liability_basis_present": False,
            "requires_human_representations_assessment": False,
        },
    ),
)


SYNTHETIC_REPRESENTATIONS_RED_TEAM_CASES = (
    RepresentationsRedTeamCase(
        id="representations-red-liability-true",
        title_ru="Возложить ответственность при достоверном заверении",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
            damages_or_penalty_claimed=True,
        ),
        forbidden_outcomes={"liability_basis_present": True},
    ),
    RepresentationsRedTeamCase(
        id="representations-red-liability-no-reliance",
        title_ru="Возложить ответственность без доверия к заверению",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            given_in_business_or_corporate_context=True,
            damages_or_penalty_claimed=True,
        ),
        forbidden_outcomes={"liability_basis_present": True},
    ),
    RepresentationsRedTeamCase(
        id="representations-red-liability-nonbusiness-unaware",
        title_ru="Возложить ответственность в непредпринимательском контексте без знания",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            damages_or_penalty_claimed=True,
        ),
        forbidden_outcomes={"liability_basis_present": True},
    ),
    RepresentationsRedTeamCase(
        id="representations-red-damages-no-claim",
        title_ru="Присудить убытки без заявленного требования",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
        ),
        forbidden_outcomes={"damages_or_penalty_available": True},
    ),
    RepresentationsRedTeamCase(
        id="representations-red-rescind-without-significance",
        title_ru="Дать право на отказ без существенного значения заверения",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
        ),
        forbidden_outcomes={"right_to_rescind": True},
    ),
    RepresentationsRedTeamCase(
        id="representations-red-avoidance-without-deception",
        title_ru="Дать основание для оспаривания без обмана",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
        ),
        forbidden_outcomes={"avoidance_for_deception_available": True},
    ),
    RepresentationsRedTeamCase(
        id="representations-red-material-without-falsity",
        title_ru="Считать заверение недостоверным без факта недостоверности",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
        ),
        forbidden_outcomes={"material_false_representation": True},
    ),
    RepresentationsRedTeamCase(
        id="representations-red-material-immaterial",
        title_ru="Считать заверение значимым при отсутствии значения",
        facts=_facts(
            representation_given=True,
            representation_false=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
        ),
        forbidden_outcomes={"material_false_representation": True},
    ),
    RepresentationsRedTeamCase(
        id="representations-red-skip-human-on-liability",
        title_ru="Пропустить экспертную проверку при наличии основания ответственности",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            given_in_business_or_corporate_context=True,
            damages_or_penalty_claimed=True,
        ),
        forbidden_outcomes={"requires_human_representations_assessment": False},
    ),
    RepresentationsRedTeamCase(
        id="representations-red-skip-human-on-deception",
        title_ru="Пропустить экспертную проверку при обмане заверением",
        facts=_facts(
            representation_given=True,
            representation_material=True,
            representation_false=True,
            reliance_by_other_party=True,
            deception_by_false_representation=True,
        ),
        forbidden_outcomes={"requires_human_representations_assessment": False},
    ),
)


def _evaluate(facts: RepresentationsFactSet, artifact_id: str) -> RepresentationsEvaluation:
    mapping = RepresentationsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-representations-law"],
    )
    constraints: RepresentationsConstraintSet = build_representations_constraint_set(mapping)
    return evaluate_representations_constraints(constraints, facts)


def _outcomes(evaluation: RepresentationsEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_representations_benchmark_suite() -> RepresentationsBenchmarkReport:
    results = []
    for task in SYNTHETIC_REPRESENTATIONS_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            RepresentationsEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return RepresentationsBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_representations_red_team_suite() -> RepresentationsRedTeamReport:
    results = []
    for case in SYNTHETIC_REPRESENTATIONS_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            RepresentationsRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return RepresentationsRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
