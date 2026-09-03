"""Приём корпуса материалов дела: договоров, актов, претензий.

## Зачем нужен второй корпус

Ошибка словарного извлекателя измерена — 73 % после стоп-фраз — но измерена на
судебных актах. Словарь собирался под другой жанр: договоры и претензии. Судебный
акт пересказывает обстоятельства и часто их **отрицает** («задолженность не
подтверждена»), а договор их **устанавливает**. Число, полученное на одном жанре,
на другой не переносится, и решать по нему, годится ли извлекатель для работы,
нельзя.

Хуже того: стоп-фразы выведены по тому же корпусу, на котором измерены. Это
оценка сверху, а не held-out. Второй корпус закрывает обе дыры сразу — он и
нужного жанра, и не участвовал в подгонке правил.

## Комплект, а не документ

Единица корпуса — **комплект по одному спору**, а не отдельный документ. Причина
в устройстве самих предикатов: договор устанавливает обязанность, срок и цену, но
о том, произведено ли исполнение и заявлены ли убытки, не говорит ничего. Это
приходит из накладной, акта, претензии. Комплект из одного договора измерял бы
три предиката из двенадцати.

## Разделение ответственности

Выгружающая сторона несёт **документы**: дословный текст, вид документа, ссылку
на публичный источник. Перевод в предикаты делается здесь, как и в выгрузке
практики. Если бы разметку присылала выгружающая сторона, эталон перестал бы быть
независимым от того, что он проверяет.

## Только публичное

В корпус берутся документы, опубликованные по закону или самим правообладателем:
государственные контракты и документы об их исполнении из единой информационной
системы закупок, формы и образцы из справочно-правовой базы. Персональные данные
граждан не берутся вовсе — не обезличиваются, а не берутся: обезличивание чужого
документа силами выгружающей стороны это ещё одна интерпретация, за которую никто
не отвечает.

## Файла может не быть

Пока выгрузка не пришла, загрузчик возвращает пустой корпус, а не падает. Это
позволяет держать приёмную сторону готовой заранее — так же, как сделано для
выгрузки практики.
"""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CASE_FILE_SCHEMA_VERSION = "documents-case-file-export-v1"

#: Путь, по которому ожидается выгрузка.
CASE_FILE_CORPUS_PATH = Path("data/documents/case_files.jsonl")

#: Виды документов, которые имеет смысл собирать, и что каждый может установить.
#:
#: Список закрытый намеренно. Открытый превратился бы в свалку: «письмо»,
#: «документ», «прочее» — и корпус перестал бы отвечать на вопрос, из чего
#: складывается материал дела.
DOCUMENT_KINDS_RU: dict[str, str] = {
    "договор": "обязанность, срок исполнения, цена, порядок и срок оплаты",
    "спецификация": "предмет и количество, согласование существенных условий",
    "товарная_накладная": "состоявшаяся передача товара",
    "акт_приёма_передачи": "состоявшаяся передача и её принятие",
    "акт_выполненных_работ": "состоявшееся исполнение работ и его принятие",
    "счёт_на_оплату": "наступление срока платежа",
    "платёжный_документ": "произведённый платёж",
    "претензия": "заявленное требование, убытки, причинная связь, просрочка",
    "ответ_на_претензию": "возражение против требования, зачёт, удержание",
    "уведомление": "юридически значимое сообщение: отказ, требование, извещение",
    "соглашение_о_расторжении": "прекращение договора соглашением сторон",
    "акт_сверки": "признанная или оспариваемая задолженность",
}

#: Откуда документ взят. Источник обязан быть публичным и проверяемым.
SOURCE_KINDS_RU: dict[str, str] = {
    "еис_закупки": (
        "единая информационная система в сфере закупок: государственные "
        "контракты и документы об их исполнении публикуются по закону"
    ),
    "справочно_правовая_база": (
        "формы и образцы документов из справочно-правовой базы, опубликованные её издателем"
    ),
    "иной_публичный_источник": (
        "документ, опубликованный самим правообладателем или обязательный к "
        "опубликованию; ссылка обязательна"
    ),
}

#: Следы редакционного аппарата справочно-правовой базы.
#:
#: Те же, что вычищались из текстов норм: аппарат — не текст документа, и его
#: присутствие означает, что выгрузка скопирована из карточки вместе с обвязкой.
APPARATUS_MARKERS = (
    "Путеводитель по ",
    "(см. текст в предыдущей редакции)",
    "КонсультантПлюс: примечание",
)

#: Наименьшая длина текста документа в знаках.
#:
#: Не придирка к объёму, а защита от заголовка вместо документа: выгрузка,
#: где вместо договора стоит его название, неотличима от пустой при чтении
#: отчёта, но полностью бесполезна для измерения.
MIN_DOCUMENT_CHARACTERS = 400


