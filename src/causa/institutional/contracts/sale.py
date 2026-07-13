from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


SALE_EVIDENCE_SCHEMA_VERSION = "contracts.sale-evidence.v0"
SALE_MAPPING_VERSION = "contracts-reviewed-sale-to-facts-v0"
SALE_MODEL_VERSION = "contracts-sale-articles-454-491-v0"


class SaleEvidencePredicate(str, Enum):
    CONTRACT_CONCLUDED = "contract_concluded"
    SELLER_TRANSFER_OWNERSHIP_DUTY = "seller_transfer_ownership_duty"
    BUYER_ACCEPTANCE_DUTY = "buyer_acceptance_duty"
    BUYER_PAYMENT_DUTY = "buyer_payment_duty"
    GOODS_EXISTING_OR_FUTURE = "goods_existing_or_future"
    GOODS_NAME_AGREED = "goods_name_agreed"
    QUANTITY_DETERMINABLE = "quantity_determinable"
    PROPERTY_RIGHT_SUBJECT = "property_right_subject"
    PROPERTY_RIGHT_NATURE_EXCLUDES_SALE_RULES = "property_right_nature_excludes_sale_rules"
    ACCESSORIES_REQUIRED = "accessories_required"
    ACCESSORIES_TRANSFERRED = "accessories_transferred"
    DOCUMENTS_REQUIRED = "documents_required"
    DOCUMENTS_TRANSFERRED = "documents_transferred"
    TRANSFER_TERM_DUE = "transfer_term_due"
    DELIVERY_LATE = "delivery_late"
    FIXED_TERM_CONTRACT = "fixed_term_contract"
    BUYER_INTEREST_LOST_AFTER_TERM = "buyer_interest_lost_after_term"
    BUYER_CONSENTED_LATE_TRANSFER = "buyer_consented_late_transfer"
    DELIVERY_OBLIGATION = "delivery_obligation"
    GOODS_DELIVERED_TO_BUYER = "goods_delivered_to_buyer"
    GOODS_MADE_AVAILABLE = "goods_made_available"
    SHIPMENT_CONTRACT = "shipment_contract"
    GOODS_HANDED_TO_CARRIER = "goods_handed_to_carrier"
    GOODS_TRANSFER_COMPLETED = "goods_transfer_completed"
    RISK_ALLOCATION_AGREED = "risk_allocation_agreed"
    RISK_PASSED_BY_AGREEMENT = "risk_passed_by_agreement"
    GOODS_SOLD_IN_TRANSIT = "goods_sold_in_transit"
    SELLER_KNEW_TRANSIT_LOSS = "seller_knew_transit_loss"
    SELLER_DISCLOSED_TRANSIT_LOSS = "seller_disclosed_transit_loss"
    THIRD_PARTY_RIGHTS_EXIST = "third_party_rights_exist"
    BUYER_CONSENTED_THIRD_PARTY_RIGHTS = "buyer_consented_third_party_rights"
    GOODS_WITHDRAWN_BY_THIRD_PARTY = "goods_withdrawn_by_third_party"
    WITHDRAWAL_GROUND_PREDATES_TRANSFER = "withdrawal_ground_predates_transfer"
    BUYER_KNEW_WITHDRAWAL_GROUND = "buyer_knew_withdrawal_ground"
    SELLER_EVICTION_EXCLUSION_AGREEMENT = "seller_eviction_exclusion_agreement"
    THIRD_PARTY_EVICTION_CLAIM_FILED = "third_party_eviction_claim_filed"
    BUYER_JOINED_SELLER_TO_EVICTION_CASE = "buyer_joined_seller_to_eviction_case"
    SELLER_PARTICIPATED_IN_EVICTION_CASE = "seller_participated_in_eviction_case"
    SELLER_COULD_PREVENT_WITHDRAWAL = "seller_could_prevent_withdrawal"
    SELLER_REFUSED_GOODS_TRANSFER = "seller_refused_goods_transfer"
    BUYER_CHOSE_CONTRACT_REFUSAL_FOR_NONTRANSFER = "buyer_chose_contract_refusal_for_nontransfer"
    INDIVIDUALLY_DEFINED_GOODS = "individually_defined_goods"
    SPECIFIC_PERFORMANCE_REQUESTED = "specific_performance_requested"
    BUYER_SET_REASONABLE_DOCUMENT_TERM = "buyer_set_reasonable_document_term"
    SELLER_FAILED_DOCUMENT_TERM = "seller_failed_document_term"
    BUYER_REFUSED_GOODS_FOR_DOCUMENTS = "buyer_refused_goods_for_documents"
    QUANTITY_SHORTFALL = "quantity_shortfall"
    EXCESS_QUANTITY = "excess_quantity"
    BUYER_NOTIFIED_EXCESS = "buyer_notified_excess"
    SELLER_DISPOSED_EXCESS_REASONABLE_TIME = "seller_disposed_excess_reasonable_time"
    BUYER_ACCEPTED_EXCESS = "buyer_accepted_excess"
    DIFFERENT_EXCESS_PRICE_AGREED = "different_excess_price_agreed"
    ASSORTMENT_REQUIRED = "assortment_required"
    ASSORTMENT_AGREED = "assortment_agreed"
    ASSORTMENT_DETERMINABLE_FROM_NEEDS = "assortment_determinable_from_needs"
    SELLER_SELECTED_ASSORTMENT = "seller_selected_assortment"
    ASSORTMENT_NONCONFORMING = "assortment_nonconforming"
    MIXED_ASSORTMENT_DELIVERY = "mixed_assortment_delivery"
    BUYER_REJECTED_NONCONFORMING_ASSORTMENT = "buyer_rejected_nonconforming_assortment"
    BUYER_REJECTED_ALL_MIXED_GOODS = "buyer_rejected_all_mixed_goods"
    BUYER_REQUIRED_ASSORTMENT_REPLACEMENT = "buyer_required_assortment_replacement"
    BUYER_NOTIFIED_ASSORTMENT_REFUSAL_REASONABLE_TIME = (
        "buyer_notified_assortment_refusal_reasonable_time"
    )
    QUALITY_TERMS_AGREED = "quality_terms_agreed"
    ORDINARY_PURPOSE_KNOWN = "ordinary_purpose_known"
    SPECIAL_PURPOSE_DISCLOSED = "special_purpose_disclosed"
    SALE_BY_SAMPLE_OR_DESCRIPTION = "sale_by_sample_or_description"
    QUALITY_DEFECT = "quality_defect"
    MANDATORY_QUALITY_REQUIREMENTS_APPLY = "mandatory_quality_requirements_apply"
    ENHANCED_QUALITY_AGREED = "enhanced_quality_agreed"
    SELLER_WARRANTY_GIVEN = "seller_warranty_given"
    WARRANTY_PERIOD_ACTIVE = "warranty_period_active"
    SHELF_LIFE_SET = "shelf_life_set"
    GOODS_TRANSFERRED_WITH_USABLE_SHELF_LIFE = "goods_transferred_with_usable_shelf_life"
    INSPECTION_REQUIRED = "inspection_required"
    BUYER_RECEIVED_GOODS = "buyer_received_goods"
    INSPECTION_TIMELY = "inspection_timely"
    INSPECTION_METHOD_COMPLIED = "inspection_method_complied"
    BUYER_CHOSE_PRICE_REDUCTION = "buyer_chose_price_reduction"
    BUYER_CHOSE_FREE_REPAIR = "buyer_chose_free_repair"
    BUYER_CHOSE_REPAIR_COSTS = "buyer_chose_repair_costs"
    DEFECT_MATERIAL = "defect_material"
    BUYER_CHOSE_REPLACEMENT = "buyer_chose_replacement"
    BUYER_CHOSE_CONTRACT_REFUSAL_FOR_DEFECT = "buyer_chose_contract_refusal_for_defect"
    BUYER_PROVED_PRETRANSFER_DEFECT_CAUSE = "buyer_proved_pretransfer_defect_cause"
    SELLER_PROVED_POSTTRANSFER_DEFECT_CAUSE = "seller_proved_posttransfer_defect_cause"
    DEFECT_DISCOVERED_WITHIN_APPLICABLE_PERIOD = "defect_discovered_within_applicable_period"
    COMPLETENESS_TERMS_AGREED = "completeness_terms_agreed"
    INCOMPLETE_GOODS = "incomplete_goods"
    BUYER_CHOSE_INCOMPLETE_PRICE_REDUCTION = "buyer_chose_incomplete_price_reduction"
    BUYER_REQUESTED_COMPLETION = "buyer_requested_completion"
    SELLER_COMPLETED_REASONABLE_TIME = "seller_completed_reasonable_time"
    BUYER_REQUESTED_COMPLETE_REPLACEMENT = "buyer_requested_complete_replacement"
    BUYER_CHOSE_CONTRACT_REFUSAL_FOR_INCOMPLETENESS = (
        "buyer_chose_contract_refusal_for_incompleteness"
    )
    SET_OF_GOODS_AGREED = "set_of_goods_agreed"
    SET_TRANSFER_COMPLETE = "set_transfer_complete"
    PACKAGING_REQUIRED = "packaging_required"
    PACKAGING_TRANSFERRED = "packaging_transferred"
    PACKAGING_CONFORMING = "packaging_conforming"
    BUYER_REQUESTED_PACKAGING = "buyer_requested_packaging"
    BUYER_REQUESTED_PACKAGING_REPLACEMENT = "buyer_requested_packaging_replacement"
    BUYER_ELECTED_OTHER_PACKAGING_REMEDY = "buyer_elected_other_packaging_remedy"
    DISCREPANCY_FOUND = "discrepancy_found"
    PROMPT_NOTICE_GIVEN = "prompt_notice_given"
    SELLER_KNEW_OR_SHOULD_HAVE_KNOWN_DISCREPANCY = "seller_knew_or_should_have_known_discrepancy"
    SELLER_PROVED_NOTICE_PREJUDICE = "seller_proved_notice_prejudice"
    BUYER_ACCEPTANCE_COMPLETED = "buyer_acceptance_completed"
    BUYER_FAILED_ACCEPTANCE = "buyer_failed_acceptance"
    SELLER_DEMANDED_ACCEPTANCE = "seller_demanded_acceptance"
    SELLER_CHOSE_CONTRACT_REFUSAL_FOR_NONACCEPTANCE = (
        "seller_chose_contract_refusal_for_nonacceptance"
    )
    PRICE_AGREED = "price_agreed"
    PRICE_DETERMINABLE = "price_determinable"
    PRICE_BASED_ON_WEIGHT = "price_based_on_weight"
    NET_WEIGHT_PROVEN = "net_weight_proven"
    PRICE_REVISION_FORMULA_AGREED = "price_revision_formula_agreed"
    PRICE_REVISION_INPUTS_PROVEN = "price_revision_inputs_proven"
    PAYMENT_DUE = "payment_due"
    BUYER_PAID = "buyer_paid"
    SELLER_DEMANDED_PAYMENT = "seller_demanded_payment"
    MULTIPLE_GOODS_TRANSFERRED = "multiple_goods_transferred"
    SELLER_SUSPENDED_REMAINING_GOODS = "seller_suspended_remaining_goods"
    PREPAYMENT_REQUIRED = "prepayment_required"
    PREPAYMENT_DUE = "prepayment_due"
    PREPAYMENT_MADE = "prepayment_made"
    SELLER_FAILED_AFTER_PREPAYMENT = "seller_failed_after_prepayment"
    BUYER_REQUESTED_PREPAID_DELIVERY = "buyer_requested_prepaid_delivery"
    BUYER_REQUESTED_PREPAYMENT_RETURN = "buyer_requested_prepayment_return"
    CREDIT_SALE = "credit_sale"
    CREDIT_PAYMENT_DUE = "credit_payment_due"
    CREDIT_PAYMENT_MADE = "credit_payment_made"
    SELLER_DEMANDED_CREDIT_PAYMENT_OR_RETURN = "seller_demanded_credit_payment_or_return"
    SELLER_SECURITY_INTEREST_APPLIES = "seller_security_interest_applies"
    INSTALLMENT_SALE = "installment_sale"
    INSTALLMENT_ESSENTIAL_TERMS_COMPLETE = "installment_essential_terms_complete"
    INSTALLMENT_PAYMENT_DUE = "installment_payment_due"
    INSTALLMENT_PAYMENT_MADE = "installment_payment_made"
    PAID_AMOUNT_EXCEEDS_HALF_PRICE = "paid_amount_exceeds_half_price"
    SELLER_CHOSE_INSTALLMENT_REFUSAL = "seller_chose_installment_refusal"
    INSURANCE_DUTY_ALLOCATED = "insurance_duty_allocated"
    INSURANCE_DUTY_DUE = "insurance_duty_due"
    INSURANCE_OBTAINED = "insurance_obtained"
    COUNTERPARTY_INSURED_GOODS = "counterparty_insured_goods"
    COUNTERPARTY_CHOSE_INSURANCE_REFUSAL = "counterparty_chose_insurance_refusal"
    TITLE_RETENTION_AGREED = "title_retention_agreed"
    TITLE_CONDITION_MET = "title_condition_met"
    BUYER_DISPOSED_BEFORE_TITLE = "buyer_disposed_before_title"
    TITLE_EARLY_DISPOSAL_PERMITTED = "title_early_disposal_permitted"
    SELLER_REQUIRED_GOODS_RETURN = "seller_required_goods_return"
    TITLE_RETURN_CONTRACT_BAR = "title_return_contract_bar"
    UNILATERAL_REFUSAL_NOTICE_DELIVERED = "unilateral_refusal_notice_delivered"
    CONTRACT_TERMINATED = "contract_terminated"
    LOSS_CLAIMED = "loss_claimed"
    CAUSATION_PROVEN = "causation_proven"


