"""Тесты автоматической квалификации дела."""

import pytest

from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
)
from causa.ui.institute_titles import INSTITUTE_TITLES_RU
from causa.ui.qualification import (
    NOT_A_CLUSTER_PREDICATE_RU,
    SPECIALISATION,
    ClusterGroup,
    QualificationCertainty,
    build_case_qualification,
    qualification_predicates,
)


@pytest.fixture(scope="module")
def supply_result():
    return build_synthetic_supply_analysis_artifact().result


def test_every_institute_has_a_russian_title() -> None:
    """Новый институт без названия ломает сборку окна, а не показывается полем."""
    institutes = {
        name[: -len("_evaluation")]
        for name in ReviewedContractAnalysisResult.model_fields
        if name.endswith("_evaluation")
    }

    assert set(INSTITUTE_TITLES_RU) == institutes


def test_excluded_predicates_carry_a_reason() -> None:
    """Молчаливое исключение предиката неотличимо от того, что его забыли."""
    for predicate, reason in NOT_A_CLUSTER_PREDICATE_RU.items():
        assert predicate.endswith("_qualified"), predicate
        assert len(reason) > 40, predicate


def test_force_majeure_is_not_a_cluster() -> None:
    """Обстоятельство непреодолимой силы — не договорный тип."""
    predicates = qualification_predicates()

    assert "liability" not in predicates
    assert "force_majeure_qualified" in NOT_A_CLUSTER_PREDICATE_RU
    assert "force_majeure_qualified" not in predicates.values()


def test_specialisation_names_known_institutes() -> None:
    """Иерархия части второй ГК не должна ссылаться на несуществующий институт."""
    for child, parent in SPECIALISATION.items():
        assert child in INSTITUTE_TITLES_RU, child
        assert parent in INSTITUTE_TITLES_RU, parent
        assert child != parent


def test_specialisation_has_no_cycles() -> None:
    """Цикл в иерархии зациклил бы вычисление вытеснения."""
    for child in SPECIALISATION:
        seen = {child}
        parent = SPECIALISATION.get(child)
        while parent is not None:
            assert parent not in seen, child
            seen.add(parent)
            parent = SPECIALISATION.get(parent)


def test_supply_displaces_sale_and_becomes_primary(supply_result) -> None:
    """Поставка — вид купли-продажи, и основная квалификация именно она.

    Если бы вытеснение не считалось, основной оказалась бы купля-продажа
    просто потому, что она раньше по алфавиту.
    """
    qualification = build_case_qualification(supply_result)
    by_institute = {c.institute: c for c in qualification.candidates}

    assert qualification.primary is not None
    assert qualification.primary.institute == "supply"
    assert by_institute["sale"].displaced_by_special_rule is True
    assert by_institute["supply"].displaced_by_special_rule is False
    assert by_institute["supply"].specialises == "sale"


def test_resolved_hierarchy_is_not_reported_as_competition(supply_result) -> None:
    """Пара «поставка и купля-продажа» разрешена статьёй 506, а не оставлена оператору."""
    qualification = build_case_qualification(supply_result)

    assert qualification.competing is False
    assert all(
        candidate.certainty is not QualificationCertainty.COMPETING
        for candidate in qualification.candidates
    )
    assert any("устройство кодекса" in note for note in qualification.notes_ru)


def test_candidates_carry_articles_and_basis(supply_result) -> None:
    """Квалификация без основания — это утверждение без источника."""
    qualification = build_case_qualification(supply_result)

    assert qualification.candidates
    for candidate in qualification.candidates:
        assert "ГК РФ" in candidate.articles_ru, candidate.institute
        assert candidate.predicate in candidate.basis_ru
        assert candidate.group in ClusterGroup


def test_no_confidence_number_is_invented() -> None:
    """Процент уверенности взяться неоткуда, и его не должно появиться."""
    from causa.ui.qualification import ClusterCandidate

    numeric = [
        name
        for name, field in ClusterCandidate.model_fields.items()
        if field.annotation in (float, int)
    ]

    assert numeric == []


def test_empty_case_reports_that_nothing_matched(supply_result) -> None:
    """Отсутствие квалификации — ответ, а не пустой экран."""
    neutral = supply_result.model_copy(
        update={
            field: getattr(supply_result, field).model_copy(
                update={
                    name: False
                    for name in type(getattr(supply_result, field)).model_fields
                    if name.endswith("_qualified")
                }
            )
            for field in ReviewedContractAnalysisResult.model_fields
            if field.endswith("_evaluation")
        }
    )

    qualification = build_case_qualification(neutral)

    assert qualification.candidates == []
    assert qualification.primary is None
    assert any("не сработал" in note for note in qualification.notes_ru)
