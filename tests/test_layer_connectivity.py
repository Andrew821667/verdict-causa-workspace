"""Тесты аудита связности со слоем общих положений."""

from causa.institutional.contracts.layer_connectivity import (
    LAYER_CONNECTIVITY_AUDIT,
    VERDICT_LABELS_RU,
    ConnectivityEntry,
    ConnectivityVerdict,
    audit_layer_connectivity,
)
from causa.institutional.contracts.real_case_pipeline import LAYER_FED_BY
from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult


def _institutes() -> list[str]:
    layers = {"general_effects", "general_consistency"}
    return sorted(
        name[: -len("_evaluation")]
        for name in ReviewedContractAnalysisResult.model_fields
        if name.endswith("_evaluation") and name[: -len("_evaluation")] not in layers
    )


def test_every_institute_outside_the_layer_carries_a_reason() -> None:
    """«Не доходит» без причины неотличимо от «забыли провести»."""
    report = audit_layer_connectivity()

    assert report.unaudited == []
    assert report.audited == len(_institutes()) - len(LAYER_FED_BY)


def test_feeding_institutes_are_not_in_the_audit() -> None:
    """Институт либо питает слой, либо объясняет, почему нет — не оба сразу."""
    for name in LAYER_FED_BY:
        assert name not in LAYER_CONNECTIVITY_AUDIT, name


def test_every_reason_is_written_out() -> None:
    """Причина обязана быть содержательной, а не отпиской."""
    for name, (verdict, reason) in LAYER_CONNECTIVITY_AUDIT.items():
        assert isinstance(verdict, ConnectivityVerdict), name
        assert len(reason) > 60, name
        assert verdict in VERDICT_LABELS_RU, name


def test_no_institute_is_left_without_a_path_to_the_layer() -> None:
    """Все три института, найденные аудитом, проведены в слой.

    `attribution_delay` — выпуском 1.0.0, `obligation_dynamics` — 1.1.0,
    `meeting_decisions` — 1.2.0. Отчёт обязан сказать об этом прямо: молчание о
    долге неотличимо от поломки показа долга.
    """
    report = audit_layer_connectivity()

    assert report.open_wiring_debt == []
    assert any("Открытого долга связности нет" in note for note in report.notes_ru)
    assert "should_be_wired" not in report.by_verdict


def test_the_debt_category_still_works_when_it_is_empty() -> None:
    """Закрытие последнего долга не должно превращать проверку в вечнозелёную.

    Категория остаётся в модели ради следующего института, вывод которого
    окажется без пути в слой, поэтому проверяются требования к записи долга, а
    не только его отсутствие сегодня.
    """
    assert ConnectivityVerdict.SHOULD_BE_WIRED in VERDICT_LABELS_RU

    debt = ConnectivityEntry(
        institute="synthetic_institute",
        verdict=ConnectivityVerdict.SHOULD_BE_WIRED,
        verdict_ru=VERDICT_LABELS_RU[ConnectivityVerdict.SHOULD_BE_WIRED],
        reason_ru=(
            "вывод по праву меняет судьбу требования и опирается на статью закона, "
            "но до слоя не доходит"
        ),
    )

    assert debt.verdict is ConnectivityVerdict.SHOULD_BE_WIRED
    # Долг обязан называть норму, из которой следует связь.
    assert "стать" in debt.reason_ru or "глав" in debt.reason_ru


def test_the_audit_does_not_invent_institutes() -> None:
    """Аудит описывает существующие институты, а не воображаемые."""
    known = set(_institutes())

    assert set(LAYER_CONNECTIVITY_AUDIT) <= known


def test_special_types_are_the_largest_group_and_share_one_reason() -> None:
    """Специальные договорные типы — решение по одному основанию, а не 48 отписок."""
    report = audit_layer_connectivity()

    special = [
        entry for entry in report.entries if entry.verdict is ConnectivityVerdict.SPECIAL_TYPE
    ]
    assert len(special) == report.by_verdict["special_type"] >= 40
    assert len({entry.reason_ru for entry in special}) == 1
