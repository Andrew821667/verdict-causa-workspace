"""Приём выгрузки судебной практики из внешней базы.

Модуль принимает файл `data/practice/cases.jsonl`, который готовит агент на
машине с базой судебной практики по заданию
[`docs/practice-base-export-brief.md`](../../../../docs/practice-base-export-brief.md).

Разделение ответственности намеренное: выгрузка несёт **правовую суть** — что суд
установил и что решил, — а перевод в предикаты институтов делается здесь. Если бы
сопоставление делала выгружающая сторона, ожидаемый итог перестал бы быть
независимым от модели, которую он проверяет.

Файла может не быть: пока база недоступна, загрузчик возвращает пустой результат,
а не падает. Это позволяет держать приёмную сторону готовой заранее.
"""

import json
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

PRACTICE_BASE_SCHEMA_VERSION = "contracts-practice-base-export-v0"

#: Путь, по которому ожидается выгрузка.
PRACTICE_BASE_PATH = Path("data/practice/cases.jsonl")

#: Допустимые исходы дела.
ALLOWED_OUTCOMES = frozenset(
    {"иск_удовлетворён", "в_иске_отказано", "удовлетворён_частично", "иное"}
)

#: Допустимые состояния проверки текста.
ALLOWED_VERIFICATION = frozenset({"текст_сверен_с_первоисточником", "извлечено_из_базы_без_сверки"})

#: Темы, ради которых выгрузка запрашивается, и статьи ГК РФ за ними.
REQUESTED_TOPICS = {
    "исковая_давность": (195, 199, 200, 205, 206, 207, 208),
    "исчисление_сроков": (190, 191, 192, 193, 194),
    "злоупотребление_правом": (10,),
    "представительство": (182, 183, 185, 189),
    "согласие_на_сделку": (157, 173),
    "дееспособность": (29, 30, 171, 172, 176),
    "правоспособность_юрлица": (49, 173),
    "оборотоспособность": (129, 168),
    "форма_сделки": (158, 160, 161, 162, 163, 165),
    "заключённость": (432, 433, 438),
    "недействительность": (166, 167, 168, 178, 179, 181),
    "вещные_права": (209, 301, 302),
    "расторжение": (450, 451, 452, 453),
    "нарушение_обязательства": (309, 310, 328, 393),
}


class PracticeCase(BaseModel):
    """Одно дело из выгрузки. Поля описаны в задании агенту."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    court: str
    instance: str
    case_number: str
    decision_date: str
    source_kind: str
    source_ref: str
    verification: str
    articles_gk: list[int] = Field(default_factory=list)
    topic_tags: list[str] = Field(default_factory=list)
    fabula_ru: str
    holding_ru: str
    outcome: str
    outcome_reason_ru: str
    quote_ru: str = ""
    contains_personal_data: bool = False
    notes_ru: str = ""

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, value: str) -> str:
        if value not in ALLOWED_OUTCOMES:
            raise ValueError(
                f"Недопустимый исход дела {value!r}; ожидается один из {sorted(ALLOWED_OUTCOMES)}."
            )
        return value

    @field_validator("verification")
    @classmethod
    def validate_verification(cls, value: str) -> str:
        if value not in ALLOWED_VERIFICATION:
            raise ValueError(
                f"Недопустимое состояние проверки {value!r}; ожидается одно из "
                f"{sorted(ALLOWED_VERIFICATION)}."
            )
        return value

    @field_validator("fabula_ru", "holding_ru")
    @classmethod
    def require_substance(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "Фабула и вывод суда обязательны: без них дело нельзя перевести в предикаты."
            )
        return value


class PracticeBaseInventory(BaseModel):
    """Что пришло в выгрузке и чего в ней не хватает."""

    schema_version: str = PRACTICE_BASE_SCHEMA_VERSION
    present: bool
    total: int = 0
    cases: list[PracticeCase] = Field(default_factory=list)
    by_topic: dict[str, int] = Field(default_factory=dict)
    by_outcome: dict[str, int] = Field(default_factory=dict)
    unverified: int = 0
    with_personal_data: int = 0
    missing_topics: list[str] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


def load_practice_base(path: Path | None = None) -> PracticeBaseInventory:
    """Прочитать выгрузку и описать её состав.

    Отсутствие файла — не ошибка: пока база недоступна, возвращается пустая
    опись с `present=False`.
    """
    target = path or PRACTICE_BASE_PATH
    if not target.exists():
        return PracticeBaseInventory(
            present=False,
            missing_topics=sorted(REQUESTED_TOPICS),
            notes_ru=[
                f"Выгрузка не найдена по пути {target}. Задание на выгрузку: "
                "docs/practice-base-export-brief.md.",
            ],
        )

    cases: list[PracticeCase] = []
    seen_ids: set[str] = set()
    for number, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Строка {number} выгрузки не является JSON: {error}") from error
        case = PracticeCase.model_validate(payload)
        if case.id in seen_ids:
            raise ValueError(f"Строка {number}: повторный идентификатор дела {case.id!r}.")
        seen_ids.add(case.id)
        cases.append(case)

    by_topic = Counter(tag for case in cases for tag in case.topic_tags)
    by_outcome = Counter(case.outcome for case in cases)
    missing = sorted(topic for topic in REQUESTED_TOPICS if not by_topic.get(topic))
    notes: list[str] = []
    if missing:
        notes.append("Темы без единого дела: " + ", ".join(missing) + ".")
    unverified = sum(case.verification == "извлечено_из_базы_без_сверки" for case in cases)
    if unverified:
        notes.append(
            f"Дел без сверки с первоисточником: {unverified}. Их выводы принимаются с "
            "оговоркой о происхождении текста."
        )
    personal = sum(case.contains_personal_data for case in cases)
    if personal:
        notes.append(
            f"Дел с оставшимися персональными данными: {personal}. Требуется обезличивание "
            "до использования в отчётах."
        )
    return PracticeBaseInventory(
        present=True,
        total=len(cases),
        cases=cases,
        by_topic=dict(sorted(by_topic.items())),
        by_outcome=dict(sorted(by_outcome.items())),
        unverified=unverified,
        with_personal_data=personal,
        missing_topics=missing,
        notes_ru=notes,
    )
