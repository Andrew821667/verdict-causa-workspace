"""Дело несёт несколько юридически значимых сообщений, а не одно.

## Какой долг закрывают эти проверки

`layer_connectivity` держал институт сообщений единственным с вердиктом
«заблокирован контрактом данных»: доставка решает, наступили ли последствия
отказа от договора, зачёта, приостановления встречного исполнения, — но контракт
данных давал один блок доказательств на институт. Какое из девятнадцати
уведомлений пакета проверено, вывод не сообщал, а остальные шли на веру.

Теперь запрос несёт `additional_messages_evidence`, и каждое сообщение сверяется
со своим предикатом своего института. Ключ сверки несёт роль, поэтому
расхождение называет, **какое** уведомление расошлось, а не просто «уведомление».
"""

import pytest

from causa.institutional.contracts.fact_consistency import (
    FACT_CONSISTENCY_VOCABULARY,
    FactConsistencyError,
)
from causa.institutional.contracts.messages import (
    MESSAGE_ROLE_LABELS_RU,
    MESSAGE_ROLE_PREDICATES,
    MessageRole,
    message_delivery_consistency_key,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)


@pytest.fixture(scope="module")
def sources():
    return build_synthetic_supply_analysis_sources()


def _message_block(template, block_id: str, role: MessageRole, *, delivered: bool):
    """Блок доказательств об одном сообщении, доставленном или нет."""
    wanted = {
        "handed_to_addressee_or_representative": delivered,
        "arrived_at_addressee": delivered,
    }
    assertions = tuple(
        assertion.model_copy(update={"value": wanted[assertion.predicate.value]})
        if assertion.predicate.value in wanted
        else assertion
        for assertion in template.assertions
    )
    return template.model_copy(
        update={"id": block_id, "message_role": role, "assertions": assertions}
    )


def test_every_role_has_a_russian_name_and_a_consistency_key() -> None:
    """Роль без имени дала бы расхождение, которое не называет уведомление."""
    assert set(MESSAGE_ROLE_LABELS_RU) == set(MESSAGE_ROLE_PREDICATES)

    for role, label in MESSAGE_ROLE_LABELS_RU.items():
        key = message_delivery_consistency_key(role)
        assert key in FACT_CONSISTENCY_VOCABULARY, role
        fact_ru, anchor_ru = FACT_CONSISTENCY_VOCABULARY[key]
        assert label in fact_ru, role
        assert "165.1" in anchor_ru


def test_a_role_is_required_to_build_a_key() -> None:
    """Сверять доставку сообщения, роль которого не названа, не с чем."""
    with pytest.raises(ValueError, match="Роль сообщения не названа"):
        message_delivery_consistency_key(MessageRole.OTHER)


def test_a_case_without_extra_messages_is_unchanged(sources) -> None:
    """Старый контракт данных остался валидным: поле необязательное."""
    result = run_reviewed_contract_analysis(build_synthetic_supply_analysis_request(), sources)

    assert result.additional_messages_evaluations == ()
    assert result.additional_messages_constraint_sets == ()
    assert result.additional_messages_evidence_mappings == ()


def test_each_message_is_checked_against_its_own_institute(sources) -> None:
    """Главная проверка: расхождение называет уведомление, а не «уведомление».

    До этой правки оба расхождения несли один ключ `message_delivery_agreement`
    и одну строку, и юрист не мог сказать, какое из сообщений разошлось.
    """
    request = build_synthetic_supply_analysis_request()
    template = request.messages_evidence
    request = request.model_copy(
        update={
            "additional_messages_evidence": (
                _message_block(template, "msg-setoff", MessageRole.SET_OFF_NOTICE, delivered=True),
                _message_block(
                    template, "msg-suspension", MessageRole.SUSPENSION_NOTICE, delivered=True
                ),
            )
        }
    )

    with pytest.raises(FactConsistencyError) as failure:
        run_reviewed_contract_analysis(request, sources)

    assert failure.value.keys == [
        "message_delivery_agreement:set_off_notice",
        "message_delivery_agreement:suspension_notice",
    ]
    lines = "\n".join(mismatch.line_ru for mismatch in failure.value.mismatches)
    assert "заявление о зачёте" in lines
    assert "приостановлении встречного исполнения" in lines


