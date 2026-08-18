"""Проект процессуального документа: текст, который действительно идёт в дело.

## Почему это отдельный жанр, а не ещё один регистр перевода

Слой перевода даёт три уровня, и верхний из них назывался «для суда, с
координатами». Название вводило в заблуждение. Достаточно посмотреть, из чего
этот уровень состоит: координаты воспроизведения, `constraint set`, provenance,
governance-журнал, восемьдесят строк формальной проверки. Судья такое не
читает. Правила проверки самого конвейера это подтверждают: для того уровня
снижен порог кириллицы и снята проверка на утечку машинной детали — то есть
машинная деталь там разрешена намеренно. Это протокол наладки, и он остался
там, где ему место (`causa.ui.reasoning`, поле `trace`).

Документ в дело устроен иначе. У него другой адресат, другая структура и другая
дисциплина: обстоятельства, правовое обоснование, требование, доказательства.
Ни одного имени предиката, ни одного отпечатка, ни одного идентификатора
источника — только то, что можно прочитать вслух в заседании.

## Жанр следует выводу, а не наоборот

Из вердикта следует, какой документ вообще имеет смысл готовить:

* нарушение установлено — проект искового заявления;
* нарушение не установлено — проект возражений на требование;
* требование перекрыто давностью — заявление о применении исковой давности;
* договор не действует как основание — возражения об отсутствии основания.

Готовить исковое заявление по делу, где требование заблокировано давностью, —
не осторожность, а вредительство, поэтому выбор жанра здесь не настройка.

## Почему проект помечается непригодным

Пока открыт хотя бы один пробел, меняющий вывод, документ не готов к подаче, и
это написано в нём самом, а не в примечании интерфейса. Бумага, вынутая из
системы и подписанная не глядя, — ровно тот способ, которым такие системы
причиняют вред.
"""

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult
from causa.ui.case_story import CaseStory
from causa.ui.documents import UploadedDocument
from causa.ui.gaps import GapQueue
from causa.ui.labels import source_label
from causa.ui.qualification import CaseQualification
from causa.ui.reasoning import ConclusionStep
from causa.ui.verdict import CaseVerdict, VerdictState

COURT_FILING_VERSION = "ui-court-filing-v0"

#: Доля кириллицы, ниже которой текст перестаёт быть документом на русском языке.
#:
#: Порог высокий намеренно. У машинной трассировки он 0.20 — там латиница по
#: делу. Здесь латинице взяться неоткуда, и её появление означает, что в текст
#: протёк идентификатор.
MINIMUM_CYRILLIC_RATIO = 0.85

#: Следы машины, которых в документе быть не может ни при каких обстоятельствах.
MACHINE_MARKERS: tuple[str, ...] = ("=True", "=False", "=true", "=false", "sha256:", "synthetic-")

#: Идентификатор вида `some_predicate_name` или `some-source-id`.
_IDENTIFIER = re.compile(r"\b[a-z][a-z0-9]*(?:[_-][a-z0-9]+){2,}\b")


class FilingKind(str, Enum):
    STATEMENT_OF_CLAIM = "statement_of_claim"
    DEFENCE = "defence"
    LIMITATION_PLEA = "limitation_plea"
    NO_BASIS_OBJECTION = "no_basis_objection"


FILING_TITLES_RU: dict[FilingKind, str] = {
    FilingKind.STATEMENT_OF_CLAIM: "Исковое заявление",
    FilingKind.DEFENCE: "Возражения на требование",
    FilingKind.LIMITATION_PLEA: "Заявление о применении исковой давности",
    FilingKind.NO_BASIS_OBJECTION: "Возражения об отсутствии основания требования",
}

#: Вывод по делу → документ, который по нему имеет смысл готовить.
FILING_BY_VERDICT: dict[VerdictState, FilingKind] = {
    VerdictState.BREACH_ESTABLISHED: FilingKind.STATEMENT_OF_CLAIM,
    VerdictState.NO_BREACH: FilingKind.DEFENCE,
    VerdictState.CLAIM_BARRED: FilingKind.LIMITATION_PLEA,
    VerdictState.FINDINGS_WITHOUT_EFFECT: FilingKind.NO_BASIS_OBJECTION,
}

#: Обязательные разделы. Документ без любого из них — не документ.
REQUIRED_SECTIONS_RU: tuple[str, ...] = (
    "Обстоятельства дела",
    "Правовое обоснование",
    "Требование",
    "Доказательства",
    "Оговорки",
)


class FilingSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title_ru: str
    paragraphs_ru: list[str] = Field(default_factory=list)


