"""Сверка объявленного правила с исполняемым.

## Зачем это существует

Каждый институт объявляет своё правило дважды. Один раз — списком строк
`expressions` в `build_*_constraint_set`; именно эти строки показываются юристу
как «формальная норма и constraint set». Второй раз — вызовами `solver.add()`
в `evaluate_*_constraints`; именно они считают ответ по делу.

Эти два текста никто никогда не сверял. Тестов, упоминающих `expressions`, в
проекте нет ни одного. Между тем расходятся они уже сейчас: объявлено 918
строк, исполняется 928 равенств, и совпадения по числу нет ни в одном модуле
из 88. То есть юристу показывают правило, по которому не считают.

Этот модуль отвечает на вопрос, который до сих пор никто не мог задать: **какие
именно правила разошлись и в какую сторону** — система строже, чем говорит, или
мягче.

## Почему это диагностика, а не кандидат в governance

Расхождение объявленного с исполняемым — дефект нашего кода, а не гипотеза о
праве. Гипотезу о праве утверждает юрист; «напечатанное правило не совпадает с
исполняемым» его утверждения не требует. Поэтому выход отсюда — отчёт и
падающий тест, а не запись в governance: требовать экспертного одобрения для
починки опечатки значит отложить починку навсегда.

## Почему сверка статическая

Обе стороны оказались строго регулярны, и это проверено:

* объявленные строки — 918 литералов, ни одна не собирается на лету;
* исполняемая часть до `solver.check()` не содержит **ни одного** ветвления:
  все 778 `if` в этих функциях стоят после решателя и собирают `reasons_ru`;
* формы `solver.add()`: 928 равенств вида «имя == выражение», 223 привязки
  входов и ровно одно неравенство.

Значит правило можно прочитать из исходника обеих сторон и сравнить решателем,
не запуская конвейер и не перебирая факты. Перебор здесь был бы и медленнее, и
слабее: он доказывает совпадение только на проверенных наборах, а Z3 доказывает
на всех сразу.

## Что считается расхождением

`MISSING_DECLARATION`
    Исполняется правило, которого нет в объявленном. Юристу его не покажут.

`MISSING_EXECUTION`
    Объявлено правило, которое не исполняется. Юристу покажут то, чего нет.

`DIFFERENT_RULE`
    Оба есть и не эквивалентны. Прилагается набор фактов, на котором стороны
    расходятся, — это машинное доказательство дефекта, а не подозрение.

`UNKNOWN_SYMBOL`
    Объявленное правило ссылается на переменные, которых в модели нет. Такое
    правило нельзя ни исполнить, ни проверить: юристу показывают условие,
    выраженное через то, чего система не знает.

`UNPARSABLE_DECLARATION`
    Объявленная строка не разбирается грамматикой. Такая строка не является
    правилом ни в каком смысле и обязана быть исправлена.
"""

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from z3 import And, Bool, Not, Or, Solver, sat

RULE_PARITY_VERSION = "reasoning-rule-parity-v0"

#: Узел разобранного выражения: ("var", имя) | ("not", узел) | ("and"|"or", [узлы]).
Node = tuple

_TOKEN = re.compile(r"\s*(\(|\)|==|[A-Za-z_][A-Za-z0-9_]*)")

_KEYWORDS = {"AND", "OR", "NOT"}


class ExpressionSyntaxError(ValueError):
    """Объявленная строка не разбирается грамматикой правил."""


# --- Разбор объявленной стороны ---------------------------------------------


def tokenize(text: str) -> list[str]:
    """Разбить строку правила на лексемы, не пропустив ни одного знака.

    Молчаливый пропуск непонятого символа — худшее, что может сделать разборщик
    правил: строка с опечаткой прошла бы как корректная. Поэтому всё, что не
    легло в лексему, обрывает разбор.
    """
    tokens: list[str] = []
    position = 0
    while position < len(text):
        match = _TOKEN.match(text, position)
        if match is None:
            remainder = text[position:].strip()
            if not remainder:
                break
            raise ExpressionSyntaxError(f"неразобранный остаток: «{remainder}»")
        tokens.append(match.group(1))
        position = match.end()
    return tokens


