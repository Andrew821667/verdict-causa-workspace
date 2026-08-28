"""Синтетическая демонстрационная карта дела о банкротстве.

Одно вымышленное дело — банкротство ООО «Стройторг» — проведено через все
четыре института банкротства (`bankruptcy_claims`, `bankruptcy_ranking`,
`bankruptcy_contest`, `bankruptcy_setoff`) по-настоящему: факты собраны в
`*FactSet`, поданы в реальные `evaluate_*`, а не в заранее написанные
`*Evaluation`. Так `BankruptcyCaseMap` доказывает, что четыре института
складываются в связную картину одного дела, а не просто похожи по форме.

Шесть кредиторов покрывают шесть разных исходов ranking (обе очереди,
залог, субординация, облигации без срока погашения, третья очередь);
две сделки — оба основания оспаривания; один зачёт — запрещённый случай.
"""

from causa.institutional.contracts.bankruptcy_case_map import (
    BankruptcyCaseMap,
    CaseParty,
    CaseTimelineEvent,
    build_claim_map_entry,
    build_setoff_map_entry,
    build_transaction_map_entry,
)
from causa.institutional.contracts.bankruptcy_claims import (
    BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS,
    BankruptcyClaimsEvidenceMappingResult,
    BankruptcyClaimsFactSet,
    build_bankruptcy_claims_constraint_set,
    evaluate_bankruptcy_claims_constraints,
)
from causa.institutional.contracts.bankruptcy_contest import (
    BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS,
    BankruptcyContestEvidenceMappingResult,
    BankruptcyContestFactSet,
    build_bankruptcy_contest_constraint_set,
    evaluate_bankruptcy_contest_constraints,
)
from causa.institutional.contracts.bankruptcy_ranking import (
    BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS,
    BankruptcyRankingEvidenceMappingResult,
    BankruptcyRankingFactSet,
    build_bankruptcy_ranking_constraint_set,
    evaluate_bankruptcy_ranking_constraints,
)
from causa.institutional.contracts.bankruptcy_setoff import (
    BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS,
    BankruptcySetoffEvidenceMappingResult,
    BankruptcySetoffFactSet,
    build_bankruptcy_setoff_constraint_set,
    evaluate_bankruptcy_setoff_constraints,
)


def _claims_evaluation(artifact_id: str, **facts: bool):
    mapping = BankruptcyClaimsEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="synthetic-case-map",
        mapping_version="synthetic-case-map",
        facts=BankruptcyClaimsFactSet(**facts),
        legal_source_refs=list(BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS),
    )
    return evaluate_bankruptcy_claims_constraints(
        build_bankruptcy_claims_constraint_set(mapping), mapping.facts
    )


def _ranking_evaluation(artifact_id: str, **facts: bool):
    mapping = BankruptcyRankingEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="synthetic-case-map",
        mapping_version="synthetic-case-map",
        facts=BankruptcyRankingFactSet(**facts),
        legal_source_refs=list(BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS),
    )
    return evaluate_bankruptcy_ranking_constraints(
        build_bankruptcy_ranking_constraint_set(mapping), mapping.facts
    )


def _contest_evaluation(artifact_id: str, **facts: bool):
    mapping = BankruptcyContestEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="synthetic-case-map",
        mapping_version="synthetic-case-map",
        facts=BankruptcyContestFactSet(**facts),
        legal_source_refs=list(BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS),
    )
    return evaluate_bankruptcy_contest_constraints(
        build_bankruptcy_contest_constraint_set(mapping), mapping.facts
    )


def _setoff_evaluation(artifact_id: str, **facts: bool):
    mapping = BankruptcySetoffEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="synthetic-case-map",
        mapping_version="synthetic-case-map",
        facts=BankruptcySetoffFactSet(**facts),
        legal_source_refs=list(BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS),
    )
    return evaluate_bankruptcy_setoff_constraints(
        build_bankruptcy_setoff_constraint_set(mapping), mapping.facts
    )


def _default_claims_facts(**overrides: bool) -> dict[str, bool]:
    values = {field_name: False for field_name in BankruptcyClaimsFactSet.model_fields}
    values.update(overrides)
    return values


def _default_ranking_facts(**overrides: bool) -> dict[str, bool]:
    values = {field_name: False for field_name in BankruptcyRankingFactSet.model_fields}
    values.update(overrides)
    return values


def _default_contest_facts(**overrides: bool) -> dict[str, bool]:
    values = {field_name: False for field_name in BankruptcyContestFactSet.model_fields}
    values.update(overrides)
    return values


