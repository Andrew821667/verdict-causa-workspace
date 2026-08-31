"""Сборка карты дела о банкротстве из проверенных материалов.

## Чего не хватало

`bankruptcy_case_map.py` описывает, как карта дела выглядит, но не отвечает
на вопрос, откуда в ней берутся факты. Пока ответа не было, карта собиралась
единственным доступным способом — руками в коде: набор булевых значений
писался прямо в вызове, из него строился `*EvidenceMappingResult`, и он шёл
в `evaluate_*`.

Так карта проходила мимо той самой двери, которая делает факт фактом в этом
проекте. Каждый институт требует `Reviewed*Evidence`: утверждение о предикате
со ссылкой на материал дела (`source_refs`), статус проверки и идентификатор
проверившего. `map_reviewed_*_evidence` отказывается работать с непроверенным
доказательством и с неполным набором предикатов. Карта дела не вызывала эти
функции ни разу.

Разница не косметическая. Утверждение «требование обеспечено залогом склада»
в реальном деле держится на договоре залога, и юрист отвечает за то, что оно
прочитано верно. Записанное булевым значением в коде, оно ничем не отличается
от догадки — и не отличимо от неё при чтении.

## Что делает этот модуль

Вводит контракт данных на дело целиком — `ReviewedBankruptcyCaseEvidence` — и
собирает из него карту, прогоняя каждый блок через настоящие
`map_reviewed_*_evidence`, `build_*_constraint_set` и `evaluate_*` четырёх
институтов. Новых правовых выводов модуль не делает: он остаётся оркестровкой,
как и `bankruptcy_case_map.py`.

## Что проверяется на входе

Проверки здесь — не формальность: каждая закрывает способ показать юристу
картину, которой в деле нет.

* `case_id` каждого блока обязан совпадать с делом — иначе в карту одного дела
  попадёт требование из другого, и это будет незаметно;
* кредитор и контрагент обязаны быть среди участников — иначе в таблице
  появится имя, которого в деле нет;
* идентификаторы требований, сделок и зачётов уникальны — иначе связь
  «сделка → порождённое требование» указывает неизвестно куда;
* `resulting_claim_id` обязан разрешаться в требование этого же дела;
* должник обязан быть среди участников.

Проверку самих доказательств — статус, проверяющего, полноту предикатов —
модуль не повторяет: её делают `map_reviewed_*_evidence`, и дублировать
чужую ответственность значило бы завести второе место, где она может
разойтись с первым.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causa.institutional.contracts.bankruptcy_case_map import (
    BankruptcyCaseMap,
    CaseParty,
    CaseTimelineEvent,
    build_claim_map_entry,
    build_setoff_map_entry,
    build_transaction_map_entry,
)
from causa.institutional.contracts.bankruptcy_claims import (
    ReviewedBankruptcyClaimsEvidence,
    build_bankruptcy_claims_constraint_set,
    evaluate_bankruptcy_claims_constraints,
    map_reviewed_bankruptcy_claims_evidence,
)
from causa.institutional.contracts.bankruptcy_contest import (
    ReviewedBankruptcyContestEvidence,
    build_bankruptcy_contest_constraint_set,
    evaluate_bankruptcy_contest_constraints,
    map_reviewed_bankruptcy_contest_evidence,
)
from causa.institutional.contracts.bankruptcy_ranking import (
    ReviewedBankruptcyRankingEvidence,
    build_bankruptcy_ranking_constraint_set,
    evaluate_bankruptcy_ranking_constraints,
    map_reviewed_bankruptcy_ranking_evidence,
)
from causa.institutional.contracts.bankruptcy_setoff import (
    ReviewedBankruptcySetoffEvidence,
    build_bankruptcy_setoff_constraint_set,
    evaluate_bankruptcy_setoff_constraints,
    map_reviewed_bankruptcy_setoff_evidence,
)

BANKRUPTCY_CASE_ASSEMBLY_VERSION = "contracts-bankruptcy-case-assembly-v0"


class CaseClaimEvidence(BaseModel):
    """Одно требование кредитора: описание и два проверенных блока фактов.

    Требование проходит через два института сразу — режим (текущее или
    реестровое) и очерёдность, — поэтому и блоков доказательств два. Разделять
    их правильно: вопрос «когда возникло обязательство» и вопрос «к какой
    категории относится требование» доказываются разными материалами дела.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    creditor_id: str
    description_ru: str
    amount: float | None = None
    currency: str = "RUB"
    claims_evidence: ReviewedBankruptcyClaimsEvidence
    ranking_evidence: ReviewedBankruptcyRankingEvidence


class CaseTransactionEvidence(BaseModel):
    """Одна оспариваемая сделка должника с проверенным блоком фактов."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    counterparty_id: str
    description_ru: str
    contest_evidence: ReviewedBankruptcyContestEvidence
    #: Требование, возникшее у контрагента после признания сделки
    #: недействительной. Связь задаётся фактом дела, а не выводится: институт
    #: оспаривания об очерёдности не судит, а институт очерёдности принимает
    #: «требование из недействительной сделки» готовым признаком.
    resulting_claim_id: str | None = None


class CaseSetoffEvidence(BaseModel):
    """Один заявленный зачёт или нетто-обязательство."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    creditor_id: str
    description_ru: str
    setoff_evidence: ReviewedBankruptcySetoffEvidence


