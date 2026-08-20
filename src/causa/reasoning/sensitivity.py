"""Однофакторный обход: система спрашивает обо всём, а не из списка.

## Зачем

Пробелы, которые видит оператор, до сих пор приходили из библиотеки правовых
операторов — семи заранее написанных вопросов. Вопрос, которого в библиотеке
нет, система не задавала никогда, даже когда он решал дело.

Измерение это подтвердило. Полный перебор всех 2¹³ = 8192 сочетаний фактов
обязательства показывает, в скольких из них переворот одного факта меняет хотя
бы один вывод:

```
remedy_requested            5394 (65,8 %)
limitation_period_expired   4096 (50,0 %)
duty_exists                 3584 (43,8 %)   <- библиотека не спрашивает
loss_claimed                2322 (28,3 %)
due_date_missed             2048 (25,0 %)
valid_exception_applies     2048 (25,0 %)
performance_completed       2048 (25,0 %)   <- библиотека не спрашивает
performance_nonconforming   2048 (25,0 %)
causation_established       2048 (25,0 %)
payment_duty_exists         1024 (12,5 %)
payment_due                 1024 (12,5 %)
payment_missed              1024 (12,5 %)
payment_defense_applies     1024 (12,5 %)   <- библиотека не спрашивает
```

Три факта из тринадцати не входят ни в один `fact_patch` библиотеки — и это
три главных возражения ответчика: «обязанности не было», «я исполнил», «у меня
есть возражение против платежа». Первое переворачивает вывод почти в половине
возможных конфигураций дела.

## Что здесь делается

Перебирается каждый булев факт по одному: значение меняется на
противоположное, модель пересчитывается, записывается, какие выводы
перевернулись. Никаких предпосылок и никакого списка вопросов — спрашивается
обо всём.

Замер на демонстрационном деле: тринадцать вызовов решателя, порядка сорока
миллисекунд. Дешевле, чем нынешняя сборка семи сценариев с проверкой хешей.

## Чем это не заменяет библиотеку операторов

Библиотека остаётся, и её роль меняется: не «о чём спрашивать», а «как назвать
найденное». У оператора есть юридическая формулировка вопроса и перечень
доказательств, которыми факт закрывается; обход этого не знает и знать не
может. Поэтому найденный обходом факт, для которого формулировки не написано,
показывается с honest-пометкой, а не выдаёт себя за юридический вопрос.

## Чего здесь нет

Пар и троек. Обход однофакторный: он найдёт факт, который переворачивает вывод
в одиночку, и не найдёт пары, которая переворачивает его только вместе. Это
названо прямо, потому что разница существенная, а поиск минимальных множеств —
отдельная работа (`z3.Optimize`), и делать вид, что она уже сделана, нельзя.
"""

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.legal_operators import FACT_LABELS_RU, OUTCOME_LABELS_RU
from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult
from causa.reasoning.formal_checks import evaluate_obligation_constraints

SENSITIVITY_VERSION = "reasoning-fact-sweep-v0"

#: Выводы, переворот которых меняет судьбу требования, а не подробность о нём.
#:
#: Список ведётся вручную и по смыслу: «возникает ли вопрос о нарушении»,
#: «доступно ли требование убытков» и «перекрыто ли требование давностью» решают
#: дело. «Пробел причинной связи» — доказательственная подробность внутри уже
#: возникшего вопроса.
DECISIVE_OUTCOMES: frozenset[str] = frozenset(
    {"breach_issue", "damages_remedy_available", "limitation_bar"}
)


class OutcomeFlip(BaseModel):
    """Один вывод, перевернувшийся от изменения одного факта."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: str
    label_ru: str
    before: bool
    after: bool

    @property
    def line_ru(self) -> str:
        return f"{self.label_ru}: станет «{'да' if self.after else 'нет'}»"


class FactSensitivity(BaseModel):
    """Что произойдёт, если один факт окажется другим."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = SENSITIVITY_VERSION
    fact: str
    label_ru: str
    from_value: bool
    to_value: bool
    flips: list[OutcomeFlip] = Field(default_factory=list)

    @property
    def decisive(self) -> bool:
        """Меняет ли этот факт судьбу требования, а не подробность о нём."""
        return any(flip.outcome in DECISIVE_OUTCOMES for flip in self.flips)

    @property
    def question_ru(self) -> str:
        state = "подтвердится" if self.to_value else "не подтвердится"
        return f"Изменится ли вывод, если «{self.label_ru.lower()}» {state}?"


def sweep_obligation_facts(result: ReviewedContractAnalysisResult) -> list[FactSensitivity]:
    """Перебрать каждый факт обязательства по одному и записать, что перевернётся.

    Возвращаются только факты, которые действительно что-то меняют: перечислять
    те, что не меняют ничего, значит выдавать список полей за список вопросов.
    """
    facts = result.evidence_mapping.facts
    constraint_set = result.constraint_set
    baseline = result.constraint_evaluation

    found: list[FactSensitivity] = []
    for field_name, field in type(facts).model_fields.items():
        if field.annotation is not bool:
            continue
        current = bool(getattr(facts, field_name))
        probe = evaluate_obligation_constraints(
            constraint_set, facts.model_copy(update={field_name: not current})
        )
        flips = [
            OutcomeFlip(
                outcome=outcome,
                label_ru=label_ru,
                before=bool(getattr(baseline, outcome)),
                after=bool(getattr(probe, outcome)),
            )
            for outcome, label_ru in OUTCOME_LABELS_RU.items()
            if bool(getattr(baseline, outcome)) != bool(getattr(probe, outcome))
        ]
        if not flips:
            continue
        found.append(
            FactSensitivity(
                fact=field_name,
                label_ru=FACT_LABELS_RU.get(field_name, field_name),
                from_value=current,
                to_value=not current,
                flips=flips,
            )
        )
    return found
