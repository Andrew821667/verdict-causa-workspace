from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


SUPPLY_EVIDENCE_SCHEMA_VERSION = "contracts.supply-evidence.v0"
SUPPLY_MAPPING_VERSION = "contracts-reviewed-supply-to-facts-v0"
SUPPLY_MODEL_VERSION = "contracts-supply-articles-506-524-v0"


class SupplyEvidencePredicate(str, Enum):
    CONTRACT_CONCLUDED = "contract_concluded"
    SUPPLIER_BUSINESS = "supplier_business"
    SUPPLIER_PRODUCED_OR_PROCURED_GOODS = "supplier_produced_or_procured_goods"
    GOODS_NONPERSONAL_USE = "goods_nonpersonal_use"
    RETAIL_SALE_CONTEXT = "retail_sale_context"
    TRANSFER_TERM_DEFINED = "transfer_term_defined"
    DISAGREEMENTS_RECEIVED = "disagreements_received"
    THIRTY_DAY_RESPONSE_OR_REFUSAL = "thirty_day_response_or_refusal"
    PERIODIC_DELIVERY = "periodic_delivery"
    DELIVERY_PERIODS_AGREED = "delivery_periods_agreed"
    DELIVERY_SCHEDULE_AGREED = "delivery_schedule_agreed"
    EARLY_DELIVERY = "early_delivery"
    BUYER_CONSENTED_EARLY_DELIVERY = "buyer_consented_early_delivery"
    BUYER_ACCEPTED_EARLY_DELIVERY = "buyer_accepted_early_delivery"
    SHIPMENT_ORDER_REQUIRED = "shipment_order_required"
    SHIPMENT_ORDER_TIMELY_COMPLETE = "shipment_order_timely_complete"
    TRANSPORT_METHOD_AGREED = "transport_method_agreed"
    SUPPLIER_SELECTED_TRANSPORT = "supplier_selected_transport"
    DELIVERY_COMPLETED = "delivery_completed"
    DELIVERY_LATE = "delivery_late"
    QUANTITY_SHORTFALL = "quantity_shortfall"
    CONTRACT_TERM_CONTINUES = "contract_term_continues"
    BUYER_REFUSED_LATE_MAKEUP_BY_NOTICE = "buyer_refused_late_makeup_by_notice"
    CROSS_ASSORTMENT_OFFSET = "cross_assortment_offset"
    BUYER_CONSENTED_OFFSET = "buyer_consented_offset"
    MAKEUP_ASSORTMENT_AGREED = "makeup_assortment_agreed"
    PRIOR_PERIOD_ASSORTMENT_PROVEN = "prior_period_assortment_proven"
    BUYER_RECEIVED_GOODS = "buyer_received_goods"
    INSPECTION_TIMELY = "inspection_timely"
    DISCREPANCY_FOUND = "discrepancy_found"
    PROMPT_WRITTEN_NOTICE = "prompt_written_notice"
    DOCUMENTS_MISMATCH = "documents_mismatch"
    CONSIGNEE_REFUSED_GOODS = "consignee_refused_goods"
    LAWFUL_REFUSAL = "lawful_refusal"
    GOODS_PRESERVED = "goods_preserved"
    SUPPLIER_NOTIFIED = "supplier_notified"
    SUPPLIER_DISPOSED_REASONABLE_TIME = "supplier_disposed_reasonable_time"
    CUSTODY_EXPENSES_DOCUMENTED = "custody_expenses_documented"
    BUYER_REALIZED_OR_RETURNED_GOODS = "buyer_realized_or_returned_goods"
    UNLAWFUL_REFUSAL = "unlawful_refusal"
    SUPPLIER_DEMANDED_PAYMENT_AFTER_REFUSAL = "supplier_demanded_payment_after_refusal"
    BUYER_SELECTION_REQUIRED = "buyer_selection_required"
    SELECTION_DUE = "selection_due"
    BUYER_FAILED_SELECTION = "buyer_failed_selection"
    SUPPLIER_NOTIFIED_READINESS = "supplier_notified_readiness"
    PAYMENT_DUE = "payment_due"
    CONSIGNEE_PAYMENT_DUTY = "consignee_payment_duty"
    CONSIGNEE_FAILED_PAYMENT = "consignee_failed_payment"
    BUYER_PAID = "buyer_paid"
    RETURNABLE_CONTAINER = "returnable_container"
    CONTAINER_RETURN_DUE = "container_return_due"
    CONTAINER_RETURNED = "container_returned"
    QUALITY_DEFECT = "quality_defect"
    DEFECT_PROMPTLY_CURED_OR_REPLACED = "defect_promptly_cured_or_replaced"
    RETAIL_PURCHASER_CLAIM = "retail_purchaser_claim"
    INCOMPLETE_GOODS = "incomplete_goods"
    INCOMPLETENESS_PROMPTLY_CURED_OR_REPLACED = "incompleteness_promptly_cured_or_replaced"
    BUYER_ACQUIRED_SUBSTITUTE = "buyer_acquired_substitute"
    SUBSTITUTE_EXPENSES_REASONABLE_DOCUMENTED = "substitute_expenses_reasonable_documented"
    PAYMENT_WITHHELD = "payment_withheld"
    PENALTY_APPLIES_TO_SHORT_OR_LATE = "penalty_applies_to_short_or_late"
    REPLENISHMENT_DUTY_CONTINUES = "replenishment_duty_continues"
    ACTUAL_REPLENISHMENT_COMPLETED = "actual_replenishment_completed"
    MULTIPLE_SUPPLY_CONTRACTS = "multiple_supply_contracts"
    PERFORMANCE_ALLOCATION_DESIGNATED = "performance_allocation_designated"
    REPEATED_LATE_DELIVERY = "repeated_late_delivery"
    IRREMEDIABLE_DEFECT = "irremediable_defect"
    REPEATED_PAYMENT_DEFAULT = "repeated_payment_default"
    REPEATED_SELECTION_FAILURE = "repeated_selection_failure"
    UNILATERAL_REFUSAL_NOTICE_DELIVERED = "unilateral_refusal_notice_delivered"
    CONTRACT_TERMINATED = "contract_terminated"
    REPLACEMENT_TRANSACTION_MADE = "replacement_transaction_made"
    REPLACEMENT_TRANSACTION_REASONABLE = "replacement_transaction_reasonable"
    REPLACEMENT_TRANSACTION_TIMELY = "replacement_transaction_timely"
    CONTRACT_PRICE_PROVEN = "contract_price_proven"
    REPLACEMENT_PRICE_PROVEN = "replacement_price_proven"
    CURRENT_PRICE_AVAILABLE = "current_price_available"
    CURRENT_PRICE_PROVEN = "current_price_proven"
    CURRENT_PRICE_TIME_PLACE_ADJUSTED = "current_price_time_place_adjusted"
    LOSS_CLAIMED = "loss_claimed"
    CAUSATION_PROVEN = "causation_proven"
    OTHER_LOSS_PROVEN = "other_loss_proven"


