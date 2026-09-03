"""Измерение ошибки словарного извлекателя на реальных судебных актах.

## Зачем измерять то, о чём и так сказано, что оно грубое

О совпадении по словам в проекте написано, что оно «ошибается предсказуемо».
Это была оценка, а не измерение: сколько именно оно ошибается и на чём, никто
не считал. Включать извлекатель в рабочий контур с непроверенной оценкой нельзя
— юрист получил бы список подсказок, о качестве которого не знает никто, и
доверял бы им ровно настолько, насколько уверенно они выглядят.

## Корпус: чем пришлось довольствоваться

Договоров и претензий в репозитории нет. Есть 55 записей судебной практики —
реальный русский юридический текст о конкретных спорах, написанный не мною.
Документом здесь считается склейка фабулы, позиции суда, основания исхода и
дословной цитаты из акта.

Это **не тот жанр**, под который писался словарь: он собирался под договоры и
претензии. Судебный акт устроен иначе — он пересказывает обстоятельства и часто
**отрицает** их («задолженность не подтверждена», «причинная связь не
доказана»), а совпадение по словам отрицания не видит. Поэтому измеренная здесь
точность не переносится на договоры автоматически. Переносится другое: перечень
способов, которыми поиск по словам ошибается, и порядок величины.

## Разметка

Эталон лежит в `data/extraction/keyword_extractor_gold.jsonl` — по одной записи
на каждое предложение извлекателя, с решением и причиной по-русски. Вопрос
разметки один и тот же для всех: **устанавливает ли документ, что предикат
истинен применительно к спорному обязательству дела**. Ответов три: «да», «нет»
и «не определено» — последнее там, где документ о факте просто не говорит.

Разметка сделана вручную. Это её главное ограничение и одновременно
единственный доступный способ: другого источника истины для этих предикатов на
этих текстах нет. Причина записана по каждой записи, поэтому спорить с разметкой
можно предметно, а не в целом.

## Эталон как регрессия на правила

Разметка сделана до того, как в извлекатель добавили стоп-фразы, и потому годится
не только для измерения точности. Снятая правилом подсказка не исчезает из
эталона — она остаётся там со своим решением, и отчёт называет поимённо, что
именно снято. Если правило когда-нибудь снимет **верную** подсказку, это будет
видно в `wrongly_suppressed`, а не растворится в улучшившейся средней цифре.

## Что делает проверка невозможной подгонку

Эталон привязан к паре «дело — предикат». Если словарь изменится и извлекатель
начнёт предлагать что-то новое, у нового предложения эталона не окажется, и
отчёт назовёт его неразмеченным, а тест упадёт. Молча улучшить цифру,
расширив словарь, нельзя: сначала придётся разметить то, что он стал находить.
"""

import json
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.practice_base import PRACTICE_BASE_PATH
from causa.ui.document_text import ExtractedText
from causa.ui.documents import FACT_TO_PREDICATE
from causa.ui.fact_extraction import ExtractionTarget, KeywordFactExtractor

EXTRACTION_EVALUATION_VERSION = "ui-extraction-evaluation-v0"

GOLD_PATH = Path("data/extraction/keyword_extractor_gold.jsonl")

#: Русские названия способов, которыми совпадение по словам промахивается.
MISS_KINDS_RU: dict[str, str] = {
    "омоним": (
        "слово встретилось в другом значении: «встречный иск» вместо встречного "
        "требования, «решение принято» вместо принятого исполнения, «в качестве "
        "вклада» вместо качества товара"
    ),
    "факт_отвергнут_судом": (
        "слово названо верно, но стоит в отрицании: «задолженность не "
        "подтверждена», «причинная связь не доказана». Поиск по словам отрицания "
        "не видит и предлагает ровно обратное тому, что установил суд"
    ),
    "смежное_понятие": (
        "слово называет соседнее правовое понятие: ущерб как основание "
        "оспаривания сделки — не требование убытков; «вследствие просрочки "
        "кредитора» — не причинная связь убытков; налоговый штраф — не требование "
        "стороны по спорному обязательству"
    ),
    "договор_ничтожен_или_незаключён": (
        "слово указывает на договорную обязанность, которой нет: договор признан "
        "ничтожным или незаключённым, и упомянутая обязанность существует только "
        "в тексте, а не в деле"
    ),
    "факт_другого_обязательства": (
        "факт установлен, но относится к другому обязательству: задолженность по "
        "налогам в споре о новации, долг по исполнительному производству в споре "
        "о торгах"
    ),
}


class GoldLabel(BaseModel):
    """Одно размеченное предложение извлекателя."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    predicate: str
    #: «да» — документ устанавливает факт; «нет» — не устанавливает либо
    #: установлено обратное; «не определено» — документ о факте не говорит.
    verdict: str
    #: Способ промаха; у верного предложения отсутствует.
    kind: str | None = None
    reason_ru: str


class PredicateScore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    predicate: str
    proposed: int
    correct: int

    @property
    def precision(self) -> float:
        return self.correct / self.proposed if self.proposed else 0.0


class KeywordExtractionReport(BaseModel):
    """Что показал прогон словарного извлекателя на корпусе судебных актов."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = EXTRACTION_EVALUATION_VERSION
    documents: int = 0
    documents_without_any_proposal: list[str] = Field(default_factory=list)
    proposals: int = 0
    correct: int = 0
    wrong: int = 0
    undetermined: int = 0
    per_predicate: list[PredicateScore] = Field(default_factory=list)
    miss_kinds: dict[str, int] = Field(default_factory=dict)
    #: Предложения, для которых эталона нет. Непустой список — дефект набора.
    unlabelled: list[str] = Field(default_factory=list)
    #: Размеченные предложения, которых извлекатель больше не выдаёт: их сняли
    #: стоп-фразы. Список не дефект, а мера — видно, сколько шума убрано.
    suppressed_by_rules: list[str] = Field(default_factory=list)
    #: Из снятых — те, что были верны. Обязан быть пуст: правило, снимающее
    #: верную подсказку, отнимает у юриста больше, чем даёт.
    wrongly_suppressed: list[str] = Field(default_factory=list)
    recall_remedy_requested: float = 0.0
    notes_ru: list[str] = Field(default_factory=list)

    @property
    def precision(self) -> float:
        return self.correct / self.proposals if self.proposals else 0.0


