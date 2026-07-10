import pytest

from causa.institutional.contracts.authority_model import evaluate_lex_specialis
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
    assert "Special source prevails over general source." in evaluation.reasons


def test_lex_specialis_keeps_general_source_when_no_special_source_exists() -> None:
    general_source = get_synthetic_contract_source(
        "synthetic-ru-contract-general-performance-duty"
    )

    evaluation = evaluate_lex_specialis([general_source])

    assert evaluation.selected_source_id == general_source.id
    assert "No more specific contractual source was available." in evaluation.reasons


def test_lex_specialis_requires_candidate_source() -> None:
    with pytest.raises(ValueError, match="At least one source"):
        evaluate_lex_specialis([])
