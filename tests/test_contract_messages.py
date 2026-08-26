"""Тесты модели юридически значимых сообщений (статья 165.1 ГК РФ)."""

import pytest

from causa.institutional.contracts.messages import (
    MessagesConstraintSet,
    MessagesFactSet,
    build_messages_constraint_set,
    evaluate_messages_constraints,
)
from causa.institutional.contracts.messages_evaluation import (
    run_messages_benchmark_suite,
    run_messages_red_team_suite,
)
from causa.institutional.contracts.synthetic_messages import (
    build_synthetic_messages_evaluation_artifact,
)


def _facts(**updates: bool) -> MessagesFactSet:
    values = {name: False for name in MessagesFactSet.model_fields}
    values.update(updates)
    return MessagesFactSet(**values)


def _evaluate(facts: MessagesFactSet):
    return evaluate_messages_constraints(MessagesConstraintSet(id="test"), facts)


QUALIFIED = {"message_asserted": True, "consequences_attached_by_law_or_transaction": True}
ADDRESSED = {
    "sent_to_statutory_or_agreed_address": True,
    "sender_and_addressee_identifiable": True,
    "form_matches_message_nature": True,
}


def test_handover_delivers_regardless_of_the_address_used() -> None:
    """Врученное сообщение доставлено, куда бы его ни посылали.

    Надлежащий адрес нужен второму пути — доставке по риску неполучения. Требовать
    его и от вручения значило бы объявить недоставленным сообщение, которое
    адресат держал в руках.
    """
    evaluation = _evaluate(_facts(**QUALIFIED, handed_to_addressee_or_representative=True))

    assert evaluation.delivered_by_handover is True
    assert evaluation.properly_addressed is False
    assert evaluation.message_delivered is True
    assert evaluation.consequences_effective is True


def test_the_addressee_bears_the_risk_of_not_collecting_the_message() -> None:
    """Содержание статьи 165.1: не вручено, но считается доставленным."""
    evaluation = _evaluate(
        _facts(
            **QUALIFIED,
            **ADDRESSED,
            arrived_at_addressee=True,
            non_receipt_due_to_addressee=True,
        )
    )

    assert evaluation.delivered_by_handover is False
    assert evaluation.delivered_by_addressee_risk is True
    assert evaluation.message_delivered is True
    assert evaluation.requires_human_message_assessment is True


def test_arrival_alone_does_not_deliver() -> None:
    """Поступление без обстоятельств, зависящих от адресата, доставки не даёт.

    Иначе любое неполученное письмо считалось бы доставленным, а норма прямо
    связывает это последствие с причинами на стороне адресата.
    """
    evaluation = _evaluate(_facts(**QUALIFIED, **ADDRESSED, arrived_at_addressee=True))

    assert evaluation.delivered_by_addressee_risk is False
    assert evaluation.message_delivered is False
    assert evaluation.delivery_not_established is True


def test_a_wrong_address_blocks_the_risk_route_only() -> None:
    """Без надлежащего адреса риск неполучения на адресата не перекладывается."""
    by_risk = _evaluate(
        _facts(
            **QUALIFIED,
            sender_and_addressee_identifiable=True,
            form_matches_message_nature=True,
            arrived_at_addressee=True,
            non_receipt_due_to_addressee=True,
        )
    )
    by_handover = _evaluate(
        _facts(**QUALIFIED, handed_to_addressee_or_representative=True)
    )

    assert by_risk.message_delivered is False
    assert by_handover.message_delivered is True


def test_another_delivery_rule_displaces_the_conclusion_rather_than_reversing_it() -> None:
    """Вытеснение общего правила — не вывод «не доставлено», а отказ выводить.

    Пункт 2 статьи 165.1 допускает иное правило в законе, сделке, обычае или
    практике сторон. Содержание такого правила модель не разбирает и поднимает
    флаг экспертизы.
    """
    evaluation = _evaluate(
        _facts(
            **QUALIFIED,
            handed_to_addressee_or_representative=True,
            transaction_sets_other_delivery_rule=True,
        )
    )

    assert evaluation.delivered_by_handover is True
    assert evaluation.default_rule_displaced is True
    assert evaluation.message_delivered is False
    assert evaluation.requires_human_message_assessment is True


def test_a_message_without_legal_consequences_is_not_qualified() -> None:
    """Не всякое письмо — юридически значимое сообщение."""
    evaluation = _evaluate(
        _facts(message_asserted=True, handed_to_addressee_or_representative=True)
    )

    assert evaluation.message_qualified is False
    assert evaluation.message_delivered is False
    assert evaluation.delivery_not_established is False
    assert evaluation.requires_human_message_assessment is False


