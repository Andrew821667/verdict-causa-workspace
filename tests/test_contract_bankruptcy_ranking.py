import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.bankruptcy_ranking import (
    BANKRUPTCY_RANKING_EVIDENCE_SCHEMA_VERSION,
    BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS,
    BANKRUPTCY_RANKING_MAPPING_VERSION,
    BANKRUPTCY_RANKING_MODEL_VERSION,
    BankruptcyRankingEvidenceAssertion,
    BankruptcyRankingEvidenceMappingResult,
    BankruptcyRankingEvidencePredicate,
    BankruptcyRankingFactSet,
    ReviewedBankruptcyRankingEvidence,
    build_bankruptcy_ranking_constraint_set,
    evaluate_bankruptcy_ranking_constraints,
    map_reviewed_bankruptcy_ranking_evidence,
)
from causa.institutional.contracts.bankruptcy_ranking_evaluation import (
    SYNTHETIC_BANKRUPTCY_RANKING_BENCHMARKS,
    SYNTHETIC_BANKRUPTCY_RANKING_RED_TEAM_CASES,
    run_bankruptcy_ranking_benchmark_suite,
    run_bankruptcy_ranking_red_team_suite,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def _evidence(**overrides) -> ReviewedBankruptcyRankingEvidence:
    values = {
        BankruptcyRankingEvidencePredicate.CLAIM_FILED_IN_BANKRUPTCY_REGISTER: True,
        BankruptcyRankingEvidencePredicate.IS_LIFE_OR_HEALTH_HARM_CLAIM: False,
        BankruptcyRankingEvidencePredicate.IS_WAGE_SEVERANCE_OR_AUTHORSHIP_CLAIM: False,
        BankruptcyRankingEvidencePredicate.IS_SECURED_BY_PLEDGE: False,
        BankruptcyRankingEvidencePredicate.IS_CLAIM_FROM_AVOIDED_TRANSACTION: False,
        BankruptcyRankingEvidencePredicate.IS_PERPETUAL_BOND_CLAIM: False,
    }
    assertions = tuple(
        BankruptcyRankingEvidenceAssertion(
            id=f"assertion-{predicate.value}",
            predicate=predicate,
            value=value,
            source_refs=("case-fact-1",),
        )
        for predicate, value in values.items()
    )
    fields = {
        "id": "evidence-bankruptcy-ranking-1",
        "case_id": "case-bankruptcy-1",
        "assertions": assertions,
        "legal_source_refs": BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS,
        "review_status": BootstrapReviewStatus.REVIEWED,
        "reviewer_id": "reviewer-1",
    }
    fields.update(overrides)
    return ReviewedBankruptcyRankingEvidence(**fields)


def test_mapping_rejects_unreviewed_evidence() -> None:
    evidence = _evidence(review_status=BootstrapReviewStatus.DRAFT)
    with pytest.raises(ValueError, match="must be reviewed"):
        map_reviewed_bankruptcy_ranking_evidence(evidence)


def test_mapping_rejects_incomplete_evidence() -> None:
    evidence = _evidence()
    incomplete = evidence.model_copy(update={"assertions": evidence.assertions[:-1]})
    with pytest.raises(ValueError, match="missing predicates"):
        map_reviewed_bankruptcy_ranking_evidence(incomplete)


def test_evidence_rejects_duplicate_predicates_and_source_refs() -> None:
    evidence = _evidence()
    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedBankruptcyRankingEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=(*evidence.assertions, evidence.assertions[0]),
            legal_source_refs=evidence.legal_source_refs,
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )
    with pytest.raises(ValidationError, match="duplicate legal source refs"):
        ReviewedBankruptcyRankingEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=evidence.assertions,
            legal_source_refs=(evidence.legal_source_refs[0], evidence.legal_source_refs[0]),
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )


def test_fact_consistency_rejects_more_than_one_special_category() -> None:
    values = {field_name: False for field_name in BankruptcyRankingFactSet.model_fields}
    values.update(
        claim_filed_in_bankruptcy_register=True,
        is_life_or_health_harm_claim=True,
        is_secured_by_pledge=True,
    )
    with pytest.raises(ValidationError, match="взаимно исключают"):
        BankruptcyRankingFactSet(**values)


def test_fact_consistency_rejects_a_ranking_category_outside_the_register() -> None:
    """Очередь есть только у требования, включённого в реестр."""
    values = {field_name: False for field_name in BankruptcyRankingFactSet.model_fields}
    values.update(is_life_or_health_harm_claim=True)

    with pytest.raises(ValidationError, match="включённого в реестр"):
        BankruptcyRankingFactSet(**values)


def test_claim_outside_the_register_lands_in_no_tier_at_all() -> None:
    """Регрессия: «все категории — нет» раньше означало третью очередь.

    Требование по делу, где банкротства нет, попадало в третью очередь
    реестра — вывод о несуществующем реестре. Теперь остаточная категория
    закрыта воротами, и модель говорит об этом вслух.
    """
    values = {field_name: False for field_name in BankruptcyRankingFactSet.model_fields}
    facts = BankruptcyRankingFactSet(**values)

    mapping = BankruptcyRankingEvidenceMappingResult(
        evidence_id="outside-register",
        schema_version=BANKRUPTCY_RANKING_EVIDENCE_SCHEMA_VERSION,
        mapping_version=BANKRUPTCY_RANKING_MAPPING_VERSION,
        facts=facts,
        legal_source_refs=list(BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS),
    )
    evaluation = evaluate_bankruptcy_ranking_constraints(
        build_bankruptcy_ranking_constraint_set(mapping), facts
    )

    assert evaluation.satisfiable is True
    assert evaluation.third_tier is False
    assert evaluation.first_tier is False
    assert evaluation.second_tier is False
    assert evaluation.requires_human_bankruptcy_ranking_assessment is False
    assert any("не включено в реестр" in reason for reason in evaluation.reasons_ru)


def test_mapping_and_constraint_set_carry_versions() -> None:
    evidence = _evidence(
        assertions=tuple(
            BankruptcyRankingEvidenceAssertion(
                id=f"assertion-{predicate.value}",
                predicate=predicate,
                value=predicate
                in (
                    BankruptcyRankingEvidencePredicate.CLAIM_FILED_IN_BANKRUPTCY_REGISTER,
                    BankruptcyRankingEvidencePredicate.IS_WAGE_SEVERANCE_OR_AUTHORSHIP_CLAIM,
                ),
                source_refs=("case-fact-1",),
            )
            for predicate in BankruptcyRankingEvidencePredicate
        )
    )
    mapping = map_reviewed_bankruptcy_ranking_evidence(evidence)

    assert mapping.schema_version == BANKRUPTCY_RANKING_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == BANKRUPTCY_RANKING_MAPPING_VERSION
    assert mapping.legal_source_refs == list(BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS)

    constraint_set = build_bankruptcy_ranking_constraint_set(mapping)
    assert constraint_set.model_version == BANKRUPTCY_RANKING_MODEL_VERSION

    evaluation = evaluate_bankruptcy_ranking_constraints(constraint_set, mapping.facts)
    assert evaluation.satisfiable is True
    assert evaluation.second_tier is True
    assert evaluation.third_tier is False


def test_bankruptcy_ranking_sources_are_verbatim_127fz_text() -> None:
    sources = [
        get_synthetic_contract_source(source_id)
        for source_id in BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS
    ]

    assert all(source.metadata["text_verbatim"] is True for source in sources)
    assert all(source.metadata["specificity"] == "special" for source in sources)
    assert all("127-ФЗ" in source.metadata["legal_reference"] for source in sources)


def test_bankruptcy_ranking_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_bankruptcy_ranking_benchmark_suite()
    red_team = run_bankruptcy_ranking_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_BANKRUPTCY_RANKING_BENCHMARKS) == 8
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_BANKRUPTCY_RANKING_RED_TEAM_CASES) == 9
    assert red_team.blocked == red_team.total
