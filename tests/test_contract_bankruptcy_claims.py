import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.bankruptcy_claims import (
    BANKRUPTCY_CLAIMS_EVIDENCE_SCHEMA_VERSION,
    BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS,
    BANKRUPTCY_CLAIMS_MAPPING_VERSION,
    BANKRUPTCY_CLAIMS_MODEL_VERSION,
    BankruptcyClaimsEvidenceAssertion,
    BankruptcyClaimsEvidencePredicate,
    BankruptcyClaimsFactSet,
    ReviewedBankruptcyClaimsEvidence,
    build_bankruptcy_claims_constraint_set,
    evaluate_bankruptcy_claims_constraints,
    map_reviewed_bankruptcy_claims_evidence,
)
from causa.institutional.contracts.bankruptcy_claims_evaluation import (
    SYNTHETIC_BANKRUPTCY_CLAIMS_BENCHMARKS,
    SYNTHETIC_BANKRUPTCY_CLAIMS_RED_TEAM_CASES,
    run_bankruptcy_claims_benchmark_suite,
    run_bankruptcy_claims_red_team_suite,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def _evidence(**overrides) -> ReviewedBankruptcyClaimsEvidence:
    values = {
        BankruptcyClaimsEvidencePredicate.OBLIGATION_AROSE_BEFORE_PETITION_ACCEPTED: True,
        BankruptcyClaimsEvidencePredicate.OBSERVATION_INTRODUCED: True,
        BankruptcyClaimsEvidencePredicate.CREDITOR_SEEKS_INDIVIDUAL_ENFORCEMENT: True,
        BankruptcyClaimsEvidencePredicate.ENFORCEMENT_DOCUMENT_PREDATES_OBSERVATION_AND_IS_EXEMPT_CATEGORY: False,
    }
    assertions = tuple(
        BankruptcyClaimsEvidenceAssertion(
            id=f"assertion-{predicate.value}",
            predicate=predicate,
            value=value,
            source_refs=("case-fact-1",),
        )
        for predicate, value in values.items()
    )
    fields = {
        "id": "evidence-bankruptcy-claims-1",
        "case_id": "case-bankruptcy-1",
        "assertions": assertions,
        "legal_source_refs": BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS,
        "review_status": BootstrapReviewStatus.REVIEWED,
        "reviewer_id": "reviewer-1",
    }
    fields.update(overrides)
    return ReviewedBankruptcyClaimsEvidence(**fields)


def test_mapping_rejects_unreviewed_evidence() -> None:
    evidence = _evidence(review_status=BootstrapReviewStatus.DRAFT)
    with pytest.raises(ValueError, match="must be reviewed"):
        map_reviewed_bankruptcy_claims_evidence(evidence)


def test_mapping_rejects_incomplete_evidence() -> None:
    evidence = _evidence()
    incomplete = evidence.model_copy(update={"assertions": evidence.assertions[:-1]})
    with pytest.raises(ValueError, match="missing predicates"):
        map_reviewed_bankruptcy_claims_evidence(incomplete)


def test_evidence_rejects_duplicate_predicates_and_source_refs() -> None:
    evidence = _evidence()
    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedBankruptcyClaimsEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=(*evidence.assertions, evidence.assertions[0]),
            legal_source_refs=evidence.legal_source_refs,
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )
    with pytest.raises(ValidationError, match="duplicate legal source refs"):
        ReviewedBankruptcyClaimsEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=evidence.assertions,
            legal_source_refs=(evidence.legal_source_refs[0], evidence.legal_source_refs[0]),
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )


def test_fact_consistency_rejects_exception_without_enforcement_attempt() -> None:
    values = {field_name: False for field_name in BankruptcyClaimsFactSet.model_fields}
    values.update(
        observation_introduced=True,
        enforcement_document_predates_observation_and_is_exempt_category=True,
    )
    with pytest.raises(ValidationError, match="Исключение по вступившему в силу"):
        BankruptcyClaimsFactSet(**values)


def test_fact_consistency_rejects_exception_without_observation() -> None:
    values = {field_name: False for field_name in BankruptcyClaimsFactSet.model_fields}
    values.update(
        creditor_seeks_individual_enforcement=True,
        enforcement_document_predates_observation_and_is_exempt_category=True,
    )
    with pytest.raises(ValidationError, match="только при введённой процедуре"):
        BankruptcyClaimsFactSet(**values)


def test_mapping_and_constraint_set_carry_versions() -> None:
    evidence = _evidence()
    mapping = map_reviewed_bankruptcy_claims_evidence(evidence)

    assert mapping.schema_version == BANKRUPTCY_CLAIMS_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == BANKRUPTCY_CLAIMS_MAPPING_VERSION
    assert mapping.legal_source_refs == list(BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS)

    constraint_set = build_bankruptcy_claims_constraint_set(mapping)
    assert constraint_set.model_version == BANKRUPTCY_CLAIMS_MODEL_VERSION

    evaluation = evaluate_bankruptcy_claims_constraints(constraint_set, mapping.facts)
    assert evaluation.satisfiable is True
    assert evaluation.individual_enforcement_suspended is True


def test_bankruptcy_claims_sources_are_verbatim_127fz_text() -> None:
    sources = [
        get_synthetic_contract_source(source_id)
        for source_id in BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS
    ]

    assert all(source.metadata["text_verbatim"] is True for source in sources)
    assert all(source.metadata["specificity"] == "special" for source in sources)
    assert all("127-ФЗ" in source.metadata["legal_reference"] for source in sources)


def test_bankruptcy_claims_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_bankruptcy_claims_benchmark_suite()
    red_team = run_bankruptcy_claims_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_BANKRUPTCY_CLAIMS_BENCHMARKS) == 7
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_BANKRUPTCY_CLAIMS_RED_TEAM_CASES) == 7
    assert red_team.blocked == red_team.total
