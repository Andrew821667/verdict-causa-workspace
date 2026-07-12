from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


OBLIGATION_DYNAMICS_EVIDENCE_SCHEMA_VERSION = "contracts.obligation-dynamics-evidence.v0"
OBLIGATION_DYNAMICS_MAPPING_VERSION = "contracts-reviewed-obligation-dynamics-to-facts-v0"
OBLIGATION_DYNAMICS_MODEL_VERSION = "contracts-obligation-dynamics-articles-382-419-v0"


class ObligationDynamicsEvidencePredicate(str, Enum):
    OBLIGATION_EXISTS = "obligation_exists"
    OBLIGATION_BREACHED = "obligation_breached"
    ACCRUED_CLAIMS_EXIST = "accrued_claims_exist"
    PARTIAL_TERMINATION_INTENDED = "partial_termination_intended"
    ASSIGNMENT_AGREEMENT_CONCLUDED = "assignment_agreement_concluded"
    ASSIGNMENT_FORM_OBSERVED = "assignment_form_observed"
    ASSIGNED_CLAIM_EXISTS = "assigned_claim_exists"
    ASSIGNED_CLAIM_IDENTIFIED = "assigned_claim_identified"
    FUTURE_CLAIM_DETERMINABLE = "future_claim_determinable"
    CLAIM_PERSONAL_TO_CREDITOR = "claim_personal_to_creditor"
    ASSIGNMENT_PROHIBITED_BY_LAW = "assignment_prohibited_by_law"
    CONTRACT_RESTRICTS_ASSIGNMENT = "contract_restricts_assignment"
    DEBTOR_CONSENT_REQUIRED = "debtor_consent_required"
    DEBTOR_CONSENT_OBTAINED = "debtor_consent_obtained"
    DEBTOR_NOTIFIED = "debtor_notified"
    PROOF_OF_TRANSFER_PROVIDED = "proof_of_transfer_provided"
    DEBTOR_PERFORMED_ORIGINAL_BEFORE_NOTICE = "debtor_performed_original_before_notice"
    DEBTOR_DEFENSE_EXISTED_AT_NOTICE = "debtor_defense_existed_at_notice"
    DEBTOR_COUNTERCLAIM_EXISTED_AT_NOTICE = "debtor_counterclaim_existed_at_notice"
    CEDENT_TRANSFERRED_DOCUMENTS = "cedent_transferred_documents"
    CLAIM_INVALID = "claim_invalid"
    CEDENT_KNEW_CLAIM_INVALID = "cedent_knew_claim_invalid"
    CEDENT_GUARANTEED_DEBTOR_PERFORMANCE = "cedent_guaranteed_debtor_performance"
    DEBTOR_FAILED_AFTER_ASSIGNMENT = "debtor_failed_after_assignment"
    DEBT_TRANSFER_AGREEMENT_CONCLUDED = "debt_transfer_agreement_concluded"
    DEBT_TRANSFER_FORM_OBSERVED = "debt_transfer_form_observed"
    NEW_DEBTOR_IDENTIFIED = "new_debtor_identified"
    CREDITOR_CONSENTED_DEBT_TRANSFER = "creditor_consented_debt_transfer"
    ORIGINAL_DEBTOR_RELEASED = "original_debtor_released"
    CUMULATIVE_DEBT_ASSUMPTION_AGREED = "cumulative_debt_assumption_agreed"
    BUSINESS_DEBT_ASSUMPTION = "business_debt_assumption"
    NEW_DEBTOR_DEFENSE_EXISTS = "new_debtor_defense_exists"
    SECURITY_PROVIDER_CONSENTED_NEW_DEBTOR = "security_provider_consented_new_debtor"
    CONTRACT_TRANSFER_AGREED = "contract_transfer_agreed"
    ALL_PARTIES_CONSENTED_CONTRACT_TRANSFER = "all_parties_consented_contract_transfer"
    PERFORMANCE_RENDERED = "performance_rendered"
    PERFORMANCE_ACCEPTED_AS_PROPER = "performance_accepted_as_proper"
    PERFORMANCE_PARTIAL = "performance_partial"
    CREDITOR_ISSUED_RECEIPT = "creditor_issued_receipt"
    CREDITOR_RETURNED_DEBT_INSTRUMENT = "creditor_returned_debt_instrument"
    CREDITOR_REFUSED_CONFIRMATION = "creditor_refused_confirmation"
    NOTARY_OR_COURT_DEPOSIT_MADE = "notary_or_court_deposit_made"
    DEPOSIT_GROUND_CREDITOR_ABSENT_OR_EVASIVE = "deposit_ground_creditor_absent_or_evasive"
    DEPOSIT_NOTICE_SENT = "deposit_notice_sent"
    ACCORD_AGREED = "accord_agreed"
    ACCORD_FORM_OBSERVED = "accord_form_observed"
    ACCORD_PERFORMANCE_PROVIDED = "accord_performance_provided"
    SET_OFF_DECLARED = "set_off_declared"
    SET_OFF_NOTICE_DELIVERED = "set_off_notice_delivered"
    COUNTERCLAIMS_MUTUAL = "counterclaims_mutual"
    COUNTERCLAIMS_HOMOGENEOUS = "counterclaims_homogeneous"
    ACTIVE_CLAIM_DUE = "active_claim_due"
    PASSIVE_CLAIM_DUE_OR_EARLY_ALLOWED = "passive_claim_due_or_early_allowed"
    SET_OFF_PROHIBITED = "set_off_prohibited"
    ACTIVE_CLAIM_LIMITATION_EXPIRED = "active_claim_limitation_expired"
    SET_OFF_AMOUNT_PROVEN = "set_off_amount_proven"
    CLAIMS_EQUAL_AMOUNT = "claims_equal_amount"
    NOVATION_AGREED = "novation_agreed"
    NOVATION_INTENT_CLEAR = "novation_intent_clear"
    NEW_SUBJECT_OR_BASIS = "new_subject_or_basis"
    NEW_OBLIGATION_TERMS_AGREED = "new_obligation_terms_agreed"
    NOVATION_FORM_OBSERVED = "novation_form_observed"
    THIRD_PARTY_SECURITY_EXISTS = "third_party_security_exists"
    THIRD_PARTY_SECURITY_CONSENTED_NOVATION = "third_party_security_consented_novation"
    DEBT_FORGIVENESS_DECLARED = "debt_forgiveness_declared"
    DEBT_FORGIVENESS_NOTICE_DELIVERED = "debt_forgiveness_notice_delivered"
    DEBTOR_OBJECTED_FORGIVENESS = "debtor_objected_forgiveness"
    THIRD_PARTY_RIGHTS_PREJUDICED = "third_party_rights_prejudiced"
    FORGIVENESS_GIFT_INTENT = "forgiveness_gift_intent"
    COMMERCIAL_PARTIES = "commercial_parties"
    MERGER_CREDITOR_AND_DEBTOR = "merger_creditor_and_debtor"
    OBJECTIVE_PERMANENT_IMPOSSIBILITY = "objective_permanent_impossibility"
    IMPOSSIBILITY_RISK_ON_DEBTOR = "impossibility_risk_on_debtor"
    DEBTOR_IN_DELAY_AT_IMPOSSIBILITY = "debtor_in_delay_at_impossibility"
    CREDITOR_CAUSED_IMPOSSIBILITY = "creditor_caused_impossibility"
    GOVERNMENT_ACT_PREVENTS_PERFORMANCE = "government_act_prevents_performance"
    GOVERNMENT_ACT_INVALIDATED = "government_act_invalidated"
    PERSONAL_DEBTOR_DIED = "personal_debtor_died"
    PERSONAL_CREDITOR_DIED = "personal_creditor_died"
    OBLIGATION_PERSONAL_TO_DECEASED = "obligation_personal_to_deceased"
    LEGAL_ENTITY_LIQUIDATED = "legal_entity_liquidated"
    STATUTORY_SUCCESSOR_EXISTS = "statutory_successor_exists"
    OTHER_DISCHARGE_GROUND_PROVEN = "other_discharge_ground_proven"


