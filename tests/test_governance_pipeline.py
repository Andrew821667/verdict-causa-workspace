from causa.governance.pipeline import GovernanceStage, advance_candidate


def test_advance_candidate_success() -> None:
    decision = advance_candidate(GovernanceStage.PROPOSED, checks_passed=True)
    assert decision.accepted is True
    assert decision.next_stage == GovernanceStage.TYPE_CLASSIFICATION
    assert decision.next_stage_label_ru == "Классификация типа"
    assert decision.reasons_ru == ["Обязательные проверки пройдены."]


def test_advance_candidate_failure() -> None:
    decision = advance_candidate(GovernanceStage.PROPOSED, checks_passed=False)
    assert decision.accepted is False
    assert decision.next_stage == GovernanceStage.REJECTED
    assert decision.reasons_ru == ["Обязательные проверки не пройдены."]