class _Parser:
    """Рекурсивный спуск по грамматике: OR ← AND ← NOT ← скобки ← имя."""

    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.position = 0

    def peek(self) -> str | None:
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def take(self) -> str:
        token = self.peek()
        if token is None:
            raise ExpressionSyntaxError("выражение оборвано")
        self.position += 1
        return token

    def parse(self) -> Node:
        node = self.disjunction()
        if self.peek() is not None:
            raise ExpressionSyntaxError(f"лишняя лексема «{self.peek()}»")
        return node

    def disjunction(self) -> Node:
        parts = [self.conjunction()]
        while self.peek() == "OR":
            self.take()
            parts.append(self.conjunction())
        return parts[0] if len(parts) == 1 else ("or", parts)

    def conjunction(self) -> Node:
        parts = [self.negation()]
        while self.peek() == "AND":
            self.take()
            parts.append(self.negation())
        return parts[0] if len(parts) == 1 else ("and", parts)

    def negation(self) -> Node:
        if self.peek() == "NOT":
            self.take()
            return ("not", self.negation())
        return self.atom()

    def atom(self) -> Node:
        token = self.take()
        if token == "(":
            node = self.disjunction()
            if self.take() != ")":
                raise ExpressionSyntaxError("не закрыта скобка")
            return node
        if token in _KEYWORDS or token in {")", "=="}:
            raise ExpressionSyntaxError(f"на месте имени стоит «{token}»")
        return ("var", token)


def parse_expression(text: str) -> Node:
    """Разобрать выражение правой части правила."""
    return _Parser(tokenize(text)).parse()


def parse_rule(line: str) -> tuple[str, Node] | None:
    """Разобрать объявленную строку. `None` — строка объявляет вход, а не правило.

    Строки без `==` — это перечисление входных фактов (так устроен
    `build_obligation_constraint_set`), и правилом они не являются.
    """
    if "==" not in line:
        name = line.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ExpressionSyntaxError(f"строка не является ни правилом, ни именем: «{line}»")
        return None
    head, _, tail = line.partition("==")
    name = head.strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ExpressionSyntaxError(f"слева от «==» не имя: «{head.strip()}»")
    return name, parse_expression(tail)


# --- Разбор исполняемой стороны ---------------------------------------------


#: Глубина раскрытия промежуточных формул. Прямолинейный код её не достигает;
#: предел стоит на случай, если кто-нибудь напишет взаимную ссылку.
_MAX_ALIAS_DEPTH = 64


def _expand_arguments(
    arguments: list[ast.AST],
    aliases: dict[str, ast.AST],
    lists: dict[str, list[ast.AST]],
    depth: int,
) -> list[Node]:
    """Раскрыть аргументы `And`/`Or`, включая распакованные списки."""
    parts: list[Node] = []
    for argument in arguments:
        if not isinstance(argument, ast.Starred):
            parts.append(_translate_call(argument, aliases, depth + 1, lists))
            continue
        inner = argument.value
        if isinstance(inner, ast.Name) and inner.id in lists:
            parts.extend(
                _translate_call(element, aliases, depth + 1, lists) for element in lists[inner.id]
            )
            continue
        if isinstance(inner, ast.ListComp):
            name = _pairwise_list(inner)
            if name is not None and name in lists:
                elements = [
                    _translate_call(element, aliases, depth + 1, lists) for element in lists[name]
                ]
                parts.extend(
                    ("and", [left, right])
                    for index, left in enumerate(elements)
                    for right in elements[index + 1 :]
                )
                continue
        raise ExpressionSyntaxError(f"непереводимое выражение: {ast.unparse(argument)}")
    return parts


def _translate_call(
    node: ast.AST,
    aliases: dict[str, ast.AST] | None = None,
    depth: int = 0,
    lists: dict[str, list[ast.AST]] | None = None,
) -> Node:
    """Перевести выражение Z3 из исходника в тот же вид, что и объявленное.

    Промежуточные формулы раскрываются на месте. Иначе `transfer_route`,
    собранная строкой выше как `Or(...)`, читалась бы как отдельная переменная,
    и сравнение сравнивало бы формулу с именем.
    """
    aliases = aliases or {}
    lists = lists or {}
    if depth > _MAX_ALIAS_DEPTH:
        raise ExpressionSyntaxError("промежуточные формулы ссылаются друг на друга по кругу")
    if isinstance(node, ast.Name):
        if node.id in aliases:
            return _translate_call(aliases[node.id], aliases, depth + 1, lists)
        return ("var", node.id)
    if isinstance(node, ast.Subscript):
        # variables["имя_факта"] либо outputs["имя_вывода"]
        index = node.slice
        if isinstance(index, ast.Constant) and isinstance(index.value, str):
            return ("var", index.value)
        raise ExpressionSyntaxError(f"непонятный индекс: {ast.unparse(node)}")
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name = node.func.id
        if name == "Not" and len(node.args) == 1:
            return ("not", _translate_call(node.args[0], aliases, depth + 1, lists))
        if name in {"And", "Or"}:
            parts = _expand_arguments(list(node.args), aliases, lists, depth)
            if not parts:
                raise ExpressionSyntaxError(f"пустое {name}: {ast.unparse(node)}")
            return (name.lower(), parts) if len(parts) > 1 else parts[0]
    raise ExpressionSyntaxError(f"непереводимое выражение: {ast.unparse(node)}")


