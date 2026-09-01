"""Тесты прогона реальных дел через весь конвейер."""

from causa.institutional.contracts.general_effects import GeneralEffectsInputs
from causa.institutional.contracts.real_case_pipeline import (
    LAYER_FED_BY,
    build_real_case_request,
    institutes_that_cannot_reach_the_layer,
    run_real_case_pipeline_suite,
)
from causa.institutional.contracts.real_case_pipeline_expectations import (
    LAYER_CONFIRMATION_ONLY_RU,
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


def test_a_case_about_non_conclusion_carries_its_own_consequences() -> None:
    """Дело о незаключённости больше не ломается о конвейер, а описывает себя.

    Раньше оно отвергалось: семь контрактов демонстрационного дела утверждали,
    что договор заключён, и сверка входов признавала смесь противоречивой. Это
    была граница приёма «одно дело — один институт», и чинить её следовало не
    исключением, а тем, чтобы дело объявило следствия позиции суда за пределами
    своего института.
    """
    scenario = next(s for s in REAL_CASE_SCENARIOS if s.case_number == "А37-976/2025")

    # Все семь расхождений, на которых конвейер обрывался, теперь названы делом.
    assert set(scenario.dependent_facts) >= {
        "temporal_effect_evidence",
        "invalidity_evidence",
        "case_evidence",
        "sale_evidence",
        "supply_evidence",
        "security_evidence",
        "termination_evidence",
    }

    report = run_real_case_pipeline_suite()
    entry = next(e for e in report.results if e.case_id == scenario.case_id)

    assert entry.accepted, entry.notes_ru
    # И правовая суть дошла до слоя: незаключённость вытесняет договор.
    assert entry.layer_changes.get("formation_defect_displaces_contract") is True
    assert entry.layer_changes.get("contract_legally_effective") is False


def test_dependent_facts_are_declared_with_a_reason_and_stay_outside_the_institute() -> None:
    """Правка чужого контракта данных обязана нести причину.

    Без этого механизм зависимых фактов превратился бы в тихое приведение
    данных к тому, что нужно конвейеру, — ровно в тот выбор версии факта за
    рецензента, от которого слой сверки отказывается.
    """
    declaring = [s for s in REAL_CASE_SCENARIOS if s.dependent_facts or s.dependent_timeline]

    assert len(declaring) == 14
    for scenario in declaring:
        assert len(scenario.dependent_facts_note_ru) > 200, scenario.case_id
        # Факты своего института живут в `facts`; смешение двух мест сделало бы
        # непонятным, что здесь перевод фабулы, а что — его следствие.
        assert f"{scenario.institute}_evidence" not in scenario.dependent_facts, scenario.case_id
        for field in scenario.dependent_facts:
            assert field.endswith("_evidence"), (scenario.case_id, field)
        for key in scenario.dependent_timeline:
            assert key in ("agreed_due_date", "actual_performance_date"), scenario.case_id


def test_the_whole_practice_set_now_reaches_the_pipeline() -> None:
    """Ни одно переведённое дело не теряется на сверке входов.

    Четырнадцать дел из пятидесяти четырёх конвейер отвергал целиком, и по ним
    юрист не видел ни одного вывода. Утверждение здесь сильное намеренно: если
    очередное дело снова начнёт отвергаться, это должно быть видно сразу и
    объяснено в `PIPELINE_REJECTION_REASONS_RU`, а не пройти незамеченным.
    """
    report = run_real_case_pipeline_suite()

    assert report.rejected == len(PIPELINE_REJECTION_REASONS_RU)
    assert report.accepted == report.total == len(REAL_CASE_SCENARIOS)


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

    # Изменение слоя бывает двух родов. Порочащее требует юриста; подтверждающее
    # — например, действительное решение собрания, которое связывает условие
    # договора, — не требует, и такие дела названы поимённо. Требовать флаг от
    # каждого означало бы считать пороком всякое влияние института на слой.
    for entry in reaching:
        assert entry.layer_changes
        if entry.case_id in LAYER_CONFIRMATION_ONLY_RU:
            assert entry.requires_human_resolution is False, entry.case_number
        else:
            assert entry.requires_human_resolution is True, entry.case_number

    assert any(entry.requires_human_resolution for entry in reaching)
    for case_id in LAYER_CONFIRMATION_ONLY_RU:
        assert any(e.case_id == case_id and e.layer_reached for e in report.results), case_id


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
    assert unreachable == ["freedom", "performance_remedies"]
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
