"""Схема правоотношения: связи между сторонами и цепочка до итога.

Проверяется главное свойство схемы — она не должна расходиться с вердиктом.
Две картины одного дела, показывающие разное, хуже, чем одна неполная.
"""

import pytest

from causa.phase0.demo_trace import build_supply_dispute_demo_trace
from causa.ui.gaps import build_gap_queue
from causa.ui.qualification import build_case_qualification
from causa.ui.relation_scheme import CREDITOR, DEBTOR, LinkState, build_relation_scheme
from causa.ui.verdict import build_case_verdict


@pytest.fixture(scope="module")
def scheme_and_verdict():
    result = build_supply_dispute_demo_trace().analysis_result
    qualification = build_case_qualification(result)
    gaps = build_gap_queue(result)
    verdict = build_case_verdict(result, qualification, gaps)
    return build_relation_scheme(result, qualification, verdict), verdict, result


def test_the_scheme_and_the_verdict_say_the_same_thing(scheme_and_verdict) -> None:
    """Схема не имеет права на собственный вывод."""
    scheme, verdict, _ = scheme_and_verdict

    assert scheme.outcome_ru == verdict.headline_ru
    assert scheme.outcome_detail_ru == verdict.detail_ru


def test_links_connect_only_the_two_declared_parties(scheme_and_verdict) -> None:
    """Третья сторона на схеме означала бы, что её взяли неизвестно откуда."""
    scheme, _, _ = scheme_and_verdict
    known = {party.id for party in scheme.parties}

    assert known == {DEBTOR, CREDITOR}
    for link in scheme.links:
        assert link.source in known
        assert link.target in known


def test_a_breached_obligation_is_marked_breached(scheme_and_verdict) -> None:
    """Просрочка в фактах и «исполнено» на схеме — это разные дела."""
    scheme, _, result = scheme_and_verdict
    performance = next(link for link in scheme.links if link.id == "link:performance")

    assert result.constraint_evaluation.late_performance_issue is True
    assert performance.state is LinkState.BREACHED


def test_an_unclaimed_relation_is_absent_and_not_denied(scheme_and_verdict) -> None:
    """«Не заявлено» и «не было» — разные утверждения, и путать их нельзя."""
    scheme, _, result = scheme_and_verdict
    payment = next(link for link in scheme.links if link.id == "link:payment")

    assert result.evidence_mapping.facts.payment_duty_exists is False
    assert payment.state is LinkState.ABSENT
    assert "не заявлено" in payment.detail_ru


def test_the_chain_breaks_where_the_condition_failed(scheme_and_verdict) -> None:
    """Обрыв виден в своём месте, а не сводится к ярлыку в конце."""
    scheme, _, result = scheme_and_verdict
    broke = scheme.broke_at

    assert result.constraint_evaluation.damages_remedy_available is False
    assert broke is not None
    assert broke.id == "stage:remedy"
