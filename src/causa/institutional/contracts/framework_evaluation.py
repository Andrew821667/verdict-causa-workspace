from pydantic import BaseModel, Field

from causa.institutional.contracts.framework import (
    FrameworkConstraintSet,
    FrameworkEvaluation,
    FrameworkEvidenceMappingResult,
    FrameworkFactSet,
    build_framework_constraint_set,
    evaluate_framework_constraints,
)


class FrameworkEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: FrameworkFactSet
    expected_outcomes: dict[str, bool]


class FrameworkEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FrameworkBenchmarkReport(BaseModel):
    id: str = "framework-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[FrameworkEvaluationResult] = Field(default_factory=list)


class FrameworkRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: FrameworkFactSet
    forbidden_outcomes: dict[str, bool]


class FrameworkRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FrameworkRedTeamReport(BaseModel):
    id: str = "framework-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[FrameworkRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> FrameworkFactSet:
    values = {field_name: False for field_name in FrameworkFactSet.model_fields}
    values.update(updates)
    return FrameworkFactSet(**values)


SYNTHETIC_FRAMEWORK_BENCHMARKS = (
    FrameworkEvaluationTask(
        id="framework-bench-valid",
        title_ru="Рамочный договор заключён с определёнными общими условиями",
        facts=_facts(
            framework_agreement_concluded=True,
            framework_general_conditions_defined=True,
        ),
        expected_outcomes={
            "framework_agreement_valid": True,
            "framework_terms_apply_to_relations": True,
            "requires_human_framework_assessment": True,
        },
    ),
    FrameworkEvaluationTask(
        id="framework-bench-specified",
        title_ru="Общие условия конкретизированы отдельным договором",
        facts=_facts(
            framework_agreement_concluded=True,
            framework_general_conditions_defined=True,
            specifying_agreement_concluded=True,
        ),
        expected_outcomes={
            "specifying_agreement_on_framework": True,
            "framework_terms_apply_to_relations": True,
            "requires_human_framework_assessment": False,
        },
    ),
    FrameworkEvaluationTask(
        id="framework-bench-override",
        title_ru="Отдельный договор урегулировал отношения иначе",
        facts=_facts(
            framework_agreement_concluded=True,
            framework_general_conditions_defined=True,
            specifying_agreement_concluded=True,
            specifying_agreement_overrides=True,
        ),
        expected_outcomes={
            "framework_terms_apply_to_relations": False,
            "specifying_agreement_on_framework": True,
        },
    ),
    FrameworkEvaluationTask(
        id="framework-bench-no-conditions",
        title_ru="Рамочный договор без определённых общих условий",
        facts=_facts(framework_agreement_concluded=True),
        expected_outcomes={
            "framework_agreement_valid": False,
            "framework_terms_apply_to_relations": False,
        },
    ),
    FrameworkEvaluationTask(
        id="framework-bench-no-framework",
        title_ru="Рамочный договор не заключён",
        facts=_facts(),
        expected_outcomes={
            "framework_agreement_valid": False,
            "framework_terms_apply_to_relations": False,
            "requires_human_framework_assessment": False,
        },
    ),
    FrameworkEvaluationTask(
        id="framework-bench-subscription-valid",
        title_ru="Абонентский договор действителен, исполнение затребовано",
        facts=_facts(
            subscription_agreement_concluded=True,
            subscription_payment_agreed=True,
            subscriber_demanded_performance=True,
        ),
        expected_outcomes={
            "subscription_agreement_valid": True,
            "subscriber_entitled_to_demand": True,
            "subscription_payment_due_without_demand": False,
        },
    ),
    FrameworkEvaluationTask(
        id="framework-bench-payment-without-demand",
        title_ru="Абонент не затребовал исполнение — плата всё равно вносится",
        facts=_facts(
            subscription_agreement_concluded=True,
            subscription_payment_agreed=True,
        ),
        expected_outcomes={
            "subscription_payment_due_without_demand": True,
            "requires_human_framework_assessment": True,
        },
    ),
    FrameworkEvaluationTask(
        id="framework-bench-payment-excused",
        title_ru="Договором предусмотрено иное — плата при отсутствии требования не вносится",
        facts=_facts(
            subscription_agreement_concluded=True,
            subscription_payment_agreed=True,
            subscription_payment_excused_by_contract=True,
        ),
        expected_outcomes={
            "subscription_payment_due_without_demand": False,
            "subscription_agreement_valid": True,
            "requires_human_framework_assessment": False,
        },
    ),
    FrameworkEvaluationTask(
        id="framework-bench-subscription-no-payment",
        title_ru="Абонентский договор без согласованной платы",
        facts=_facts(subscription_agreement_concluded=True),
        expected_outcomes={
            "subscription_agreement_valid": False,
            "subscriber_entitled_to_demand": False,
            "subscription_payment_due_without_demand": False,
        },
    ),
    FrameworkEvaluationTask(
        id="framework-bench-both",
        title_ru="Рамочный конкретизирован и абонентский с затребованным исполнением",
        facts=_facts(
            framework_agreement_concluded=True,
            framework_general_conditions_defined=True,
            specifying_agreement_concluded=True,
            subscription_agreement_concluded=True,
            subscription_payment_agreed=True,
            subscriber_demanded_performance=True,
        ),
        expected_outcomes={
            "specifying_agreement_on_framework": True,
            "subscription_agreement_valid": True,
            "subscription_payment_due_without_demand": False,
            "requires_human_framework_assessment": False,
        },
    ),
)


