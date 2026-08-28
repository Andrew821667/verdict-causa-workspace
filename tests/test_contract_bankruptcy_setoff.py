import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.bankruptcy_setoff import (
    BANKRUPTCY_SETOFF_EVIDENCE_SCHEMA_VERSION,
    BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS,
    BANKRUPTCY_SETOFF_MAPPING_VERSION,
    BANKRUPTCY_SETOFF_MODEL_VERSION,
    BankruptcySetoffEvidenceAssertion,
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


def test_bankruptcy_setoff_sources_are_verbatim_127fz_text() -> None:
    sources = [
        get_synthetic_contract_source(source_id)
        for source_id in BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS
    ]

    assert all(source.metadata["text_verbatim"] is True for source in sources)
    assert all(source.metadata["specificity"] == "special" for source in sources)
    assert all("127-ФЗ" in source.metadata["legal_reference"] for source in sources)


def test_bankruptcy_setoff_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_bankruptcy_setoff_benchmark_suite()
    red_team = run_bankruptcy_setoff_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_BANKRUPTCY_SETOFF_BENCHMARKS) == 5
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_BANKRUPTCY_SETOFF_RED_TEAM_CASES) == 6
    assert red_team.blocked == red_team.total
