"""Benchmark и red-team для модели юридически значимых сообщений."""

from pydantic import BaseModel, Field

from causa.institutional.contracts.messages import (
    MessagesConstraintSet,
    MessagesEvaluation,
    MessagesEvidenceMappingResult,
    MessagesFactSet,
    build_messages_constraint_set,
    evaluate_messages_constraints,
)


class MessagesEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: MessagesFactSet
    expected_outcomes: dict[str, bool]


class MessagesEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class MessagesBenchmarkReport(BaseModel):
    id: str = "messages-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[MessagesEvaluationResult] = Field(default_factory=list)


class MessagesRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: MessagesFactSet
    forbidden_outcomes: dict[str, bool]


class MessagesRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class MessagesRedTeamReport(BaseModel):
    id: str = "messages-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[MessagesRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> MessagesFactSet:
    values = {field_name: False for field_name in MessagesFactSet.model_fields}
    values.update(updates)
    return MessagesFactSet(**values)


_QUALIFIED = {"message_asserted": True, "consequences_attached_by_law_or_transaction": True}
_ADDRESSED = {
    "sent_to_statutory_or_agreed_address": True,
    "sender_and_addressee_identifiable": True,
    "form_matches_message_nature": True,
}


SYNTHETIC_MESSAGES_BENCHMARKS = (
    MessagesEvaluationTask(
        id="messages-bench-not-qualified",
        title_ru="Сообщение есть, но последствий для другого лица закон и сделка с ним не связывают",
        facts=_facts(message_asserted=True, handed_to_addressee_or_representative=True),
        expected_outcomes={
            "message_qualified": False,
            "message_delivered": False,
            "delivery_not_established": False,
            "requires_human_message_assessment": False,
        },
    ),
    MessagesEvaluationTask(
        id="messages-bench-handover",
        title_ru="Вручено адресату: адрес отправления значения не имеет",
        facts=_facts(**_QUALIFIED, handed_to_addressee_or_representative=True),
        expected_outcomes={
            "delivered_by_handover": True,
            "properly_addressed": False,
            "message_delivered": True,
            "consequences_effective": True,
            "requires_human_message_assessment": False,
        },
    ),
    MessagesEvaluationTask(
        id="messages-bench-representative",
        title_ru="Вручено представителю адресата — то же последствие, что и вручение самому адресату",
        facts=_facts(**_QUALIFIED, **_ADDRESSED, handed_to_addressee_or_representative=True),
        expected_outcomes={
            "delivered_by_handover": True,
            "message_delivered": True,
            "consequences_effective": True,
        },
    ),
    MessagesEvaluationTask(
        id="messages-bench-addressee-risk",
        title_ru="Не вручено, но поступило по надлежащему адресу: риск неполучения на адресате",
        facts=_facts(
            **_QUALIFIED,
            **_ADDRESSED,
            arrived_at_addressee=True,
            non_receipt_due_to_addressee=True,
        ),
        expected_outcomes={
            "delivered_by_handover": False,
            "delivered_by_addressee_risk": True,
            "message_delivered": True,
            "consequences_effective": True,
            "requires_human_message_assessment": True,
        },
    ),
    MessagesEvaluationTask(
        id="messages-bench-arrived-not-addressee-fault",
        title_ru="Поступило, но невручение не зависело от адресата: доставка не выводится",
        facts=_facts(**_QUALIFIED, **_ADDRESSED, arrived_at_addressee=True),
        expected_outcomes={
            "delivered_by_addressee_risk": False,
            "message_delivered": False,
            "delivery_not_established": True,
        },
    ),
    MessagesEvaluationTask(
        id="messages-bench-wrong-address",
        title_ru="Поступило и не получено по вине адресата, но послано не по надлежащему адресу",
        facts=_facts(
            **_QUALIFIED,
            sender_and_addressee_identifiable=True,
            form_matches_message_nature=True,
            arrived_at_addressee=True,
            non_receipt_due_to_addressee=True,
        ),
        expected_outcomes={
            "properly_addressed": False,
            "delivered_by_addressee_risk": False,
            "message_delivered": False,
            "delivery_not_established": True,
        },
    ),
    MessagesEvaluationTask(
        id="messages-bench-sender-unidentifiable",
        title_ru="Нельзя достоверно установить, от кого исходило сообщение",
        facts=_facts(
            **_QUALIFIED,
            sent_to_statutory_or_agreed_address=True,
            form_matches_message_nature=True,
            arrived_at_addressee=True,
            non_receipt_due_to_addressee=True,
        ),
        expected_outcomes={
            "properly_addressed": False,
            "delivered_by_addressee_risk": False,
            "message_delivered": False,
        },
    ),
    MessagesEvaluationTask(
        id="messages-bench-transaction-other-rule",
        title_ru="Сделка установила иное правило доставки: общее правило вытеснено",
        facts=_facts(
            **_QUALIFIED,
            handed_to_addressee_or_representative=True,
            transaction_sets_other_delivery_rule=True,
        ),
        expected_outcomes={
            "delivered_by_handover": True,
            "default_rule_displaced": True,
            "message_delivered": False,
            "consequences_effective": False,
            "requires_human_message_assessment": True,
        },
    ),
    MessagesEvaluationTask(
        id="messages-bench-custom-other-rule",
        title_ru="Иное следует из практики, установившейся во взаимоотношениях сторон",
        facts=_facts(
            **_QUALIFIED,
            **_ADDRESSED,
            arrived_at_addressee=True,
            non_receipt_due_to_addressee=True,
            custom_or_practice_sets_other_delivery_rule=True,
        ),
        expected_outcomes={
            "delivered_by_addressee_risk": True,
            "default_rule_displaced": True,
            "message_delivered": False,
        },
    ),
    MessagesEvaluationTask(
        id="messages-bench-nothing-sent",
        title_ru="Сообщение квалифицировано, но не поступило и не вручено",
        facts=_facts(**_QUALIFIED, **_ADDRESSED),
        expected_outcomes={
            "message_qualified": True,
            "message_delivered": False,
            "delivery_not_established": True,
            "requires_human_message_assessment": True,
        },
    ),
)