REQUIRED_OBLIGATION_DYNAMICS_PREDICATES = frozenset(ObligationDynamicsEvidencePredicate)


class ObligationDynamicsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ObligationDynamicsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedObligationDynamicsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = OBLIGATION_DYNAMICS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ObligationDynamicsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=3)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedObligationDynamicsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Obligation-dynamics evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Obligation-dynamics evidence contains duplicate legal source refs.")
        return self


class ObligationDynamicsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    obligation_exists: bool
    obligation_breached: bool
    accrued_claims_exist: bool
    partial_termination_intended: bool
    assignment_agreement_concluded: bool
    assignment_form_observed: bool
    assigned_claim_exists: bool
    assigned_claim_identified: bool
    future_claim_determinable: bool
    claim_personal_to_creditor: bool
    assignment_prohibited_by_law: bool
    contract_restricts_assignment: bool
    debtor_consent_required: bool
    debtor_consent_obtained: bool
    debtor_notified: bool
    proof_of_transfer_provided: bool
    debtor_performed_original_before_notice: bool
    debtor_defense_existed_at_notice: bool
    debtor_counterclaim_existed_at_notice: bool
    cedent_transferred_documents: bool
    claim_invalid: bool
    cedent_knew_claim_invalid: bool
    cedent_guaranteed_debtor_performance: bool
    debtor_failed_after_assignment: bool
    debt_transfer_agreement_concluded: bool
    debt_transfer_form_observed: bool
    new_debtor_identified: bool
    creditor_consented_debt_transfer: bool
    original_debtor_released: bool
    cumulative_debt_assumption_agreed: bool
    business_debt_assumption: bool
    new_debtor_defense_exists: bool
    security_provider_consented_new_debtor: bool
    contract_transfer_agreed: bool
    all_parties_consented_contract_transfer: bool
    performance_rendered: bool
    performance_accepted_as_proper: bool
    performance_partial: bool
    creditor_issued_receipt: bool
    creditor_returned_debt_instrument: bool
    creditor_refused_confirmation: bool
    notary_or_court_deposit_made: bool
    deposit_ground_creditor_absent_or_evasive: bool
    deposit_notice_sent: bool
    accord_agreed: bool
    accord_form_observed: bool
    accord_performance_provided: bool
    set_off_declared: bool
    set_off_notice_delivered: bool
    counterclaims_mutual: bool
    counterclaims_homogeneous: bool
    active_claim_due: bool
    passive_claim_due_or_early_allowed: bool
    set_off_prohibited: bool
    active_claim_limitation_expired: bool
    set_off_amount_proven: bool
    claims_equal_amount: bool
    novation_agreed: bool
    novation_intent_clear: bool
    new_subject_or_basis: bool
    new_obligation_terms_agreed: bool
    novation_form_observed: bool
    third_party_security_exists: bool
    third_party_security_consented_novation: bool
    debt_forgiveness_declared: bool
    debt_forgiveness_notice_delivered: bool
    debtor_objected_forgiveness: bool
    third_party_rights_prejudiced: bool
    forgiveness_gift_intent: bool
    commercial_parties: bool
    merger_creditor_and_debtor: bool
    objective_permanent_impossibility: bool
    impossibility_risk_on_debtor: bool
    debtor_in_delay_at_impossibility: bool
    creditor_caused_impossibility: bool
    government_act_prevents_performance: bool
    government_act_invalidated: bool
    personal_debtor_died: bool
    personal_creditor_died: bool
    obligation_personal_to_deceased: bool
    legal_entity_liquidated: bool
    statutory_successor_exists: bool
    other_discharge_ground_proven: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ObligationDynamicsFactSet":
        if self.obligation_breached and not self.obligation_exists:
            raise ValueError("A breached obligation must exist.")
        if self.accrued_claims_exist and not self.obligation_exists:
            raise ValueError("Accrued claims require an existing obligation.")
        if self.assignment_form_observed and not self.assignment_agreement_concluded:
            raise ValueError("Assignment form requires an assignment agreement.")
        if self.debtor_consent_obtained and not self.debtor_consent_required:
            raise ValueError("Debtor consent requires a consent requirement.")
        if self.debtor_performed_original_before_notice and self.debtor_notified:
            raise ValueError("Performance before notice conflicts with prior debtor notice.")
        if self.cedent_knew_claim_invalid and not self.claim_invalid:
            raise ValueError("Knowledge of invalidity requires an invalid claim.")
        if self.debtor_failed_after_assignment and not self.assignment_agreement_concluded:
            raise ValueError("Post-assignment failure requires an assignment agreement.")
        if self.debt_transfer_form_observed and not self.debt_transfer_agreement_concluded:
            raise ValueError("Debt-transfer form requires a debt-transfer agreement.")
        if self.original_debtor_released and not self.debt_transfer_agreement_concluded:
            raise ValueError("Original-debtor release requires a debt-transfer agreement.")
        if self.cumulative_debt_assumption_agreed and self.original_debtor_released:
            raise ValueError("Cumulative assumption conflicts with original-debtor release.")
        if self.all_parties_consented_contract_transfer and not self.contract_transfer_agreed:
            raise ValueError("All-party consent requires an agreed contract transfer.")
        if self.performance_accepted_as_proper and not self.performance_rendered:
            raise ValueError("Accepted performance must have been rendered.")
        if self.performance_partial and not self.performance_rendered:
            raise ValueError("Partial performance must have been rendered.")
        if self.creditor_issued_receipt and not self.performance_rendered:
            raise ValueError("A receipt requires rendered performance.")
        if self.deposit_notice_sent and not self.notary_or_court_deposit_made:
            raise ValueError("Deposit notice requires a notary or court deposit.")
        if self.accord_form_observed and not self.accord_agreed:
            raise ValueError("Accord form requires an accord agreement.")
        if self.accord_performance_provided and not self.accord_agreed:
            raise ValueError("Accord performance requires an accord agreement.")
        if self.set_off_notice_delivered and not self.set_off_declared:
            raise ValueError("Set-off notice requires a set-off declaration.")
        if self.claims_equal_amount and not self.set_off_amount_proven:
            raise ValueError("Equal claims require proven set-off amounts.")
        if self.novation_intent_clear and not self.novation_agreed:
            raise ValueError("Novation intent requires a novation agreement.")
        if self.third_party_security_consented_novation and not self.third_party_security_exists:
            raise ValueError("Security consent requires existing third-party security.")
        if self.debt_forgiveness_notice_delivered and not self.debt_forgiveness_declared:
            raise ValueError("Forgiveness notice requires declared forgiveness.")
        if self.debtor_objected_forgiveness and not self.debt_forgiveness_notice_delivered:
            raise ValueError("Forgiveness objection requires delivered notice.")
        if self.government_act_invalidated and not self.government_act_prevents_performance:
            raise ValueError("Invalidated government act requires a preventing act.")
        if self.obligation_personal_to_deceased and not (
            self.personal_debtor_died or self.personal_creditor_died
        ):
            raise ValueError("A personal death-related obligation requires a deceased party.")
        if self.statutory_successor_exists and not self.legal_entity_liquidated:
            raise ValueError("A statutory successor requires liquidation.")
        return self


class ObligationDynamicsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ObligationDynamicsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ObligationDynamicsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ObligationDynamicsFactProvenance] = Field(default_factory=list)


class ObligationDynamicsConstraintSet(BaseModel):
    id: str
    model_version: str = OBLIGATION_DYNAMICS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ObligationDynamicsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    assignment_effective: bool
    assignment_enforceable_against_debtor: bool
    assignment_contract_breach_issue: bool
    debtor_original_performance_discharges: bool
    debtor_defenses_preserved: bool
    debtor_setoff_against_assignee_issue: bool
    cedent_document_transfer_issue: bool
    cedent_invalid_claim_warranty_issue: bool
    cedent_performance_guarantee_issue: bool
    debt_transfer_effective: bool
    original_debtor_released_effective: bool
    cumulative_debtors: bool
    new_debtor_defenses_preserved: bool
    third_party_security_terminated_on_transfer: bool
    contract_transfer_effective: bool
    parties_changed_not_discharged: bool
    proper_performance_discharge: bool
    partial_performance_discharge: bool
    creditor_confirmation_issue: bool
    notary_deposit_discharge: bool
    notary_deposit_notice_issue: bool
    accord_agreement_only: bool
    accord_discharge: bool
    setoff_bar: bool
    setoff_prerequisites: bool
    setoff_effective: bool
    setoff_full_discharge: bool
    setoff_partial_discharge: bool
    novation_effective: bool
    new_obligation_created_by_novation: bool
    original_accessories_terminated_by_novation: bool
    third_party_security_survives_novation: bool
    forgiveness_gift_bar: bool
    debt_forgiveness_effective: bool
    merger_discharge: bool
    impossibility_discharge: bool
    creditor_caused_impossibility_issue: bool
    government_act_discharge: bool
    government_act_losses_issue: bool
    government_act_restoration_issue: bool
    death_discharge: bool
    liquidation_discharge: bool
    other_discharge_effective: bool
    obligation_discharged_full: bool
    obligation_partially_remaining: bool
    accrued_claims_preserved: bool
    competing_discharge_paths: bool
    requires_human_dynamics_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_obligation_dynamics_evidence(
    evidence: ReviewedObligationDynamicsEvidence,
) -> ObligationDynamicsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Obligation-dynamics evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Obligation-dynamics evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_OBLIGATION_DYNAMICS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed obligation-dynamics evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_OBLIGATION_DYNAMICS_PREDICATES
    }
    return ObligationDynamicsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=OBLIGATION_DYNAMICS_MAPPING_VERSION,
        facts=ObligationDynamicsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ObligationDynamicsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_OBLIGATION_DYNAMICS_PREDICATES,
                key=lambda item: item.value,
            )
        ],
    )