def build_synthetic_bankruptcy_case_map() -> BankruptcyCaseMap:
    debtor = CaseParty(id="debtor", name_ru="ООО «Стройторг»", role_ru="должник")
    parties = [
        debtor,
        CaseParty(id="creditor-a", name_ru="Иванов И. И.", role_ru="кредитор"),
        CaseParty(id="creditor-b", name_ru="Петров П. П. (работник)", role_ru="кредитор"),
        CaseParty(id="creditor-c", name_ru="Банк «Кредит-Инвест»", role_ru="кредитор"),
        CaseParty(id="creditor-d", name_ru="ООО «Поставщик»", role_ru="кредитор"),
        CaseParty(id="creditor-e", name_ru="ООО «Аффилированная компания»", role_ru="кредитор"),
        CaseParty(id="creditor-f", name_ru="Держатель бессрочных облигаций", role_ru="кредитор"),
        CaseParty(id="manager", name_ru="Сидоров С. С.", role_ru="конкурсный управляющий"),
    ]
    timeline = [
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
    ]

    claims = [
        build_claim_map_entry(
            entry_id="claim-a",
            creditor_id="creditor-a",
            description_ru="Требование о возмещении вреда здоровью при исполнении работ",
            amount=1_200_000,
            claims_evaluation=_claims_evaluation(
                "claim-a", **_default_claims_facts(obligation_arose_before_petition_accepted=True)
            ),
            ranking_evaluation=_ranking_evaluation(
                "claim-a", **_default_ranking_facts(is_life_or_health_harm_claim=True)
            ),
        ),
        build_claim_map_entry(
            entry_id="claim-b",
            creditor_id="creditor-b",
            description_ru="Задолженность по заработной плате за три месяца",
            amount=450_000,
            claims_evaluation=_claims_evaluation(
                "claim-b", **_default_claims_facts(obligation_arose_before_petition_accepted=True)
            ),
            ranking_evaluation=_ranking_evaluation(
                "claim-b",
                **_default_ranking_facts(is_wage_severance_or_authorship_claim=True),
            ),
        ),
        build_claim_map_entry(
            entry_id="claim-c",
            creditor_id="creditor-c",
            description_ru="Требование по кредитному договору, обеспеченное залогом склада",
            amount=18_000_000,
            claims_evaluation=_claims_evaluation(
                "claim-c", **_default_claims_facts(obligation_arose_before_petition_accepted=True)
            ),
            ranking_evaluation=_ranking_evaluation(
                "claim-c", **_default_ranking_facts(is_secured_by_pledge=True)
            ),
        ),
        build_claim_map_entry(
            entry_id="claim-d",
            creditor_id="creditor-d",
            description_ru="Оплата поставки материалов, договор заключён после наблюдения",
            amount=620_000,
            claims_evaluation=_claims_evaluation(
                "claim-d",
                **_default_claims_facts(
                    obligation_arose_before_petition_accepted=False,
                    observation_introduced=True,
                ),
            ),
            ranking_evaluation=_ranking_evaluation("claim-d", **_default_ranking_facts()),
        ),
        build_claim_map_entry(
            entry_id="claim-e",
            creditor_id="creditor-e",
            description_ru="Требование, возникшее из сделки, впоследствии оспоренной по п. 2 ст. 61.2",
            amount=3_500_000,
            claims_evaluation=_claims_evaluation(
                "claim-e", **_default_claims_facts(obligation_arose_before_petition_accepted=True)
            ),
            ranking_evaluation=_ranking_evaluation(
                "claim-e", **_default_ranking_facts(is_claim_from_avoided_transaction=True)
            ),
        ),
        build_claim_map_entry(
            entry_id="claim-f",
            creditor_id="creditor-f",
            description_ru="Требование по облигациям без срока погашения",
            amount=7_000_000,
            claims_evaluation=_claims_evaluation(
                "claim-f", **_default_claims_facts(obligation_arose_before_petition_accepted=True)
            ),
            ranking_evaluation=_ranking_evaluation(
                "claim-f", **_default_ranking_facts(is_perpetual_bond_claim=True)
            ),
        ),
    ]

    transactions = [
        build_transaction_map_entry(
            entry_id="transaction-1",
            counterparty_id="creditor-e",
            description_ru=(
                "Безвозмездная передача оборудования аффилированному лицу за четыре "
                "месяца до принятия заявления"
            ),
            contest_evaluation=_contest_evaluation(
                "transaction-1",
                **_default_contest_facts(
                    transaction_within_three_years_before_or_after_petition=True,
                    harm_to_creditors_caused=True,
                    counterparty_knew_of_harmful_purpose=True,
                    applicant_is_administrator=True,
                ),
            ),
            resulting_claim_id="claim-e",
        ),
        build_transaction_map_entry(
            entry_id="transaction-2",
            counterparty_id="creditor-d",
            description_ru=(
                "Платёж поставщику за две недели до принятия заявления, обеспечивший "
                "исполнение более раннего долга"
            ),
            contest_evaluation=_contest_evaluation(
                "transaction-2",
                **_default_contest_facts(
                    transaction_within_six_months_before_petition=True,
                    preference_ground_present=True,
                    preference_narrow_ground_present=True,
                    applicant_is_administrator=True,
                ),
            ),
        ),
    ]

    setoffs = [
        build_setoff_map_entry(
            entry_id="setoff-1",
            creditor_id="creditor-c",
            description_ru=(
                "Банк заявил о зачёте остатка на расчётном счёте против части "
                "требования по кредитному договору после введения наблюдения"
            ),
            setoff_evaluation=_setoff_evaluation(
                "setoff-1",
                observation_introduced=True,
                setoff_of_mutual_homogeneous_claims_asserted=True,
                setoff_would_violate_priority_order=True,
                arises_from_financial_contract_netting_under_article_4_1=False,
            ),
        ),
    ]

    return BankruptcyCaseMap(
        case_id="synthetic-bankruptcy-stroytorg-2026",
        debtor=debtor,
        parties=parties,
        timeline=timeline,
        claims=claims,
        transactions=transactions,
        setoffs=setoffs,
        notes_ru=[
            "Синтетическое дело: имена, суммы и обстоятельства вымышлены для "
            "демонстрации карты дела, а не взяты из реальной практики.",
        ],
    )