SYNTHETIC_MESSAGES_RED_TEAM_CASES = (
    MessagesRedTeamCase(
        id="messages-red-arrival-alone",
        title_ru="Поступление само по себе не делает сообщение доставленным",
        facts=_facts(**_QUALIFIED, **_ADDRESSED, arrived_at_addressee=True),
        forbidden_outcomes={"message_delivered": True, "consequences_effective": True},
    ),
    MessagesRedTeamCase(
        id="messages-red-address-alone",
        title_ru="Надлежащий адрес сам по себе не заменяет ни вручения, ни поступления",
        facts=_facts(**_QUALIFIED, **_ADDRESSED),
        forbidden_outcomes={"delivered_by_addressee_risk": True, "message_delivered": True},
    ),
    MessagesRedTeamCase(
        id="messages-red-risk-without-address",
        title_ru="Риск неполучения не перекладывается на адресата при ненадлежащем адресе",
        facts=_facts(
            **_QUALIFIED,
            arrived_at_addressee=True,
            non_receipt_due_to_addressee=True,
        ),
        forbidden_outcomes={"delivered_by_addressee_risk": True},
    ),
    MessagesRedTeamCase(
        id="messages-red-consequences-without-qualification",
        title_ru="Последствия не наступают у сообщения, с которым закон их не связывает",
        facts=_facts(
            message_asserted=True,
            **_ADDRESSED,
            handed_to_addressee_or_representative=True,
        ),
        forbidden_outcomes={"consequences_effective": True, "message_delivered": True},
    ),
    MessagesRedTeamCase(
        id="messages-red-displaced-rule-still-delivers",
        title_ru="Вытесненное правило не может служить основанием вывода о доставке",
        facts=_facts(
            **_QUALIFIED,
            **_ADDRESSED,
            handed_to_addressee_or_representative=True,
            law_sets_other_delivery_rule=True,
        ),
        forbidden_outcomes={"message_delivered": True, "consequences_effective": True},
    ),
    MessagesRedTeamCase(
        id="messages-red-silent-non-delivery",
        title_ru="Недоказанная доставка не проходит молча — она поднимает флаг экспертизы",
        facts=_facts(**_QUALIFIED, **_ADDRESSED, arrived_at_addressee=True),
        forbidden_outcomes={"requires_human_message_assessment": False},
    ),
)


def _evaluate(facts: MessagesFactSet, artifact_id: str) -> MessagesEvaluation:
    mapping = MessagesEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-messages-law"],
    )
    constraints: MessagesConstraintSet = build_messages_constraint_set(mapping)
    return evaluate_messages_constraints(constraints, facts)


def _outcomes(evaluation: MessagesEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_messages_benchmark_suite() -> MessagesBenchmarkReport:
    results = []
    for task in SYNTHETIC_MESSAGES_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            MessagesEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return MessagesBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_messages_red_team_suite() -> MessagesRedTeamReport:
    results = []
    for case in SYNTHETIC_MESSAGES_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            MessagesRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return MessagesRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
