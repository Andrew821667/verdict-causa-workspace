"""Основное окно: линия вывода, спор вокруг неё и три регистра изложения.

## Два вида одного результата

По умолчанию оператор видит **линию вывода** — упорядоченную цепочку: норма
применима → договор заключён → сделка действительна → срок пропущен →
основание освобождения не подтверждено → нарушение. Каждое звено несёт ссылки
на источники, из которых оно получено.

Переключатель открывает **спор** — то же самое, но с трёх сторон.

## Чем этот спор является и чем не является

Раздел 8.2 концепции описывает состязательное рассуждение нескольких агентов
(за, против, критик, доктрина, калибратор). В ядре его нет, и рисовать
несуществующий спор агентов интерфейс не будет.

Здесь спор собран из трёх источников, которые конвейер действительно вычисляет:

**За** — утверждения, приведшие к выводу, со ссылками на источники.

**Против** — материальные контрфактические сценарии: факты, установление
которых переворачивает вывод. Это возражение, вычисленное решателем, а не
сочинённое; в нём видно, чем именно вывод уязвим.

**Критик пути** — сравнение с альтернативным путём рассуждения и записанная
причина, по которой он отклонён (`build_reasoning_path_comparison`).

Разница существенная, и она названа в интерфейсе прямо: это не спор агентов, а
разбор одного пути с трёх сторон.

## Почему линия задана списком, а не выведена

Порядок звеньев — юридическое утверждение о том, в каком порядке решается спор
о нарушении договора, а не свойство модели данных. Он ведётся здесь вручную и
обязан ломаться при появлении нового звена, а не подстраиваться под него.
"""

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisRequest,
    ReviewedContractAnalysisResult,
)
from causa.translation import TranslationAssertion, TranslationAssertionCode, TranslationLevel
from causa.translation_pipeline import (
    TranslationBundle,
    build_reasoning_path_comparison,
    build_translation_assertions,
)

REASONING_VIEW_VERSION = "ui-reasoning-view-v0"

_C = TranslationAssertionCode

#: Порядок решения спора о нарушении договора — то, что оператор читает сверху вниз.
#:
#: Список ведётся вручную: это утверждение о праве, а не о структуре данных.
CONCLUSION_SPINE: tuple[tuple[TranslationAssertionCode, str], ...] = (
    (_C.SOURCE_APPLICABLE, "Применима ли норма на дату оценки"),
    (_C.CONTRACT_CONCLUDED_PREREQUISITES, "Заключён ли договор"),
    (_C.TRANSACTION_PRESUMED_EFFECTIVE, "Действительна ли сделка"),
    (_C.VOID_GROUND_DETECTED, "Есть ли основание ничтожности"),
    (_C.SUPPLY_CONTRACT_QUALIFIED, "Каким типом описывается договор"),
    (_C.DUE_DATE_MISSED, "Пропущен ли срок"),
    (_C.LIABILITY_EXEMPTION_PREREQUISITES, "Подтверждено ли основание освобождения"),
    (_C.BREACH_ISSUE, "Возникает ли вопрос о нарушении"),
    (_C.DAMAGES_REMEDY_AVAILABLE, "Доступно ли требование убытков"),
    (_C.CAUSATION_EVIDENCE_GAP, "Остался ли пробел причинной связи"),
    (_C.LIMITATION_BAR, "Заблокировано ли требование исковой давностью"),
    (_C.HUMAN_RESOLUTION_REQUIRED, "Требуется ли решение человека"),
)


class ConclusionStep(BaseModel):
    """Одно звено линии вывода."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    question_ru: str
    value: bool | str
    text_ru: str
    source_refs: list[str] = Field(default_factory=list)


class DebateSide(BaseModel):
    """Одна сторона разбора: чем она является и что в ней."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title_ru: str
    origin_ru: str
    points_ru: list[str] = Field(default_factory=list)


class DebateView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    disclaimer_ru: str = (
        "Это не состязательный разбор нескольких агентов из раздела 8.2 концепции: "
        "в ядре его нет. Это один путь рассуждения, показанный с трёх сторон, "
        "каждая из которых вычислена конвейером."
    )
    supporting: DebateSide
    opposing: DebateSide
    critic: DebateSide