def load_gold(path: Path = GOLD_PATH) -> tuple[GoldLabel, ...]:
    return tuple(
        GoldLabel.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def build_case_documents() -> list[tuple[str, ExtractedText]]:
    """Корпус: судебные акты выгрузки как документы для извлекателя.

    Склейка фиксирована здесь, а не в разметке: измерение обязано быть
    воспроизводимым от исходных данных, а не от того, что я однажды скопировал.
    """
    documents = []
    for line in PRACTICE_BASE_PATH.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        text = "\n\n".join(
            part
            for part in (
                record.get("fabula_ru", ""),
                record.get("holding_ru", ""),
                record.get("outcome_reason_ru", ""),
                record.get("quote_ru", ""),
            )
            if part
        )
        documents.append(
            (
                record["id"],
                ExtractedText(
                    document_id=f"doc:{record['id']}",
                    filename=f"{record['id']}.txt",
                    extracted=True,
                    format_ru="текст судебного акта",
                    text=text,
                    characters=len(text),
                ),
            )
        )
    return documents


def run_keyword_extraction_evaluation() -> KeywordExtractionReport:
    """Прогнать словарный извлекатель по корпусу и сверить с эталоном."""
    gold = {(item.case_id, item.predicate): item for item in load_gold()}
    targets = tuple(
        ExtractionTarget(institute="case", predicate=name) for name in FACT_TO_PREDICATE
    )
    extractor = KeywordFactExtractor()

    seen: set[tuple[str, str]] = set()
    verdicts: Counter[str] = Counter()
    per_predicate: dict[str, Counter[str]] = {}
    miss_kinds: Counter[str] = Counter()
    unlabelled: list[str] = []
    empty_documents: list[str] = []
    remedy_hits = 0

    documents = build_case_documents()
    for case_id, text in documents:
        proposals = extractor.propose(text, targets).candidates
        if not proposals:
            empty_documents.append(case_id)
        for candidate in proposals:
            key = (case_id, candidate.predicate)
            seen.add(key)
            if candidate.predicate == "remedy_requested":
                remedy_hits += 1
            label = gold.get(key)
            if label is None:
                unlabelled.append(f"{case_id}:{candidate.predicate}")
                continue
            verdicts[label.verdict] += 1
            bucket = per_predicate.setdefault(candidate.predicate, Counter())
            bucket[label.verdict] += 1
            if label.kind:
                miss_kinds[label.kind] += 1

    suppressed = sorted(gold.keys() - seen)
    wrongly = sorted(
        f"{case}:{predicate}"
        for case, predicate in suppressed
        if gold[(case, predicate)].verdict == "да"
    )
    proposals_total = sum(verdicts.values()) + len(unlabelled)
    scores = [
        PredicateScore(predicate=name, proposed=sum(counts.values()), correct=counts["да"])
        for name, counts in sorted(per_predicate.items(), key=lambda kv: -sum(kv[1].values()))
    ]
    notes = [
        "Корпус — судебные акты, а не договоры и претензии, под которые собирался "
        "словарь. Точность на договорах может отличаться; переносится не число, а "
        "перечень способов промаха.",
        "Полнота измерена по одному предикату — `remedy_requested`: в каждой записи "
        "выгрузки требование заявлено, потому что все они разрешают спор по иску. "
        "Эталона на отрицательных примерах по остальным предикатам нет, и полноту "
        "по ним измерением здесь не подменяется.",
        "Разметка сделана вручную, причина записана по каждой записи. Это её "
        "ограничение и одновременно единственный доступный источник истины.",
        "Эталон размечен до введения стоп-фраз и потому работает регрессией на "
        "них: снятая подсказка остаётся в нём с решением, и если правило снимет "
        "верную, это будет видно поимённо, а не растворится в средней цифре.",
    ]
    if unlabelled:
        notes.append(
            "Есть предложения без эталона: словарь изменился, а разметка — нет. "
            "Пока они не размечены, числа отчёта неполны."
        )
    return KeywordExtractionReport(
        documents=len(documents),
        documents_without_any_proposal=sorted(empty_documents),
        proposals=proposals_total,
        correct=verdicts["да"],
        wrong=verdicts["нет"],
        undetermined=verdicts["не определено"],
        per_predicate=scores,
        miss_kinds=dict(sorted(miss_kinds.items(), key=lambda kv: -kv[1])),
        unlabelled=sorted(unlabelled),
        suppressed_by_rules=[f"{case}:{predicate}" for case, predicate in suppressed],
        wrongly_suppressed=wrongly,
        recall_remedy_requested=remedy_hits / len(documents) if documents else 0.0,
        notes_ru=notes,
    )
