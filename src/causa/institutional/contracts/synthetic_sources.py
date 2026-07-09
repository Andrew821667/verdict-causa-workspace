from causa.core.models import LegalSource, SourceType


SYNTHETIC_CONTRACT_SOURCES = [
    LegalSource(
        id="synthetic-ru-contract-supply-delivery-duty",
        title="Synthetic supply delivery duty",
        source_type=SourceType.STATUTE,
        text=(
            "Synthetic source: in a supply relation, the supplier must deliver goods "
            "by the agreed date unless a valid excuse applies."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "delivery_duty"},
    ),
    LegalSource(
        id="synthetic-ru-contract-delivery-term",
        title="Synthetic agreed delivery term",
        source_type=SourceType.STATUTE,
        text=(
            "Synthetic source: when parties agree a delivery date, performance is "
            "assessed against that date."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "delivery_term"},
    ),
    LegalSource(
        id="synthetic-ru-contract-valid-excuse",
        title="Synthetic valid excuse rule",
        source_type=SourceType.STATUTE,
        text=(
            "Synthetic source: a valid contractual or statutory excuse can prevent "
            "a late delivery issue from becoming a breach issue."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "valid_excuse"},
    ),
    LegalSource(
        id="synthetic-ru-contract-acceptance-defects",
        title="Synthetic acceptance and defects rule",
        source_type=SourceType.STATUTE,
        text=(
            "Synthetic source: acceptance and defects should be evaluated separately "
            "from the basic delivery date question."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "acceptance_defects"},
    ),
    LegalSource(
        id="synthetic-ru-contract-payment-duty",
        title="Synthetic buyer payment duty",
        source_type=SourceType.STATUTE,
        text=(
            "Synthetic source: the buyer payment duty should not be erased by an "
            "unrelated delivery argument without source-grounded analysis."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "payment_duty"},
    ),
    LegalSource(
        id="synthetic-ru-contract-penalty-reduction",
        title="Synthetic penalty reduction boundary",
        source_type=SourceType.STATUTE,
        text=(
            "Synthetic source: penalty reduction analysis should not erase all "
            "liability automatically."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "penalty_reduction"},
    ),
]


def get_synthetic_contract_source(source_id: str) -> LegalSource:
    for source in SYNTHETIC_CONTRACT_SOURCES:
        if source.id == source_id:
            return source
    msg = f"Unknown synthetic contract source: {source_id}"
    raise KeyError(msg)
