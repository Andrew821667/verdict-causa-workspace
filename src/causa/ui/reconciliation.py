"""Согласование зависимых фактов: одно утверждение оператора на все институты.

## Откуда взялась задача

Оператор закрывает пробел документом — и получает отказ: слой сверки видит, что
тот же факт по-другому описан в других институтах. Отказ правильный, потому что
иначе решателю пришлось бы молча выбрать одну из двух версий. Но и оставлять
оператора перед списком из восьми расхождений без выхода нельзя: он утверждал
**один** факт, а не восемь разных.

## Что делает согласование

Приводит зависимые факты рецензента к тому, что следует из вывода модели, —
именно к тому, что предлагает сама ошибка сверки первым вариантом. Ключ
расхождения указывает, в каком наборе фактов и какой предикат исправить;
исправление получает тот же документ в `source_refs`, что и исходное
утверждение.

Три свойства, без которых это было бы тихой правкой данных:

1. **Только по команде.** Без явного согласия оператора закрытие пробела
   по-прежнему отвергается с разбором.
2. **Со списком.** Возвращается перечень того, что изменено, на русском.
3. **Не для всего.** Расхождения, которые нельзя привести в согласие
   механически, названы отдельно и останавливают согласование целиком.

## Почему согласуемо не всё

Часть сверок сравнивает не факт рецензента с выводом модели, а **два вывода**
или два факта разных институтов. Там «привести в согласие» означало бы выбрать
версию — ровно то, что запрещено. Такие ключи перечислены в
`UNRECONCILABLE_RU` с причиной, и тест не даёт оставить ключ без записи ни в
одном из трёх списков.

## Третий класс: цель называет само дело

Обычно ключ сверки указывает на постоянную пару «набор фактов, предикат». Но
сверка доставки сообщения устроена иначе: какой именно предикат исправлять,
зависит от роли сообщения, которую назвал переводчик фабулы. Один и тот же ключ
ведёт то в поставку, то в расторжение, то в обеспечение.

Записать такой ключ постоянной парой значило бы соврать, а объявить
несогласуемым — тоже: он согласуем совершенно механически, просто цель берётся
из дела. Поэтому у него свой список `ROLE_DEPENDENT_FACTS`, где записано, откуда
берётся цель.

Часть ролей называет предикат от противного («не уведомлён»): значение `True`
там значит отсутствие доставки. Согласование пишет в такой предикат не вывод
модели напрямую, а его отрицание — резолвер цели сообщает полярность вместе с
институтом и предикатом.
"""

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.fact_consistency import (
    FACT_CONSISTENCY_VOCABULARY,
    FactConsistencyMismatch,
)
from causa.institutional.contracts.messages import MESSAGE_ROLE_PREDICATES, MessageRole
from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisRequest
from causa.ui.documents import UploadedDocument

RECONCILIATION_VERSION = "ui-fact-reconciliation-v0"

#: Ключ сверки → набор фактов дела и предикат, который в нём надо исправить.
#:
#: Список ведётся вручную и обязан ломаться при появлении новой сверки: молча
#: пропущенный ключ означал бы, что согласование где-то не сработает без
#: объяснения.
RECONCILABLE_FACTS: dict[str, tuple[str, str]] = {
    "dynamics_breach_status": ("obligation_dynamics_evidence", "obligation_breached"),
    "dynamics_obligation_status": ("obligation_dynamics_evidence", "obligation_exists"),
    "dynamics_performance_status": ("obligation_dynamics_evidence", "performance_rendered"),
    "dynamics_proper_performance": (
        "obligation_dynamics_evidence",
        "performance_accepted_as_proper",
    ),
    "invalidity_transaction_status": ("invalidity_evidence", "transaction_concluded"),
    "liability_breach_fact": ("liability_evidence", "breach_established"),
    "remedies_breach_status": ("performance_remedies_evidence", "breach_established"),
    "remedies_causation": ("performance_remedies_evidence", "causation_proven"),
    "remedies_loss_claim": ("performance_remedies_evidence", "loss_claimed"),
    "remedies_monetary_delay": ("performance_remedies_evidence", "monetary_delay"),
    "remedies_obligation_status": ("performance_remedies_evidence", "obligation_exists"),
    "remedies_tender_status": ("performance_remedies_evidence", "performance_tendered"),
    "sale_causation": ("sale_evidence", "causation_proven"),
    "sale_contract_status": ("sale_evidence", "contract_concluded"),
    "sale_delay_status": ("sale_evidence", "delivery_late"),
    "sale_loss_claim": ("sale_evidence", "loss_claimed"),
    "sale_payment_due": ("sale_evidence", "payment_due"),
    "sale_termination_status": ("sale_evidence", "contract_terminated"),
    "sale_transfer_status": ("sale_evidence", "goods_transfer_completed"),
    "security_breach_status": ("security_evidence", "main_obligation_breached"),
    "security_invalidity_status": ("security_evidence", "main_obligation_invalid"),
    "security_main_obligation_status": ("security_evidence", "main_obligation_exists"),
    "supply_causation": ("supply_evidence", "causation_proven"),
    "supply_contract_status": ("supply_evidence", "contract_concluded"),
    "supply_delay_status": ("supply_evidence", "delivery_late"),
    "supply_delivery_status": ("supply_evidence", "delivery_completed"),
    "supply_loss_claim": ("supply_evidence", "loss_claimed"),
    "supply_payment_due": ("supply_evidence", "payment_due"),
    "supply_termination_status": ("supply_evidence", "contract_terminated"),
    "termination_contract_status": ("termination_evidence", "contract_formed"),
    "termination_substantial_breach": ("termination_evidence", "substantial_breach_proven"),
}

_TWO_CONCLUSIONS = (
    "сверка сравнивает два вывода моделей, а не факт рецензента с выводом: "
    "привести их «в согласие» можно только выбрав версию, а этого система не делает"
)
_COMPOSITE = (
    "сверяемое значение собрано из нескольких фактов, и какой из них исправлять — "
    "решение юриста, а не механическая подстановка"
)
_BOTH_REVIEWER = (
    "обе стороны сверки — факты рецензента из разных институтов; система не "
    "решает, какой из них верен"
)

#: Ключи, цель которых называет само дело, и откуда она берётся.
#:
#: Согласование здесь такое же механическое, как и по постоянной паре, — меняется
#: лишь то, что предикат ищется не в таблице, а в данных дела.
ROLE_DEPENDENT_FACTS: dict[str, str] = {
    "message_delivery_agreement": (
        "предикат доставки называет роль сообщения, объявленная в доказательствах "
        "по статье 165.1: она указывает институт и его предикат"
    ),
}


#: Ключи, которые согласовать механически нельзя, и почему.
UNRECONCILABLE_RU: dict[str, str] = {
    "contractual_duty": _COMPOSITE,
    "sale_breach_status": _TWO_CONCLUSIONS,
    "supply_breach_status": _TWO_CONCLUSIONS,
    "sale_refusal_termination": _TWO_CONCLUSIONS,
    "supply_refusal_termination": _TWO_CONCLUSIONS,
    "sale_supply_qualification": _TWO_CONCLUSIONS,
    "temporal_effect_conclusion_moment": _TWO_CONCLUSIONS,
    "sale_nonconformity": _COMPOSITE,
    "supply_nonconformity": _COMPOSITE,
}
for _key in FACT_CONSISTENCY_VOCABULARY:
    if _key.startswith("sale_supply_pair:"):
        UNRECONCILABLE_RU[_key] = _BOTH_REVIEWER


class FactAlignment(BaseModel):
    """Один зависимый факт, приведённый в согласие."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    evidence_field: str
    predicate: str
    before: bool
    after: bool
    fact_ru: str

    @property
    def line_ru(self) -> str:
        return f"{self.fact_ru}: {'да' if self.before else 'нет'} → {'да' if self.after else 'нет'}"


class UnreconcilableMismatchError(ValueError):
    """Среди расхождений есть такие, которые нельзя согласовать механически."""

    def __init__(self, keys: list[str]) -> None:
        self.keys = keys
        super().__init__(
            "Эти расхождения нельзя согласовать автоматически: "
            + "; ".join(
                f"{key} — {UNRECONCILABLE_RU.get(key, 'причина не записана')}" for key in keys
            )
        )


def _target(key: str, request: ReviewedContractAnalysisRequest) -> tuple[str, str, bool]:
    """Куда и в какой полярности писать согласованное значение.

    Третий элемент — `negated`: цель из постоянной пары всегда `False`, а цель
    из дела берёт полярность предиката у самой роли. Предикат от противного
    («не уведомлён») получает не вывод модели напрямую, а его отрицание.
    """
    if key not in ROLE_DEPENDENT_FACTS:
        field, predicate = RECONCILABLE_FACTS[key]
        return field, predicate, False
    role = request.messages_evidence.message_role
    if role is MessageRole.OTHER:
        raise KeyError(
            "Сверка доставки сообщения не могла сработать без роли: согласовывать нечего."
        )
    target = MESSAGE_ROLE_PREDICATES[role]
    return f"{target.institute}_evidence", target.predicate, target.negated


def reconcile(
    request: ReviewedContractAnalysisRequest,
    mismatches: list[FactConsistencyMismatch],
    document: UploadedDocument | None = None,
) -> tuple[ReviewedContractAnalysisRequest, list[FactAlignment], list[str]]:
    """Привести зависимые факты к тому, что следует из выводов моделей.

    Возвращает изменённый запрос, список согласованного и ключи, которые
    согласовать механически нельзя. Последние **не** отменяют проход: часть из
    них исчезает сама, когда согласован факт, из которого они выведены. Если
    же согласовывать больше нечего, а они остались, решение принимает
    вызывающий — здесь эта развилка не прячется.
    """
    unknown = [
        mismatch.key
        for mismatch in mismatches
        if mismatch.key not in RECONCILABLE_FACTS
        and mismatch.key not in ROLE_DEPENDENT_FACTS
        and mismatch.key not in UNRECONCILABLE_RU
    ]
    if unknown:
        raise KeyError("Сверки без записи о согласовании: " + ", ".join(sorted(set(unknown))))
    blocked = sorted({mismatch.key for mismatch in mismatches if mismatch.key in UNRECONCILABLE_RU})

    updates: dict[str, dict[str, bool]] = {}
    alignments: list[FactAlignment] = []
    for mismatch in mismatches:
        if mismatch.key in UNRECONCILABLE_RU:
            # Такие расхождения часто исчезают сами, когда согласован факт, из
            # которого они выведены. Поэтому они не останавливают проход, а
            # возвращаются вызывающему: решение принимает он.
            continue
        field, predicate, negated = _target(mismatch.key, request)
        value = not mismatch.expected if negated else mismatch.expected
        updates.setdefault(field, {})[predicate] = value
        alignments.append(
            FactAlignment(
                key=mismatch.key,
                evidence_field=field,
                predicate=predicate,
                before=mismatch.actual,
                after=mismatch.expected,
                fact_ru=mismatch.fact_ru,
            )
        )

    changed: dict[str, object] = {}
    for field, wanted in updates.items():
        evidence = getattr(request, field)
        assertions = tuple(
            assertion
            if assertion.predicate.value not in wanted
            else assertion.model_copy(
                update={
                    "value": wanted[assertion.predicate.value],
                    "source_refs": tuple(
                        {*assertion.source_refs, *([document.id] if document else [])}
                    ),
                }
            )
            for assertion in evidence.assertions
        )
        changed[field] = evidence.model_copy(update={"assertions": assertions})
    return request.model_copy(update=changed), alignments, blocked


class ReconciliationReport(BaseModel):
    """Что потребовалось согласовать, чтобы утверждение оператора прошло."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = RECONCILIATION_VERSION
    alignments: list[FactAlignment] = Field(default_factory=list)
    passes: int = 0
    notes_ru: list[str] = Field(default_factory=list)

    @property
    def summary_ru(self) -> str:
        if not self.alignments:
            return "Зависимые факты согласовывать не потребовалось."
        return (
            f"Согласовано зависимых фактов: {len(self.alignments)}. "
            "Каждый приведён к тому, что следует из вывода модели; документ "
            "оператора записан их источником."
        )
