"""Предложение фактов по документу: шов для модели и ворота проверки юристом.

## Зачем понадобился отдельный модуль

Стенд умеет доставать текст из файла и находить в нём места по словарю русских
слов ([`document_text`](document_text.py)). Дальше оператор читает найденное и
сам утверждает факт ([`documents.apply_closure`](documents.py)). Это честно, но
не масштабируется: словарь ведётся руками и покрывает двенадцать предикатов
блока дела, тогда как предикатов у институтов около полутора тысяч.

В настоящей эксплуатации разбирать документ будет языковая модель. Здесь она не
вызывается ни разу — в этом репозитории нет ключа и вызывать его нельзя, — но
место, куда она подключается, должно быть построено заранее и с воротами, а не
дописано потом вокруг уже работающего кода.

## Что здесь есть и чего здесь нет

Есть **предложение** факта: `FactCandidate`. Он несёт предикат, предлагаемое
значение, дословную цитату из документа, её положение в тексте, того, кто
предложил, и почему. Он не является фактом и не может им стать сам по себе.

Нет пути из `FactCandidate` в запрос анализа. Такого пути нет намеренно, и его
отсутствие проверяется тестом. Единственная дверь в проверенные факты дела —
`documents.apply_closure`, и она принимает `GapClosure` оператора. Чтобы
предложение туда попало, юрист обязан его подтвердить:

1. назвать себя (`reviewer_id`);
2. назвать значение сам — оно может отличаться от предложенного;
3. пройти сверку цитаты: та обязана дословно находиться в тексте документа.

Третья проверка — не формальность. Она ловит два разных случая одним способом:
модель, сочинившую цитату, которой в документе нет, и документ, подменённый
после разбора. Ни то, ни другое не должно доходить до анализа молча.

## Почему подтверждение не «галочка согласен»

Потому что подтверждение записывается как утверждение юриста, а не как согласие
с моделью. В `ConfirmedFact` хранятся оба значения — предложенное и принятое, —
и расхождение видно. Юрист, поправивший модель, оставляет след ровно такой же
прочности, как юрист, с ней согласившийся.

## Два извлекателя

`KeywordFactExtractor` работает без модели вообще: он переносит сюда словарь
`FACT_KEYWORDS_RU` и предлагает предикат там, где слово нашлось. Уверенность у
него не вычисляется, а объявлена низкой: совпадение по словам ошибается
предсказуемо, и слово «неустойка» в оглавлении договора ничего не
устанавливает.

`LanguageModelFactExtractor` — шов. Без переданного клиента он отказывается
работать вслух: `ExtractorNotConfiguredError` вместо пустого списка. Пустой
список неотличим от «модель ничего не нашла», а это разные вещи.
"""

from enum import Enum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causa.ui.document_text import FACT_KEYWORDS_RU, QUOTE_RADIUS, ExtractedText
from causa.ui.documents import DERIVED_FACTS_RU, FACT_TO_PREDICATE, ClosureKind, GapClosure

FACT_EXTRACTION_VERSION = "ui-fact-extraction-v0"

#: Оговорка, сопровождающая любой набор предложений.
#:
#: Она обязательна и не настраивается: набор предложений, показанный без неё,
#: читается как разбор документа, а разбора здесь нет.
PROPOSAL_CAVEAT_RU = (
    "Это предложения, а не установленные обстоятельства. Факт утверждает юрист, "
    "прочитав документ; предложение лишь показывает, где смотреть."
)

#: Уверенность совпадения по словам. Объявлена, а не вычислена.
#:
#: Вычислять её было бы нечем: частота слова в документе ничего не говорит о
#: том, устанавливает ли оно обстоятельство. Число здесь означает одно — «низкая
#: и одинаковая», чтобы порядок предложений не выглядел содержательным.
KEYWORD_CONFIDENCE = 0.2


class ExtractorKind(str, Enum):
    #: Совпадение по словарю русских слов. Работает без ключа и без модели.
    KEYWORDS = "keywords"
    #: Языковая модель. Подключается ключом в эксплуатации.
    LANGUAGE_MODEL = "language_model"


