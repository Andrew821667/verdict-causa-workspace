import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
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


def test_the_case_map_is_built_from_reviewed_evidence_only() -> None:
    """Карта обязана проходить через ту же дверь, что и всё остальное.

    Прежде она собиралась мимо неё: булевы значения писались прямо в коде, из
    них строился `*EvidenceMappingResult`, и `map_reviewed_*_evidence` не
    вызывалась ни разу. Утверждение «требование обеспечено залогом склада»
    держится в деле на договоре залога, и за прочтение отвечает юрист;
    записанное булевым значением в коде, оно неотличимо от догадки.
    """
    from causa.institutional.contracts.synthetic_bankruptcy_case_map import (
        build_synthetic_bankruptcy_case_evidence,
    )

    evidence = build_synthetic_bankruptcy_case_evidence()

    for claim in evidence.claims:
        for block in (claim.claims_evidence, claim.ranking_evidence):
            assert block.review_status is BootstrapReviewStatus.REVIEWED, claim.id
            assert block.reviewer_id, claim.id
            # Каждое утверждение обязано указывать на материал дела.
            assert all(assertion.source_refs for assertion in block.assertions), claim.id
    for deal in evidence.transactions:
        assert deal.contest_evidence.review_status is BootstrapReviewStatus.REVIEWED, deal.id
    for setoff in evidence.setoffs:
        assert setoff.setoff_evidence.review_status is BootstrapReviewStatus.REVIEWED, setoff.id


def test_unreviewed_materials_cannot_become_a_case_map() -> None:
    """Непроверенное доказательство обязано остановить сборку, а не пройти тихо."""
    from causa.institutional.contracts.bankruptcy_case_assembly import build_bankruptcy_case_map
    from causa.institutional.contracts.synthetic_bankruptcy_case_map import (
        build_synthetic_bankruptcy_case_evidence,
    )

    evidence = build_synthetic_bankruptcy_case_evidence()
    first = evidence.claims[0]
    draft = first.claims_evidence.model_copy(update={"review_status": BootstrapReviewStatus.DRAFT})
    broken = evidence.model_copy(
        update={
            "claims": (first.model_copy(update={"claims_evidence": draft}), *evidence.claims[1:])
        }
    )

    with pytest.raises(ValueError, match="must be reviewed"):
        build_bankruptcy_case_map(broken)


def test_a_creditor_outside_the_case_is_rejected() -> None:
    """Имя, которого в деле нет, не должно появиться в таблице требований."""
    from causa.institutional.contracts.bankruptcy_case_assembly import (
        ReviewedBankruptcyCaseEvidence,
    )
    from causa.institutional.contracts.synthetic_bankruptcy_case_map import (
        build_synthetic_bankruptcy_case_evidence,
    )

    evidence = build_synthetic_bankruptcy_case_evidence()
    stranger = evidence.claims[0].model_copy(update={"creditor_id": "creditor-unknown"})

    with pytest.raises(ValidationError, match="не значится среди участников"):
        ReviewedBankruptcyCaseEvidence(
            case_id=evidence.case_id,
            debtor=evidence.debtor,
            parties=evidence.parties,
            claims=(stranger,),
        )


def test_evidence_from_another_case_is_rejected() -> None:
    """Требование из чужого дела в карте было бы незаметно."""
    from causa.institutional.contracts.bankruptcy_case_assembly import (
        ReviewedBankruptcyCaseEvidence,
    )
    from causa.institutional.contracts.synthetic_bankruptcy_case_map import (
        build_synthetic_bankruptcy_case_evidence,
    )

    evidence = build_synthetic_bankruptcy_case_evidence()
    first = evidence.claims[0]
    alien = first.model_copy(
        update={"claims_evidence": first.claims_evidence.model_copy(update={"case_id": "other"})}
    )

    with pytest.raises(ValidationError, match="относятся к делу other"):
        ReviewedBankruptcyCaseEvidence(
            case_id=evidence.case_id,
            debtor=evidence.debtor,
            parties=evidence.parties,
            claims=(alien,),
        )


def test_a_transaction_cannot_point_at_a_claim_that_is_not_there() -> None:
    """Связь «сделка → порождённое требование» обязана разрешаться."""
    from causa.institutional.contracts.bankruptcy_case_assembly import (
        ReviewedBankruptcyCaseEvidence,
    )
    from causa.institutional.contracts.synthetic_bankruptcy_case_map import (
        build_synthetic_bankruptcy_case_evidence,
    )

    evidence = build_synthetic_bankruptcy_case_evidence()
    dangling = evidence.transactions[0].model_copy(update={"resulting_claim_id": "claim-zzz"})

    with pytest.raises(ValidationError, match="которого в деле нет"):
        ReviewedBankruptcyCaseEvidence(
            case_id=evidence.case_id,
            debtor=evidence.debtor,
            parties=evidence.parties,
            transactions=(dangling,),
        )