class ReviewedBankruptcyCaseEvidence(BaseModel):
    """Материалы дела о банкротстве, прошедшие проверку юристом."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = BANKRUPTCY_CASE_ASSEMBLY_VERSION
    case_id: str
    debtor: CaseParty
    parties: tuple[CaseParty, ...] = Field(min_length=1)
    timeline: tuple[CaseTimelineEvent, ...] = ()
    claims: tuple[CaseClaimEvidence, ...] = ()
    transactions: tuple[CaseTransactionEvidence, ...] = ()
    setoffs: tuple[CaseSetoffEvidence, ...] = ()
    notes_ru: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_integrity(self) -> "ReviewedBankruptcyCaseEvidence":
        party_ids = [party.id for party in self.parties]
        if len(party_ids) != len(set(party_ids)):
            raise ValueError("Участники дела содержат повторяющиеся идентификаторы.")
        known = set(party_ids)
        if self.debtor.id not in known:
            raise ValueError("Должник обязан быть среди участников дела.")

        entry_ids = (
            [claim.id for claim in self.claims]
            + [deal.id for deal in self.transactions]
            + [setoff.id for setoff in self.setoffs]
        )
        if len(entry_ids) != len(set(entry_ids)):
            raise ValueError(
                "Идентификаторы требований, сделок и зачётов обязаны быть различны: "
                "иначе связь между записями карты указывает неизвестно куда."
            )

        claim_ids = {claim.id for claim in self.claims}
        for claim in self.claims:
            self._require_party(claim.creditor_id, known, f"требования {claim.id}")
            self._require_case(claim.claims_evidence.case_id, f"требования {claim.id}")
            self._require_case(claim.ranking_evidence.case_id, f"требования {claim.id}")
        for deal in self.transactions:
            self._require_party(deal.counterparty_id, known, f"сделки {deal.id}")
            self._require_case(deal.contest_evidence.case_id, f"сделки {deal.id}")
            if deal.resulting_claim_id is not None and deal.resulting_claim_id not in claim_ids:
                raise ValueError(
                    f"Сделка {deal.id} ссылается на требование "
                    f"{deal.resulting_claim_id}, которого в деле нет."
                )
        for setoff in self.setoffs:
            self._require_party(setoff.creditor_id, known, f"зачёта {setoff.id}")
            self._require_case(setoff.setoff_evidence.case_id, f"зачёта {setoff.id}")
        return self

    def _require_party(self, party_id: str, known: set[str], where: str) -> None:
        if party_id not in known:
            raise ValueError(
                f"Сторона {party_id} у {where} не значится среди участников дела: "
                "в карте появилось бы имя, которого в деле нет."
            )

    def _require_case(self, case_id: str, where: str) -> None:
        if case_id != self.case_id:
            raise ValueError(
                f"Доказательства {where} относятся к делу {case_id}, а карта строится "
                f"по делу {self.case_id}."
            )


def build_bankruptcy_case_map(evidence: ReviewedBankruptcyCaseEvidence) -> BankruptcyCaseMap:
    """Собрать карту дела, прогнав каждый блок через настоящие институты.

    Ни один вывод здесь не вычисляется заново: `evaluate_*` четырёх институтов
    вызываются как есть, а карта лишь раскладывает их результат по записям.
    """
    claims = []
    for claim in evidence.claims:
        claims_mapping = map_reviewed_bankruptcy_claims_evidence(claim.claims_evidence)
        ranking_mapping = map_reviewed_bankruptcy_ranking_evidence(claim.ranking_evidence)
        claims.append(
            build_claim_map_entry(
                entry_id=claim.id,
                creditor_id=claim.creditor_id,
                description_ru=claim.description_ru,
                amount=claim.amount,
                currency=claim.currency,
                claims_evaluation=evaluate_bankruptcy_claims_constraints(
                    build_bankruptcy_claims_constraint_set(claims_mapping),
                    claims_mapping.facts,
                ),
                ranking_evaluation=evaluate_bankruptcy_ranking_constraints(
                    build_bankruptcy_ranking_constraint_set(ranking_mapping),
                    ranking_mapping.facts,
                ),
            )
        )

    transactions = []
    for deal in evidence.transactions:
        contest_mapping = map_reviewed_bankruptcy_contest_evidence(deal.contest_evidence)
        transactions.append(
            build_transaction_map_entry(
                entry_id=deal.id,
                counterparty_id=deal.counterparty_id,
                description_ru=deal.description_ru,
                contest_evaluation=evaluate_bankruptcy_contest_constraints(
                    build_bankruptcy_contest_constraint_set(contest_mapping),
                    contest_mapping.facts,
                ),
                resulting_claim_id=deal.resulting_claim_id,
            )
        )

    setoffs = []
    for setoff in evidence.setoffs:
        setoff_mapping = map_reviewed_bankruptcy_setoff_evidence(setoff.setoff_evidence)
        setoffs.append(
            build_setoff_map_entry(
                entry_id=setoff.id,
                creditor_id=setoff.creditor_id,
                description_ru=setoff.description_ru,
                setoff_evaluation=evaluate_bankruptcy_setoff_constraints(
                    build_bankruptcy_setoff_constraint_set(setoff_mapping),
                    setoff_mapping.facts,
                ),
            )
        )

    return BankruptcyCaseMap(
        case_id=evidence.case_id,
        debtor=evidence.debtor,
        parties=list(evidence.parties),
        timeline=list(evidence.timeline),
        claims=claims,
        transactions=transactions,
        setoffs=setoffs,
        notes_ru=list(evidence.notes_ru),
    )