class ExtractionTarget(BaseModel):
    """Предикат, по которому спрашивают документ."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    #: Институт; `case` — блок фактов самого дела.
    institute: str
    predicate: str
    label_ru: str = ""


class FactCandidate(BaseModel):
    """Предложение факта. Фактом не является и в анализ сам не попадает."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    institute: str
    predicate: str
    proposed_value: bool
    #: Дословный кусок текста документа. Сверяется при подтверждении.
    quote_ru: str = Field(min_length=1)
    position: int = Field(ge=0)
    extractor: ExtractorKind
    extractor_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale_ru: str = ""


class ExtractionResult(BaseModel):
    """Что один извлекатель предложил по одному документу."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = FACT_EXTRACTION_VERSION
    document_id: str
    extractor: ExtractorKind
    extractor_id: str
    candidates: tuple[FactCandidate, ...] = ()
    notes_ru: tuple[str, ...] = ()

    @model_validator(mode="after")
    def keep_the_caveat(self) -> "ExtractionResult":
        if PROPOSAL_CAVEAT_RU not in self.notes_ru:
            raise ValueError(
                "Набор предложений обязан нести оговорку о том, что это предложения, "
                "а не установленные обстоятельства."
            )
        for candidate in self.candidates:
            if candidate.document_id != self.document_id:
                raise ValueError(
                    f"Предложение по документу {candidate.document_id} попало в набор "
                    f"по документу {self.document_id}."
                )
        return self


class ConfirmedFact(BaseModel):
    """Предложение, которое юрист проверил и утвердил своим именем."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    institute: str
    predicate: str
    #: Значение, которое утверждает юрист. Может отличаться от предложенного.
    value: bool
    proposed_value: bool
    quote_ru: str
    reviewer_id: str
    extractor: ExtractorKind
    extractor_id: str
    #: Замечание юриста; обязательно, когда он поправил предложение.
    reviewer_note_ru: str = ""

    @property
    def differs_from_proposal(self) -> bool:
        return self.value != self.proposed_value

    @property
    def line_ru(self) -> str:
        verdict = "да" if self.value else "нет"
        if not self.differs_from_proposal:
            return f"{self.predicate} = {verdict} (подтверждено: {self.reviewer_id})"
        proposed = "да" if self.proposed_value else "нет"
        return (
            f"{self.predicate} = {verdict} (предложено {proposed}, исправлено: {self.reviewer_id})"
        )


class ExtractorNotConfiguredError(RuntimeError):
    """Извлекатель вызван без того, что ему нужно для работы."""


class UnverifiedQuoteError(ValueError):
    """Цитата предложения не найдена в тексте документа дословно."""


class UnreviewedCandidateError(ValueError):
    """Предложение пытались провести в дело без проверившего."""


class FactExtractor(Protocol):
    """Что обязан уметь извлекатель, чтобы его можно было подключить.

    Протокол намеренно узкий: на входе текст документа и перечень предикатов, о
    которых спрашивают, на выходе — предложения. Ни запроса анализа, ни
    проверенных фактов дела извлекатель не видит и изменить не может.
    """

    kind: ExtractorKind
    id: str

    def propose(
        self, text: ExtractedText, targets: tuple[ExtractionTarget, ...]
    ) -> ExtractionResult: ...


def _quote(text: str, position: int, length: int) -> str:
    start = max(0, position - QUOTE_RADIUS)
    end = min(len(text), position + length + QUOTE_RADIUS)
    return ("… " if start else "") + text[start:end].strip() + (" …" if end < len(text) else "")