class RegisterText(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    level: TranslationLevel
    level_ru: str
    text: str
    faithfulness_passed: bool
    usability_passed: bool


LEVEL_LABELS_RU = {
    TranslationLevel.EXECUTIVE: "коротко для решения",
    TranslationLevel.PROFESSIONAL: "для юриста",
    TranslationLevel.FORENSIC: "для суда, с координатами",
}


class ReasoningView(BaseModel):
    """Содержимое основного окна дела."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = REASONING_VIEW_VERSION
    line: list[ConclusionStep] = Field(default_factory=list)
    debate: DebateView
    registers: list[RegisterText] = Field(default_factory=list)
    #: Все 80 утверждений — не скрыты, а убраны на второй план.
    all_assertions: list[ConclusionStep] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


def _step(
    assertion: TranslationAssertion,
    question_ru: str,
) -> ConclusionStep:
    return ConclusionStep(
        code=assertion.code.value,
        question_ru=question_ru,
        value=assertion.value,
        text_ru=assertion.text_ru,
        source_refs=list(assertion.source_refs),
    )


def build_reasoning_view(
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
    bundle: TranslationBundle | None = None,
) -> ReasoningView:
    """Собрать основное окно: линию вывода, спор и регистры изложения."""
    assertions = build_translation_assertions(request, result)
    by_code = {assertion.code: assertion for assertion in assertions}

    line: list[ConclusionStep] = []
    missing: list[str] = []
    for code, question_ru in CONCLUSION_SPINE:
        assertion = by_code.get(code)
        if assertion is None:
            missing.append(code.value)
            continue
        line.append(_step(assertion, question_ru))

    # Полные списки источников остаются в линии вывода: перенесённые сюда, они
    # превращают колонку «За» в стену идентификаторов и прячут сам довод.
    supporting_points = [f"{step.text_ru} (источников: {len(step.source_refs)})" for step in line]

    report = result.counterfactual_sensitivity
    opposing_points: list[str] = []
    if report is not None:
        for scenario in report.scenarios:
            if not scenario.material:
                continue
            flips = ", ".join(
                f"{delta.field_label_ru} → {'да' if delta.after else 'нет'}"
                for delta in scenario.outcome_deltas
            )
            opposing_points.append(f"{scenario.legal_question_ru} Тогда: {flips}.")

    comparison = build_reasoning_path_comparison(request, result)
    critic_points = [f"Отклонённый путь: {step}" for step in comparison.alternative_path_ru] + list(
        comparison.material_differences_ru
    )
    critic_points.append(comparison.selection_reason_ru)

    registers: list[RegisterText] = []
    if bundle is not None:
        for level in TranslationLevel:
            artifact = bundle.artifact_for(level)
            registers.append(
                RegisterText(
                    level=level,
                    level_ru=LEVEL_LABELS_RU[level],
                    text=artifact.text,
                    faithfulness_passed=artifact.faithfulness_passed,
                    usability_passed=artifact.usability_passed,
                )
            )

    notes: list[str] = []
    if missing:
        notes.append(
            "Звенья линии вывода отсутствуют в наборе утверждений: "
            + ", ".join(missing)
            + ". Линия показана неполной, а не достроена догадкой."
        )
    if not registers:
        notes.append(
            "Регистры изложения не собраны: bundle Translation Layer для этого "
            "дела не передан. Текст для суда не подменяется текстом для юриста."
        )

    return ReasoningView(
        line=line,
        debate=DebateView(
            supporting=DebateSide(
                title_ru="За",
                origin_ru=(
                    "утверждения, из которых собран вывод; полные ссылки на "
                    "источники — во вкладке «Линия вывода»"
                ),
                points_ru=supporting_points,
            ),
            opposing=DebateSide(
                title_ru="Против",
                origin_ru=(
                    "материальные контрфакты: факты, установление которых "
                    "переворачивает вывод (вычислено решателем)"
                ),
                points_ru=opposing_points,
            ),
            critic=DebateSide(
                title_ru="Критик пути",
                origin_ru="сравнение с альтернативным путём и причина его отклонения",
                points_ru=critic_points,
            ),
        ),
        registers=registers,
        all_assertions=[_step(assertion, "полный список утверждений") for assertion in assertions],
        notes_ru=notes,
    )
