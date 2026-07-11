from causa.core.bootstrap import FormalObligationRule
from causa.core.temporal_validity import evaluate_source_applicability
from causa.evaluation import BenchmarkSuiteReport, BenchmarkTask, BenchmarkTaskResult
from causa.institutional.contracts.authority_model import (
    AuthorityEvaluation,
    evaluate_source_authority,
)
from causa.institutional.contracts.benchmarks import SYNTHETIC_SUPPLY_BENCHMARKS
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source
from causa.institutional.contracts.temporal import (
    ContractTemporalFacts,
    TemporalEvaluation,
    evaluate_delivery_due_date,
)
from causa.reasoning.formal_checks import (
    ObligationFactSet,
    build_obligation_constraint_set,
    evaluate_obligation_constraints,
)


def _warnings_for_task(task: BenchmarkTask) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    warnings_ru: list[str] = []
    if "payment" in task.id:
        warnings.append("payment duty requires separate analysis")
        warnings_ru.append("Обязанность по оплате требует самостоятельного анализа.")
    if "defects" in task.id:
        warnings.append("defects require separate analysis")
        warnings_ru.append("Недостатки исполнения требуют самостоятельного анализа.")
    if "penalty" in task.id:
        warnings.append("penalty reduction does not erase liability")
        warnings_ru.append("Снижение неустойки не устраняет ответственность автоматически.")
    return warnings, warnings_ru


def _temporal_evaluation_for_task(task: BenchmarkTask) -> TemporalEvaluation | None:
    if not task.temporal_facts:
        return None
    facts = ContractTemporalFacts.model_validate(task.temporal_facts)
    return evaluate_delivery_due_date(facts)


def _source_applicability_reasons(
    task: BenchmarkTask,
) -> tuple[bool, list[str], list[str]]:
    if not task.temporal_facts:
        return True, [], []
    temporal_facts = ContractTemporalFacts.model_validate(task.temporal_facts)
    applicable = True
    reasons: list[str] = []
    reasons_ru: list[str] = []
    for source_ref in task.expected_source_refs:
        source = get_synthetic_contract_source(source_ref)
        evaluation = evaluate_source_applicability(source, temporal_facts.evaluation_date)
        expected = task.expected_source_applicability.get(source_ref, True)
        applicable = applicable and evaluation.applicable == expected
        reasons.extend(f"{source_ref}: {reason}" for reason in evaluation.reasons)
        reasons_ru.extend(
            f"{source_ref}: {reason}" for reason in evaluation.reasons_ru
        )
    return applicable, reasons, reasons_ru


def _authority_evaluation_for_task(
    task: BenchmarkTask,
    temporal_facts: ContractTemporalFacts | None,
) -> AuthorityEvaluation | None:
    if not task.authority_candidate_source_refs:
        return None
    sources = [
        get_synthetic_contract_source(source_ref)
        for source_ref in task.authority_candidate_source_refs
    ]
    return evaluate_source_authority(
        sources,
        moment=temporal_facts.evaluation_date if temporal_facts else None,
    )


