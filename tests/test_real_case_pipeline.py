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
    PIPELINE_REJECTION_REASONS_RU,
    UNREACHABLE_INSTITUTES_RU,
)
from causa.institutional.contracts.real_case_scenarios import REAL_CASE_SCENARIOS
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_sources,
)


def test_every_rejection_by_the_pipeline_is_explained() -> None:
    """Отказ конвейера — измеренный результат, а не сбой.

    Дело накладывается на демонстрационное дело о поставке, и сверка входов
    может признать смесь противоречивой. Раньше такого дела в наборе не было и
    отказ означал бы падение; теперь он обязан быть записан с причиной, иначе
    поломка стала бы неотличима от границы приёма.
    """
    report = run_real_case_pipeline_suite()

    assert report.total == len(REAL_CASE_SCENARIOS)
    assert report.accepted + report.rejected == report.total
    assert report.accepted >= 1

    for entry in report.results:
        assert entry.accepted or entry.rejection_explained, entry.case_number
    # Обратная сторона: запись об отказе обязана соответствовать делу, которое
    # конвейер действительно отвергает. Иначе стенд молча потерял бы окно, а
    # причина отказа осталась бы стоять как объяснение несуществующего события.
    rejected = {entry.case_id for entry in report.results if not entry.accepted}
    for case_id in PIPELINE_REJECTION_REASONS_RU:
        assert any(s.case_id == case_id for s in REAL_CASE_SCENARIOS), case_id
        assert case_id in rejected, case_id


def test_a_case_about_non_conclusion_cannot_be_overlaid_on_a_concluded_contract() -> None:
    """Граница приёма наложения названа и проверена, а не только описана.

    Дело о незаключённости сносит основание всего разбора: семь контрактов
    демонстрационного дела утверждают, что договор заключён. Это ограничение
    самого приёма «одно дело — один институт», и его следует держать видимым:
    иначе очередное такое дело выглядело бы поломкой конвейера.
    """
    report = run_real_case_pipeline_suite()

    rejected = {entry.case_number for entry in report.results if not entry.accepted}

    assert "А37-976/2025" in rejected
    assert "А67-8637/2022" in rejected
    for entry in report.results:
        if entry.case_number in rejected:
            assert "сверке входов" in entry.notes_ru[0]


def test_institute_conclusions_do_not_depend_on_the_surrounding_case() -> None:
    """Вывод института внутри конвейера тот же, что в одиночном прогоне.

    Расхождение означало бы, что вывод зависит от окружения, а не от фактов, —
    и тогда одиночный прогон в `real_case_scenarios` ничего не доказывал бы.
    """
    report = run_real_case_pipeline_suite()

    for entry in report.results:
        if not entry.accepted:
            continue
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
        if not entry.accepted:
            continue
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
    assert len(GeneralEffectsInputs.model_fields) == 22
    assert len(LAYER_FED_BY) == 16
    assert "freedom" not in LAYER_FED_BY
    # Проведён в выпуске 1.0.0: просрочка кредитора снимает основание считать
    # должника просрочившим (статья 405 пункт 3 ГК РФ).
    assert "attribution_delay" in LAYER_FED_BY
    # Проведён в выпуске 1.2.0: ничтожное решение собрания лишает основания
    # договорное условие, которое на нём держится (статьи 181.3 и 181.5 ГК РФ).
    assert "meeting_decisions" in LAYER_FED_BY


def test_institutes_that_cannot_reach_the_layer_are_named() -> None:
    """Недоходимость до слоя — измеренный факт, а не умолчание."""
    unreachable = institutes_that_cannot_reach_the_layer()

    # Считается по институтам переведённых дел, а не по всем раннерам: раннер
    # есть у каждого смоделированного института, и перечень всех недоходимых
    # описывал бы устройство слоя, а не набор дел.
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
