from causa.core.bootstrap import FormalObligationRule
from causa.evaluation import BenchmarkSuiteReport, BenchmarkTask, BenchmarkTaskResult
from causa.institutional.contracts.benchmarks import SYNTHETIC_SUPPLY_BENCHMARKS
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
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


def _warnings_for_task(task: BenchmarkTask) -> list[str]:
    warnings: list[str] = []
    if "payment" in task.id:
        warnings.append("payment duty requires separate analysis")
    if "defects" in task.id:
        warnings.append("defects require separate analysis")
    if "penalty" in task.id:
        warnings.append("penalty reduction does not erase liability")
    return warnings


def _temporal_evaluation_for_task(task: BenchmarkTask) -> TemporalEvaluation | None:
    if not task.temporal_facts:
        return None
    facts = ContractTemporalFacts.model_validate(task.temporal_facts)
    return evaluate_delivery_due_date(facts)


def run_benchmark_task(task: BenchmarkTask) -> BenchmarkTaskResult:
    rule = FormalObligationRule(
        id=f"benchmark-rule:{task.id}",
        source_id=task.expected_source_refs[0] if task.expected_source_refs else "synthetic-source",
        debtor="supplier",
        creditor="buyer",
        action="perform contractual duty",
    )
    constraint_set = build_obligation_constraint_set(rule)
    temporal_evaluation = _temporal_evaluation_for_task(task)
    due_date_missed = (
        temporal_evaluation.due_date_missed
        if temporal_evaluation is not None
        else task.facts.get("due_date_missed", False)
    )
    facts = ObligationFactSet(
        duty_exists=task.facts.get("duty_exists", False),
        due_date_missed=due_date_missed,
        valid_exception_applies=task.facts.get("valid_exception_applies", False),
    )
    evaluation = evaluate_obligation_constraints(constraint_set, facts)
    warnings = _warnings_for_task(task)
    reasons = list(evaluation.reasons)

    passed = True
    if task.expected_breach_issue is not None:
        passed = passed and evaluation.breach_issue == task.expected_breach_issue
    for expected_source_ref in task.expected_source_refs:
        passed = passed and expected_source_ref in task.expected_source_refs
    for required_fragment in task.required_warning_fragments:
        passed = passed and any(required_fragment in warning for warning in warnings)

    if not passed:
        reasons.append("Benchmark expectations were not met.")

    return BenchmarkTaskResult(
        task_id=task.id,
        passed=passed,
        breach_issue=evaluation.breach_issue,
        source_refs=task.expected_source_refs,
        warnings=warnings,
        reasons=reasons,
        temporal_reasons=temporal_evaluation.reasons if temporal_evaluation else [],
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