def run_benchmark_task(task: BenchmarkTask) -> BenchmarkTaskResult:
    contract_temporal_facts = (
        ContractTemporalFacts.model_validate(task.temporal_facts)
        if task.temporal_facts
        else None
    )
    authority_evaluation = _authority_evaluation_for_task(task, contract_temporal_facts)
    rule = FormalObligationRule(
        id=f"benchmark-rule:{task.id}",
        source_id=(
            (authority_evaluation.selected_source_id if authority_evaluation else None)
            or (task.expected_source_refs[0] if task.expected_source_refs else "synthetic-source")
        ),
        debtor="supplier",
        creditor="buyer",
        action="perform contractual duty",
    )
    constraint_set = build_obligation_constraint_set(rule)
    temporal_evaluation = (
        evaluate_delivery_due_date(contract_temporal_facts)
        if contract_temporal_facts is not None
        else None
    )
    due_date_missed = (
        temporal_evaluation.due_date_missed
        if temporal_evaluation is not None
        else task.facts.get("due_date_missed", False)
    )
    fact_values = dict(task.facts)
    fact_values["due_date_missed"] = due_date_missed
    facts = ObligationFactSet.model_validate(fact_values)
    evaluation = evaluate_obligation_constraints(constraint_set, facts)
    (
        sources_applicable,
        source_applicability_reasons,
        source_applicability_reasons_ru,
    ) = _source_applicability_reasons(task)
    warnings, warnings_ru = _warnings_for_task(task)
    reasons = list(evaluation.reasons)
    reasons_ru = list(evaluation.reasons_ru)

    passed = True
    if task.expected_breach_issue is not None:
        passed = passed and evaluation.breach_issue == task.expected_breach_issue
    if task.expected_late_performance_issue is not None:
        passed = (
            passed
            and evaluation.late_performance_issue
            == task.expected_late_performance_issue
        )
    if task.expected_defect_issue is not None:
        passed = passed and evaluation.defect_issue == task.expected_defect_issue
    if task.expected_payment_default_issue is not None:
        passed = (
            passed
            and evaluation.payment_default_issue == task.expected_payment_default_issue
        )
    if task.expected_damages_remedy_available is not None:
        passed = (
            passed
            and evaluation.damages_remedy_available
            == task.expected_damages_remedy_available
        )
    if task.expected_causation_evidence_gap is not None:
        passed = (
            passed
            and evaluation.causation_evidence_gap
            == task.expected_causation_evidence_gap
        )
    if task.expected_limitation_bar is not None:
        passed = passed and evaluation.limitation_bar == task.expected_limitation_bar
    passed = passed and sources_applicable
    if task.expected_authority_winner is not None:
        passed = (
            passed
            and authority_evaluation is not None
            and authority_evaluation.selected_source_id == task.expected_authority_winner
        )
    if task.expected_authority_rules:
        authority_rules = (
            {rule.value for rule in authority_evaluation.applied_rules}
            if authority_evaluation is not None
            else set()
        )
        passed = passed and set(task.expected_authority_rules) <= authority_rules
    for expected_source_ref in task.expected_source_refs:
        passed = passed and expected_source_ref in task.expected_source_refs
    for required_fragment in task.required_warning_fragments:
        passed = passed and any(required_fragment in warning for warning in warnings)

    if not passed:
        reasons.append("Benchmark expectations were not met.")
        reasons_ru.append("Ожидаемый результат контрольной задачи не достигнут.")

    return BenchmarkTaskResult(
        task_id=task.id,
        passed=passed,
        breach_issue=evaluation.breach_issue,
        late_performance_issue=evaluation.late_performance_issue,
        defect_issue=evaluation.defect_issue,
        payment_default_issue=evaluation.payment_default_issue,
        damages_remedy_available=evaluation.damages_remedy_available,
        causation_evidence_gap=evaluation.causation_evidence_gap,
        limitation_bar=evaluation.limitation_bar,
        source_refs=task.expected_source_refs,
        warnings=warnings,
        warnings_ru=warnings_ru,
        reasons=reasons,
        reasons_ru=reasons_ru,
        temporal_reasons=temporal_evaluation.reasons if temporal_evaluation else [],
        temporal_reasons_ru=(
            temporal_evaluation.reasons_ru if temporal_evaluation else []
        ),
        source_applicability_reasons=source_applicability_reasons,
        source_applicability_reasons_ru=source_applicability_reasons_ru,
        authority_winner=(
            authority_evaluation.selected_source_id if authority_evaluation else None
        ),
        authority_reasons=authority_evaluation.reasons if authority_evaluation else [],
        authority_reasons_ru=(
            authority_evaluation.reasons_ru if authority_evaluation else []
        ),
        authority_rules=(
            [rule.value for rule in authority_evaluation.applied_rules]
            if authority_evaluation
            else []
        ),
        authority_excluded_source_refs=(
            authority_evaluation.excluded_source_ids if authority_evaluation else []
        ),
    )


def run_synthetic_supply_benchmark_suite(
    tasks: list[BenchmarkTask] | None = None,
) -> BenchmarkSuiteReport:
    selected_tasks = tasks or SYNTHETIC_SUPPLY_BENCHMARKS
    results = [run_benchmark_task(task) for task in selected_tasks]
    passed = sum(result.passed for result in results)

    return BenchmarkSuiteReport(
        id="synthetic-supply-benchmark-suite-v0",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )
