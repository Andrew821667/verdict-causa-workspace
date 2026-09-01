"""Карта дела о банкротстве: одна структура на дело, а не на институт.

## Зачем нужен отдельный модуль

Четыре института банкротства (`bankruptcy_claims`, `bankruptcy_ranking`,
`bankruptcy_contest`, `bankruptcy_setoff`) разбирают одно требование или одну
сделку за раз — так и должно быть, каждый отвечает на свой узкий правовой
вопрос. Но реальное дело о банкротстве — это не одно требование, а обычно
десятки: разные кредиторы, разные основания, разные сделки под ударом,
раскиданные по разным очередям и трекам. Понять дело целиком, глядя на
`BankruptcyRankingEvaluation` одного кредитора, нельзя — нужна сводная
картина.

Этот модуль не вводит ни одного нового предиката и не принимает ни одного
правового решения. Он строго оркестрирует уже проверенные функции
`evaluate_*` четырёх институтов над множеством требований и сделок одного
дела и раскладывает результат в одну структуру, пригодную для таблицы,
временной шкалы и графа сделок. Каждая запись карты хранит исходный
`*Evaluation` целиком — сводная метка (`status_label_ru`) добавлена только
для отображения, поверх него, а не вместо него.

## Не институт

У модуля нет `FactSet`, `ConstraintSet` и решателя Z3: он не разбирает право,
а раскладывает уже разобранное. Поэтому он не входит ни в один из четырёх
списков `CONTRACTS_PACKAGE_MANIFEST` (`bootstrap_schema_refs` и соседние) —
институтом в смысле пакета он не является.

## Откуда берутся факты

Здесь описано только то, как карта выглядит. Откуда в ней факты — вопрос
`bankruptcy_case_assembly.py`: он вводит контракт данных на дело целиком и
собирает карту, прогоняя каждый блок через настоящие
`map_reviewed_*_evidence` четырёх институтов. Собрать карту в обход проверки
всё ещё возможно — конструкторы записей ниже принимают готовый `*Evaluation`,
и это нужно тестам, — но для дела так делать нельзя: утверждение о факте без
ссылки на материал и без проверившего неотличимо от догадки.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.bankruptcy_claims import BankruptcyClaimsEvaluation
from causa.institutional.contracts.bankruptcy_contest import BankruptcyContestEvaluation
from causa.institutional.contracts.bankruptcy_ranking import BankruptcyRankingEvaluation
from causa.institutional.contracts.bankruptcy_setoff import BankruptcySetoffEvaluation

BANKRUPTCY_CASE_MAP_VERSION = "contracts-bankruptcy-case-map-v0"


class CaseParty(BaseModel):
    """Участник дела: должник, кредитор или управляющий."""

    id: str
    name_ru: str
    role_ru: str


class CaseTimelineEvent(BaseModel):
    """Одна процедурная веха дела — то, от чего институты банкротства считают окна."""

    date: str
    label_ru: str
    legal_reference_ru: str = ""


class ClaimMapEntry(BaseModel):
    """Одно требование одного кредитора, с полным выводом claims и ranking."""

    id: str
    creditor_id: str
    description_ru: str
    amount: float | None = None
    currency: str = "RUB"
    claims_evaluation: BankruptcyClaimsEvaluation
    ranking_evaluation: BankruptcyRankingEvaluation
    status_label_ru: str
    requires_human_assessment: bool


class TransactionMapEntry(BaseModel):
    """Одна оспариваемая сделка, с полным выводом contest.

    `resulting_claim_id`, если задан, — ссылка на запись в `claims`: после
    признания сделки недействительной у контрагента может возникнуть
    субординированное требование (абзац пункта 4 статьи 134 127-ФЗ). Модуль
    эту связь не выводит сам — она задаётся тем же способом, каким собрана
    вся карта: из факта дела, а не из предположения.
    """

    id: str
    counterparty_id: str
    description_ru: str
    contest_evaluation: BankruptcyContestEvaluation
    status_label_ru: str
    resulting_claim_id: str | None = None


class SetoffMapEntry(BaseModel):
    """Один заявленный зачёт или нетто-обязательство, с полным выводом setoff."""

    id: str
    creditor_id: str
    description_ru: str
    setoff_evaluation: BankruptcySetoffEvaluation
    status_label_ru: str


class BankruptcyCaseMap(BaseModel):
    """Сводная карта дела: стороны, вехи, требования, сделки, зачёты."""

    version: str = BANKRUPTCY_CASE_MAP_VERSION
    case_id: str
    debtor: CaseParty
    parties: list[CaseParty] = Field(default_factory=list)
    timeline: list[CaseTimelineEvent] = Field(default_factory=list)
    claims: list[ClaimMapEntry] = Field(default_factory=list)
    transactions: list[TransactionMapEntry] = Field(default_factory=list)
    setoffs: list[SetoffMapEntry] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


def _current_payment_tier_ru(ranking_evaluation: BankruptcyRankingEvaluation) -> str:
    """Очередь текущего платежа по пункту 2 статьи 134 — словами.

    Пятая очередь названа своим номером, а не «прочее»: закон её так и вводит
    («иные текущие платежи»), и подменять номер словом значило бы прятать от
    читателя, что требование в очереди стоит.
    """
    if ranking_evaluation.current_payment_ahead_of_all_current:
        return "вперёд всех текущих: снижение угрозы катастрофы (п. 1.1 ст. 134 127-ФЗ)"
    if ranking_evaluation.current_payment_first_tier:
        return "первая очередь (расходы по делу и вознаграждение управляющего)"
    if ranking_evaluation.current_payment_second_tier:
        return "вторая очередь (оплата труда после принятия заявления)"
    if ranking_evaluation.current_payment_third_tier:
        return "третья очередь (привлечённые управляющим лица)"
    if ranking_evaluation.current_payment_fourth_tier:
        return "четвёртая очередь (эксплуатационные платежи)"
    if ranking_evaluation.current_payment_fifth_tier:
        return "пятая очередь (иные текущие платежи)"
    return (
        "очередь не определена: требование названо текущим в модели статьи 5, "
        "но ни к одной очереди пункта 2 статьи 134 не отнесено"
    )


def summarize_claim_status_ru(
    claims_evaluation: BankruptcyClaimsEvaluation,
    ranking_evaluation: BankruptcyRankingEvaluation,
) -> str:
    """Одна строка вместо двух Evaluation — только для отображения в таблице.

    Порядок проверки — не произвольный: текущий статус (claims) исключает
    вопрос о реестровой очереди вообще (пункт 2 статьи 5 127-ФЗ — текущие
    платежи не включаются в реестр), поэтому проверяется первым. Но «текущее»
    — ещё не ответ: у текущих платежей своя очерёдность, пункт 2 статьи 134, и
    называть её надо так же точно, как реестровую. Дальше — особые треки
    ranking в порядке их именования в самом абзаце пункта 4 статьи 134:
    первая очередь, вторая, залог, субординация, последняя очередь, третья.
    """
    if claims_evaluation.claim_is_current:
        return "текущее требование, " + _current_payment_tier_ru(ranking_evaluation)
    if ranking_evaluation.excess_executive_severance_after_third_tier:
        return "за третьей очередью реестра: пособие руководителя сверх минимума (п. 2.1 ст. 134)"
    if ranking_evaluation.first_tier:
        return "реестровое, первая очередь (вред жизни/здоровью)"
    if ranking_evaluation.second_tier:
        return "реестровое, вторая очередь (зарплата, авторское вознаграждение)"
    if ranking_evaluation.satisfied_from_pledge_proceeds:
        return "реестровое, залоговое (ст. 138 127-ФЗ)"
    if ranking_evaluation.subordinated_after_third_tier:
        return "реестровое, субординировано (после третьей очереди)"
    if ranking_evaluation.satisfied_last_after_all_other_creditors:
        return "реестровое, облигации без срока погашения (последним)"
    if ranking_evaluation.third_tier:
        return "реестровое, третья очередь"
    return "требует проверки: очередь не определена"


def summarize_transaction_status_ru(contest_evaluation: BankruptcyContestEvaluation) -> str:
    """Одна строка вместо BankruptcyContestEvaluation — только для отображения."""
    if contest_evaluation.voidable_as_unequal_consideration:
        return "оспорена: неравноценное исполнение (п. 1 ст. 61.2 127-ФЗ)"
    if contest_evaluation.voidable_as_harm_to_creditors:
        return "оспорена: вред кредиторам (п. 2 ст. 61.2 127-ФЗ)"
    if contest_evaluation.voidable_as_preference_short_window:
        return "оспорена: предпочтение, короткое окно (п. 1-2 ст. 61.3 127-ФЗ)"
    if contest_evaluation.voidable_as_preference_six_month_window:
        return "оспорена: предпочтение, шесть месяцев (п. 3 ст. 61.3 127-ФЗ)"
    return "основание оспаривания не подтверждено"


def summarize_setoff_status_ru(setoff_evaluation: BankruptcySetoffEvaluation) -> str:
    """Одна строка вместо BankruptcySetoffEvaluation — только для отображения."""
    if setoff_evaluation.setoff_prohibited:
        return "зачёт запрещён: нарушает очерёдность (абз. 6 п. 1 ст. 63 127-ФЗ)"
    if setoff_evaluation.setoff_permitted_as_priority_neutral:
        return "зачёт допустим: очерёдность не нарушена"
    if setoff_evaluation.netting_permitted_by_financial_contract_exception:
        return "нетто-обязательство допустимо (исключение ст. 4.1 127-ФЗ)"
    return "зачёт или нетто-обязательство не заявлены"


def build_claim_map_entry(
    *,
    entry_id: str,
    creditor_id: str,
    description_ru: str,
    claims_evaluation: BankruptcyClaimsEvaluation,
    ranking_evaluation: BankruptcyRankingEvaluation,
    amount: float | None = None,
    currency: str = "RUB",
) -> ClaimMapEntry:
    return ClaimMapEntry(
        id=entry_id,
        creditor_id=creditor_id,
        description_ru=description_ru,
        amount=amount,
        currency=currency,
        claims_evaluation=claims_evaluation,
        ranking_evaluation=ranking_evaluation,
        status_label_ru=summarize_claim_status_ru(claims_evaluation, ranking_evaluation),
        requires_human_assessment=(
            claims_evaluation.requires_human_bankruptcy_claims_assessment
            or ranking_evaluation.requires_human_bankruptcy_ranking_assessment
        ),
    )


def build_transaction_map_entry(
    *,
    entry_id: str,
    counterparty_id: str,
    description_ru: str,
    contest_evaluation: BankruptcyContestEvaluation,
    resulting_claim_id: str | None = None,
) -> TransactionMapEntry:
    return TransactionMapEntry(
        id=entry_id,
        counterparty_id=counterparty_id,
        description_ru=description_ru,
        contest_evaluation=contest_evaluation,
        status_label_ru=summarize_transaction_status_ru(contest_evaluation),
        resulting_claim_id=resulting_claim_id,
    )


def build_setoff_map_entry(
    *,
    entry_id: str,
    creditor_id: str,
    description_ru: str,
    setoff_evaluation: BankruptcySetoffEvaluation,
) -> SetoffMapEntry:
    return SetoffMapEntry(
        id=entry_id,
        creditor_id=creditor_id,
        description_ru=description_ru,
        setoff_evaluation=setoff_evaluation,
        status_label_ru=summarize_setoff_status_ru(setoff_evaluation),
    )
