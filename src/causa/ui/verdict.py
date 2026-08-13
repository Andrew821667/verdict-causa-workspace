"""Вердикт по делу: главный ответ, который должен читаться первым.

## Чего не хватало

Первая версия окна показывала двенадцать звеньев рассуждения и ни одного
ответа. Юрист, открывший дело, видел работу системы, но не видел, что она
поняла. Разбор без вердикта — это протокол вычисления, а не результат.

## Как вердикт выводится

Из тех же полей, что уже вычислены; порядок проверок — юридический, а не
удобный:

1. **Выводы института не имеют эффекта.** Договор не заключён, недействителен
   или порочен по форме: слой общих положений говорит
   `institute_conclusions_displaced` либо `breach_findings_without_effect`.
   Спорить о просрочке в этом случае бессмысленно, и вердикт об этом.
2. **Требование заблокировано.** `claims_barred_by_limitation` — давность
   съела требование независимо от того, было нарушение или нет.
3. **Нарушение установлено** либо **не установлено** — `breach_issue`.

Отдельно от вердикта идут два ограничителя, которые его не отменяют, но меняют
то, что с ним можно делать: доступность требования убытков и запрос
человеческой оценки.

## Почему вердикт не «уверен на N процентов»

По той же причине, по которой её нет у квалификации: решатель отвечает «да» или
«нет» по проверенным фактам. Неопределённость выражается иначе — числом
пробелов, которые переворачивают вывод. Семь открытых пробелов рядом с «да»
честнее, чем «да, 62%».
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult
from causa.ui.gaps import GapQueue
from causa.ui.qualification import CaseQualification

VERDICT_VERSION = "ui-verdict-v0"


class VerdictState(str, Enum):
    BREACH_ESTABLISHED = "breach_established"
    NO_BREACH = "no_breach"
    CLAIM_BARRED = "claim_barred"
    FINDINGS_WITHOUT_EFFECT = "findings_without_effect"


class Tone(str, Enum):
    """Как показывать значение: это оценка серьёзности, а не украшение."""

    NEUTRAL = "neutral"
    GOOD = "good"
    WARN = "warn"
    STOP = "stop"


class VerdictMetric(BaseModel):
    """Одна плитка состояния дела."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    label_ru: str
    value_ru: str
    tone: Tone = Tone.NEUTRAL
    hint_ru: str = ""


class CaseVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = VERDICT_VERSION
    state: VerdictState
    tone: Tone
    headline_ru: str
    detail_ru: str
    #: Что ограничивает вывод, не отменяя его.
    qualifiers_ru: list[str] = Field(default_factory=list)
    #: Что делать дальше — одна строка, а не список пожеланий.
    next_step_ru: str = ""
    metrics: list[VerdictMetric] = Field(default_factory=list)


def _needs_human(result: ReviewedContractAnalysisResult) -> list[str]:
    flagged: list[str] = []
    for field_name in ReviewedContractAnalysisResult.model_fields:
        if not field_name.endswith("_evaluation"):
            continue
        evaluation = getattr(result, field_name)
        for name in type(evaluation).model_fields:
            if name.startswith("requires_human_") and getattr(evaluation, name) is True:
                flagged.append(field_name[: -len("_evaluation")])
                break
    return flagged


