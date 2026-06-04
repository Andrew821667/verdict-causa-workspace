from causa.core.models import LegalClaim


def test_legal_claim_confidence_range() -> None:
    claim = LegalClaim(
        id="claim-1",
        text="The supplier breached the delivery obligation.",
        confidence=0.8,
    )
    assert claim.confidence == 0.8
