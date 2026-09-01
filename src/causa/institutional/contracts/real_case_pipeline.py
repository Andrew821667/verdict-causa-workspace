"""Прогон реальных дел через весь конвейер и измерение доходимости до выводов.

## Что здесь измеряется и почему это другой вопрос

`real_case_scenarios` запускает **один институт**: дело даёт факты для него, и
проверяется его вывод. Этого достаточно, чтобы сказать «модель института согласна
с судом», и недостаточно, чтобы сказать «система разобрала дело».

Здесь дело проходит `run_reviewed_contract_analysis` целиком, и измеряются три
разных свойства, которые одиночный прогон измерить не может:

1. **Дело проходит.** Факты реального дела не отвергаются жёсткими сверками
   входов — то есть согласуются с остальными институтами.
2. **Вывод института не меняется.** То, что институт сказал в одиночку, он
   говорит и внутри конвейера. Расхождение означало бы, что вывод зависит от
   окружения, а не от фактов.
3. **Дело доходит до слоя общих положений.** Или не доходит — и тогда обязано
   быть записано, почему молчание правильно.

Третье свойство — единственное, ради которого стоило это писать. Вывод
института, который никуда не распространяется, не влияет на то, что прочитает
юрист.

## Оговорка, без которой измерение вводит в заблуждение

Дело накладывается на демонстрационное дело о поставке: заменяются факты того
института, к которому дело переведено, а также те факты других контрактов
данных, которые дело объявило следствием позиции суда (`dependent_facts`,
`dependent_timeline`). Всё остальное остаётся демонстрационным. Полностью
собрать реальное дело нельзя — выгрузка не содержит фактов для девяноста с
лишним институтов, и достраивать их пришлось бы мне.

Поэтому здесь **не** проверяется, что система «решила дело так же, как суд».
Проверяется, что правовая суть дела проходит конвейер, не меняется в нём и
доходит (или обоснованно не доходит) до итоговых выводов.

## Почему появились зависимые факты

Правовой вывод суда почти никогда не остаётся внутри одного института.
Ничтожная сделка не порождает договорной обязанности; прекращённое зачётом или
новацией обязательство не может быть одновременно исполненным. Пока дело
описывало только «свой» институт, сверка входов справедливо отвергала смесь — и
четырнадцать дел из пятидесяти четырёх не доходили ни до одного вывода.

Чинить это «приведением в согласие» на стороне конвейера было нельзя: слой
сверки отказывается выбирать версию факта за рецензента, и автоматический выбор
на стороне набора дел был бы тем же выбором, только спрятанным. Поэтому версию
называет перевод фабулы — с обоснованием, которое требует тест.
"""

from datetime import date

from pydantic import BaseModel, Field

from causa.institutional.contracts.fact_consistency import FactConsistencyError
from causa.institutional.contracts.general_effects import GeneralEffectsInputs
from causa.institutional.contracts.real_case_pipeline_expectations import (
    LAYER_SILENCE_REASONS_RU,
    PIPELINE_REJECTION_REASONS_RU,
    UNREACHABLE_INSTITUTES_RU,
)
from causa.institutional.contracts.real_case_scenarios import (
    INSTITUTE_RUNNERS,
    REAL_CASE_SCENARIOS,
    RealCaseScenario,
    _flip,
)
from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisResult,
    run_reviewed_contract_analysis,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)

REAL_CASE_PIPELINE_VERSION = "contracts-real-case-pipeline-v0"

#: Институты, чьи выводы питают слой общих положений.
#:
#: Список ведётся здесь, а не выводится из кода: он должен ломаться при
#: изменении набора входов слоя, а не подстраиваться под него.
LAYER_FED_BY = (
    "formation",
    "invalidity",
    "form",
    "limitation",
    "representation",
    "property_rights",
    "civil_principles",
    "transactions",
    "terms",
    "persons",
    "objects",
    "constraint",
    "termination",
    "attribution_delay",
    "obligation_dynamics",
    "meeting_decisions",
)

_INSTITUTE_EVALUATION_FIELD = {name: f"{name}_evaluation" for name in INSTITUTE_RUNNERS}

_IGNORED_EVALUATION_FIELDS = frozenset(
    {"constraint_set_id", "satisfiable", "reasons_ru", "warnings_ru"}
)


