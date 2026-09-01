"""Синтетическое дело о банкротстве — материалами, а не булевыми значениями.

Одно вымышленное дело, банкротство ООО «Стройторг», записано так, как в этот
проект попадают факты: проверенными доказательствами. Каждое утверждение о
предикате несёт ссылку на материал дела (`source_refs`), статус проверки и
идентификатора проверившего, и проходит через `map_reviewed_*_evidence`
своего института — те самые функции, которые отказываются работать с
непроверенным или неполным набором.

Раньше это же дело собиралось иначе: булевы значения писались прямо в вызове,
из них строился `*EvidenceMappingResult`, и карта проходила мимо проверки
вовсе. Разницу видно на одном примере: «требование обеспечено залогом склада»
в реальном деле держится на договоре залога, и за прочтение отвечает юрист;
записанное булевым значением в коде, оно ничем не отличается от догадки.

Шесть кредиторов покрывают шесть разных исходов очерёдности (обе очереди,
залог, субординация, облигации без срока погашения, третья очередь); две
сделки — оба основания оспаривания; один зачёт — запрещённый случай.
"""

from causa.institutional.contracts.bankruptcy_case_assembly import (
    CaseClaimEvidence,
    CaseSetoffEvidence,
    CaseTransactionEvidence,
    ReviewedBankruptcyCaseEvidence,
    build_bankruptcy_case_map,
)
from causa.institutional.contracts.bankruptcy_case_map import (
    BankruptcyCaseMap,
    CaseParty,
    CaseTimelineEvent,
)
from causa.institutional.contracts.bankruptcy_claims import (
    BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS,
    BankruptcyClaimsEvidenceAssertion,
    BankruptcyClaimsEvidencePredicate,
    ReviewedBankruptcyClaimsEvidence,
)
from causa.institutional.contracts.bankruptcy_contest import (
    BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS,
    BankruptcyContestEvidenceAssertion,
    BankruptcyContestEvidencePredicate,
    ReviewedBankruptcyContestEvidence,
)
from causa.institutional.contracts.bankruptcy_ranking import (
    BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS,
    BankruptcyRankingEvidenceAssertion,
    BankruptcyRankingEvidencePredicate,
    ReviewedBankruptcyRankingEvidence,
)
from causa.institutional.contracts.bankruptcy_setoff import (
    BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS,
    BankruptcySetoffEvidenceAssertion,
    BankruptcySetoffEvidencePredicate,
    ReviewedBankruptcySetoffEvidence,
)

CASE_ID = "synthetic-bankruptcy-stroytorg-2026"
REVIEWER_ID = "synthetic-bankruptcy-reviewer"


def _assertions(assertion_cls, predicate_enum, source_ref: str, true_predicates: set[str]):
    """Утверждения по всем предикатам института, каждое со ссылкой на материал.

    Полный набор обязателен: `map_reviewed_*_evidence` отвергает неполный, и
    это правильно — умолчание «о чём не сказано, того нет» пряталось бы в коде
    сборки вместо того, чтобы быть заявленным юристом.
    """
    return tuple(
        assertion_cls(
            id=f"{source_ref}:{predicate.value}",
            predicate=predicate,
            value=predicate.value in true_predicates,
            source_refs=(source_ref,),
        )
        for predicate in predicate_enum
    )


def _claims_evidence(entry_id: str, *true_predicates: str) -> ReviewedBankruptcyClaimsEvidence:
    source_ref = f"{CASE_ID}:{entry_id}:claims"
    return ReviewedBankruptcyClaimsEvidence(
        id=f"evidence-{entry_id}-claims",
        case_id=CASE_ID,
        assertions=_assertions(
            BankruptcyClaimsEvidenceAssertion,
            BankruptcyClaimsEvidencePredicate,
            source_ref,
            set(true_predicates),
        ),
        legal_source_refs=BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS,
        review_status="reviewed",
        reviewer_id=REVIEWER_ID,
    )


def _ranking_evidence(entry_id: str, *true_predicates: str) -> ReviewedBankruptcyRankingEvidence:
    source_ref = f"{CASE_ID}:{entry_id}:ranking"
    return ReviewedBankruptcyRankingEvidence(
        id=f"evidence-{entry_id}-ranking",
        case_id=CASE_ID,
        assertions=_assertions(
            BankruptcyRankingEvidenceAssertion,
            BankruptcyRankingEvidencePredicate,
            source_ref,
            set(true_predicates),
        ),
        legal_source_refs=BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS,
        review_status="reviewed",
        reviewer_id=REVIEWER_ID,
    )


def _contest_evidence(entry_id: str, *true_predicates: str) -> ReviewedBankruptcyContestEvidence:
    source_ref = f"{CASE_ID}:{entry_id}:contest"
    return ReviewedBankruptcyContestEvidence(
        id=f"evidence-{entry_id}-contest",
        case_id=CASE_ID,
        assertions=_assertions(
            BankruptcyContestEvidenceAssertion,
            BankruptcyContestEvidencePredicate,
            source_ref,
            set(true_predicates),
        ),
        legal_source_refs=BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS,
        review_status="reviewed",
        reviewer_id=REVIEWER_ID,
    )


