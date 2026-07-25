from pydantic import BaseModel, Field

from causa.institutional.contracts.public_contract import (
    PublicContractConstraintSet,
    PublicContractEvaluation,
    PublicContractEvidenceMappingResult,
    PublicContractFactSet,
    build_public_contract_constraint_set,
    evaluate_public_contract_constraints,
)


class PublicContractEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: PublicContractFactSet
    expected_outcomes: dict[str, bool]


class PublicContractEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PublicContractBenchmarkReport(BaseModel):
    id: str = "public-contract-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[PublicContractEvaluationResult] = Field(default_factory=list)


class PublicContractRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: PublicContractFactSet
    forbidden_outcomes: dict[str, bool]


class PublicContractRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PublicContractRedTeamReport(BaseModel):
    id: str = "public-contract-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[PublicContractRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> PublicContractFactSet:
    values = {field_name: False for field_name in PublicContractFactSet.model_fields}
    values.update(updates)
    return PublicContractFactSet(**values)


SYNTHETIC_PUBLIC_CONTRACT_BENCHMARKS = (
    PublicContractEvaluationTask(
        id="public-bench-compliant",
        title_ru="Публичный договор заключён на единых условиях без нарушений",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            terms_uniform_for_category=True,
        ),
        expected_outcomes={
            "duty_to_contract_applies": True,
            "unlawful_refusal": False,
            "uniform_terms_satisfied": True,
            "requires_human_public_contract_assessment": False,
        },
    ),
    PublicContractEvaluationTask(
        id="public-bench-unlawful-refusal",
        title_ru="Необоснованный отказ при наличии возможности исполнения",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            refusal_without_lawful_ground=True,
        ),
        expected_outcomes={
            "unlawful_refusal": True,
            "requires_human_public_contract_assessment": True,
        },
    ),
    PublicContractEvaluationTask(
        id="public-bench-refusal-no-capacity",
        title_ru="Отказ при отсутствии возможности предоставить исполнение",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            refusal_without_lawful_ground=True,
        ),
        expected_outcomes={"unlawful_refusal": False},
    ),
    PublicContractEvaluationTask(
        id="public-bench-compulsion",
        title_ru="Необоснованный отказ и требование о понуждении",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            refusal_without_lawful_ground=True,
            compulsion_demanded=True,
        ),
        expected_outcomes={
            "unlawful_refusal": True,
            "compulsion_available": True,
        },
    ),
    PublicContractEvaluationTask(
        id="public-bench-unlawful-preference",
        title_ru="Недопустимое предпочтение одному лицу перед другим",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            terms_uniform_for_category=True,
            preference_given_without_legal_basis=True,
        ),
        expected_outcomes={
            "unlawful_preference": True,
            "requires_human_public_contract_assessment": True,
        },
    ),
    PublicContractEvaluationTask(
        id="public-bench-non-uniform-terms",
        title_ru="Различие условий без законных оснований",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
        ),
        expected_outcomes={
            "uniform_terms_satisfied": False,
            "requires_human_public_contract_assessment": True,
        },
    ),
    PublicContractEvaluationTask(
        id="public-bench-lawful-differentiation",
        title_ru="Различие условий допускается законом (льготы отдельным категориям)",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            lawful_differentiation=True,
        ),
        expected_outcomes={
            "uniform_terms_satisfied": True,
            "requires_human_public_contract_assessment": False,
        },
    ),
    PublicContractEvaluationTask(
        id="public-bench-void-terms",
        title_ru="Условия, противоречащие публичному режиму, ничтожны",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            terms_uniform_for_category=True,
            terms_conflict_with_public_rules=True,
        ),
        expected_outcomes={
            "discriminatory_terms_void": True,
            "requires_human_public_contract_assessment": True,
        },
    ),
    PublicContractEvaluationTask(
        id="public-bench-not-public",
        title_ru="Договор не носит публичного характера",
        facts=_facts(
            counterparty_requested_contract=True,
            performance_possible=True,
            refusal_without_lawful_ground=True,
        ),
        expected_outcomes={
            "duty_to_contract_applies": False,
            "unlawful_refusal": False,
            "requires_human_public_contract_assessment": False,
        },
    ),
    PublicContractEvaluationTask(
        id="public-bench-no-request",
        title_ru="Публичный режим без обращения контрагента",
        facts=_facts(
            public_contract_regime=True,
            performance_possible=True,
            terms_uniform_for_category=True,
        ),
        expected_outcomes={
            "duty_to_contract_applies": False,
            "unlawful_refusal": False,
        },
    ),
)


