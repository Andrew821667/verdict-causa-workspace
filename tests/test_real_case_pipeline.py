"""Тесты прогона реальных дел через весь конвейер."""

from causa.institutional.contracts.general_effects import GeneralEffectsInputs
from causa.institutional.contracts.real_case_pipeline import (
    LAYER_FED_BY,
    build_real_case_request,
    institutes_that_cannot_reach_the_layer,
    run_real_case_pipeline_suite,
)
from causa.institutional.contracts.real_case_pipeline_expectations import (
    LAYER_SILENCE_REASONS_RU,
    UNREACHABLE_INSTITUTES_RU,
)
from causa.institutional.contracts.real_case_scenarios import REAL_CASE_SCENARIOS
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_sources,
)


def test_every_real_case_passes_the_whole_pipeline() -> None:
    """Факты реальных дел не отвергаются сверками входов."""
    report = run_real_case_pipeline_suite()

    assert report.total == len(REAL_CASE_SCENARIOS)
    assert report.accepted == report.total


def test_institute_conclusions_do_not_depend_on_the_surrounding_case() -> None:
    """Вывод института внутри конвейера тот же, что в одиночном прогоне.

    Расхождение означало бы, что вывод зависит от окружения, а не от фактов, —
    и тогда одиночный прогон в `real_case_scenarios` ничего не доказывал бы.
    """
    report = run_real_case_pipeline_suite()

    for entry in report.results:
        assert entry.institute_conclusions_unchanged, (
            entry.case_number,
            entry.changed_institute_fields,
        )


def test_layer_silence_is_always_explained() -> None:
    """Дело, не дошедшее до слоя, обязано нести причину молчания.

    Без этого измерение выродилось бы в «всё хорошо»: молчание слоя ничем не
    отличалось бы от согласия с судом.
    """
    report = run_real_case_pipeline_suite()

    for entry in report.results:
        assert entry.layer_reached or entry.silence_explained, entry.case_number
    for case_id in LAYER_SILENCE_REASONS_RU:
        assert any(s.case_id == case_id for s in REAL_CASE_SCENARIOS), case_id


def test_at_least_one_case_reaches_the_final_conclusions() -> None:
    """Хотя бы одно дело обязано менять итоговые выводы.

    Если бы не менялось ни одно, набор проверял бы только то, что конвейер не
    падает, — а это гораздо более слабое утверждение.
    """
    report = run_real_case_pipeline_suite()

    assert report.reaching_the_layer >= 1
    reaching = [entry for entry in report.results if entry.layer_reached]
    for entry in reaching:
        assert entry.layer_changes
        assert entry.requires_human_resolution is True


def test_the_set_of_layer_inputs_is_pinned() -> None:
    """Список питающих институтов ведётся вручную и обязан совпасть с моделью.

    Он должен ломаться при изменении входов слоя, а не подстраиваться под них.
    """
    assert len(GeneralEffectsInputs.model_fields) == 18
    assert len(LAYER_FED_BY) == 15
    assert "freedom" not in LAYER_FED_BY
    # Проведён в выпуске 1.0.0: просрочка кредитора снимает основание считать
    # должника просрочившим (статья 405 пункт 3 ГК РФ).
    assert "attribution_delay" in LAYER_FED_BY


def test_institutes_that_cannot_reach_the_layer_are_named() -> None:
    """Недоходимость до слоя — измеренный факт, а не умолчание."""
    unreachable = institutes_that_cannot_reach_the_layer()

    assert unreachable == ["freedom"]
    for name in unreachable:
        assert name in UNREACHABLE_INSTITUTES_RU, name
        assert len(UNREACHABLE_INSTITUTES_RU[name]) > 40


def test_the_overlay_keeps_the_rest_of_the_demo_case() -> None:
    """Оговорка измерения проверяется, а не только описывается.

    Дело накладывается на демонстрационное дело о поставке: заменяются факты
    одного института, остальные контракты данных остаются прежними.
    """
    scenario = REAL_CASE_SCENARIOS[0]
    request = build_real_case_request(scenario)
    result = run_reviewed_contract_analysis(request, build_synthetic_supply_analysis_sources())

    # Профиль дела остался поставочным, а не стал профилем реального спора.
    assert result.supply_evaluation.supply_contract_qualified is True
    assert request.case_id == "case-supply-1"