def build_case_verdict(
    result: ReviewedContractAnalysisResult,
    qualification: CaseQualification,
    gaps: GapQueue,
) -> CaseVerdict:
    """Собрать главный ответ по делу."""
    constraint = result.constraint_evaluation
    layer = result.general_effects_evaluation
    flagged = _needs_human(result)
    blocking = gaps.blocking_count

    if layer.institute_conclusions_displaced or layer.breach_findings_without_effect:
        state = VerdictState.FINDINGS_WITHOUT_EFFECT
        tone = Tone.STOP
        headline = "Выводы о нарушении не имеют эффекта"
        detail = (
            "Договор как основание требований не действует: он не заключён, "
            "недействителен либо порочен по форме. Спор о просрочке в этом "
            "случае решается не сроками, а судьбой самой сделки."
        )
        next_step = "Разобрать основание недействительности до возврата к вопросу о нарушении."
    elif layer.claims_barred_by_limitation:
        state = VerdictState.CLAIM_BARRED
        tone = Tone.STOP
        headline = "Требование заблокировано исковой давностью"
        detail = (
            "Заявление о пропуске срока перекрывает требование независимо от "
            "того, было нарушение или нет (статья 199 ГК РФ)."
        )
        next_step = "Проверить основания перерыва, приостановления или восстановления срока."
    elif constraint.breach_issue:
        state = VerdictState.BREACH_ESTABLISHED
        tone = Tone.WARN
        parts = []
        if constraint.late_performance_issue:
            parts.append("просрочка исполнения")
        if constraint.defect_issue:
            parts.append("ненадлежащее исполнение")
        if constraint.payment_default_issue:
            parts.append("просрочка платежа")
        headline = "Вопрос о нарушении обязательства возникает"
        detail = (
            ("Установлено: " + ", ".join(parts) + ". ") if parts else ""
        ) + "Применимое основание освобождения от ответственности не подтверждено."
        next_step = (
            "Закрыть пробелы, от которых зависит вывод, — до этого вывод не окончателен."
            if blocking
            else "Перейти к выбору средства защиты и расчёту требования."
        )
    else:
        state = VerdictState.NO_BREACH
        tone = Tone.GOOD
        headline = "Нарушение обязательства не установлено"
        detail = (
            "По проверенным фактам предпосылки нарушения не подтверждены. Это "
            "вывод о представленных фактах, а не о деле вообще."
        )
        next_step = "Проверить, все ли материалы загружены: вывод держится на том, что есть."

    qualifiers: list[str] = []
    if state is VerdictState.BREACH_ESTABLISHED and not constraint.damages_remedy_available:
        qualifiers.append(
            "Требование убытков формально недоступно: подтверждены не все его предпосылки."
        )
    if constraint.causation_evidence_gap:
        qualifiers.append(
            "Причинная связь между нарушением и убытками не доказана — это "
            "доказательственный пробел, а не отказ в требовании."
        )
    if layer.limitation_conclusion_unreliable:
        qualifiers.append("Вывод об исковой давности ненадёжен: входные факты о сроке неполны.")
    if layer.term_deprived_of_meeting_basis:
        qualifiers.append(
            "Условие договора держится на решении собрания, которое ничтожно либо не "
            "принято: в этой части у требования нет основания. Какое именно условие "
            "спорно, определяет юрист (статьи 181.3 и 181.5 ГК РФ)."
        )
    if layer.term_meeting_basis_challengeable:
        qualifiers.append(
            "Решение собрания, на котором держится условие договора, оспоримо: условие "
            "действует, пока суд не признал решение недействительным (статья 181.4 ГК РФ)."
        )
    if flagged:
        qualifiers.append(
            "Институт запросил юридическую оценку человека — вывод нельзя "
            "показывать как окончательный."
        )

    primary = qualification.primary
    metrics = [
        VerdictMetric(
            label_ru="Тип договора",
            value_ru=primary.title_ru if primary else "не определён",
            tone=Tone.NEUTRAL if primary else Tone.WARN,
            hint_ru=primary.articles_ru if primary else "ни один предикат квалификации не сработал",
        ),
        VerdictMetric(
            label_ru="Пробелов, меняющих вывод",
            value_ru=str(blocking),
            tone=Tone.WARN if blocking else Tone.GOOD,
            hint_ru=(
                "пока они открыты, вывод не окончателен"
                if blocking
                else "ни один известный вопрос не переворачивает вывод"
            ),
        ),
        VerdictMetric(
            label_ru="Договор действует",
            value_ru="да" if layer.contract_legally_effective else "нет",
            tone=Tone.GOOD if layer.contract_legally_effective else Tone.STOP,
            hint_ru="основание требований из договора",
        ),
        VerdictMetric(
            label_ru="Судебная защита",
            value_ru="доступна" if layer.judicial_protection_available else "недоступна",
            tone=Tone.GOOD if layer.judicial_protection_available else Tone.STOP,
            hint_ru="исковая давность и пределы осуществления прав",
        ),
    ]
    if flagged:
        metrics.append(
            VerdictMetric(
                label_ru="Требуется человек",
                value_ru=str(len(flagged)),
                tone=Tone.STOP,
                hint_ru="институтов, дошедших до границы своей компетенции",
            )
        )

    return CaseVerdict(
        state=state,
        tone=tone,
        headline_ru=headline,
        detail_ru=detail,
        qualifiers_ru=qualifiers,
        next_step_ru=next_step,
        metrics=metrics,
    )