REQUIRED_SALE_PREDICATES = frozenset(SaleEvidencePredicate)


class SaleEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: SaleEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedSaleEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = SALE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[SaleEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=4)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedSaleEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Sale evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Sale evidence contains duplicate legal source refs.")
        return self


class SaleFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_concluded: bool
    seller_transfer_ownership_duty: bool
    buyer_acceptance_duty: bool
    buyer_payment_duty: bool
    goods_existing_or_future: bool
    goods_name_agreed: bool
    quantity_determinable: bool
    property_right_subject: bool
    property_right_nature_excludes_sale_rules: bool
    accessories_required: bool
    accessories_transferred: bool
    documents_required: bool
    documents_transferred: bool
    transfer_term_due: bool
    delivery_late: bool
    fixed_term_contract: bool
    buyer_interest_lost_after_term: bool
    buyer_consented_late_transfer: bool
    delivery_obligation: bool
    goods_delivered_to_buyer: bool
    goods_made_available: bool
    shipment_contract: bool
    goods_handed_to_carrier: bool
    goods_transfer_completed: bool
    risk_allocation_agreed: bool
    risk_passed_by_agreement: bool
    goods_sold_in_transit: bool
    seller_knew_transit_loss: bool
    seller_disclosed_transit_loss: bool
    third_party_rights_exist: bool
    buyer_consented_third_party_rights: bool
    goods_withdrawn_by_third_party: bool
    withdrawal_ground_predates_transfer: bool
    buyer_knew_withdrawal_ground: bool
    seller_eviction_exclusion_agreement: bool
    third_party_eviction_claim_filed: bool
    buyer_joined_seller_to_eviction_case: bool
    seller_participated_in_eviction_case: bool
    seller_could_prevent_withdrawal: bool
    seller_refused_goods_transfer: bool
    buyer_chose_contract_refusal_for_nontransfer: bool
    individually_defined_goods: bool
    specific_performance_requested: bool
    buyer_set_reasonable_document_term: bool
    seller_failed_document_term: bool
    buyer_refused_goods_for_documents: bool
    quantity_shortfall: bool
    excess_quantity: bool
    buyer_notified_excess: bool
    seller_disposed_excess_reasonable_time: bool
    buyer_accepted_excess: bool
    different_excess_price_agreed: bool
    assortment_required: bool
    assortment_agreed: bool
    assortment_determinable_from_needs: bool
    seller_selected_assortment: bool
    assortment_nonconforming: bool
    mixed_assortment_delivery: bool
    buyer_rejected_nonconforming_assortment: bool
    buyer_rejected_all_mixed_goods: bool
    buyer_required_assortment_replacement: bool
    buyer_notified_assortment_refusal_reasonable_time: bool
    quality_terms_agreed: bool
    ordinary_purpose_known: bool
    special_purpose_disclosed: bool
    sale_by_sample_or_description: bool
    quality_defect: bool
    mandatory_quality_requirements_apply: bool
    enhanced_quality_agreed: bool
    seller_warranty_given: bool
    warranty_period_active: bool
    shelf_life_set: bool
    goods_transferred_with_usable_shelf_life: bool
    inspection_required: bool
    buyer_received_goods: bool
    inspection_timely: bool
    inspection_method_complied: bool
    buyer_chose_price_reduction: bool
    buyer_chose_free_repair: bool
    buyer_chose_repair_costs: bool
    defect_material: bool
    buyer_chose_replacement: bool
    buyer_chose_contract_refusal_for_defect: bool
    buyer_proved_pretransfer_defect_cause: bool
    seller_proved_posttransfer_defect_cause: bool
    defect_discovered_within_applicable_period: bool
    completeness_terms_agreed: bool
    incomplete_goods: bool
    buyer_chose_incomplete_price_reduction: bool
    buyer_requested_completion: bool
    seller_completed_reasonable_time: bool
    buyer_requested_complete_replacement: bool
    buyer_chose_contract_refusal_for_incompleteness: bool
    set_of_goods_agreed: bool
    set_transfer_complete: bool
    packaging_required: bool
    packaging_transferred: bool
    packaging_conforming: bool
    buyer_requested_packaging: bool
    buyer_requested_packaging_replacement: bool
    buyer_elected_other_packaging_remedy: bool
    discrepancy_found: bool
    prompt_notice_given: bool
    seller_knew_or_should_have_known_discrepancy: bool
    seller_proved_notice_prejudice: bool
    buyer_acceptance_completed: bool
    buyer_failed_acceptance: bool
    seller_demanded_acceptance: bool
    seller_chose_contract_refusal_for_nonacceptance: bool
    price_agreed: bool
    price_determinable: bool
    price_based_on_weight: bool
    net_weight_proven: bool
    price_revision_formula_agreed: bool
    price_revision_inputs_proven: bool
    payment_due: bool
    buyer_paid: bool
    seller_demanded_payment: bool
    multiple_goods_transferred: bool
    seller_suspended_remaining_goods: bool
    prepayment_required: bool
    prepayment_due: bool
    prepayment_made: bool
    seller_failed_after_prepayment: bool
    buyer_requested_prepaid_delivery: bool
    buyer_requested_prepayment_return: bool
    credit_sale: bool
    credit_payment_due: bool
    credit_payment_made: bool
    seller_demanded_credit_payment_or_return: bool
    seller_security_interest_applies: bool
    installment_sale: bool
    installment_essential_terms_complete: bool
    installment_payment_due: bool
    installment_payment_made: bool
    paid_amount_exceeds_half_price: bool
    seller_chose_installment_refusal: bool
    insurance_duty_allocated: bool
    insurance_duty_due: bool
    insurance_obtained: bool
    counterparty_insured_goods: bool
    counterparty_chose_insurance_refusal: bool
    title_retention_agreed: bool
    title_condition_met: bool
    buyer_disposed_before_title: bool
    title_early_disposal_permitted: bool
    seller_required_goods_return: bool
    title_return_contract_bar: bool
    unilateral_refusal_notice_delivered: bool
    contract_terminated: bool
    loss_claimed: bool
    causation_proven: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "SaleFactSet":
        if self.property_right_nature_excludes_sale_rules and not self.property_right_subject:
            raise ValueError("Exclusion by nature requires a property-right sale subject.")
        if self.delivery_late and not self.transfer_term_due:
            raise ValueError("Late delivery requires a due transfer term.")
        if self.buyer_interest_lost_after_term and not self.fixed_term_contract:
            raise ValueError("Loss of interest after term requires a fixed-term sale.")
        if self.buyer_consented_late_transfer and not self.delivery_late:
            raise ValueError("Consent to late transfer requires late delivery.")
        if self.risk_passed_by_agreement and not self.risk_allocation_agreed:
            raise ValueError("Contractual risk passage requires an agreed risk allocation.")
        transit_facts = (self.seller_knew_transit_loss, self.seller_disclosed_transit_loss)
        if any(transit_facts) and not self.goods_sold_in_transit:
            raise ValueError("Transit-loss facts require goods sold while in transit.")
        third_party_facts = (
            self.buyer_consented_third_party_rights,
            self.goods_withdrawn_by_third_party,
            self.withdrawal_ground_predates_transfer,
            self.buyer_knew_withdrawal_ground,
            self.seller_eviction_exclusion_agreement,
        )
        if any(third_party_facts) and not self.third_party_rights_exist:
            raise ValueError("Third-party consequences require third-party rights.")
        eviction_case_facts = (
            self.buyer_joined_seller_to_eviction_case,
            self.seller_participated_in_eviction_case,
            self.seller_could_prevent_withdrawal,
        )
        if any(eviction_case_facts) and not self.third_party_eviction_claim_filed:
            raise ValueError("Eviction procedure facts require a third-party claim.")
        if self.specific_performance_requested and not (
            self.seller_refused_goods_transfer and self.individually_defined_goods
        ):
            raise ValueError("Specific performance requires refusal of individually defined goods.")
        if (
            self.buyer_chose_contract_refusal_for_nontransfer
            and not self.seller_refused_goods_transfer
        ):
            raise ValueError("Nontransfer refusal requires the seller to refuse goods transfer.")
        document_gap = (self.accessories_required and not self.accessories_transferred) or (
            self.documents_required and not self.documents_transferred
        )
        if (
            self.buyer_set_reasonable_document_term
            or self.seller_failed_document_term
            or self.buyer_refused_goods_for_documents
        ) and not document_gap:
            raise ValueError("Document remedies require missing accessories or documents.")
        excess_facts = (
            self.buyer_notified_excess,
            self.seller_disposed_excess_reasonable_time,
            self.buyer_accepted_excess,
            self.different_excess_price_agreed,
        )
        if any(excess_facts) and not self.excess_quantity:
            raise ValueError("Excess-quantity facts require excess goods.")
        if self.assortment_agreed and not self.assortment_required:
            raise ValueError("Agreed assortment requires an assortment obligation.")
        if self.seller_selected_assortment and not (
            self.assortment_required and self.assortment_determinable_from_needs
        ):
            raise ValueError("Seller assortment choice requires known buyer needs.")
        assortment_remedy_facts = (
            self.mixed_assortment_delivery,
            self.buyer_rejected_nonconforming_assortment,
            self.buyer_rejected_all_mixed_goods,
            self.buyer_required_assortment_replacement,
            self.buyer_notified_assortment_refusal_reasonable_time,
        )
        if any(assortment_remedy_facts) and not self.assortment_nonconforming:
            raise ValueError("Assortment remedies require nonconforming assortment.")
        if self.warranty_period_active and not self.seller_warranty_given:
            raise ValueError("An active warranty period requires a seller warranty.")
        if self.goods_transferred_with_usable_shelf_life and not self.shelf_life_set:
            raise ValueError("Usable shelf-life evidence requires an established shelf life.")
        if (self.inspection_timely or self.inspection_method_complied) and not (
            self.inspection_required and self.buyer_received_goods
        ):
            raise ValueError(
                "Inspection performance requires received goods and an inspection duty."
            )
        defect_facts = (
            self.buyer_chose_price_reduction,
            self.buyer_chose_free_repair,
            self.buyer_chose_repair_costs,
            self.defect_material,
            self.buyer_chose_replacement,
            self.buyer_chose_contract_refusal_for_defect,
            self.buyer_proved_pretransfer_defect_cause,
            self.seller_proved_posttransfer_defect_cause,
            self.defect_discovered_within_applicable_period,
        )
        if any(defect_facts) and not self.quality_defect:
            raise ValueError("Defect remedies and proof require a quality defect.")
        incomplete_facts = (
            self.buyer_chose_incomplete_price_reduction,
            self.buyer_requested_completion,
            self.seller_completed_reasonable_time,
            self.buyer_requested_complete_replacement,
            self.buyer_chose_contract_refusal_for_incompleteness,
        )
        if any(incomplete_facts) and not self.incomplete_goods:
            raise ValueError("Completeness remedies require incomplete goods.")
        if self.set_transfer_complete and not self.set_of_goods_agreed:
            raise ValueError("Complete set transfer requires an agreed set of goods.")
        packaging_issue = self.packaging_required and (
            not self.packaging_transferred or not self.packaging_conforming
        )
        packaging_actions = (
            self.buyer_requested_packaging,
            self.buyer_requested_packaging_replacement,
            self.buyer_elected_other_packaging_remedy,
        )
        if any(packaging_actions) and not packaging_issue:
            raise ValueError("Packaging remedies require missing or nonconforming packaging.")
        notice_facts = (
            self.prompt_notice_given,
            self.seller_knew_or_should_have_known_discrepancy,
            self.seller_proved_notice_prejudice,
        )
        if any(notice_facts) and not self.discrepancy_found:
            raise ValueError("Notice facts require a discovered discrepancy.")
        if self.buyer_acceptance_completed and not self.buyer_received_goods:
            raise ValueError("Completed acceptance requires received goods.")
        if (
            self.seller_demanded_acceptance or self.seller_chose_contract_refusal_for_nonacceptance
        ) and not self.buyer_failed_acceptance:
            raise ValueError("Seller acceptance remedies require buyer nonacceptance.")
        if self.net_weight_proven and not self.price_based_on_weight:
            raise ValueError("Net-weight proof requires weight-based pricing.")
        if self.price_revision_inputs_proven and not self.price_revision_formula_agreed:
            raise ValueError("Revision inputs require an agreed price-revision formula.")
        if self.seller_demanded_payment and not self.payment_due:
            raise ValueError("A payment demand requires payment to be due.")
        if self.seller_suspended_remaining_goods and not (
            self.multiple_goods_transferred and self.payment_due and not self.buyer_paid
        ):
            raise ValueError("Suspension requires multiple goods and payment default.")
        if self.prepayment_due and not self.prepayment_required:
            raise ValueError("Prepayment can be due only when required.")
        if self.prepayment_made and not self.prepayment_required:
            raise ValueError("Prepayment evidence requires a prepayment duty.")
        if (
            self.seller_failed_after_prepayment
            or self.buyer_requested_prepaid_delivery
            or self.buyer_requested_prepayment_return
        ) and not self.prepayment_made:
            raise ValueError("Buyer prepayment remedies require completed prepayment.")
        credit_facts = (
            self.credit_payment_due,
            self.credit_payment_made,
            self.seller_demanded_credit_payment_or_return,
            self.seller_security_interest_applies,
        )
        if any(credit_facts) and not self.credit_sale:
            raise ValueError("Credit-sale facts require sale on credit.")
        installment_facts = (
            self.installment_essential_terms_complete,
            self.installment_payment_due,
            self.installment_payment_made,
            self.paid_amount_exceeds_half_price,
            self.seller_chose_installment_refusal,
        )
        if any(installment_facts) and not self.installment_sale:
            raise ValueError("Installment facts require an installment sale.")
        insurance_facts = (
            self.insurance_duty_due,
            self.insurance_obtained,
            self.counterparty_insured_goods,
            self.counterparty_chose_insurance_refusal,
        )
        if any(insurance_facts) and not self.insurance_duty_allocated:
            raise ValueError("Insurance consequences require an allocated insurance duty.")
        title_facts = (
            self.title_condition_met,
            self.buyer_disposed_before_title,
            self.title_early_disposal_permitted,
            self.seller_required_goods_return,
            self.title_return_contract_bar,
        )
        if any(title_facts) and not self.title_retention_agreed:
            raise ValueError("Title-retention consequences require an agreed reservation of title.")
        if self.causation_proven and not self.loss_claimed:
            raise ValueError("Proven causation requires a loss claim.")
        return self


class SaleFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class SaleEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: SaleFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[SaleFactProvenance] = Field(default_factory=list)


class SaleConstraintSet(BaseModel):
    id: str
    model_version: str = SALE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class SaleEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    sale_contract_qualified: bool
    property_right_sale_rules_applicable: bool
    transfer_package_complete: bool
    transfer_package_gap: bool
    late_fixed_term_transfer_requires_consent: bool
    transfer_duty_performed: bool
    risk_passed_by_default: bool
    risk_passed_by_contract: bool
    transit_risk_passed_at_conclusion: bool
    transit_risk_clause_challenge: bool
    third_party_rights_breach: bool
    eviction_loss_remedy_available: bool
    eviction_exclusion_ineffective: bool
    buyer_eviction_procedure_gap: bool
    seller_eviction_defense_barred: bool
    goods_transfer_refusal_remedy_available: bool
    specific_performance_available: bool
    documents_remedy_available: bool
    documents_refusal_ground: bool
    quantity_shortfall_remedies: bool
    excess_quantity_deemed_accepted: bool
    excess_quantity_payment_due: bool
    seller_assortment_choice_default: bool
    assortment_remedies_available: bool
    mixed_assortment_total_refusal_available: bool
    assortment_deemed_accepted: bool
    quality_standard_requires_general_default: bool
    quality_remedies_available: bool
    material_defect_remedies_available: bool
    defect_causation_requirement_satisfied: bool
    warranty_seller_burden_applies: bool
    defect_claim_timely: bool
    shelf_life_transfer_breach: bool
    quality_inspection_gap: bool
    completeness_primary_remedies: bool
    completeness_secondary_remedies: bool
    set_delivery_breach: bool
    packaging_remedies_available: bool
    notice_defense_available: bool
    notice_defense_displaced_by_seller_knowledge: bool
    buyer_acceptance_breach: bool
    seller_nonacceptance_remedies: bool
    price_general_default_required: bool
    net_weight_price_controls: bool
    price_revision_requires_review: bool
    payment_default: bool
    seller_payment_remedies: bool
    prepayment_default: bool
    prepaid_buyer_remedies: bool
    credit_payment_default: bool
    credit_seller_remedies: bool
    credit_goods_security_active: bool
    installment_terms_gap: bool
    installment_refusal_available: bool
    installment_refusal_barred_by_half_payment: bool
    insurance_breach: bool
    insurance_self_help_available: bool
    insurance_refusal_available: bool
    title_disposal_bar: bool
    title_return_remedy: bool
    sale_contract_refusal_effective: bool
    sale_breach_established: bool
    requires_human_sale_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_sale_evidence(evidence: ReviewedSaleEvidence) -> SaleEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Sale evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Sale evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(predicate.value for predicate in REQUIRED_SALE_PREDICATES - assertions.keys())
    if missing:
        raise ValueError(
            "Reviewed sale evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_SALE_PREDICATES
    }
    return SaleEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=SALE_MAPPING_VERSION,
        facts=SaleFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            SaleFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_SALE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_sale_constraint_set(mapping: SaleEvidenceMappingResult) -> SaleConstraintSet:
    return SaleConstraintSet(
        id=f"sale-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "sale_contract == concluded AND transfer_ownership_duty AND acceptance_duty AND payment_duty AND goods_subject AND name AND quantity",
            "transfer_duty == completed AND (delivery OR availability OR carrier_handover)",
            "default_risk_passage == transfer_duty AND NOT agreed_risk_allocation",
            "eviction_remedy == withdrawal_on_pretransfer_ground AND NOT buyer_knowledge AND NOT preventable_procedure_gap",
            "quality_remedy == defect AND timely_claim AND applicable_causation_burden",
            "notice_defense == late_notice AND proven_prejudice AND NOT seller_knowledge",
            "payment_default == payment_due AND NOT paid",
            "installment_refusal == installment_default AND seller_refusal AND NOT more_than_half_paid",
            "title_return == retained_title AND unmet_condition AND seller_return_demand",
            "sale_refusal == statutory_refusal_ground AND delivered_notice",
        ],
    )


