"""Три значения факта и бремя доказывания.

## Корневой потолок, который здесь снимается

У факта в этой системе не было значения «неизвестно». Восемьдесят пять наборов
фактов, тысяча триста шестьдесят пять булевых полей, ни одного трёхзначного.
Значит «основание освобождения не установлено» кодировалось тем же битом, что
«основания освобождения нет», и подавалось в правило

    late_performance_issue == duty_exists AND due_date_missed
                              AND NOT valid_exception_applies

как факт **в пользу истца**. Система не могла отличить «я проверил, и этого
нет» от «я не знаю».

## Почему одного третьего значения мало

Трёхзначный факт сам по себе задачу не решает, а перекладывает: «неизвестно» на
входе даёт «зависит» на выходе, и система начнёт отвечать «зависит» по делам,
которые суд решает уверенно.

В праве «не доказано» — не факт о мире, а **правило распределения**: у кого
бремя, тот и проигрывает по этому элементу. Поэтому третье значение вводится
вместе с бременем, а не после него.

## Как это устроено

Известные факты закрепляются равенством, неизвестные остаются свободными
переменными, и по каждому выводу решателю задаются два вопроса: возможно ли
«да» и возможно ли «нет».

* возможно только «да» — вывод доказан при любом доопределении;
* возможно только «нет» — опровергнут при любом;
* возможно и то и другое — **зависит**, и тогда работает бремя: каждый
  неизвестный факт принимает значение, невыгодное той стороне, которая обязана
  была его доказать.

Правило берётся из `constraint_set.expressions` — из объявленного текста, а не
из второй рукописной копии на Python. Так можно с тех пор, как сверка доказала,
что объявленное и исполняемое совпадают во всех 88 институтах: правило впервые
стало данными, и это первый его потребитель.

## Границы

Модель здесь одна — обязательство, тринадцать фактов. Остальные восемьдесят
четыре не тронуты намеренно: сначала устройство доказывается на модели, чьи
выводы читают линия вывода, вердикт, очередь пробелов и проект документа, и
только потом переносится вширь. Обратный порядок означал бы переписать тысячу
триста полей, не проверив замысел.
"""

from enum import Enum
from itertools import product

from pydantic import BaseModel, ConfigDict, Field
from z3 import Bool, Not, Solver, sat

from causa.institutional.contracts.legal_operators import FACT_LABELS_RU, OUTCOME_LABELS_RU
from causa.reasoning.formal_checks import ConstraintSet, ObligationFactSet
from causa.reasoning.rule_parity import compile_to_z3, parse_rule

THREE_VALUED_VERSION = "reasoning-three-valued-v0"


class Party(str, Enum):
    CLAIMANT = "claimant"
    RESPONDENT = "respondent"


PARTY_LABELS_RU = {
    Party.CLAIMANT: "истец",
    Party.RESPONDENT: "ответчик",
}


