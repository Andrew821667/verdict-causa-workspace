from causa.institutional.contracts.schema import ContractCase, ContractRelationType


def test_contract_case_creation() -> None:
    case = ContractCase(
        id="case-1",
        relation_type=ContractRelationType.SUPPLY,
    )
    assert case.relation_type == ContractRelationType.SUPPLY