def _pairwise_list(node: ast.ListComp) -> str | None:
    """Имя списка, если это перебор всех пар его элементов.

    Три института спрашивают «не сработали ли два основания сразу» и пишут это
    одинаково: `[And(left, right) for index, left in enumerate(paths)
    for right in paths[index + 1:]]`. Форма узкая, повторяется дословно, и
    поддержать её дешевле, чем оставить три правила непрочитанными.
    """
    if len(node.generators) != 2:
        return None
    first, second = node.generators
    if not (
        isinstance(first.iter, ast.Call)
        and isinstance(first.iter.func, ast.Name)
        and first.iter.func.id == "enumerate"
        and isinstance(first.iter.args[0], ast.Name)
    ):
        return None
    name = first.iter.args[0].id
    if not (
        isinstance(second.iter, ast.Subscript)
        and isinstance(second.iter.value, ast.Name)
        and second.iter.value.id == name
        and isinstance(second.iter.slice, ast.Slice)
    ):
        return None
    element = node.elt
    if not (
        isinstance(element, ast.Call)
        and isinstance(element.func, ast.Name)
        and element.func.id == "And"
        and len(element.args) == 2
    ):
        return None
    return name


def _lists(function: ast.FunctionDef) -> dict[str, list[ast.AST]]:
    """Списки формул: `full_paths = [...]`, раскрываемые через `Or(*full_paths)`."""
    found: dict[str, list[ast.AST]] = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target, value = node.targets[0], node.value
        if isinstance(target, ast.Name) and isinstance(value, ast.List):
            found[target.id] = list(value.elts)
    return found


def _aliases(function: ast.FunctionDef) -> dict[str, ast.AST]:
    """Промежуточные имена: и формулы, и короткие псевдонимы входов.

    Псевдоним входа (`pretrial = variables["pretrial_order_satisfied"]`) так же
    обязателен к раскрытию, как и формула: иначе сверка сравнивала бы короткое
    имя из кода с полным именем из объявления и объявляла бы расхождение там,
    где его нет.
    """
    found: dict[str, ast.AST] = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target, value = node.targets[0], node.value
        if not isinstance(target, ast.Name):
            continue
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in {"And", "Or", "Not"}
        ):
            found[target.id] = value
        elif isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
            index = value.slice
            if isinstance(index, ast.Constant) and isinstance(index.value, str):
                found[target.id] = value
    return found


def _dict_rules(function: ast.FunctionDef) -> dict[str, ast.AST]:
    """Правила, собранные словарём и добавленные циклом.

    Один модуль (купля-продажа) объявляет правила как `derived = {"имя": ...}`
    и добавляет их циклом `for name, expression in derived.items()`. Слева от
    `==` там стоит переменная цикла, поэтому без этой поддержки у института
    не находилось **ни одного** правила — и вся его объявленная часть выглядела
    неисполняемой.
    """
    loops_over: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.For):
            continue
        iterator = node.iter
        if not (
            isinstance(iterator, ast.Call)
            and isinstance(iterator.func, ast.Attribute)
            and iterator.func.attr == "items"
            and isinstance(iterator.func.value, ast.Name)
        ):
            continue
        adds = any(
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr == "add"
            for inner in ast.walk(node)
        )
        if adds:
            loops_over.add(iterator.func.value.id)

    found: dict[str, ast.AST] = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target, value = node.targets[0], node.value
        if not (isinstance(target, ast.Name) and target.id in loops_over):
            continue
        if not isinstance(value, ast.Dict):
            continue
        for key, item in zip(value.keys, value.values):
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                found[key.value] = item
    return found


