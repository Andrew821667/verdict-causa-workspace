"""Обход кодекса: чего в модели нет, независимо от того, какие дела мы отобрали.

## Зачем он, если покрытие уже измеряется

[Покрытие практики](practice_coverage.py) сопоставляет статьи, на которые
сослались суды, с диапазонами институтов. Измерение честное, но
самоподтверждающееся дважды: дела отбирались внутри покрытых тем, а статья,
которую суды не применяют, в нём вообще не появится.

Обход кодекса переворачивает вопрос. Он идёт не от дел, а от закона: берёт
полный список статей частей первой и второй и спрашивает, какие из них не
заявлены ни одним институтом. Отбор дел на результат не влияет.

## Почему список статей выгружается, а не пишется здесь

Первый черновой обход шёл по целым номерам, названным по памяти, и видел 453
статьи в части первой. В кодексе их 613: сто шестьдесят номеров — с точкой, и
двенадцать — с третьим уровнем вида «123.20-4». Обход по памяти пропустил бы
почти четверть части первой и не заметил бы этого.

Поэтому список статей — данные, выгруженные из первоисточника
(`docs/code-structure-export-brief.md`), а не таблица в коде. Отсутствие файла
не ошибка: пока выгрузки нет, обход честно сообщает, что измерять нечем.

## Что обход не находит

Он находит то, что модель **не объявила**. Он не находит того, что модель
объявила покрытым и разбирает неверно, — как пункт 2 статьи 174.1, попавший в
диапазон института, но не смоделированный. Такое видно только на настоящем
споре.

Два измерения дополняют друг друга: обход даёт полноту, практика —
правильность.
"""

import json
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from causa.institutional.contracts.practice_base import normalize_article
from causa.institutional.contracts.practice_coverage import (
    INSTITUTE_ARTICLE_RANGES,
    article_sort_key,
    institutes_for_article,
)

CODE_COVERAGE_VERSION = "contracts-code-coverage-v0"

CODE_STRUCTURE_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "code" / "gk_articles.jsonl"
)

#: Почему статья не заявлена ни одним институтом.
#:
#: Две разные записи, и смешивать их нельзя. **Граница** — область, которую
#: пакет сознательно не моделирует, и её отсутствие не дефект. **Пробел** —
#: статья, которую следует смоделировать: её пропустили, и запись об этом
#: обязана называть, чем именно она важна, а не оправдывать пропуск.
#:
#: Ключ — номер статьи или диапазон вида «860.1–860.15».
CODE_GAP_REASONS_RU: dict[str, tuple[str, str]] = {
    "53.1–123.28": (
        "граница",
        "Юридические лица (глава 4): пакет моделирует договорное право, а не "
        "корпоративное. В модели есть правоспособность юридического лица и "
        "полномочия его органа, но не создание, реорганизация, ликвидация и "
        "устройство отдельных организационно-правовых форм.",
    ),
    "124–127": (
        "граница",
        "Участие публичных образований (глава 5): пакет не моделирует особенности "
        "выступления Российской Федерации, субъектов и муниципальных образований "
        "в гражданском обороте.",
    ),
    "152.1–152.2": (
        "граница",
        "Охрана изображения гражданина и охрана частной жизни: нематериальные "
        "блага моделируются лишь в той части, которая нужна договорному спору "
        "(статьи 150–152), а специальные способы защиты изображения и частной "
        "жизни — нет.",
    ),
    "306": (
        "пробел",
        "Последствия прекращения права собственности в силу закона: убытки "
        "возмещает государство. Статья замыкает главу о защите права "
        "собственности, которую пакет моделирует, и выпала из диапазона "
        "института (301–305) без причины.",
    ),
    "420": (
        "граница",
        "Понятие договора: статья лежит между моделью обязательств и моделью "
        "свободы договора и не содержит правила, которое можно проверить.",
    ),
    "427": (
        "пробел",
        "Примерные условия договора: условие договора может определяться "
        "примерными условиями, опубликованными в печати. Пакет моделирует "
        "толкование договора и свободу договора, но не источник условия, "
        "лежащий вне самого договора.",
    ),
    "431.1": (
        "пробел",
        "Недействительность договора. Специальное правило для "
        "предпринимательских договоров: сторона, принявшая исполнение и не "
        "исполнившая своё, не вправе требовать признания договора "
        "недействительным. Пакет моделирует статьи 166–181 и эстоппель "
        "заключённости (пункт 3 статьи 432), но не этот — хотя он той же "
        "природы и прямо примыкает к модели недействительности.",
    ),
    "444": (
        "граница",
        "Место заключения договора: правило нужно для определения применимого "
        "права и обычаев, а не для разрешения спора по существу обязательства.",
    ),
    "449.1": (
        "пробел",
        "Публичные торги при обращении взыскания. Модель порядка заключения "
        "(445–449) разбирает торги как способ заключения договора, а не "
        "исполнительную продажу имущества должника. Пробел уже встретился на "
        "реальном деле А43-11257/2024.",
    ),
    "844.1": (
        "пробел",
        "Договор банковского вклада, удостоверенный сберегательным "
        "сертификатом. Институт вклада заявляет 834–844 и обрывается на статье "
        "перед этой: номер отличается на долю, и статья выпала незамеченной.",
    ),
    "926.1–926.8": (
        "пробел",
        "Условное депонирование (эскроу), глава 47.1 целиком. Восемь статей, "
        "не заявленных никем. Глава вставлена в кодекс между хранением и "
        "страхованием, и разбор кодекса по порядку глав её перешагнул.",
    ),
}


