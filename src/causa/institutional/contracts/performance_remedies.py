from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PERFORMANCE_REMEDIES_EVIDENCE_SCHEMA_VERSION = "contracts.performance-remedies-evidence.v0"
PERFORMANCE_REMEDIES_MAPPING_VERSION = "contracts-reviewed-performance-remedies-to-facts-v0"
PERFORMANCE_REMEDIES_MODEL_VERSION = "contracts-performance-remedies-articles-309-328-393-4061-v0"


class PerformanceRemediesEvidencePredicate(str, Enum):
    OBLIGATION_EXISTS = "obligation_exists"
    BREACH_ESTABLISHED = "breach_established"
    PERFORMANCE_TENDERED = "performance_tendered"
    SUBJECT_CONFORMS = "subject_conforms"
    QUALITY_QUANTITY_CONFORM = "quality_quantity_conform"
    PERFORMANCE_AT_DUE_TIME = "performance_at_due_time"
    PERFORMANCE_AT_PROPER_PLACE = "performance_at_proper_place"
    PERFORMANCE_TO_PROPER_RECIPIENT = "performance_to_proper_recipient"
    DEBTOR_REQUESTED_AUTHORITY_PROOF = "debtor_requested_authority_proof"
    AUTHORITY_PROOF_PROVIDED = "authority_proof_provided"
    PARTIAL_PERFORMANCE_TENDERED = "partial_performance_tendered"
    PARTIAL_PERFORMANCE_ALLOWED = "partial_performance_allowed"
    MONETARY_OBLIGATION = "monetary_obligation"
    ALL_PARTIES_ACTING_IN_BUSINESS = "all_parties_acting_in_business"
    EARLY_PERFORMANCE_TENDERED = "early_performance_tendered"
    EARLY_PERFORMANCE_ALLOWED = "early_performance_allowed"
    THIRD_PARTY_PERFORMANCE_TENDERED = "third_party_performance_tendered"
    DEBTOR_ASSIGNED_THIRD_PARTY_PERFORMANCE = "debtor_assigned_third_party_performance"
    DEBTOR_MONETARY_DELAY = "debtor_monetary_delay"
    THIRD_PARTY_PROPERTY_RIGHT_AT_RISK = "third_party_property_right_at_risk"
    PERSONAL_PERFORMANCE_REQUIRED = "personal_performance_required"
    DEMAND_OBLIGATION = "demand_obligation"
    CREDITOR_DEMAND_DELIVERED = "creditor_demand_delivered"
    STATUTORY_OR_AGREED_GRACE_ELAPSED = "statutory_or_agreed_grace_elapsed"
    CREDITOR_PREREQUISITE_ACTION_REQUIRED = "creditor_prerequisite_action_required"
    CREDITOR_PREREQUISITE_ACTION_COMPLETED = "creditor_prerequisite_action_completed"
    PAYMENT_RECEIVED_BY_CREDITOR_BANK = "payment_received_by_creditor_bank"
    MULTIPLE_HOMOGENEOUS_DEBTS = "multiple_homogeneous_debts"
    DEBTOR_DESIGNATED_DEBT = "debtor_designated_debt"
    DEBT_DESIGNATION_VALID = "debt_designation_valid"
    PAYMENT_INSUFFICIENT = "payment_insufficient"
    EXTRA_EXPENSES_CAUSED_BY_CREDITOR = "extra_expenses_caused_by_creditor"
    ALTERNATIVE_OBLIGATION = "alternative_obligation"
    CHOICE_HOLDER_SELECTED = "choice_holder_selected"
    FACULTATIVE_OBLIGATION = "facultative_obligation"
    FACULTATIVE_SUBSTITUTE_TENDERED = "facultative_substitute_tendered"
    MULTIPLE_DEBTORS = "multiple_debtors"
    SOLIDARITY_BY_LAW_OR_CONTRACT = "solidarity_by_law_or_contract"
    JOINT_BUSINESS_OBLIGATION = "joint_business_obligation"
    ONE_SOLIDARY_DEBTOR_PERFORMED_FULL = "one_solidary_debtor_performed_full"
    CREDITOR_CLAIMED_ONE_SOLIDARY_DEBTOR = "creditor_claimed_one_solidary_debtor"
    INTERNAL_RECOURSE_SHARES_PROVEN = "internal_recourse_shares_proven"
    RECIPROCAL_OBLIGATIONS = "reciprocal_obligations"
    COUNTERPERFORMANCE_DUE = "counterperformance_due"
    COUNTERPARTY_FAILED_DUE_PERFORMANCE = "counterparty_failed_due_performance"
    CLEAR_FUTURE_NONPERFORMANCE = "clear_future_nonperformance"
    SUSPENSION_NOTICE_DELIVERED = "suspension_notice_delivered"
    REFUSAL_NOTICE_DELIVERED = "refusal_notice_delivered"
    OWN_COUNTERPERFORMANCE_TENDERED = "own_counterperformance_tendered"
    SPECIFIC_CLAIM_OVERRIDE = "specific_claim_override"
    LOSS_CLAIMED = "loss_claimed"
    ACTUAL_LOSS_PROVEN = "actual_loss_proven"
    LOST_PROFIT_CLAIMED = "lost_profit_claimed"
    LOST_PROFIT_MEASURES_PROVEN = "lost_profit_measures_proven"
    CAUSATION_PROVEN = "causation_proven"
    REASONABLE_AMOUNT_BASIS = "reasonable_amount_basis"
    EXACT_AMOUNT_NOT_ESTABLISHED = "exact_amount_not_established"
    CREDITOR_MITIGATION_TAKEN = "creditor_mitigation_taken"
    CREDITOR_CONTRIBUTED_TO_LOSS = "creditor_contributed_to_loss"
    REPLACEMENT_TRANSACTION_MADE = "replacement_transaction_made"
    REPLACEMENT_TRANSACTION_REASONABLE = "replacement_transaction_reasonable"
    CURRENT_PRICE_AVAILABLE = "current_price_available"
    SPECIFIC_PERFORMANCE_CLAIMED = "specific_performance_claimed"
    PERFORMANCE_OBJECTIVELY_POSSIBLE = "performance_objectively_possible"
    CREDITOR_LOST_INTEREST_DUE_DELAY = "creditor_lost_interest_due_delay"
    SUBSTITUTE_PERFORMANCE_BY_CREDITOR = "substitute_performance_by_creditor"
    SUBSTITUTE_COSTS_REASONABLE_DOCUMENTED = "substitute_costs_reasonable_documented"
    INDIVIDUAL_SPECIFIC_THING_DUE = "individual_specific_thing_due"
    THING_TRANSFERRED_TO_PROTECTED_THIRD_PARTY = "thing_transferred_to_protected_third_party"
    MONETARY_DELAY = "monetary_delay"
    ARTICLE_395_CLAIMED = "article_395_claimed"
    PENALTY_FOR_SAME_MONETARY_DELAY = "penalty_for_same_monetary_delay"
    ARTICLE_395_CONTRACT_OVERRIDE = "article_395_contract_override"
    STATUTORY_RATE_BASIS_PROVEN = "statutory_rate_basis_proven"
    INTEREST_PERIOD_PROVEN = "interest_period_proven"
    DAMAGES_ABOVE_INTEREST_CLAIMED = "damages_above_interest_claimed"
    DAMAGES_ABOVE_INTEREST_PROVEN = "damages_above_interest_proven"
    THIRD_PARTY_CAUSED_BREACH = "third_party_caused_breach"
    DEBTOR_RESPONSIBLE_FOR_THIRD_PARTY = "debtor_responsible_for_third_party"
    PRIMARY_DEBTOR_CLAIMED = "primary_debtor_claimed"
    PRIMARY_REFUSED_OR_NO_RESPONSE = "primary_refused_or_no_response"
    SUBSIDIARY_DEBTOR_CLAIMED = "subsidiary_debtor_claimed"
    LIABILITY_LIMIT_CLAUSE_OR_LAW = "liability_limit_clause_or_law"
    INTENTIONAL_BREACH = "intentional_breach"
    ADVANCE_INTENTIONAL_LIABILITY_EXCLUSION = "advance_intentional_liability_exclusion"
    DEBTOR_DELAY = "debtor_delay"
    CREDITOR_REFUSED_PROPER_PERFORMANCE = "creditor_refused_proper_performance"
    CREDITOR_OMITTED_REQUIRED_ACTION = "creditor_omitted_required_action"
    CREDITOR_DELAY_LOSS_PROVEN = "creditor_delay_loss_proven"
    INDEMNITY_AGREEMENT = "indemnity_agreement"
    INDEMNITY_BUSINESS_CONTEXT = "indemnity_business_context"
    INDEMNITY_CLEAR = "indemnity_clear"
    INDEMNITY_TRIGGER_UNRELATED_TO_BREACH = "indemnity_trigger_unrelated_to_breach"
    INDEMNITY_LOSS_OCCURRED = "indemnity_loss_occurred"
    INDEMNITY_AMOUNT_OR_METHOD_AGREED = "indemnity_amount_or_method_agreed"
    INDEMNITY_BAD_FAITH_EVENT_CAUSED = "indemnity_bad_faith_event_caused"