SYNTHETIC_PUBLIC_CONTRACT_RED_TEAM_CASES = (
    PublicContractRedTeamCase(
        id="public-red-refusal-lawful",
        title_ru="Признать отказ правомерным при необоснованном уклонении",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            refusal_without_lawful_ground=True,
        ),
        forbidden_outcomes={"unlawful_refusal": False},
    ),
    PublicContractRedTeamCase(
        id="public-red-duty-without-request",
        title_ru="Установить обязанность заключить договор без обращения контрагента",
        facts=_facts(
            public_contract_regime=True,
            performance_possible=True,
            terms_uniform_for_category=True,
        ),
        forbidden_outcomes={"duty_to_contract_applies": True},
    ),
    PublicContractRedTeamCase(
        id="public-red-duty-without-regime",
        title_ru="Установить обязанность заключить непубличный договор",
        facts=_facts(
            counterparty_requested_contract=True,
            performance_possible=True,
            refusal_without_lawful_ground=True,
        ),
        forbidden_outcomes={"unlawful_refusal": True},
    ),
    PublicContractRedTeamCase(
        id="public-red-compulsion-without-refusal",
        title_ru="Дать понуждение без необоснованного отказа",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            terms_uniform_for_category=True,
            compulsion_demanded=True,
        ),
        forbidden_outcomes={"compulsion_available": True},
    ),
    PublicContractRedTeamCase(
        id="public-red-preference-allowed",
        title_ru="Признать допустимым предпочтение без законных оснований",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            terms_uniform_for_category=True,
            preference_given_without_legal_basis=True,
        ),
        forbidden_outcomes={"unlawful_preference": False},
    ),
    PublicContractRedTeamCase(
        id="public-red-uniform-ignored",
        title_ru="Считать условия едиными при их различии без оснований",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
        ),
        forbidden_outcomes={"uniform_terms_satisfied": True},
    ),
    PublicContractRedTeamCase(
        id="public-red-void-terms-valid",
        title_ru="Признать действительными условия, противоречащие публичному режиму",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            terms_uniform_for_category=True,
            terms_conflict_with_public_rules=True,
        ),
        forbidden_outcomes={"discriminatory_terms_void": False},
    ),
    PublicContractRedTeamCase(
        id="public-red-skip-human-on-refusal",
        title_ru="Пропустить экспертную проверку при необоснованном отказе",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            refusal_without_lawful_ground=True,
        ),
        forbidden_outcomes={"requires_human_public_contract_assessment": False},
    ),
    PublicContractRedTeamCase(
        id="public-red-refusal-without-capacity",
        title_ru="Признать отказ неправомерным при отсутствии возможности исполнения",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            refusal_without_lawful_ground=True,
        ),
        forbidden_outcomes={"unlawful_refusal": True},
    ),
    PublicContractRedTeamCase(
        id="public-red-block-lawful-differentiation",
        title_ru="Считать условия неединообразными при законных льготах",
        facts=_facts(
            public_contract_regime=True,
            counterparty_requested_contract=True,
            performance_possible=True,
            lawful_differentiation=True,
        ),
        forbidden_outcomes={"uniform_terms_satisfied": False},
    ),
)


def _evaluate(facts: PublicContractFactSet, artifact_id: str) -> PublicContractEvaluation:
    mapping = PublicContractEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-public-contract-law"],
    )
    constraints: PublicContractConstraintSet = build_public_contract_constraint_set(mapping)
    return evaluate_public_contract_constraints(constraints, facts)


def _outcomes(evaluation: PublicContractEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_public_contract_benchmark_suite() -> PublicContractBenchmarkReport:
    results = []
    for task in SYNTHETIC_PUBLIC_CONTRACT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            PublicContractEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return PublicContractBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_public_contract_red_team_suite() -> PublicContractRedTeamReport:
    results = []
    for case in SYNTHETIC_PUBLIC_CONTRACT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            PublicContractRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return PublicContractRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