def build_obligation_dynamics_constraint_set(
    mapping: ObligationDynamicsEvidenceMappingResult,
) -> ObligationDynamicsConstraintSet:
    return ObligationDynamicsConstraintSet(
        id=f"obligation-dynamics-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "assignment_effective == obligation_exists AND assignment_agreement AND form AND identifiable_claim AND transferable_claim AND required_consent",
            "debt_transfer_effective == obligation_exists AND debt_transfer_agreement AND form AND new_debtor AND creditor_consent",
            "contract_transfer_effective == obligation_exists AND contract_transfer_agreed AND all_parties_consent AND required_forms",
            "proper_performance_discharge == obligation_exists AND rendered AND accepted_proper AND NOT partial",
            "notary_deposit_discharge == obligation_exists AND deposit_made AND statutory_deposit_ground",
            "accord_discharge == obligation_exists AND accord_agreed AND form AND accord_performance_provided",
            "setoff_effective == obligation_exists AND declaration_delivered AND mutual_homogeneous_due_claims AND amount_proven AND NOT bar",
            "novation_effective == obligation_exists AND agreement AND clear_replacement_intent AND new_subject_or_basis AND new_terms AND form",
            "debt_forgiveness_effective == obligation_exists AND forgiveness_notice AND NOT objection AND NOT third_party_prejudice AND NOT commercial_gift_bar",
            "impossibility_discharge == obligation_exists AND objective_permanent_impossibility AND NOT risk_on_debtor AND NOT debtor_delay",
            "obligation_discharged_full == OR(full discharge paths) AND NOT partial_termination_intended",
        ],
    )