class CodeArticle(BaseModel):
    """Одна статья кодекса из выгрузки структуры."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    number: str
    title_ru: str
    part: int
    section_ru: str
    chapter_number: str
    chapter_title_ru: str
    paragraph_ru: str = ""
    in_force: bool = True
    source_ref: str = ""

    @field_validator("number", "chapter_number", mode="before")
    @classmethod
    def normalize(cls, value: object) -> object:
        return normalize_article(value)


class ChapterGap(BaseModel):
    """Непокрытые статьи одной главы."""

    part: int
    chapter_number: str
    chapter_title_ru: str
    articles: list[str] = Field(default_factory=list)
    span: str = ""
    kind_ru: str = ""
    reason_ru: str = ""


class CodeStructure(BaseModel):
    version: str = CODE_COVERAGE_VERSION
    present: bool = False
    articles: list[CodeArticle] = Field(default_factory=list)
    total: int = 0
    in_force: int = 0
    repealed: int = 0
    chapters: int = 0
    notes_ru: list[str] = Field(default_factory=list)


class CodeCoverageReport(BaseModel):
    version: str = CODE_COVERAGE_VERSION
    present: bool = False
    articles_in_force: int = 0
    articles_claimed: int = 0
    articles_unclaimed: int = 0
    gaps: list[ChapterGap] = Field(default_factory=list)
    declared_boundaries: int = 0
    real_gaps: int = 0
    unexplained: list[str] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


def load_code_structure(path: Path | None = None) -> CodeStructure:
    """Прочитать выгрузку структуры кодекса.

    Отсутствие файла — не ошибка: пока выгрузки нет, обход сообщает, что
    измерять нечем, и указывает на задание.
    """
    target = path or CODE_STRUCTURE_PATH
    if not target.exists():
        return CodeStructure(
            present=False,
            notes_ru=[
                f"Выгрузка структуры кодекса не найдена по пути {target}. Задание: "
                "docs/code-structure-export-brief.md.",
            ],
        )

    articles: list[CodeArticle] = []
    seen: set[tuple[int, str]] = set()
    for number, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Строка {number} выгрузки не является JSON: {error}") from error
        article = CodeArticle.model_validate(payload)
        marker = (article.part, article.number)
        if marker in seen:
            raise ValueError(f"Строка {number}: повторная статья {article.number!r}.")
        seen.add(marker)
        articles.append(article)

    articles.sort(key=lambda item: (item.part, article_sort_key(item.number)))
    repealed = sum(not item.in_force for item in articles)
    chapters = len({(item.part, item.chapter_number) for item in articles})
    notes: list[str] = []
    if repealed:
        notes.append(
            f"Статей, утративших силу: {repealed}. Непокрытыми они не считаются: "
            "утратившей силу статье институт не нужен, а исключить их из выгрузки "
            "значило бы оставить в нумерации дыру, которую обход принял бы за пробел."
        )
    return CodeStructure(
        present=True,
        articles=articles,
        total=len(articles),
        in_force=len(articles) - repealed,
        repealed=repealed,
        chapters=chapters,
        notes_ru=notes,
    )


def _span(numbers: list[str]) -> str:
    """Диапазон статей строкой: «860.1–860.15» или «306»."""
    if not numbers:
        return ""
    return numbers[0] if len(numbers) == 1 else f"{numbers[0]}–{numbers[-1]}"


def gap_reason_ru(article: str) -> tuple[str, str]:
    """Чем объясняется непокрытие статьи: границей модели или пробелом.

    Ключ таблицы — либо номер статьи, либо диапазон вида «860.1–860.15».
    Искать по участку, который вывела группировка, нельзя: в одной главе могут
    лежать статьи с разными причинами, и общий ключ на них не найдётся. Так
    первый прогон и оставил без объяснения главы 27 и 28, где пробелы разной
    природы стоят рядом.
    """
    key = normalize_article(article)
    known = CODE_GAP_REASONS_RU.get(key)
    if known:
        return known
    target = article_sort_key(key)
    for span, answer in CODE_GAP_REASONS_RU.items():
        low, _, high = span.partition("\u2013")
        if high and article_sort_key(low) <= target <= article_sort_key(high):
            return answer
    return ("", "Причина непокрытия не записана — это дефект карты, а не ответ.")


def measure_code_coverage(structure: CodeStructure) -> CodeCoverageReport:
    """Пройти кодекс статья за статьёй и назвать всё, что никем не заявлено."""
    if not structure.present:
        return CodeCoverageReport(present=False, notes_ru=list(structure.notes_ru))

    live = [item for item in structure.articles if item.in_force]
    unclaimed = [item for item in live if not institutes_for_article(item.number)]

    # Группируется по главе И по причине: в одной главе могут стоять рядом
    # объявленная граница и настоящий пробел, и сливать их в один участок
    # значило бы объяснять один другим.
    grouped: dict[tuple[int, str, str, str, str], list[str]] = {}
    for item in unclaimed:
        kind, reason = gap_reason_ru(item.number)
        marker = (item.part, item.chapter_number, item.chapter_title_ru, kind, reason)
        grouped.setdefault(marker, []).append(item.number)

    gaps: list[ChapterGap] = [
        ChapterGap(
            part=part,
            chapter_number=chapter,
            chapter_title_ru=title,
            articles=numbers,
            span=_span(numbers),
            kind_ru=kind,
            reason_ru=reason,
        )
        for (part, chapter, title, kind, reason), numbers in grouped.items()
    ]
    gaps.sort(key=lambda entry: (entry.part, article_sort_key(entry.articles[0])))

    kinds = Counter(entry.kind_ru for entry in gaps)
    unexplained = [entry.span for entry in gaps if not entry.kind_ru]

    notes = [
        f"Действующих статей в частях первой и второй: {len(live)}. Заявлено "
        f"институтами: {len(live) - len(unclaimed)}, не заявлено: {len(unclaimed)}.",
        "Измерение не зависит от того, какие дела мы отобрали: оно идёт от закона, "
        "а не от практики. Поэтому оно находит статьи, на которые суды не ссылались "
        "ни разу, — и не находит того, что модель объявила покрытым и разбирает "
        "неверно.",
        f"Участков без института: {len(gaps)}. Из них объявленных границ модели — "
        f"{kinds.get('граница', 0)}, настоящих пробелов — {kinds.get('пробел', 0)}.",
        "Граница и пробел — разные записи, и смешивать их нельзя. Граница говорит "
        "«эту часть кодекса пакет не моделирует и не собирается». Пробел говорит "
        "«эту статью следует смоделировать, её пропустили».",
    ]
    if unexplained:
        notes.append(
            "Участки без объяснения: "
            + ", ".join(unexplained)
            + ". Каждый обязан быть либо закрыт институтом, либо назван в "
            "CODE_GAP_REASONS_RU."
        )
    return CodeCoverageReport(
        present=True,
        articles_in_force=len(live),
        articles_claimed=len(live) - len(unclaimed),
        articles_unclaimed=len(unclaimed),
        gaps=gaps,
        declared_boundaries=kinds.get("граница", 0),
        real_gaps=kinds.get("пробел", 0),
        unexplained=unexplained,
        notes_ru=notes,
    )


def articles_beyond_declared_ranges() -> list[str]:
    """Диапазоны институтов, выходящие за пределы частей первой и второй.

    Проверка карты на выдумку: институт не может заявить статью, которой в
    кодексе нет. До выгрузки такое утверждение проверить было нечем.
    """
    structure = load_code_structure()
    if not structure.present:
        return []
    known = {item.number for item in structure.articles}
    missing: list[str] = []
    for ranges in INSTITUTE_ARTICLE_RANGES.values():
        for low, high in ranges:
            for edge in (low, high):
                if edge not in known:
                    missing.append(edge)
    return sorted(set(missing), key=article_sort_key)


def render_code_coverage_ru(report: CodeCoverageReport) -> str:
    """Человекочитаемый отчёт обхода."""
    if not report.present:
        return "\n".join(["# Обход кодекса", "", *(f"- {note}" for note in report.notes_ru)])
    lines = ["# Обход кодекса: чего в модели нет", ""]
    lines += [f"- {note}" for note in report.notes_ru]
    lines.append("")
    for entry in report.gaps:
        mark = entry.kind_ru or "БЕЗ ОБЪЯСНЕНИЯ"
        lines.append(
            f"## Часть {entry.part}, глава {entry.chapter_number}. "
            f"{entry.chapter_title_ru} — {mark}"
        )
        lines.append("")
        lines.append(f"Статьи {entry.span} ({len(entry.articles)}).")
        lines.append("")
        lines.append(entry.reason_ru)
        lines.append("")
    return "\n".join(lines)


def code_coverage_payload(report: CodeCoverageReport) -> dict:
    """Отчёт в виде данных для артефакта."""
    return report.model_dump(mode="json")
