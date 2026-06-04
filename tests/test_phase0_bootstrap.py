import pytest

from causa.core.bootstrap import (
    BootstrapReviewStatus,
    NormCondition,
    NormConsequence,
    ReviewedNormJSON,
    translate_reviewed_norm,
)


def test_unreviewed_norm_cannot_be_translated() -> None:
    norm = ReviewedNormJSON(id="norm-1", source_id="source-1")

    with pytest.raises(ValueError, match="Only reviewed"):
        translate_reviewed_norm(norm)


def test_reviewed_norm_translation_preserves_coordinates() -> None:
    norm = ReviewedNormJSON(
        id="norm-1",
        source_id="source-1",
        subjects=["supplier", "buyer"],
        actions=["deliver goods"],
        conditions=[NormCondition(id="condition-1", text="Supply contract exists.")],
        consequences=[NormConsequence(id="consequence-1", text="Delivery duty applies.")],
        review_status=BootstrapReviewStatus.REVIEWED,
        reviewer_id="domain-owner-1",
    )

    result = translate_reviewed_norm(norm)

    assert result.norm_id == "norm-1"
    assert result.source_id == "source-1"
    assert result.schema_version == "contracts.norm.v0"
    assert result.translator_version == "contracts-json-to-formal-v0"
    assert result.obligation_rule.id == "obligation-rule:norm-1"
    assert result.obligation_rule.debtor == "supplier"
    assert result.obligation_rule.creditor == "buyer"
    assert result.obligation_rule.action == "deliver goods"
    assert result.obligation_rule.conditions[0].source_ref == "source-1"
