"""Фабула дела: что произошло, изложенное по-русски из проверенных фактов.

## Зачем отдельный модуль

Окно дела открывалось вердиктом: «Вопрос о нарушении обязательства возникает».
Ответ есть, а дела нет. Юрист, впервые открывший карточку, не понимал, о чём
спор: какое обязательство, между кем, что и когда произошло. Вердикт без
фабулы — это ответ без вопроса.

## Откуда берутся предложения

Из тех же тринадцати фактов обязательства и трёх дат, на которых работает
решатель, и **больше ниоткуда**. Здесь нет ни пересказа документов (система их
не разбирает), ни имён сторон (их нет во входах модели), ни сумм. Всё, чего в
фактах нет, в фабуле не появляется — иначе фабула стала бы сочинением, которое
выглядит как материалы дела.

## Почему «не установлено», а не «нет»

Модель замкнута: факт, который не утверждён, считается ложным. Но «оплата не
просрочена» и «о просрочке оплаты ничего не утверждалось» — разные вещи, и для
юриста разница решающая. Поэтому ложное значение излагается как «не
установлено», а не как отрицание по существу.

## Краткая и подробная

Краткая фабула — три предложения: из какого отношения спор, что случилось,
какой вопрос решается. Подробная — те же факты по разделам, с указанием, на
каких источниках каждый держится. Обе собраны из одного набора: краткая не
может утверждать то, чего нет в подробной.
"""

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult
from causa.ui.qualification import CaseQualification

CASE_STORY_VERSION = "ui-case-story-v0"


class StoryFact(BaseModel):
    """Одно обстоятельство дела и то, чем оно подтверждается."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    #: Имя факта в модели обязательства — чтобы утверждение можно было проверить.
    fact: str
    text_ru: str
    #: Ложь означает «не установлено», а не «установлено обратное».
    established: bool
    source_refs: list[str] = Field(default_factory=list)


class StorySection(BaseModel):
    """Раздел подробной фабулы."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title_ru: str
    facts: list[StoryFact] = Field(default_factory=list)


