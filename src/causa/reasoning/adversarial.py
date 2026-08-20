"""Спор как расхождение двух допустимых миров.

## Что было

Колонка «Критик пути» собиралась функцией `build_reasoning_path_comparison`,
которая принимает дело и результат — и использует из них ровно два значения:
идентификатор дела и один булев вывод. Пять её строк из шести совпадают дословно
для любого дела, шестая отличается словом «да» или «нет». Отклонённый
«альтернативный путь» — одна фраза про то, что нельзя считать любую просрочку
нарушением: заведомо негодный оппонент, который никогда не строится и никогда не
оценивается.

Колонка «За» была пересказом линии вывода. Настоящей в этом споре была одна
сторона из трёх.

## Что здесь

Спор не сочиняется и не порождается моделью — он **уже существует в деле** как
расхождение между двумя допустимыми доопределениями спорных фактов.

Спорный факт — тот, который стороны вправе толковать по-разному, потому что он
ничем не закрыт. Из него строятся два мира:

**мир истца** — каждый спорный факт принимает значение, выгодное истцу;
**мир ответчика** — то же самое в пользу ответчика.

Оба прогоняются через одно и то же правило, и дальше всё вычисляется:

* **за** — выводы, устоявшие в обоих мирах: их не поколеблет ни одно толкование
  спорного;
* **против** — выводы, падающие в мире ответчика: вот чем позиция уязвима;
* **критик** — спорные факты, от доказывания которых расхождение зависит, в
  порядке того, сколько выводов каждый переключает.

## Откуда известно, что выгодно кому

Из таблицы бремени доказывания, а не из новой таблицы. Сторона, обязанная
доказать факт, нуждается в значении, противоположном тому, которое факт
принимает недоказанным: кредитор доказывает существование обязанности, значит
ему выгодно «да»; должник доказывает отсутствие вины, значит ему выгодно «да» по
основанию освобождения. Второй такой таблицы заводить нельзя — разойдутся.

## Чем это не является

Это не состязательное рассуждение пяти агентов из раздела 8.2 концепции. Три
роли из пяти здесь построены, и построены без языковой модели; двух других —
доктрины и калибратора — нет. Доктрине нужен корпус и поиск по нему, которого в
ядре нет; калибратору нужно число уверенности, которому неоткуда взяться.
Отсутствие названо, а не имитировано.
"""

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.legal_operators import FACT_LABELS_RU, OUTCOME_LABELS_RU
from causa.reasoning.formal_checks import ConstraintSet, ObligationFactSet
from causa.reasoning.three_valued import (
    BURDEN_BY_FACT,
    PARTY_LABELS_RU,
    Party,
    UnknownFactError,
    _outcomes_for,
    _rules,
)

ADVERSARIAL_VERSION = "reasoning-two-worlds-v0"


def favourable_value(fact: str, party: Party) -> bool:
    """Какое значение факта выгодно этой стороне.

    Выводится из бремени: сторона, обязанная доказать факт, нуждается в
    значении, противоположном тому, которое факт принимает недоказанным.
    """
    rule = BURDEN_BY_FACT.get(fact)
    if rule is None:
        raise UnknownFactError(f"Для факта «{fact}» не записано бремя доказывания.")
    wanted_by_bearer = not rule.unproven_value
    return wanted_by_bearer if party is rule.borne_by else rule.unproven_value


class ContestedFact(BaseModel):
    """Спорный факт и то, чем он оборачивается для каждой стороны."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fact: str
    label_ru: str
    claimant_value: bool
    respondent_value: bool
    #: Сколько выводов переключает этот факт между мирами.
    switches: list[str] = Field(default_factory=list)

    @property
    def line_ru(self) -> str:
        bearer = BURDEN_BY_FACT[self.fact]
        return (
            f"{self.label_ru}: доказывает {PARTY_LABELS_RU[bearer.borne_by]}; "
            f"от него зависит выводов — {len(self.switches)}"
        )


class WorldConclusion(BaseModel):
    """Один вывод в двух мирах."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: str
    label_ru: str
    in_claimant_world: bool
    in_respondent_world: bool

    @property
    def stable(self) -> bool:
        return self.in_claimant_world == self.in_respondent_world


