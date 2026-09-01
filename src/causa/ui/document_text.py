"""Чтение приложенных документов и поиск мест, относящихся к пробелам.

## Что здесь появилось и что не появилось

Появилось: стенд теперь **достаёт текст** из приложенного файла и показывает
его оператору, а также находит в нём места, которые могут относиться к
конкретному открытому вопросу.

Не появилось: извлечения фактов. Система по-прежнему не понимает документ и не
делает из него выводов. Найденное место — это совпадение по словам, а не
установленное обстоятельство, и в интерфейсе оно называется именно так.

Разница здесь не терминологическая. Поиск по словам ошибается предсказуемо:
слово «неустойка» в оглавлении договора ничего не устанавливает. Утверждение о
факте по-прежнему делает оператор, а документ остаётся записанным основанием
этого утверждения. Меняется одно: раньше оператор читал документ у себя, теперь
может прочитать нужное место здесь.

## Почему поиск по словам, а не модель

Потому что здесь модель не вызывается: в этом репозитории ключа нет и обращаться
к нему нельзя. Поиск по словам — то, что можно сделать честно и проверяемо:
правило видно, ошибку видно, воспроизводимость полная.

В эксплуатации языковая модель подключается ключом, и место, куда она
подключается, построено отдельно — [`fact_extraction`](fact_extraction.py).
Важно, что там она предлагает, а не устанавливает: предложение становится
фактом только после того, как юрист назвал себя, назвал значение сам и цитата
предложения сверена с текстом документа дословно. Словарь ниже от этого не
исчезает: он остаётся тем, что работает без ключа вообще.

## Форматы

`.txt`, `.md`, `.csv` — прямое декодирование (UTF-8, при неудаче CP1251:
русские документы из старых систем приходят именно в ней).

`.docx` — распаковка zip и разбор `word/document.xml` средствами стандартной
библиотеки. Абзацы разделяются по `</w:p>`, иначе текст слипается в одну строку.

`.pdf` — через `pypdf`, если он установлен. Если нет — честный отказ, а не
пустой текст: пустой текст неотличим от документа без слов.

Скан без текстового слоя не читается ничем из перечисленного, и это тоже
сказано прямо, а не выглядит как пустой документ.
"""

import re
import zipfile
from datetime import date
from html import unescape
from io import BytesIO
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field

from causa.ui.documents import ClosureKind, UploadedDocument
from causa.ui.gaps import TypedGap

DOCUMENT_TEXT_VERSION = "ui-document-text-v0"

#: Сколько знаков текста стенд оставляет от одного документа.
#:
#: Ограничение не техническое, а смысловое: стенд показывает место в документе,
#: а не хранит дело. Договор на тысячу страниц здесь читать незачем.
MAX_TEXT_CHARACTERS = 400_000

#: Сколько знаков контекста показывать вокруг найденного слова.
QUOTE_RADIUS = 220

#: Сколько мест показывать по одному вопросу. Больше — это уже не подсказка.
MAX_FRAGMENTS_PER_GAP = 5


class ExtractedText(BaseModel):
    """Текст документа — или честная запись о том, почему его нет."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = DOCUMENT_TEXT_VERSION
    document_id: str
    filename: str
    #: Ложь означает, что текст достать не удалось; тогда `text` пуст.
    extracted: bool
    format_ru: str
    text: str = ""
    characters: int = 0
    truncated: bool = False
    note_ru: str = ""


class TextFragment(BaseModel):
    """Место в документе, совпавшее со словом из словаря вопроса."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    filename: str
    matched_ru: str
    quote_ru: str
    position: int


class DateCandidate(BaseModel):
    """Дата, найденная в тексте документа."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    filename: str
    value: date
    quote_ru: str
    position: int


class GapEvidenceHints(BaseModel):
    """Что нашлось в документах по одному открытому вопросу."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = DOCUMENT_TEXT_VERSION
    gap_id: str
    fragments: list[TextFragment] = Field(default_factory=list)
    dates: list[DateCandidate] = Field(default_factory=list)
    note_ru: str = (
        "Это совпадения по словам, а не установленные обстоятельства. "
        "Утверждение о факте делает оператор, прочитав документ."
    )


# --- Извлечение текста ------------------------------------------------------

_XML_TAG = re.compile(r"<[^>]+>")
_PARAGRAPH_END = re.compile(r"</w:p>")
_WHITESPACE = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n{3,}")


def _tidy(text: str) -> str:
    text = _WHITESPACE.sub(" ", text.replace("\r\n", "\n").replace("\r", "\n"))
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _BLANK_LINES.sub("\n\n", text).strip()


