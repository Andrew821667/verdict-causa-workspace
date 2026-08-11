"""Тесты института решений собраний (глава 9.1 ГК РФ, статьи 181.1–181.5)."""

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.meeting_decisions import (
    MEETING_DECISIONS_EVIDENCE_SCHEMA_VERSION,
    MEETING_DECISIONS_MAPPING_VERSION,
    MEETING_DECISIONS_MODEL_VERSION,
    MeetingDecisionsEvidenceMappingResult,
    MeetingDecisionsFactSet,
    ReviewedMeetingDecisionsEvidence,
    build_meeting_decisions_constraint_set,
    evaluate_meeting_decisions_constraints,
)
from causa.institutional.contracts.meeting_decisions_evaluation import (
    SYNTHETIC_MEETING_DECISIONS_BENCHMARKS,
    SYNTHETIC_MEETING_DECISIONS_RED_TEAM_CASES,
    run_meeting_decisions_benchmark_suite,
    run_meeting_decisions_red_team_suite,
)
from causa.institutional.contracts.practice_coverage import institutes_for_article
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_meeting_decisions import (
    build_synthetic_meeting_decisions_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)


def _facts(**updates: bool) -> MeetingDecisionsFactSet:
    values = {field_name: False for field_name in MeetingDecisionsFactSet.model_fields}
    values.update(updates)
    return MeetingDecisionsFactSet(**values)


def _run(facts: MeetingDecisionsFactSet):
    mapping = MeetingDecisionsEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=facts,
        legal_source_refs=["test-law"],
    )
    return evaluate_meeting_decisions_constraints(
        build_meeting_decisions_constraint_set(mapping), facts
    )


def _flip(evidence, **updates: bool):
    return evidence.model_copy(
        update={
            "assertions": tuple(
                assertion.model_copy(update={"value": updates[assertion.predicate.value]})
                if assertion.predicate.value in updates
                else assertion
                for assertion in evidence.assertions
            )
        }
    )


_LAWFUL = {
    "meeting_decision_asserted": True,
    "quorum_present": True,
    "required_majority_obtained": True,
}


def test_institute_closes_the_last_coverage_gap_real_practice_hit() -> None:
    """Глава 9.1 была последним существенным пробелом покрытия.

    Дело 45-КГ23-2-К7 сослалось на статьи 181.3 и 181.5, а их не разбирал ни один
    институт пакета.
    """
    for article in ("181.1", "181.2", "181.3", "181.4", "181.5"):
        assert institutes_for_article(article) == ["meeting_decisions"]
    # Решение собрания не сделка: диапазон недействительности сделок не задет.
    assert institutes_for_article("181") == ["invalidity"]


def test_reviewed_meeting_decisions_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.meeting_decisions_evidence_mapping
    assert mapping.schema_version == MEETING_DECISIONS_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == MEETING_DECISIONS_MAPPING_VERSION
    assert result.meeting_decisions_constraint_set.model_version == MEETING_DECISIONS_MODEL_VERSION
    evaluation = result.meeting_decisions_evaluation
    # В демонстрационном деле решений сообщества не принималось.
    assert evaluation.meeting_decision_qualified is False
    assert evaluation.requires_human_meeting_decision_assessment is False


def test_three_outcomes_are_not_mixed() -> None:
    """Не принято, ничтожно и оспоримо — три разных исхода."""
    not_adopted = _run(_facts(meeting_decision_asserted=True, quorum_present=True))
    assert not_adopted.decision_not_adopted is True
    assert not_adopted.decision_void is False
    assert not_adopted.decision_voidable is False
    assert not_adopted.decision_binds_all_participants is False

    void = _run(_facts(**_LAWFUL, question_outside_competence=True))
    assert void.decision_void is True
    assert void.decision_voidable is False
    assert void.decision_binds_all_participants is False

    voidable = _run(_facts(**_LAWFUL, participant_equality_breached=True))
    assert voidable.decision_voidable is True
    assert voidable.decision_void is False
    # Оспоримое решение действует, пока не признано недействительным.
    assert voidable.decision_binds_all_participants is True


def test_curing_clauses_do_not_reach_nullity() -> None:
    """Оговорки статьи 181.4 снимают оспоримость, но не ничтожность."""
    cured = _run(
        _facts(
            **_LAWFUL,
            minutes_requirements_breached=True,
            vote_could_not_affect_outcome=True,
            no_material_adverse_consequences=True,
        )
    )
    assert cured.voidability_cured_by_immateriality is True
    assert cured.decision_voidable is False

    with_nullity = _run(
        _facts(
            **_LAWFUL,
            contrary_to_public_order_or_morality=True,
            minutes_requirements_breached=True,
            vote_could_not_affect_outcome=True,
            no_material_adverse_consequences=True,
            decision_confirmed_by_later_decision=True,
        )
    )
    assert with_nullity.decision_void is True
    assert with_nullity.decision_binds_all_participants is False


def test_full_participation_cures_the_agenda_defect_only() -> None:
    """Участие всех снимает порок повестки, но не иные основания ничтожности."""
    agenda = _run(_facts(**_LAWFUL, question_outside_agenda=True, all_participants_took_part=True))
    assert agenda.agenda_violation_void is False
    assert agenda.decision_void is False

    competence = _run(
        _facts(**_LAWFUL, question_outside_competence=True, all_participants_took_part=True)
    )
    assert competence.decision_void is True


def test_fact_set_rejects_full_participation_without_quorum() -> None:
    with pytest.raises(ValidationError, match="кворум не может"):
        _facts(meeting_decision_asserted=True, all_participants_took_part=True)

    with pytest.raises(ValidationError, match="Подтверждение решения"):
        _facts(decision_confirmed_by_later_decision=True)


def test_nullity_ground_is_reachable_through_the_full_pipeline() -> None:
    request = build_synthetic_supply_analysis_request()
    void_decision = request.model_copy(
        update={
            "meeting_decisions_evidence": _flip(
                request.meeting_decisions_evidence,
                meeting_decision_asserted=True,
                required_majority_obtained=True,
                question_outside_competence=True,
            )
        }
    )

    result = run_reviewed_contract_analysis(
        void_decision, build_synthetic_supply_analysis_sources()
    )

    evaluation = result.meeting_decisions_evaluation
    assert evaluation.decision_void is True
    assert evaluation.quorum_absent is True
    assert result.requires_human_resolution is True


def test_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.meeting_decisions_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedMeetingDecisionsEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=(*evidence.assertions, evidence.assertions[0]),
            legal_source_refs=evidence.legal_source_refs,
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )

    incomplete = evidence.model_copy(update={"assertions": evidence.assertions[:-1]})
    with pytest.raises(ValueError, match="missing predicates"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"meeting_decisions_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_evidence() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.meeting_decisions_evidence

    with pytest.raises(ValueError, match="Meeting-decisions evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "meeting_decisions_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_meeting_decisions_benchmark_suite()
    red_team = run_meeting_decisions_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_MEETING_DECISIONS_BENCHMARKS) == 12
    assert benchmark.failed == 0, [r for r in benchmark.results if not r.passed]
    assert red_team.total == len(SYNTHETIC_MEETING_DECISIONS_RED_TEAM_CASES) == 10
    assert red_team.unblocked == 0, [r for r in red_team.results if not r.blocked]


def test_synthetic_artifact_is_reproducible() -> None:
    artifact = build_synthetic_meeting_decisions_evaluation_artifact()

    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0
    assert "181.1–181.5" in artifact.disclaimer_ru
    assert any(
        "не является сделкой" in warning for warning in artifact.reviewed_evaluation.warnings_ru
    )
