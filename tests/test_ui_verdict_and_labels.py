"""Тесты вердикта по делу, подписей источников и сборки интерфейса в один файл."""

import pytest

from causa.phase0.demo_trace import build_supply_dispute_demo_trace
from causa.ui.desktop import build_demo_case_view
from causa.ui.gaps import build_gap_queue
from causa.ui.labels import source_label, source_labels
from causa.ui.qualification import build_case_qualification
from causa.ui.verdict import CaseVerdict, Tone, VerdictState, build_case_verdict
from causa.ui.web_bundle import ExportNotFoundError, assert_self_contained, inline_export


@pytest.fixture(scope="module")
def trace():
    return build_supply_dispute_demo_trace()


def _verdict(result):
    qualification = build_case_qualification(result)
    return build_case_verdict(result, qualification, build_gap_queue(result))


def test_the_demo_case_leads_with_an_answer(trace) -> None:
    """Разбор без вердикта — протокол вычисления, а не результат."""
    verdict = _verdict(trace.analysis_result)

    assert verdict.state is VerdictState.BREACH_ESTABLISHED
    assert verdict.headline_ru
    assert verdict.detail_ru
    assert verdict.next_step_ru


def test_damages_unavailability_qualifies_but_does_not_replace_the_verdict(trace) -> None:
    """Ограничитель меняет то, что с выводом делать, а не сам вывод."""
    verdict = _verdict(trace.analysis_result)

    assert any("убытк" in line for line in verdict.qualifiers_ru)
    assert verdict.state is VerdictState.BREACH_ESTABLISHED


def test_displaced_conclusions_beat_the_breach_question(trace) -> None:
    """Если договор не действует, спорить о просрочке бессмысленно."""
    result = trace.analysis_result
    displaced = result.model_copy(
        update={
            "general_effects_evaluation": result.general_effects_evaluation.model_copy(
                update={"institute_conclusions_displaced": True}
            )
        }
    )

    verdict = _verdict(displaced)

    assert verdict.state is VerdictState.FINDINGS_WITHOUT_EFFECT
    assert verdict.tone is Tone.STOP


def test_a_term_without_a_meeting_basis_qualifies_the_verdict(trace) -> None:
    """Оператор обязан увидеть, что у части требования отпало основание.

    Слой не отменяет вывод о нарушении: он не знает, о каком условии спор.
    Поэтому это оговорка к вердикту, а не другой вердикт.
    """
    result = trace.analysis_result
    without_basis = result.model_copy(
        update={
            "general_effects_evaluation": result.general_effects_evaluation.model_copy(
                update={"term_deprived_of_meeting_basis": True}
            )
        }
    )

    verdict = _verdict(without_basis)

    assert verdict.state is VerdictState.BREACH_ESTABLISHED
    assert any("решени" in line and "собрани" in line for line in verdict.qualifiers_ru)


def test_limitation_bar_beats_the_breach_question(trace) -> None:
    """Давность перекрывает требование независимо от наличия нарушения."""
    result = trace.analysis_result
    barred = result.model_copy(
        update={
            "general_effects_evaluation": result.general_effects_evaluation.model_copy(
                update={"claims_barred_by_limitation": True}
            )
        }
    )

    verdict = _verdict(barred)

    assert verdict.state is VerdictState.CLAIM_BARRED
    assert "199" in verdict.detail_ru


def test_the_verdict_invents_no_confidence_number() -> None:
    """Неопределённость выражается числом пробелов, а не процентом уверенности."""
    numeric = [
        name for name, field in CaseVerdict.model_fields.items() if field.annotation in (float, int)
    ]

    assert numeric == []


def test_every_metric_carries_a_hint(trace) -> None:
    """Плитка без пояснения — число без единицы измерения."""
    verdict = _verdict(trace.analysis_result)

    assert len(verdict.metrics) >= 4
    for metric in verdict.metrics:
        assert metric.hint_ru, metric.label_ru
        assert metric.value_ru


def test_source_labels_read_like_law_not_like_identifiers() -> None:
    """Список из двадцати четырёх идентификаторов не читается никем."""
    assert source_label("synthetic-ru-gk438-443-acceptance-model-v1").label_ru == (
        "ГК РФ, статьи 438–443"
    )
    assert source_label("synthetic-ru-gk432-contract-formation-model-v1").label_ru == (
        "ГК РФ, статья 432"
    )
    assert source_label("synthetic-ru-plenum49-formation-guidance-v1").label_ru == (
        "Постановление Пленума ВС РФ № 49"
    )
    assert (
        source_label("synthetic-case-supply-1-formation-evidence").label_ru == "Заключение договора"
    )


def test_an_unknown_identifier_passes_through_unchanged() -> None:
    """Правило, которое не сработало, возвращает идентификатор, а не догадку."""
    label = source_label("некий-источник-без-соглашения")

    assert label.label_ru == "некий-источник-без-соглашения"
    assert label.recognised is False


def test_the_demo_case_sources_are_all_recognised() -> None:
    """Если бы половина подписей не разбиралась, список остался бы нечитаемым."""
    view = build_demo_case_view()

    assert len(view.sources) >= 20
    assert [source.id for source in view.sources if not source.recognised] == []


def test_labels_keep_the_identifier_next_to_the_caption() -> None:
    """Подпись — украшение над данными, а не их замена."""
    labels = source_labels(["synthetic-ru-gk333-penalty-model-v1"])

    assert labels[0].id == "synthetic-ru-gk333-penalty-model-v1"
    assert labels[0].label_ru != labels[0].id


def test_the_bundler_refuses_a_missing_export(tmp_path) -> None:
    """Собрать интерфейс, которого нет, нельзя — и ошибка об этом говорит."""
    with pytest.raises(ExportNotFoundError, match="npm run build"):
        inline_export(tmp_path)


def test_the_bundler_inlines_styles_and_scripts(tmp_path) -> None:
    """Файл, который тянет ресурсы снаружи, откроется не везде."""
    (tmp_path / "_next").mkdir()
    (tmp_path / "_next" / "app.css").write_text("body{color:red}", encoding="utf-8")
    (tmp_path / "_next" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "index.html").write_text(
        "<html><head>"
        '<link rel="preload" as="script" href="/_next/app.js"/>'
        '<link rel="stylesheet" href="/_next/app.css"/>'
        '<script src="/_next/app.js" async=""></script>'
        "</head><body><p>привет</p></body></html>",
        encoding="utf-8",
    )

    html = inline_export(tmp_path)

    assert "body{color:red}" in html
    assert "console.log(1)" in html
    assert "preload" not in html
    assert_self_contained(html)


def test_self_containment_is_checked_on_attributes_not_on_code() -> None:
    """Имя чанка внутри кода — регистрация модуля, а не запрос за ним."""
    assert_self_contained('<script>register("/_next/static/chunks/a.js")</script>')

    with pytest.raises(ValueError, match="внешние ресурсы"):
        assert_self_contained('<script src="/_next/static/chunks/a.js"></script>')
