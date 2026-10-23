import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.core.models import SourceType
from causa.institutional.contracts.bankruptcy_setoff import (
    BANKRUPTCY_SETOFF_EVIDENCE_SCHEMA_VERSION,
    BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS,
    BANKRUPTCY_SETOFF_MAPPING_VERSION,
    BANKRUPTCY_SETOFF_MODEL_VERSION,
    BankruptcySetoffEvidenceAssertion,
    BankruptcySetoffEvidenceMappingResult,
    BankruptcySetoffEvidencePredicate,
    BankruptcySetoffFactSet,
    ReviewedBankruptcySetoffEvidence,
    build_bankruptcy_setoff_constraint_set,
    evaluate_bankruptcy_setoff_constraints,
    map_reviewed_bankruptcy_setoff_evidence,
)
from causa.institutional.contracts.bankruptcy_setoff_evaluation import (
    SYNTHETIC_BANKRUPTCY_SETOFF_BENCHMARKS,
    SYNTHETIC_BANKRUPTCY_SETOFF_RED_TEAM_CASES,
    run_bankruptcy_setoff_benchmark_suite,
    run_bankruptcy_setoff_red_team_suite,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def _evidence(**overrides) -> ReviewedBankruptcySetoffEvidence:
    values = {predicate: False for predicate in BankruptcySetoffEvidencePredicate}
    assertions = tuple(
        BankruptcySetoffEvidenceAssertion(
            id=f"assertion-{predicate.value}",
            predicate=predicate,
            value=value,
            source_refs=("case-fact-1",),
        )
        for predicate, value in values.items()
    )
    fields = {
        "id": "evidence-bankruptcy-setoff-1",
        "case_id": "case-bankruptcy-1",
        "assertions": assertions,
        "legal_source_refs": BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS,
        "review_status": BootstrapReviewStatus.REVIEWED,
        "reviewer_id": "reviewer-1",
    }
    fields.update(overrides)
    return ReviewedBankruptcySetoffEvidence(**fields)


def test_mapping_rejects_unreviewed_evidence() -> None:
    evidence = _evidence(review_status=BootstrapReviewStatus.DRAFT)
    with pytest.raises(ValueError, match="must be reviewed"):
        map_reviewed_bankruptcy_setoff_evidence(evidence)


def test_mapping_rejects_incomplete_evidence() -> None:
    evidence = _evidence()
    incomplete = evidence.model_copy(update={"assertions": evidence.assertions[:-1]})
    with pytest.raises(ValueError, match="missing predicates"):
        map_reviewed_bankruptcy_setoff_evidence(incomplete)


def test_evidence_rejects_duplicate_predicates_and_source_refs() -> None:
    evidence = _evidence()
    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedBankruptcySetoffEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=(*evidence.assertions, evidence.assertions[0]),
            legal_source_refs=evidence.legal_source_refs,
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )
    with pytest.raises(ValidationError, match="duplicate legal source refs"):
        ReviewedBankruptcySetoffEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=evidence.assertions,
            legal_source_refs=(evidence.legal_source_refs[0], evidence.legal_source_refs[0]),
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )


def test_fact_consistency_rejects_setoff_and_netting_together() -> None:
    values = {field_name: False for field_name in BankruptcySetoffFactSet.model_fields}
    values.update(
        setoff_of_mutual_homogeneous_claims_asserted=True,
        arises_from_financial_contract_netting_under_article_4_1=True,
    )
    with pytest.raises(ValidationError, match="разные механизмы прекращения"):
        BankruptcySetoffFactSet(**values)


def test_fact_consistency_rejects_priority_violation_without_setoff() -> None:
    values = {field_name: False for field_name in BankruptcySetoffFactSet.model_fields}
    values.update(setoff_would_violate_priority_order=True)
    with pytest.raises(ValidationError, match="зачёт встречного однородного требования не заявлен"):
        BankruptcySetoffFactSet(**values)


def test_mapping_and_constraint_set_carry_versions() -> None:
    evidence = _evidence(
        assertions=tuple(
            BankruptcySetoffEvidenceAssertion(
                id=f"assertion-{predicate.value}",
                predicate=predicate,
                value=predicate
                in (
                    BankruptcySetoffEvidencePredicate.OBSERVATION_INTRODUCED,
                    BankruptcySetoffEvidencePredicate.SETOFF_OF_MUTUAL_HOMOGENEOUS_CLAIMS_ASSERTED,
                ),
                source_refs=("case-fact-1",),
            )
            for predicate in BankruptcySetoffEvidencePredicate
        )
    )
    mapping = map_reviewed_bankruptcy_setoff_evidence(evidence)

    assert mapping.schema_version == BANKRUPTCY_SETOFF_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == BANKRUPTCY_SETOFF_MAPPING_VERSION
    assert mapping.legal_source_refs == list(BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS)

    constraint_set = build_bankruptcy_setoff_constraint_set(mapping)
    assert constraint_set.model_version == BANKRUPTCY_SETOFF_MODEL_VERSION

    evaluation = evaluate_bankruptcy_setoff_constraints(constraint_set, mapping.facts)
    assert evaluation.satisfiable is True
    assert evaluation.setoff_permitted_as_priority_neutral is True


