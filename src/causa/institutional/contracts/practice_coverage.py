"""Покрытие реальных дел институтами пакета: измерение по статьям ГК РФ.

Первый вопрос к полученной выгрузке судебной практики — не «сходятся ли выводы»,
а «умеет ли модель вообще разбирать такие дела». Ответ даёт сопоставление статей,
на которые сослался суд, с диапазонами статей, которые заявляют институты пакета.

Измерение намеренно грубое и намеренно честное. Оно отвечает на вопрос
«объявлен ли институт для этой статьи», а не «правильно ли он её моделирует»:
попадание статьи в диапазон не означает, что предикаты института покрывают
именно то соображение, ради которого суд статью привёл. Поэтому результат —
верхняя граница покрытия, а не оценка качества.

Диапазоны продублированы здесь явно, а не выведены из строк версий моделей.
Строки версий кодируют номера лоссово: «1-16-1» — это статьи 1–16.1, «3083» —
308.3, «429-1-429-4» — 429.1–429.4. Разбор такой записи молча ошибался бы на
статьях с точкой — ровно там, где выгрузка и разошлась с приёмной стороной.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.practice_base import (
    PracticeBaseInventory,
    PracticeCase,
    normalize_article,
)

PRACTICE_COVERAGE_VERSION = "contracts-practice-coverage-v0"

#: Диапазоны статей ГК РФ, заявленные институтами пакета.
#:
#: Границы включительные. Диапазоны пересекаются, и это не ошибка: статью 393
#: заявляют и модель средств защиты, и модель ответственности — они разбирают
#: разные её стороны.
INSTITUTE_ARTICLE_RANGES: dict[str, tuple[tuple[str, str], ...]] = {
    "civil_principles": (("1", "16.1"),),
    "persons": (("17", "53"),),
    "objects": (("128", "152"),),
    "transactions": (("153", "157.1"),),
    "form": (("158", "165"), ("434", "434")),
    "invalidity": (("166", "181"),),
    "representation": (("182", "189"),),
    "terms": (("190", "194"),),
    "limitation": (("195", "208"),),
    "property_rights": (("209", "305"),),
    "general_obligations": (("307", "308.3"),),
    "performance_remedies": (("309", "328"), ("393", "393"), ("406.1", "406.1")),
    "security": (("329", "381.2"),),
    "liability": (("333", "401"),),
    # Строка версии модели заявляет 382–419, но предикаты разбирают главу 24
    # (перемена лиц) и главу 26 (прекращение обязательства). Главы 25
    # (ответственность, 393–406.1) среди них нет. Здесь записано то, что
    # моделируется, иначе измерение объявляло бы покрытыми статьи 402–406,
    # которых не разбирает никто.
    "obligation_dynamics": (("382", "392.3"), ("407", "419")),
    "freedom": (("421", "424"),),
    "temporal_effect": (("425", "425"), ("433", "433")),
    "public_contract": (("426", "426"),),
    "adhesion": (("428", "428"),),
    "preliminary": (("429", "429"),),
    "framework": (("429.1", "429.1"), ("429.4", "429.4")),
    "option": (("429.2", "429.3"),),
    "third_party": (("430", "430"),),
    "interpretation": (("431", "431"),),
    "representations": (("431.2", "431.2"),),
    "formation": (("432", "443"),),
    "precontractual": (("434.1", "434.1"),),
    "procedure": (("445", "449"),),
    "termination": (("450", "453"),),
    "sale": (("454", "491"),),
    "retail_sale": (("492", "505"),),
    "supply": (("506", "524"),),
    "state_supply": (("525", "534"),),
    "contractation": (("535", "538"),),
    "energy_supply": (("539", "548"),),
    "real_estate_sale": (("549", "558"),),
    "enterprise_sale": (("559", "566"),),
    "barter": (("567", "571"),),
    "gift": (("572", "582"),),
    "annuity": (("583", "605"),),
    "lease": (("606", "625"),),
    "rental": (("626", "631"),),
    "vehicle_lease": (("632", "649"),),
    "building_lease": (("650", "655"),),
    "enterprise_lease": (("656", "664"),),
    "leasing": (("665", "670"),),
    "residential_lease": (("671", "688"),),
    "gratuitous_use": (("689", "701"),),
    "work_contract": (("702", "729"),),
    "consumer_work": (("730", "739"),),
    "construction_contract": (("740", "757"),),
    "design_work": (("758", "762"),),
    "state_work": (("763", "768"),),
    "research_work": (("769", "778"),),
    "paid_services": (("779", "783.1"),),
    "carriage": (("784", "800"),),
    "forwarding": (("801", "806"),),
    "loan": (("807", "818"),),
    "credit": (("819", "821.1"),),
    "commercial_credit": (("822", "823"),),
    "factoring": (("824", "833"),),
    "bank_deposit": (("834", "844"),),
    "bank_account": (("845", "860"),),
    "settlements": (("861", "885"),),
    "storage": (("886", "906"),),
    "warehouse_storage": (("907", "918"),),
    "special_storage": (("919", "926"),),
    "insurance": (("927", "943"),),
    "insurance_settlement": (("944", "970"),),
    "mandate": (("971", "979"),),
    "negotiorum_gestio": (("980", "989"),),
    "commission": (("990", "1004"),),
    "agency": (("1005", "1011"),),
    "trust_management": (("1012", "1026"),),
    "franchise": (("1027", "1040"),),
    "partnership": (("1041", "1054"),),
    "public_promise": (("1055", "1061"),),
    "games": (("1062", "1063"),),
    "tort_general": (("1064", "1083"),),
    "tort_life_health": (("1084", "1094"),),
    "product_liability": (("1095", "1098"),),
    "moral_harm": (("1099", "1101"),),
    "unjust_enrichment": (("1102", "1109"),),
}

#: Пробелы, известные заранее, и чем они объясняются.
#:
#: Заполняется по результатам измерения: статья попадает сюда, когда установлено,
#: что её не покрывает ни один институт, и названа причина.
KNOWN_GAPS_RU: dict[str, str] = {
    "181.3": "решения собраний (глава 9.1, статьи 181.1–181.5) в пакете не моделируются",
    "181.4": "решения собраний (глава 9.1, статьи 181.1–181.5) в пакете не моделируются",
    "181.5": "решения собраний (глава 9.1, статьи 181.1–181.5) в пакете не моделируются",
    "420": "понятие договора: статья лежит между моделью обязательств и моделью свободы договора",
    "403": "ответственность должника за действия третьих лиц не выделена в предикаты",
    "404": "вина кредитора как основание снижения ответственности не выделена в предикаты",
}


def article_sort_key(article: str) -> tuple[int, int]:
    """Ключ порядка статей: 157 < 157.1 < 158, 308 < 308.3 < 309."""
    major, _, minor = normalize_article(article).partition(".")
    return int(major), int(minor) if minor else 0


def institutes_for_article(article: str) -> list[str]:
    """Институты, заявившие статью в своём диапазоне."""
    key = article_sort_key(article)
    return sorted(
        name
        for name, ranges in INSTITUTE_ARTICLE_RANGES.items()
        if any(article_sort_key(low) <= key <= article_sort_key(high) for low, high in ranges)
    )


class CaseCoverage(BaseModel):
    """Покрытие одного дела институтами пакета."""

    case_id: str
    case_number: str
    articles: list[str] = Field(default_factory=list)
    institutes: list[str] = Field(default_factory=list)
    uncovered_articles: list[str] = Field(default_factory=list)
    fully_covered: bool
    outcome_is_final: bool


class PracticeCoverageReport(BaseModel):
    """Что из полученной практики модель заявляет, а что нет."""

    version: str = PRACTICE_COVERAGE_VERSION
    total_cases: int = 0
    fully_covered_cases: int = 0
    checkable_cases: int = 0
    distinct_articles: int = 0
    uncovered_articles: list[str] = Field(default_factory=list)
    unexplained_gaps: list[str] = Field(default_factory=list)
    institute_hits: dict[str, int] = Field(default_factory=dict)
    cases: list[CaseCoverage] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


def cover_case(case: PracticeCase) -> CaseCoverage:
    """Сопоставить статьи одного дела с институтами пакета."""
    institutes: set[str] = set()
    uncovered: list[str] = []
    for article in case.articles_gk:
        found = institutes_for_article(article)
        if found:
            institutes.update(found)
        else:
            uncovered.append(article)
    return CaseCoverage(
        case_id=case.id,
        case_number=case.case_number,
        articles=sorted(case.articles_gk, key=article_sort_key),
        institutes=sorted(institutes),
        uncovered_articles=sorted(uncovered, key=article_sort_key),
        fully_covered=not uncovered,
        outcome_is_final=case.outcome_is_final,
    )


def measure_practice_coverage(inventory: PracticeBaseInventory) -> PracticeCoverageReport:
    """Измерить, какую долю полученной практики пакет заявляет своими институтами."""
    covered = [cover_case(case) for case in inventory.cases]
    hits: dict[str, int] = {}
    for entry in covered:
        for institute in entry.institutes:
            hits[institute] = hits.get(institute, 0) + 1
    uncovered = sorted(
        {article for entry in covered for article in entry.uncovered_articles},
        key=article_sort_key,
    )
    distinct = {article for entry in covered for article in entry.articles}
    checkable = sum(entry.fully_covered and entry.outcome_is_final for entry in covered)
    unexplained = [article for article in uncovered if article not in KNOWN_GAPS_RU]

    notes: list[str] = []
    if uncovered:
        notes.append(
            "Статьи без института: "
            + ", ".join(
                f"{article} — {KNOWN_GAPS_RU.get(article, 'причина не установлена')}"
                for article in uncovered
            )
            + "."
        )
    if unexplained:
        notes.append(
            "Пробелы без объяснения: "
            + ", ".join(unexplained)
            + ". Их нужно либо закрыть институтом, либо назвать причину в KNOWN_GAPS_RU."
        )
    notes.append(
        f"Дел, пригодных для полной сверки: {checkable} из {len(covered)}. Полная сверка "
        "требует и покрытия всех статей института, и окончательного исхода спора."
    )
    notes.append(
        "Попадание статьи в диапазон института не означает, что предикаты разбирают "
        "именно то соображение, ради которого суд статью привёл. Это верхняя граница "
        "покрытия."
    )
    return PracticeCoverageReport(
        total_cases=len(covered),
        fully_covered_cases=sum(entry.fully_covered for entry in covered),
        checkable_cases=checkable,
        distinct_articles=len(distinct),
        uncovered_articles=uncovered,
        unexplained_gaps=unexplained,
        institute_hits=dict(sorted(hits.items(), key=lambda item: (-item[1], item[0]))),
        cases=covered,
        notes_ru=notes,
    )