def _decode(content: bytes) -> str | None:
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def _from_docx(content: bytes) -> str | None:
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            document = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile):
        return None
    xml = document.decode("utf-8", errors="replace")
    # Разрыв абзаца обязан стать переводом строки до снятия разметки: иначе
    # весь договор превращается в одну строку без единой границы.
    xml = _PARAGRAPH_END.sub("\n", xml)
    return unescape(_XML_TAG.sub("", xml))


def _from_pdf(content: bytes) -> tuple[str | None, str]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, (
            "Чтение PDF требует пакета pypdf, он не установлен. "
            "Приложите документ в формате DOCX или TXT — либо установите пакет."
        )
    try:
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as error:  # noqa: BLE001 — сообщение важнее типа ошибки
        return None, f"PDF не разобран: {error}"
    text = "\n\n".join(pages)
    if not text.strip():
        return None, (
            "В PDF нет текстового слоя: это скан. Распознавания в стенде нет, "
            "поэтому текст показать нечего — приложите текстовую версию."
        )
    return text, ""


FORMAT_LABELS_RU: dict[str, str] = {
    ".txt": "простой текст",
    ".md": "простой текст",
    ".csv": "простой текст",
    ".docx": "документ Word",
    ".pdf": "документ PDF",
}


def extract_text(document: UploadedDocument, content: bytes) -> ExtractedText:
    """Достать текст из файла, ничего в нём не интерпретируя."""
    suffix = PurePosixPath(document.filename).suffix.lower()
    format_ru = FORMAT_LABELS_RU.get(suffix, f"формат {suffix or 'без расширения'}")

    note = ""
    if suffix in {".txt", ".md", ".csv", ""}:
        raw = _decode(content)
        if raw is None:
            note = "Кодировка файла не распознана: ни UTF-8, ни CP1251."
    elif suffix == ".docx":
        raw = _from_docx(content)
        if raw is None:
            note = "Файл не открылся как документ Word."
    elif suffix == ".pdf":
        raw, note = _from_pdf(content)
    else:
        raw = None
        note = (
            f"Формат «{suffix}» стенд не читает. Читаются TXT, MD, CSV, DOCX и "
            "PDF с текстовым слоем."
        )

    if raw is None:
        return ExtractedText(
            document_id=document.id,
            filename=document.filename,
            extracted=False,
            format_ru=format_ru,
            note_ru=note or "Текст извлечь не удалось.",
        )

    text = _tidy(raw)
    truncated = len(text) > MAX_TEXT_CHARACTERS
    if truncated:
        text = text[:MAX_TEXT_CHARACTERS]
    return ExtractedText(
        document_id=document.id,
        filename=document.filename,
        extracted=True,
        format_ru=format_ru,
        text=text,
        characters=len(text),
        truncated=truncated,
        note_ru=(
            f"Показаны первые {MAX_TEXT_CHARACTERS} знаков: остальное отсечено."
            if truncated
            else "Текст извлечён как есть; система его не разбирала."
        ),
    )


# --- Поиск мест под пробел --------------------------------------------------

#: Факт модели обязательства → слова, по которым его ищут в документе.
#:
#: Словарь ведётся вручную и по-русски. Это не онтология и не претензия на
#: понимание: это список слов, которые в договорах и претензиях действительно
#: стоят рядом с соответствующим обстоятельством. Ошибки такого поиска
#: предсказуемы, и потому он допустим там, где догадка модели была бы нет.
FACT_KEYWORDS_RU: dict[str, tuple[str, ...]] = {
    "duty_exists": (
        "обязуется",
        "обязан",
        "предмет договора",
        "поставить",
        "передать товар",
        "выполнить работ",
        "оказать услуг",
    ),
    "due_date_missed": (
        "срок поставки",
        "срок исполнения",
        "не позднее",
        "в течение",
        "дата поставки",
        "просрочк",
    ),
    "performance_completed": (
        "акт приём",
        "акт прием",
        "товарная накладная",
        "универсальный передаточный",
        "отгруж",
        "принят",
        "передан",
    ),
    "performance_nonconforming": (
        "недостат",
        "ненадлежащ",
        "качеств",
        "несоответств",
        "брак",
        "рекламац",
    ),
    "payment_duty_exists": (
        "оплат",
        "цена договора",
        "стоимость",
        "счёт на оплату",
        "счет на оплату",
    ),
    "payment_due": ("срок оплаты", "оплатить в течение", "аванс", "предоплат"),
    "payment_missed": ("задолженност", "не оплачен", "неоплат", "просрочка платеж"),
    "payment_defense_applies": ("зачёт", "зачет", "встречн", "удержан", "приостанов"),
    "valid_exception_applies": (
        "непреодолимой силы",
        "форс-мажор",
        "обстоятельства, за которые",
        "не отвечает",
    ),
    "loss_claimed": ("убытк", "ущерб", "упущенн"),
    "causation_established": ("вследствие", "в результате", "причинн", "повлекл"),
    "remedy_requested": ("претензи", "требован", "взыска", "неустойк", "штраф", "пени"),
    "limitation_period_expired": ("исковой давности", "срок давности", "пропущен срок"),
}

