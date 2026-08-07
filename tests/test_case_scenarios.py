"""Сквозная проверка анализа на смоделированных фабулах дел."""

import pytest

from causa.institutional.contracts.case_scenarios import (
    CASE_SCENARIOS,
    run_case_scenario,
    run_case_scenario_suite,
)


def test_suite_covers_at_least_ten_modelled_situations() -> None:
    assert len(CASE_SCENARIOS) >= 10
    assert len({scenario.id for scenario in CASE_SCENARIOS}) == len(CASE_SCENARIOS)


def test_every_scenario_states_its_legal_basis() -> None:
    """Ожидаемый результат выведен из закона, а не считан с вывода системы."""
    for scenario in CASE_SCENARIOS:
        assert scenario.fabula_ru.strip()
        assert "ГК РФ" in scenario.legal_basis_ru
        assert scenario.expected_outcomes


@pytest.mark.parametrize("scenario", CASE_SCENARIOS, ids=lambda item: item.id)
def test_scenario_matches_expected_legal_outcome(scenario) -> None:
    result = run_case_scenario(scenario)
    observed = {}
    for name in scenario.expected_outcomes:
        target = result
        for part in name.split("."):
            target = getattr(target, part)
        observed[name] = bool(target)
    assert observed == scenario.expected_outcomes


def test_case_scenario_suite_passes_completely() -> None:
    report = run_case_scenario_suite()

    assert report.total == len(CASE_SCENARIOS)
    assert report.failed == 0, [item.mismatched for item in report.results if not item.passed]