class RealCasePipelineResult(BaseModel):
    """Что дало прохождение одного дела через весь конвейер."""

    case_id: str
    case_number: str
    institute: str
    accepted: bool
    rejection_explained: bool = True
    institute_conclusions_unchanged: bool
    changed_institute_fields: list[str] = Field(default_factory=list)
    layer_changes: dict[str, bool] = Field(default_factory=dict)
    layer_reached: bool = False
    requires_human_resolution: bool = False
    silence_explained: bool = True
    notes_ru: list[str] = Field(default_factory=list)


class RealCasePipelineReport(BaseModel):
    version: str = REAL_CASE_PIPELINE_VERSION
    total: int = 0
    accepted: int = 0
    rejected: int = 0
    reaching_the_layer: int = 0
    results: list[RealCasePipelineResult] = Field(default_factory=list)
    institutes_that_cannot_reach_the_layer: list[str] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


def build_real_case_request(scenario: RealCaseScenario):
    """Наложить факты реального дела на демонстрационное дело о поставке.

    Наложение идёт в два приёма. Сначала подменяются факты института, к
    которому дело переведено, — это и есть перевод фабулы. Затем подменяются
    факты других контрактов данных, объявленные в `dependent_facts`: следствия
    той же позиции суда, лежащие за пределами одного института.

    Второй приём добавлен не ради того, чтобы дело прошло. Без него дело о
    ничтожной сделке накладывалось на демонстрационное дело, где договорная
    обязанность существует, и сверка входов справедливо отвергала смесь.
    Выбирать версию факта за рецензента система отказывается — поэтому версию
    называет перевод фабулы, с обоснованием и под проверкой теста.
    """
    request = build_synthetic_supply_analysis_request()
    field = INSTITUTE_RUNNERS[scenario.institute].evidence_field
    updates = {field: _flip(getattr(request, field), scenario.facts)}
    for dependent_field, facts in scenario.dependent_facts.items():
        updates[dependent_field] = _flip(getattr(request, dependent_field), facts)
    if scenario.dependent_timeline:
        updates["temporal_evidence"] = request.temporal_evidence.model_copy(
            update={
                key: date.fromisoformat(value) if value is not None else None
                for key, value in scenario.dependent_timeline.items()
            }
        )
    return request.model_copy(update=updates)


def _evaluation_fields(evaluation) -> list[str]:
    return [
        name for name in type(evaluation).model_fields if name not in _IGNORED_EVALUATION_FIELDS
    ]


def _layer_fields() -> list[str]:
    from causa.institutional.contracts.general_effects import GeneralEffectsEvaluation

    return [
        name
        for name in GeneralEffectsEvaluation.model_fields
        if name not in _IGNORED_EVALUATION_FIELDS
    ]


def institutes_that_cannot_reach_the_layer() -> list[str]:
    """Институты набора реальных дел, чьи выводы не могут дойти до слоя.

    Считается по институтам переведённых дел, а не по всем раннерам. Раннер
    есть у каждого смоделированного института — их больше восьмидесяти, — и
    перечислять недоходимость всех значило бы измерять устройство слоя, а не
    набор дел. Здесь спрашивается о делах, которые действительно прогоняются.
    """
    declared = set(GeneralEffectsInputs.model_fields)
    if not declared:  # pragma: no cover - защита от пустой модели входов
        raise ValueError("Слой общих положений не объявил ни одного входа.")
    used = {scenario.institute for scenario in REAL_CASE_SCENARIOS}
    return sorted(name for name in used if name not in LAYER_FED_BY)