def test_messages_that_agree_with_their_institutes_pass(sources) -> None:
    """Согласованные сообщения проходят, и их разборы попадают в результат."""
    request = build_synthetic_supply_analysis_request()
    template = request.messages_evidence
    # Демонстрационное дело утверждает, что ни одно из этих уведомлений не
    # доставлено, поэтому согласованный блок обязан говорить то же.
    request = request.model_copy(
        update={
            "additional_messages_evidence": (
                _message_block(template, "msg-setoff", MessageRole.SET_OFF_NOTICE, delivered=False),
                _message_block(
                    template, "msg-foreclosure", MessageRole.FORECLOSURE_NOTICE, delivered=False
                ),
            )
        }
    )

    result = run_reviewed_contract_analysis(request, sources)

    assert len(result.additional_messages_evaluations) == 2
    assert all(
        evaluation.message_delivered is False
        for evaluation in result.additional_messages_evaluations
    )
    # Артефакт обязан воспроизводиться: модель перепроверяет каждый разбор.
    assert len(result.additional_messages_constraint_sets) == 2


def test_two_blocks_about_one_notice_are_refused(sources) -> None:
    """Выбирать, какой блок считать спорным, система не станет."""
    request = build_synthetic_supply_analysis_request()
    template = request.messages_evidence
    request = request.model_copy(
        update={
            "additional_messages_evidence": (
                _message_block(template, "msg-a", MessageRole.SET_OFF_NOTICE, delivered=True),
                _message_block(template, "msg-b", MessageRole.SET_OFF_NOTICE, delivered=False),
            )
        }
    )

    with pytest.raises(ValueError, match="несколько блоков об одном и том же уведомлении"):
        run_reviewed_contract_analysis(request, sources)


def test_an_extra_block_without_a_role_is_refused(sources) -> None:
    """Дополнительный блок добавлен ради привязки к уведомлению дела."""
    request = build_synthetic_supply_analysis_request()
    template = request.messages_evidence
    request = request.model_copy(
        update={
            "additional_messages_evidence": (template.model_copy(update={"id": "msg-nowhere"}),)
        }
    )

    with pytest.raises(ValueError, match="обязаны назвать роль"):
        run_reviewed_contract_analysis(request, sources)


def test_extra_messages_of_another_case_are_refused(sources) -> None:
    """Сообщение чужого дела в карте этого дела было бы незаметно."""
    request = build_synthetic_supply_analysis_request()
    template = request.messages_evidence
    foreign = _message_block(
        template, "msg-foreign", MessageRole.SET_OFF_NOTICE, delivered=False
    ).model_copy(update={"case_id": "case-another-1"})

    with pytest.raises(ValueError, match="case_id does not match"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"additional_messages_evidence": (foreign,)}), sources
        )


def test_an_unreviewed_extra_message_is_refused(sources) -> None:
    """Непроверенное доказательство не становится фактом из-за того, что оно второе."""
    from causa.core.bootstrap import BootstrapReviewStatus

    request = build_synthetic_supply_analysis_request()
    template = request.messages_evidence
    draft = _message_block(
        template, "msg-draft", MessageRole.SET_OFF_NOTICE, delivered=False
    ).model_copy(update={"review_status": BootstrapReviewStatus.DRAFT})

    with pytest.raises(ValueError, match="Additional messages evidence msg-draft"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"additional_messages_evidence": (draft,)}), sources
        )


def test_the_human_flag_rises_from_any_message(sources) -> None:
    """Пункт 2 статьи 165.1: иное правило доставки требует юриста.

    Флаг обязан подниматься от любого сообщения дела, а не только от спорного:
    иначе второе сообщение с вытесненным общим правилом прошло бы молча.
    """
    request = build_synthetic_supply_analysis_request()
    template = request.messages_evidence
    displaced = _message_block(
        template, "msg-displaced", MessageRole.SET_OFF_NOTICE, delivered=False
    )
    displaced = displaced.model_copy(
        update={
            "assertions": tuple(
                assertion.model_copy(update={"value": True})
                if assertion.predicate.value == "transaction_sets_other_delivery_rule"
                else assertion
                for assertion in displaced.assertions
            )
        }
    )

    result = run_reviewed_contract_analysis(
        request.model_copy(update={"additional_messages_evidence": (displaced,)}), sources
    )

    assert result.additional_messages_evaluations[0].requires_human_message_assessment is True
    assert result.requires_human_resolution is True