class TwoWorldDebate(BaseModel):
    """Спор, вычисленный из дела, а не написанный заранее."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = ADVERSARIAL_VERSION
    contested: list[ContestedFact] = Field(default_factory=list)
    conclusions: list[WorldConclusion] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)

    @property
    def supporting_ru(self) -> list[str]:
        """Выводы, устоявшие в обоих мирах."""
        return [
            f"{item.label_ru}: «{'да' if item.in_claimant_world else 'нет'}» при любом "
            "толковании спорного"
            for item in self.conclusions
            if item.stable
        ]

    @property
    def opposing_ru(self) -> list[str]:
        """Выводы, расходящиеся между мирами: чем позиция уязвима."""
        return [
            f"{item.label_ru}: у истца «{'да' if item.in_claimant_world else 'нет'}», "
            f"у ответчика «{'да' if item.in_respondent_world else 'нет'}»"
            for item in self.conclusions
            if not item.stable
        ]

    @property
    def critic_ru(self) -> list[str]:
        """Спорные факты в порядке того, сколько выводов каждый решает."""
        return [item.line_ru for item in self.contested if item.switches]

    @property
    def disputed(self) -> bool:
        return any(not item.stable for item in self.conclusions)


#: Приставка идентификатора документа, приложенного оператором.
_DOCUMENT_PREFIX = "doc:"


def contested_without_documents(result) -> set[str]:
    """Факты, за которыми не стоит ни одного приложенного документа.

    Это и есть спорное в обычном смысле: пока факт держится только на
    утверждении, противная сторона вправе прочитать его иначе. Как только
    оператор закрывает факт документом, идентификатор документа попадает в
    `source_refs`, и факт перестаёт быть спорным.

    Определение намеренно грубое и проверяемое. Тонкое — «документ слабый»,
    «документ оспорим» — потребовало бы оценки доказательства, которой система
    не делает и делать не должна.
    """
    return {
        item.fact_name
        for item in result.evidence_mapping.provenance
        if not any(str(ref).startswith(_DOCUMENT_PREFIX) for ref in item.source_refs)
    }


def build_two_world_debate(
    constraint_set: ConstraintSet,
    facts: ObligationFactSet,
    contested: set[str] | None = None,
) -> TwoWorldDebate:
    """Построить спор как расхождение двух допустимых миров.

    `contested` — факты, которые стороны вправе толковать по-разному. Пустое
    множество означает, что спорить не о чем, и это тоже ответ.
    """
    contested = set(contested or ())
    declared = set(type(facts).model_fields)
    strangers = sorted(contested - declared)
    if strangers:
        raise UnknownFactError("В модели обязательства нет фактов: " + ", ".join(strangers))

    rules = _rules(constraint_set)
    base = {name: bool(getattr(facts, name)) for name in declared}

    def world(party: Party) -> dict[str, bool]:
        values = dict(base)
        values.update({fact: favourable_value(fact, party) for fact in contested})
        return _outcomes_for(rules, values)

    claimant = world(Party.CLAIMANT)
    respondent = world(Party.RESPONDENT)

    conclusions = [
        WorldConclusion(
            outcome=name,
            label_ru=label_ru,
            in_claimant_world=bool(claimant.get(name, False)),
            in_respondent_world=bool(respondent.get(name, False)),
        )
        for name, label_ru in OUTCOME_LABELS_RU.items()
        if name in rules
    ]

    # Какой спорный факт что решает. Считается прямо: взять мир одной стороны,
    # уступить в нём один факт другой стороне и посмотреть, что перевернулось.
    #
    # Убирать факт из спорных было бы неверно: если расхождение держат два
    # факта, каждый из которых достаточен сам по себе, то удаление любого из
    # них ничего не меняет, и оба выглядели бы ни на что не влияющими. Ровно
    # это и произошло при первой попытке — колонка «критик» вышла пустой при
    # двух живых расхождениях.
    claimant_inputs = dict(base)
    claimant_inputs.update({fact: favourable_value(fact, Party.CLAIMANT) for fact in contested})
    respondent_inputs = dict(base)
    respondent_inputs.update({fact: favourable_value(fact, Party.RESPONDENT) for fact in contested})

    contested_facts: list[ContestedFact] = []
    for fact in sorted(contested):
        switched: set[str] = set()
        for start, other in (
            (claimant_inputs, Party.RESPONDENT),
            (respondent_inputs, Party.CLAIMANT),
        ):
            conceded = dict(start)
            conceded[fact] = favourable_value(fact, other)
            outcomes = _outcomes_for(rules, conceded)
            reference = _outcomes_for(rules, start)
            switched |= {
                name
                for name in rules
                if name in OUTCOME_LABELS_RU
                and bool(outcomes.get(name, False)) != bool(reference.get(name, False))
            }
        contested_facts.append(
            ContestedFact(
                fact=fact,
                label_ru=FACT_LABELS_RU.get(fact, fact),
                claimant_value=favourable_value(fact, Party.CLAIMANT),
                respondent_value=favourable_value(fact, Party.RESPONDENT),
                switches=sorted(switched),
            )
        )
    contested_facts.sort(key=lambda item: (-len(item.switches), item.fact))

    notes: list[str] = []
    if not contested:
        notes.append(
            "Спорных фактов не объявлено: оба мира совпадают, и спорить не о чем. "
            "Это ответ о деле, а не отсутствие проверки."
        )
    else:
        notes.append(
            "Спор вычислен из дела: это расхождение двух допустимых толкований "
            "спорных фактов, а не сочинённое возражение."
        )
    notes.append(
        "Это не состязательный разбор пяти агентов из раздела 8.2 концепции. "
        "Здесь три роли из пяти; доктрины и калибратора нет, и они не имитируются."
    )
    return TwoWorldDebate(contested=contested_facts, conclusions=conclusions, notes_ru=notes)
