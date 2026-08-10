"""Тесты предварительной сверки входов с якорными выводами."""

from causa.institutional.contracts.anchor_preflight import (
    ANCHOR_PREFLIGHT_VERSION,
    check_anchor_consistency,
)
from causa.institutional.contracts.case_scenarios import _flip
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
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