class KeywordFactExtractor:
    """Совпадение по словарю русских слов. Ни ключа, ни модели не требует.

    Предлагает только `True`: слово в документе может указывать на то, что
    обстоятельство есть, и никогда — на то, что его нет. Отсутствие слова
    отсутствия обстоятельства не доказывает, и предлагать `False` значило бы
    выдавать молчание документа за его содержание.
    """

    kind = ExtractorKind.KEYWORDS
    id = "keyword-extractor-v0"

    def propose(
        self, text: ExtractedText, targets: tuple[ExtractionTarget, ...]
    ) -> ExtractionResult:
        if not text.extracted:
            return ExtractionResult(
                document_id=text.document_id,
                extractor=self.kind,
                extractor_id=self.id,
                notes_ru=(
                    PROPOSAL_CAVEAT_RU,
                    f"Текст документа достать не удалось: {text.note_ru}",
                ),
            )
        lowered = text.text.lower()
        candidates: list[FactCandidate] = []
        skipped: list[str] = []
        for target in targets:
            words = FACT_KEYWORDS_RU.get(target.predicate)
            if words is None:
                skipped.append(target.predicate)
                continue
            for word in words:
                position = lowered.find(word.lower())
                if position < 0:
                    continue
                candidates.append(
                    FactCandidate(
                        document_id=text.document_id,
                        institute=target.institute,
                        predicate=target.predicate,
                        proposed_value=True,
                        quote_ru=_quote(text.text, position, len(word)),
                        position=position,
                        extractor=self.kind,
                        extractor_id=self.id,
                        confidence=KEYWORD_CONFIDENCE,
                        rationale_ru=f"В документе найдено слово «{word}».",
                    )
                )
                break
        notes = [PROPOSAL_CAVEAT_RU]
        if skipped:
            # Молчать о непокрытых предикатах нельзя: их отсутствие в ответе
            # неотличимо от «в документе ничего не нашлось».
            notes.append(
                "Словаря нет для предикатов: "
                + ", ".join(sorted(set(skipped)))
                + ". Совпадение по словам ведётся вручную и покрывает лишь часть "
                "предикатов; в эксплуатации остальное разбирает языковая модель."
            )
        return ExtractionResult(
            document_id=text.document_id,
            extractor=self.kind,
            extractor_id=self.id,
            candidates=tuple(candidates),
            notes_ru=tuple(notes),
        )


class LanguageModelFactExtractor:
    """Шов для языковой модели: сюда подключается ключ в эксплуатации.

    Клиент передаётся снаружи и обязан уметь одно: по тексту документа и
    перечню предикатов вернуть предложения. Ни в этом репозитории, ни в тестах
    клиента нет, и без него извлекатель отказывается работать вслух.

    Отказ, а не пустой список, — существенная часть замысла. Пустой список
    неотличим от «модель прочитала документ и ничего не нашла», а это ровно тот
    вид молчания, который в юридической системе стоит дороже всего: оператор
    решил бы, что вопрос закрыт.
    """

    kind = ExtractorKind.LANGUAGE_MODEL

    def __init__(self, client=None, *, extractor_id: str = "language-model-extractor-v0") -> None:
        self._client = client
        self.id = extractor_id

    def propose(
        self, text: ExtractedText, targets: tuple[ExtractionTarget, ...]
    ) -> ExtractionResult:
        if self._client is None:
            raise ExtractorNotConfiguredError(
                "Языковая модель не подключена: ключ и клиент задаются в эксплуатации, "
                "а этот репозиторий модель не вызывает. Пустой ответ вместо отказа "
                "означал бы, что документ прочитан и в нём ничего нет."
            )
        proposals = self._client.propose(text=text, targets=targets)
        return ExtractionResult(
            document_id=text.document_id,
            extractor=self.kind,
            extractor_id=self.id,
            candidates=tuple(proposals),
            notes_ru=(PROPOSAL_CAVEAT_RU,),
        )