class CaseFileDocument(BaseModel):
    """Один документ материалов дела, дословно."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    kind: str
    title_ru: str
    #: Дословный текст документа. Пересказ не годится: измеряется поиск по
    #: словам, и пересказ измерял бы слова пересказчика.
    text: str
    #: Ссылка на публикацию: реестровый номер, идентификатор карточки, URL.
    source_ref: str = Field(min_length=3)
    source_kind: str
    #: Обязано быть ложью: документы с персональными данными не берутся.
    contains_personal_data: bool = False

    @field_validator("kind")
    @classmethod
    def known_kind(cls, value: str) -> str:
        if value not in DOCUMENT_KINDS_RU:
            raise ValueError(
                f"Вид документа {value!r} не описан. Допустимые: "
                + ", ".join(sorted(DOCUMENT_KINDS_RU))
            )
        return value

    @field_validator("source_kind")
    @classmethod
    def known_source(cls, value: str) -> str:
        if value not in SOURCE_KINDS_RU:
            raise ValueError(
                f"Источник {value!r} не описан. Допустимые: " + ", ".join(sorted(SOURCE_KINDS_RU))
            )
        return value

    @model_validator(mode="after")
    def validate_text(self) -> "CaseFileDocument":
        if len(self.text) < MIN_DOCUMENT_CHARACTERS:
            raise ValueError(
                f"Документ {self.id}: текст короче {MIN_DOCUMENT_CHARACTERS} знаков. "
                "Похоже, вместо документа выгружено его название."
            )
        found = [marker for marker in APPARATUS_MARKERS if marker in self.text]
        if found:
            raise ValueError(
                f"Документ {self.id}: в тексте остался редакционный аппарат "
                f"({', '.join(found)}). Он не часть документа и портит поиск по словам."
            )
        if self.contains_personal_data:
            raise ValueError(
                f"Документ {self.id}: помечен как содержащий персональные данные. "
                "Такие документы в корпус не берутся — ни обезличенными, ни как есть."
            )
        return self


class CaseFile(BaseModel):
    """Комплект документов по одному спору."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = CASE_FILE_SCHEMA_VERSION
    id: str
    title_ru: str
    #: О чём спор — одним предложением, словами выгружающей стороны.
    dispute_ru: str = Field(min_length=20)
    documents: tuple[CaseFileDocument, ...] = Field(min_length=2)
    notes_ru: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_composition(self) -> "CaseFile":
        ids = [document.id for document in self.documents]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Комплект {self.id}: повторяющиеся идентификаторы документов.")
        kinds = {document.kind for document in self.documents}
        if "договор" not in kinds:
            raise ValueError(
                f"Комплект {self.id}: нет договора. Без него нечем установить "
                "обязанность, срок и цену, и остальные документы не к чему отнести."
            )
        return self


class CaseFileCorpus(BaseModel):
    """Весь корпус материалов дел."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = CASE_FILE_SCHEMA_VERSION
    case_files: tuple[CaseFile, ...] = ()

    @property
    def documents(self) -> tuple[CaseFileDocument, ...]:
        return tuple(document for case in self.case_files for document in case.documents)

    @model_validator(mode="after")
    def validate_uniqueness(self) -> "CaseFileCorpus":
        case_ids = [case.id for case in self.case_files]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("Корпус содержит комплекты с повторяющимися идентификаторами.")
        document_ids = [document.id for document in self.documents]
        if len(document_ids) != len(set(document_ids)):
            raise ValueError("Корпус содержит документы с повторяющимися идентификаторами.")
        return self


def load_case_file_corpus(path: Path = CASE_FILE_CORPUS_PATH) -> CaseFileCorpus:
    """Прочитать выгрузку. Отсутствие файла — пустой корпус, а не ошибка."""
    if not path.exists():
        return CaseFileCorpus()
    case_files = tuple(
        CaseFile.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    return CaseFileCorpus(case_files=case_files)


def describe_corpus_ru(corpus: CaseFileCorpus) -> list[str]:
    """Что в корпусе есть и чего в нём не хватает — по-русски."""
    if not corpus.case_files:
        return ["Корпус материалов дел пуст: выгрузка ещё не пришла."]
    kinds: dict[str, int] = {}
    for document in corpus.documents:
        kinds[document.kind] = kinds.get(document.kind, 0) + 1
    lines = [
        f"Комплектов: {len(corpus.case_files)}, документов: {len(corpus.documents)}.",
        "По видам: "
        + ", ".join(f"{kind} — {count}" for kind, count in sorted(kinds.items()))
        + ".",
    ]
    missing = sorted(set(DOCUMENT_KINDS_RU) - set(kinds))
    if missing:
        lines.append(
            "Ни одного документа таких видов: "
            + ", ".join(missing)
            + ". Предикаты, которые они устанавливают, корпусом не проверяются."
        )
    without_claim = [
        case.id
        for case in corpus.case_files
        if not any(document.kind == "претензия" for document in case.documents)
    ]
    if without_claim:
        lines.append(
            f"Комплектов без претензии: {len(without_claim)} из {len(corpus.case_files)}. "
            "Претензия — единственный документ, где заявляются убытки, причинная связь "
            "и требование, поэтому её отсутствие сужает измерение сильнее прочего."
        )
    return lines


def load_corpus_json(path: Path = CASE_FILE_CORPUS_PATH) -> list[dict]:
    """Сырые записи выгрузки — для проверки приёмки до разбора моделью."""
    if not path.exists():
        return []
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
