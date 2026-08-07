"""Проверка анализа на фабулах, привязанных к разъяснениям Верховного Суда РФ."""

import pytest

from causa.institutional.contracts.practice_scenarios import (
    PRACTICE_SCENARIOS,
    run_practice_scenario,
    run_practice_scenario_suite,
)


def test_every_scenario_names_a_published_source() -> None:
    """Фабула без ссылки на опубликованный акт в набор не допускается."""
    for scenario in PRACTICE_SCENARIOS:
        assert "Пленума" in scenario.source_ru
        assert scenario.source_url.startswith("https://")
        assert scenario.position_ru.strip()
        assert scenario.fabula_ru.strip()


def test_verification_status_is_stated_for_every_scenario() -> None:
    """Непроверенность источника фиксируется явно, а не умалчивается.

    Сетевая политика среды блокирует загрузку правовых сайтов, поэтому тексты
    позиций получены из выдачи поиска и постранично не сверены. Набор обязан
    это признавать.
    """
    for scenario in PRACTICE_SCENARIOS:
        assert scenario.verification.strip()
        assert "поиска" in scenario.verification


@pytest.mark.parametrize("scenario", PRACTICE_SCENARIOS, ids=lambda item: item.id)
def test_scenario_matches_published_position(scenario) -> None:
    result = run_practice_scenario(scenario)
    observed = {}
    for name in scenario.expected_outcomes:
        target = result
        for part in name.split("."):
            target = getattr(target, part)
        observed[name] = bool(target)
    assert observed == scenario.expected_outcomes


def test_practice_scenario_suite_passes_completely() -> None:
    report = run_practice_scenario_suite()

    assert report.total == len(PRACTICE_SCENARIOS)
    assert report.failed == 0, [item.mismatched for item in report.results if not item.passed]
