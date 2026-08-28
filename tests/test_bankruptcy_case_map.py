from causa.institutional.contracts.bankruptcy_case_map import (
    BankruptcyCaseMap,
    summarize_claim_status_ru,
    summarize_setoff_status_ru,
    summarize_transaction_status_ru,
)
from causa.institutional.contracts.synthetic_bankruptcy_case_map import (
    build_synthetic_bankruptcy_case_map,
)


def test_synthetic_case_map_builds_and_round_trips() -> None:
    case = build_synthetic_bankruptcy_case_map()

    assert isinstance(case, BankruptcyCaseMap)
    assert case.debtor.id == "debtor"
    assert len(case.parties) == 8
    assert len(case.claims) == 6
    assert len(case.transactions) == 2
    assert len(case.setoffs) == 1

    round_tripped = BankruptcyCaseMap.model_validate_json(case.model_dump_json())
    assert round_tripped == case


def test_every_claim_carries_a_distinct_ranking_track() -> None:
    case = build_synthetic_bankruptcy_case_map()

    labels = [claim.status_label_ru for claim in case.claims]
    assert len(labels) == len(set(labels)), labels


def test_claim_status_prefers_current_over_ranking_tier() -> None:
    from causa.institutional.contracts.bankruptcy_claims import BankruptcyClaimsEvaluation
    from causa.institutional.contracts.bankruptcy_ranking import BankruptcyRankingEvaluation

    claims_evaluation = BankruptcyClaimsEvaluation(
        constraint_set_id="x",
        satisfiable=True,
        claim_is_current=True,
        individual_enforcement_suspended=False,
        individual_enforcement_permitted_by_exception=False,
        requires_human_bankruptcy_claims_assessment=False,
    )
    ranking_evaluation = BankruptcyRankingEvaluation(
        constraint_set_id="x",
        satisfiable=True,
        first_tier=True,
        second_tier=False,
        third_tier=False,
        subordinated_after_third_tier=False,
        satisfied_from_pledge_proceeds=False,
        satisfied_last_after_all_other_creditors=False,
        requires_human_bankruptcy_ranking_assessment=False,
    )

    label = summarize_claim_status_ru(claims_evaluation, ranking_evaluation)

    assert "текущее" in label
    assert "первая очередь" not in label


def test_transaction_status_names_the_ground_not_just_voidable() -> None:
    case = build_synthetic_bankruptcy_case_map()

    labels = [t.status_label_ru for t in case.transactions]
    assert any("вред кредиторам" in label for label in labels)
    assert any("предпочтение" in label for label in labels)


def test_setoff_status_reflects_prohibition() -> None:
    case = build_synthetic_bankruptcy_case_map()

    assert case.setoffs[0].setoff_evaluation.setoff_prohibited is True
    assert "запрещён" in case.setoffs[0].status_label_ru


def test_resulting_claim_id_links_transaction_to_claim() -> None:
    case = build_synthetic_bankruptcy_case_map()

    linked = next(t for t in case.transactions if t.resulting_claim_id is not None)
    assert linked.resulting_claim_id == "claim-e"
    assert any(c.id == linked.resulting_claim_id for c in case.claims)


def test_summarize_functions_have_a_fallback_for_unset_facts() -> None:
    from causa.institutional.contracts.bankruptcy_contest import BankruptcyContestEvaluation
    from causa.institutional.contracts.bankruptcy_setoff import BankruptcySetoffEvaluation

    empty_contest = BankruptcyContestEvaluation(
        constraint_set_id="x",
        satisfiable=True,
        voidable_as_unequal_consideration=False,
        voidable_as_harm_to_creditors=False,
        transaction_voidable_as_suspicious=False,
        voidable_as_preference_short_window=False,
        voidable_as_preference_six_month_window=False,
        transaction_voidable_as_preference=False,
        transaction_voidable=False,
        standing_to_file=False,
        requires_human_bankruptcy_contest_assessment=False,
    )
    empty_setoff = BankruptcySetoffEvaluation(
        constraint_set_id="x",
        satisfiable=True,
        setoff_prohibited=False,
        setoff_permitted_as_priority_neutral=False,
        netting_permitted_by_financial_contract_exception=False,
        requires_human_bankruptcy_setoff_assessment=False,
    )

    assert summarize_transaction_status_ru(empty_contest) == "основание оспаривания не подтверждено"
    assert summarize_setoff_status_ru(empty_setoff) == "зачёт или нетто-обязательство не заявлены"