REQUIRED_PERFORMANCE_REMEDIES_PREDICATES = frozenset(PerformanceRemediesEvidencePredicate)


class PerformanceRemediesEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: PerformanceRemediesEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedPerformanceRemediesEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PERFORMANCE_REMEDIES_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[PerformanceRemediesEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=3)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedPerformanceRemediesEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Performance-remedies evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Performance-remedies evidence contains duplicate legal source refs.")
        return self


class PerformanceRemediesFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    obligation_exists: bool
    breach_established: bool
    performance_tendered: bool
    subject_conforms: bool
    quality_quantity_conform: bool
    performance_at_due_time: bool
    performance_at_proper_place: bool
    performance_to_proper_recipient: bool
    debtor_requested_authority_proof: bool
    authority_proof_provided: bool
    partial_performance_tendered: bool
    partial_performance_allowed: bool
    monetary_obligation: bool
    all_parties_acting_in_business: bool
    early_performance_tendered: bool
    early_performance_allowed: bool
    third_party_performance_tendered: bool
    debtor_assigned_third_party_performance: bool
    debtor_monetary_delay: bool
    third_party_property_right_at_risk: bool
    personal_performance_required: bool
    demand_obligation: bool
    creditor_demand_delivered: bool
    statutory_or_agreed_grace_elapsed: bool
    creditor_prerequisite_action_required: bool
    creditor_prerequisite_action_completed: bool
    payment_received_by_creditor_bank: bool
    multiple_homogeneous_debts: bool
    debtor_designated_debt: bool
    debt_designation_valid: bool
    payment_insufficient: bool
    extra_expenses_caused_by_creditor: bool
    alternative_obligation: bool
    choice_holder_selected: bool
    facultative_obligation: bool
    facultative_substitute_tendered: bool
    multiple_debtors: bool
    solidarity_by_law_or_contract: bool
    joint_business_obligation: bool
    one_solidary_debtor_performed_full: bool
    creditor_claimed_one_solidary_debtor: bool
    internal_recourse_shares_proven: bool
    reciprocal_obligations: bool
    counterperformance_due: bool
    counterparty_failed_due_performance: bool
    clear_future_nonperformance: bool
    suspension_notice_delivered: bool
    refusal_notice_delivered: bool
    own_counterperformance_tendered: bool
    specific_claim_override: bool
    loss_claimed: bool
    actual_loss_proven: bool
    lost_profit_claimed: bool
    lost_profit_measures_proven: bool
    causation_proven: bool
    reasonable_amount_basis: bool
    exact_amount_not_established: bool
    creditor_mitigation_taken: bool
    creditor_contributed_to_loss: bool
    replacement_transaction_made: bool
    replacement_transaction_reasonable: bool
    current_price_available: bool
    specific_performance_claimed: bool
    performance_objectively_possible: bool
    creditor_lost_interest_due_delay: bool
    substitute_performance_by_creditor: bool
    substitute_costs_reasonable_documented: bool
    individual_specific_thing_due: bool
    thing_transferred_to_protected_third_party: bool
    monetary_delay: bool
    article_395_claimed: bool
    penalty_for_same_monetary_delay: bool
    article_395_contract_override: bool
    statutory_rate_basis_proven: bool
    interest_period_proven: bool
    damages_above_interest_claimed: bool
    damages_above_interest_proven: bool
    third_party_caused_breach: bool
    debtor_responsible_for_third_party: bool
    primary_debtor_claimed: bool
    primary_refused_or_no_response: bool
    subsidiary_debtor_claimed: bool
    liability_limit_clause_or_law: bool
    intentional_breach: bool
    advance_intentional_liability_exclusion: bool
    debtor_delay: bool
    creditor_refused_proper_performance: bool
    creditor_omitted_required_action: bool
    creditor_delay_loss_proven: bool
    indemnity_agreement: bool
    indemnity_business_context: bool
    indemnity_clear: bool
    indemnity_trigger_unrelated_to_breach: bool
    indemnity_loss_occurred: bool
    indemnity_amount_or_method_agreed: bool
    indemnity_bad_faith_event_caused: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "PerformanceRemediesFactSet":
        if self.breach_established and not self.obligation_exists:
            raise ValueError("A breach requires an existing obligation.")
        if self.partial_performance_tendered and not self.performance_tendered:
            raise ValueError("Partial performance requires tendered performance.")
        if self.early_performance_tendered and not self.performance_tendered:
            raise ValueError("Early performance requires tendered performance.")
        if self.authority_proof_provided and not self.debtor_requested_authority_proof:
            raise ValueError("Authority proof requires a debtor request in this model.")
        if self.debtor_monetary_delay and not self.monetary_obligation:
            raise ValueError("Monetary delay requires a monetary obligation.")
        if self.creditor_demand_delivered and not self.demand_obligation:
            raise ValueError("A demand requires a demand obligation.")
        if self.statutory_or_agreed_grace_elapsed and not self.creditor_demand_delivered:
            raise ValueError("The grace period requires a delivered demand.")
        if (
            self.creditor_prerequisite_action_completed
            and not self.creditor_prerequisite_action_required
        ):
            raise ValueError("A completed prerequisite requires a prerequisite action.")
        if self.payment_received_by_creditor_bank and not self.monetary_obligation:
            raise ValueError("Bank receipt requires a monetary obligation.")
        if self.debtor_designated_debt and not self.multiple_homogeneous_debts:
            raise ValueError("Debt designation requires multiple homogeneous debts.")
        if self.debt_designation_valid and not self.debtor_designated_debt:
            raise ValueError("A valid designation requires debtor designation.")
        if self.choice_holder_selected and not self.alternative_obligation:
            raise ValueError("A choice requires an alternative obligation.")
        if self.facultative_substitute_tendered and not self.facultative_obligation:
            raise ValueError("A substitute requires a facultative obligation.")
        if self.one_solidary_debtor_performed_full and not self.multiple_debtors:
            raise ValueError("Solidary performance requires multiple debtors.")
        if self.internal_recourse_shares_proven and not self.one_solidary_debtor_performed_full:
            raise ValueError("Recourse shares require full performance by one debtor.")
        if self.counterperformance_due and not self.reciprocal_obligations:
            raise ValueError("Counterperformance requires reciprocal obligations.")
        if self.suspension_notice_delivered and not self.reciprocal_obligations:
            raise ValueError("Suspension notice requires reciprocal obligations.")
        if self.refusal_notice_delivered and not self.reciprocal_obligations:
            raise ValueError("Refusal notice requires reciprocal obligations.")
        if self.actual_loss_proven and not self.loss_claimed:
            raise ValueError("Proven actual loss requires a loss claim.")
        if self.exact_amount_not_established and not self.loss_claimed:
            raise ValueError("An inexact loss amount requires a loss claim.")
        if self.lost_profit_measures_proven and not self.lost_profit_claimed:
            raise ValueError("Lost-profit measures require a lost-profit claim.")
        if self.replacement_transaction_reasonable and not self.replacement_transaction_made:
            raise ValueError("Replacement reasonableness requires a replacement transaction.")
        if (
            self.substitute_costs_reasonable_documented
            and not self.substitute_performance_by_creditor
        ):
            raise ValueError("Substitute costs require substitute performance.")
        if self.article_395_claimed and not self.monetary_delay:
            raise ValueError("An article 395 claim requires monetary delay.")
        if self.damages_above_interest_proven and not self.damages_above_interest_claimed:
            raise ValueError("Excess damages proof requires an excess-damages claim.")
        if self.debtor_responsible_for_third_party and not self.third_party_caused_breach:
            raise ValueError("Third-party responsibility requires third-party breach causation.")
        if self.primary_refused_or_no_response and not self.primary_debtor_claimed:
            raise ValueError("Primary refusal requires a claim to the primary debtor.")
        if self.advance_intentional_liability_exclusion and not self.liability_limit_clause_or_law:
            raise ValueError("Intentional exclusion requires a liability limitation.")
        if self.intentional_breach and not self.breach_established:
            raise ValueError("Intentional breach requires an established breach.")
        if self.creditor_delay_loss_proven and not (
            self.creditor_refused_proper_performance or self.creditor_omitted_required_action
        ):
            raise ValueError("Creditor-delay loss requires creditor delay conduct.")
        if self.indemnity_clear and not self.indemnity_agreement:
            raise ValueError("Clear indemnity terms require an indemnity agreement.")
        if self.indemnity_loss_occurred and not self.indemnity_agreement:
            raise ValueError("Indemnity loss requires an indemnity agreement.")
        if self.indemnity_amount_or_method_agreed and not self.indemnity_agreement:
            raise ValueError("Indemnity amount requires an indemnity agreement.")
        return self


class PerformanceRemediesFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class PerformanceRemediesEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: PerformanceRemediesFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[PerformanceRemediesFactProvenance] = Field(default_factory=list)


class PerformanceRemediesConstraintSet(BaseModel):
    id: str
    model_version: str = PERFORMANCE_REMEDIES_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class PerformanceRemediesEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    proper_performance: bool
    recipient_authority_gap: bool
    partial_performance_acceptance_required: bool
    partial_performance_refusal_available: bool
    early_performance_permitted: bool
    third_party_performance_acceptance_required: bool
    third_party_subrogation_issue: bool
    demand_obligation_due: bool
    creditor_prerequisite_delay: bool
    bank_payment_completed: bool
    debtor_allocation_effective: bool
    default_payment_allocation_issue: bool
    creditor_extra_expense_liability_issue: bool
    alternative_choice_effective: bool
    facultative_substitute_effective: bool
    solidary_obligation: bool
    solidary_external_discharge: bool
    solidary_internal_recourse: bool
    counterperformance_suspension_available: bool
    counterperformance_refusal_available: bool
    counterparty_specific_claim_barred: bool
    damages_prerequisites_satisfied: bool
    lost_profit_supported: bool
    judicial_loss_estimation_required: bool
    creditor_fault_reduction_issue: bool
    replacement_transaction_damages: bool
    current_price_damages: bool
    specific_performance_available: bool
    substitute_performance_cost_recovery: bool
    individual_thing_claim_available: bool
    article_395_interest_available: bool
    article_395_penalty_conflict: bool
    excess_monetary_damages_available: bool
    debtor_answers_for_third_party: bool
    subsidiary_liability_prerequisites: bool
    liability_limit_issue: bool
    intentional_liability_exclusion_invalid: bool
    debtor_in_delay: bool
    creditor_in_delay: bool
    debtor_delay_excluded_by_creditor: bool
    creditor_delay_damages_issue: bool
    indemnity_prerequisites_satisfied: bool
    indemnity_bad_faith_bar: bool
    competing_remedy_paths: bool
    requires_human_performance_remedies_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_performance_remedies_evidence(
    evidence: ReviewedPerformanceRemediesEvidence,
) -> PerformanceRemediesEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Performance-remedies evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Performance-remedies evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value
        for predicate in REQUIRED_PERFORMANCE_REMEDIES_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed performance-remedies evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_PERFORMANCE_REMEDIES_PREDICATES
    }
    return PerformanceRemediesEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PERFORMANCE_REMEDIES_MAPPING_VERSION,
        facts=PerformanceRemediesFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            PerformanceRemediesFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_PERFORMANCE_REMEDIES_PREDICATES,
                key=lambda item: item.value,
            )
        ],
    )


