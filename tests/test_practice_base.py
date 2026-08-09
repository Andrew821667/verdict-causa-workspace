"""Тесты приёма выгрузки судебной практики из внешней базы."""

import json

import pytest
from pydantic import ValidationError

from causa.institutional.contracts.practice_base import (
    PRACTICE_BASE_PATH,
    REQUESTED_TOPICS,
    PracticeCase,
    load_practice_base,
)

_VALID = {
    "id": "a40-12345-2023",
    "court": "Арбитражный суд города Москвы",
    "instance": "первая",
    "case_number": "А40-12345/2023",
    "decision_date": "2023-05-17",
    "source_kind": "kad.arbitr.ru",
    "source_ref": "https://kad.arbitr.ru/Card/example",
    "verification": "текст_сверен_с_первоисточником",
    "articles_gk": [199, 506],
    "topic_tags": ["исковая_давность", "поставка"],
    "fabula_ru": "Поставщик передал товар с просрочкой; ответчик заявил о применении давности.",
    "holding_ru": "Суд установил истечение срока и отказал в иске.",
    "outcome": "в_иске_отказано",
    "outcome_reason_ru": "истечение срока исковой давности по заявлению стороны",
    "quote_ru": "Истечение срока исковой давности является основанием к отказу в иске.",
    "contains_personal_data": False,
    "notes_ru": "",
}


def test_missing_export_is_not_an_error(tmp_path) -> None:
    """Отсутствие выгрузки возвращает пустую опись, а не падает."""
    inventory = load_practice_base(tmp_path / "нет-такого-файла.jsonl")

    assert inventory.present is False
    assert inventory.total == 0
    assert set(inventory.missing_topics) == set(REQUESTED_TOPICS)
    assert any("нет-такого-файла.jsonl" in note for note in inventory.notes_ru)


def test_repository_export_loads() -> None:
    """Выгрузка, лежащая в репозитории, читается приёмной стороной без правок."""
    if not PRACTICE_BASE_PATH.exists():
        pytest.skip("Выгрузка ещё не получена.")

    inventory = load_practice_base()

    assert inventory.present is True
    assert inventory.total > 0
    # Метки выгрузки приведены к запрошенным темам: нераспознанных не остаётся.
    assert inventory.unknown_topics == []


def test_case_requires_substance_and_valid_outcome() -> None:
    with pytest.raises(ValidationError, match="Фабула и вывод суда обязательны"):
        PracticeCase.model_validate({**_VALID, "fabula_ru": "   "})

    with pytest.raises(ValidationError, match="Недопустимый исход дела"):
        PracticeCase.model_validate({**_VALID, "outcome": "выиграли"})

    with pytest.raises(ValidationError, match="Недопустимое состояние проверки"):
        PracticeCase.model_validate({**_VALID, "verification": "наверное"})


def test_export_is_read_and_described(tmp_path) -> None:
    second = {
        **_VALID,
        "id": "a41-777-2024",
        "topic_tags": ["злоупотребление_правом"],
        "verification": "извлечено_из_базы_без_сверки",
        "outcome": "удовлетворён_частично",
        "contains_personal_data": True,
    }
    export = tmp_path / "cases.jsonl"
    export.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in (_VALID, second)) + "\n",
        encoding="utf-8",
    )

    inventory = load_practice_base(export)

    assert inventory.present is True
    assert inventory.total == 2
    assert inventory.by_topic["исковая_давность"] == 1
    assert inventory.by_outcome["в_иске_отказано"] == 1
    # Непроверенные тексты и персональные данные названы, а не проглочены.
    assert inventory.unverified == 1
    assert inventory.with_personal_data == 1
    assert any("без сверки" in note for note in inventory.notes_ru)
    assert any("персональными данными" in note for note in inventory.notes_ru)
    # Темы без единого дела перечисляются, чтобы выгрузку можно было дополнить.
    assert "недействительность" in inventory.missing_topics


def test_articles_with_a_point_survive_the_import() -> None:
    """Статьи ГК РФ с точкой — не ошибка выгрузки.

    Первая полученная выгрузка сослалась на статьи 181.3, 181.5, 327.1, 388.1 и
    393.1. Приёмная сторона объявляла номер статьи целым числом и отвергала их;
    отвергала она при этом действующие нормы, а не испорченные данные.
    """
    case = PracticeCase.model_validate({**_VALID, "articles_gk": [181.3, 327.1, 199, "393.1"]})

    assert case.articles_gk == ["181.3", "327.1", "199", "393.1"]

    with pytest.raises(ValidationError, match="Недопустимый номер статьи"):
        PracticeCase.model_validate({**_VALID, "articles_gk": ["статья 199"]})


def test_topic_labels_from_the_brief_are_mapped_to_requested_topics() -> None:
    """Метки, названные прозой задания, приводятся к ключам перечня тем.

    Расхождение внесено заданием агенту, где темы названы иначе, чем ключи
    здесь. Согласование сделано на приёмной стороне.
    """
    case = PracticeCase.model_validate(
        {**_VALID, "topic_tags": ["изменение_и_расторжение_договора", "заключенность_договора"]}
    )

    assert case.topic_tags == ["расторжение", "заключённость"]
    assert all(tag in REQUESTED_TOPICS for tag in case.topic_tags)


def test_remand_decisions_are_counted_apart_from_final_outcomes(tmp_path) -> None:
    """Отмена с направлением на новое рассмотрение не даёт ожидаемого итога спора."""
    remand = {**_VALID, "id": "vs-remand", "outcome": "иное"}
    export = tmp_path / "cases.jsonl"
    export.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in (_VALID, remand)) + "\n",
        encoding="utf-8",
    )

    inventory = load_practice_base(export)

    assert inventory.total == 2
    assert inventory.with_final_outcome == 1
    assert any("окончательным исходом" in note for note in inventory.notes_ru)


def test_duplicate_case_id_is_rejected(tmp_path) -> None:
    export = tmp_path / "cases.jsonl"
    export.write_text(
        "\n".join(json.dumps(_VALID, ensure_ascii=False) for _ in range(2)) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="повторный идентификатор дела"):
        load_practice_base(export)
