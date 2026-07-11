from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import FormalObligationRule
from causa.institutional.contracts.counterfactual_evaluation import (
    SYNTHETIC_COUNTERFACTUAL_BENCHMARKS,
    SyntheticCounterfactualEvaluationArtifact,
    run_counterfactual_benchmark_suite,
    run_counterfactual_red_team_suite,
)
from causa.institutional.contracts.legal_operators import (
    ContractLegalOperator,
    ContractLegalOperatorCode,
    ContractLegalOperatorLibrary,
    ContractCounterfactualSensitivityReport,
    build_contract_legal_operator_library,
    run_contract_counterfactual_sensitivity,
)
from causa.institutional.contracts.synthetic_counterfactual import (
    build_synthetic_counterfactual_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
)
from causa.reasoning.counterfactual import CounterfactualBudget, LegalOperatorKind
from causa.reasoning.formal_checks import (
    ObligationFactSet,
    build_obligation_constraint_set,
)


def _constraint_set():
    return build_obligation_constraint_set(
        FormalObligationRule(
            id="test-counterfactual-rule",
            source_id="synthetic-test-source",
            debtor="поставщик",
            creditor="покупатель",
            action="исполнить обязательство",
        )
    )


def _baseline_facts() -> ObligationFactSet:
    return ObligationFactSet(
        duty_exists=True,
        due_date_missed=True,
        performance_completed=True,
    )


def test_operator_library_is_complete_deterministic_and_tamper_evident() -> None:
    library = build_contract_legal_operator_library()

    assert {operator.code for operator in library.operators} == set(
        ContractLegalOperatorCode
    )
    assert library == build_contract_legal_operator_library()
    assert library.content_hash.startswith("sha256:")
    assert all(operator.requires_human_review for operator in library.operators)

    payload = library.model_dump(mode="json")
    payload["operators"][0]["title_ru"] = "Подмененный оператор"
    with pytest.raises(ValidationError, match="Hash библиотеки"):
        ContractLegalOperatorLibrary.model_validate(payload)


def test_operator_contract_rejects_direct_outcome_and_unknown_fact_mutation() -> None:
    for field_name in ("breach_issue", "invented_fact"):
        with pytest.raises(ValidationError, match="неразрешенные поля"):
            ContractLegalOperator(
                id="contract-operator:correct_performance_date",
                code=ContractLegalOperatorCode.CORRECT_PERFORMANCE_DATE,
                kind=LegalOperatorKind.CHANGE_TEMPORAL_ANCHOR,
                title_ru="Недопустимая подмена",
                legal_question_ru="Можно ли напрямую подменить результат?",
                fact_patch={field_name: False},
                required_evidence_ru=("Не применяется",),
            )


def test_operator_contract_cannot_disable_human_review() -> None:
    with pytest.raises(ValidationError, match="требует проверки юристом"):
        ContractLegalOperator(
            id="contract-operator:correct_performance_date",
            code=ContractLegalOperatorCode.CORRECT_PERFORMANCE_DATE,
            kind=LegalOperatorKind.CHANGE_TEMPORAL_ANCHOR,
            title_ru="Недопустимый оператор",
            legal_question_ru="Можно ли отключить проверку?",
            fact_patch={"due_date_missed": False},
            required_evidence_ru=("Документ о сроке",),
            requires_human_review=False,
        )


def test_sensitivity_report_is_bounded_material_and_does_not_mutate_baseline() -> None:
    baseline = _baseline_facts()
    baseline_payload = baseline.model_dump(mode="json")

    report = run_contract_counterfactual_sensitivity(
        trace_id="test-trace",
        constraint_set=_constraint_set(),
        baseline_facts=baseline,
    )

    assert baseline.model_dump(mode="json") == baseline_payload
    assert len(report.scenarios) == 7
    assert len(report.critical_scenario_ids) == 7
    assert report.skipped_operators == []
    assert report.budget_exhausted is False
    assert all(scenario.material for scenario in report.scenarios)
    assert all(scenario.baseline_fact_hash == report.baseline_fact_hash for scenario in report.scenarios)
    assert report.critical_scenario_ids[:3] == [
        "counterfactual:test-trace:activate_valid_exception",
        "counterfactual:test-trace:confirm_nonconforming_performance",
        "counterfactual:test-trace:correct_performance_date",
    ]