SYNTHETIC_FRAMEWORK_RED_TEAM_CASES = (
    FrameworkRedTeamCase(
        id="framework-red-valid-without-conditions",
        title_ru="Признать рамочный договор действительным без общих условий",
        facts=_facts(framework_agreement_concluded=True),
        forbidden_outcomes={"framework_agreement_valid": True},
    ),
    FrameworkRedTeamCase(
        id="framework-red-apply-when-overridden",
        title_ru="Применять общие условия рамочного, когда указано иное",
        facts=_facts(
            framework_agreement_concluded=True,
            framework_general_conditions_defined=True,
            specifying_agreement_concluded=True,
            specifying_agreement_overrides=True,
        ),
        forbidden_outcomes={"framework_terms_apply_to_relations": True},
    ),
    FrameworkRedTeamCase(
        id="framework-red-specified-without-valid-framework",
        title_ru="Признать конкретизацию при недействительном рамочном договоре",
        facts=_facts(
            framework_agreement_concluded=True,
            specifying_agreement_concluded=True,
        ),
        forbidden_outcomes={"specifying_agreement_on_framework": True},
    ),
    FrameworkRedTeamCase(
        id="framework-red-subscription-valid-without-payment",
        title_ru="Признать абонентский договор действительным без согласованной платы",
        facts=_facts(subscription_agreement_concluded=True),
        forbidden_outcomes={"subscription_agreement_valid": True},
    ),
    FrameworkRedTeamCase(
        id="framework-red-skip-payment-without-demand",
        title_ru="Освободить абонента от платы при отсутствии требования",
        facts=_facts(
            subscription_agreement_concluded=True,
            subscription_payment_agreed=True,
        ),
        forbidden_outcomes={"subscription_payment_due_without_demand": False},
    ),
    FrameworkRedTeamCase(
        id="framework-red-charge-when-excused",
        title_ru="Взыскивать плату без требования, когда договором предусмотрено иное",
        facts=_facts(
            subscription_agreement_concluded=True,
            subscription_payment_agreed=True,
            subscription_payment_excused_by_contract=True,
        ),
        forbidden_outcomes={"subscription_payment_due_without_demand": True},
    ),
    FrameworkRedTeamCase(
        id="framework-red-entitle-without-agreement",
        title_ru="Признать право требовать исполнение без действительного абонентского договора",
        facts=_facts(subscription_agreement_concluded=True),
        forbidden_outcomes={"subscriber_entitled_to_demand": True},
    ),
    FrameworkRedTeamCase(
        id="framework-red-skip-human-on-payment",
        title_ru="Пропустить экспертную проверку при обязанности платить без требования",
        facts=_facts(
            subscription_agreement_concluded=True,
            subscription_payment_agreed=True,
        ),
        forbidden_outcomes={"requires_human_framework_assessment": False},
    ),
    FrameworkRedTeamCase(
        id="framework-red-skip-human-on-open-terms",
        title_ru="Пропустить проверку при применении общих условий без отдельного договора",
        facts=_facts(
            framework_agreement_concluded=True,
            framework_general_conditions_defined=True,
        ),
        forbidden_outcomes={"requires_human_framework_assessment": False},
    ),
    FrameworkRedTeamCase(
        id="framework-red-apply-without-valid-framework",
        title_ru="Применять общие условия при недействительном рамочном договоре",
        facts=_facts(framework_agreement_concluded=True),
        forbidden_outcomes={"framework_terms_apply_to_relations": True},
    ),
)


def _evaluate(facts: FrameworkFactSet, artifact_id: str) -> FrameworkEvaluation:
    mapping = FrameworkEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-framework-law"],
    )
    constraints: FrameworkConstraintSet = build_framework_constraint_set(mapping)
    return evaluate_framework_constraints(constraints, facts)


def _outcomes(evaluation: FrameworkEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_framework_benchmark_suite() -> FrameworkBenchmarkReport:
    results = []
    for task in SYNTHETIC_FRAMEWORK_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            FrameworkEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return FrameworkBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_framework_red_team_suite() -> FrameworkRedTeamReport:
    results = []
    for case in SYNTHETIC_FRAMEWORK_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            FrameworkRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return FrameworkRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
