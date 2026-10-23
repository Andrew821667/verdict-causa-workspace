"""Тесты предварительной сверки входов с якорными выводами."""

import pytest

from causa.institutional.contracts.anchor_preflight import (
    ANCHOR_PREFLIGHT_VERSION,
    check_anchor_consistency,
)
from causa.institutional.contracts.case_scenarios import _flip
from causa.institutional.contracts.fact_consistency import FactConsistencyError
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)


def test_demo_case_inputs_agree_with_the_anchors() -> None:
    """Демонстрационное дело согласовано — сверка не должна выдумывать расхождений."""
    report = check_anchor_consistency(build_synthetic_supply_analysis_request())

    assert report.version == ANCHOR_PREFLIGHT_VERSION
    assert report.consistent is True
    assert report.mismatches == []
    assert report.checked > 0
    assert report.anchors_ru["договорная обязанность существует"] is True
    assert "согласованы" in report.summary_ru


def test_all_mismatches_are_reported_at_once() -> None:
    """Ради этого модуль и написан: расхождения собираются разом, а не по одному.

    Прежний путь — узнавать о каждом следующем расхождении только после
    исправления предыдущего, по одному прогону анализа на расхождение.
    """
    request = build_synthetic_supply_analysis_request()
    # Договорный эффект вытеснен недействительностью, но зависимые институты
    # об этом не знают: ровно та ситуация, ради которой сверка написана.
    displaced = request.model_copy(
        update={
            "invalidity_evidence": _flip(
                request.invalidity_evidence,
                {
                    "transaction_concluded": True,
                    "violates_law": True,
                    "law_expressly_makes_void": True,
                },
            )
        }
    )

    report = check_anchor_consistency(displaced)

    assert report.consistent is False
    assert len(report.mismatches) > 1
    assert report.anchors_ru["договорный эффект вытеснен"] is True
    assert report.anchors_ru["договорная обязанность существует"] is False
    fields = {(entry.evidence_field, entry.predicate) for entry in report.mismatches}
    assert ("case_evidence", "duty_exists") in fields
    for entry in report.mismatches:
        assert entry.expected != entry.actual
        assert entry.anchor_ru.strip()
        assert entry.fix_ru.startswith("Установите ")


def test_what_the_preflight_does_not_cover_is_stated() -> None:
    """Границы сверки названы в самом отчёте, а не только в документации."""
    report = check_anchor_consistency(build_synthetic_supply_analysis_request())

    assert report.not_covered_ru
    assert any("breach_issue" in note for note in report.not_covered_ru)


@pytest.mark.parametrize(
    ("evidence_field", "updates"),
    [
        ("formation_evidence", {}),
        (
            "formation_evidence",
            {
                "acceptance_by_conduct": False,
                "performance_conduct_started_in_time": False,
                "bad_faith_non_conclusion_objection": True,
            },
        ),
        (
            "formation_evidence",
            {"acceptance_by_conduct": False, "performance_conduct_started_in_time": False},
        ),
        (
            "invalidity_evidence",
            {
                "transaction_concluded": True,
                "violates_law": True,
                "law_expressly_makes_void": True,
                "invalid_part_separable": True,
                "remainder_preserves_transaction_purpose": True,
            },
        ),
        (
            "invalidity_evidence",
            {"transaction_concluded": True, "violates_law": True, "law_expressly_makes_void": True},
        ),
    ],
    ids=[
        "демонстрационное дело",
        "возражение о незаключённости отклонено",
        "договор не заключён",
        "недействительна часть",
        "недействительна вся сделка",
    ],
)
def test_the_preflight_agrees_with_the_pipeline(evidence_field: str, updates: dict) -> None:
    """Предварительная сверка и конвейер обязаны соглашаться, согласованы ли входы.

    Выпуск 1.32.0 перевёл сверки конвейера на понятие «договор связывает стороны», а
    предварительная сверка осталась при прежнем: при отклонённом возражении о
    незаключённости она требовала бы от институтов считать договор несуществующим,
    а конвейер — нет. Расхождение нашлось при подготовке выпуска 1.33.0, при
    чтении кода; теперь оба берут понятие из одной функции модели заключения.
    """
    request = build_synthetic_supply_analysis_request()
    forged = request.model_copy(
        update={evidence_field: _flip(getattr(request, evidence_field), updates)}
    )

    preflight = check_anchor_consistency(forged)
    try:
        run_reviewed_contract_analysis(forged, build_synthetic_supply_analysis_sources())
        pipeline_accepts = True
    except FactConsistencyError:
        pipeline_accepts = False

    assert preflight.consistent is pipeline_accepts