class BurdenRule(BaseModel):
    """Кто несёт риск того, что факт останется недоказанным."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fact: str
    borne_by: Party
    #: Значение, которое факт принимает, оставшись недоказанным.
    unproven_value: bool
    basis_ru: str

    @property
    def line_ru(self) -> str:
        label = FACT_LABELS_RU.get(self.fact, self.fact)
        return (
            f"{label}: доказывает {PARTY_LABELS_RU[self.borne_by]}; "
            f"недоказанное считается «{'да' if self.unproven_value else 'нет'}» "
            f"({self.basis_ru})"
        )


#: Распределение бремени по фактам обязательства.
#:
#: Таблица ведётся вручную и с основанием на каждую строку: это утверждение о
#: праве, а не свойство модели данных. Общее правило — каждая сторона доказывает
#: обстоятельства, на которые ссылается (статья 65 АПК РФ, статья 56 ГПК РФ);
#: изъятия из него названы прямо.
BURDEN_OF_PROOF: tuple[BurdenRule, ...] = (
    BurdenRule(
        fact="duty_exists",
        borne_by=Party.CLAIMANT,
        unproven_value=False,
        basis_ru="кредитор доказывает существование обязательства, на котором строит требование",
    ),
    BurdenRule(
        fact="due_date_missed",
        borne_by=Party.CLAIMANT,
        unproven_value=False,
        basis_ru="кредитор доказывает наступление и пропуск срока исполнения",
    ),
    BurdenRule(
        fact="valid_exception_applies",
        borne_by=Party.RESPONDENT,
        unproven_value=False,
        basis_ru="отсутствие вины доказывает должник, пункт 2 статьи 401 ГК РФ",
    ),
    BurdenRule(
        fact="performance_completed",
        borne_by=Party.RESPONDENT,
        unproven_value=False,
        basis_ru="доказательство исполнения лежит на должнике, статья 408 ГК РФ",
    ),
    BurdenRule(
        fact="performance_nonconforming",
        borne_by=Party.CLAIMANT,
        unproven_value=False,
        basis_ru="недостатки исполнения доказывает тот, кто на них ссылается",
    ),
    BurdenRule(
        fact="payment_duty_exists",
        borne_by=Party.CLAIMANT,
        unproven_value=False,
        basis_ru="кредитор доказывает основание денежного обязательства",
    ),
    BurdenRule(
        fact="payment_due",
        borne_by=Party.CLAIMANT,
        unproven_value=False,
        basis_ru="кредитор доказывает наступление срока платежа",
    ),
    BurdenRule(
        fact="payment_missed",
        borne_by=Party.RESPONDENT,
        unproven_value=True,
        basis_ru=(
            "оплату доказывает должник, статья 408 ГК РФ; недоказанная оплата "
            "означает, что платёж не произведён"
        ),
    ),
    BurdenRule(
        fact="payment_defense_applies",
        borne_by=Party.RESPONDENT,
        unproven_value=False,
        basis_ru="возражение против требования доказывает тот, кто его заявляет",
    ),
    BurdenRule(
        fact="loss_claimed",
        borne_by=Party.CLAIMANT,
        unproven_value=False,
        basis_ru="убытки заявляет и доказывает кредитор, статья 393 ГК РФ",
    ),
    BurdenRule(
        fact="causation_established",
        borne_by=Party.CLAIMANT,
        unproven_value=False,
        basis_ru="причинную связь между нарушением и убытками доказывает кредитор",
    ),
    BurdenRule(
        fact="remedy_requested",
        borne_by=Party.CLAIMANT,
        unproven_value=False,
        basis_ru="способ защиты выбирает и заявляет кредитор",
    ),
    BurdenRule(
        fact="limitation_period_expired",
        borne_by=Party.RESPONDENT,
        unproven_value=False,
        basis_ru=(
            "исковая давность применяется только по заявлению стороны в споре, "
            "пункт 2 статьи 199 ГК РФ"
        ),
    ),
)

BURDEN_BY_FACT: dict[str, BurdenRule] = {rule.fact: rule for rule in BURDEN_OF_PROOF}


class OutcomeStatus(str, Enum):
    #: Вывод верен при любом доопределении неизвестных фактов.
    PROVEN = "proven"
    #: Вывод неверен при любом доопределении.
    REFUTED = "refuted"
    #: Вывод зависит от того, чем окажутся неизвестные факты.
    DEPENDS = "depends"


STATUS_LABELS_RU = {
    OutcomeStatus.PROVEN: "да при любом доопределении неизвестного",
    OutcomeStatus.REFUTED: "нет при любом доопределении неизвестного",
    OutcomeStatus.DEPENDS: "зависит от неизвестного",
}


class OutcomeVerdict(BaseModel):
    """Что известно о выводе, когда часть фактов не установлена."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: str
    label_ru: str
    status: OutcomeStatus
    status_ru: str
    #: Значение после применения бремени доказывания.
    resolved: bool
    #: Неизвестные факты, от которых вывод зависит. Пусто, если не зависит.
    driven_by: list[str] = Field(default_factory=list)
    #: Почему вывод разрешён именно так. Пусто, если он не зависел ни от чего.
    resolution_ru: str = ""


class ThreeValuedEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = THREE_VALUED_VERSION
    unknown_facts: list[str] = Field(default_factory=list)
    outcomes: list[OutcomeVerdict] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)

    def outcome(self, name: str) -> OutcomeVerdict:
        return next(item for item in self.outcomes if item.outcome == name)

    @property
    def depends_on_anything(self) -> bool:
        return any(item.status is OutcomeStatus.DEPENDS for item in self.outcomes)


class UnknownFactError(KeyError):
    """Неизвестным объявлен факт, которого в модели обязательства нет."""


def _rules(constraint_set: ConstraintSet) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for line in constraint_set.expressions:
        rule = parse_rule(line)
        if rule is not None:
            parsed[rule[0]] = rule[1]
    return parsed


def _evaluate_node(node, values: dict[str, bool]) -> bool:
    """Посчитать формулу на готовых значениях, без решателя.

    Решатель нужен там, где ответ требуется сразу по всем доопределениям.
    Когда значения известны, он избыточен, а перебор доопределений на нём
    обошёлся бы в тысячи вызовов.
    """
    kind = node[0]
    if kind == "var":
        return bool(values.get(node[1], False))
    if kind == "not":
        return not _evaluate_node(node[1], values)
    if kind == "and":
        return all(_evaluate_node(part, values) for part in node[1])
    return any(_evaluate_node(part, values) for part in node[1])


def _outcomes_for(rules: dict[str, object], values: dict[str, bool]) -> dict[str, bool]:
    """Довести значения до всех выводов, разрешая ссылки между правилами."""
    computed = dict(values)
    remaining = dict(rules)
    while remaining:
        progressed = False
        for name, node in list(remaining.items()):
            missing = _symbols(node) - set(computed)
            if missing:
                continue
            computed[name] = _evaluate_node(node, computed)
            del remaining[name]
            progressed = True
        if not progressed:
            # Правила ссылаются друг на друга по кругу: считать нечего.
            break
    return computed


def _symbols(node) -> set[str]:
    if node[0] == "var":
        return {node[1]}
    if node[0] == "not":
        return _symbols(node[1])
    return {name for part in node[1] for name in _symbols(part)}