def _setoff_evidence(entry_id: str, *true_predicates: str) -> ReviewedBankruptcySetoffEvidence:
    source_ref = f"{CASE_ID}:{entry_id}:setoff"
    return ReviewedBankruptcySetoffEvidence(
        id=f"evidence-{entry_id}-setoff",
        case_id=CASE_ID,
        assertions=_assertions(
            BankruptcySetoffEvidenceAssertion,
            BankruptcySetoffEvidencePredicate,
            source_ref,
            set(true_predicates),
        ),
        legal_source_refs=BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS,
        review_status="reviewed",
        reviewer_id=REVIEWER_ID,
    )


DEBTOR = CaseParty(id="debtor", name_ru="ООО «Стройторг»", role_ru="должник")

PARTIES = (
    DEBTOR,
    CaseParty(id="creditor-a", name_ru="Иванов И. И.", role_ru="кредитор"),
    CaseParty(id="creditor-b", name_ru="Петров П. П. (работник)", role_ru="кредитор"),
    CaseParty(id="creditor-c", name_ru="Банк «Кредит-Инвест»", role_ru="кредитор"),
    CaseParty(id="creditor-d", name_ru="ООО «Поставщик»", role_ru="кредитор"),
    CaseParty(id="creditor-e", name_ru="ООО «Аффилированная компания»", role_ru="кредитор"),
    CaseParty(id="creditor-f", name_ru="Держатель бессрочных облигаций", role_ru="кредитор"),
    CaseParty(
        id="creditor-g", name_ru="АО «Горэнергосбыт»", role_ru="кредитор по текущим платежам"
    ),
    CaseParty(id="manager", name_ru="Сидоров С. С.", role_ru="конкурсный управляющий"),
)

TIMELINE = (
    CaseTimelineEvent(
        date="2026-01-15",
        label_ru="Принято заявление о признании должника банкротом",
        legal_reference_ru="ст. 62 127-ФЗ",
    ),
    CaseTimelineEvent(
        date="2026-01-15",
        label_ru="Введено наблюдение",
        legal_reference_ru="ст. 62-63 127-ФЗ",
    ),
    CaseTimelineEvent(
        date="2026-06-01",
        label_ru="Открыто конкурсное производство",
        legal_reference_ru="ст. 124 127-ФЗ",
    ),
)


