"""Дословный источник обязан нести текст нормы, а не аппарат вокруг неё.

`metadata["text_verbatim"] = True` — обещание: здесь лежит текст закона, а не
пересказ. Проверка 215 таких источников показала, что обещание нарушалось
молча: вместе с текстом статей приехал редакционный аппарат КонсультантПлюс —
блоки «Путеводитель по судебной практике» со списком вопросов и подписи
гиперссылок «(см. текст в предыдущей редакции)», 16,6% всех абзацев.

Опасность не в объёме, а в неразличимости: юрист, открывший источник статьи
492 ГК, читал «- Признается ли розничной куплей-продажей приобретение
юрлицами товаров для собственных нужд» на том месте, где должен начинаться
текст статьи. Вопрос коммерческого справочника выглядел нормой.

Эти тесты — сторож на возврат аппарата при следующей выгрузке.
"""

import json
from pathlib import Path

from causa.institutional.contracts.synthetic_sources import SYNTHETIC_CONTRACT_SOURCES

ROOT = Path(__file__).resolve().parents[1]

#: Формы, доказанно не несущие правового содержания.
GUIDE_HEADER = "Путеводитель по "
LINK_LABEL = "(см. текст в предыдущей редакции)"


def _verbatim_sources():
    return [s for s in SYNTHETIC_CONTRACT_SOURCES if s.metadata.get("text_verbatim") is True]


def _law_article_texts():
    path = ROOT / "data/laws/127fz_articles.jsonl"
    return [json.loads(line)["text_ru"] for line in path.open(encoding="utf-8")]


def test_verbatim_sources_carry_no_guide_blocks() -> None:
    """«Путеводитель по судебной практике» — продукт справочника, а не норма."""
    offenders = [s.id for s in _verbatim_sources() if GUIDE_HEADER in s.text]

    assert offenders == [], offenders


def test_verbatim_sources_carry_no_dangling_hyperlink_labels() -> None:
    """Подпись гиперссылки в отрыве от гиперссылки не значит ничего."""
    offenders = [s.id for s in _verbatim_sources() if LINK_LABEL in s.text]

    assert offenders == [], offenders


def test_verbatim_sources_have_no_orphan_bullet_paragraphs() -> None:
    """Абзац-пункт «- ...» встречался только внутри блока Путеводителя.

    Блоки сняты, поэтому таких абзацев не должно остаться вовсе. Если новая
    выгрузка принесёт пункт списка, он либо часть нормы — и тогда проверку
    нужно осознанно ослабить, — либо снова аппарат.
    """
    offenders = [
        s.id for s in _verbatim_sources() if any(p.startswith("- ") for p in s.text.split("\n\n"))
    ]

    assert offenders == [], offenders


def test_law_export_is_clean_of_the_same_apparatus() -> None:
    """Чистить надо и выгрузку: иначе следующая пересадка вернёт аппарат."""
    texts = _law_article_texts()

    assert texts, "выгрузка 127-ФЗ пуста"
    assert not [t for t in texts if GUIDE_HEADER in t or LINK_LABEL in t]
    assert not [t for t in texts if any(p.startswith("- ") for p in t.split("\n\n"))]


def test_editorial_notes_are_kept_on_purpose() -> None:
    """Блоки «КонсультантПлюс: примечание.» оставлены сознательно.

    Обрамление у них редакционное, но содержание правовое: нормы, признанные
    не соответствующими Конституции РФ, переходные положения, отсылки к
    постановлениям КС РФ. Молчаливое удаление стоило бы этой информации.
    Тест фиксирует решение, чтобы «оставлено» не превратилось со временем в
    «не заметили»: примечания обязаны сохраниться и не остаться без тела.
    """
    with_notes = [s for s in _verbatim_sources() if "КонсультантПлюс: примечание" in s.text]

    assert len(with_notes) >= 40, len(with_notes)
    for source in with_notes:
        paragraphs = source.text.split("\n\n")
        for index, paragraph in enumerate(paragraphs):
            if paragraph.startswith("КонсультантПлюс: примечание"):
                assert index + 1 < len(paragraphs), source.id
                assert paragraphs[index + 1].strip(), source.id


def test_no_verbatim_source_lost_its_text() -> None:
    """Чистка не должна оставлять источник пустым или почти пустым."""
    for source in _verbatim_sources():
        assert len(source.text.strip()) > 200, source.id