class FilingCheck(BaseModel):
    """Проверка жанра: то, чем документ отличается от машинного вывода."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    title_ru: str
    passed: bool
    detail_ru: str = ""


class CourtFiling(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = COURT_FILING_VERSION
    kind: FilingKind
    title_ru: str
    sections: list[FilingSection] = Field(default_factory=list)
    checks: list[FilingCheck] = Field(default_factory=list)
    #: Ложь означает, что документ нельзя подавать в этом виде.
    ready_to_file: bool = False
    #: Почему нельзя — одной строкой, в самом документе, а не сбоку.
    blocker_ru: str = ""
    text: str = ""


#: Виды источников, которые в документе можно назвать нормой.
#:
#: Материалы дела и условия договора нормой не являются, и складывать их в
#: правовое обоснование нельзя: это разные разделы документа.
_NORM_KINDS: frozenset[str] = frozenset({"закон", "разъяснение высшей инстанции"})


def _legal_grounds_ru(
    line: list[ConclusionStep],
    qualification: CaseQualification,
) -> list[str]:
    """Нормы, на которых держится вывод, — сгруппированные по вопросам разбора.

    Источники берутся из звеньев линии вывода, а не из полного реестра дела:
    в реестре больше двухсот источников, и перечислить их все — значит не
    сослаться ни на что.
    """
    grounds: list[str] = []
    primary = qualification.primary
    if primary is not None and primary.articles_ru:
        grounds.append(
            f"Отношения сторон описываются институтом «{primary.title_ru}» ({primary.articles_ru})."
        )
        if primary.specialises is not None:
            grounds.append(
                "Специальные правила этого института применяются вместе с общими "
                "правилами того типа, видом которого он является."
            )

    for step in line:
        norms: list[str] = []
        for ref in step.source_refs:
            label = source_label(ref)
            if label.recognised and label.kind_ru in _NORM_KINDS and label.label_ru not in norms:
                norms.append(label.label_ru)
        if norms:
            grounds.append(f"{step.question_ru} — {'; '.join(norms)}.")

    if len(grounds) <= 1:
        grounds.append(
            "Норма, на которой держится требование, в материалах дела не "
            "опознана: правовое обоснование заполняет юрист."
        )
    return grounds


def _claim_ru(kind: FilingKind, result: ReviewedContractAnalysisResult) -> list[str]:
    constraint = result.constraint_evaluation
    if kind is FilingKind.STATEMENT_OF_CLAIM:
        parts: list[str] = []
        if constraint.late_performance_issue:
            parts.append("признать нарушением обязательства просрочку исполнения")
        if constraint.defect_issue:
            parts.append("признать нарушением обязательства ненадлежащее исполнение")
        if constraint.payment_default_issue:
            parts.append("признать нарушением обязательства просрочку платежа")
        if not parts:
            parts.append("признать нарушением обязательства установленные обстоятельства")
        claim = ["Прошу: " + "; ".join(parts) + "."]
        if constraint.damages_remedy_available:
            claim.append(
                "Предпосылки требования о возмещении убытков подтверждены; "
                "размер убытков определяет истец."
            )
        else:
            claim.append(
                "Требование о возмещении убытков в этом виде не подтверждено: "
                "подтверждены не все его предпосылки. Заявлять его без этого нельзя."
            )
        return claim
    if kind is FilingKind.DEFENCE:
        return [
            "Прошу: в удовлетворении требования отказать.",
            "По проверенным обстоятельствам предпосылки нарушения обязательства не подтверждены.",
        ]
    if kind is FilingKind.LIMITATION_PLEA:
        return [
            "Прошу: применить исковую давность и в иске отказать (статьи 196, 199 и 200 ГК РФ).",
            "Заявление о пропуске срока перекрывает требование независимо от "
            "того, было нарушение или нет.",
        ]
    return [
        "Прошу: в удовлетворении требования отказать.",
        "Договор не действует как основание требования, поэтому спор о "
        "просрочке исполнения не имеет предмета.",
    ]


def _evidence_ru(documents: list[UploadedDocument]) -> list[str]:
    if not documents:
        return [
            "К делу не приложено ни одного документа. Обстоятельства подтверждены "
            "утверждениями, внесёнными в систему, и без документов в дело не идут."
        ]
    lines = ["Приложения:"]
    lines.extend(
        f"{index}. {document.filename} — {document.size_bytes} байт."
        for index, document in enumerate(documents, start=1)
    )
    lines.append(
        "Содержимое приложенных файлов система не разбирала: они приложены как "
        "основание утверждений оператора."
    )
    return lines


def _caveats_ru(verdict: CaseVerdict, gaps: GapQueue) -> list[str]:
    lines: list[str] = []
    if gaps.blocking_count:
        lines.append(
            f"Документ не готов к подаче: открыто вопросов, меняющих вывод — "
            f"{gaps.blocking_count}. Пока они открыты, изложенное здесь не "
            f"является установленным."
        )
    lines.extend(verdict.qualifiers_ru)
    lines.append(
        "Проект подготовлен автоматически из проверенных фактов дела. Он не "
        "является судебным выводом или юридической консультацией и подлежит "
        "проверке юристом до подачи."
    )
    return lines


def _assemble(title_ru: str, sections: list[FilingSection]) -> str:
    blocks = [title_ru.upper()]
    for section in sections:
        blocks.append(section.title_ru + "\n" + "\n".join(section.paragraphs_ru))
    return "\n\n".join(blocks)


def _cyrillic_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    cyrillic = sum(1 for char in letters if "Ѐ" <= char <= "ӿ")
    return cyrillic / len(letters)


def _run_checks(text: str, sections: list[FilingSection], gaps: GapQueue) -> list[FilingCheck]:
    titles = {section.title_ru for section in sections}
    missing = [title for title in REQUIRED_SECTIONS_RU if title not in titles]

    leaked = [marker for marker in MACHINE_MARKERS if marker in text]
    identifiers = sorted(set(_IDENTIFIER.findall(text)))
    ratio = _cyrillic_ratio(text)

    return [
        FilingCheck(
            code="required_sections",
            title_ru="Все обязательные разделы на месте",
            passed=not missing,
            detail_ru=("Не хватает разделов: " + ", ".join(missing)) if missing else "",
        ),
        FilingCheck(
            code="no_machine_detail",
            title_ru="Машинной детали в тексте нет",
            passed=not leaked,
            detail_ru=("В текст протекло: " + ", ".join(leaked)) if leaked else "",
        ),
        FilingCheck(
            code="no_identifiers",
            title_ru="Идентификаторов системы в тексте нет",
            passed=not identifiers,
            detail_ru=(
                "В тексте найдены идентификаторы: " + ", ".join(identifiers) if identifiers else ""
            ),
        ),
        FilingCheck(
            code="cyrillic_ratio",
            title_ru="Документ написан по-русски",
            passed=ratio >= MINIMUM_CYRILLIC_RATIO,
            detail_ru=(
                f"Доля кириллицы {ratio:.2f} ниже порога {MINIMUM_CYRILLIC_RATIO:.2f}"
                if ratio < MINIMUM_CYRILLIC_RATIO
                else ""
            ),
        ),
        FilingCheck(
            code="no_blocking_gaps",
            title_ru="Вопросов, меняющих вывод, не осталось",
            passed=gaps.blocking_count == 0,
            detail_ru=(f"Открыто вопросов: {gaps.blocking_count}" if gaps.blocking_count else ""),
        ),
    ]


def build_court_filing(
    *,
    result: ReviewedContractAnalysisResult,
    story: CaseStory,
    line: list[ConclusionStep],
    qualification: CaseQualification,
    verdict: CaseVerdict,
    gaps: GapQueue,
    documents: list[UploadedDocument] | None = None,
) -> CourtFiling:
    """Собрать проект процессуального документа по выводу системы."""
    kind = FILING_BY_VERDICT[verdict.state]
    title_ru = FILING_TITLES_RU[kind]

    circumstances: list[str] = []
    index = 1
    for section in story.sections:
        for fact in section.facts:
            if not fact.established:
                continue
            circumstances.append(f"{index}. {fact.text_ru}")
            index += 1
    if not circumstances:
        circumstances.append(
            "По делу не подтверждено ни одного обстоятельства. Излагать в этом "
            "документе нечего, и это само по себе обстоятельство."
        )
    circumstances.insert(0, story.summary_ru)

    sections = [
        FilingSection(title_ru="Обстоятельства дела", paragraphs_ru=circumstances),
        FilingSection(
            title_ru="Правовое обоснование",
            paragraphs_ru=_legal_grounds_ru(line, qualification),
        ),
        FilingSection(title_ru="Требование", paragraphs_ru=_claim_ru(kind, result)),
        FilingSection(title_ru="Доказательства", paragraphs_ru=_evidence_ru(documents or [])),
        FilingSection(title_ru="Оговорки", paragraphs_ru=_caveats_ru(verdict, gaps)),
    ]

    text = _assemble(title_ru, sections)
    checks = _run_checks(text, sections, gaps)
    failed = [check for check in checks if not check.passed]

    return CourtFiling(
        kind=kind,
        title_ru=title_ru,
        sections=sections,
        checks=checks,
        ready_to_file=not failed,
        blocker_ru="; ".join(check.title_ru for check in failed),
        text=text,
    )
