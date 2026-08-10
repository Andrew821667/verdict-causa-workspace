"""Тесты прогона модели на реальных делах из выгрузки судебной практики."""

import pytest

from causa.institutional.contracts.practice_base import PRACTICE_BASE_PATH, load_practice_base
from causa.institutional.contracts.real_case_scenarios import (
    INSTITUTE_RUNNERS,
    REAL_CASE_SCENARIOS,
    UNMAPPED_FINAL_CASES_RU,
    run_real_case_suite,
)


def test_model_agrees_with_the_courts_on_every_mapped_case() -> None:
    report = run_real_case_suite()

    assert report.total == len(REAL_CASE_SCENARIOS)
    assert report.failed_case_ids == [], report.results
    assert report.passed == report.total


def test_every_scenario_points_at_a_real_case_in_the_export() -> None:
    """Дело набора обязано существовать в выгрузке — с тем же номером."""
    if not PRACTICE_BASE_PATH.exists():
        pytest.skip("Выгрузка ещё не получена.")

    by_id = {case.id: case for case in load_practice_base().cases}

    for scenario in REAL_CASE_SCENARIOS:
        assert scenario.case_id in by_id, scenario.case_id
        assert by_id[scenario.case_id].case_number == scenario.case_number
        assert scenario.institute in INSTITUTE_RUNNERS


def test_no_checkable_case_is_silently_skipped() -> None:
    """Дело с окончательным исходом либо переведено, либо отказ объяснён.

    Без этой проверки набор мог бы расти только за счёт дел, на которых модель
    сходится, а неудобные оставались бы за кадром без следа.
    """
    if not PRACTICE_BASE_PATH.exists():
        pytest.skip("Выгрузка ещё не получена.")

    final_ids = {case.id for case in load_practice_base().cases if case.outcome_is_final}
    mapped = {scenario.case_id for scenario in REAL_CASE_SCENARIOS}

    unaccounted = final_ids - mapped - UNMAPPED_FINAL_CASES_RU.keys()

    assert not unaccounted, (
        f"Дела с окончательным исходом без перевода и без объяснения: {sorted(unaccounted)}."
    )


def test_declared_facts_cover_the_whole_evidence_contract() -> None:
    """Перевод фабулы задаёт все предикаты института, а не часть.

    Частичная подмена оставила бы остальные значения из демонстрационного дела о
    поставке, и вывод относился бы к смеси двух дел.
    """
    from causa.institutional.contracts.synthetic_reviewed_analysis import (
        build_synthetic_supply_analysis_request,
    )

    request = build_synthetic_supply_analysis_request()

    for scenario in REAL_CASE_SCENARIOS:
        runner = INSTITUTE_RUNNERS[scenario.institute]
        evidence = getattr(request, runner.evidence_field)
        contract = {assertion.predicate.value for assertion in evidence.assertions}
        assert scenario.facts.keys() == contract, scenario.case_id


def test_mapping_notes_are_written() -> None:
    """Каждое дело несёт запись о том, как фабула переведена в предикаты."""
    for scenario in REAL_CASE_SCENARIOS:
        assert scenario.court_holding_ru.strip()
        assert len(scenario.mapping_note_ru.strip()) > 80, scenario.case_id