def confirm_candidate(
    *,
    candidate: FactCandidate,
    text: ExtractedText,
    reviewer_id: str,
    value: bool,
    reviewer_note_ru: str = "",
) -> ConfirmedFact:
    """Подтвердить предложение именем юриста и сверить цитату с документом.

    Значение принимает юрист, а не извлекатель: параметр `value` обязателен и
    задаётся явно. Согласие и исправление проходят одной дверью, поэтому
    поправить модель не дороже, чем с ней согласиться.
    """
    if not reviewer_id.strip():
        raise UnreviewedCandidateError(
            "Предложение нельзя провести в дело без проверившего: утверждение о факте "
            "без имени неотличимо от догадки."
        )
    if reviewer_id.strip() == candidate.extractor_id:
        raise UnreviewedCandidateError(
            "Проверяющим назван сам извлекатель. Проверка, которую делает тот же, кто "
            "предложил, проверкой не является."
        )
    if candidate.document_id != text.document_id:
        raise UnverifiedQuoteError(
            f"Предложение относится к документу {candidate.document_id}, "
            f"а сверяется с текстом документа {text.document_id}."
        )
    if not _quote_is_in(candidate.quote_ru, text.text):
        raise UnverifiedQuoteError(
            "Цитата предложения не найдена в тексте документа дословно. Так выглядят "
            "два разных случая: сочинённая цитата и подменённый после разбора "
            "документ. Оба до анализа доходить не должны."
        )
    if value != candidate.proposed_value and not reviewer_note_ru.strip():
        raise UnreviewedCandidateError(
            "Юрист поправил предложение, не сказав почему. Исправление без причины "
            "теряется: в деле останется значение, а основание — нет."
        )
    return ConfirmedFact(
        document_id=candidate.document_id,
        institute=candidate.institute,
        predicate=candidate.predicate,
        value=value,
        proposed_value=candidate.proposed_value,
        quote_ru=candidate.quote_ru,
        reviewer_id=reviewer_id.strip(),
        extractor=candidate.extractor,
        extractor_id=candidate.extractor_id,
        reviewer_note_ru=reviewer_note_ru.strip(),
    )


def _quote_is_in(quote: str, text: str) -> bool:
    """Цитата вырезана из текста с многоточиями по краям — их снимаем."""
    core = quote.strip()
    if core.startswith("… "):
        core = core[2:]
    if core.endswith(" …"):
        core = core[:-2]
    return core.strip() in text


def closure_from_confirmed(
    *,
    gap_id: str,
    document_id: str,
    confirmed: tuple[ConfirmedFact, ...],
    statement_ru: str,
) -> GapClosure:
    """Собрать закрытие пробела из подтверждённых фактов блока дела.

    Единственный выход отсюда в анализ, и он проходит через ту же дверь, что и
    ручное закрытие пробела: `documents.apply_closure`. Отдельного пути для
    предложений нет и быть не должно — иначе рядом с проверяемой дверью
    появилась бы вторая, непроверяемая.
    """
    if not confirmed:
        raise UnreviewedCandidateError("Закрытие пробела не содержит ни одного факта.")
    if not statement_ru.strip():
        raise UnreviewedCandidateError(
            "Закрытие пробела без утверждения оператора своими словами: в деле должно "
            "остаться то, что он утверждает, а не только значение предиката."
        )
    foreign = sorted({item.document_id for item in confirmed} - {document_id})
    if foreign:
        raise ValueError(
            "Подтверждённые факты ссылаются на другие документы: " + ", ".join(foreign)
        )
    outside = sorted({item.institute for item in confirmed} - {"case"})
    if outside:
        # Закрытие пробела меняет блок фактов дела. Предложения по институтам
        # существуют, но провести их сюда значило бы записать факт одного
        # контракта данных в другой.
        raise ValueError(
            "Через закрытие пробела проводятся только факты блока дела; здесь есть "
            "факты институтов: " + ", ".join(outside)
        )
    derived = sorted({item.predicate for item in confirmed} & DERIVED_FACTS_RU.keys())
    if derived:
        raise ValueError(
            "Эти факты не утверждаются, а вычисляются: "
            + "; ".join(f"{name} — {DERIVED_FACTS_RU[name]}" for name in derived)
        )
    unknown = sorted({item.predicate for item in confirmed} - FACT_TO_PREDICATE.keys())
    if unknown:
        raise ValueError("Предикаты вне блока фактов дела: " + ", ".join(unknown))
    conflicting = {
        predicate
        for predicate in {item.predicate for item in confirmed}
        if len({item.value for item in confirmed if item.predicate == predicate}) > 1
    }
    if conflicting:
        raise ValueError(
            "По одному предикату подтверждены разные значения: "
            + ", ".join(sorted(conflicting))
            + ". Выбирать между ними система не станет."
        )
    return GapClosure(
        gap_id=gap_id,
        document_id=document_id,
        kind=ClosureKind.ASSERTED_FACT,
        fact_updates={item.predicate: item.value for item in confirmed},
        statement_ru=statement_ru.strip(),
    )
