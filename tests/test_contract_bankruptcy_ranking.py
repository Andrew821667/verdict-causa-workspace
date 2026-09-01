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
    # Полный набор предикатов, а не перечисленный руками: перечень рос дважды,
    # и оба раза помощник тихо начинал строить неполное доказательство —
    # проверка полноты срабатывала не там, где её проверяют.
    values = {predicate: False for predicate in BankruptcyRankingEvidencePredicate}
    values[BankruptcyRankingEvidencePredicate.CLAIM_FILED_IN_BANKRUPTCY_REGISTER] = True
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


def _current_facts(**updates: bool) -> BankruptcyRankingFactSet:
    """Факты по требованию кредитора по текущим платежам."""
    values = {field: False for field in BankruptcyRankingFactSet.model_fields}
    values["is_current_payment_claim"] = True
    values.update(updates)
    return BankruptcyRankingFactSet(**values)


def _evaluate(facts: BankruptcyRankingFactSet):
    mapping = BankruptcyRankingEvidenceMappingResult(
        evidence_id="test",
        schema_version=BANKRUPTCY_RANKING_EVIDENCE_SCHEMA_VERSION,
        mapping_version=BANKRUPTCY_RANKING_MAPPING_VERSION,
        facts=facts,
        legal_source_refs=list(BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS),
    )
    return evaluate_bankruptcy_ranking_constraints(
        build_bankruptcy_ranking_constraint_set(mapping), facts
    )


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

    assert benchmark.total == len(SYNTHETIC_BANKRUPTCY_RANKING_BENCHMARKS) == 16
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_BANKRUPTCY_RANKING_RED_TEAM_CASES) == 15
    assert red_team.blocked == red_team.total


def test_current_payments_have_their_own_five_tiers() -> None:
    """Пункт 2 статьи 134 — самостоятельная очерёдность, а не отсутствие очереди.

    До этого модель разбирала только реестровые требования, и любой текущий
    платёж читался как «очередь не определена». Но закон определяет её точно, и
    порядок расчётов с текущими кредиторами — не менее спорный вопрос, чем
    порядок в реестре.
    """
    cases = {
        "is_proceeding_cost_or_mandatory_engagement": "current_payment_first_tier",
        "is_post_petition_labour_payment": "current_payment_second_tier",
        "is_discretionary_engagement_payment": "current_payment_third_tier",
        "is_utility_payment": "current_payment_fourth_tier",
    }
    for predicate, output in cases.items():
        facts = _current_facts(**{predicate: True})
        evaluation = _evaluate(facts)
        assert getattr(evaluation, output) is True, predicate
        assert evaluation.current_payment_fifth_tier is False, predicate
        # Реестровые очереди к текущему платежу не применяются вовсе.
        assert evaluation.third_tier is False, predicate


def test_other_current_payments_fall_into_the_fifth_tier() -> None:
    """Пятая очередь — остаточная категория закона, и она названа своим номером."""
    evaluation = _evaluate(_current_facts())

    assert evaluation.current_payment_fifth_tier is True
    assert evaluation.current_payment_first_tier is False
    assert any("пятой очереди" in reason for reason in evaluation.reasons_ru)


def test_disaster_prevention_costs_go_ahead_of_all_current_payments() -> None:
    """Пункт 1.1 вытесняет пять очередей, а не встаёт в одну из них."""
    evaluation = _evaluate(_current_facts(is_technogenic_risk_mitigation_expense=True))

    assert evaluation.current_payment_ahead_of_all_current is True
    assert evaluation.current_payment_fifth_tier is False
    # Реальность угрозы и минимальный размер расходов — оценочные вопросы, и
    # решает их юрист, а не решатель.
    assert evaluation.requires_human_bankruptcy_ranking_assessment is True


def test_a_claim_cannot_be_both_current_and_in_the_register() -> None:
    """Требования по текущим платежам в реестр не включаются (п. 2 ст. 5 127-ФЗ)."""
    with pytest.raises(ValidationError, match="одновременно текущим и реестровым"):
        BankruptcyRankingFactSet(
            **{
                **{field: False for field in BankruptcyRankingFactSet.model_fields},
                "claim_filed_in_bankruptcy_register": True,
                "is_current_payment_claim": True,
            }
        )


def test_current_tiers_are_mutually_exclusive() -> None:
    """Пять очередей пункта 2 перечислены как взаимно исключающие."""
    with pytest.raises(ValidationError, match="нескольким очередям пункта 2"):
        _current_facts(is_utility_payment=True, is_post_petition_labour_payment=True)


def test_a_current_tier_requires_a_current_claim() -> None:
    """Очередь текущих платежей без самого признака текущего платежа — не факт."""
    with pytest.raises(ValidationError, match="только для требования"):
        BankruptcyRankingFactSet(
            **{
                **{field: False for field in BankruptcyRankingFactSet.model_fields},
                "is_utility_payment": True,
            }
        )


def test_excess_executive_severance_is_not_a_current_payment() -> None:
    """Пункт 2.1 прямо исключает такое требование из текущих платежей."""
    with pytest.raises(ValidationError, match="исключено из текущих платежей"):
        _current_facts(is_excess_executive_severance=True)

    evaluation = _evaluate(
        BankruptcyRankingFactSet(
            **{
                **{field: False for field in BankruptcyRankingFactSet.model_fields},
                "is_excess_executive_severance": True,
            }
        )
    )
    assert evaluation.excess_executive_severance_after_third_tier is True
    assert evaluation.current_payment_fifth_tier is False


def test_the_model_says_out_loud_that_calendar_order_is_not_its_business() -> None:
    """Внутри очереди закон велит платить по календарю, а дат у модели нет.

    Молчание об этом читалось бы как «очередь определена полностью», хотя
    очередь — только половина ответа.
    """
    evaluation = _evaluate(_current_facts(is_utility_payment=True))

    assert any("календарная" in reason for reason in evaluation.reasons_ru)