def evaluate_obligation_dynamics_constraints(
    constraint_set: ObligationDynamicsConstraintSet,
    facts: ObligationDynamicsFactSet,
) -> ObligationDynamicsEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in ObligationDynamicsFactSet.model_fields
    }
    outputs = {
        field_name: Bool(field_name)
        for field_name in ObligationDynamicsEvaluation.model_fields
        if field_name not in {"constraint_set_id", "satisfiable", "reasons_ru", "warnings_ru"}
    }
    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    claim_identifiable = Or(
        And(variables["assigned_claim_exists"], variables["assigned_claim_identified"]),
        variables["future_claim_determinable"],
    )
    claim_transferable = And(
        Not(variables["claim_personal_to_creditor"]),
        Not(variables["assignment_prohibited_by_law"]),
        Or(
            Not(variables["debtor_consent_required"]),
            variables["debtor_consent_obtained"],
        ),
    )
    solver.add(
        outputs["assignment_effective"]
        == And(
            variables["obligation_exists"],
            variables["assignment_agreement_concluded"],
            variables["assignment_form_observed"],
            claim_identifiable,
            claim_transferable,
            Not(variables["claim_invalid"]),
        )
    )
    solver.add(
        outputs["assignment_enforceable_against_debtor"]
        == And(
            outputs["assignment_effective"],
            variables["debtor_notified"],
            variables["proof_of_transfer_provided"],
        )
    )
    solver.add(
        outputs["assignment_contract_breach_issue"]
        == And(
            outputs["assignment_effective"],
            variables["contract_restricts_assignment"],
        )
    )
    solver.add(
        outputs["debtor_original_performance_discharges"]
        == And(
            outputs["assignment_effective"],
            variables["debtor_performed_original_before_notice"],
        )
    )
    solver.add(
        outputs["debtor_defenses_preserved"]
        == And(outputs["assignment_effective"], variables["debtor_defense_existed_at_notice"])
    )
    solver.add(
        outputs["debtor_setoff_against_assignee_issue"]
        == And(
            outputs["assignment_effective"],
            variables["debtor_counterclaim_existed_at_notice"],
        )
    )
    solver.add(
        outputs["cedent_document_transfer_issue"]
        == And(
            outputs["assignment_effective"],
            Not(variables["cedent_transferred_documents"]),
        )
    )
    solver.add(
        outputs["cedent_invalid_claim_warranty_issue"]
        == And(
            variables["assignment_agreement_concluded"],
            variables["claim_invalid"],
        )
    )
    solver.add(
        outputs["cedent_performance_guarantee_issue"]
        == And(
            outputs["assignment_effective"],
            variables["cedent_guaranteed_debtor_performance"],
            variables["debtor_failed_after_assignment"],
        )
    )
    solver.add(
        outputs["debt_transfer_effective"]
        == And(
            variables["obligation_exists"],
            variables["debt_transfer_agreement_concluded"],
            variables["debt_transfer_form_observed"],
            variables["new_debtor_identified"],
            variables["creditor_consented_debt_transfer"],
        )
    )
    solver.add(
        outputs["original_debtor_released_effective"]
        == And(outputs["debt_transfer_effective"], variables["original_debtor_released"])
    )
    solver.add(
        outputs["cumulative_debtors"]
        == And(
            outputs["debt_transfer_effective"],
            Not(variables["original_debtor_released"]),
            Or(
                variables["cumulative_debt_assumption_agreed"],
                variables["business_debt_assumption"],
            ),
        )
    )
    solver.add(
        outputs["new_debtor_defenses_preserved"]
        == And(outputs["debt_transfer_effective"], variables["new_debtor_defense_exists"])
    )
    solver.add(
        outputs["third_party_security_terminated_on_transfer"]
        == And(
            outputs["debt_transfer_effective"],
            variables["third_party_security_exists"],
            Not(variables["security_provider_consented_new_debtor"]),
        )
    )
    solver.add(
        outputs["contract_transfer_effective"]
        == And(
            variables["obligation_exists"],
            variables["contract_transfer_agreed"],
            variables["all_parties_consented_contract_transfer"],
            variables["assignment_form_observed"],
            variables["debt_transfer_form_observed"],
        )
    )
    solver.add(
        outputs["proper_performance_discharge"]
        == And(
            variables["obligation_exists"],
            variables["performance_rendered"],
            variables["performance_accepted_as_proper"],
            Not(variables["performance_partial"]),
        )
    )
    solver.add(
        outputs["partial_performance_discharge"]
        == And(
            variables["obligation_exists"],
            variables["performance_rendered"],
            variables["performance_accepted_as_proper"],
            variables["performance_partial"],
        )
    )
    solver.add(
        outputs["creditor_confirmation_issue"]
        == And(
            variables["performance_rendered"],
            variables["creditor_refused_confirmation"],
            Not(
                Or(
                    variables["creditor_issued_receipt"],
                    variables["creditor_returned_debt_instrument"],
                )
            ),
        )
    )
    solver.add(
        outputs["notary_deposit_discharge"]
        == And(
            variables["obligation_exists"],
            variables["notary_or_court_deposit_made"],
            variables["deposit_ground_creditor_absent_or_evasive"],
        )
    )
    solver.add(
        outputs["notary_deposit_notice_issue"]
        == And(outputs["notary_deposit_discharge"], Not(variables["deposit_notice_sent"]))
    )
    solver.add(
        outputs["accord_agreement_only"]
        == And(
            variables["obligation_exists"],
            variables["accord_agreed"],
            variables["accord_form_observed"],
            Not(variables["accord_performance_provided"]),
        )
    )
    solver.add(
        outputs["accord_discharge"]
        == And(
            variables["obligation_exists"],
            variables["accord_agreed"],
            variables["accord_form_observed"],
            variables["accord_performance_provided"],
        )
    )
    solver.add(
        outputs["setoff_bar"]
        == Or(
            variables["set_off_prohibited"],
            variables["active_claim_limitation_expired"],
        )
    )
    solver.add(
        outputs["setoff_prerequisites"]
        == And(
            variables["obligation_exists"],
            variables["counterclaims_mutual"],
            variables["counterclaims_homogeneous"],
            variables["active_claim_due"],
            variables["passive_claim_due_or_early_allowed"],
            variables["set_off_amount_proven"],
            Not(outputs["setoff_bar"]),
        )
    )
    solver.add(
        outputs["setoff_effective"]
        == And(
            outputs["setoff_prerequisites"],
            variables["set_off_declared"],
            variables["set_off_notice_delivered"],
        )
    )
    solver.add(
        outputs["setoff_full_discharge"]
        == And(outputs["setoff_effective"], variables["claims_equal_amount"])
    )
    solver.add(
        outputs["setoff_partial_discharge"]
        == And(outputs["setoff_effective"], Not(variables["claims_equal_amount"]))
    )
    solver.add(
        outputs["novation_effective"]
        == And(
            variables["obligation_exists"],
            variables["novation_agreed"],
            variables["novation_intent_clear"],
            variables["new_subject_or_basis"],
            variables["new_obligation_terms_agreed"],
            variables["novation_form_observed"],
        )
    )
    solver.add(outputs["new_obligation_created_by_novation"] == outputs["novation_effective"])
    solver.add(
        outputs["original_accessories_terminated_by_novation"]
        == And(
            outputs["novation_effective"],
            variables["third_party_security_exists"],
            Not(variables["third_party_security_consented_novation"]),
        )
    )
    solver.add(
        outputs["third_party_security_survives_novation"]
        == And(
            outputs["novation_effective"],
            variables["third_party_security_exists"],
            variables["third_party_security_consented_novation"],
        )
    )
    solver.add(
        outputs["forgiveness_gift_bar"]
        == And(variables["forgiveness_gift_intent"], variables["commercial_parties"])
    )
    solver.add(
        outputs["debt_forgiveness_effective"]
        == And(
            variables["obligation_exists"],
            variables["debt_forgiveness_declared"],
            variables["debt_forgiveness_notice_delivered"],
            Not(variables["debtor_objected_forgiveness"]),
            Not(variables["third_party_rights_prejudiced"]),
            Not(outputs["forgiveness_gift_bar"]),
        )
    )
    solver.add(
        outputs["merger_discharge"]
        == And(variables["obligation_exists"], variables["merger_creditor_and_debtor"])
    )
    solver.add(
        outputs["impossibility_discharge"]
        == And(
            variables["obligation_exists"],
            variables["objective_permanent_impossibility"],
            Not(variables["impossibility_risk_on_debtor"]),
            Not(variables["debtor_in_delay_at_impossibility"]),
        )
    )
    solver.add(
        outputs["creditor_caused_impossibility_issue"]
        == And(outputs["impossibility_discharge"], variables["creditor_caused_impossibility"])
    )
    solver.add(
        outputs["government_act_discharge"]
        == And(
            variables["obligation_exists"],
            variables["government_act_prevents_performance"],
            Not(variables["government_act_invalidated"]),
        )
    )
    solver.add(outputs["government_act_losses_issue"] == outputs["government_act_discharge"])
    solver.add(
        outputs["government_act_restoration_issue"]
        == And(
            variables["government_act_prevents_performance"],
            variables["government_act_invalidated"],
        )
    )
    solver.add(
        outputs["death_discharge"]
        == And(
            variables["obligation_exists"],
            variables["obligation_personal_to_deceased"],
            Or(variables["personal_debtor_died"], variables["personal_creditor_died"]),
        )
    )
    solver.add(
        outputs["liquidation_discharge"]
        == And(
            variables["obligation_exists"],
            variables["legal_entity_liquidated"],
            Not(variables["statutory_successor_exists"]),
        )
    )
    solver.add(
        outputs["other_discharge_effective"]
        == And(variables["obligation_exists"], variables["other_discharge_ground_proven"])
    )
    full_paths = [
        outputs["proper_performance_discharge"],
        outputs["notary_deposit_discharge"],
        outputs["accord_discharge"],
        outputs["setoff_full_discharge"],
        outputs["novation_effective"],
        outputs["debt_forgiveness_effective"],
        outputs["merger_discharge"],
        outputs["impossibility_discharge"],
        outputs["government_act_discharge"],
        outputs["death_discharge"],
        outputs["liquidation_discharge"],
        outputs["other_discharge_effective"],
    ]
    solver.add(
        outputs["obligation_discharged_full"]
        == And(Or(*full_paths), Not(variables["partial_termination_intended"]))
    )
    partial_path = Or(
        outputs["partial_performance_discharge"],
        outputs["setoff_partial_discharge"],
        variables["partial_termination_intended"],
    )
    solver.add(
        outputs["obligation_partially_remaining"]
        == And(
            variables["obligation_exists"],
            partial_path,
            Not(outputs["obligation_discharged_full"]),
        )
    )
    solver.add(
        outputs["accrued_claims_preserved"]
        == And(
            variables["accrued_claims_exist"],
            variables["obligation_breached"],
            Or(outputs["obligation_discharged_full"], outputs["obligation_partially_remaining"]),
            Not(outputs["novation_effective"]),
            Not(outputs["debt_forgiveness_effective"]),
        )
    )
    party_change = Or(
        outputs["assignment_effective"],
        outputs["debt_transfer_effective"],
        outputs["contract_transfer_effective"],
    )
    solver.add(
        outputs["parties_changed_not_discharged"]
        == And(party_change, Not(outputs["obligation_discharged_full"]))
    )
    solver.add(
        outputs["competing_discharge_paths"]
        == Or(
            *[
                And(left, right)
                for index, left in enumerate(full_paths)
                for right in full_paths[index + 1 :]
            ]
        )
    )
    solver.add(
        outputs["requires_human_dynamics_assessment"]
        == Or(
            party_change,
            outputs["notary_deposit_discharge"],
            outputs["accord_agreement_only"],
            outputs["accord_discharge"],
            outputs["setoff_effective"],
            outputs["setoff_bar"],
            outputs["novation_effective"],
            outputs["debt_forgiveness_effective"],
            outputs["merger_discharge"],
            outputs["impossibility_discharge"],
            outputs["government_act_discharge"],
            outputs["death_discharge"],
            outputs["liquidation_discharge"],
            outputs["other_discharge_effective"],
            outputs["creditor_confirmation_issue"],
            outputs["cedent_invalid_claim_warranty_issue"],
            outputs["competing_discharge_paths"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ObligationDynamicsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            **{
                field_name: False
                for field_name in outputs
                if field_name != "requires_human_dynamics_assessment"
            },
            requires_human_dynamics_assessment=True,
            reasons_ru=["Набор фактов о перемене лиц и прекращении обязательства противоречив."],
            warnings_ru=["Требуется повторная проверка исходных данных юристом."],
        )
    model = solver.model()
    values = {
        field_name: bool(model.eval(variable, model_completion=True))
        for field_name, variable in outputs.items()
    }
    reasons_ru = []
    if values["parties_changed_not_discharged"]:
        reasons_ru.append("Состав участников изменен без прекращения обязательства.")
    if values["obligation_discharged_full"]:
        reasons_ru.append("Выявлено формальное основание полного прекращения обязательства.")
    elif values["obligation_partially_remaining"]:
        reasons_ru.append("Обязательство прекращено только в части и сохраняется в остатке.")
    else:
        reasons_ru.append("Полное или частичное прекращение обязательства не подтверждено.")
    if values["accrued_claims_preserved"]:
        reasons_ru.append("Ранее возникшие требования из нарушения сохранены отдельно.")
    return ObligationDynamicsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        **values,
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель не определяет размер уступленного требования, зачета или остатка долга.",
            "Толкование воли на новацию, отступное и прощение долга требует оценки юриста.",
            "Специальные правила банкротства, исполнительного производства и отдельных обязательств проверяются отдельно.",
        ],
    )