REQUIRED_SUPPLY_PREDICATES = frozenset(SupplyEvidencePredicate)


class SupplyEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: SupplyEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedSupplyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = SUPPLY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[SupplyEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=4)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedSupplyEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Supply evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Supply evidence contains duplicate legal source refs.")
        return self


class SupplyFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_concluded: bool
    supplier_business: bool
    supplier_produced_or_procured_goods: bool
    goods_nonpersonal_use: bool
    retail_sale_context: bool
    transfer_term_defined: bool
    disagreements_received: bool
    thirty_day_response_or_refusal: bool
    periodic_delivery: bool
    delivery_periods_agreed: bool
    delivery_schedule_agreed: bool
    early_delivery: bool
    buyer_consented_early_delivery: bool
    buyer_accepted_early_delivery: bool
    shipment_order_required: bool
    shipment_order_timely_complete: bool
    transport_method_agreed: bool
    supplier_selected_transport: bool
    delivery_completed: bool
    delivery_late: bool
    quantity_shortfall: bool
    contract_term_continues: bool
    buyer_refused_late_makeup_by_notice: bool
    cross_assortment_offset: bool
    buyer_consented_offset: bool
    makeup_assortment_agreed: bool
    prior_period_assortment_proven: bool
    buyer_received_goods: bool
    inspection_timely: bool
    discrepancy_found: bool
    prompt_written_notice: bool
    documents_mismatch: bool
    consignee_refused_goods: bool
    lawful_refusal: bool
    goods_preserved: bool
    supplier_notified: bool
    supplier_disposed_reasonable_time: bool
    custody_expenses_documented: bool
    buyer_realized_or_returned_goods: bool
    unlawful_refusal: bool
    supplier_demanded_payment_after_refusal: bool
    buyer_selection_required: bool
    selection_due: bool
    buyer_failed_selection: bool
    supplier_notified_readiness: bool
    payment_due: bool
    consignee_payment_duty: bool
    consignee_failed_payment: bool
    buyer_paid: bool
    returnable_container: bool
    container_return_due: bool
    container_returned: bool
    quality_defect: bool
    defect_promptly_cured_or_replaced: bool
    retail_purchaser_claim: bool
    incomplete_goods: bool
    incompleteness_promptly_cured_or_replaced: bool
    buyer_acquired_substitute: bool
    substitute_expenses_reasonable_documented: bool
    payment_withheld: bool
    penalty_applies_to_short_or_late: bool
    replenishment_duty_continues: bool
    actual_replenishment_completed: bool
    multiple_supply_contracts: bool
    performance_allocation_designated: bool
    repeated_late_delivery: bool
    irremediable_defect: bool
    repeated_payment_default: bool
    repeated_selection_failure: bool
    unilateral_refusal_notice_delivered: bool
    contract_terminated: bool
    replacement_transaction_made: bool
    replacement_transaction_reasonable: bool
    replacement_transaction_timely: bool
    contract_price_proven: bool
    replacement_price_proven: bool
    current_price_available: bool
    current_price_proven: bool
    current_price_time_place_adjusted: bool
    loss_claimed: bool
    causation_proven: bool
    other_loss_proven: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "SupplyFactSet":
        if self.thirty_day_response_or_refusal and not self.disagreements_received:
            raise ValueError("A disagreement response requires received disagreements.")
        if self.delivery_periods_agreed and not self.periodic_delivery:
            raise ValueError("Agreed delivery periods require periodic delivery.")
        if self.delivery_schedule_agreed and not self.periodic_delivery:
            raise ValueError("A delivery schedule requires periodic delivery.")
        if self.delivery_schedule_agreed and not self.delivery_periods_agreed:
            raise ValueError("A delivery schedule requires agreed delivery periods.")
        if self.buyer_consented_early_delivery and not self.early_delivery:
            raise ValueError("Buyer consent to early delivery requires early delivery.")
        if self.buyer_accepted_early_delivery and not self.early_delivery:
            raise ValueError("Acceptance of early delivery requires early delivery.")
        if self.shipment_order_timely_complete and not self.shipment_order_required:
            raise ValueError("A shipment order can be complete only when it is required.")
        if self.supplier_selected_transport and self.transport_method_agreed:
            raise ValueError("Supplier transport choice requires no agreed transport method.")
        if self.buyer_refused_late_makeup_by_notice and not self.quantity_shortfall:
            raise ValueError("Late make-up refusal requires a quantity shortfall.")
        if self.cross_assortment_offset and not self.quantity_shortfall:
            raise ValueError("Cross-assortment offset requires a quantity shortfall.")
        if (self.makeup_assortment_agreed or self.prior_period_assortment_proven) and not (
            self.quantity_shortfall
        ):
            raise ValueError("Make-up assortment facts require a quantity shortfall.")
        if self.inspection_timely and not self.buyer_received_goods:
            raise ValueError("Inspection requires received goods.")
        custody_facts = (
            self.goods_preserved,
            self.supplier_notified,
            self.supplier_disposed_reasonable_time,
            self.custody_expenses_documented,
            self.buyer_realized_or_returned_goods,
        )
        if any(custody_facts) and not self.lawful_refusal:
            raise ValueError("Responsible-custody facts require lawful refusal of goods.")
        if self.unlawful_refusal and self.lawful_refusal:
            raise ValueError("Refusal cannot be both lawful and unlawful.")
        if self.supplier_demanded_payment_after_refusal and not self.unlawful_refusal:
            raise ValueError("A payment demand after refusal requires unlawful refusal.")
        if self.selection_due and not self.buyer_selection_required:
            raise ValueError("Selection can be due only when buyer selection is required.")
        if self.buyer_failed_selection and not (
            self.buyer_selection_required and self.selection_due
        ):
            raise ValueError("Selection failure requires a due buyer-selection duty.")
        if self.consignee_failed_payment and not (self.consignee_payment_duty and self.payment_due):
            raise ValueError("Consignee nonpayment requires a due payment duty.")
        if (self.container_return_due or self.container_returned) and not self.returnable_container:
            raise ValueError("Container return facts require returnable containers.")
        if self.defect_promptly_cured_or_replaced and not self.quality_defect:
            raise ValueError("Prompt defect cure requires a quality defect.")
        if self.retail_purchaser_claim and not self.quality_defect:
            raise ValueError("A retail-purchaser claim requires a quality defect.")
        if self.incompleteness_promptly_cured_or_replaced and not self.incomplete_goods:
            raise ValueError("Prompt completion requires incomplete goods.")
        nonconformity = self.quantity_shortfall or self.quality_defect or self.incomplete_goods
        if self.buyer_acquired_substitute and not nonconformity:
            raise ValueError(
                "A substitute purchase requires short, defective, or incomplete supply."
            )
        if self.substitute_expenses_reasonable_documented and not self.buyer_acquired_substitute:
            raise ValueError("Substitute expenses require a substitute purchase.")
        if self.penalty_applies_to_short_or_late and not (
            self.quantity_shortfall or self.delivery_late
        ):
            raise ValueError("Supply penalty requires short or late delivery.")
        if (self.replenishment_duty_continues or self.actual_replenishment_completed) and not (
            self.quantity_shortfall or self.delivery_late
        ):
            raise ValueError("Replenishment facts require short or late delivery.")
        if self.performance_allocation_designated and not self.multiple_supply_contracts:
            raise ValueError("Performance allocation requires multiple supply contracts.")
        if self.repeated_late_delivery and not self.delivery_late:
            raise ValueError("Repeated delay requires late delivery.")
        if self.irremediable_defect and not self.quality_defect:
            raise ValueError("An irremediable defect requires a quality defect.")
        if self.repeated_selection_failure and not self.buyer_failed_selection:
            raise ValueError("Repeated selection failure requires buyer selection failure.")
        if self.repeated_payment_default and not self.payment_due:
            raise ValueError("Repeated payment default requires a due payment obligation.")
        if self.replacement_transaction_reasonable and not self.replacement_transaction_made:
            raise ValueError("Replacement reasonableness requires a replacement transaction.")
        if self.replacement_transaction_timely and not self.replacement_transaction_made:
            raise ValueError("Replacement timeliness requires a replacement transaction.")
        if self.replacement_transaction_made and not self.contract_terminated:
            raise ValueError("Article 524 replacement transaction requires contract termination.")
        if self.replacement_price_proven and not self.replacement_transaction_made:
            raise ValueError("Replacement price proof requires a replacement transaction.")
        if self.current_price_proven and not self.current_price_available:
            raise ValueError("Current-price proof requires an available current price.")
        if self.current_price_time_place_adjusted and not self.current_price_proven:
            raise ValueError("Current-price adjustment requires proven current price.")
        if self.causation_proven and not self.loss_claimed:
            raise ValueError("Proven causation requires a loss claim.")
        if self.other_loss_proven and not self.loss_claimed:
            raise ValueError("Other proven loss requires a loss claim.")
        return self


class SupplyFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class SupplyEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: SupplyFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[SupplyFactProvenance] = Field(default_factory=list)


class SupplyConstraintSet(BaseModel):
    id: str
    model_version: str = SUPPLY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class SupplyEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    supply_contract_qualified: bool
    delivery_term_requires_general_default: bool
    negotiation_response_breach: bool
    negotiation_loss_issue: bool
    monthly_delivery_default: bool
    agreed_delivery_schedule_controls: bool
    early_delivery_permitted: bool
    unauthorized_early_delivery: bool
    early_delivery_counts_next_period: bool
    shipment_order_default: bool
    shipment_order_loss_issue: bool
    supplier_transport_choice: bool
    makeup_delivery_required: bool
    late_makeup_refusal_effective: bool
    cross_assortment_offset_barred: bool
    makeup_assortment_default_to_prior_period: bool
    acceptance_duties_satisfied: bool
    acceptance_inspection_gap: bool
    acceptance_notice_gap: bool
    transport_acceptance_issue: bool
    responsible_custody_duties_satisfied: bool
    responsible_custody_gap: bool
    supplier_custody_cost_liability: bool
    buyer_disposal_available: bool
    supplier_payment_claim_after_unlawful_refusal: bool
    selection_supplier_remedy_available: bool
    buyer_payment_claim_available: bool
    container_return_breach: bool
    quality_remedies_available: bool
    quality_remedies_displaced_by_prompt_cure: bool
    retail_purchaser_direct_demands: bool
    completeness_remedies_available: bool
    completeness_remedies_displaced_by_prompt_cure: bool
    cover_purchase_cost_recovery: bool
    payment_withholding_available: bool
    penalty_continues_until_replenishment: bool
    default_contract_allocation_required: bool
    supplier_material_breach: bool
    buyer_material_breach: bool
    supply_unilateral_refusal_effective: bool
    concrete_price_damages_available: bool
    abstract_current_price_damages_available: bool
    other_damages_preserved: bool
    supply_breach_established: bool
    requires_human_supply_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_supply_evidence(
    evidence: ReviewedSupplyEvidence,
) -> SupplyEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Supply evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Supply evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_SUPPLY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed supply evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_SUPPLY_PREDICATES
    }
    return SupplyEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=SUPPLY_MAPPING_VERSION,
        facts=SupplyFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            SupplyFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_SUPPLY_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_supply_constraint_set(mapping: SupplyEvidenceMappingResult) -> SupplyConstraintSet:
    return SupplyConstraintSet(
        id=f"supply-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "supply_contract == concluded AND supplier_business AND produced_or_procured_goods AND nonpersonal_goods_use AND NOT retail_sale_context",
            "delivery_term_general_default == supply_contract AND NOT transfer_term AND NOT periodic_delivery",
            "negotiation_response_breach == disagreements_received AND NOT timely_response_or_refusal",
            "early_delivery_permitted == early_delivery AND buyer_consent",
            "makeup_delivery == shortfall AND contract_term_continues AND NOT buyer_refusal_notice",
            "makeup_assortment_default == shortfall AND no_assortment_agreement AND prior_period_assortment",
            "acceptance_duties == received AND timely_inspection AND (no_discrepancy OR prompt_notice)",
            "transport_acceptance_issue == documents_mismatch OR consignee_refused_goods",
            "responsible_custody == lawful_refusal AND preserved AND supplier_notified",
            "article_520_cover == unremedied_nonconformity AND substitute_purchase AND documented_expenses",
            "article_520_withholding == unremedied_quality_or_completeness AND payment_withheld",
            "article_523_refusal == material_breach AND delivered_notice",
            "article_524_concrete_damages == termination AND reasonable_replacement AND proven_prices AND causation",
            "article_524_abstract_damages == termination AND no_replacement AND current_price AND causation",
        ],
    )


