"""Таксономия противоречий в договорных делах.

`CONTRACT_CONTRADICTION_TYPES` — словарь имён для разметки противоречий внутри
одного института; он описывает предметную область и ничего не проверяет сам.

`CROSS_INSTITUTE_CONTRADICTION_TYPES` устроен иначе: каждое имя из этого набора
обязано проверяться слоем сверки `general_consistency` и соответствовать полю
его оценки. Соответствие закреплено тестом
`test_every_declared_cross_institute_type_is_checked`, а достижимость каждого
типа в полном конвейере — тестом
`test_every_declared_conflict_fires_end_to_end`. Поэтому набор не может ни
снова стать перечнем без потребителей, ни содержать сверку, которая объявлена,
но сработать не способна.
"""

CROSS_INSTITUTE_CONTRADICTION_TYPES = (
    "capacity_invalidity_conflict",
    "entity_capacity_invalidity_conflict",
    "limited_capacity_invalidity_conflict",
    "minor_capacity_invalidity_conflict",
    "consent_invalidity_conflict",
    "circulation_lawfulness_conflict",
    "formation_form_observance_conflict",
    "circulation_public_interest_conflict",
)


CONTRACT_CONTRADICTION_TYPES = [
    "performance_status_conflict",
    "delivery_date_conflict",
    "payment_status_conflict",
    "authority_conflict",
    "temporal_validity_conflict",
    "offer_intent_conflict",
    "essential_terms_conflict",
    "acceptance_scope_conflict",
    "contract_form_conflict",
    "modification_termination_target_conflict",
    "unilateral_right_conflict",
    "termination_effective_date_conflict",
    "accrued_claim_survival_conflict",
    "void_voidable_classification_conflict",
    "invalidity_standing_conflict",
    "invalidity_effect_conflict",
    "restitution_scope_conflict",
    "accessory_independent_security_conflict",
    "pledge_opposability_conflict",
    "pledge_enforcement_route_conflict",
    "surety_scope_termination_conflict",
    "guarantee_demand_compliance_conflict",
    "deposit_advance_classification_conflict",
    "security_payment_credit_return_conflict",
    "assignment_validity_notice_conflict",
    "assignment_debtor_defense_conflict",
    "debt_transfer_release_conflict",
    "party_change_discharge_conflict",
    "performance_discharge_accrued_claim_conflict",
    "accord_agreement_performance_conflict",
    "setoff_prerequisite_conflict",
    "novation_intent_conflict",
    "forgiveness_objection_conflict",
    "impossibility_risk_conflict",
    "liquidation_successor_conflict",
    "proper_performance_element_conflict",
    "partial_performance_acceptance_conflict",
    "third_party_personal_performance_conflict",
    "solidary_share_conflict",
    "counterperformance_suspension_conflict",
    "damages_causation_amount_conflict",
    "specific_performance_possibility_conflict",
    "article_395_penalty_overlap_conflict",
    "debtor_creditor_delay_conflict",
    "indemnity_breach_classification_conflict",
]