def test_sensitivity_report_enforces_fact_and_scenario_budgets() -> None:
    fact_limited = run_contract_counterfactual_sensitivity(
        trace_id="fact-limited",
        constraint_set=_constraint_set(),
        baseline_facts=_baseline_facts(),
        operator_codes=[ContractLegalOperatorCode.ESTABLISH_PAYMENT_DEFAULT],
        budget=CounterfactualBudget(max_changed_facts_per_scenario=1),
    )
    scenario_limited = run_contract_counterfactual_sensitivity(
        trace_id="scenario-limited",
        constraint_set=_constraint_set(),
        baseline_facts=_baseline_facts(),
        operator_codes=[
            ContractLegalOperatorCode.CORRECT_PERFORMANCE_DATE,
            ContractLegalOperatorCode.ACTIVATE_VALID_EXCEPTION,
        ],
        budget=CounterfactualBudget(max_scenarios=1),
    )

    assert fact_limited.scenarios == []
    assert fact_limited.skipped_operators[0].reason_code == "fact_budget_exceeded"
    assert len(scenario_limited.scenarios) == 1
    assert scenario_limited.budget_exhausted is True
    assert scenario_limited.skipped_operators[0].reason_code == "scenario_budget_exceeded"


def test_sensitivity_report_accepts_explicit_empty_operator_selection() -> None:
    report = run_contract_counterfactual_sensitivity(
        trace_id="empty-selection",
        constraint_set=_constraint_set(),
        baseline_facts=_baseline_facts(),
        operator_codes=[],
    )

    assert report.scenarios == []
    assert report.skipped_operators == []
    assert report.critical_scenario_ids == []


def test_sensitivity_report_rejects_tampered_baseline_hash() -> None:
    report = run_contract_counterfactual_sensitivity(
        trace_id="tamper-test",
        constraint_set=_constraint_set(),
        baseline_facts=_baseline_facts(),
    )
    payload = report.model_dump(mode="json")
    payload["baseline_fact_hash"] = "sha256:tampered"

    with pytest.raises(ValidationError, match="Hash исходных фактов"):
        ContractCounterfactualSensitivityReport.model_validate(payload)


def test_sensitivity_report_skips_operator_with_unmet_preconditions() -> None:
    report = run_contract_counterfactual_sensitivity(
        trace_id="precondition-test",
        constraint_set=_constraint_set(),
        baseline_facts=_baseline_facts().model_copy(update={"due_date_missed": False}),
        operator_codes=[ContractLegalOperatorCode.ACTIVATE_VALID_EXCEPTION],
    )

    assert report.scenarios == []
    assert report.skipped_operators[0].reason_code == "precondition_not_met"
    assert "Пропуск срока" in report.skipped_operators[0].reason_ru


def test_counterfactual_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_counterfactual_benchmark_suite()
    red_team = run_counterfactual_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_COUNTERFACTUAL_BENCHMARKS) == 7
    assert benchmark.passed == benchmark.total
    assert benchmark.failed == 0
    assert red_team.total == 7
    assert red_team.blocked == red_team.total
    assert red_team.unblocked == 0
    assert all(result.reasons_ru for result in red_team.results)


def test_reviewed_analysis_embeds_counterfactual_sensitivity() -> None:
    report = build_synthetic_supply_analysis_artifact().result.counterfactual_sensitivity

    assert report.operator_library_version == "contracts-legal-operators-ru-v1"
    assert report.baseline_evaluation.breach_issue is True
    assert len(report.scenarios) == 7
    assert "требуют проверки юристом" in report.disclaimer_ru


def test_exported_counterfactual_artifact_is_valid_and_reproducible() -> None:
    fixture_path = Path("examples/synthetic_counterfactual_evaluation_report.json")
    fixture = SyntheticCounterfactualEvaluationArtifact.model_validate_json(
        fixture_path.read_text(encoding="utf-8")
    )

    assert fixture == build_synthetic_counterfactual_evaluation_artifact()
    assert fixture.benchmark_report.failed == 0
    assert fixture.red_team_report.unblocked == 0
