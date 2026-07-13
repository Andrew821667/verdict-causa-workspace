from enum import Enum
from pydantic import BaseModel, Field


class TranslationLevel(str, Enum):
    EXECUTIVE = "executive"
    PROFESSIONAL = "professional"
    FORENSIC = "forensic"


class TranslationAssertionCode(str, Enum):
    SOURCE_APPLICABLE = "source_applicable"
    VALID_OFFER = "valid_offer"
    CONTRACT_CONCLUDED_PREREQUISITES = "contract_concluded_prerequisites"
    CONDUCT_ACCEPTANCE_VALID = "conduct_acceptance_valid"
    COUNTEROFFER_DETECTED = "counteroffer_detected"
    NON_CONCLUSION_OBJECTION_BARRED = "non_conclusion_objection_barred"
    TRANSACTION_PRESUMED_EFFECTIVE = "transaction_presumed_effective"
    VOID_GROUND_DETECTED = "void_ground_detected"
    VOIDABLE_GROUND_DETECTED = "voidable_ground_detected"
    VOIDABLE_INVALIDITY_EFFECTIVE = "voidable_invalidity_effective"
    INVALIDITY_ESTOPPEL_BAR = "invalidity_estoppel_bar"
    PARTIAL_INVALIDITY_ONLY = "partial_invalidity_only"
    DISGUISED_TRANSACTION_RULES = "disguised_transaction_rules"
    INVALIDITY_RESTITUTION_REQUIRED = "invalidity_restitution_required"
    SECURITY_MECHANISM_DETECTED = "security_mechanism_detected"
    SECURITY_ENFORCEMENT_AVAILABLE = "security_enforcement_available"
    PLEDGE_FORECLOSURE_PREREQUISITES = "pledge_foreclosure_prerequisites"
    RETENTION_AVAILABLE = "retention_available"
    SURETY_ENFORCEABLE = "surety_enforceable"
    GUARANTEE_DEMAND_PAYABLE = "guarantee_demand_payable"
    DEPOSIT_PROVEN = "deposit_proven"
    SECURITY_PAYMENT_CREDIT_AVAILABLE = "security_payment_credit_available"
    ASSIGNMENT_EFFECTIVE = "assignment_effective"
    DEBT_TRANSFER_EFFECTIVE = "debt_transfer_effective"
    CONTRACT_TRANSFER_EFFECTIVE = "contract_transfer_effective"
    PARTIES_CHANGED_NOT_DISCHARGED = "parties_changed_not_discharged"
    PROPER_PERFORMANCE_DISCHARGE = "proper_performance_discharge"
    ACCORD_DISCHARGE = "accord_discharge"
    SETOFF_EFFECTIVE = "setoff_effective"
    NOVATION_EFFECTIVE = "novation_effective"
    DEBT_FORGIVENESS_EFFECTIVE = "debt_forgiveness_effective"
    IMPOSSIBILITY_DISCHARGE = "impossibility_discharge"
    OBLIGATION_DISCHARGED_FULL = "obligation_discharged_full"
    DYNAMICS_ACCRUED_CLAIMS_PRESERVED = "dynamics_accrued_claims_preserved"
    PERFORMANCE_PROPER = "performance_proper"
    PARTIAL_PERFORMANCE_ACCEPTANCE_REQUIRED = "partial_performance_acceptance_required"
    THIRD_PARTY_PERFORMANCE_ACCEPTANCE_REQUIRED = "third_party_performance_acceptance_required"
    SOLIDARY_OBLIGATION = "solidary_obligation"
    COUNTERPERFORMANCE_SUSPENSION_AVAILABLE = "counterperformance_suspension_available"
    PERFORMANCE_DAMAGES_AVAILABLE = "performance_damages_available"
    SPECIFIC_PERFORMANCE_AVAILABLE = "specific_performance_available"
    ARTICLE_395_INTEREST_AVAILABLE = "article_395_interest_available"
    CREDITOR_IN_DELAY = "creditor_in_delay"
    INDEMNITY_PREREQUISITES = "indemnity_prerequisites"
    INTENTIONAL_LIABILITY_EXCLUSION_INVALID = "intentional_liability_exclusion_invalid"
    SUPPLY_CONTRACT_QUALIFIED = "supply_contract_qualified"
    SUPPLY_ACCEPTANCE_DUTIES_SATISFIED = "supply_acceptance_duties_satisfied"
    SUPPLY_MAKEUP_DELIVERY_REQUIRED = "supply_makeup_delivery_required"
    SUPPLY_UNILATERAL_REFUSAL_EFFECTIVE = "supply_unilateral_refusal_effective"
    SUPPLY_PRICE_DAMAGES_AVAILABLE = "supply_price_damages_available"
    CONTRACT_CONTINUES_UNCHANGED = "contract_continues_unchanged"
    EFFECTIVE_MODIFICATION = "effective_modification"
    EFFECTIVE_TERMINATION = "effective_termination"
    JUDICIAL_TERMINATION_PREREQUISITES = "judicial_termination_prerequisites"
    CHANGED_CIRCUMSTANCES_GROUND = "changed_circumstances_ground"
    INVALID_UNILATERAL_ACTION = "invalid_unilateral_action"
    ACCRUED_CLAIMS_PRESERVED = "accrued_claims_preserved"
    DUE_DATE_MISSED = "due_date_missed"
    BREACH_ISSUE = "breach_issue"
    LATE_PERFORMANCE_ISSUE = "late_performance_issue"
    DEFECT_ISSUE = "defect_issue"
    PAYMENT_DEFAULT_ISSUE = "payment_default_issue"
    DAMAGES_REMEDY_AVAILABLE = "damages_remedy_available"
    CAUSATION_EVIDENCE_GAP = "causation_evidence_gap"
    LIMITATION_BAR = "limitation_bar"
    AUTHORITY_WINNER = "authority_winner"
    HUMAN_RESOLUTION_REQUIRED = "human_resolution_required"
    COUNTERFACTUAL_SENSITIVITY = "counterfactual_sensitivity"
    FAULT_REBUTTED = "fault_rebutted"
    FORCE_MAJEURE_QUALIFIED = "force_majeure_qualified"
    LIABILITY_EXEMPTION_PREREQUISITES = "liability_exemption_prerequisites"
    LIABILITY_ISSUE = "liability_issue"
    PENALTY_REDUCTION_PREREQUISITES = "penalty_reduction_prerequisites"
    INTENTIONAL_EXCLUSION_INVALID = "intentional_exclusion_invalid"


class TranslationAssertion(BaseModel):
    code: TranslationAssertionCode
    value: bool | str
    text_ru: str
    source_refs: list[str] = Field(default_factory=list)


class TranslationArtifact(BaseModel):
    id: str
    trace_id: str
    level: TranslationLevel
    locale: str = "ru-RU"
    template_version: str
    template_content_hash: str | None = None
    policy_snapshot_id: str | None = None
    policy_content_hash: str | None = None
    text: str
    assertions: list[TranslationAssertion] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    faithfulness_checked: bool = False
    faithfulness_passed: bool = False
    usability_checked: bool = False
    usability_passed: bool = False