class CaseStory(BaseModel):
    """Фабула дела: коротко и подробно."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = CASE_STORY_VERSION
    #: Три предложения, которые читаются первыми.
    summary_ru: str
    #: Какой вопрос решается по этой фабуле.
    question_ru: str
    sections: list[StorySection] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)

    @property
    def established_count(self) -> int:
        return sum(1 for section in self.sections for fact in section.facts if fact.established)

    @property
    def fact_count(self) -> int:
        return sum(len(section.facts) for section in self.sections)


#: Факт → как он читается, когда установлен и когда не установлен.
#:
#: Список ведётся вручную и полностью: формулировка обстоятельства дела — это
#: юридическое утверждение, а не автоматический пересказ имени поля. Новый факт
#: обязан сломать этот словарь, а не проскользнуть безымянным.
FACT_SENTENCES_RU: dict[str, tuple[str, str]] = {
    "duty_exists": (
        "Между сторонами существует обязательство, из которого заявлено требование.",
        "Существование обязательства не установлено.",
    ),
    "due_date_missed": (
        "Срок исполнения обязательства пропущен.",
        "Пропуск срока исполнения не установлен.",
    ),
    "performance_completed": (
        "Обязательство исполнено.",
        "Исполнение обязательства не установлено.",
    ),
    "performance_nonconforming": (
        "Исполнение отступает от условий обязательства.",
        "Ненадлежащее качество исполнения не установлено.",
    ),
    "valid_exception_applies": (
        "Установлено обстоятельство, освобождающее должника от ответственности.",
        "Основание освобождения от ответственности не установлено.",
    ),
    "payment_duty_exists": (
        "На стороне контрагента существует денежное обязательство.",
        "Денежное обязательство контрагента не установлено.",
    ),
    "payment_due": (
        "Срок платежа наступил.",
        "Наступление срока платежа не установлено.",
    ),
    "payment_missed": (
        "Платёж в срок не произведён.",
        "Просрочка платежа не установлена.",
    ),
    "payment_defense_applies": (
        "У плательщика есть возражение против требования об оплате.",
        "Возражение против требования об оплате не установлено.",
    ),
    "loss_claimed": (
        "Заявлены убытки.",
        "Убытки не заявлены.",
    ),
    "causation_established": (
        "Причинная связь между нарушением и убытками доказана.",
        "Причинная связь между нарушением и убытками не доказана.",
    ),
    "remedy_requested": (
        "Средство защиты заявлено.",
        "Средство защиты не заявлено.",
    ),
    "limitation_period_expired": (
        "Срок исковой давности по требованию истёк.",
        "Истечение срока исковой давности не установлено.",
    ),
}

#: Разделы подробной фабулы и порядок фактов в них.
#:
#: Порядок юридический, а не алфавитный: сначала само обязательство, затем срок
#: и исполнение, затем расчёты, затем требование, и только потом возражения.
STORY_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Обязательство", ("duty_exists",)),
    (
        "Срок и исполнение",
        ("due_date_missed", "performance_completed", "performance_nonconforming"),
    ),
    ("Расчёты", ("payment_duty_exists", "payment_due", "payment_missed")),
    ("Требование", ("loss_claimed", "causation_established", "remedy_requested")),
    (
        "Возражения",
        ("valid_exception_applies", "payment_defense_applies", "limitation_period_expired"),
    ),
)


def _dates_sentence_ru(result: ReviewedContractAnalysisResult) -> str:
    """Предложение о сроках. Пустая строка, если дат в деле нет."""
    temporal = result.temporal_facts
    agreed = temporal.agreed_due_date
    actual = temporal.actual_performance_date
    if agreed is None and actual is None:
        return ""
    if agreed is None:
        return f"Исполнение состоялось {actual:%d.%m.%Y}; согласованный срок в деле не указан."
    if actual is None:
        return (
            f"Согласованный срок исполнения — {agreed:%d.%m.%Y}; "
            f"исполнение на дату оценки {temporal.evaluation_date:%d.%m.%Y} не зафиксировано."
        )
    if actual <= agreed:
        return (
            f"Согласованный срок исполнения — {agreed:%d.%m.%Y}, "
            f"исполнение состоялось {actual:%d.%m.%Y}, в пределах срока."
        )
    days = (actual - agreed).days
    return (
        f"Согласованный срок исполнения — {agreed:%d.%m.%Y}, "
        f"исполнение состоялось {actual:%d.%m.%Y}: просрочка составила "
        f"{days} {_days_ru(days)}."
    )


def _days_ru(days: int) -> str:
    """Согласование слова «день» с числом."""
    tail_two, tail_one = days % 100, days % 10
    if 11 <= tail_two <= 14:
        return "дней"
    if tail_one == 1:
        return "день"
    if 2 <= tail_one <= 4:
        return "дня"
    return "дней"


def _relation_sentence_ru(qualification: CaseQualification) -> str:
    primary = qualification.primary
    if primary is None:
        return (
            "Спор из обязательства, договорный тип которого система не "
            "определила: ни один предикат квалификации не сработал."
        )
    sentence = f"Спор из отношений, которые система квалифицировала как «{primary.title_ru}»"
    if primary.articles_ru:
        sentence += f" ({primary.articles_ru})"
    if qualification.competing:
        sentence += "; в деле сработала не одна квалификация, и это видно в разделе «Обзор»"
    return sentence + "."


def _question_ru(result: ReviewedContractAnalysisResult) -> str:
    constraint = result.constraint_evaluation
    layer = result.general_effects_evaluation
    if layer.institute_conclusions_displaced or layer.breach_findings_without_effect:
        return (
            "Решается судьба самой сделки: действует ли договор как основание "
            "требований. До этого вопрос о просрочке не имеет значения."
        )
    if layer.claims_barred_by_limitation:
        return (
            "Решается, перекрыто ли требование заявлением о пропуске срока "
            "исковой давности (статья 199 ГК РФ)."
        )
    if constraint.breach_issue:
        return (
            "Решается, возникает ли вопрос о нарушении обязательства и какое "
            "средство защиты доступно кредитору."
        )
    return "Решается, подтверждены ли предпосылки нарушения обязательства."


def build_case_story(
    result: ReviewedContractAnalysisResult,
    qualification: CaseQualification,
) -> CaseStory:
    """Собрать фабулу дела из проверенных фактов и дат."""
    facts = result.evidence_mapping.facts
    provenance = {
        item.fact_name: list(item.source_refs) for item in result.evidence_mapping.provenance
    }

    known = set(FACT_SENTENCES_RU)
    declared = set(type(facts).model_fields)
    if declared - known:
        raise ValueError(
            "У фактов обязательства нет формулировки для фабулы: "
            + ", ".join(sorted(declared - known))
            + ". Добавьте её в FACT_SENTENCES_RU — молча пропускать факт нельзя."
        )

    sections: list[StorySection] = []
    for title_ru, names in STORY_SECTIONS:
        entries: list[StoryFact] = []
        for name in names:
            value = bool(getattr(facts, name))
            established, missing = FACT_SENTENCES_RU[name]
            entries.append(
                StoryFact(
                    fact=name,
                    text_ru=established if value else missing,
                    established=value,
                    source_refs=provenance.get(name, []),
                )
            )
        sections.append(StorySection(title_ru=title_ru, facts=entries))

    placed = {name for _, names in STORY_SECTIONS for name in names}
    if placed != declared:
        raise ValueError(
            "Факты обязательства не разложены по разделам фабулы: "
            + ", ".join(sorted(declared ^ placed))
        )

    dates = _dates_sentence_ru(result)
    summary_parts = [_relation_sentence_ru(qualification)]
    if dates:
        summary_parts.append(dates)
    summary_parts.append(_question_ru(result))

    notes: list[str] = [
        "Фабула собрана из проверенных фактов дела и дат, а не из текста "
        "документов: содержимое приложенных файлов система не разбирает.",
    ]
    if not any(fact.established for section in sections for fact in section.facts):
        notes.append(
            "Ни один факт обязательства не подтверждён: фабулы по существу нет, "
            "и вывод по такому делу держится на пустоте."
        )

    return CaseStory(
        summary_ru=" ".join(summary_parts),
        question_ru=_question_ru(result),
        sections=sections,
        notes_ru=notes,
    )
