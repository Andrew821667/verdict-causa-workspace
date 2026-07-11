from datetime import date

import pytest

from causa.core.models import LegalSource, SourceType
from causa.core.source_hierarchy import AuthorityLevel
from causa.institutional.contracts.authority_model import (
    AuthorityResolutionRule,
    authority_level_for_source,
    evaluate_lex_specialis,
    evaluate_source_authority,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_lex_specialis_selects_special_source_regardless_of_candidate_order() -> None:
    general_source = get_synthetic_contract_source(
        "synthetic-ru-contract-general-performance-duty"
    )
    special_source = get_synthetic_contract_source(
        "synthetic-ru-contract-supply-specific-delivery-duty"
    )

    evaluation = evaluate_lex_specialis([special_source, general_source])

    assert evaluation.selected_source_id == special_source.id
    assert evaluation.candidate_source_ids == [special_source.id, general_source.id]
    assert (
        "Special source prevails over general source at the same authority level."
        in evaluation.reasons
    )


def test_lex_specialis_keeps_general_source_when_no_special_source_exists() -> None:
    general_source = get_synthetic_contract_source(
        "synthetic-ru-contract-general-performance-duty"
    )

    evaluation = evaluate_lex_specialis([general_source])

    assert evaluation.selected_source_id == general_source.id
    assert (
        "Selected synthetic-ru-contract-general-performance-duty at statutory authority."
        in evaluation.reasons
    )


def test_lex_specialis_requires_candidate_source() -> None:
    with pytest.raises(ValueError, match="At least one source"):
        evaluate_lex_specialis([])


def test_authority_level_is_derived_from_supported_source_types() -> None:
    sources_by_level = {
        AuthorityLevel.STATUTORY: LegalSource(
            id="statute",
            title="Statute",
            source_type=SourceType.STATUTE,
            text="Synthetic statute.",
        ),
        AuthorityLevel.JUDICIAL: LegalSource(
            id="case-law",
            title="Case law",
            source_type=SourceType.CASE_LAW,
            text="Synthetic case law.",
        ),
        AuthorityLevel.CONTRACTUAL: LegalSource(
            id="contract",
            title="Contract",
            source_type=SourceType.CONTRACT,
            text="Synthetic contract term.",
        ),
        AuthorityLevel.FACTUAL: LegalSource(
            id="fact",
            title="Fact",
            source_type=SourceType.FACT,
            text="Synthetic fact.",
        ),
    }

    assert {
        authority_level_for_source(source) for source in sources_by_level.values()
    } == set(sources_by_level)


def test_higher_authority_prevails_over_more_specific_lower_source() -> None:
    statute = LegalSource(
        id="statute",
        title="Statute",
        source_type=SourceType.STATUTE,
        text="Synthetic statute.",
        metadata={"specificity": "general"},
    )
    contract = LegalSource(
        id="contract",
        title="Contract",
        source_type=SourceType.CONTRACT,
        text="Synthetic special contract term.",
        metadata={"specificity": "special"},
    )

    evaluation = evaluate_source_authority([contract, statute])

    assert evaluation.selected_source_id == statute.id
    assert AuthorityResolutionRule.HIGHER_AUTHORITY in evaluation.applied_rules
    assert AuthorityResolutionRule.LEX_SPECIALIS not in evaluation.applied_rules


def test_temporal_applicability_is_checked_before_authority_ranking() -> None:
    expired_statute = LegalSource(
        id="expired-statute",
        title="Expired statute",
        source_type=SourceType.STATUTE,
        text="Synthetic expired statute.",
        valid_to="2025-12-31",
    )
    current_case_law = LegalSource(
        id="current-case-law",
        title="Current case law",
        source_type=SourceType.CASE_LAW,
        text="Synthetic current case law.",
        valid_from="2020-01-01",
    )

    evaluation = evaluate_source_authority(
        [expired_statute, current_case_law],
        moment=date(2026, 1, 21),
    )

    assert evaluation.selected_source_id == current_case_law.id
    assert evaluation.excluded_source_ids == [expired_statute.id]
    assert AuthorityResolutionRule.TEMPORAL_APPLICABILITY in evaluation.applied_rules


def test_equal_authority_and_specificity_requires_human_resolution() -> None:
    first_statute = LegalSource(
        id="first-statute",
        title="First statute",
        source_type=SourceType.STATUTE,
        text="Synthetic statute.",
    )
    second_statute = LegalSource(
        id="second-statute",
        title="Second statute",
        source_type=SourceType.STATUTE,
        text="Synthetic statute.",
    )

    evaluation = evaluate_source_authority([first_statute, second_statute])

    assert evaluation.selected_source_id is None
    assert AuthorityResolutionRule.UNRESOLVED_EQUAL_AUTHORITY in evaluation.applied_rules