def build_performance_remedies_constraint_set(
    mapping: PerformanceRemediesEvidenceMappingResult,
) -> PerformanceRemediesConstraintSet:
    return PerformanceRemediesConstraintSet(
        id=f"performance-remedies-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "proper_performance == obligation_exists AND tendered AND conforming_subject_quality_quantity_time_place_recipient",
            "third_party_acceptance == third_party_tendered AND statutory_acceptance_ground AND NOT personal_performance",
            "solidary_obligation == multiple_debtors AND (law_or_contract OR joint_business_obligation)",
            "counterperformance_suspension == reciprocal_due AND nonperformance_risk AND delivered_notice",
            "damages == breach AND claimed_loss AND proven_loss_type AND causation AND reasonable_amount_basis",
            "article_395_interest == monetary_delay AND claim AND rate_period AND NOT same-delay-penalty-conflict",
            "creditor_delay == refused_proper_performance OR omitted_required_action",
            "indemnity == business_agreement AND clear_nonbreach_trigger AND occurred_loss AND amount_method AND NOT bad_faith",
        ],
    )


def evaluate_performance_remedies_constraints(
    constraint_set: PerformanceRemediesConstraintSet,
    facts: PerformanceRemediesFactSet,
) -> PerformanceRemediesEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in PerformanceRemediesFactSet.model_fields
    }
    outputs = {
        field_name: Bool(field_name)
        for field_name in PerformanceRemediesEvaluation.model_fields
        if field_name not in {"constraint_set_id", "satisfiable", "reasons_ru", "warnings_ru"}
    }
    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    solver.add(
        outputs["proper_performance"]
        == And(
            variables["obligation_exists"],
            variables["performance_tendered"],
            variables["subject_conforms"],
            variables["quality_quantity_conform"],
            variables["performance_at_due_time"],
            variables["performance_at_proper_place"],
            variables["performance_to_proper_recipient"],
            Not(variables["partial_performance_tendered"]),
        )
    )
    solver.add(
        outputs["recipient_authority_gap"]
        == And(
            variables["performance_tendered"],
            variables["debtor_requested_authority_proof"],
            Not(variables["authority_proof_provided"]),
        )
    )
    partial_acceptance_ground = Or(
        variables["partial_performance_allowed"], variables["monetary_obligation"]
    )
    solver.add(
        outputs["partial_performance_acceptance_required"]
        == And(variables["partial_performance_tendered"], partial_acceptance_ground)
    )
    solver.add(
        outputs["partial_performance_refusal_available"]
        == And(variables["partial_performance_tendered"], Not(partial_acceptance_ground))
    )
    solver.add(
        outputs["early_performance_permitted"]
        == And(
            variables["early_performance_tendered"],
            Or(
                Not(variables["all_parties_acting_in_business"]),
                variables["early_performance_allowed"],
            ),
        )
    )
    third_party_ground = Or(
        variables["debtor_assigned_third_party_performance"],
        variables["debtor_monetary_delay"],
        variables["third_party_property_right_at_risk"],
    )
    solver.add(
        outputs["third_party_performance_acceptance_required"]
        == And(
            variables["third_party_performance_tendered"],
            third_party_ground,
            Not(variables["personal_performance_required"]),
        )
    )
    solver.add(
        outputs["third_party_subrogation_issue"]
        == outputs["third_party_performance_acceptance_required"]
    )
    solver.add(
        outputs["demand_obligation_due"]
        == And(
            variables["demand_obligation"],
            variables["creditor_demand_delivered"],
            variables["statutory_or_agreed_grace_elapsed"],
        )
    )
    solver.add(
        outputs["creditor_prerequisite_delay"]
        == And(
            variables["creditor_prerequisite_action_required"],
            Not(variables["creditor_prerequisite_action_completed"]),
        )
    )
    solver.add(
        outputs["bank_payment_completed"]
        == And(variables["monetary_obligation"], variables["payment_received_by_creditor_bank"])
    )
    solver.add(
        outputs["debtor_allocation_effective"]
        == And(
            variables["multiple_homogeneous_debts"],
            variables["payment_insufficient"],
            variables["debtor_designated_debt"],
            variables["debt_designation_valid"],
        )
    )
    solver.add(
        outputs["default_payment_allocation_issue"]
        == And(
            variables["multiple_homogeneous_debts"],
            variables["payment_insufficient"],
            Not(outputs["debtor_allocation_effective"]),
        )
    )
    solver.add(
        outputs["creditor_extra_expense_liability_issue"]
        == variables["extra_expenses_caused_by_creditor"]
    )
    solver.add(
        outputs["alternative_choice_effective"]
        == And(variables["alternative_obligation"], variables["choice_holder_selected"])
    )
    solver.add(
        outputs["facultative_substitute_effective"]
        == And(variables["facultative_obligation"], variables["facultative_substitute_tendered"])
    )
    solver.add(
        outputs["solidary_obligation"]
        == And(
            variables["multiple_debtors"],
            Or(
                variables["solidarity_by_law_or_contract"],
                variables["joint_business_obligation"],
            ),
        )
    )
    solver.add(
        outputs["solidary_external_discharge"]
        == And(outputs["solidary_obligation"], variables["one_solidary_debtor_performed_full"])
    )
    solver.add(
        outputs["solidary_internal_recourse"]
        == And(outputs["solidary_external_discharge"], variables["internal_recourse_shares_proven"])
    )
    counterparty_default = Or(
        variables["counterparty_failed_due_performance"],
        variables["clear_future_nonperformance"],
    )
    solver.add(
        outputs["counterperformance_suspension_available"]
        == And(
            variables["reciprocal_obligations"],
            variables["counterperformance_due"],
            counterparty_default,
            variables["suspension_notice_delivered"],
        )
    )
    solver.add(
        outputs["counterperformance_refusal_available"]
        == And(
            variables["reciprocal_obligations"],
            variables["counterperformance_due"],
            variables["counterparty_failed_due_performance"],
            variables["refusal_notice_delivered"],
        )
    )
    solver.add(
        outputs["counterparty_specific_claim_barred"]
        == And(
            variables["reciprocal_obligations"],
            Not(variables["own_counterperformance_tendered"]),
            Not(variables["specific_claim_override"]),
        )
    )
    proven_loss_type = Or(
        variables["actual_loss_proven"],
        And(
            variables["lost_profit_claimed"],
            variables["lost_profit_measures_proven"],
        ),
    )
    solver.add(
        outputs["damages_prerequisites_satisfied"]
        == And(
            variables["breach_established"],
            variables["loss_claimed"],
            proven_loss_type,
            variables["causation_proven"],
            variables["reasonable_amount_basis"],
        )
    )
    solver.add(
        outputs["lost_profit_supported"]
        == And(
            outputs["damages_prerequisites_satisfied"],
            variables["lost_profit_claimed"],
            variables["lost_profit_measures_proven"],
        )
    )
    solver.add(
        outputs["judicial_loss_estimation_required"]
        == And(
            outputs["damages_prerequisites_satisfied"],
            variables["exact_amount_not_established"],
        )
    )
    solver.add(
        outputs["creditor_fault_reduction_issue"]
        == And(
            variables["breach_established"],
            Or(
                variables["creditor_contributed_to_loss"],
                Not(variables["creditor_mitigation_taken"]),
            ),
        )
    )
    solver.add(
        outputs["replacement_transaction_damages"]
        == And(
            variables["breach_established"],
            variables["replacement_transaction_made"],
            variables["replacement_transaction_reasonable"],
        )
    )
    solver.add(
        outputs["current_price_damages"]
        == And(
            variables["breach_established"],
            Not(variables["replacement_transaction_made"]),
            variables["current_price_available"],
        )
    )
    solver.add(
        outputs["specific_performance_available"]
        == And(
            variables["obligation_exists"],
            variables["specific_performance_claimed"],
            variables["performance_objectively_possible"],
            Not(variables["creditor_lost_interest_due_delay"]),
        )
    )
    solver.add(
        outputs["substitute_performance_cost_recovery"]
        == And(
            variables["breach_established"],
            variables["substitute_performance_by_creditor"],
            variables["substitute_costs_reasonable_documented"],
        )
    )
    solver.add(
        outputs["individual_thing_claim_available"]
        == And(
            variables["individual_specific_thing_due"],
            Not(variables["thing_transferred_to_protected_third_party"]),
        )
    )
    solver.add(
        outputs["article_395_penalty_conflict"]
        == And(
            variables["monetary_delay"],
            variables["article_395_claimed"],
            variables["penalty_for_same_monetary_delay"],
            Not(variables["article_395_contract_override"]),
        )
    )
    solver.add(
        outputs["article_395_interest_available"]
        == And(
            variables["monetary_delay"],
            variables["article_395_claimed"],
            variables["statutory_rate_basis_proven"],
            variables["interest_period_proven"],
            Not(outputs["article_395_penalty_conflict"]),
        )
    )
    solver.add(
        outputs["excess_monetary_damages_available"]
        == And(
            outputs["article_395_interest_available"],
            variables["damages_above_interest_claimed"],
            variables["damages_above_interest_proven"],
        )
    )
    solver.add(
        outputs["debtor_answers_for_third_party"]
        == And(
            variables["third_party_caused_breach"],
            variables["debtor_responsible_for_third_party"],
        )
    )
    solver.add(
        outputs["subsidiary_liability_prerequisites"]
        == And(
            variables["primary_debtor_claimed"],
            variables["primary_refused_or_no_response"],
            variables["subsidiary_debtor_claimed"],
        )
    )
    solver.add(
        outputs["liability_limit_issue"]
        == And(variables["breach_established"], variables["liability_limit_clause_or_law"])
    )
    solver.add(
        outputs["intentional_liability_exclusion_invalid"]
        == And(
            variables["intentional_breach"],
            variables["advance_intentional_liability_exclusion"],
        )
    )
    creditor_delay = Or(
        variables["creditor_refused_proper_performance"],
        variables["creditor_omitted_required_action"],
        outputs["creditor_prerequisite_delay"],
    )
    solver.add(outputs["creditor_in_delay"] == creditor_delay)
    solver.add(
        outputs["debtor_delay_excluded_by_creditor"]
        == And(variables["debtor_delay"], outputs["creditor_in_delay"])
    )
    solver.add(
        outputs["debtor_in_delay"]
        == And(variables["debtor_delay"], Not(outputs["creditor_in_delay"]))
    )
    solver.add(
        outputs["creditor_delay_damages_issue"]
        == And(outputs["creditor_in_delay"], variables["creditor_delay_loss_proven"])
    )
    solver.add(
        outputs["indemnity_bad_faith_bar"]
        == And(variables["indemnity_agreement"], variables["indemnity_bad_faith_event_caused"])
    )
    solver.add(
        outputs["indemnity_prerequisites_satisfied"]
        == And(
            variables["indemnity_agreement"],
            variables["indemnity_business_context"],
            variables["indemnity_clear"],
            variables["indemnity_trigger_unrelated_to_breach"],
            variables["indemnity_loss_occurred"],
            variables["indemnity_amount_or_method_agreed"],
            Not(outputs["indemnity_bad_faith_bar"]),
        )
    )
    remedy_paths = [
        outputs["damages_prerequisites_satisfied"],
        outputs["specific_performance_available"],
        outputs["substitute_performance_cost_recovery"],
        outputs["individual_thing_claim_available"],
        outputs["article_395_interest_available"],
        outputs["indemnity_prerequisites_satisfied"],
    ]
    solver.add(
        outputs["competing_remedy_paths"]
        == Or(
            *[
                And(left, right)
                for index, left in enumerate(remedy_paths)
                for right in remedy_paths[index + 1 :]
            ]
        )
    )
    solver.add(
        outputs["requires_human_performance_remedies_assessment"]
        == Or(
            outputs["recipient_authority_gap"],
            outputs["third_party_performance_acceptance_required"],
            outputs["default_payment_allocation_issue"],
            outputs["solidary_obligation"],
            outputs["counterperformance_suspension_available"],
            outputs["counterperformance_refusal_available"],
            outputs["counterparty_specific_claim_barred"],
            outputs["damages_prerequisites_satisfied"],
            outputs["judicial_loss_estimation_required"],
            outputs["creditor_fault_reduction_issue"],
            outputs["specific_performance_available"],
            outputs["article_395_interest_available"],
            outputs["article_395_penalty_conflict"],
            outputs["subsidiary_liability_prerequisites"],
            outputs["liability_limit_issue"],
            outputs["creditor_in_delay"],
            outputs["indemnity_prerequisites_satisfied"],
            outputs["indemnity_bad_faith_bar"],
            outputs["competing_remedy_paths"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return PerformanceRemediesEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            **{
                field_name: False
                for field_name in outputs
                if field_name != "requires_human_performance_remedies_assessment"
            },
            requires_human_performance_remedies_assessment=True,
            reasons_ru=["Набор фактов об исполнении и средствах защиты противоречив."],
            warnings_ru=["Требуется повторная проверка исходных данных юристом."],
        )
    model = solver.model()
    values = {
        field_name: bool(model.eval(variable, model_completion=True))
        for field_name, variable in outputs.items()
    }
    reasons_ru = []
    if values["proper_performance"]:
        reasons_ru.append("Подтверждены формальные признаки надлежащего исполнения.")
    if values["counterperformance_suspension_available"]:
        reasons_ru.append("Подтверждены предпосылки приостановления встречного исполнения.")
    if values["damages_prerequisites_satisfied"]:
        reasons_ru.append("Подтверждены формальные предпосылки требования убытков.")
    if values["article_395_interest_available"]:
        reasons_ru.append("Подтверждены формальные предпосылки процентов по статье 395 ГК РФ.")
    if values["creditor_in_delay"]:
        reasons_ru.append("Выявлены формальные признаки просрочки кредитора.")
    if not reasons_ru:
        reasons_ru.append("Активный путь исполнения или средства защиты не подтвержден.")
    return PerformanceRemediesEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        **values,
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель не рассчитывает сумму долга, убытков, процентов, регресса или возмещения потерь.",
            "Разумность расходов, причинная связь, упущенная выгода и снижение ответственности требуют оценки доказательств.",
            "Специальные правила отдельных договоров, банкротства, потребительских и публичных отношений проверяются отдельно.",
        ],
    )
