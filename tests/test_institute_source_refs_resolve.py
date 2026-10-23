"""Каждая объявленная институтом ссылка на источник обязана разрешаться.

## Откуда взялась проверка

Институт зачёта в банкротстве ссылался на статью 4.1 127-ФЗ в комментарии и в
предупреждении — и честно писал, что текста этой статьи в пакете нет, а признак
принимается как внешний факт. Так и было: статья лежала в выгрузке
`data/laws/127fz_articles.jsonl`, но источником пакета не стала, и ни один тест
этого не видел. Ссылки в `*_LEGAL_SOURCE_REFS` проверялись поимённо в тестах
своих институтов; ссылка, которой в наборе вовсе нет, не проверялась никем.

Проверка ниже закрывает именно эту слепоту и смотрит в два места, потому что
ссылки объявляются двумя способами:

* **константой модуля** `*_LEGAL_SOURCE_REFS` — так делают четыре института
  банкротства и институт ответственности управляющих лиц, и именно там жила дыра;
* **блоком доказательств** демонстрационного запроса — так делают остальные, и их
  ссылки проходят проверку источников в самом конвейере.

Отсутствующий источник — не мелочь оформления: модель, ссылающаяся в пустоту,
непроверяема ровно в той части, которой ссылается.
"""

import importlib
import pkgutil

import pytest

from causa.institutional import contracts as contracts_package
from causa.institutional.contracts.synthetic_sources import SYNTHETIC_CONTRACT_SOURCES

#: Идентификаторы всех зарегистрированных источников пакета.
REGISTERED = {source.id for source in SYNTHETIC_CONTRACT_SOURCES}


def _declared_refs() -> dict[str, tuple[str, ...]]:
    """Все константы `*_LEGAL_SOURCE_REFS` пакета договорного права."""
    found: dict[str, tuple[str, ...]] = {}
    for module_info in pkgutil.iter_modules(contracts_package.__path__):
        module = importlib.import_module(f"causa.institutional.contracts.{module_info.name}")
        for name in dir(module):
            if not name.endswith("_LEGAL_SOURCE_REFS"):
                continue
            value = getattr(module, name)
            if isinstance(value, tuple | list) and all(isinstance(item, str) for item in value):
                found[f"{module_info.name}.{name}"] = tuple(value)
    return found


DECLARED = _declared_refs()


def test_the_package_declares_source_refs_at_all() -> None:
    """Пустой перечень означал бы, что проверка ничего не проверяет.

    Констант тридцать четыре, и это не недосмотр: модульной константой ссылки
    объявляют институты банкротства, институт ответственности управляющих лиц,
    институт понятия договора, институт банкротства гражданина, институт
    очерёдности его требований и их наборы оценки — одна и та же константа видна
    и в самом институте, и в его наборе оценки, и там, где он проведён в
    конвейер. У остальных институтов ссылки приходят блоком доказательств, и их
    проверяет тест ниже.
    """
    assert len(DECLARED) == 34, sorted(DECLARED)


def test_every_ref_of_the_demo_request_resolves_too() -> None:
    """Девяносто девять блоков доказательств — вторая половина той же проверки."""
    from causa.institutional.contracts.synthetic_reviewed_analysis import (
        build_synthetic_supply_analysis_request,
    )

    request = build_synthetic_supply_analysis_request()
    dangling: dict[str, list[str]] = {}
    blocks = 0
    for field in type(request).model_fields:
        refs = getattr(getattr(request, field), "legal_source_refs", None)
        if not refs:
            continue
        blocks += 1
        missing = [ref for ref in refs if ref not in REGISTERED]
        if missing:
            dangling[field] = missing

    assert blocks == 99, blocks
    assert dangling == {}, dangling


@pytest.mark.parametrize("where", sorted(DECLARED))
def test_every_declared_ref_resolves_to_a_registered_source(where: str) -> None:
    """Ссылка в пустоту делает непроверяемой ту часть модели, которой она есть."""
    missing = [ref for ref in DECLARED[where] if ref not in REGISTERED]

    assert missing == [], f"{where} ссылается на незарегистрированные источники: {missing}"


def test_article_4_1_of_the_bankruptcy_law_is_sourced() -> None:
    """Регрессия на найденный случай, поимённо.

    Общая проверка выше поймала бы его снова, но запись поимённо говорит, что
    именно было сломано, — иначе причина правки теряется в истории.
    """
    from causa.institutional.contracts.bankruptcy_setoff import (
        BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS,
    )
    from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source

    ref = "synthetic-ru-127fz-4.1-financial-contract-netting-v1"
    assert ref in BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS

    source = get_synthetic_contract_source(ref)
    assert source.metadata["text_verbatim"] is True
    assert source.text.startswith("Статья 4.1.")
    # Та самая отсылка абзаца шестого пункта 1 статьи 63, ради которой статья и
    # понадобилась: режим финансовых договоров и нетто-обязательства.
    assert "финансовы" in source.text
    assert len(source.text) > 5000