def evaluate_sale_constraints(
    constraint_set: SaleConstraintSet,
    facts: SaleFactSet,
) -> SaleEvaluation:
    variables = {field_name: Bool(field_name) for field_name in SaleFactSet.model_fields}
    outputs = {
        field_name: Bool(field_name)
        for field_name in SaleEvaluation.model_fields
        if field_name not in {"constraint_set_id", "satisfiable", "reasons_ru", "warnings_ru"}
    }
    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    transfer_package_gap = Or(
        And(variables["accessories_required"], Not(variables["accessories_transferred"])),
        And(variables["documents_required"], Not(variables["documents_transferred"])),
    )
    transfer_route = Or(
        And(variables["delivery_obligation"], variables["goods_delivered_to_buyer"]),
        And(
            Not(variables["delivery_obligation"]),
            Not(variables["shipment_contract"]),
            variables["goods_made_available"],
        ),
        And(variables["shipment_contract"], variables["goods_handed_to_carrier"]),
    )
    eviction_procedure_relief = And(
        variables["third_party_eviction_claim_filed"],
        Not(variables["buyer_joined_seller_to_eviction_case"]),
        variables["seller_could_prevent_withdrawal"],
    )
    ordinary_defect_election = Or(
        variables["buyer_chose_price_reduction"],
        variables["buyer_chose_free_repair"],
        variables["buyer_chose_repair_costs"],
    )
    material_defect_election = Or(
        variables["buyer_chose_replacement"],
        variables["buyer_chose_contract_refusal_for_defect"],
    )
    warranty_burden = And(
        variables["seller_warranty_given"],
        variables["warranty_period_active"],
    )
    defect_causation = Or(
        And(warranty_burden, Not(variables["seller_proved_posttransfer_defect_cause"])),
        And(Not(warranty_burden), variables["buyer_proved_pretransfer_defect_cause"]),
    )
    packaging_issue = And(
        variables["goods_transfer_completed"],
        variables["packaging_required"],
        Or(Not(variables["packaging_transferred"]), Not(variables["packaging_conforming"])),
    )
    refusal_ground = Or(
        And(
            variables["seller_refused_goods_transfer"],
            variables["buyer_chose_contract_refusal_for_nontransfer"],
        ),
        And(
            transfer_package_gap,
            variables["buyer_set_reasonable_document_term"],
            variables["seller_failed_document_term"],
            variables["buyer_refused_goods_for_documents"],
        ),
        And(
            variables["quality_defect"],
            variables["defect_material"],
            defect_causation,
            variables["defect_discovered_within_applicable_period"],
            variables["buyer_chose_contract_refusal_for_defect"],
        ),
        And(
            variables["incomplete_goods"],
            variables["buyer_requested_completion"],
            Not(variables["seller_completed_reasonable_time"]),
            variables["buyer_chose_contract_refusal_for_incompleteness"],
        ),
        And(
            variables["buyer_failed_acceptance"],
            variables["seller_chose_contract_refusal_for_nonacceptance"],
        ),
        And(
            variables["installment_sale"],
            variables["installment_payment_due"],
            Not(variables["installment_payment_made"]),
            Not(variables["paid_amount_exceeds_half_price"]),
            variables["seller_chose_installment_refusal"],
        ),
        And(
            variables["insurance_duty_allocated"],
            variables["insurance_duty_due"],
            Not(variables["insurance_obtained"]),
            variables["counterparty_chose_insurance_refusal"],
        ),
    )
    derived = {
        "sale_contract_qualified": And(
            variables["contract_concluded"],
            variables["seller_transfer_ownership_duty"],
            variables["buyer_acceptance_duty"],
            variables["buyer_payment_duty"],
            variables["goods_existing_or_future"],
            variables["goods_name_agreed"],
            variables["quantity_determinable"],
        ),
        "property_right_sale_rules_applicable": And(
            variables["property_right_subject"],
            Not(variables["property_right_nature_excludes_sale_rules"]),
        ),
        "transfer_package_complete": And(
            variables["goods_transfer_completed"], Not(transfer_package_gap)
        ),
        "transfer_package_gap": And(variables["goods_transfer_completed"], transfer_package_gap),
        "late_fixed_term_transfer_requires_consent": And(
            variables["delivery_late"],
            variables["fixed_term_contract"],
            variables["buyer_interest_lost_after_term"],
            Not(variables["buyer_consented_late_transfer"]),
        ),
        "transfer_duty_performed": And(variables["goods_transfer_completed"], transfer_route),
        "risk_passed_by_default": And(
            variables["goods_transfer_completed"],
            transfer_route,
            Not(variables["risk_allocation_agreed"]),
        ),
        "risk_passed_by_contract": And(
            variables["risk_allocation_agreed"], variables["risk_passed_by_agreement"]
        ),
        "transit_risk_passed_at_conclusion": And(
            variables["goods_sold_in_transit"],
            Not(variables["risk_allocation_agreed"]),
        ),
        "transit_risk_clause_challenge": And(
            variables["goods_sold_in_transit"],
            variables["seller_knew_transit_loss"],
            Not(variables["seller_disclosed_transit_loss"]),
        ),
        "third_party_rights_breach": And(
            variables["third_party_rights_exist"],
            Not(variables["buyer_consented_third_party_rights"]),
        ),
        "eviction_loss_remedy_available": And(
            variables["goods_withdrawn_by_third_party"],
            variables["withdrawal_ground_predates_transfer"],
            Not(variables["buyer_knew_withdrawal_ground"]),
            Not(eviction_procedure_relief),
            variables["loss_claimed"],
            variables["causation_proven"],
        ),
        "eviction_exclusion_ineffective": And(
            variables["third_party_rights_exist"],
            variables["seller_eviction_exclusion_agreement"],
        ),
        "buyer_eviction_procedure_gap": And(
            variables["third_party_eviction_claim_filed"],
            Not(variables["buyer_joined_seller_to_eviction_case"]),
        ),
        "seller_eviction_defense_barred": And(
            variables["third_party_eviction_claim_filed"],
            variables["buyer_joined_seller_to_eviction_case"],
            Not(variables["seller_participated_in_eviction_case"]),
        ),
        "goods_transfer_refusal_remedy_available": variables["seller_refused_goods_transfer"],
        "specific_performance_available": And(
            variables["seller_refused_goods_transfer"],
            variables["individually_defined_goods"],
            variables["specific_performance_requested"],
        ),
        "documents_remedy_available": And(
            transfer_package_gap, variables["buyer_set_reasonable_document_term"]
        ),
        "documents_refusal_ground": And(
            transfer_package_gap,
            variables["buyer_set_reasonable_document_term"],
            variables["seller_failed_document_term"],
            variables["buyer_refused_goods_for_documents"],
        ),
        "quantity_shortfall_remedies": variables["quantity_shortfall"],
        "excess_quantity_deemed_accepted": And(
            variables["excess_quantity"],
            variables["buyer_notified_excess"],
            Not(variables["seller_disposed_excess_reasonable_time"]),
            variables["buyer_accepted_excess"],
        ),
        "excess_quantity_payment_due": And(
            variables["excess_quantity"],
            variables["buyer_accepted_excess"],
        ),
        "seller_assortment_choice_default": And(
            variables["assortment_required"],
            Not(variables["assortment_agreed"]),
            variables["assortment_determinable_from_needs"],
            variables["seller_selected_assortment"],
        ),
        "assortment_remedies_available": variables["assortment_nonconforming"],
        "mixed_assortment_total_refusal_available": And(
            variables["assortment_nonconforming"],
            variables["mixed_assortment_delivery"],
            variables["buyer_rejected_all_mixed_goods"],
            variables["buyer_notified_assortment_refusal_reasonable_time"],
        ),
        "assortment_deemed_accepted": And(
            variables["assortment_nonconforming"],
            Not(variables["buyer_notified_assortment_refusal_reasonable_time"]),
        ),
        "quality_standard_requires_general_default": And(
            Not(variables["quality_terms_agreed"]),
            Or(
                variables["ordinary_purpose_known"],
                variables["special_purpose_disclosed"],
                variables["sale_by_sample_or_description"],
                variables["mandatory_quality_requirements_apply"],
            ),
        ),
        "quality_remedies_available": And(
            variables["quality_defect"],
            defect_causation,
            variables["defect_discovered_within_applicable_period"],
            ordinary_defect_election,
        ),
        "material_defect_remedies_available": And(
            variables["quality_defect"],
            variables["defect_material"],
            defect_causation,
            variables["defect_discovered_within_applicable_period"],
            material_defect_election,
        ),
        "defect_causation_requirement_satisfied": And(
            variables["quality_defect"], defect_causation
        ),
        "warranty_seller_burden_applies": And(variables["quality_defect"], warranty_burden),
        "defect_claim_timely": And(
            variables["quality_defect"], variables["defect_discovered_within_applicable_period"]
        ),
        "shelf_life_transfer_breach": And(
            variables["goods_transfer_completed"],
            variables["shelf_life_set"],
            Not(variables["goods_transferred_with_usable_shelf_life"]),
        ),
        "quality_inspection_gap": And(
            variables["inspection_required"],
            variables["buyer_received_goods"],
            Or(Not(variables["inspection_timely"]), Not(variables["inspection_method_complied"])),
        ),
        "completeness_primary_remedies": And(
            variables["incomplete_goods"],
            Or(
                variables["buyer_chose_incomplete_price_reduction"],
                variables["buyer_requested_completion"],
            ),
        ),
        "completeness_secondary_remedies": And(
            variables["incomplete_goods"],
            variables["buyer_requested_completion"],
            Not(variables["seller_completed_reasonable_time"]),
            Or(
                variables["buyer_requested_complete_replacement"],
                variables["buyer_chose_contract_refusal_for_incompleteness"],
            ),
        ),
        "set_delivery_breach": And(
            variables["set_of_goods_agreed"],
            variables["transfer_term_due"],
            Not(variables["set_transfer_complete"]),
        ),
        "packaging_remedies_available": And(
            packaging_issue,
            Or(
                variables["buyer_requested_packaging"],
                variables["buyer_requested_packaging_replacement"],
                variables["buyer_elected_other_packaging_remedy"],
            ),
        ),
        "notice_defense_available": And(
            variables["discrepancy_found"],
            Not(variables["prompt_notice_given"]),
            variables["seller_proved_notice_prejudice"],
            Not(variables["seller_knew_or_should_have_known_discrepancy"]),
        ),
        "notice_defense_displaced_by_seller_knowledge": And(
            variables["discrepancy_found"],
            Not(variables["prompt_notice_given"]),
            variables["seller_knew_or_should_have_known_discrepancy"],
        ),
        "buyer_acceptance_breach": variables["buyer_failed_acceptance"],
        "seller_nonacceptance_remedies": And(
            variables["buyer_failed_acceptance"],
            Or(
                variables["seller_demanded_acceptance"],
                variables["seller_chose_contract_refusal_for_nonacceptance"],
            ),
        ),
        "price_general_default_required": And(
            Not(variables["price_agreed"]), Not(variables["price_determinable"])
        ),
        "net_weight_price_controls": And(
            variables["price_based_on_weight"], variables["net_weight_proven"]
        ),
        "price_revision_requires_review": And(
            variables["price_revision_formula_agreed"],
            Not(variables["price_revision_inputs_proven"]),
        ),
        "payment_default": And(variables["payment_due"], Not(variables["buyer_paid"])),
        "seller_payment_remedies": And(
            variables["payment_due"],
            Not(variables["buyer_paid"]),
            variables["seller_demanded_payment"],
        ),
        "prepayment_default": And(
            variables["prepayment_required"],
            variables["prepayment_due"],
            Not(variables["prepayment_made"]),
        ),
        "prepaid_buyer_remedies": And(
            variables["prepayment_made"],
            variables["seller_failed_after_prepayment"],
            Or(
                variables["buyer_requested_prepaid_delivery"],
                variables["buyer_requested_prepayment_return"],
            ),
        ),
        "credit_payment_default": And(
            variables["credit_sale"],
            variables["credit_payment_due"],
            Not(variables["credit_payment_made"]),
        ),
        "credit_seller_remedies": And(
            variables["credit_sale"],
            variables["credit_payment_due"],
            Not(variables["credit_payment_made"]),
            variables["seller_demanded_credit_payment_or_return"],
        ),
        "credit_goods_security_active": And(
            variables["credit_sale"], variables["seller_security_interest_applies"]
        ),
        "installment_terms_gap": And(
            variables["installment_sale"],
            Not(variables["installment_essential_terms_complete"]),
        ),
        "installment_refusal_available": And(
            variables["installment_sale"],
            variables["installment_payment_due"],
            Not(variables["installment_payment_made"]),
            variables["seller_chose_installment_refusal"],
            Not(variables["paid_amount_exceeds_half_price"]),
        ),
        "installment_refusal_barred_by_half_payment": And(
            variables["installment_sale"],
            variables["installment_payment_due"],
            Not(variables["installment_payment_made"]),
            variables["seller_chose_installment_refusal"],
            variables["paid_amount_exceeds_half_price"],
        ),
        "insurance_breach": And(
            variables["insurance_duty_allocated"],
            variables["insurance_duty_due"],
            Not(variables["insurance_obtained"]),
        ),
        "insurance_self_help_available": And(
            variables["insurance_duty_allocated"],
            variables["insurance_duty_due"],
            Not(variables["insurance_obtained"]),
            variables["counterparty_insured_goods"],
        ),
        "insurance_refusal_available": And(
            variables["insurance_duty_allocated"],
            variables["insurance_duty_due"],
            Not(variables["insurance_obtained"]),
            variables["counterparty_chose_insurance_refusal"],
        ),
        "title_disposal_bar": And(
            variables["title_retention_agreed"],
            Not(variables["title_condition_met"]),
            variables["buyer_disposed_before_title"],
            Not(variables["title_early_disposal_permitted"]),
        ),
        "title_return_remedy": And(
            variables["title_retention_agreed"],
            Not(variables["title_condition_met"]),
            variables["seller_required_goods_return"],
            Not(variables["title_return_contract_bar"]),
        ),
        "sale_contract_refusal_effective": And(
            variables["contract_concluded"],
            refusal_ground,
            variables["unilateral_refusal_notice_delivered"],
        ),
    }
    sale_breach = Or(
        variables["delivery_late"],
        transfer_package_gap,
        variables["seller_refused_goods_transfer"],
        derived["transit_risk_clause_challenge"],
        derived["third_party_rights_breach"],
        variables["quantity_shortfall"],
        variables["assortment_nonconforming"],
        And(variables["quality_defect"], defect_causation),
        derived["shelf_life_transfer_breach"],
        derived["quality_inspection_gap"],
        variables["incomplete_goods"],
        derived["set_delivery_breach"],
        packaging_issue,
        variables["buyer_failed_acceptance"],
        derived["payment_default"],
        derived["prepayment_default"],
        variables["seller_failed_after_prepayment"],
        derived["credit_payment_default"],
        derived["insurance_breach"],
        derived["title_disposal_bar"],
    )
    derived["sale_breach_established"] = sale_breach
    review_outputs = [
        value
        for name, value in derived.items()
        if name
        not in {
            "sale_contract_qualified",
            "property_right_sale_rules_applicable",
            "transfer_package_complete",
            "transfer_duty_performed",
            "risk_passed_by_default",
            "risk_passed_by_contract",
            "sale_breach_established",
        }
    ]
    derived["requires_human_sale_assessment"] = Or(*review_outputs)
    for field_name, expression in derived.items():
        solver.add(outputs[field_name] == expression)

    satisfiable = solver.check() == sat
    if not satisfiable:
        return SaleEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            **{
                field_name: False
                for field_name in outputs
                if field_name != "requires_human_sale_assessment"
            },
            requires_human_sale_assessment=True,
            reasons_ru=["Набор фактов о купле-продаже противоречив."],
            warnings_ru=["Требуется повторная проверка исходных данных юристом."],
        )
    model = solver.model()
    values = {
        field_name: bool(model.eval(variable, model_completion=True))
        for field_name, variable in outputs.items()
    }
    reasons_ru = []
    if values["sale_contract_qualified"]:
        reasons_ru.append("Подтверждены формальные признаки договора купли-продажи.")
    if values["transfer_package_gap"]:
        reasons_ru.append("Выявлен пробел в передаче товара, принадлежностей или документов.")
    if values["late_fixed_term_transfer_requires_consent"]:
        reasons_ru.append(
            "Просроченная передача по договору к определенному сроку требует согласия покупателя."
        )
    if values["third_party_rights_breach"]:
        reasons_ru.append("Товар передан с несогласованными правами третьих лиц.")
    if values["eviction_loss_remedy_available"]:
        reasons_ru.append(
            "Подтверждены формальные предпосылки ответственности продавца при эвикции."
        )
    if values["quality_remedies_available"] or values["material_defect_remedies_available"]:
        reasons_ru.append("Подтверждены формальные предпосылки требований из недостатков товара.")
    if values["completeness_secondary_remedies"]:
        reasons_ru.append(
            "Неустраненная некомплектность активирует вторичные средства защиты покупателя."
        )
    if values["notice_defense_available"]:
        reasons_ru.append(
            "Продавец подтвердил формальную предпосылку возражения из несвоевременного извещения."
        )
    if values["payment_default"] or values["credit_payment_default"]:
        reasons_ru.append("Выявлена просрочка оплаты товара покупателем.")
    if values["title_disposal_bar"]:
        reasons_ru.append(
            "Распоряжение товаром совершено до перехода сохраненного за продавцом права собственности."
        )
    if values["sale_contract_refusal_effective"]:
        reasons_ru.append(
            "Подтверждены формальные предпосылки специального отказа от договора купли-продажи."
        )
    if values["sale_breach_established"]:
        reasons_ru.append("Выявлено нарушение обязанности по общим правилам купли-продажи.")
    if not reasons_ru:
        reasons_ru.append(
            "Активное специальное последствие общих правил купли-продажи не подтверждено."
        )
    return SaleEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        **values,
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет формальные предпосылки статей 454–491 ГК РФ и не подменяет квалификацию суда.",
            "Существенность недостатка, разумность срока, доказанность причин и толкование выбора средства защиты оценивает юрист.",
            "Общие правила купли-продажи применяются к поставке постольку, поскольку специальные нормы не устанавливают иное.",
        ],
    )