def test_non_receipt_requires_arrival() -> None:
    """Невручение по обстоятельствам адресата имеет смысл лишь для поступившего.

    Не поступившее сообщение не вручено по обстоятельствам отправителя или связи,
    а не адресата.
    """
    with pytest.raises(ValueError, match="поступило"):
        _facts(**QUALIFIED, non_receipt_due_to_addressee=True)


def test_a_message_cannot_be_handed_over_and_unclaimed_at_once() -> None:
    """Вручение и риск неполучения — два разных пути, а не один."""
    with pytest.raises(ValueError, match="вручённым и невручённым"):
        _facts(
            **QUALIFIED,
            handed_to_addressee_or_representative=True,
            arrived_at_addressee=True,
            non_receipt_due_to_addressee=True,
        )


def test_benchmark_and_red_team_suites_pass() -> None:
    benchmark = run_messages_benchmark_suite()
    red_team = run_messages_red_team_suite()

    assert benchmark.failed == 0, [r.task_id for r in benchmark.results if not r.passed]
    assert benchmark.total >= 10
    assert red_team.unblocked == 0, [r.case_id for r in red_team.results if not r.blocked]
    assert red_team.total >= 6


def test_the_synthetic_artifact_replays_from_reviewed_evidence() -> None:
    artifact = build_synthetic_messages_evaluation_artifact()

    assert artifact.reviewed_evaluation.satisfiable is True
    assert artifact.benchmark_report.failed == 0
    assert artifact.red_team_report.unblocked == 0


def test_the_constraint_set_declares_what_it_executes() -> None:
    """Объявленный текст правил обязан совпасть с исполняемым.

    Сверка правил проверяет это по всему пакету; здесь — на самом институте,
    чтобы новый институт не появился уже с расхождением.
    """
    from causa.institutional.contracts.messages import MessagesEvidenceMappingResult

    mapping = MessagesEvidenceMappingResult(
        evidence_id="test",
        schema_version="test",
        mapping_version="test",
        facts=_facts(**QUALIFIED),
        legal_source_refs=["test-law"],
    )
    expressions = build_messages_constraint_set(mapping).expressions

    assert len(expressions) == 9
    assert any(line.startswith("message_delivered ==") for line in expressions)


def test_every_message_role_names_a_predicate_that_actually_exists() -> None:
    """Реестр ролей обязан ломаться, когда институт переименовал свой предикат.

    Роль связывает вывод статьи 165.1 с предикатом чужого института. Если тот
    предикат исчезнет или сменит имя, сверка молча перестанет что-либо
    проверять — и долг связности вернётся незамеченным.
    """
    from causa.institutional.contracts.messages import (
        MESSAGE_ROLE_PREDICATES,
        MessageRole,
    )
    from causa.institutional.contracts.reviewed_analysis import (
        ReviewedContractAnalysisRequest,
    )

    for role, (institute, predicate) in MESSAGE_ROLE_PREDICATES.items():
        field = ReviewedContractAnalysisRequest.model_fields.get(f"{institute}_evidence")
        assert field is not None, role
        enum_field = field.annotation.model_fields["assertions"]
        predicate_enum = enum_field.annotation.__args__[0].model_fields["predicate"].annotation
        assert predicate in {item.value for item in predicate_enum}, (role, predicate)

    # OTHER — единственная роль без предиката: сообщение, доставку которого
    # ни один институт отдельно не утверждает.
    assert set(MessageRole) - set(MESSAGE_ROLE_PREDICATES) == {MessageRole.OTHER}


def test_the_role_check_rejects_a_message_that_contradicts_its_institute() -> None:
    """Сверка, неспособная отвергнуть противоречие, ничего не проверяет."""
    import pytest as _pytest

    from causa.institutional.contracts.fact_consistency import FactConsistencyError
    from causa.institutional.contracts.messages import MessageRole
    from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
    from causa.institutional.contracts.synthetic_reviewed_analysis import (
        build_synthetic_supply_analysis_request,
        build_synthetic_supply_analysis_sources,
    )

    request = build_synthetic_supply_analysis_request()
    # Спорное сообщение доставлено (вручено под подпись), а предикат поставки о
    # доставке уведомления об отказе говорит обратное.
    evidence = request.messages_evidence.model_copy(
        update={"message_role": MessageRole.SUPPLY_UNILATERAL_REFUSAL_NOTICE}
    )

    with _pytest.raises(FactConsistencyError) as failure:
        run_reviewed_contract_analysis(
            request.model_copy(update={"messages_evidence": evidence}),
            build_synthetic_supply_analysis_sources(),
        )

    assert "message_delivery_agreement" in failure.value.keys