def _bool_names(function: ast.FunctionDef) -> set[str]:
    """Локальные имена, объявленные как `X = Bool(...)` — это выходы правил."""
    names: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        value = node.value
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "Bool"
        ):
            names.add(target.id)
    return names


def _left_name(
    node: ast.AST,
    bool_names: set[str],
    aliases: dict[str, ast.AST] | None = None,
) -> str | None:
    """Имя выхода слева от `==`, если это выход, а не что-то другое.

    Способов записи выхода накопилось три, и каждый пропущенный даёт не пустой
    результат, а ложное обвинение:

    * отдельное имя — `x = Bool("x")`;
    * словарь — `outputs["x"]`;
    * короткое имя словарного выхода — `breach_ground = outputs["substantial_
      breach_ground_satisfied"]`, а дальше `solver.add(breach_ground == ...)`.

    Третий способ я пропустил в первой версии, и двенадцать правил расторжения
    договора выглядели ненаписанными, хотя написаны. Сверка, ошибающаяся в свою
    пользу, хуже отсутствия сверки.
    """
    aliases = aliases or {}
    if isinstance(node, ast.Name):
        if node.id in bool_names:
            return node.id
        alias = aliases.get(node.id)
        if isinstance(alias, ast.Subscript):
            index = alias.slice
            if isinstance(index, ast.Constant) and isinstance(index.value, str):
                return index.value
        return None
    if isinstance(node, ast.Subscript):
        index = node.slice
        if isinstance(index, ast.Constant) and isinstance(index.value, str):
            return index.value
    return None


def _is_input_binding(node: ast.AST) -> bool:
    """Правая часть — значение факта из входа, а не формула.

    `solver.add(x == getattr(facts, name))` и `solver.add(x == facts.x)` не
    правила, а привязка входов: на объявленной стороне им соответствуют не
    выражения, а перечисление имён фактов.
    """
    if isinstance(node, ast.Attribute):
        return True
    return (
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr"
    )


# --- Сбор по пакету ---------------------------------------------------------


class DivergenceKind(str, Enum):
    MISSING_DECLARATION = "missing_declaration"
    MISSING_EXECUTION = "missing_execution"
    DIFFERENT_RULE = "different_rule"
    UNKNOWN_SYMBOL = "unknown_symbol"
    UNPARSABLE_DECLARATION = "unparsable_declaration"
    UNTRANSLATABLE_EXECUTION = "untranslatable_execution"


KIND_LABELS_RU: dict[DivergenceKind, str] = {
    DivergenceKind.MISSING_DECLARATION: "исполняется, но не объявлено",
    DivergenceKind.MISSING_EXECUTION: "объявлено, но не исполняется",
    DivergenceKind.DIFFERENT_RULE: "объявлено и исполняется по-разному",
    DivergenceKind.UNKNOWN_SYMBOL: "объявленное ссылается на несуществующие переменные",
    DivergenceKind.UNPARSABLE_DECLARATION: "объявленная строка не разбирается",
    DivergenceKind.UNTRANSLATABLE_EXECUTION: "исполняемое выражение не переводится",
}


@dataclass(frozen=True)
class Divergence:
    """Одно расхождение между объявленным правилом и исполняемым."""

    institute: str
    output: str
    kind: DivergenceKind
    detail_ru: str = ""
    #: Набор фактов, на котором стороны расходятся. Только для DIFFERENT_RULE.
    counterexample: dict[str, bool] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.institute, self.output, self.kind.value)

    @property
    def line_ru(self) -> str:
        text = f"{self.institute} · {self.output} — {KIND_LABELS_RU[self.kind]}"
        if self.detail_ru:
            text += f": {self.detail_ru}"
        return text


@dataclass(frozen=True)
class InstituteParity:
    """Итог сверки по одному институту."""

    institute: str
    module: str
    declared_rules: int
    executed_rules: int
    matched: int
    divergences: list[Divergence] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.divergences


@dataclass(frozen=True)
class ParityReport:
    version: str = RULE_PARITY_VERSION
    institutes: list[InstituteParity] = field(default_factory=list)

    @property
    def divergences(self) -> list[Divergence]:
        return [item for institute in self.institutes for item in institute.divergences]

    @property
    def clean_institutes(self) -> list[InstituteParity]:
        return [institute for institute in self.institutes if institute.clean]

    @property
    def declared_total(self) -> int:
        return sum(institute.declared_rules for institute in self.institutes)

    @property
    def executed_total(self) -> int:
        return sum(institute.executed_rules for institute in self.institutes)


