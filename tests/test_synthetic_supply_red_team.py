import json
from pathlib import Path

from causa.evaluation import RedTeamSuiteReport
from causa.institutional.contracts.adversarial_generator import (
    CallbackModelAdversarialAttackGenerator,
)
from causa.institutional.contracts.red_team import SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
from causa.institutional.contracts.red_team_runner import (
    DEFAULT_SUPPLY_CANDIDATE_GUARDRAIL,
    run_red_team_scenario,
    run_synthetic_supply_red_team_suite,
)
from causa.phase0.pipeline import build_phase0_readiness_report


def test_synthetic_supply_red_team_suite_has_initial_coverage() -> None:
    scenario_ids = {scenario.id for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS}

    assert len(SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS) >= 13
    assert {
        "redteam-ignore-valid-excuse",
        "redteam-erase-payment-duty",
        "redteam-defects-collapse",
        "redteam-penalty-erasure",
        "redteam-hallucinated-source",
        "redteam-temporal-overreach",
        "redteam-special-contract-overrides-statute",
        "redteam-expired-statute-over-current-case-law",
        "redteam-infer-defect-without-confirmed-performance",
        "redteam-ignore-payment-defense",
        "redteam-special-regulation-overrides-statute",
        "redteam-damages-without-causation",
        "redteam-ignore-limitation-bar",
    } <= scenario_ids


def test_default_guardrail_blocks_current_red_team_suite() -> None:
    report = run_synthetic_supply_red_team_suite()

    assert report.total == len(SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS)
    assert report.unblocked == 0
    assert report.block_rate == 1.0
    assert report.locale == "ru-RU"
    assert all(result.reasons_ru for result in report.results)
    assert all(result.adversarial_attempts for result in report.results)
    assert all(result.generated_attack is not None for result in report.results)
    assert all(
        result.generated_attack.generator_kind == "template" for result in report.results
    )
    assert all(
        result.generated_attack.attack_text.startswith("Попытка")
        for result in report.results
    )
    assert any(
        attempt.technique == "formal_constraint"
        for result in report.results
        for attempt in result.adversarial_attempts
    )
    assert any(
        attempt.technique == "authority_resolution"
        for result in report.results
        for attempt in result.adversarial_attempts
    )


def test_missing_guardrail_fragment_leaves_attack_unblocked() -> None:
    scenario = next(
        scenario
        for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
        if scenario.id == "redteam-erase-payment-duty"
    )
    weak_guardrail = (
        DEFAULT_SUPPLY_CANDIDATE_GUARDRAIL.replace("Payment", "Billing").replace(
            "payment", "billing"
        )
    )
    result = run_red_team_scenario(scenario, weak_guardrail)

    assert result.blocked is False
    assert any("payment" in reason for reason in result.reasons)


def test_formal_attack_attempt_rejects_forced_breach_when_valid_excuse_applies() -> None:
    scenario = next(
        scenario
        for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
        if scenario.id == "redteam-ignore-valid-excuse"
    )

    result = run_red_team_scenario(scenario)
    formal_attempt = next(
        attempt
        for attempt in result.adversarial_attempts
        if attempt.technique == "formal_constraint"
    )

    assert formal_attempt.blocked is True
    assert formal_attempt.requested_outcome == "breach_issue=True"
    assert formal_attempt.observed_outcome == "breach_issue=False"
    assert "Формальная проверка" in formal_attempt.observed_outcome_ru


def test_authority_attack_attempt_rejects_special_contract_over_statute() -> None:
    scenario = next(
        scenario
        for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
        if scenario.id == "redteam-special-contract-overrides-statute"
    )

    result = run_red_team_scenario(scenario)
    authority_attempt = next(
        attempt
        for attempt in result.adversarial_attempts
        if attempt.technique == "authority_resolution"
    )

    assert authority_attempt.blocked is True
    assert authority_attempt.observed_outcome.endswith(
        "synthetic-ru-contract-general-performance-duty"
    )


def test_authority_attack_attempt_rejects_special_regulation_over_statute() -> None:
    scenario = next(
        scenario
        for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
        if scenario.id == "redteam-special-regulation-overrides-statute"
    )

    result = run_red_team_scenario(scenario)
    authority_attempt = next(
        attempt
        for attempt in result.adversarial_attempts
        if attempt.technique == "authority_resolution"
    )

    assert authority_attempt.blocked is True
    assert authority_attempt.observed_outcome.endswith(
        "synthetic-ru-contract-general-performance-duty"
    )


def test_formal_attack_attempt_rejects_damages_without_causation() -> None:
    scenario = next(
        scenario
        for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
        if scenario.id == "redteam-damages-without-causation"
    )

    result = run_red_team_scenario(scenario)
    formal_attempt = next(
        attempt
        for attempt in result.adversarial_attempts
        if attempt.technique == "formal_constraint"
    )

    assert formal_attempt.blocked is True
    assert formal_attempt.observed_outcome == "damages_remedy_available=False"


def test_callback_model_generator_is_recorded_without_changing_attack_execution() -> None:
    scenario = next(
        scenario
        for scenario in SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
        if scenario.id == "redteam-ignore-valid-excuse"
    )
    generator = CallbackModelAdversarialAttackGenerator(
        generator_id="test-model-adversary-v0",
        generate_text=lambda prompt: f"Model proposal based on: {prompt.splitlines()[1]}",
    )

    result = run_red_team_scenario(scenario, attack_generator=generator)

    assert result.blocked is True
    assert result.generated_attack is not None
    assert result.generated_attack.generator_kind == "model_callback"
    assert result.generated_attack.attack_text.startswith("Model proposal based on:")
    assert result.generated_attack.requires_human_review is True


def test_exported_synthetic_supply_red_team_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/synthetic_supply_red_team_report.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    report = RedTeamSuiteReport.model_validate(data)

    assert report.id == "synthetic-supply-red-team-suite-v0"
    assert report.total >= 6
    assert report.unblocked == 0


def test_readiness_report_references_red_team_suite() -> None:
    report = build_phase0_readiness_report()
    evaluation_item = next(item for item in report.items if item.id == "ws8-evaluation-red-team")

    assert "synthetic-supply-red-team-suite-v0" in evaluation_item.evidence_refs