def evaluate_supply_constraints(
    constraint_set: SupplyConstraintSet,
    facts: SupplyFactSet,
) -> SupplyEvaluation:
    variables = {field_name: Bool(field_name) for field_name in SupplyFactSet.model_fields}
    outputs = {
        field_name: Bool(field_name)
        for field_name in SupplyEvaluation.model_fields
        if field_name not in {"constraint_set_id", "satisfiable", "reasons_ru", "warnings_ru"}
    }
    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    solver.add(
        outputs["supply_contract_qualified"]
        == And(
            variables["contract_concluded"],
            variables["supplier_business"],
            variables["supplier_produced_or_procured_goods"],
            variables["goods_nonpersonal_use"],
            Not(variables["retail_sale_context"]),
        )
    )
    solver.add(
        outputs["delivery_term_requires_general_default"]
        == And(
            outputs["supply_contract_qualified"],
            Not(variables["transfer_term_defined"]),
            Not(variables["periodic_delivery"]),
        )
    )
    solver.add(
        outputs["negotiation_response_breach"]
        == And(
            variables["disagreements_received"],
            Not(variables["thirty_day_response_or_refusal"]),
        )
    )
    solver.add(
        outputs["negotiation_loss_issue"]
        == And(
            outputs["negotiation_response_breach"],
            variables["loss_claimed"],
            variables["causation_proven"],
        )
    )
    solver.add(
        outputs["monthly_delivery_default"]
        == And(
            variables["periodic_delivery"],
            Not(variables["delivery_periods_agreed"]),
        )
    )
    solver.add(
        outputs["agreed_delivery_schedule_controls"]
        == And(
            variables["periodic_delivery"],
            variables["delivery_periods_agreed"],
            variables["delivery_schedule_agreed"],
        )
    )
    solver.add(
        outputs["early_delivery_permitted"]
        == And(
            variables["early_delivery"],
            variables["buyer_consented_early_delivery"],
        )
    )
    solver.add(
        outputs["unauthorized_early_delivery"]
        == And(
            variables["early_delivery"],
            Not(variables["buyer_consented_early_delivery"]),
        )
    )
    solver.add(
        outputs["early_delivery_counts_next_period"]
        == And(
            variables["early_delivery"],
            variables["buyer_accepted_early_delivery"],
        )
    )
    solver.add(
        outputs["shipment_order_default"]
        == And(
            variables["shipment_order_required"],
            Not(variables["shipment_order_timely_complete"]),
        )
    )
    solver.add(
        outputs["shipment_order_loss_issue"]
        == And(
            outputs["shipment_order_default"],
            variables["loss_claimed"],
            variables["causation_proven"],
        )
    )
    solver.add(
        outputs["supplier_transport_choice"]
        == And(
            Not(variables["transport_method_agreed"]),
            variables["supplier_selected_transport"],
        )
    )
    solver.add(
        outputs["makeup_delivery_required"]
        == And(
            variables["quantity_shortfall"],
            variables["contract_term_continues"],
            Not(variables["buyer_refused_late_makeup_by_notice"]),
        )
    )
    solver.add(
        outputs["late_makeup_refusal_effective"]
        == And(
            variables["quantity_shortfall"],
            variables["buyer_refused_late_makeup_by_notice"],
        )
    )
    solver.add(
        outputs["cross_assortment_offset_barred"]
        == And(
            variables["cross_assortment_offset"],
            Not(variables["buyer_consented_offset"]),
        )
    )
    solver.add(
        outputs["makeup_assortment_default_to_prior_period"]
        == And(
            variables["quantity_shortfall"],
            Not(variables["makeup_assortment_agreed"]),
            variables["prior_period_assortment_proven"],
        )
    )
    solver.add(
        outputs["acceptance_duties_satisfied"]
        == And(
            variables["buyer_received_goods"],
            variables["inspection_timely"],
            Or(Not(variables["discrepancy_found"]), variables["prompt_written_notice"]),
        )
    )
    solver.add(
        outputs["acceptance_inspection_gap"]
        == And(
            variables["buyer_received_goods"],
            Not(variables["inspection_timely"]),
        )
    )
    solver.add(
        outputs["acceptance_notice_gap"]
        == And(
            variables["buyer_received_goods"],
            variables["discrepancy_found"],
            Not(variables["prompt_written_notice"]),
        )
    )
    solver.add(
        outputs["transport_acceptance_issue"]
        == Or(variables["documents_mismatch"], variables["consignee_refused_goods"])
    )
    solver.add(
        outputs["responsible_custody_duties_satisfied"]
        == And(
            variables["lawful_refusal"],
            variables["goods_preserved"],
            variables["supplier_notified"],
        )
    )
    solver.add(
        outputs["responsible_custody_gap"]
        == And(
            variables["lawful_refusal"],
            Or(
                Not(variables["goods_preserved"]),
                Not(variables["supplier_notified"]),
            ),
        )
    )
    solver.add(
        outputs["supplier_custody_cost_liability"]
        == And(
            outputs["responsible_custody_duties_satisfied"],
            variables["custody_expenses_documented"],
        )
    )
    solver.add(
        outputs["buyer_disposal_available"]
        == And(
            outputs["responsible_custody_duties_satisfied"],
            Not(variables["supplier_disposed_reasonable_time"]),
            variables["buyer_realized_or_returned_goods"],
        )
    )
    solver.add(
        outputs["supplier_payment_claim_after_unlawful_refusal"]
        == And(
            variables["unlawful_refusal"],
            variables["supplier_demanded_payment_after_refusal"],
            Not(variables["buyer_paid"]),
        )
    )
    solver.add(
        outputs["selection_supplier_remedy_available"]
        == And(
            variables["buyer_failed_selection"],
            variables["supplier_notified_readiness"],
        )
    )
    solver.add(
        outputs["buyer_payment_claim_available"]
        == And(
            variables["consignee_payment_duty"],
            variables["consignee_failed_payment"],
            Not(variables["buyer_paid"]),
        )
    )
    solver.add(
        outputs["container_return_breach"]
        == And(
            variables["returnable_container"],
            variables["container_return_due"],
            Not(variables["container_returned"]),
        )
    )
    solver.add(
        outputs["quality_remedies_available"]
        == And(
            variables["quality_defect"],
            Not(variables["defect_promptly_cured_or_replaced"]),
        )
    )
    solver.add(
        outputs["quality_remedies_displaced_by_prompt_cure"]
        == And(
            variables["quality_defect"],
            variables["defect_promptly_cured_or_replaced"],
        )
    )
    solver.add(outputs["retail_purchaser_direct_demands"] == variables["retail_purchaser_claim"])
    solver.add(
        outputs["completeness_remedies_available"]
        == And(
            variables["incomplete_goods"],
            Not(variables["incompleteness_promptly_cured_or_replaced"]),
        )
    )
    solver.add(
        outputs["completeness_remedies_displaced_by_prompt_cure"]
        == And(
            variables["incomplete_goods"],
            variables["incompleteness_promptly_cured_or_replaced"],
        )
    )
    unremedied_quality_or_completeness = Or(
        And(
            variables["quality_defect"],
            Not(variables["defect_promptly_cured_or_replaced"]),
        ),
        And(
            variables["incomplete_goods"],
            Not(variables["incompleteness_promptly_cured_or_replaced"]),
        ),
    )
    unremedied_nonconformity = Or(
        And(
            variables["quantity_shortfall"],
            Not(variables["actual_replenishment_completed"]),
        ),
        unremedied_quality_or_completeness,
    )
    solver.add(
        outputs["cover_purchase_cost_recovery"]
        == And(
            unremedied_nonconformity,
            variables["buyer_acquired_substitute"],
            variables["substitute_expenses_reasonable_documented"],
        )
    )
    solver.add(
        outputs["payment_withholding_available"]
        == And(unremedied_quality_or_completeness, variables["payment_withheld"])
    )
    solver.add(
        outputs["penalty_continues_until_replenishment"]
        == And(
            variables["penalty_applies_to_short_or_late"],
            variables["replenishment_duty_continues"],
            Not(variables["actual_replenishment_completed"]),
        )
    )
    solver.add(
        outputs["default_contract_allocation_required"]
        == And(
            variables["multiple_supply_contracts"],
            Not(variables["performance_allocation_designated"]),
        )
    )
    solver.add(
        outputs["supplier_material_breach"]
        == Or(variables["repeated_late_delivery"], variables["irremediable_defect"])
    )
    solver.add(
        outputs["buyer_material_breach"]
        == Or(
            variables["repeated_payment_default"],
            variables["repeated_selection_failure"],
        )
    )
    solver.add(
        outputs["supply_unilateral_refusal_effective"]
        == And(
            variables["contract_concluded"],
            Or(outputs["supplier_material_breach"], outputs["buyer_material_breach"]),
            variables["unilateral_refusal_notice_delivered"],
        )
    )
    solver.add(
        outputs["concrete_price_damages_available"]
        == And(
            variables["contract_terminated"],
            variables["replacement_transaction_made"],
            variables["replacement_transaction_reasonable"],
            variables["replacement_transaction_timely"],
            variables["contract_price_proven"],
            variables["replacement_price_proven"],
            variables["loss_claimed"],
            variables["causation_proven"],
        )
    )
    solver.add(
        outputs["abstract_current_price_damages_available"]
        == And(
            variables["contract_terminated"],
            Not(variables["replacement_transaction_made"]),
            variables["contract_price_proven"],
            variables["current_price_available"],
            variables["current_price_proven"],
            variables["current_price_time_place_adjusted"],
            variables["loss_claimed"],
            variables["causation_proven"],
        )
    )
    solver.add(
        outputs["other_damages_preserved"]
        == And(
            variables["contract_terminated"],
            variables["loss_claimed"],
            variables["causation_proven"],
            variables["other_loss_proven"],
        )
    )
    solver.add(
        outputs["supply_breach_established"]
        == Or(
            variables["delivery_late"],
            outputs["unauthorized_early_delivery"],
            variables["quantity_shortfall"],
            variables["quality_defect"],
            variables["incomplete_goods"],
            outputs["shipment_order_default"],
            outputs["container_return_breach"],
            variables["consignee_failed_payment"],
            variables["buyer_failed_selection"],
            outputs["responsible_custody_gap"],
            variables["unlawful_refusal"],
        )
    )
    review_outputs = [
        outputs["delivery_term_requires_general_default"],
        outputs["negotiation_response_breach"],
        outputs["negotiation_loss_issue"],
        outputs["shipment_order_default"],
        outputs["shipment_order_loss_issue"],
        outputs["unauthorized_early_delivery"],
        outputs["makeup_delivery_required"],
        outputs["cross_assortment_offset_barred"],
        outputs["makeup_assortment_default_to_prior_period"],
        outputs["acceptance_inspection_gap"],
        outputs["acceptance_notice_gap"],
        outputs["transport_acceptance_issue"],
        outputs["responsible_custody_gap"],
        outputs["supplier_custody_cost_liability"],
        outputs["buyer_disposal_available"],
        outputs["supplier_payment_claim_after_unlawful_refusal"],
        outputs["selection_supplier_remedy_available"],
        outputs["buyer_payment_claim_available"],
        outputs["quality_remedies_available"],
        outputs["completeness_remedies_available"],
        outputs["cover_purchase_cost_recovery"],
        outputs["payment_withholding_available"],
        outputs["penalty_continues_until_replenishment"],
        outputs["default_contract_allocation_required"],
        outputs["supply_unilateral_refusal_effective"],
        outputs["concrete_price_damages_available"],
        outputs["abstract_current_price_damages_available"],
        outputs["other_damages_preserved"],
    ]
    solver.add(outputs["requires_human_supply_assessment"] == Or(*review_outputs))

    satisfiable = solver.check() == sat
    if not satisfiable:
        return SupplyEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            **{
                field_name: False
                for field_name in outputs
                if field_name != "requires_human_supply_assessment"
            },
            requires_human_supply_assessment=True,
            reasons_ru=["Набор фактов о договоре поставки противоречив."],
            warnings_ru=["Требуется повторная проверка исходных данных юристом."],
        )
    model = solver.model()
    values = {
        field_name: bool(model.eval(variable, model_completion=True))
        for field_name, variable in outputs.items()
    }
    reasons_ru = []
    if values["supply_contract_qualified"]:
        reasons_ru.append("Подтверждены квалифицирующие признаки договора поставки.")
    if values["delivery_term_requires_general_default"]:
        reasons_ru.append(
            "Прямой срок поставки не указан; требуется определить его по общим правилам статей 314 и 457 ГК РФ."
        )
    if values["makeup_delivery_required"]:
        reasons_ru.append("Недопоставка подлежит восполнению в пределах срока договора.")
    if values["negotiation_response_breach"]:
        reasons_ru.append("Выявлено нарушение срока ответа на предложение о разногласиях.")
    if values["shipment_order_default"]:
        reasons_ru.append("Не подтверждена своевременная полная отгрузочная разнарядка.")
    if values["unauthorized_early_delivery"]:
        reasons_ru.append("Досрочная поставка произведена без подтвержденного согласия покупателя.")
    if values["makeup_assortment_default_to_prior_period"]:
        reasons_ru.append(
            "Ассортимент восполнения определяется ассортиментом периода недопоставки."
        )
    if values["acceptance_inspection_gap"]:
        reasons_ru.append("Не подтверждена своевременная проверка принятого товара.")
    if values["acceptance_notice_gap"]:
        reasons_ru.append("Выявлен пробел в своевременном письменном извещении о расхождениях.")
    if values["transport_acceptance_issue"]:
        reasons_ru.append(
            "Приемка от перевозчика требует проверки транспортных документов и применимых транспортных правил."
        )
    if values["responsible_custody_gap"]:
        reasons_ru.append("Обязанности ответственного хранения подтверждены не полностью.")
    if values["supplier_payment_claim_after_unlawful_refusal"]:
        reasons_ru.append(
            "Подтверждены предпосылки требования оплаты при неправомерном отказе от товара."
        )
    if values["supply_unilateral_refusal_effective"]:
        reasons_ru.append("Подтверждены специальные предпосылки одностороннего отказа.")
    if values["concrete_price_damages_available"]:
        reasons_ru.append("Подтвержден конкретный расчет убытков по заменяющей сделке.")
    if values["abstract_current_price_damages_available"]:
        reasons_ru.append("Подтвержден абстрактный расчет убытков по текущей цене.")
    if values["supply_breach_established"]:
        reasons_ru.append("Выявлено нарушение специальной обязанности по договору поставки.")
    if not reasons_ru:
        reasons_ru.append("Активное специальное последствие договора поставки не подтверждено.")
    return SupplyEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        **values,
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет формальные предпосылки статей 506–524 ГК РФ и не подменяет квалификацию суда.",
            "Разумный срок, существенность, повторность, качество уведомлений и доказанность цен оценивает юрист.",
            "Инструкции П-6 и П-7 учитываются как договорный порядок приемки только при соответствующей отсылке.",
        ],
    )