def build_synthetic_bankruptcy_case_evidence() -> ReviewedBankruptcyCaseEvidence:
    """Материалы синтетического дела в том виде, в каком их проверил юрист."""
    return ReviewedBankruptcyCaseEvidence(
        case_id=CASE_ID,
        debtor=DEBTOR,
        parties=PARTIES,
        timeline=TIMELINE,
        claims=(
            CaseClaimEvidence(
                id="claim-a",
                creditor_id="creditor-a",
                description_ru="Требование о возмещении вреда здоровью при исполнении работ",
                amount=1_200_000,
                claims_evidence=_claims_evidence(
                    "claim-a",
                    "bankruptcy_case_opened",
                    "obligation_arose_before_petition_accepted",
                ),
                ranking_evidence=_ranking_evidence(
                    "claim-a",
                    "claim_filed_in_bankruptcy_register",
                    "is_life_or_health_harm_claim",
                ),
            ),
            CaseClaimEvidence(
                id="claim-b",
                creditor_id="creditor-b",
                description_ru="Задолженность по заработной плате за три месяца",
                amount=450_000,
                claims_evidence=_claims_evidence(
                    "claim-b",
                    "bankruptcy_case_opened",
                    "obligation_arose_before_petition_accepted",
                ),
                ranking_evidence=_ranking_evidence(
                    "claim-b",
                    "claim_filed_in_bankruptcy_register",
                    "is_wage_severance_or_authorship_claim",
                ),
            ),
            CaseClaimEvidence(
                id="claim-c",
                creditor_id="creditor-c",
                description_ru="Требование по кредитному договору, обеспеченное залогом склада",
                amount=18_000_000,
                claims_evidence=_claims_evidence(
                    "claim-c",
                    "bankruptcy_case_opened",
                    "obligation_arose_before_petition_accepted",
                ),
                ranking_evidence=_ranking_evidence(
                    "claim-c",
                    "claim_filed_in_bankruptcy_register",
                    "is_secured_by_pledge",
                ),
            ),
            CaseClaimEvidence(
                id="claim-d",
                creditor_id="creditor-d",
                description_ru="Оплата поставки материалов, договор заключён после наблюдения",
                amount=620_000,
                # Обязательство возникло ПОСЛЕ принятия заявления: признак
                # obligation_arose_before_petition_accepted не заявлен.
                claims_evidence=_claims_evidence(
                    "claim-d",
                    "bankruptcy_case_opened",
                    "observation_introduced",
                ),
                # Текущее требование в реестр не включается (пункт 2 статьи 5),
                # и очередь у него своя: поставка материалов — не расходы по
                # делу, не оплата труда, не привлечённое управляющим лицо и не
                # эксплуатационный платёж, поэтому пятая, «иные текущие».
                ranking_evidence=_ranking_evidence(
                    "claim-d",
                    "is_current_payment_claim",
                ),
            ),
            CaseClaimEvidence(
                id="claim-g",
                creditor_id="creditor-g",
                description_ru="Коммунальные платежи за производственный корпус после наблюдения",
                amount=310_000,
                claims_evidence=_claims_evidence(
                    "claim-g",
                    "bankruptcy_case_opened",
                    "observation_introduced",
                ),
                # Эксплуатационные платежи названы в законе прямо: четвёртая
                # очередь текущих (абзац пятый пункта 2 статьи 134 127-ФЗ).
                ranking_evidence=_ranking_evidence(
                    "claim-g",
                    "is_current_payment_claim",
                    "is_utility_payment",
                ),
            ),
            CaseClaimEvidence(
                id="claim-h",
                creditor_id="manager",
                description_ru="Вознаграждение арбитражного управляющего за процедуру наблюдения",
                amount=180_000,
                claims_evidence=_claims_evidence(
                    "claim-h",
                    "bankruptcy_case_opened",
                    "observation_introduced",
                ),
                # Первая очередь текущих платежей: вознаграждение управляющего
                # названо в абзаце втором пункта 2 статьи 134 127-ФЗ.
                ranking_evidence=_ranking_evidence(
                    "claim-h",
                    "is_current_payment_claim",
                    "is_proceeding_cost_or_mandatory_engagement",
                ),
            ),
            CaseClaimEvidence(
                id="claim-e",
                creditor_id="creditor-e",
                description_ru=(
                    "Требование, возникшее из сделки, впоследствии оспоренной по п. 2 ст. 61.2"
                ),
                amount=3_500_000,
                claims_evidence=_claims_evidence(
                    "claim-e",
                    "bankruptcy_case_opened",
                    "obligation_arose_before_petition_accepted",
                ),
                ranking_evidence=_ranking_evidence(
                    "claim-e",
                    "claim_filed_in_bankruptcy_register",
                    "is_claim_from_avoided_transaction",
                ),
            ),
            CaseClaimEvidence(
                id="claim-f",
                creditor_id="creditor-f",
                description_ru="Требование по облигациям без срока погашения",
                amount=7_000_000,
                claims_evidence=_claims_evidence(
                    "claim-f",
                    "bankruptcy_case_opened",
                    "obligation_arose_before_petition_accepted",
                ),
                ranking_evidence=_ranking_evidence(
                    "claim-f",
                    "claim_filed_in_bankruptcy_register",
                    "is_perpetual_bond_claim",
                ),
            ),
        ),
        transactions=(
            CaseTransactionEvidence(
                id="transaction-1",
                counterparty_id="creditor-e",
                description_ru=(
                    "Безвозмездная передача оборудования аффилированному лицу за четыре "
                    "месяца до принятия заявления"
                ),
                contest_evidence=_contest_evidence(
                    "transaction-1",
                    "transaction_within_three_years_before_or_after_petition",
                    "harm_to_creditors_caused",
                    "counterparty_knew_of_harmful_purpose",
                    "applicant_is_administrator",
                ),
                resulting_claim_id="claim-e",
            ),
            CaseTransactionEvidence(
                id="transaction-2",
                counterparty_id="creditor-d",
                description_ru=(
                    "Платёж поставщику за две недели до принятия заявления, обеспечивший "
                    "исполнение более раннего долга"
                ),
                contest_evidence=_contest_evidence(
                    "transaction-2",
                    "transaction_within_six_months_before_petition",
                    "preference_ground_present",
                    "preference_narrow_ground_present",
                    "applicant_is_administrator",
                ),
            ),
        ),
        setoffs=(
            CaseSetoffEvidence(
                id="setoff-1",
                creditor_id="creditor-c",
                description_ru=(
                    "Банк заявил о зачёте остатка на расчётном счёте против части "
                    "требования по кредитному договору после введения наблюдения"
                ),
                setoff_evidence=_setoff_evidence(
                    "setoff-1",
                    "observation_introduced",
                    "setoff_of_mutual_homogeneous_claims_asserted",
                    "setoff_would_violate_priority_order",
                ),
            ),
        ),
        notes_ru=(
            "Синтетическое дело: имена, суммы и обстоятельства вымышлены для "
            "демонстрации карты дела, а не взяты из реальной практики.",
        ),
    )


def build_synthetic_bankruptcy_case_map() -> BankruptcyCaseMap:
    """Карта синтетического дела, собранная из проверенных материалов."""
    return build_bankruptcy_case_map(build_synthetic_bankruptcy_case_evidence())