def test_bankruptcy_setoff_sources_are_verbatim() -> None:
    """Статьи 127-ФЗ, статьи ГК РФ и пункты обзоров ВС РФ — все дословно."""
    sources = [
        get_synthetic_contract_source(source_id)
        for source_id in BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS
    ]

    assert all(source.metadata["text_verbatim"] is True for source in sources)
    statutes = [source for source in sources if source.source_type == SourceType.STATUTE]
    practice = [source for source in sources if source.source_type == SourceType.CASE_LAW]
    assert len(statutes) + len(practice) == len(sources)
    assert {
        reference
        for source in statutes
        for reference in ("127-ФЗ", "ГК РФ")
        if reference in source.metadata["legal_reference"]
    } == {"127-ФЗ", "ГК РФ"}
    assert len(practice) == 3
    assert all("Президиумом ВС РФ" in source.metadata["legal_reference"] for source in practice)


def test_the_saldo_criterion_is_read_from_the_supreme_court_review() -> None:
    """Критерий модели — дословно из пункта 17 Обзора за 2022 год, а не из памяти."""
    text = get_synthetic_contract_source(
        "synthetic-ru-vs-review-bankruptcy-2022-17-heat-transfer-saldo-v1"
    ).text

    assert (
        "Сопоставление обязанностей сторон из одного договора (либо нескольких "
        "взаимосвязанных договоров)" in text
    )
    assert "не могут быть квалифицированы как зачет" in text
    assert "не препятствует определению итоговой обязанности" in text


def _facts(**updates: bool) -> BankruptcySetoffFactSet:
    values = {field_name: False for field_name in BankruptcySetoffFactSet.model_fields}
    values.update(updates)
    return BankruptcySetoffFactSet(**values)


def _evaluate(facts: BankruptcySetoffFactSet):
    mapping = BankruptcySetoffEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=facts,
        legal_source_refs=list(BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS),
    )
    return evaluate_bankruptcy_setoff_constraints(
        build_bankruptcy_setoff_constraint_set(mapping), facts
    )


PRIORITY_VIOLATING_SETOFF = {
    "observation_introduced": True,
    "setoff_of_mutual_homogeneous_claims_asserted": True,
    "setoff_would_violate_priority_order": True,
}
SALDO_ONE_CONTRACT = {
    "counter_obligations_arise_from_one_contract": True,
    "operation_determines_final_obligation_by_comparing_performances": True,
}


@pytest.mark.parametrize(
    "source",
    [
        "counter_obligations_arise_from_one_contract",
        "counter_obligations_arise_from_linked_contracts",
    ],
)
def test_saldo_needs_both_the_contract_link_and_the_final_obligation(source: str) -> None:
    assert _evaluate(_facts(**{source: True})).operation_is_saldo_not_setoff is False
    assert (
        _evaluate(
            _facts(
                **{source: True},
                operation_determines_final_obligation_by_comparing_performances=True,
            )
        ).operation_is_saldo_not_setoff
        is True
    )


def test_saldo_lifts_the_setoff_prohibition_and_the_flag_only_on_one_contract() -> None:
    one = _evaluate(_facts(**PRIORITY_VIOLATING_SETOFF, **SALDO_ONE_CONTRACT))
    linked = _evaluate(
        _facts(
            **PRIORITY_VIOLATING_SETOFF,
            counter_obligations_arise_from_linked_contracts=True,
            operation_determines_final_obligation_by_comparing_performances=True,
        )
    )

    assert one.setoff_prohibited is False and linked.setoff_prohibited is False
    assert one.requires_human_bankruptcy_setoff_assessment is False
    assert linked.requires_human_bankruptcy_setoff_assessment is True


def test_prior_judgments_change_no_conclusion() -> None:
    """Взыскание встречных требований судом названо, чтобы быть отброшенным."""
    named = {"prior_judgments_do_not_bar_saldo", "reasons_ru", "constraint_set_id"}
    checked = 0
    for task in SYNTHETIC_BANKRUPTCY_SETOFF_BENCHMARKS:
        if not task.facts.operation_determines_final_obligation_by_comparing_performances:
            continue
        without = _evaluate(
            task.facts.model_copy(update={"counter_claims_already_awarded_by_court": False})
        ).model_dump(exclude=named)
        with_ = _evaluate(
            task.facts.model_copy(update={"counter_claims_already_awarded_by_court": True})
        ).model_dump(exclude=named)
        assert without == with_, task.id
        checked += 1
    assert checked >= 5


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        (
            {
                "counter_obligations_arise_from_one_contract": True,
                "counter_obligations_arise_from_linked_contracts": True,
            },
            "одним договором|одного договора",
        ),
        (
            {"operation_determines_final_obligation_by_comparing_performances": True},
            "независимых договоров",
        ),
        (
            {
                **SALDO_ONE_CONTRACT,
                "arises_from_financial_contract_netting_under_article_4_1": True,
            },
            "Сальдо по договору и нетто-обязательство",
        ),
        ({"penalty_counted_in_saldo": True}, "завершающую обязанность не определяет"),
        ({"counter_claims_already_awarded_by_court": True}, "завершающую обязанность не"),
        (
            {**SALDO_ONE_CONTRACT, "penalty_clearly_disproportionate_to_breach": True},
            "неустойка при сальдировании не учтена",
        ),
    ],
    ids=[
        "один и взаимосвязанные",
        "без договорной связи",
        "сальдо и статья 4.1",
        "неустойка без сальдо",
        "судебные акты без сальдо",
        "несоразмерность без неустойки",
    ],
)
def test_saldo_facts_are_consistent(updates: dict, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        _facts(**updates)


def test_bankruptcy_setoff_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_bankruptcy_setoff_benchmark_suite()
    red_team = run_bankruptcy_setoff_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_BANKRUPTCY_SETOFF_BENCHMARKS) == 12
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_BANKRUPTCY_SETOFF_RED_TEAM_CASES) == 13
    assert red_team.blocked == red_team.total