def run_real_case_through_pipeline(
    scenario: RealCaseScenario,
    baseline: ReviewedContractAnalysisResult,
    sources,
) -> RealCasePipelineResult:
    """Прогнать одно дело целиком и сравнить с демонстрационным дном."""
    from causa.institutional.contracts.real_case_scenarios import run_real_case_scenario

    standalone = run_real_case_scenario(scenario)
    try:
        result = run_reviewed_contract_analysis(build_real_case_request(scenario), sources)
    except FactConsistencyError as error:
        # Отказ конвейера — это измерение, а не сбой: смесь фактов реального
        # дела с остальными контрактами демонстрационного дела признана
        # противоречивой. Падать здесь означало бы потерять результат.
        reason = PIPELINE_REJECTION_REASONS_RU.get(scenario.case_id)
        return RealCasePipelineResult(
            case_id=scenario.case_id,
            case_number=scenario.case_number,
            institute=scenario.institute,
            accepted=False,
            rejection_explained=bool(reason),
            institute_conclusions_unchanged=True,
            notes_ru=[
                "Конвейер отверг дело на сверке входов: "
                + "; ".join(str(error).splitlines()[1:])
                + ".",
                reason or "Причина отказа не записана — это дефект набора, а не ответ.",
            ],
        )

    inside = getattr(result, _INSTITUTE_EVALUATION_FIELD[scenario.institute])
    changed = [
        name
        for name in _evaluation_fields(standalone)
        if getattr(standalone, name) != getattr(inside, name)
    ]
    layer_changes = {
        name: getattr(result.general_effects_evaluation, name)
        for name in _layer_fields()
        if getattr(baseline.general_effects_evaluation, name)
        != getattr(result.general_effects_evaluation, name)
    }
    notes: list[str] = []
    silence_explained = True
    if layer_changes:
        notes.append(
            "Правовая суть дела дошла до слоя общих положений: "
            + ", ".join(sorted(layer_changes))
            + "."
        )
    else:
        reason = LAYER_SILENCE_REASONS_RU.get(scenario.case_id)
        silence_explained = bool(reason)
        notes.append(
            f"Слой общих положений не изменился. {reason}"
            if reason
            else "Слой общих положений не изменился, и причина молчания не записана."
        )
    return RealCasePipelineResult(
        case_id=scenario.case_id,
        case_number=scenario.case_number,
        institute=scenario.institute,
        accepted=True,
        institute_conclusions_unchanged=not changed,
        changed_institute_fields=changed,
        layer_changes=layer_changes,
        layer_reached=bool(layer_changes),
        requires_human_resolution=result.requires_human_resolution,
        silence_explained=silence_explained,
        notes_ru=notes,
    )


def run_real_case_pipeline_suite() -> RealCasePipelineReport:
    """Прогнать все переведённые дела через весь конвейер."""
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(build_synthetic_supply_analysis_request(), sources)
    results = [
        run_real_case_through_pipeline(scenario, baseline, sources)
        for scenario in REAL_CASE_SCENARIOS
    ]
    unreachable = institutes_that_cannot_reach_the_layer()
    reaching = sum(entry.layer_reached for entry in results)
    rejected = [entry for entry in results if not entry.accepted]
    with_dependent = [
        scenario
        for scenario in REAL_CASE_SCENARIOS
        if scenario.dependent_facts or scenario.dependent_timeline
    ]
    notes = [
        "Дело накладывается на демонстрационное дело о поставке: заменяются факты "
        "того института, к которому дело переведено, и те факты других контрактов "
        "данных, которые дело объявило следствием позиции суда. Поэтому здесь не "
        "проверяется, что система решила дело так же, как суд.",
        f"Объявили зависимые факты: {len(with_dependent)} из {len(results)}. Каждое "
        "такое объявление несёт причину, выведенную из позиции суда, и проверяется "
        "тестом: правка чужого контракта данных без записанной причины неотличима "
        "от подгонки под конвейер.",
        f"Дошли до слоя общих положений: {reaching} из {len(results)}. Молчание слоя "
        "по остальным делам обязано быть объяснено, и объяснения проверяются тестом.",
    ]
    if rejected:
        notes.append(
            f"Отвергнуто конвейером: {len(rejected)} из {len(results)}. Отказ означает, "
            "что факты дела несовместимы с остальными контрактами демонстрационного "
            "дела, а не что модель ошиблась по существу спора: "
            + ", ".join(sorted(entry.case_number for entry in rejected))
            + "."
        )
    if unreachable:
        notes.append(
            "Институты этого набора, чьи выводы не могут дойти до слоя: "
            + ", ".join(
                f"{name} — {UNREACHABLE_INSTITUTES_RU.get(name, 'причина не записана')}"
                for name in unreachable
            )
            + "."
        )
    return RealCasePipelineReport(
        total=len(results),
        accepted=sum(entry.accepted for entry in results),
        rejected=len(rejected),
        reaching_the_layer=reaching,
        results=results,
        institutes_that_cannot_reach_the_layer=unreachable,
        notes_ru=notes,
    )
