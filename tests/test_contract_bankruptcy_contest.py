import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.bankruptcy_contest import (
    BANKRUPTCY_CONTEST_EVIDENCE_SCHEMA_VERSION,
    BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS,
    BANKRUPTCY_CONTEST_MAPPING_VERSION,
    BANKRUPTCY_CONTEST_MODEL_VERSION,
    BankruptcyContestEvidenceAssertion,
    BankruptcyContestEvidencePredicate,
    BankruptcyContestFactSet,
    ReviewedBankruptcyContestEvidence,
    build_bankruptcy_contest_constraint_set,
    evaluate_bankruptcy_contest_constraints,
    map_reviewed_bankruptcy_contest_evidence,
)
from causa.institutional.contracts.bankruptcy_contest_evaluation import (
    SYNTHETIC_BANKRUPTCY_CONTEST_BENCHMARKS,
    SYNTHETIC_BANKRUPTCY_CONTEST_RED_TEAM_CASES,
    run_bankruptcy_contest_benchmark_suite,
    run_bankruptcy_contest_red_team_suite,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def _evidence(**overrides) -> ReviewedBankruptcyContestEvidence:
    values = {predicate: False for predicate in BankruptcyContestEvidencePredicate}
    assertions = tuple(
        BankruptcyContestEvidenceAssertion(
            id=f"assertion-{predicate.value}",
            predicate=predicate,
            value=value,
            source_refs=("case-fact-1",),
        )
        for predicate, value in values.items()
    )
    fields = {
        "id": "evidence-bankruptcy-contest-1",
        "case_id": "case-bankruptcy-1",
        "assertions": assertions,
        "legal_source_refs": BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS,
        "review_status": BootstrapReviewStatus.REVIEWED,
        "reviewer_id": "reviewer-1",
    }
    fields.update(overrides)
    return ReviewedBankruptcyContestEvidence(**fields)


def test_mapping_rejects_unreviewed_evidence() -> None:
    evidence = _evidence(review_status=BootstrapReviewStatus.DRAFT)
    with pytest.raises(ValueError, match="must be reviewed"):
        map_reviewed_bankruptcy_contest_evidence(evidence)


def test_mapping_rejects_incomplete_evidence() -> None:
    evidence = _evidence()
    incomplete = evidence.model_copy(update={"assertions": evidence.assertions[:-1]})
    with pytest.raises(ValueError, match="missing predicates"):
        map_reviewed_bankruptcy_contest_evidence(incomplete)


def test_evidence_rejects_duplicate_predicates_and_source_refs() -> None:
    evidence = _evidence()
    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedBankruptcyContestEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=(*evidence.assertions, evidence.assertions[0]),
            legal_source_refs=evidence.legal_source_refs,
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )
    with pytest.raises(ValidationError, match="duplicate legal source refs"):
        ReviewedBankruptcyContestEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=evidence.assertions,
            legal_source_refs=(evidence.legal_source_refs[0], evidence.legal_source_refs[0]),
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )


def test_fact_consistency_rejects_one_year_without_three_year_window() -> None:
    values = {field_name: False for field_name in BankruptcyContestFactSet.model_fields}
    values.update(
        transaction_within_one_year_before_or_after_petition=True,
        transaction_within_three_years_before_or_after_petition=False,
    )
    with pytest.raises(ValidationError, match="лежит и в пределах трёх лет"):
        BankruptcyContestFactSet(**values)


def test_fact_consistency_rejects_narrow_ground_without_general_ground() -> None:
    values = {field_name: False for field_name in BankruptcyContestFactSet.model_fields}
    values.update(preference_narrow_ground_present=True, preference_ground_present=False)
    with pytest.raises(ValidationError, match="частный случай общего основания"):
        BankruptcyContestFactSet(**values)


def test_mapping_and_constraint_set_carry_versions() -> None:
    evidence = _evidence(
        assertions=tuple(
            BankruptcyContestEvidenceAssertion(
                id=f"assertion-{predicate.value}",
                predicate=predicate,
                value=predicate == BankruptcyContestEvidencePredicate.APPLICANT_IS_ADMINISTRATOR,
                source_refs=("case-fact-1",),
            )
            for predicate in BankruptcyContestEvidencePredicate
        )
    )
    mapping = map_reviewed_bankruptcy_contest_evidence(evidence)

    assert mapping.schema_version == BANKRUPTCY_CONTEST_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == BANKRUPTCY_CONTEST_MAPPING_VERSION
    assert mapping.legal_source_refs == list(BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS)

    constraint_set = build_bankruptcy_contest_constraint_set(mapping)
    assert constraint_set.model_version == BANKRUPTCY_CONTEST_MODEL_VERSION

    evaluation = evaluate_bankruptcy_contest_constraints(constraint_set, mapping.facts)
    assert evaluation.satisfiable is True
    assert evaluation.standing_to_file is True
    assert evaluation.transaction_voidable is False


def test_bankruptcy_contest_sources_are_verbatim_127fz_text() -> None:
    sources = [
        get_synthetic_contract_source(source_id)
        for source_id in BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS
    ]

    assert all(source.metadata["text_verbatim"] is True for source in sources)
    assert all(source.metadata["specificity"] == "special" for source in sources)
    assert all("127-ФЗ" in source.metadata["legal_reference"] for source in sources)


def test_bankruptcy_contest_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_bankruptcy_contest_benchmark_suite()
    red_team = run_bankruptcy_contest_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_BANKRUPTCY_CONTEST_BENCHMARKS) == 11
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_BANKRUPTCY_CONTEST_RED_TEAM_CASES) == 8
    assert red_team.blocked == red_team.total
