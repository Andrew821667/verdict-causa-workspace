"""Институт банкротства не вправе утверждать о пакете то, что пакет опровергает.

Выпуски 1.26.0 и 1.27.0 смоделировали статьи 213.27 и 213.28 закона 127-ФЗ, а
соседние институты продолжали писать юристу, что «пакет их не моделирует», — и
поднимали флаг по этой, уже ложной, причине. Дефект нашёлся при подготовке
выпуска 1.28.0, при чтении, а не тестом: ни один тест не сверял утверждения
институтов о пакете с самим пакетом.

Тест сверяет. Он смотрит в документацию модулей, в причины и в предупреждения,
которые институты выдают на своих наборах оценки, и запрещает предложение, где
статья главы X, смоделированная в пакете, соседствует с утверждением, что пакет
её не моделирует. Утверждения о самой модели («эта модель не разбирает»)
разрешены: институт вправе не делать того, что делает соседний. Запрещено
утверждение о пакете.
"""

import importlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Статьи главы X, которые пакет моделирует, и институт, который это делает.
#:
#: Перечень ведётся вручную и сверяется ниже со ссылками самих институтов: статья
#: не может числиться смоделированной, если её источника нет среди правовых
#: ссылок названного института.
MODELLED_CHAPTER_10_ARTICLES: dict[str, tuple[str, str]] = {
    "213.2": ("citizen_procedure", "synthetic-ru-127fz-213.2-citizen-bankruptcy-procedures-v1"),
    "213.3": ("citizen_commencement", "synthetic-ru-127fz-213.3-citizen-case-commencement-v1"),
    "213.4": ("citizen_commencement", "synthetic-ru-127fz-213.4-citizen-own-application-v1"),
    "213.5": ("citizen_commencement", "synthetic-ru-127fz-213.5-creditor-application-v1"),
    "213.6": ("citizen_procedure", "synthetic-ru-127fz-213.6-citizen-application-merits-v1"),
    "213.13": (
        "citizen_procedure",
        "synthetic-ru-127fz-213.13-restructuring-plan-requirements-v1",
    ),
    "213.27": ("citizen_ranking", "synthetic-ru-127fz-213.27-citizen-creditor-ranking-v1"),
    "213.28": (
        "citizen_release",
        "synthetic-ru-127fz-213.28-citizen-release-from-obligations-v1",
    ),
}

#: Институты, чьи тексты проверяются.
INSTITUTES = (
    "bankruptcy_claims",
    "bankruptcy_ranking",
    "bankruptcy_contest",
    "bankruptcy_setoff",
    "citizen_bankruptcy",
    "citizen_ranking",
    "citizen_release",
    "citizen_commencement",
    "citizen_procedure",
)

_ARTICLE = re.compile(r"213\.(\d+)(?![\d.])")
_PACKAGE_NEGATION = re.compile(r"пакет\w*.{0,60}?не\s+(?:смоделирован|моделирует)", re.DOTALL)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
#: Отсылка к статье, названной в предыдущем предложении. Именно так были
#: написаны две из шести устаревших фраз выпуска 1.27.0: «…это статья 213.27.
#: Эту статью пакет не моделирует» — и предложение без номера статьи
#: сторож, читающий по одному предложению, пропускал.
_ANAPHOR = re.compile(r"\b(?:эту статью|эти статьи|эта статья|его|её|их)\b", re.IGNORECASE)


def _modelled_in(sentence: str) -> set[str]:
    return {f"213.{number}" for number in _ARTICLE.findall(sentence)} & (
        MODELLED_CHAPTER_10_ARTICLES.keys()
    )


def stale_claims(text: str) -> list[str]:
    """Предложения, где смоделированная статья названа несмоделированной пакетом.

    Статья может быть названа в том же предложении или в предыдущем, если
    предложение с отрицанием отсылает к ней местоимением.
    """
    sentences = _SENTENCE_END.split(" ".join(text.split()))
    found = []
    for index, sentence in enumerate(sentences):
        if not _PACKAGE_NEGATION.search(sentence):
            continue
        if _modelled_in(sentence):
            found.append(sentence)
        elif index and _ANAPHOR.search(sentence) and _modelled_in(sentences[index - 1]):
            found.append(f"{sentences[index - 1]} {sentence}")
    return found


