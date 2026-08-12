"""Человекочитаемые подписи к идентификаторам источников.

## Зачем

Идентификатор `synthetic-ru-gk438-443-acceptance-model-v1` точен и бесполезен
для юриста. В списке из двадцати четырёх таких строк не видно ничего, кроме
того, что строк двадцать четыре. Здесь идентификатор превращается в «ГК РФ,
статьи 438–443», а сам идентификатор никуда не девается: он остаётся в данных
и показывается рядом.

## Границы приёма

Это разбор соглашения об именовании, а не знание о праве. Правило, которое не
сработало, возвращает идентификатор как есть — **никогда** не догадку. Тест
проверяет и это: неизвестный идентификатор обязан пройти насквозь.

Соглашение синтетическое, и в промышленной выгрузке идентификаторы будут
другими. Поэтому подпись — украшение поверх данных, а не их замена: интерфейс
обязан уметь показать источник и без подписи.
"""

import re

from pydantic import BaseModel, ConfigDict

from causa.ui.institute_titles import INSTITUTE_TITLES_RU

LABELS_VERSION = "ui-source-labels-v0"


class SourceLabel(BaseModel):
    """Идентификатор источника и то, как его читать."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    #: Короткая подпись для списка. Равна идентификатору, если правило не нашлось.
    label_ru: str
    #: Откуда это: закон, разъяснение, договор, материалы дела.
    kind_ru: str
    #: Ложь означает, что подпись — это сам идентификатор.
    recognised: bool = True


_KIND_LAW = "закон"
_KIND_GUIDANCE = "разъяснение высшей инстанции"
_KIND_CONTRACT = "условие договора"
_KIND_CASE = "материалы дела"
_KIND_UNKNOWN = "источник"

# Материалы дела: `synthetic-case-<дело>-<институт>-evidence`.
_CASE_EVIDENCE = re.compile(r"^synthetic-case-[a-z0-9-]+?-([a-z-]+)-evidence$")

# Норма ГК: `synthetic-ru-gk432-...` либо диапазон `synthetic-ru-gk438-443-...`.
_GK_ARTICLE = re.compile(r"^synthetic-ru-gk(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?-")

# Разъяснение: `synthetic-ru-plenum49-...`.
_PLENUM = re.compile(r"^synthetic-ru-plenum(\d+)-")

# Договорное условие: `synthetic-ru-contract-<о чём>-vN` либо без версии.
_CONTRACT_TERM = re.compile(r"^synthetic-ru-contract-(.+?)(?:-v\d+)?$")

#: О чём договорное условие. Ведётся явно: догадываться по slug нельзя.
_CONTRACT_TERM_RU: dict[str, str] = {
    "supply-delivery-duty": "обязанность поставки",
    "supply-delivery-term": "срок поставки",
}

#: Институты в идентификаторах материалов дела пишутся через дефис.
_INSTITUTE_BY_SLUG = {name.replace("_", "-"): name for name in INSTITUTE_TITLES_RU}

#: Наборы фактов, чей slug не совпадает ни с одним институтом. Ведутся явно:
#: догадка по окончанию идентификатора здесь ошибётся молча.
_CASE_EVIDENCE_RU: dict[str, str] = {
    "reviewed": "Факты обязательства: срок, исполнение, оплата",
    "special-supply": "Факты поставки: приёмка, недопоставка, отказ",
}


def _articles_ru(first: str, last: str | None) -> str:
    if last is None:
        return f"ГК РФ, статья {first}"
    return f"ГК РФ, статьи {first}–{last}"


def source_label(source_id: str) -> SourceLabel:
    """Превратить идентификатор источника в подпись, ничего не выдумывая."""
    match = _CASE_EVIDENCE.match(source_id)
    if match:
        slug = match.group(1)
        institute = _INSTITUTE_BY_SLUG.get(slug)
        if institute is not None:
            return SourceLabel(
                id=source_id,
                label_ru=INSTITUTE_TITLES_RU[institute],
                kind_ru=_KIND_CASE,
            )
        named = _CASE_EVIDENCE_RU.get(slug)
        if named is not None:
            return SourceLabel(id=source_id, label_ru=named, kind_ru=_KIND_CASE)
        # Институт не опознан — подпись остаётся идентификатором, а не
        # приблизительным пересказом его конца.
        return SourceLabel(id=source_id, label_ru=source_id, kind_ru=_KIND_CASE, recognised=False)

    match = _GK_ARTICLE.match(source_id)
    if match:
        return SourceLabel(
            id=source_id,
            label_ru=_articles_ru(match.group(1), match.group(2)),
            kind_ru=_KIND_LAW,
        )

    match = _PLENUM.match(source_id)
    if match:
        return SourceLabel(
            id=source_id,
            label_ru=f"Постановление Пленума ВС РФ № {match.group(1)}",
            kind_ru=_KIND_GUIDANCE,
        )

    match = _CONTRACT_TERM.match(source_id)
    if match:
        subject = _CONTRACT_TERM_RU.get(match.group(1))
        if subject is not None:
            return SourceLabel(
                id=source_id,
                label_ru=f"Условие договора: {subject}",
                kind_ru=_KIND_CONTRACT,
            )
        return SourceLabel(
            id=source_id, label_ru=source_id, kind_ru=_KIND_CONTRACT, recognised=False
        )

    return SourceLabel(id=source_id, label_ru=source_id, kind_ru=_KIND_UNKNOWN, recognised=False)


def source_labels(source_ids: list[str]) -> list[SourceLabel]:
    return [source_label(source_id) for source_id in source_ids]