#: Слова для пробелов, закрываемых датой. Дата ищется отдельно, но место в
#: документе всё равно нужно показать.
DATE_KEYWORDS_RU: tuple[str, ...] = (
    "срок поставки",
    "срок исполнения",
    "не позднее",
    "в течение",
    "дата поставки",
    "дата подписания",
)

_MONTHS_RU: dict[str, int] = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}

_NUMERIC_DATE = re.compile(r"\b(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\b")
_WORDED_DATE = re.compile(
    r"[«\"]?(\d{1,2})[»\"]?\s+(" + "|".join(_MONTHS_RU) + r")\s+(\d{4})",
    re.IGNORECASE,
)


def _quote(text: str, position: int, length: int) -> str:
    start = max(0, position - QUOTE_RADIUS)
    end = min(len(text), position + length + QUOTE_RADIUS)
    quote = text[start:end].replace("\n", " ").strip()
    if start > 0:
        quote = "… " + quote
    if end < len(text):
        quote = quote + " …"
    return quote


def _find_fragments(
    extracted: ExtractedText,
    keywords: tuple[str, ...],
) -> list[TextFragment]:
    lowered = extracted.text.lower()
    found: list[TextFragment] = []
    used: list[int] = []
    for keyword in keywords:
        start = 0
        while len(found) < MAX_FRAGMENTS_PER_GAP:
            position = lowered.find(keyword, start)
            if position == -1:
                break
            start = position + len(keyword)
            # Два совпадения в одном абзаце — это одно место, а не два.
            if any(abs(position - seen) < QUOTE_RADIUS for seen in used):
                continue
            used.append(position)
            found.append(
                TextFragment(
                    document_id=extracted.document_id,
                    filename=extracted.filename,
                    matched_ru=keyword,
                    quote_ru=_quote(extracted.text, position, len(keyword)),
                    position=position,
                )
            )
        if len(found) >= MAX_FRAGMENTS_PER_GAP:
            break
    return found


def _find_dates(extracted: ExtractedText) -> list[DateCandidate]:
    found: list[DateCandidate] = []
    seen: set[date] = set()
    for match in _NUMERIC_DATE.finditer(extracted.text):
        day, month, year = (int(part) for part in match.groups())
        try:
            value = date(year, month, day)
        except ValueError:
            continue
        if value in seen:
            continue
        seen.add(value)
        found.append(
            DateCandidate(
                document_id=extracted.document_id,
                filename=extracted.filename,
                value=value,
                quote_ru=_quote(extracted.text, match.start(), len(match.group(0))),
                position=match.start(),
            )
        )
    for match in _WORDED_DATE.finditer(extracted.text):
        day, month_ru, year = match.groups()
        try:
            value = date(int(year), _MONTHS_RU[month_ru.lower()], int(day))
        except (ValueError, KeyError):
            continue
        if value in seen:
            continue
        seen.add(value)
        found.append(
            DateCandidate(
                document_id=extracted.document_id,
                filename=extracted.filename,
                value=value,
                quote_ru=_quote(extracted.text, match.start(), len(match.group(0))),
                position=match.start(),
            )
        )
    return sorted(found, key=lambda item: item.position)[:MAX_FRAGMENTS_PER_GAP]


def build_gap_hints(
    gaps: list[TypedGap],
    texts: list[ExtractedText],
) -> list[GapEvidenceHints]:
    """Найти в приложенных документах места, относящиеся к каждому пробелу."""
    readable = [item for item in texts if item.extracted and item.text]
    if not readable:
        return []

    hints: list[GapEvidenceHints] = []
    for gap in gaps:
        if gap.closure_kind is None:
            continue
        if gap.closure_kind is ClosureKind.SUPPLIED_DATE:
            keywords = DATE_KEYWORDS_RU
        else:
            keywords = tuple(
                word for field in gap.fact_updates for word in FACT_KEYWORDS_RU.get(field, ())
            )
        if not keywords:
            continue

        fragments: list[TextFragment] = []
        dates: list[DateCandidate] = []
        for extracted in readable:
            fragments.extend(_find_fragments(extracted, keywords))
            if gap.closure_kind is ClosureKind.SUPPLIED_DATE:
                dates.extend(_find_dates(extracted))
        if not fragments and not dates:
            continue
        hints.append(
            GapEvidenceHints(
                gap_id=gap.id,
                fragments=fragments[:MAX_FRAGMENTS_PER_GAP],
                dates=dates[:MAX_FRAGMENTS_PER_GAP],
            )
        )
    return hints