#: Шесть устаревших фраз выпуска 1.27.0 — дословно. Сторож обязан ловить каждую.
STALE_PHRASES_OF_RELEASE_1_27_0 = (
    "Статья 213.27 в пакете не смоделирована; модель называет её применимой и "
    "поднимает флаг юриста.",
    "Очерёдность удовлетворения требований кредиторов гражданина устанавливает закон о "
    "банкротстве, а не ГК РФ (пункт 2 статьи 25 ГК РФ): для гражданина это статья 213.27 "
    "закона 127-ФЗ. Эту статью пакет не моделирует, поэтому очерёдность здесь не "
    "определяется — называется лишь то, чем её определять.",
    "Требуется оценка юриста. Очерёдность требований гражданина (статья 213.27 закона "
    "127-ФЗ), особенности банкротства предпринимателя и банкротство крестьянского "
    "хозяйства в пакете не смоделированы: модель называет применимое правило, но не "
    "применяет его.",
    "Исключения перечисляет не эта статья, а статья 213.28 (пункты 4–6) и соседние. Их "
    "содержание пакет не моделирует, поэтому заявленное исключение снимает вывод о "
    "погашении и поднимает флаг юриста, а не подменяется догадкой.",
    "Требуется оценка юриста. Исключения из погашения требований (статья 213.28 закона) в "
    "пакете не смоделированы; распределение выручки от реализации предмета залога модель "
    "называет правилами, но не считает — денежных величин в её фактах нет.",
    "Перечень исключений из погашения требований даёт статья 213.28 закона, и пакет его "
    "не моделирует: заявленное исключение снимает вывод о погашении и поднимает флаг "
    "юриста.",
)


def _texts_of(institute: str) -> list[str]:
    module = importlib.import_module(f"causa.institutional.contracts.{institute}")
    evaluation = importlib.import_module(f"causa.institutional.contracts.{institute}_evaluation")
    texts = [module.__doc__ or "", evaluation.__doc__ or ""]
    prefix = f"SYNTHETIC_{institute.upper()}"
    cases = [
        *getattr(evaluation, f"{prefix}_BENCHMARKS"),
        *getattr(evaluation, f"{prefix}_RED_TEAM_CASES"),
    ]
    for case in cases:
        result = evaluation._evaluate(case.facts, case.id)
        texts.extend(result.reasons_ru)
        texts.extend(result.warnings_ru)
    return texts


@pytest.mark.parametrize("phrase", STALE_PHRASES_OF_RELEASE_1_27_0)
def test_the_detector_catches_every_stale_phrase_of_release_1_27_0(phrase: str) -> None:
    """Сторож проверяется на тех самых фразах, которые он должен был поймать.

    Первая редакция сторожа читала по одному предложению и пропускала две фразы
    из шести — с отсылкой местоимением к статье, названной предложением раньше.
    Её самотест был составлен так, что пропуск не показывал. Поэтому здесь
    фразы взяты дословно из кода выпуска 1.27.0 (коммит 55e319c), а не придуманы
    под сторожа; дословность сверена с этим коммитом при написании теста. Сверять
    её в самом тесте значило бы привязать его к глубине клона репозитория.
    """
    assert stale_claims(phrase), phrase


def test_the_detector_lets_true_statements_through() -> None:
    """Утверждение о самой модели и рассказ о прошлом выпуске — не дефект."""
    about_the_model = "Перечень исключений даёт статья 213.28, и эта модель его не разбирает."
    about_history = (
        "В выпуске 1.26.0 статья 213.28 пакетом не была смоделирована, и флаг поднимался."
    )
    about_an_unmodelled_article = "Статью 213.31 о мировом соглашении пакет не моделирует."
    unrelated_neighbour = (
        "Статья 213.28 называет субсидиарную ответственность. Её саму пакет не моделирует."
    )

    assert stale_claims(about_the_model) == []
    assert stale_claims(about_history) == []
    assert stale_claims(about_an_unmodelled_article) == []
    # Честный предел сторожа: местоимение может отсылать не к статье, а к
    # предмету, который статья называет, и тогда сторож срабатывает ложно.
    # Такую фразу надо писать без местоимения — так она и читается однозначнее.
    assert stale_claims(unrelated_neighbour) != []


@pytest.mark.parametrize("article", sorted(MODELLED_CHAPTER_10_ARTICLES))
def test_every_listed_article_is_really_sourced_by_its_institute(article: str) -> None:
    """Перечень смоделированных статей не может разойтись с самими институтами."""
    institute, source_id = MODELLED_CHAPTER_10_ARTICLES[article]
    module = importlib.import_module(f"causa.institutional.contracts.{institute}")
    refs = getattr(module, f"{institute.upper()}_LEGAL_SOURCE_REFS")

    assert source_id in refs, (article, institute)


@pytest.mark.parametrize("institute", INSTITUTES)
def test_no_institute_tells_the_lawyer_a_modelled_article_is_unmodelled(institute: str) -> None:
    claims = [claim for text in _texts_of(institute) for claim in stale_claims(text)]

    assert claims == [], f"{institute} утверждает о пакете неверное: {claims}"


@pytest.mark.parametrize(
    "spec", sorted(path.name for path in (ROOT / "docs").glob("*.md")), ids=str
)
def test_no_specification_tells_the_reader_a_modelled_article_is_unmodelled(spec: str) -> None:
    """То же требование к спецификациям: читатель документа — тот же юрист.

    Первый прогон сторожа по документации нашёл ещё одну такую фразу — в
    спецификации института статьи 213.27, о статье 213.28, — которую не видел
    прогон по коду.
    """
    claims = stale_claims((ROOT / "docs" / spec).read_text(encoding="utf-8"))

    assert claims == [], f"{spec} утверждает о пакете неверное: {claims}"