def _institute_of(name: str) -> str:
    if name.startswith("build_") and name.endswith("_constraint_set"):
        return name[len("build_") : -len("_constraint_set")]
    if name.startswith("evaluate_") and name.endswith("_constraints"):
        return name[len("evaluate_") : -len("_constraints")]
    raise ValueError(f"имя не похоже ни на объявление, ни на исполнение: {name}")


def collect_declared(tree: ast.Module) -> dict[str, tuple[dict[str, Node], list[Divergence]]]:
    """Правила, объявленные строками, по институтам одного модуля."""
    found: dict[str, tuple[dict[str, Node], list[Divergence]]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not (node.name.startswith("build_") and node.name.endswith("_constraint_set")):
            continue
        institute = _institute_of(node.name)
        rules: dict[str, Node] = {}
        problems: list[Divergence] = []
        for keyword in ast.walk(node):
            if not (isinstance(keyword, ast.keyword) and keyword.arg == "expressions"):
                continue
            if not isinstance(keyword.value, ast.List):
                continue
            for element in keyword.value.elts:
                if not (isinstance(element, ast.Constant) and isinstance(element.value, str)):
                    continue
                try:
                    parsed = parse_rule(element.value)
                except ExpressionSyntaxError as error:
                    problems.append(
                        Divergence(
                            institute=institute,
                            output=element.value.split("==")[0].strip()[:60],
                            kind=DivergenceKind.UNPARSABLE_DECLARATION,
                            detail_ru=str(error),
                        )
                    )
                    continue
                if parsed is not None:
                    rules[parsed[0]] = parsed[1]
        found[institute] = (rules, problems)
    return found


def collect_executed(tree: ast.Module) -> dict[str, tuple[dict[str, Node], list[Divergence]]]:
    """Правила, исполняемые решателем, по институтам одного модуля."""
    found: dict[str, tuple[dict[str, Node], list[Divergence]]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not (node.name.startswith("evaluate_") and node.name.endswith("_constraints")):
            continue
        institute = _institute_of(node.name)
        outputs = _bool_names(node)
        aliases = _aliases(node)
        lists = _lists(node)
        rules: dict[str, Node] = {}
        problems: list[Divergence] = []
        for name, expression in _dict_rules(node).items():
            try:
                rules[name] = _translate_call(expression, aliases, lists=lists)
            except ExpressionSyntaxError as error:
                problems.append(
                    Divergence(
                        institute=institute,
                        output=name,
                        kind=DivergenceKind.UNTRANSLATABLE_EXECUTION,
                        detail_ru=str(error),
                    )
                )
        for call in ast.walk(node):
            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "add"
                and call.args
            ):
                continue
            argument = call.args[0]
            if not (
                isinstance(argument, ast.Compare)
                and len(argument.ops) == 1
                and isinstance(argument.ops[0], ast.Eq)
            ):
                # Ограничение, не являющееся определением выхода.
                continue
            name = _left_name(argument.left, outputs, aliases)
            if name is None or _is_input_binding(argument.comparators[0]):
                continue
            try:
                rules[name] = _translate_call(argument.comparators[0], aliases, lists=lists)
            except ExpressionSyntaxError as error:
                problems.append(
                    Divergence(
                        institute=institute,
                        output=name,
                        kind=DivergenceKind.UNTRANSLATABLE_EXECUTION,
                        detail_ru=str(error),
                    )
                )
        found[institute] = (rules, problems)
    return found


# --- Сравнение --------------------------------------------------------------


def symbols_of(node: Node) -> set[str]:
    """Все имена, упомянутые в выражении."""
    if node[0] == "var":
        return {node[1]}
    if node[0] == "not":
        return symbols_of(node[1])
    return {name for part in node[1] for name in symbols_of(part)}


def _to_z3(node: Node, symbols: dict[str, object]):
    kind = node[0]
    if kind == "var":
        return symbols.setdefault(node[1], Bool(node[1]))
    if kind == "not":
        return Not(_to_z3(node[1], symbols))
    parts = [_to_z3(part, symbols) for part in node[1]]
    return And(*parts) if kind == "and" else Or(*parts)


def compile_to_z3(node: Node, symbols: dict[str, object]):
    """Собрать выражение Z3 по разобранному правилу.

    Публичная точка входа: правило стало данными, и считать по нему собирается
    не только сверка (`causa.reasoning.three_valued`).
    """
    return _to_z3(node, symbols)


def equivalent(declared: Node, executed: Node) -> dict[str, bool] | None:
    """`None` — правила совпадают. Иначе набор фактов, на котором они расходятся.

    Проверяется решателем, а не перебором: перебор доказал бы совпадение только
    на проверенных наборах, а здесь утверждение нужно для всех сразу.
    """
    symbols: dict[str, object] = {}
    solver = Solver()
    solver.add(Not(_to_z3(declared, symbols) == _to_z3(executed, symbols)))
    if solver.check() != sat:
        return None
    model = solver.model()
    return {
        name: bool(model.eval(symbol, model_completion=True))
        for name, symbol in sorted(symbols.items())
    }


def compare_institute(
    institute: str,
    module: str,
    declared: dict[str, Node],
    executed: dict[str, Node],
    problems: list[Divergence],
) -> InstituteParity:
    divergences = list(problems)
    matched = 0

    # Словарь модели — всё, что вообще упоминается исполняемой стороной: и
    # выходы, и входы. Объявленное правило, вышедшее за его пределы, выражено
    # через то, чего система не знает, и проверять его не с чем.
    known = set(executed)
    for rule in executed.values():
        known |= symbols_of(rule)

    unknown_outputs: set[str] = set()
    for output, rule in sorted(declared.items()):
        strangers = sorted(symbols_of(rule) - known)
        if not strangers:
            continue
        unknown_outputs.add(output)
        divergences.append(
            Divergence(
                institute=institute,
                output=output,
                kind=DivergenceKind.UNKNOWN_SYMBOL,
                detail_ru="в модели нет переменных: " + ", ".join(strangers),
            )
        )

    for output in sorted(set(declared) | set(executed)):
        if output in unknown_outputs:
            # Про это правило уже сказано, и сказано точнее.
            continue
        if output not in declared:
            divergences.append(
                Divergence(
                    institute=institute,
                    output=output,
                    kind=DivergenceKind.MISSING_DECLARATION,
                    detail_ru="правило считает ответ, но юристу не показывается",
                )
            )
            continue
        if output not in executed:
            divergences.append(
                Divergence(
                    institute=institute,
                    output=output,
                    kind=DivergenceKind.MISSING_EXECUTION,
                    detail_ru="правило показывается юристу, но ответ по нему не считается",
                )
            )
            continue
        counterexample = equivalent(declared[output], executed[output])
        if counterexample is None:
            matched += 1
            continue
        divergences.append(
            Divergence(
                institute=institute,
                output=output,
                kind=DivergenceKind.DIFFERENT_RULE,
                detail_ru="стороны расходятся на приведённом наборе фактов",
                counterexample=counterexample,
            )
        )
    return InstituteParity(
        institute=institute,
        module=module,
        declared_rules=len(declared),
        executed_rules=len(executed),
        matched=matched,
        divergences=divergences,
    )


def audit_rule_parity(root: Path | None = None) -> ParityReport:
    """Сверить объявленное с исполняемым во всём пакете."""
    root = root or Path(__file__).resolve().parents[1]
    institutes: list[InstituteParity] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        declared = collect_declared(tree)
        executed = collect_executed(tree)
        for institute in sorted(set(declared) | set(executed)):
            declared_rules, declared_problems = declared.get(institute, ({}, []))
            executed_rules, executed_problems = executed.get(institute, ({}, []))
            institutes.append(
                compare_institute(
                    institute=institute,
                    module=path.name,
                    declared=declared_rules,
                    executed=executed_rules,
                    problems=declared_problems + executed_problems,
                )
            )
    return ParityReport(institutes=institutes)


# --- Обратный перевод -------------------------------------------------------


def render_expression(node: Node) -> str:
    """Записать формулу грамматикой объявленных правил.

    Скобки ставятся только там, где без них меняется смысл: приоритет
    `NOT` → `AND` → `OR` тот же, что и при разборе.
    """
    kind = node[0]
    if kind == "var":
        return node[1]
    if kind == "not":
        inner = node[1]
        text = render_expression(inner)
        return f"NOT ({text})" if inner[0] in {"and", "or"} else f"NOT {text}"
    if kind == "and":
        parts = [
            f"({render_expression(part)})" if part[0] == "or" else render_expression(part)
            for part in node[1]
        ]
        return " AND ".join(parts)
    return " OR ".join(render_expression(part) for part in node[1])


def render_rule(name: str, node: Node) -> str:
    """Строка правила в том виде, в каком она объявляется."""
    return f"{name} == {render_expression(node)}"


def lost_conditions(declared: dict[str, Node], executed: dict[str, Node]) -> dict[str, list[str]]:
    """Условия, объявленные когда-то и отсутствующие в модели.

    Это единственная часть расхождения, которую нельзя закрыть механически.
    Имя, которое кто-то написал в правиле, а модель о нём не знает, — либо
    описка, либо условие, которое забыли реализовать. Второе решает юрист, и
    молча стереть такое имя, переписав объявленное по исполняемому, значит
    потерять чьё-то юридическое утверждение.
    """
    known = set(executed)
    for rule in executed.values():
        known |= symbols_of(rule)
    lost: dict[str, list[str]] = {}
    for output, rule in sorted(declared.items()):
        strangers = sorted(symbols_of(rule) - known)
        if strangers:
            lost[output] = strangers
    return lost


# --- Отчёт ------------------------------------------------------------------


def render_report_ru(report: ParityReport) -> str:
    """Отчёт по-русски: что сошлось, что нет и где именно."""
    lines: list[str] = [
        "СВЕРКА ОБЪЯВЛЕННОГО ПРАВИЛА С ИСПОЛНЯЕМЫМ",
        "",
        f"Институтов: {len(report.institutes)}; из них без расхождений: "
        f"{len(report.clean_institutes)}.",
        f"Объявлено правил: {report.declared_total}; исполняется: {report.executed_total}; "
        f"совпало дословно по смыслу: {sum(item.matched for item in report.institutes)}.",
        f"Расхождений: {len(report.divergences)}.",
        "",
        "Совпадение проверено решателем: для каждой пары правил доказано, что они "
        "дают одинаковый ответ при любых фактах, а не только при проверенных.",
        "",
    ]

    counts: dict[DivergenceKind, int] = {}
    for divergence in report.divergences:
        counts[divergence.kind] = counts.get(divergence.kind, 0) + 1
    if counts:
        lines.append("По видам:")
        for kind in DivergenceKind:
            if kind in counts:
                lines.append(f"  {counts[kind]:5d}  {KIND_LABELS_RU[kind]}")
        lines.append("")

    dirty = [item for item in report.institutes if item.divergences]
    if not dirty:
        lines.append("Расхождений нет: объявленное правило и исполняемое совпадают везде.")
        return "\n".join(lines)

    lines.append("По институтам:")
    for institute in sorted(dirty, key=lambda item: -len(item.divergences)):
        lines.append(
            f"\n{institute.institute} ({institute.module}) — "
            f"объявлено {institute.declared_rules}, исполняется {institute.executed_rules}, "
            f"совпало {institute.matched}, расхождений {len(institute.divergences)}"
        )
        for divergence in institute.divergences:
            lines.append(f"  · {divergence.output} — {KIND_LABELS_RU[divergence.kind]}")
            if divergence.detail_ru:
                lines.append(f"      {divergence.detail_ru}")
            if divergence.counterexample:
                facts = ", ".join(
                    f"{name}={'да' if value else 'нет'}"
                    for name, value in divergence.counterexample.items()
                )
                lines.append(f"      расходятся при: {facts}")
    return "\n".join(lines)


def report_payload(report: ParityReport) -> dict:
    """Отчёт в виде данных — для выгрузки и для сравнения между выпусками."""
    return {
        "version": report.version,
        "institutes_total": len(report.institutes),
        "institutes_clean": len(report.clean_institutes),
        "declared_rules": report.declared_total,
        "executed_rules": report.executed_total,
        "matched_rules": sum(item.matched for item in report.institutes),
        "divergences_total": len(report.divergences),
        "institutes": [
            {
                "institute": item.institute,
                "module": item.module,
                "declared_rules": item.declared_rules,
                "executed_rules": item.executed_rules,
                "matched": item.matched,
                "divergences": [
                    {
                        "output": divergence.output,
                        "kind": divergence.kind.value,
                        "kind_ru": KIND_LABELS_RU[divergence.kind],
                        "detail_ru": divergence.detail_ru,
                        "counterexample": divergence.counterexample,
                    }
                    for divergence in item.divergences
                ],
            }
            for item in report.institutes
        ],
    }
