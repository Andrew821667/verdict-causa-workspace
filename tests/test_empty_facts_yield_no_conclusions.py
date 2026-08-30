"""Институт не должен делать выводов о деле, которого в фактах нет.

## Почему эта проверка появилась

Подключение четырёх институтов банкротства к конвейеру перевернуло
`requires_human_resolution` с False на True в чистом споре о поставке.
Причина оказалась не в проводке: `bankruptcy_claims` читал набор фактов, где
всё ложно, как «обязательство возникло после принятия заявления», объявлял
требование текущим платежом и поднимал флаг переходного периода КС РФ — в
деле, где банкротства нет вовсе. Главный сигнал «зови юриста» стал вечно
истинным, то есть бессмысленным.

Пока институтов было немного, пустой блок фактов был редкостью. Сейчас их 95,
и для любого дела почти все институты не относятся к спору — пустой блок стал
нормой, а не исключением. Значит, цена этого дефекта выросла.

## Что именно проверяется

Каждый институт получает набор фактов, где всё ложно, и не должен поднимать
флаг проверки юристом. Это самая ядовитая форма дефекта: она портит сводный
сигнал по делу, а не только вывод одного института.

## Чего проверка НЕ требует

Молчания вообще. Утвердительный вывод на пустых фактах бывает правомерным:

- «форма соблюдена, если письменная форма не требуется» (`form`) — верно,
  нет требования — нет нарушения;
- «перерыв в подаче правомерен, если перерыва не было» (`energy_supply`);
- «единство условий соблюдено, если режим публичного договора не применяется»
  (`public_contract`);
- «требование не подлежит исковой давности» (`limitation`) — отрицание входа,
  а не утверждение сверх него.

Такие выводы говорят об отсутствии нарушения, а не о существовании отношения.
Отличать их от ложных утверждений о несуществующем деле — работа юриста, а не
регулярного выражения, поэтому список ниже ведётся руками и обязан нести
причину по каждой записи.
"""

import importlib

import pytest

from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult

#: Слои, а не институты: у них на входе Inputs, а не FactSet.
LAYERS = {"general_effects", "general_consistency"}

#: Институты без модуля того же имени либо с иным соглашением об именах.
#: Они разбираются собственными тестами, а не этой проверкой.
OUTSIDE_CONVENTION = {"authority", "constraint", "temporal"}

#: Выводы, истинные на пустых фактах правомерно, с причиной по каждому.
#: Записи здесь — не исключения «чтобы тест позеленел», а утверждение о праве.
LAWFUL_ON_EMPTY_FACTS: dict[str, dict[str, str]] = {
    "energy_supply": {
        "supply_interruption_lawful": (
            "перерыв в подаче правомерен, если перерыва не было: вывод об "
            "отсутствии нарушения, а не о существовании энергоснабжения"
        ),
    },
    "form": {
        "written_form_satisfied": (
            "письменная форма соблюдена, если она не требуется (пункт 1 статьи 159): "
            "нет требования — нет нарушения"
        ),
        "notarial_form_satisfied": (
            "то же для нотариальной формы (статья 163): она обязательна лишь в "
            "случаях, указанных в законе или соглашении сторон"
        ),
        "form_requirement_satisfied": (
            "конъюнкция двух предыдущих выводов: требование о форме соблюдено, "
            "когда ни письменная, ни нотариальная форма не нарушены"
        ),
    },
    "limitation": {
        "claim_not_subject_to_limitation": (
            "прямое отрицание входного признака (статья 208), а не утверждение "
            "о существовании требования"
        ),
    },
    "public_contract": {
        "uniform_terms_satisfied": (
            "единство условий соблюдено, если режим публичного договора не применяется (статья 426)"
        ),
    },
}


def _institutes() -> list[str]:
    return sorted(
        name[: -len("_evaluation")]
        for name in ReviewedContractAnalysisResult.model_fields
        if name.endswith("_evaluation")
        and name[: -len("_evaluation")] not in LAYERS | OUTSIDE_CONVENTION
    )


def _camel(snake: str) -> str:
    return "".join(part.capitalize() for part in snake.split("_"))


def _evaluate_on_empty_facts(name: str):
    module = importlib.import_module(f"causa.institutional.contracts.{name}")
    prefix = _camel(name)
    fact_set = getattr(module, f"{prefix}FactSet")
    mapping_result = getattr(module, f"{prefix}EvidenceMappingResult")
    build = getattr(module, f"build_{name}_constraint_set")
    evaluate = getattr(module, f"evaluate_{name}_constraints")
    refs = getattr(module, f"{name.upper()}_LEGAL_SOURCE_REFS", ())

    facts = fact_set(**{field: False for field in fact_set.model_fields})
    mapping = mapping_result(
        evidence_id="empty-facts-audit",
        schema_version="empty-facts-audit",
        mapping_version="empty-facts-audit",
        facts=facts,
        legal_source_refs=list(refs),
    )
    return evaluate(build(mapping), facts)


@pytest.mark.parametrize("institute", _institutes())
def test_empty_facts_never_demand_a_lawyer(institute: str) -> None:
    """Пустой блок фактов не должен портить сводный сигнал по делу."""
    evaluation = _evaluate_on_empty_facts(institute)

    flagged = [
        name
        for name in type(evaluation).model_fields
        if name.startswith("requires_human_") and getattr(evaluation, name) is True
    ]

    assert flagged == [], f"{institute} требует юриста на пустых фактах: {flagged}"


@pytest.mark.parametrize("institute", _institutes())
def test_affirmative_conclusions_on_empty_facts_are_declared(institute: str) -> None:
    """Новый утвердительный вывод на пустых фактах обязан быть объяснён.

    Тест не запрещает такие выводы — он запрещает заводить их молча. Если
    институт начал что-то утверждать о деле, которого в фактах нет, это либо
    правомерная оценка отсутствия нарушения, и тогда причина пишется в
    `LAWFUL_ON_EMPTY_FACTS`, либо дефект — и тогда его чинят.
    """
    evaluation = _evaluate_on_empty_facts(institute)
    declared = LAWFUL_ON_EMPTY_FACTS.get(institute, {})

    undeclared = [
        name
        for name in type(evaluation).model_fields
        if getattr(evaluation, name) is True
        and name != "satisfiable"
        and not name.startswith("requires_human_")
        and name not in declared
    ]

    assert undeclared == [], f"{institute} утверждает на пустых фактах без записи: {undeclared}"


def test_every_declared_exception_states_a_reason() -> None:
    """Запись без причины неотличима от отписки ради зелёного теста."""
    for institute, outputs in LAWFUL_ON_EMPTY_FACTS.items():
        assert outputs, institute
        for output, reason in outputs.items():
            assert len(reason) > 40, f"{institute}.{output}"


def test_the_two_institutes_the_audit_repaired_stay_silent() -> None:
    """Регрессия на найденное аудитом: `sale` и `freedom` больше не утверждают.

    `sale` выводил «цена определяется по общему правилу пункта 3 статьи 424» —
    утверждение о существующем договоре купли-продажи; `freedom` — «договор
    заключён свободно и предполагается возмездным». Оба через свои
    `requires_human_*` поднимали флаг проверки юристом на пустом месте.
    """
    for institute in ("sale", "freedom"):
        evaluation = _evaluate_on_empty_facts(institute)
        affirmed = [
            name
            for name in type(evaluation).model_fields
            if getattr(evaluation, name) is True and name != "satisfiable"
        ]
        assert affirmed == [], f"{institute}: {affirmed}"
