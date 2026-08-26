from pydantic import BaseModel, Field

from causa.institutional.contracts.invalidity import (
    InvalidityEvaluation,
    InvalidityEvidenceMappingResult,
    InvalidityFactSet,
    build_invalidity_constraint_set,
    evaluate_invalidity_constraints,
)


class InvalidityEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: InvalidityFactSet
    expected_outcomes: dict[str, bool]


class InvalidityEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class InvalidityBenchmarkReport(BaseModel):
    id: str = "invalidity-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[InvalidityEvaluationResult] = Field(default_factory=list)


class InvalidityRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: InvalidityFactSet
    forbidden_outcomes: dict[str, bool]


class InvalidityRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class InvalidityRedTeamReport(BaseModel):
    id: str = "invalidity-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[InvalidityRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> InvalidityFactSet:
    values = {field_name: False for field_name in InvalidityFactSet.model_fields}
    values["transaction_concluded"] = True
    values.update(updates)
    return InvalidityFactSet(**values)


def _voidable_claim(**updates: bool) -> InvalidityFactSet:
    return _facts(
        invalidity_claim_made=True,
        claimant_is_transaction_party=True,
        claimant_rights_or_interests_affected=True,
        court_decision_entered_into_force=True,
        **updates,
    )


SYNTHETIC_INVALIDITY_BENCHMARKS = (
    InvalidityEvaluationTask(
        id="invalidity-bench-valid",
        title_ru="Основания недействительности отсутствуют",
        facts=_facts(),
        expected_outcomes={
            "transaction_presumed_effective": True,
            "contractual_effect_displaced": False,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-law-default",
        title_ru="Нарушение закона по общему правилу",
        facts=_facts(violates_law=True),
        expected_outcomes={"unlawful_voidable_ground": True, "unlawful_void_ground": False},
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-law-public",
        title_ru="Нарушение закона с посягательством на публичные интересы",
        facts=_facts(violates_law=True, public_interests_or_third_rights_affected=True),
        expected_outcomes={"unlawful_void_ground": True, "contractual_effect_displaced": True},
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-sham",
        title_ru="Мнимая сделка",
        facts=_facts(sham_intent_proven=True),
        expected_outcomes={"sham_void_ground": True, "void_ground_detected": True},
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-feigned",
        title_ru="Притворная и прикрываемая сделки",
        facts=_facts(feigned_intent_proven=True, disguised_transaction_identified=True),
        expected_outcomes={
            "feigned_void_ground": True,
            "disguised_transaction_rules_required": True,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-consent",
        title_ru="Отсутствие требуемого согласия при осведомленности контрагента",
        facts=_voidable_claim(required_consent_absent=True, counterparty_knew_consent_absent=True),
        expected_outcomes={"consent_voidable_ground": True, "voidable_invalidity_effective": True},
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-authority",
        title_ru="Нарушение ограничения полномочий",
        facts=_voidable_claim(
            authority_restriction_violated=True, counterparty_knew_authority_restriction=True
        ),
        expected_outcomes={
            "authority_voidable_ground": True,
            "voidable_invalidity_effective": True,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-mistake",
        title_ru="Существенное заблуждение",
        facts=_voidable_claim(material_mistake_proven=True),
        expected_outcomes={"mistake_voidable_ground": True, "voidable_invalidity_effective": True},
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-mistake-risk",
        title_ru="Риск заблуждения принят стороной",
        facts=_facts(material_mistake_proven=True, mistake_risk_assumed=True),
        expected_outcomes={"mistake_voidable_ground": False, "voidable_ground_detected": False},
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-deception",
        title_ru="Сделка под влиянием обмана",
        facts=_voidable_claim(deception_proven=True),
        expected_outcomes={"coercion_voidable_ground": True, "contractual_effect_displaced": True},
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-adverse",
        title_ru="Кабальная сделка",
        facts=_voidable_claim(
            adverse_circumstances_proven=True,
            extremely_unfavorable_terms_proven=True,
            counterparty_exploited_circumstances=True,
        ),
        expected_outcomes={"coercion_voidable_ground": True, "voidable_invalidity_effective": True},
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-incapacity",
        title_ru="Сделка недееспособного и реституция",
        facts=_facts(
            incapacitated_person_transaction=True,
            party_a_performed=True,
            return_in_kind_possible=True,
        ),
        expected_outcomes={"capacity_void_ground": True, "restitution_in_kind": True},
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-partial",
        title_ru="Отделимая недействительная часть",
        facts=_facts(
            law_expressly_makes_void=True,
            violates_law=True,
            invalid_part_separable=True,
            remainder_preserves_transaction_purpose=True,
        ),
        expected_outcomes={"partial_invalidity_only": True, "entire_transaction_affected": False},
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-limitation",
        title_ru="Истечение срока по оспоримой сделке",
        facts=_facts(
            invalidity_claim_made=True,
            claimant_is_transaction_party=True,
            claimant_rights_or_interests_affected=True,
            required_consent_absent=True,
            counterparty_knew_consent_absent=True,
            voidable_limitation_period_expired=True,
            court_decision_entered_into_force=True,
        ),
        expected_outcomes={
            "voidable_invalidity_prerequisites": False,
            "voidable_invalidity_effective": False,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-entrepreneurial-estoppel",
        title_ru="Пункт 2 статьи 431.1: сторона приняла исполнение и знала об основании",
        facts=_voidable_claim(
            violates_law=True,
            performance_accepted_under_entrepreneurial_contract=True,
            claimant_did_not_reciprocate_performance=True,
            claimant_knew_ground_at_performance_acceptance=True,
        ),
        expected_outcomes={
            "entrepreneurial_estoppel_bar": True,
            "voidable_invalidity_prerequisites": False,
            "voidable_invalidity_effective": False,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-entrepreneurial-estoppel-exception-179",
        title_ru="Исключение по статье 179: обман не подпадает под запрет 431.1",
        facts=_voidable_claim(
            deception_proven=True,
            performance_accepted_under_entrepreneurial_contract=True,
            claimant_did_not_reciprocate_performance=True,
            claimant_knew_ground_at_performance_acceptance=True,
        ),
        expected_outcomes={
            "entrepreneurial_estoppel_bar": False,
            "voidable_invalidity_effective": True,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-entrepreneurial-estoppel-exception-174-1",
        title_ru="Исключение по пункту 1 статьи 174: ограничение полномочий",
        facts=_voidable_claim(
            authority_restriction_violated=True,
            counterparty_knew_authority_restriction=True,
            performance_accepted_under_entrepreneurial_contract=True,
            claimant_did_not_reciprocate_performance=True,
            claimant_knew_ground_at_performance_acceptance=True,
        ),
        expected_outcomes={
            "entrepreneurial_estoppel_bar": False,
            "voidable_invalidity_effective": True,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-entrepreneurial-estoppel-not-174-2",
        title_ru="Пункт 2 статьи 174 запретом 431.1 не исключён",
        facts=_voidable_claim(
            obvious_entity_damage_proven=True,
            counterparty_knew_obvious_damage=True,
            performance_accepted_under_entrepreneurial_contract=True,
            claimant_did_not_reciprocate_performance=True,
            claimant_knew_ground_at_performance_acceptance=True,
        ),
        expected_outcomes={
            "entrepreneurial_estoppel_bar": True,
            "voidable_invalidity_effective": False,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-entrepreneurial-estoppel-public-interest",
        title_ru="Исключение: исполнение нарушает публичные интересы",
        facts=_voidable_claim(
            violates_law=True,
            performance_accepted_under_entrepreneurial_contract=True,
            claimant_did_not_reciprocate_performance=True,
            claimant_knew_ground_at_performance_acceptance=True,
            performance_violates_third_party_or_public_interests=True,
        ),
        expected_outcomes={
            "entrepreneurial_estoppel_bar": False,
            "voidable_invalidity_effective": True,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-statutory-disposal-prohibition",
        title_ru="Пункт 1 статьи 174.1: запрет из закона — ничтожность в части",
        facts=_facts(statutory_disposal_prohibition_violated=True),
        expected_outcomes={
            "disposal_prohibition_nullity": True,
            "void_ground_detected": True,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-judicial-prohibition-does-not-void",
        title_ru="Пункт 2 статьи 174.1: судебный запрет недействительности не влечёт",
        facts=_facts(
            violates_law=True,
            public_interests_or_third_rights_affected=True,
            judicial_disposal_prohibition_violated=True,
        ),
        expected_outcomes={
            "judicial_prohibition_does_not_void": True,
            "unlawful_void_ground": False,
            "unlawful_voidable_ground": False,
            "void_ground_detected": False,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-secured-creditor-rights-survive",
        title_ru="Приобретатель знал о запрете — права кредитора сохраняются",
        facts=_facts(
            judicial_disposal_prohibition_violated=True,
            acquirer_knew_of_disposal_prohibition=True,
        ),
        expected_outcomes={
            "secured_creditor_rights_survive": True,
            "void_ground_detected": False,
        },
    ),
    InvalidityEvaluationTask(
        id="invalidity-bench-prohibition-unaware-acquirer",
        title_ru="Приобретатель не знал о запрете — права кредитора не выводятся",
        facts=_facts(judicial_disposal_prohibition_violated=True),
        expected_outcomes={
            "judicial_prohibition_does_not_void": True,
            "secured_creditor_rights_survive": False,
        },
    ),
)


SYNTHETIC_INVALIDITY_RED_TEAM_CASES = (
    InvalidityRedTeamCase(
        id="invalidity-red-law-nullity",
        title_ru="Объявить любое нарушение закона ничтожным",
        facts=_facts(violates_law=True),
        forbidden_outcomes={"unlawful_void_ground": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-no-knowledge-consent",
        title_ru="Оспорить согласие без осведомленности контрагента",
        facts=_facts(required_consent_absent=True),
        forbidden_outcomes={"consent_voidable_ground": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-no-knowledge-authority",
        title_ru="Оспорить полномочия без знания другой стороны",
        facts=_facts(authority_restriction_violated=True),
        forbidden_outcomes={"authority_voidable_ground": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-no-standing",
        title_ru="Признать оспоримую сделку без надлежащего заявителя",
        facts=_facts(
            required_consent_absent=True,
            counterparty_knew_consent_absent=True,
            invalidity_claim_made=True,
        ),
        forbidden_outcomes={"voidable_invalidity_prerequisites": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-no-judgment",
        title_ru="Считать основание оспоримости уже действующей недействительностью",
        facts=_facts(
            required_consent_absent=True,
            counterparty_knew_consent_absent=True,
            invalidity_claim_made=True,
            claimant_is_transaction_party=True,
            claimant_rights_or_interests_affected=True,
        ),
        forbidden_outcomes={"voidable_invalidity_effective": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-estoppel",
        title_ru="Игнорировать подтверждение оспоримой сделки",
        facts=_facts(
            required_consent_absent=True,
            counterparty_knew_consent_absent=True,
            invalidity_claim_made=True,
            claimant_is_transaction_party=True,
            claimant_rights_or_interests_affected=True,
            party_confirmed_voidable_transaction=True,
            ground_known_at_confirmation=True,
            court_decision_entered_into_force=True,
        ),
        forbidden_outcomes={"voidable_invalidity_effective": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-mistake-risk",
        title_ru="Игнорировать принятый риск заблуждения",
        facts=_facts(material_mistake_proven=True, mistake_risk_assumed=True),
        forbidden_outcomes={"mistake_voidable_ground": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-adverse-incomplete",
        title_ru="Признать кабальность только по тяжелым обстоятельствам",
        facts=_facts(adverse_circumstances_proven=True),
        forbidden_outcomes={"coercion_voidable_ground": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-feigned-no-disguise",
        title_ru="Применить правила прикрываемой сделки без ее идентификации",
        facts=_facts(feigned_intent_proven=True),
        forbidden_outcomes={"disguised_transaction_rules_required": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-void-limit",
        title_ru="Применить последствия ничтожности после истечения срока",
        facts=_facts(
            sham_intent_proven=True,
            execution_started=True,
            void_limitation_period_expired=True,
            nullity_consequences_requested=True,
            claimant_is_transaction_party=True,
        ),
        forbidden_outcomes={"nullity_consequences_prerequisites": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-entire",
        title_ru="Уничтожить всю сделку при отделимости условия",
        facts=_facts(
            violates_law=True,
            law_expressly_makes_void=True,
            invalid_part_separable=True,
            remainder_preserves_transaction_purpose=True,
        ),
        forbidden_outcomes={"entire_transaction_affected": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-restitution-no-performance",
        title_ru="Назначить реституцию без исполнения",
        facts=_facts(sham_intent_proven=True),
        forbidden_outcomes={"restitution_required": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-money-no-value",
        title_ru="Назначить денежную реституцию без оценки стоимости",
        facts=_facts(sham_intent_proven=True, party_a_performed=True),
        forbidden_outcomes={"monetary_restitution_issue": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-damages-no-causation",
        title_ru="Присудить дополнительные убытки без причинной связи",
        facts=_facts(sham_intent_proven=True, additional_damages_claimed=True),
        forbidden_outcomes={"additional_damages_issue": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-estoppel-without-acceptance",
        title_ru="Применить запрет 431.1 без принятого исполнения",
        facts=_voidable_claim(
            violates_law=True,
            claimant_did_not_reciprocate_performance=False,
            claimant_knew_ground_at_performance_acceptance=False,
        ),
        forbidden_outcomes={"entrepreneurial_estoppel_bar": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-estoppel-without-knowledge",
        title_ru="Применить запрет 431.1, не зная об основании при получении исполнения",
        facts=_voidable_claim(
            violates_law=True,
            performance_accepted_under_entrepreneurial_contract=True,
            claimant_did_not_reciprocate_performance=True,
        ),
        forbidden_outcomes={"entrepreneurial_estoppel_bar": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-estoppel-over-mistake",
        title_ru="Распространить запрет 431.1 на существенное заблуждение (статья 178)",
        facts=_voidable_claim(
            material_mistake_proven=True,
            performance_accepted_under_entrepreneurial_contract=True,
            claimant_did_not_reciprocate_performance=True,
            claimant_knew_ground_at_performance_acceptance=True,
        ),
        forbidden_outcomes={"entrepreneurial_estoppel_bar": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-article-168-from-judicial-prohibition",
        title_ru="Вывести основание статьи 168 из запрета пункта 2 статьи 174.1",
        facts=_facts(
            violates_law=True,
            public_interests_or_third_rights_affected=True,
            judicial_disposal_prohibition_violated=True,
        ),
        forbidden_outcomes={"unlawful_void_ground": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-creditor-rights-without-knowledge",
        title_ru="Дать кредитору права против приобретателя, не знавшего о запрете",
        facts=_facts(judicial_disposal_prohibition_violated=True),
        forbidden_outcomes={"secured_creditor_rights_survive": True},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-suppress-168-for-ordinary-violation",
        title_ru="Снять основание статьи 168 с обычного нарушения закона",
        facts=_facts(violates_law=True, public_interests_or_third_rights_affected=True),
        forbidden_outcomes={"unlawful_void_ground": False},
    ),
    InvalidityRedTeamCase(
        id="invalidity-red-statutory-prohibition-as-non-void",
        title_ru="Отнести запрет из закона к пункту 2 и не выводить ничтожности",
        facts=_facts(statutory_disposal_prohibition_violated=True),
        forbidden_outcomes={"disposal_prohibition_nullity": False},
    ),
)


def _evaluate(facts: InvalidityFactSet, artifact_id: str) -> InvalidityEvaluation:
    mapping = InvalidityEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-invalidity-law"],
    )
    constraint_set = build_invalidity_constraint_set(mapping)
    return evaluate_invalidity_constraints(constraint_set, facts)


def _outcomes(evaluation: InvalidityEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_invalidity_benchmark_suite() -> InvalidityBenchmarkReport:
    results = []
    for task in SYNTHETIC_INVALIDITY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            InvalidityEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return InvalidityBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_invalidity_red_team_suite() -> InvalidityRedTeamReport:
    results = []
    for case in SYNTHETIC_INVALIDITY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            InvalidityRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return InvalidityRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
