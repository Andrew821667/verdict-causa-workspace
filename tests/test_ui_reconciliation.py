"""Тесты согласования зависимых фактов."""

import base64

import pytest

from causa.institutional.contracts.fact_consistency import (
    FACT_CONSISTENCY_VOCABULARY,
    FactConsistencyMismatch,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.ui.documents import build_document
from causa.ui.reconciliation import (
    RECONCILABLE_FACTS,
    ROLE_DEPENDENT_FACTS,
    UNRECONCILABLE_RU,
    reconcile,
)
from causa.ui.server import DesktopService
from causa.ui.session import GapClosureBrokeInvariant, GapClosureConflict

WORKSPACE = "ws-demo-supply"
CASE = "case-supply-1"


def _service() -> DesktopService:
    return DesktopService()


def _upload(service) -> str:
    uploaded = service.add_document(
        WORKSPACE,
        CASE,
        {"filename": "Док.pdf", "content_base64": base64.b64encode(b"x").decode()},
    )
    return uploaded["document"]["id"]


def _gap(service, code: str):
    view = service.state.view(WORKSPACE, CASE)
    return next(gap for gap in view.gaps.gaps if gap.id.endswith(code))


def test_every_consistency_key_is_classified() -> None:
    """Ключ без записи означал бы, что согласование где-то молча не сработает.

    Классов три: согласуемое по постоянной паре, согласуемое по цели, которую
    называет само дело, и несогласуемое механически. Пересекаться они не имеют
    права — иначе непонятно, какое правило сработает.
    """
    classified = set(RECONCILABLE_FACTS) | set(ROLE_DEPENDENT_FACTS) | set(UNRECONCILABLE_RU)

    assert classified == set(FACT_CONSISTENCY_VOCABULARY)
    assert set(RECONCILABLE_FACTS).isdisjoint(UNRECONCILABLE_RU)
    assert set(ROLE_DEPENDENT_FACTS).isdisjoint(RECONCILABLE_FACTS)
    assert set(ROLE_DEPENDENT_FACTS).isdisjoint(UNRECONCILABLE_RU)
    for reason in ROLE_DEPENDENT_FACTS.values():
        assert len(reason) > 40


def test_every_unreconcilable_key_carries_a_reason() -> None:
    for key, reason in UNRECONCILABLE_RU.items():
        assert len(reason) > 40, key


def test_reconcilable_targets_name_real_evidence_and_predicates() -> None:
    """Карта согласования обязана ломаться, а не промахиваться молча."""
    request = build_synthetic_supply_analysis_request()

    for key, (field, predicate) in RECONCILABLE_FACTS.items():
        evidence = getattr(request, field, None)
        assert evidence is not None, key
        predicates = {assertion.predicate.value for assertion in evidence.assertions}
        assert predicate in predicates, f"{key}: {field}.{predicate}"


def test_reconciliation_records_the_document_as_the_source() -> None:
    """Исправленный факт обязан показывать, на чём держится его новое значение."""
    request = build_synthetic_supply_analysis_request()
    document = build_document(
        case_id=CASE, filename="Расчёт.pdf", content=b"calc", uploaded_by="op"
    )
    mismatch = FactConsistencyMismatch(
        key="remedies_loss_claim",
        fact_ru="средства защиты: заявлены убытки",
        anchor_ru="статья 393 ГК РФ",
        expected=True,
        actual=False,
    )

    updated, alignments, blocked = reconcile(request, [mismatch], document)

    assertion = next(
        item
        for item in updated.performance_remedies_evidence.assertions
        if item.predicate.value == "loss_claimed"
    )
    assert assertion.value is True
    assert document.id in assertion.source_refs
    assert [item.key for item in alignments] == ["remedies_loss_claim"]
    assert blocked == []


def test_unreconcilable_keys_do_not_stop_a_pass() -> None:
    """Часть таких расхождений исчезает сама, когда согласован исходный факт."""
    request = build_synthetic_supply_analysis_request()
    blocked_mismatch = FactConsistencyMismatch(
        key="sale_breach_status",
        fact_ru="купля-продажа: нарушение установлено",
        anchor_ru="нарушение выводится моделью обязательства",
        expected=False,
        actual=True,
    )

    _, alignments, blocked = reconcile(request, [blocked_mismatch])

    assert alignments == []
    assert blocked == ["sale_breach_status"]


def test_an_unknown_key_is_refused_rather_than_ignored() -> None:
    request = build_synthetic_supply_analysis_request()
    mismatch = FactConsistencyMismatch(
        key="remedies_loss_claim",
        fact_ru="…",
        anchor_ru="…",
        expected=True,
        actual=False,
    ).model_copy(update={"key": "выдуманная_сверка"})

    with pytest.raises(KeyError, match="без записи о согласовании"):
        reconcile(request, [mismatch])


def test_without_consent_the_closure_is_still_refused() -> None:
    """Согласование — решение оператора, а не поведение по умолчанию."""
    service = _service()
    document_id = _upload(service)
    gap = _gap(service, "request_damages_with_causation")

    with pytest.raises(GapClosureConflict):
        service.close_gap(
            WORKSPACE,
            CASE,
            {
                "gap_id": gap.id,
                "document_id": document_id,
                "kind": "asserted_fact",
                "fact_updates": gap.fact_updates,
            },
        )


def test_with_consent_the_case_is_recomputed_and_the_change_is_shown() -> None:
    """Одно утверждение оператора применяется ко всем наборам, где записан тот же факт."""
    service = _service()
    document_id = _upload(service)
    gap = _gap(service, "request_damages_with_causation")

    result = service.close_gap(
        WORKSPACE,
        CASE,
        {
            "gap_id": gap.id,
            "document_id": document_id,
            "kind": "asserted_fact",
            "fact_updates": gap.fact_updates,
            "reconcile_dependents": True,
        },
    )

    change = result["change"]
    reconciliation = result["reconciliation"]
    assert any(step["question_ru"].startswith("Доступно ли") for step in change["steps"])
    assert change["blocking_gaps_after"] < change["blocking_gaps_before"]
    assert reconciliation["lines_ru"]
    assert reconciliation["passes"] >= 2
    assert "Согласовано зависимых фактов" in reconciliation["summary_ru"]


def test_a_broken_institute_rule_stops_reconciliation_and_names_it() -> None:
    """Заявленная неустойка требует установленного нарушения — и это не обходится."""
    service = _service()
    document_id = _upload(service)
    gap = _gap(service, "activate_valid_exception")

    with pytest.raises(GapClosureBrokeInvariant) as failure:
        service.close_gap(
            WORKSPACE,
            CASE,
            {
                "gap_id": gap.id,
                "document_id": document_id,
                "kind": "asserted_fact",
                "fact_updates": gap.fact_updates,
                "reconcile_dependents": True,
            },
        )

    payload = failure.value.payload()
    assert payload["broken_rules"]
    assert "откачено" in payload["explanation_ru"]
    assert service.session(WORKSPACE, CASE).closures == []


def test_a_closure_blocked_only_by_unreconcilable_keys_says_which() -> None:
    """Оператор должен видеть, что именно система отказалась выбирать за него."""
    service = _service()
    document_id = _upload(service)
    gap = _gap(service, "confirm_nonconforming_performance")

    with pytest.raises(GapClosureConflict) as failure:
        service.close_gap(
            WORKSPACE,
            CASE,
            {
                "gap_id": gap.id,
                "document_id": document_id,
                "kind": "asserted_fact",
                "fact_updates": gap.fact_updates,
                "reconcile_dependents": True,
            },
        )

    payload = failure.value.payload()
    assert payload["blocked_ru"]
    assert any("nonconformity" in line for line in payload["blocked_ru"])


def test_role_dependent_key_is_reconciled_to_the_target_the_case_names() -> None:
    """Цель берётся из роли сообщения, а не из постоянной таблицы.

    Проверка обязана видеть именно тот институт, который назвала роль: если
    резолвер вернёт что-то другое, согласование молча исправит чужой предикат.
    """
    from causa.institutional.contracts.fact_consistency import FactConsistencyError
    from causa.institutional.contracts.messages import MessageRole
    from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
    from causa.institutional.contracts.synthetic_reviewed_analysis import (
        build_synthetic_supply_analysis_sources,
    )

    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    evidence = request.messages_evidence.model_copy(
        update={"message_role": MessageRole.SUPPLY_UNILATERAL_REFUSAL_NOTICE}
    )
    broken = request.model_copy(update={"messages_evidence": evidence})

    with pytest.raises(FactConsistencyError) as failure:
        run_reviewed_contract_analysis(broken, sources)

    fixed, alignments, blocked = reconcile(broken, failure.value.mismatches)

    assert blocked == []
    assert [(item.evidence_field, item.predicate) for item in alignments] == [
        ("supply_evidence", "unilateral_refusal_notice_delivered")
    ]
    assert alignments[0].before is False
    assert alignments[0].after is True
    # Согласованный запрос обязан проходить анализ: иначе согласование только
    # переставило противоречие с места на место.
    run_reviewed_contract_analysis(fixed, sources)


def test_a_role_added_for_the_delivery_sweep_resolves_too() -> None:
    """Роль, добавленная при доведении реестра до всех уведомлений о доставке.

    Прежний тест проверял первую роль, заведённую под 165.1; этот — одну из
    четырнадцати, а не восемь: резолвер не должен был остаться зашитым под
    единственный институт, который у него был на момент первой проверки.
    """
    from causa.institutional.contracts.fact_consistency import FactConsistencyError
    from causa.institutional.contracts.messages import MessageRole
    from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
    from causa.institutional.contracts.synthetic_reviewed_analysis import (
        build_synthetic_supply_analysis_sources,
    )

    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    evidence = request.messages_evidence.model_copy(
        update={"message_role": MessageRole.ASSIGNMENT_DEBTOR_NOTICE}
    )
    broken = request.model_copy(update={"messages_evidence": evidence})

    with pytest.raises(FactConsistencyError) as failure:
        run_reviewed_contract_analysis(broken, sources)

    fixed, alignments, blocked = reconcile(broken, failure.value.mismatches)

    assert blocked == []
    assert [(item.evidence_field, item.predicate) for item in alignments] == [
        ("obligation_dynamics_evidence", "debtor_notified")
    ]
    run_reviewed_contract_analysis(fixed, sources)


def test_a_negated_role_is_reconciled_to_its_negation() -> None:
    """Согласование пишет отрицание вывода модели, а не вывод напрямую.

    Предикат `creditors_not_notified` назван от противного: `True` значит
    «не уведомлены». Дело так и утверждает, хотя статья 165.1 признаёт
    сообщение доставленным. Если бы согласование записало вывод модели
    (`True`, «доставлено») напрямую в этот предикат, оно объявило бы
    кредиторов неуведомлёнными — ровно обратное тому, что установлено.
    """
    from causa.institutional.contracts.fact_consistency import FactConsistencyError
    from causa.institutional.contracts.messages import MessageRole
    from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
    from causa.institutional.contracts.synthetic_reviewed_analysis import (
        build_synthetic_supply_analysis_sources,
    )

    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    evidence = request.messages_evidence.model_copy(
        update={"message_role": MessageRole.ENTERPRISE_LEASE_CREDITORS_NOTICE}
    )
    lease_assertions = tuple(
        assertion.model_copy(update={"value": True})
        if assertion.predicate.value == "creditors_not_notified"
        else assertion
        for assertion in request.enterprise_lease_evidence.assertions
    )
    lease_evidence = request.enterprise_lease_evidence.model_copy(
        update={"assertions": lease_assertions}
    )
    broken = request.model_copy(
        update={"messages_evidence": evidence, "enterprise_lease_evidence": lease_evidence}
    )

    with pytest.raises(FactConsistencyError) as failure:
        run_reviewed_contract_analysis(broken, sources)

    fixed, alignments, blocked = reconcile(broken, failure.value.mismatches)

    assert blocked == []
    assert [(item.evidence_field, item.predicate) for item in alignments] == [
        ("enterprise_lease_evidence", "creditors_not_notified")
    ]
    # Отчёт говорит о доставке («да»), но в предикат от противного обязано
    # уйти отрицание: доставлено = True → «не уведомлены» = False.
    assert alignments[0].before is False
    assert alignments[0].after is True
    assert fixed.enterprise_lease_evidence.assertions[
        [a.predicate.value for a in fixed.enterprise_lease_evidence.assertions].index(
            "creditors_not_notified"
        )
    ].value is False
    run_reviewed_contract_analysis(fixed, sources)