def evaluate_with_unknowns(
    constraint_set: ConstraintSet,
    facts: ObligationFactSet,
    unknown: set[str] | None = None,
) -> ThreeValuedEvaluation:
    """Оценить выводы, оставив неустановленные факты неопределёнными.

    `unknown` — факты, о которых по делу ничего не установлено. Значения этих
    полей в `facts` не читаются: смысл третьего значения в том, что его нет.
    """
    unknown = set(unknown or ())
    declared = set(type(facts).model_fields)
    strangers = sorted(unknown - declared)
    if strangers:
        raise UnknownFactError("В модели обязательства нет фактов: " + ", ".join(strangers))
    without_burden = sorted(unknown - set(BURDEN_BY_FACT))
    if without_burden:
        raise UnknownFactError(
            "Для этих фактов не записано бремя доказывания: " + ", ".join(without_burden)
        )

    rules = _rules(constraint_set)
    known = {name: bool(getattr(facts, name)) for name in declared if name not in unknown}

    # Статус по всем доопределениям сразу — работа решателя: перебор доказал бы
    # утверждение только на переборанных наборах.
    symbols: dict[str, object] = {name: Bool(name) for name in declared}
    for output in rules:
        symbols.setdefault(output, Bool(output))

    def solver_with_rules() -> Solver:
        solver = Solver()
        for name, value in known.items():
            solver.add(symbols[name] == value)
        for output, node in rules.items():
            solver.add(symbols[output] == compile_to_z3(node, symbols))
        return solver

    # Разрешение по бремени: каждый неизвестный факт принимает значение,
    # невыгодное стороне, которая обязана была его доказать.
    burdened = dict(known)
    burdened.update({name: BURDEN_BY_FACT[name].unproven_value for name in unknown})
    resolved_values = _outcomes_for(rules, burdened)

    outcomes: list[OutcomeVerdict] = []
    for name, label_ru in OUTCOME_LABELS_RU.items():
        if name not in rules:
            continue
        can_be_true = solver_with_rules()
        can_be_true.add(symbols[name])
        can_be_false = solver_with_rules()
        can_be_false.add(Not(symbols[name]))
        true_possible = can_be_true.check() == sat
        false_possible = can_be_false.check() == sat

        if true_possible and false_possible:
            status = OutcomeStatus.DEPENDS
            driven_by = _drivers(rules, known, unknown, name)
        elif true_possible:
            status = OutcomeStatus.PROVEN
            driven_by = []
        else:
            status = OutcomeStatus.REFUTED
            driven_by = []

        resolved = bool(resolved_values.get(name, False))
        resolution = ""
        if status is OutcomeStatus.DEPENDS:
            bearers = sorted({PARTY_LABELS_RU[BURDEN_BY_FACT[fact].borne_by] for fact in driven_by})
            resolution = (
                "Недоказанное толкуется против того, кто обязан был доказать: "
                + ", ".join(bearers)
                + f". Поэтому вывод принят как «{'да' if resolved else 'нет'}»."
            )
        outcomes.append(
            OutcomeVerdict(
                outcome=name,
                label_ru=label_ru,
                status=status,
                status_ru=STATUS_LABELS_RU[status],
                resolved=resolved,
                driven_by=driven_by,
                resolution_ru=resolution,
            )
        )

    notes: list[str] = []
    if unknown:
        notes.append(
            "Неустановленными объявлены факты: "
            + ", ".join(FACT_LABELS_RU.get(name, name) for name in sorted(unknown))
            + ". «Не установлено» здесь означает именно это, а не «установлено обратное»."
        )
    else:
        notes.append("Неустановленных фактов по делу нет: третье значение ни на что не влияет.")
    return ThreeValuedEvaluation(unknown_facts=sorted(unknown), outcomes=outcomes, notes_ru=notes)


#: Предел перебора доопределений при поиске решающих фактов.
#:
#: Неизвестных в реальном деле единицы; предел стоит на случай, когда их
#: объявят десятками, и тогда честнее сказать «зависит от всех», чем считать час.
_MAX_COMPLETIONS = 12


def _drivers(
    rules: dict[str, object],
    known: dict[str, bool],
    unknown: set[str],
    outcome: str,
) -> list[str]:
    """Какие из неизвестных фактов действительно решают судьбу вывода.

    Неизвестных может быть много, а зависеть вывод — от одного. Называть все
    значит требовать доказывания того, что ничего не изменит.
    """
    ordered = sorted(unknown)
    if len(ordered) > _MAX_COMPLETIONS:
        return ordered
    drivers: set[str] = set()
    for combination in product([False, True], repeat=len(ordered)):
        values = dict(known)
        values.update(dict(zip(ordered, combination)))
        base = _outcomes_for(rules, values).get(outcome, False)
        for index, name in enumerate(ordered):
            flipped = dict(values)
            flipped[name] = not values[name]
            if _outcomes_for(rules, flipped).get(outcome, False) != base:
                drivers.add(name)
    return sorted(drivers)
