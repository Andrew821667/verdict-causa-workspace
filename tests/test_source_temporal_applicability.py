from datetime import date

from causa.core.models import LegalSource, SourceType
from causa.core.temporal_validity import evaluate_source_applicability


def test_source_applicable_inside_validity_window() -> None:
    source = LegalSource(
        id="source-1",
        title="Synthetic source",
        source_type=SourceType.STATUTE,
        text="Synthetic text.",
        valid_from="2020-01-01",
        valid_to="2026-12-31",
    )

    evaluation = evaluate_source_applicability(source, date(2026, 1, 15))

    assert evaluation.applicable is True
    assert evaluation.source_id == "source-1"


def test_source_not_applicable_before_valid_from() -> None:
    source = LegalSource(
        id="source-1",
        title="Synthetic source",
        source_type=SourceType.STATUTE,
        text="Synthetic text.",
        valid_from="2020-01-01",
    )

    evaluation = evaluate_source_applicability(source, date(2019, 12, 31))

    assert evaluation.applicable is False
    assert "before source valid_from" in evaluation.reasons[0]


def test_source_not_applicable_after_valid_to() -> None:
    source = LegalSource(
        id="source-1",
        title="Synthetic source",
        source_type=SourceType.STATUTE,
        text="Synthetic text.",
        valid_to="2020-01-01",
    )

    evaluation = evaluate_source_applicability(source, date(2020, 1, 2))

    assert evaluation.applicable is False
    assert "after source valid_to" in evaluation.reasons[0]
