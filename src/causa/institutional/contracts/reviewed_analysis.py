from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causa.core.bootstrap import (
    BootstrapReviewStatus,
    DEFAULT_BOOTSTRAP_SCHEMA_VERSION,
    FormalObligationRule,
    FormalTranslationResult,
    ReviewedNormJSON,
    translate_reviewed_norm,
)
from causa.core.models import LegalSource, SourceType
from causa.core.temporal_validity import (
    SourceApplicabilityEvaluation,
    evaluate_source_applicability,
)
from causa.institutional.contracts.authority_model import (
    AuthorityEvaluation,
    evaluate_source_authority,
)
from causa.institutional.contracts.legal_operators import (
    ContractCounterfactualSensitivityReport,
    run_contract_counterfactual_sensitivity,
)
from causa.institutional.contracts.liability import (
    LIABILITY_EVIDENCE_SCHEMA_VERSION,
    LiabilityConstraintSet,
    LiabilityEvaluation,
    LiabilityEvidenceMappingResult,
    ReviewedLiabilityEvidence,
    build_liability_constraint_set,
    evaluate_liability_constraints,
    map_reviewed_liability_evidence,
)
from causa.institutional.contracts.formation import (
    FORMATION_EVIDENCE_SCHEMA_VERSION,
    FormationConstraintSet,
    FormationEvaluation,
    FormationEvidenceMappingResult,
    ReviewedFormationEvidence,
    build_formation_constraint_set,
    evaluate_formation_constraints,
    map_reviewed_formation_evidence,
)
from causa.institutional.contracts.temporal_effect import (
    TEMPORAL_EFFECT_EVIDENCE_SCHEMA_VERSION,
    ReviewedTemporalEffectEvidence,
    TemporalEffectConstraintSet,
    TemporalEffectEvaluation,
    TemporalEffectEvidenceMappingResult,
    build_temporal_effect_constraint_set,
    evaluate_temporal_effect_constraints,
    map_reviewed_temporal_effect_evidence,
)
from causa.institutional.contracts.limitation import (
    LIMITATION_EVIDENCE_SCHEMA_VERSION,
    LimitationConstraintSet,
    LimitationEvaluation,
    LimitationEvidenceMappingResult,
    ReviewedLimitationEvidence,
    build_limitation_constraint_set,
    evaluate_limitation_constraints,
    map_reviewed_limitation_evidence,
)
from causa.institutional.contracts.interpretation import (
    INTERPRETATION_EVIDENCE_SCHEMA_VERSION,
    InterpretationConstraintSet,
    InterpretationEvaluation,
    InterpretationEvidenceMappingResult,
    ReviewedInterpretationEvidence,
    build_interpretation_constraint_set,
    evaluate_interpretation_constraints,
    map_reviewed_interpretation_evidence,
)
from causa.institutional.contracts.form import (
    FORM_EVIDENCE_SCHEMA_VERSION,
    FormConstraintSet,
    FormEvaluation,
    FormEvidenceMappingResult,
    ReviewedFormEvidence,
    build_form_constraint_set,
    evaluate_form_constraints,
    map_reviewed_form_evidence,
)
from causa.institutional.contracts.preliminary import (
    PRELIMINARY_EVIDENCE_SCHEMA_VERSION,
    PreliminaryConstraintSet,
    PreliminaryEvaluation,
    PreliminaryEvidenceMappingResult,
    ReviewedPreliminaryEvidence,
    build_preliminary_constraint_set,
    evaluate_preliminary_constraints,
    map_reviewed_preliminary_evidence,
)
from causa.institutional.contracts.adhesion import (
    ADHESION_EVIDENCE_SCHEMA_VERSION,
    AdhesionConstraintSet,
    AdhesionEvaluation,
    AdhesionEvidenceMappingResult,
    ReviewedAdhesionEvidence,
    build_adhesion_constraint_set,
    evaluate_adhesion_constraints,
    map_reviewed_adhesion_evidence,
)
from causa.institutional.contracts.representations import (
    REPRESENTATIONS_EVIDENCE_SCHEMA_VERSION,
    RepresentationsConstraintSet,
    RepresentationsEvaluation,
    RepresentationsEvidenceMappingResult,
    ReviewedRepresentationsEvidence,
    build_representations_constraint_set,
    evaluate_representations_constraints,
    map_reviewed_representations_evidence,
)
from causa.institutional.contracts.precontractual import (
    PRECONTRACTUAL_EVIDENCE_SCHEMA_VERSION,
    PrecontractualConstraintSet,
    PrecontractualEvaluation,
    PrecontractualEvidenceMappingResult,
    ReviewedPrecontractualEvidence,
    build_precontractual_constraint_set,
    evaluate_precontractual_constraints,
    map_reviewed_precontractual_evidence,
)
from causa.institutional.contracts.framework import (
    FRAMEWORK_EVIDENCE_SCHEMA_VERSION,
    FrameworkConstraintSet,
    FrameworkEvaluation,
    FrameworkEvidenceMappingResult,
    ReviewedFrameworkEvidence,
    build_framework_constraint_set,
    evaluate_framework_constraints,
    map_reviewed_framework_evidence,
)
from causa.institutional.contracts.freedom import (
    FREEDOM_EVIDENCE_SCHEMA_VERSION,
    FreedomConstraintSet,
    FreedomEvaluation,
    FreedomEvidenceMappingResult,
    ReviewedFreedomEvidence,
    build_freedom_constraint_set,
    evaluate_freedom_constraints,
    map_reviewed_freedom_evidence,
)
from causa.institutional.contracts.general_obligations import (
    GENERAL_OBLIGATIONS_EVIDENCE_SCHEMA_VERSION,
    GeneralObligationsConstraintSet,
    GeneralObligationsEvaluation,
    GeneralObligationsEvidenceMappingResult,
    ReviewedGeneralObligationsEvidence,
    build_general_obligations_constraint_set,
    evaluate_general_obligations_constraints,
    map_reviewed_general_obligations_evidence,
)
from causa.institutional.contracts.retail_sale import (
    RETAIL_SALE_EVIDENCE_SCHEMA_VERSION,
    ReviewedRetailSaleEvidence,
    RetailSaleConstraintSet,
    RetailSaleEvaluation,
    RetailSaleEvidenceMappingResult,
    build_retail_sale_constraint_set,
    evaluate_retail_sale_constraints,
    map_reviewed_retail_sale_evidence,
)
from causa.institutional.contracts.contractation import (
    CONTRACTATION_EVIDENCE_SCHEMA_VERSION,
    ContractationConstraintSet,
    ContractationEvaluation,
    ContractationEvidenceMappingResult,
    ReviewedContractationEvidence,
    build_contractation_constraint_set,
    evaluate_contractation_constraints,
    map_reviewed_contractation_evidence,
)
from causa.institutional.contracts.energy_supply import (
    ENERGY_SUPPLY_EVIDENCE_SCHEMA_VERSION,
    EnergySupplyConstraintSet,
    EnergySupplyEvaluation,
    EnergySupplyEvidenceMappingResult,
    ReviewedEnergySupplyEvidence,
    build_energy_supply_constraint_set,
    evaluate_energy_supply_constraints,
    map_reviewed_energy_supply_evidence,
)
from causa.institutional.contracts.barter import (
    BARTER_EVIDENCE_SCHEMA_VERSION,
    BarterConstraintSet,
    BarterEvaluation,
    BarterEvidenceMappingResult,
    ReviewedBarterEvidence,
    build_barter_constraint_set,
    evaluate_barter_constraints,
    map_reviewed_barter_evidence,
)
from causa.institutional.contracts.annuity import (
    ANNUITY_EVIDENCE_SCHEMA_VERSION,
    AnnuityConstraintSet,
    AnnuityEvaluation,
    AnnuityEvidenceMappingResult,
    ReviewedAnnuityEvidence,
    build_annuity_constraint_set,
    evaluate_annuity_constraints,
    map_reviewed_annuity_evidence,
)
from causa.institutional.contracts.lease import (
    LEASE_EVIDENCE_SCHEMA_VERSION,
    LeaseConstraintSet,
    LeaseEvaluation,
    LeaseEvidenceMappingResult,
    ReviewedLeaseEvidence,
    build_lease_constraint_set,
    evaluate_lease_constraints,
    map_reviewed_lease_evidence,
)
from causa.institutional.contracts.rental import (
    RENTAL_EVIDENCE_SCHEMA_VERSION,
    RentalConstraintSet,
    RentalEvaluation,
    RentalEvidenceMappingResult,
    ReviewedRentalEvidence,
    build_rental_constraint_set,
    evaluate_rental_constraints,
    map_reviewed_rental_evidence,
)
from causa.institutional.contracts.vehicle_lease import (
    VEHICLE_LEASE_EVIDENCE_SCHEMA_VERSION,
    ReviewedVehicleLeaseEvidence,
    VehicleLeaseConstraintSet,
    VehicleLeaseEvaluation,
    VehicleLeaseEvidenceMappingResult,
    build_vehicle_lease_constraint_set,
    evaluate_vehicle_lease_constraints,
    map_reviewed_vehicle_lease_evidence,
)
from causa.institutional.contracts.building_lease import (
    BUILDING_LEASE_EVIDENCE_SCHEMA_VERSION,
    BuildingLeaseConstraintSet,
    BuildingLeaseEvaluation,
    BuildingLeaseEvidenceMappingResult,
    ReviewedBuildingLeaseEvidence,
    build_building_lease_constraint_set,
    evaluate_building_lease_constraints,
    map_reviewed_building_lease_evidence,
)
from causa.institutional.contracts.enterprise_lease import (
    ENTERPRISE_LEASE_EVIDENCE_SCHEMA_VERSION,
    EnterpriseLeaseConstraintSet,
    EnterpriseLeaseEvaluation,
    EnterpriseLeaseEvidenceMappingResult,
    ReviewedEnterpriseLeaseEvidence,
    build_enterprise_lease_constraint_set,
    evaluate_enterprise_lease_constraints,
    map_reviewed_enterprise_lease_evidence,
)
from causa.institutional.contracts.leasing import (
    LEASING_EVIDENCE_SCHEMA_VERSION,
    LeasingConstraintSet,
    LeasingEvaluation,
    LeasingEvidenceMappingResult,
    ReviewedLeasingEvidence,
    build_leasing_constraint_set,
    evaluate_leasing_constraints,
    map_reviewed_leasing_evidence,
)
from causa.institutional.contracts.residential_lease import (
    RESIDENTIAL_LEASE_EVIDENCE_SCHEMA_VERSION,
    ResidentialLeaseConstraintSet,
    ResidentialLeaseEvaluation,
    ResidentialLeaseEvidenceMappingResult,
    ReviewedResidentialLeaseEvidence,
    build_residential_lease_constraint_set,
    evaluate_residential_lease_constraints,
    map_reviewed_residential_lease_evidence,
)
from causa.institutional.contracts.gratuitous_use import (
    GRATUITOUS_USE_EVIDENCE_SCHEMA_VERSION,
    GratuitousUseConstraintSet,
    GratuitousUseEvaluation,
    GratuitousUseEvidenceMappingResult,
    ReviewedGratuitousUseEvidence,
    build_gratuitous_use_constraint_set,
    evaluate_gratuitous_use_constraints,
    map_reviewed_gratuitous_use_evidence,
)
from causa.institutional.contracts.work_contract import (
    WORK_CONTRACT_EVIDENCE_SCHEMA_VERSION,
    ReviewedWorkContractEvidence,
    WorkContractConstraintSet,
    WorkContractEvaluation,
    WorkContractEvidenceMappingResult,
    build_work_contract_constraint_set,
    evaluate_work_contract_constraints,
    map_reviewed_work_contract_evidence,
)
from causa.institutional.contracts.consumer_work import (
    CONSUMER_WORK_EVIDENCE_SCHEMA_VERSION,
    ConsumerWorkConstraintSet,
    ConsumerWorkEvaluation,
    ConsumerWorkEvidenceMappingResult,
    ReviewedConsumerWorkEvidence,
    build_consumer_work_constraint_set,
    evaluate_consumer_work_constraints,
    map_reviewed_consumer_work_evidence,
)
from causa.institutional.contracts.construction_contract import (
    CONSTRUCTION_CONTRACT_EVIDENCE_SCHEMA_VERSION,
    ConstructionContractConstraintSet,
    ConstructionContractEvaluation,
    ConstructionContractEvidenceMappingResult,
    ReviewedConstructionContractEvidence,
    build_construction_contract_constraint_set,
    evaluate_construction_contract_constraints,
    map_reviewed_construction_contract_evidence,
)
from causa.institutional.contracts.design_work import (
    DESIGN_WORK_EVIDENCE_SCHEMA_VERSION,
    DesignWorkConstraintSet,
    DesignWorkEvaluation,
    DesignWorkEvidenceMappingResult,
    ReviewedDesignWorkEvidence,
    build_design_work_constraint_set,
    evaluate_design_work_constraints,
    map_reviewed_design_work_evidence,
)
from causa.institutional.contracts.state_work import (
    STATE_WORK_EVIDENCE_SCHEMA_VERSION,
    ReviewedStateWorkEvidence,
    StateWorkConstraintSet,
    StateWorkEvaluation,
    StateWorkEvidenceMappingResult,
    build_state_work_constraint_set,
    evaluate_state_work_constraints,
    map_reviewed_state_work_evidence,
)
from causa.institutional.contracts.research_work import (
    RESEARCH_WORK_EVIDENCE_SCHEMA_VERSION,
    ResearchWorkConstraintSet,
    ResearchWorkEvaluation,
    ResearchWorkEvidenceMappingResult,
    ReviewedResearchWorkEvidence,
    build_research_work_constraint_set,
    evaluate_research_work_constraints,
    map_reviewed_research_work_evidence,
)
from causa.institutional.contracts.paid_services import (
    PAID_SERVICES_EVIDENCE_SCHEMA_VERSION,
    PaidServicesConstraintSet,
    PaidServicesEvaluation,
    PaidServicesEvidenceMappingResult,
    ReviewedPaidServicesEvidence,
    build_paid_services_constraint_set,
    evaluate_paid_services_constraints,
    map_reviewed_paid_services_evidence,
)
from causa.institutional.contracts.carriage import (
    CARRIAGE_EVIDENCE_SCHEMA_VERSION,
    CarriageConstraintSet,
    CarriageEvaluation,
    CarriageEvidenceMappingResult,
    ReviewedCarriageEvidence,
    build_carriage_constraint_set,
    evaluate_carriage_constraints,
    map_reviewed_carriage_evidence,
)
from causa.institutional.contracts.forwarding import (
    FORWARDING_EVIDENCE_SCHEMA_VERSION,
    ForwardingConstraintSet,
    ForwardingEvaluation,
    ForwardingEvidenceMappingResult,
    ReviewedForwardingEvidence,
    build_forwarding_constraint_set,
    evaluate_forwarding_constraints,
    map_reviewed_forwarding_evidence,
)
from causa.institutional.contracts.gift import (
    GIFT_EVIDENCE_SCHEMA_VERSION,
    GiftConstraintSet,
    GiftEvaluation,
    GiftEvidenceMappingResult,
    ReviewedGiftEvidence,
    build_gift_constraint_set,
    evaluate_gift_constraints,
    map_reviewed_gift_evidence,
)
from causa.institutional.contracts.enterprise_sale import (
    ENTERPRISE_SALE_EVIDENCE_SCHEMA_VERSION,
    EnterpriseSaleConstraintSet,
    EnterpriseSaleEvaluation,
    EnterpriseSaleEvidenceMappingResult,
    ReviewedEnterpriseSaleEvidence,
    build_enterprise_sale_constraint_set,
    evaluate_enterprise_sale_constraints,
    map_reviewed_enterprise_sale_evidence,
)
from causa.institutional.contracts.real_estate_sale import (
    REAL_ESTATE_SALE_EVIDENCE_SCHEMA_VERSION,
    RealEstateSaleConstraintSet,
    RealEstateSaleEvaluation,
    RealEstateSaleEvidenceMappingResult,
    ReviewedRealEstateSaleEvidence,
    build_real_estate_sale_constraint_set,
    evaluate_real_estate_sale_constraints,
    map_reviewed_real_estate_sale_evidence,
)
from causa.institutional.contracts.state_supply import (
    STATE_SUPPLY_EVIDENCE_SCHEMA_VERSION,
    ReviewedStateSupplyEvidence,
    StateSupplyConstraintSet,
    StateSupplyEvaluation,
    StateSupplyEvidenceMappingResult,
    build_state_supply_constraint_set,
    evaluate_state_supply_constraints,
    map_reviewed_state_supply_evidence,
)
from causa.institutional.contracts.option import (
    OPTION_EVIDENCE_SCHEMA_VERSION,
    OptionConstraintSet,
    OptionEvaluation,
    OptionEvidenceMappingResult,
    ReviewedOptionEvidence,
    build_option_constraint_set,
    evaluate_option_constraints,
    map_reviewed_option_evidence,
)
from causa.institutional.contracts.procedure import (
    PROCEDURE_EVIDENCE_SCHEMA_VERSION,
    ProcedureConstraintSet,
    ProcedureEvaluation,
    ProcedureEvidenceMappingResult,
    ReviewedProcedureEvidence,
    build_procedure_constraint_set,
    evaluate_procedure_constraints,
    map_reviewed_procedure_evidence,
)
from causa.institutional.contracts.public_contract import (
    PUBLIC_CONTRACT_EVIDENCE_SCHEMA_VERSION,
    PublicContractConstraintSet,
    PublicContractEvaluation,
    PublicContractEvidenceMappingResult,
    ReviewedPublicContractEvidence,
    build_public_contract_constraint_set,
    evaluate_public_contract_constraints,
    map_reviewed_public_contract_evidence,
)
from causa.institutional.contracts.third_party import (
    THIRD_PARTY_EVIDENCE_SCHEMA_VERSION,
    ReviewedThirdPartyEvidence,
    ThirdPartyConstraintSet,
    ThirdPartyEvaluation,
    ThirdPartyEvidenceMappingResult,
    build_third_party_constraint_set,
    evaluate_third_party_constraints,
    map_reviewed_third_party_evidence,
)
from causa.institutional.contracts.termination import (
    TERMINATION_EVIDENCE_SCHEMA_VERSION,
    ReviewedTerminationEvidence,
    TerminationConstraintSet,
    TerminationEvaluation,
    TerminationEvidenceMappingResult,
    build_termination_constraint_set,
    evaluate_termination_constraints,
    map_reviewed_termination_evidence,
)
from causa.institutional.contracts.invalidity import (
    INVALIDITY_EVIDENCE_SCHEMA_VERSION,
    InvalidityConstraintSet,
    InvalidityEvaluation,
    InvalidityEvidenceMappingResult,
    ReviewedInvalidityEvidence,
    build_invalidity_constraint_set,
    evaluate_invalidity_constraints,
    map_reviewed_invalidity_evidence,
)
from causa.institutional.contracts.security import (
    SECURITY_EVIDENCE_SCHEMA_VERSION,
    ReviewedSecurityEvidence,
    SecurityConstraintSet,
    SecurityEvaluation,
    SecurityEvidenceMappingResult,
    build_security_constraint_set,
    evaluate_security_constraints,
    map_reviewed_security_evidence,
)
from causa.institutional.contracts.obligation_dynamics import (
    OBLIGATION_DYNAMICS_EVIDENCE_SCHEMA_VERSION,
    ObligationDynamicsConstraintSet,
    ObligationDynamicsEvaluation,
    ObligationDynamicsEvidenceMappingResult,
    ReviewedObligationDynamicsEvidence,
    build_obligation_dynamics_constraint_set,
    evaluate_obligation_dynamics_constraints,
    map_reviewed_obligation_dynamics_evidence,
)
from causa.institutional.contracts.performance_remedies import (
    PERFORMANCE_REMEDIES_EVIDENCE_SCHEMA_VERSION,
    PerformanceRemediesConstraintSet,
    PerformanceRemediesEvaluation,
    PerformanceRemediesEvidenceMappingResult,
    ReviewedPerformanceRemediesEvidence,
    build_performance_remedies_constraint_set,
    evaluate_performance_remedies_constraints,
    map_reviewed_performance_remedies_evidence,
)
from causa.institutional.contracts.sale import (
    SALE_EVIDENCE_SCHEMA_VERSION,
    ReviewedSaleEvidence,
    SaleConstraintSet,
    SaleEvaluation,
    SaleEvidenceMappingResult,
    build_sale_constraint_set,
    evaluate_sale_constraints,
    map_reviewed_sale_evidence,
)
from causa.institutional.contracts.supply import (
    SUPPLY_EVIDENCE_SCHEMA_VERSION,
    ReviewedSupplyEvidence,
    SupplyConstraintSet,
    SupplyEvaluation,
    SupplyEvidenceMappingResult,
    build_supply_constraint_set,
    evaluate_supply_constraints,
    map_reviewed_supply_evidence,
)
from causa.institutional.contracts.temporal import (
    ContractTemporalFacts,
    TemporalEvaluation,
    evaluate_delivery_due_date,
)
from causa.reasoning.formal_checks import (
    ConstraintEvaluation,
    ConstraintSet,
    ObligationFactSet,
    build_obligation_constraint_set,
    evaluate_obligation_constraints,
)
from causa.reasoning.counterfactual import CounterfactualBudget


CASE_EVIDENCE_SCHEMA_VERSION = "contracts.case-evidence.v9"
EVIDENCE_MAPPING_VERSION = "contracts-reviewed-evidence-to-facts-v0"
ANALYSIS_PIPELINE_VERSION = "contracts-reviewed-analysis-v9"


class ContractEvidencePredicate(str, Enum):
    DUTY_EXISTS = "duty_exists"
    VALID_EXCEPTION_APPLIES = "valid_exception_applies"
    PERFORMANCE_COMPLETED = "performance_completed"
    PERFORMANCE_NONCONFORMING = "performance_nonconforming"
    PAYMENT_DUTY_EXISTS = "payment_duty_exists"
    PAYMENT_DUE = "payment_due"
    PAYMENT_MISSED = "payment_missed"
    PAYMENT_DEFENSE_APPLIES = "payment_defense_applies"
    LOSS_CLAIMED = "loss_claimed"
    CAUSATION_ESTABLISHED = "causation_established"
    REMEDY_REQUESTED = "remedy_requested"
    LIMITATION_PERIOD_EXPIRED = "limitation_period_expired"


REQUIRED_EVIDENCE_PREDICATES = frozenset(ContractEvidencePredicate)


class CaseEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ContractEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCaseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CASE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CaseEvidenceAssertion, ...]
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicate_predicates(self) -> "ReviewedCaseEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Case evidence contains duplicate predicates.")
        return self


class ReviewedTemporalEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    agreed_due_date: date | None = None
    actual_performance_date: date | None = None
    evaluation_date: date
    source_refs: tuple[str, ...] = Field(min_length=1)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None


class ReviewedAuthorityInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    candidate_source_ids: tuple[str, ...] = Field(min_length=1)
    evaluation_date: date
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicate_sources(self) -> "ReviewedAuthorityInput":
        if len(self.candidate_source_ids) != len(set(self.candidate_source_ids)):
            raise ValueError("Authority input contains duplicate candidate sources.")
        return self


class ReviewedContractAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    reviewed_norm: ReviewedNormJSON
    case_evidence: ReviewedCaseEvidence
    temporal_evidence: ReviewedTemporalEvidence
    authority_input: ReviewedAuthorityInput
    formation_evidence: ReviewedFormationEvidence
    temporal_effect_evidence: ReviewedTemporalEffectEvidence
    limitation_evidence: ReviewedLimitationEvidence
    interpretation_evidence: ReviewedInterpretationEvidence
    form_evidence: ReviewedFormEvidence
    preliminary_evidence: ReviewedPreliminaryEvidence
    third_party_evidence: ReviewedThirdPartyEvidence
    public_contract_evidence: ReviewedPublicContractEvidence
    adhesion_evidence: ReviewedAdhesionEvidence
    representations_evidence: ReviewedRepresentationsEvidence
    precontractual_evidence: ReviewedPrecontractualEvidence
    option_evidence: ReviewedOptionEvidence
    framework_evidence: ReviewedFrameworkEvidence
    freedom_evidence: ReviewedFreedomEvidence
    procedure_evidence: ReviewedProcedureEvidence
    general_obligations_evidence: ReviewedGeneralObligationsEvidence
    retail_sale_evidence: ReviewedRetailSaleEvidence
    state_supply_evidence: ReviewedStateSupplyEvidence
    contractation_evidence: ReviewedContractationEvidence
    energy_supply_evidence: ReviewedEnergySupplyEvidence
    real_estate_sale_evidence: ReviewedRealEstateSaleEvidence
    enterprise_sale_evidence: ReviewedEnterpriseSaleEvidence
    barter_evidence: ReviewedBarterEvidence
    gift_evidence: ReviewedGiftEvidence
    annuity_evidence: ReviewedAnnuityEvidence
    lease_evidence: ReviewedLeaseEvidence
    rental_evidence: ReviewedRentalEvidence
    vehicle_lease_evidence: ReviewedVehicleLeaseEvidence
    building_lease_evidence: ReviewedBuildingLeaseEvidence
    enterprise_lease_evidence: ReviewedEnterpriseLeaseEvidence
    leasing_evidence: ReviewedLeasingEvidence
    residential_lease_evidence: ReviewedResidentialLeaseEvidence
    gratuitous_use_evidence: ReviewedGratuitousUseEvidence
    work_contract_evidence: ReviewedWorkContractEvidence
    consumer_work_evidence: ReviewedConsumerWorkEvidence
    construction_contract_evidence: ReviewedConstructionContractEvidence
    design_work_evidence: ReviewedDesignWorkEvidence
    state_work_evidence: ReviewedStateWorkEvidence
    research_work_evidence: ReviewedResearchWorkEvidence
    paid_services_evidence: ReviewedPaidServicesEvidence
    carriage_evidence: ReviewedCarriageEvidence
    forwarding_evidence: ReviewedForwardingEvidence
    invalidity_evidence: ReviewedInvalidityEvidence
    security_evidence: ReviewedSecurityEvidence
    obligation_dynamics_evidence: ReviewedObligationDynamicsEvidence
    performance_remedies_evidence: ReviewedPerformanceRemediesEvidence
    sale_evidence: ReviewedSaleEvidence
    supply_evidence: ReviewedSupplyEvidence
    termination_evidence: ReviewedTerminationEvidence
    liability_evidence: ReviewedLiabilityEvidence


class FactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)
    formal_atom_refs: list[str] = Field(default_factory=list)


class CaseEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    formal_rule_id: str
    facts: ObligationFactSet
    provenance: list[FactProvenance] = Field(default_factory=list)


class ReviewedContractAnalysisResult(BaseModel):
    request_id: str
    case_id: str
    pipeline_version: str
    reviewer_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    formal_translation: FormalTranslationResult
    temporal_facts: ContractTemporalFacts
    temporal_evaluation: TemporalEvaluation
    source_applicability: SourceApplicabilityEvaluation
    evidence_mapping: CaseEvidenceMappingResult
    constraint_set: ConstraintSet
    constraint_evaluation: ConstraintEvaluation
    formation_evidence_mapping: FormationEvidenceMappingResult
    formation_constraint_set: FormationConstraintSet
    formation_evaluation: FormationEvaluation
    temporal_effect_evidence_mapping: TemporalEffectEvidenceMappingResult
    temporal_effect_constraint_set: TemporalEffectConstraintSet
    temporal_effect_evaluation: TemporalEffectEvaluation
    limitation_evidence_mapping: LimitationEvidenceMappingResult
    limitation_constraint_set: LimitationConstraintSet
    limitation_evaluation: LimitationEvaluation
    interpretation_evidence_mapping: InterpretationEvidenceMappingResult
    interpretation_constraint_set: InterpretationConstraintSet
    interpretation_evaluation: InterpretationEvaluation
    form_evidence_mapping: FormEvidenceMappingResult
    form_constraint_set: FormConstraintSet
    form_evaluation: FormEvaluation
    preliminary_evidence_mapping: PreliminaryEvidenceMappingResult
    preliminary_constraint_set: PreliminaryConstraintSet
    preliminary_evaluation: PreliminaryEvaluation
    third_party_evidence_mapping: ThirdPartyEvidenceMappingResult
    third_party_constraint_set: ThirdPartyConstraintSet
    third_party_evaluation: ThirdPartyEvaluation
    public_contract_evidence_mapping: PublicContractEvidenceMappingResult
    public_contract_constraint_set: PublicContractConstraintSet
    public_contract_evaluation: PublicContractEvaluation
    adhesion_evidence_mapping: AdhesionEvidenceMappingResult
    adhesion_constraint_set: AdhesionConstraintSet
    adhesion_evaluation: AdhesionEvaluation
    representations_evidence_mapping: RepresentationsEvidenceMappingResult
    representations_constraint_set: RepresentationsConstraintSet
    representations_evaluation: RepresentationsEvaluation
    precontractual_evidence_mapping: PrecontractualEvidenceMappingResult
    precontractual_constraint_set: PrecontractualConstraintSet
    precontractual_evaluation: PrecontractualEvaluation
    option_evidence_mapping: OptionEvidenceMappingResult
    option_constraint_set: OptionConstraintSet
    option_evaluation: OptionEvaluation
    framework_evidence_mapping: FrameworkEvidenceMappingResult
    framework_constraint_set: FrameworkConstraintSet
    framework_evaluation: FrameworkEvaluation
    freedom_evidence_mapping: FreedomEvidenceMappingResult
    freedom_constraint_set: FreedomConstraintSet
    freedom_evaluation: FreedomEvaluation
    procedure_evidence_mapping: ProcedureEvidenceMappingResult
    procedure_constraint_set: ProcedureConstraintSet
    procedure_evaluation: ProcedureEvaluation
    general_obligations_evidence_mapping: GeneralObligationsEvidenceMappingResult
    general_obligations_constraint_set: GeneralObligationsConstraintSet
    general_obligations_evaluation: GeneralObligationsEvaluation
    retail_sale_evidence_mapping: RetailSaleEvidenceMappingResult
    retail_sale_constraint_set: RetailSaleConstraintSet
    retail_sale_evaluation: RetailSaleEvaluation
    state_supply_evidence_mapping: StateSupplyEvidenceMappingResult
    state_supply_constraint_set: StateSupplyConstraintSet
    state_supply_evaluation: StateSupplyEvaluation
    contractation_evidence_mapping: ContractationEvidenceMappingResult
    contractation_constraint_set: ContractationConstraintSet
    contractation_evaluation: ContractationEvaluation
    energy_supply_evidence_mapping: EnergySupplyEvidenceMappingResult
    energy_supply_constraint_set: EnergySupplyConstraintSet
    energy_supply_evaluation: EnergySupplyEvaluation
    real_estate_sale_evidence_mapping: RealEstateSaleEvidenceMappingResult
    real_estate_sale_constraint_set: RealEstateSaleConstraintSet
    real_estate_sale_evaluation: RealEstateSaleEvaluation
    enterprise_sale_evidence_mapping: EnterpriseSaleEvidenceMappingResult
    enterprise_sale_constraint_set: EnterpriseSaleConstraintSet
    enterprise_sale_evaluation: EnterpriseSaleEvaluation
    barter_evidence_mapping: BarterEvidenceMappingResult
    barter_constraint_set: BarterConstraintSet
    barter_evaluation: BarterEvaluation
    gift_evidence_mapping: GiftEvidenceMappingResult
    gift_constraint_set: GiftConstraintSet
    gift_evaluation: GiftEvaluation
    annuity_evidence_mapping: AnnuityEvidenceMappingResult
    annuity_constraint_set: AnnuityConstraintSet
    annuity_evaluation: AnnuityEvaluation
    lease_evidence_mapping: LeaseEvidenceMappingResult
    lease_constraint_set: LeaseConstraintSet
    lease_evaluation: LeaseEvaluation
    rental_evidence_mapping: RentalEvidenceMappingResult
    rental_constraint_set: RentalConstraintSet
    rental_evaluation: RentalEvaluation
    vehicle_lease_evidence_mapping: VehicleLeaseEvidenceMappingResult
    vehicle_lease_constraint_set: VehicleLeaseConstraintSet
    vehicle_lease_evaluation: VehicleLeaseEvaluation
    building_lease_evidence_mapping: BuildingLeaseEvidenceMappingResult
    building_lease_constraint_set: BuildingLeaseConstraintSet
    building_lease_evaluation: BuildingLeaseEvaluation
    enterprise_lease_evidence_mapping: EnterpriseLeaseEvidenceMappingResult
    enterprise_lease_constraint_set: EnterpriseLeaseConstraintSet
    enterprise_lease_evaluation: EnterpriseLeaseEvaluation
    leasing_evidence_mapping: LeasingEvidenceMappingResult
    leasing_constraint_set: LeasingConstraintSet
    leasing_evaluation: LeasingEvaluation
    residential_lease_evidence_mapping: ResidentialLeaseEvidenceMappingResult
    residential_lease_constraint_set: ResidentialLeaseConstraintSet
    residential_lease_evaluation: ResidentialLeaseEvaluation
    gratuitous_use_evidence_mapping: GratuitousUseEvidenceMappingResult
    gratuitous_use_constraint_set: GratuitousUseConstraintSet
    gratuitous_use_evaluation: GratuitousUseEvaluation
    work_contract_evidence_mapping: WorkContractEvidenceMappingResult
    work_contract_constraint_set: WorkContractConstraintSet
    work_contract_evaluation: WorkContractEvaluation
    consumer_work_evidence_mapping: ConsumerWorkEvidenceMappingResult
    consumer_work_constraint_set: ConsumerWorkConstraintSet
    consumer_work_evaluation: ConsumerWorkEvaluation
    construction_contract_evidence_mapping: ConstructionContractEvidenceMappingResult
    construction_contract_constraint_set: ConstructionContractConstraintSet
    construction_contract_evaluation: ConstructionContractEvaluation
    design_work_evidence_mapping: DesignWorkEvidenceMappingResult
    design_work_constraint_set: DesignWorkConstraintSet
    design_work_evaluation: DesignWorkEvaluation
    state_work_evidence_mapping: StateWorkEvidenceMappingResult
    state_work_constraint_set: StateWorkConstraintSet
    state_work_evaluation: StateWorkEvaluation
    research_work_evidence_mapping: ResearchWorkEvidenceMappingResult
    research_work_constraint_set: ResearchWorkConstraintSet
    research_work_evaluation: ResearchWorkEvaluation
    paid_services_evidence_mapping: PaidServicesEvidenceMappingResult
    paid_services_constraint_set: PaidServicesConstraintSet
    paid_services_evaluation: PaidServicesEvaluation
    carriage_evidence_mapping: CarriageEvidenceMappingResult
    carriage_constraint_set: CarriageConstraintSet
    carriage_evaluation: CarriageEvaluation
    forwarding_evidence_mapping: ForwardingEvidenceMappingResult
    forwarding_constraint_set: ForwardingConstraintSet
    forwarding_evaluation: ForwardingEvaluation
    invalidity_evidence_mapping: InvalidityEvidenceMappingResult
    invalidity_constraint_set: InvalidityConstraintSet
    invalidity_evaluation: InvalidityEvaluation
    security_evidence_mapping: SecurityEvidenceMappingResult
    security_constraint_set: SecurityConstraintSet
    security_evaluation: SecurityEvaluation
    obligation_dynamics_evidence_mapping: ObligationDynamicsEvidenceMappingResult
    obligation_dynamics_constraint_set: ObligationDynamicsConstraintSet
    obligation_dynamics_evaluation: ObligationDynamicsEvaluation
    performance_remedies_evidence_mapping: PerformanceRemediesEvidenceMappingResult
    performance_remedies_constraint_set: PerformanceRemediesConstraintSet
    performance_remedies_evaluation: PerformanceRemediesEvaluation
    sale_evidence_mapping: SaleEvidenceMappingResult
    sale_constraint_set: SaleConstraintSet
    sale_evaluation: SaleEvaluation
    supply_evidence_mapping: SupplyEvidenceMappingResult
    supply_constraint_set: SupplyConstraintSet
    supply_evaluation: SupplyEvaluation
    termination_evidence_mapping: TerminationEvidenceMappingResult
    termination_constraint_set: TerminationConstraintSet
    termination_evaluation: TerminationEvaluation
    liability_evidence_mapping: LiabilityEvidenceMappingResult
    liability_constraint_set: LiabilityConstraintSet
    liability_evaluation: LiabilityEvaluation
    counterfactual_sensitivity: ContractCounterfactualSensitivityReport
    authority_evaluation: AuthorityEvaluation
    requires_human_resolution: bool
    warnings: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_analysis_replay(self) -> "ReviewedContractAnalysisResult":
        expected_formation_set = build_formation_constraint_set(self.formation_evidence_mapping)
        if self.formation_constraint_set != expected_formation_set:
            raise ValueError("Formation constraint set does not replay from reviewed evidence.")
        expected_formation_evaluation = evaluate_formation_constraints(
            expected_formation_set,
            self.formation_evidence_mapping.facts,
        )
        if self.formation_evaluation != expected_formation_evaluation:
            raise ValueError("Formation evaluation does not replay from reviewed evidence.")
        expected_temporal_effect_set = build_temporal_effect_constraint_set(
            self.temporal_effect_evidence_mapping
        )
        if self.temporal_effect_constraint_set != expected_temporal_effect_set:
            raise ValueError(
                "Temporal-effect constraint set does not replay from reviewed evidence."
            )
        expected_temporal_effect_evaluation = evaluate_temporal_effect_constraints(
            expected_temporal_effect_set,
            self.temporal_effect_evidence_mapping.facts,
        )
        if self.temporal_effect_evaluation != expected_temporal_effect_evaluation:
            raise ValueError("Temporal-effect evaluation does not replay from reviewed evidence.")
        # Момент заключения (статья 433) не может быть установлен, если formation не
        # подтвердил формальные предпосылки заключения договора (статьи 432–443).
        if (
            self.temporal_effect_evaluation.conclusion_moment_established
            and not self.formation_evaluation.contract_concluded_prerequisites
        ):
            raise ValueError("Temporal-effect conclusion moment does not match formation result.")
        expected_limitation_set = build_limitation_constraint_set(self.limitation_evidence_mapping)
        if self.limitation_constraint_set != expected_limitation_set:
            raise ValueError("Limitation constraint set does not replay from reviewed evidence.")
        expected_limitation_evaluation = evaluate_limitation_constraints(
            expected_limitation_set,
            self.limitation_evidence_mapping.facts,
        )
        if self.limitation_evaluation != expected_limitation_evaluation:
            raise ValueError("Limitation evaluation does not replay from reviewed evidence.")
        expected_interpretation_set = build_interpretation_constraint_set(
            self.interpretation_evidence_mapping
        )
        if self.interpretation_constraint_set != expected_interpretation_set:
            raise ValueError(
                "Interpretation constraint set does not replay from reviewed evidence."
            )
        expected_interpretation_evaluation = evaluate_interpretation_constraints(
            expected_interpretation_set,
            self.interpretation_evidence_mapping.facts,
        )
        if self.interpretation_evaluation != expected_interpretation_evaluation:
            raise ValueError("Interpretation evaluation does not replay from reviewed evidence.")
        expected_form_set = build_form_constraint_set(self.form_evidence_mapping)
        if self.form_constraint_set != expected_form_set:
            raise ValueError("Form constraint set does not replay from reviewed evidence.")
        expected_form_evaluation = evaluate_form_constraints(
            expected_form_set,
            self.form_evidence_mapping.facts,
        )
        if self.form_evaluation != expected_form_evaluation:
            raise ValueError("Form evaluation does not replay from reviewed evidence.")
        expected_preliminary_set = build_preliminary_constraint_set(
            self.preliminary_evidence_mapping
        )
        if self.preliminary_constraint_set != expected_preliminary_set:
            raise ValueError("Preliminary constraint set does not replay from reviewed evidence.")
        expected_preliminary_evaluation = evaluate_preliminary_constraints(
            expected_preliminary_set,
            self.preliminary_evidence_mapping.facts,
        )
        if self.preliminary_evaluation != expected_preliminary_evaluation:
            raise ValueError("Preliminary evaluation does not replay from reviewed evidence.")
        expected_third_party_set = build_third_party_constraint_set(
            self.third_party_evidence_mapping
        )
        if self.third_party_constraint_set != expected_third_party_set:
            raise ValueError("Third-party constraint set does not replay from reviewed evidence.")
        expected_third_party_evaluation = evaluate_third_party_constraints(
            expected_third_party_set,
            self.third_party_evidence_mapping.facts,
        )
        if self.third_party_evaluation != expected_third_party_evaluation:
            raise ValueError("Third-party evaluation does not replay from reviewed evidence.")
        expected_public_contract_set = build_public_contract_constraint_set(
            self.public_contract_evidence_mapping
        )
        if self.public_contract_constraint_set != expected_public_contract_set:
            raise ValueError(
                "Public-contract constraint set does not replay from reviewed evidence."
            )
        expected_public_contract_evaluation = evaluate_public_contract_constraints(
            expected_public_contract_set,
            self.public_contract_evidence_mapping.facts,
        )
        if self.public_contract_evaluation != expected_public_contract_evaluation:
            raise ValueError("Public-contract evaluation does not replay from reviewed evidence.")
        expected_adhesion_set = build_adhesion_constraint_set(self.adhesion_evidence_mapping)
        if self.adhesion_constraint_set != expected_adhesion_set:
            raise ValueError("Adhesion constraint set does not replay from reviewed evidence.")
        expected_adhesion_evaluation = evaluate_adhesion_constraints(
            expected_adhesion_set,
            self.adhesion_evidence_mapping.facts,
        )
        if self.adhesion_evaluation != expected_adhesion_evaluation:
            raise ValueError("Adhesion evaluation does not replay from reviewed evidence.")
        expected_representations_set = build_representations_constraint_set(
            self.representations_evidence_mapping
        )
        if self.representations_constraint_set != expected_representations_set:
            raise ValueError(
                "Representations constraint set does not replay from reviewed evidence."
            )
        expected_representations_evaluation = evaluate_representations_constraints(
            expected_representations_set,
            self.representations_evidence_mapping.facts,
        )
        if self.representations_evaluation != expected_representations_evaluation:
            raise ValueError("Representations evaluation does not replay from reviewed evidence.")
        expected_precontractual_set = build_precontractual_constraint_set(
            self.precontractual_evidence_mapping
        )
        if self.precontractual_constraint_set != expected_precontractual_set:
            raise ValueError(
                "Precontractual constraint set does not replay from reviewed evidence."
            )
        expected_precontractual_evaluation = evaluate_precontractual_constraints(
            expected_precontractual_set,
            self.precontractual_evidence_mapping.facts,
        )
        if self.precontractual_evaluation != expected_precontractual_evaluation:
            raise ValueError("Precontractual evaluation does not replay from reviewed evidence.")
        expected_option_set = build_option_constraint_set(self.option_evidence_mapping)
        if self.option_constraint_set != expected_option_set:
            raise ValueError("Option constraint set does not replay from reviewed evidence.")
        expected_option_evaluation = evaluate_option_constraints(
            expected_option_set,
            self.option_evidence_mapping.facts,
        )
        if self.option_evaluation != expected_option_evaluation:
            raise ValueError("Option evaluation does not replay from reviewed evidence.")
        expected_framework_set = build_framework_constraint_set(self.framework_evidence_mapping)
        if self.framework_constraint_set != expected_framework_set:
            raise ValueError("Framework constraint set does not replay from reviewed evidence.")
        expected_framework_evaluation = evaluate_framework_constraints(
            expected_framework_set,
            self.framework_evidence_mapping.facts,
        )
        if self.framework_evaluation != expected_framework_evaluation:
            raise ValueError("Framework evaluation does not replay from reviewed evidence.")
        expected_freedom_set = build_freedom_constraint_set(self.freedom_evidence_mapping)
        if self.freedom_constraint_set != expected_freedom_set:
            raise ValueError("Freedom constraint set does not replay from reviewed evidence.")
        expected_freedom_evaluation = evaluate_freedom_constraints(
            expected_freedom_set,
            self.freedom_evidence_mapping.facts,
        )
        if self.freedom_evaluation != expected_freedom_evaluation:
            raise ValueError("Freedom evaluation does not replay from reviewed evidence.")
        expected_procedure_set = build_procedure_constraint_set(self.procedure_evidence_mapping)
        if self.procedure_constraint_set != expected_procedure_set:
            raise ValueError("Procedure constraint set does not replay from reviewed evidence.")
        expected_procedure_evaluation = evaluate_procedure_constraints(
            expected_procedure_set,
            self.procedure_evidence_mapping.facts,
        )
        if self.procedure_evaluation != expected_procedure_evaluation:
            raise ValueError("Procedure evaluation does not replay from reviewed evidence.")
        expected_general_obligations_set = build_general_obligations_constraint_set(
            self.general_obligations_evidence_mapping
        )
        if self.general_obligations_constraint_set != expected_general_obligations_set:
            raise ValueError(
                "General obligations constraint set does not replay from reviewed evidence."
            )
        expected_general_obligations_evaluation = evaluate_general_obligations_constraints(
            expected_general_obligations_set,
            self.general_obligations_evidence_mapping.facts,
        )
        if self.general_obligations_evaluation != expected_general_obligations_evaluation:
            raise ValueError(
                "General obligations evaluation does not replay from reviewed evidence."
            )
        expected_retail_sale_set = build_retail_sale_constraint_set(
            self.retail_sale_evidence_mapping
        )
        if self.retail_sale_constraint_set != expected_retail_sale_set:
            raise ValueError("Retail sale constraint set does not replay from reviewed evidence.")
        expected_retail_sale_evaluation = evaluate_retail_sale_constraints(
            expected_retail_sale_set,
            self.retail_sale_evidence_mapping.facts,
        )
        if self.retail_sale_evaluation != expected_retail_sale_evaluation:
            raise ValueError("Retail sale evaluation does not replay from reviewed evidence.")
        expected_state_supply_set = build_state_supply_constraint_set(
            self.state_supply_evidence_mapping
        )
        if self.state_supply_constraint_set != expected_state_supply_set:
            raise ValueError("State supply constraint set does not replay from reviewed evidence.")
        expected_state_supply_evaluation = evaluate_state_supply_constraints(
            expected_state_supply_set,
            self.state_supply_evidence_mapping.facts,
        )
        if self.state_supply_evaluation != expected_state_supply_evaluation:
            raise ValueError("State supply evaluation does not replay from reviewed evidence.")
        expected_contractation_set = build_contractation_constraint_set(
            self.contractation_evidence_mapping
        )
        if self.contractation_constraint_set != expected_contractation_set:
            raise ValueError("Contractation constraint set does not replay from reviewed evidence.")
        expected_contractation_evaluation = evaluate_contractation_constraints(
            expected_contractation_set,
            self.contractation_evidence_mapping.facts,
        )
        if self.contractation_evaluation != expected_contractation_evaluation:
            raise ValueError("Contractation evaluation does not replay from reviewed evidence.")
        expected_energy_supply_set = build_energy_supply_constraint_set(
            self.energy_supply_evidence_mapping
        )
        if self.energy_supply_constraint_set != expected_energy_supply_set:
            raise ValueError("Energy supply constraint set does not replay from reviewed evidence.")
        expected_energy_supply_evaluation = evaluate_energy_supply_constraints(
            expected_energy_supply_set,
            self.energy_supply_evidence_mapping.facts,
        )
        if self.energy_supply_evaluation != expected_energy_supply_evaluation:
            raise ValueError("Energy supply evaluation does not replay from reviewed evidence.")
        expected_real_estate_sale_set = build_real_estate_sale_constraint_set(
            self.real_estate_sale_evidence_mapping
        )
        if self.real_estate_sale_constraint_set != expected_real_estate_sale_set:
            raise ValueError(
                "Real estate sale constraint set does not replay from reviewed evidence."
            )
        expected_real_estate_sale_evaluation = evaluate_real_estate_sale_constraints(
            expected_real_estate_sale_set,
            self.real_estate_sale_evidence_mapping.facts,
        )
        if self.real_estate_sale_evaluation != expected_real_estate_sale_evaluation:
            raise ValueError("Real estate sale evaluation does not replay from reviewed evidence.")
        expected_enterprise_sale_set = build_enterprise_sale_constraint_set(
            self.enterprise_sale_evidence_mapping
        )
        if self.enterprise_sale_constraint_set != expected_enterprise_sale_set:
            raise ValueError(
                "Enterprise sale constraint set does not replay from reviewed evidence."
            )
        expected_enterprise_sale_evaluation = evaluate_enterprise_sale_constraints(
            expected_enterprise_sale_set,
            self.enterprise_sale_evidence_mapping.facts,
        )
        if self.enterprise_sale_evaluation != expected_enterprise_sale_evaluation:
            raise ValueError("Enterprise sale evaluation does not replay from reviewed evidence.")
        expected_barter_set = build_barter_constraint_set(self.barter_evidence_mapping)
        if self.barter_constraint_set != expected_barter_set:
            raise ValueError("Barter constraint set does not replay from reviewed evidence.")
        expected_barter_evaluation = evaluate_barter_constraints(
            expected_barter_set,
            self.barter_evidence_mapping.facts,
        )
        if self.barter_evaluation != expected_barter_evaluation:
            raise ValueError("Barter evaluation does not replay from reviewed evidence.")
        expected_gift_set = build_gift_constraint_set(self.gift_evidence_mapping)
        if self.gift_constraint_set != expected_gift_set:
            raise ValueError("Gift constraint set does not replay from reviewed evidence.")
        expected_gift_evaluation = evaluate_gift_constraints(
            expected_gift_set,
            self.gift_evidence_mapping.facts,
        )
        if self.gift_evaluation != expected_gift_evaluation:
            raise ValueError("Gift evaluation does not replay from reviewed evidence.")
        expected_annuity_set = build_annuity_constraint_set(self.annuity_evidence_mapping)
        if self.annuity_constraint_set != expected_annuity_set:
            raise ValueError("Annuity constraint set does not replay from reviewed evidence.")
        expected_annuity_evaluation = evaluate_annuity_constraints(
            expected_annuity_set,
            self.annuity_evidence_mapping.facts,
        )
        if self.annuity_evaluation != expected_annuity_evaluation:
            raise ValueError("Annuity evaluation does not replay from reviewed evidence.")
        expected_lease_set = build_lease_constraint_set(self.lease_evidence_mapping)
        if self.lease_constraint_set != expected_lease_set:
            raise ValueError("Lease constraint set does not replay from reviewed evidence.")
        expected_lease_evaluation = evaluate_lease_constraints(
            expected_lease_set,
            self.lease_evidence_mapping.facts,
        )
        if self.lease_evaluation != expected_lease_evaluation:
            raise ValueError("Lease evaluation does not replay from reviewed evidence.")
        expected_rental_set = build_rental_constraint_set(self.rental_evidence_mapping)
        if self.rental_constraint_set != expected_rental_set:
            raise ValueError("Rental constraint set does not replay from reviewed evidence.")
        expected_rental_evaluation = evaluate_rental_constraints(
            expected_rental_set,
            self.rental_evidence_mapping.facts,
        )
        if self.rental_evaluation != expected_rental_evaluation:
            raise ValueError("Rental evaluation does not replay from reviewed evidence.")
        expected_vehicle_lease_set = build_vehicle_lease_constraint_set(
            self.vehicle_lease_evidence_mapping
        )
        if self.vehicle_lease_constraint_set != expected_vehicle_lease_set:
            raise ValueError("Vehicle-lease constraint set does not replay from reviewed evidence.")
        expected_vehicle_lease_evaluation = evaluate_vehicle_lease_constraints(
            expected_vehicle_lease_set,
            self.vehicle_lease_evidence_mapping.facts,
        )
        if self.vehicle_lease_evaluation != expected_vehicle_lease_evaluation:
            raise ValueError("Vehicle-lease evaluation does not replay from reviewed evidence.")
        expected_building_lease_set = build_building_lease_constraint_set(
            self.building_lease_evidence_mapping
        )
        if self.building_lease_constraint_set != expected_building_lease_set:
            raise ValueError(
                "Building-lease constraint set does not replay from reviewed evidence."
            )
        expected_building_lease_evaluation = evaluate_building_lease_constraints(
            expected_building_lease_set,
            self.building_lease_evidence_mapping.facts,
        )
        if self.building_lease_evaluation != expected_building_lease_evaluation:
            raise ValueError("Building-lease evaluation does not replay from reviewed evidence.")
        expected_enterprise_lease_set = build_enterprise_lease_constraint_set(
            self.enterprise_lease_evidence_mapping
        )
        if self.enterprise_lease_constraint_set != expected_enterprise_lease_set:
            raise ValueError(
                "Enterprise-lease constraint set does not replay from reviewed evidence."
            )
        expected_enterprise_lease_evaluation = evaluate_enterprise_lease_constraints(
            expected_enterprise_lease_set,
            self.enterprise_lease_evidence_mapping.facts,
        )
        if self.enterprise_lease_evaluation != expected_enterprise_lease_evaluation:
            raise ValueError("Enterprise-lease evaluation does not replay from reviewed evidence.")
        expected_leasing_set = build_leasing_constraint_set(self.leasing_evidence_mapping)
        if self.leasing_constraint_set != expected_leasing_set:
            raise ValueError("Leasing constraint set does not replay from reviewed evidence.")
        expected_leasing_evaluation = evaluate_leasing_constraints(
            expected_leasing_set,
            self.leasing_evidence_mapping.facts,
        )
        if self.leasing_evaluation != expected_leasing_evaluation:
            raise ValueError("Leasing evaluation does not replay from reviewed evidence.")
        expected_residential_lease_set = build_residential_lease_constraint_set(
            self.residential_lease_evidence_mapping
        )
        if self.residential_lease_constraint_set != expected_residential_lease_set:
            raise ValueError(
                "Residential-lease constraint set does not replay from reviewed evidence."
            )
        expected_residential_lease_evaluation = evaluate_residential_lease_constraints(
            expected_residential_lease_set,
            self.residential_lease_evidence_mapping.facts,
        )
        if self.residential_lease_evaluation != expected_residential_lease_evaluation:
            raise ValueError("Residential-lease evaluation does not replay from reviewed evidence.")
        expected_gratuitous_use_set = build_gratuitous_use_constraint_set(
            self.gratuitous_use_evidence_mapping
        )
        if self.gratuitous_use_constraint_set != expected_gratuitous_use_set:
            raise ValueError(
                "Gratuitous-use constraint set does not replay from reviewed evidence."
            )
        expected_gratuitous_use_evaluation = evaluate_gratuitous_use_constraints(
            expected_gratuitous_use_set,
            self.gratuitous_use_evidence_mapping.facts,
        )
        if self.gratuitous_use_evaluation != expected_gratuitous_use_evaluation:
            raise ValueError("Gratuitous-use evaluation does not replay from reviewed evidence.")
        expected_work_contract_set = build_work_contract_constraint_set(
            self.work_contract_evidence_mapping
        )
        if self.work_contract_constraint_set != expected_work_contract_set:
            raise ValueError("Work-contract constraint set does not replay from reviewed evidence.")
        expected_work_contract_evaluation = evaluate_work_contract_constraints(
            expected_work_contract_set,
            self.work_contract_evidence_mapping.facts,
        )
        if self.work_contract_evaluation != expected_work_contract_evaluation:
            raise ValueError("Work-contract evaluation does not replay from reviewed evidence.")
        expected_consumer_work_set = build_consumer_work_constraint_set(
            self.consumer_work_evidence_mapping
        )
        if self.consumer_work_constraint_set != expected_consumer_work_set:
            raise ValueError("Consumer-work constraint set does not replay from reviewed evidence.")
        expected_consumer_work_evaluation = evaluate_consumer_work_constraints(
            expected_consumer_work_set,
            self.consumer_work_evidence_mapping.facts,
        )
        if self.consumer_work_evaluation != expected_consumer_work_evaluation:
            raise ValueError("Consumer-work evaluation does not replay from reviewed evidence.")
        expected_construction_contract_set = build_construction_contract_constraint_set(
            self.construction_contract_evidence_mapping
        )
        if self.construction_contract_constraint_set != expected_construction_contract_set:
            raise ValueError(
                "Construction-contract constraint set does not replay from reviewed evidence."
            )
        expected_construction_contract_evaluation = evaluate_construction_contract_constraints(
            expected_construction_contract_set,
            self.construction_contract_evidence_mapping.facts,
        )
        if self.construction_contract_evaluation != expected_construction_contract_evaluation:
            raise ValueError(
                "Construction-contract evaluation does not replay from reviewed evidence."
            )
        expected_design_work_set = build_design_work_constraint_set(
            self.design_work_evidence_mapping
        )
        if self.design_work_constraint_set != expected_design_work_set:
            raise ValueError("Design-work constraint set does not replay from reviewed evidence.")
        expected_design_work_evaluation = evaluate_design_work_constraints(
            expected_design_work_set,
            self.design_work_evidence_mapping.facts,
        )
        if self.design_work_evaluation != expected_design_work_evaluation:
            raise ValueError("Design-work evaluation does not replay from reviewed evidence.")
        expected_state_work_set = build_state_work_constraint_set(self.state_work_evidence_mapping)
        if self.state_work_constraint_set != expected_state_work_set:
            raise ValueError("State-work constraint set does not replay from reviewed evidence.")
        expected_state_work_evaluation = evaluate_state_work_constraints(
            expected_state_work_set,
            self.state_work_evidence_mapping.facts,
        )
        if self.state_work_evaluation != expected_state_work_evaluation:
            raise ValueError("State-work evaluation does not replay from reviewed evidence.")
        expected_research_work_set = build_research_work_constraint_set(
            self.research_work_evidence_mapping
        )
        if self.research_work_constraint_set != expected_research_work_set:
            raise ValueError("Research-work constraint set does not replay from reviewed evidence.")
        expected_research_work_evaluation = evaluate_research_work_constraints(
            expected_research_work_set,
            self.research_work_evidence_mapping.facts,
        )
        if self.research_work_evaluation != expected_research_work_evaluation:
            raise ValueError("Research-work evaluation does not replay from reviewed evidence.")
        expected_paid_services_set = build_paid_services_constraint_set(
            self.paid_services_evidence_mapping
        )
        if self.paid_services_constraint_set != expected_paid_services_set:
            raise ValueError("Paid-services constraint set does not replay from reviewed evidence.")
        expected_paid_services_evaluation = evaluate_paid_services_constraints(
            expected_paid_services_set,
            self.paid_services_evidence_mapping.facts,
        )
        if self.paid_services_evaluation != expected_paid_services_evaluation:
            raise ValueError("Paid-services evaluation does not replay from reviewed evidence.")
        expected_carriage_set = build_carriage_constraint_set(self.carriage_evidence_mapping)
        if self.carriage_constraint_set != expected_carriage_set:
            raise ValueError("Carriage constraint set does not replay from reviewed evidence.")
        expected_carriage_evaluation = evaluate_carriage_constraints(
            expected_carriage_set,
            self.carriage_evidence_mapping.facts,
        )
        if self.carriage_evaluation != expected_carriage_evaluation:
            raise ValueError("Carriage evaluation does not replay from reviewed evidence.")
        expected_forwarding_set = build_forwarding_constraint_set(self.forwarding_evidence_mapping)
        if self.forwarding_constraint_set != expected_forwarding_set:
            raise ValueError("Forwarding constraint set does not replay from reviewed evidence.")
        expected_forwarding_evaluation = evaluate_forwarding_constraints(
            expected_forwarding_set,
            self.forwarding_evidence_mapping.facts,
        )
        if self.forwarding_evaluation != expected_forwarding_evaluation:
            raise ValueError("Forwarding evaluation does not replay from reviewed evidence.")
        expected_invalidity_set = build_invalidity_constraint_set(self.invalidity_evidence_mapping)
        if self.invalidity_constraint_set != expected_invalidity_set:
            raise ValueError("Invalidity constraint set does not replay from reviewed evidence.")
        expected_invalidity_evaluation = evaluate_invalidity_constraints(
            expected_invalidity_set,
            self.invalidity_evidence_mapping.facts,
        )
        if self.invalidity_evaluation != expected_invalidity_evaluation:
            raise ValueError("Invalidity evaluation does not replay from reviewed evidence.")
        if (
            self.invalidity_evidence_mapping.facts.transaction_concluded
            != self.formation_evaluation.contract_concluded_prerequisites
        ):
            raise ValueError("Invalidity transaction status does not match formation result.")
        expected_contractual_duty = (
            self.formation_evaluation.contract_concluded_prerequisites
            and not self.invalidity_evaluation.contractual_effect_displaced
        )
        if expected_contractual_duty != self.evidence_mapping.facts.duty_exists:
            raise ValueError(
                "Formation and invalidity results do not match contractual duty evidence."
            )
        expected_security_set = build_security_constraint_set(self.security_evidence_mapping)
        if self.security_constraint_set != expected_security_set:
            raise ValueError("Security constraint set does not replay from reviewed evidence.")
        expected_security_evaluation = evaluate_security_constraints(
            expected_security_set,
            self.security_evidence_mapping.facts,
        )
        if self.security_evaluation != expected_security_evaluation:
            raise ValueError("Security evaluation does not replay from reviewed evidence.")
        if (
            self.security_evidence_mapping.facts.main_obligation_exists
            != self.formation_evaluation.contract_concluded_prerequisites
        ):
            raise ValueError("Security main obligation status does not match formation result.")
        if (
            self.security_evidence_mapping.facts.main_obligation_invalid
            != self.invalidity_evaluation.contractual_effect_displaced
        ):
            raise ValueError("Security invalidity status does not match invalidity result.")
        if (
            self.security_evidence_mapping.facts.main_obligation_breached
            != self.constraint_evaluation.breach_issue
        ):
            raise ValueError("Security breach status does not match obligation evaluation.")
        expected_dynamics_set = build_obligation_dynamics_constraint_set(
            self.obligation_dynamics_evidence_mapping
        )
        if self.obligation_dynamics_constraint_set != expected_dynamics_set:
            raise ValueError(
                "Obligation-dynamics constraint set does not replay from reviewed evidence."
            )
        expected_dynamics_evaluation = evaluate_obligation_dynamics_constraints(
            expected_dynamics_set,
            self.obligation_dynamics_evidence_mapping.facts,
        )
        if self.obligation_dynamics_evaluation != expected_dynamics_evaluation:
            raise ValueError(
                "Obligation-dynamics evaluation does not replay from reviewed evidence."
            )
        if (
            self.obligation_dynamics_evidence_mapping.facts.obligation_exists
            != self.evidence_mapping.facts.duty_exists
        ):
            raise ValueError("Obligation-dynamics obligation status does not match duty evidence.")
        if (
            self.obligation_dynamics_evidence_mapping.facts.obligation_breached
            != self.constraint_evaluation.breach_issue
        ):
            raise ValueError(
                "Obligation-dynamics breach status does not match obligation evaluation."
            )
        if (
            self.obligation_dynamics_evidence_mapping.facts.performance_rendered
            != self.evidence_mapping.facts.performance_completed
        ):
            raise ValueError(
                "Obligation-dynamics performance status does not match performance evidence."
            )
        expected_proper_performance = (
            self.evidence_mapping.facts.performance_completed
            and not self.evidence_mapping.facts.performance_nonconforming
        )
        if (
            self.obligation_dynamics_evidence_mapping.facts.performance_accepted_as_proper
            != expected_proper_performance
        ):
            raise ValueError(
                "Obligation-dynamics proper-performance status does not match case evidence."
            )
        expected_performance_remedies_set = build_performance_remedies_constraint_set(
            self.performance_remedies_evidence_mapping
        )
        if self.performance_remedies_constraint_set != expected_performance_remedies_set:
            raise ValueError(
                "Performance-remedies constraint set does not replay from reviewed evidence."
            )
        expected_performance_remedies_evaluation = evaluate_performance_remedies_constraints(
            expected_performance_remedies_set,
            self.performance_remedies_evidence_mapping.facts,
        )
        if self.performance_remedies_evaluation != expected_performance_remedies_evaluation:
            raise ValueError(
                "Performance-remedies evaluation does not replay from reviewed evidence."
            )
        performance_facts = self.performance_remedies_evidence_mapping.facts
        if performance_facts.obligation_exists != self.evidence_mapping.facts.duty_exists:
            raise ValueError("Performance-remedies obligation status does not match duty evidence.")
        if performance_facts.breach_established != self.constraint_evaluation.breach_issue:
            raise ValueError(
                "Performance-remedies breach status does not match obligation evaluation."
            )
        if (
            performance_facts.performance_tendered
            != self.obligation_dynamics_evidence_mapping.facts.performance_rendered
        ):
            raise ValueError(
                "Performance-remedies tender status does not match obligation-dynamics evidence."
            )
        if performance_facts.loss_claimed != self.evidence_mapping.facts.loss_claimed:
            raise ValueError("Performance-remedies loss claim does not match case evidence.")
        if performance_facts.causation_proven != self.evidence_mapping.facts.causation_established:
            raise ValueError("Performance-remedies causation does not match case evidence.")
        expected_monetary_delay = (
            self.evidence_mapping.facts.payment_duty_exists
            and self.evidence_mapping.facts.payment_due
            and self.evidence_mapping.facts.payment_missed
            and not self.evidence_mapping.facts.payment_defense_applies
        )
        if performance_facts.monetary_delay != expected_monetary_delay:
            raise ValueError(
                "Performance-remedies monetary-delay status does not match payment evidence."
            )
        expected_sale_set = build_sale_constraint_set(self.sale_evidence_mapping)
        if self.sale_constraint_set != expected_sale_set:
            raise ValueError("Sale constraint set does not replay from reviewed evidence.")
        expected_sale_evaluation = evaluate_sale_constraints(
            expected_sale_set,
            self.sale_evidence_mapping.facts,
        )
        if self.sale_evaluation != expected_sale_evaluation:
            raise ValueError("Sale evaluation does not replay from reviewed evidence.")
        sale_facts = self.sale_evidence_mapping.facts
        if (
            sale_facts.contract_concluded
            != self.formation_evaluation.contract_concluded_prerequisites
        ):
            raise ValueError("Sale contract status does not match formation result.")
        if sale_facts.goods_transfer_completed != self.evidence_mapping.facts.performance_completed:
            raise ValueError("Sale transfer status does not match performance evidence.")
        if sale_facts.delivery_late != self.temporal_evaluation.due_date_missed:
            raise ValueError("Sale delay status does not match temporal evaluation.")
        sale_basic_nonconforming = (
            sale_facts.quantity_shortfall
            or sale_facts.quality_defect
            or sale_facts.incomplete_goods
        )
        if sale_basic_nonconforming != self.evidence_mapping.facts.performance_nonconforming:
            raise ValueError("Sale nonconformity does not match performance evidence.")
        if sale_facts.loss_claimed != self.evidence_mapping.facts.loss_claimed:
            raise ValueError("Sale loss claim does not match case evidence.")
        if sale_facts.causation_proven != self.evidence_mapping.facts.causation_established:
            raise ValueError("Sale causation does not match case evidence.")
        if sale_facts.payment_due != self.evidence_mapping.facts.payment_due:
            raise ValueError("Sale payment due status does not match case evidence.")
        if self.sale_evaluation.sale_breach_established != self.constraint_evaluation.breach_issue:
            raise ValueError("Sale breach status does not match obligation evaluation.")
        expected_supply_set = build_supply_constraint_set(self.supply_evidence_mapping)
        if self.supply_constraint_set != expected_supply_set:
            raise ValueError("Supply constraint set does not replay from reviewed evidence.")
        expected_supply_evaluation = evaluate_supply_constraints(
            expected_supply_set,
            self.supply_evidence_mapping.facts,
        )
        if self.supply_evaluation != expected_supply_evaluation:
            raise ValueError("Supply evaluation does not replay from reviewed evidence.")
        supply_facts = self.supply_evidence_mapping.facts
        if (
            supply_facts.contract_concluded
            != self.formation_evaluation.contract_concluded_prerequisites
        ):
            raise ValueError("Supply contract status does not match formation result.")
        if supply_facts.delivery_completed != self.evidence_mapping.facts.performance_completed:
            raise ValueError("Supply delivery status does not match performance evidence.")
        if supply_facts.delivery_late != self.temporal_evaluation.due_date_missed:
            raise ValueError("Supply delay status does not match temporal evaluation.")
        supply_nonconforming = (
            supply_facts.quantity_shortfall
            or supply_facts.quality_defect
            or supply_facts.incomplete_goods
        )
        if supply_nonconforming != self.evidence_mapping.facts.performance_nonconforming:
            raise ValueError("Supply nonconformity does not match performance evidence.")
        if supply_facts.loss_claimed != self.evidence_mapping.facts.loss_claimed:
            raise ValueError("Supply loss claim does not match case evidence.")
        if supply_facts.causation_proven != self.evidence_mapping.facts.causation_established:
            raise ValueError("Supply causation does not match case evidence.")
        if supply_facts.payment_due != self.evidence_mapping.facts.payment_due:
            raise ValueError("Supply payment due status does not match case evidence.")
        sale_supply_pairs = (
            (sale_facts.contract_concluded, supply_facts.contract_concluded, "contract"),
            (sale_facts.goods_transfer_completed, supply_facts.delivery_completed, "delivery"),
            (sale_facts.delivery_late, supply_facts.delivery_late, "delay"),
            (sale_facts.quantity_shortfall, supply_facts.quantity_shortfall, "quantity"),
            (sale_facts.quality_defect, supply_facts.quality_defect, "quality"),
            (sale_facts.incomplete_goods, supply_facts.incomplete_goods, "completeness"),
            (sale_facts.buyer_received_goods, supply_facts.buyer_received_goods, "receipt"),
            (sale_facts.inspection_timely, supply_facts.inspection_timely, "inspection"),
            (sale_facts.discrepancy_found, supply_facts.discrepancy_found, "discrepancy"),
            (sale_facts.prompt_notice_given, supply_facts.prompt_written_notice, "notice"),
            (sale_facts.payment_due, supply_facts.payment_due, "payment due"),
            (sale_facts.buyer_paid, supply_facts.buyer_paid, "payment"),
            (sale_facts.contract_terminated, supply_facts.contract_terminated, "termination"),
        )
        for sale_value, supply_value, label in sale_supply_pairs:
            if sale_value != supply_value:
                raise ValueError(f"Sale and supply {label} facts do not match.")
        if (
            self.sale_evaluation.sale_contract_qualified
            != self.supply_evaluation.supply_contract_qualified
        ):
            raise ValueError("Sale and supply qualification results do not match.")
        if (
            self.supply_evaluation.supply_breach_established
            != self.constraint_evaluation.breach_issue
        ):
            raise ValueError("Supply breach status does not match obligation evaluation.")
        expected_termination_set = build_termination_constraint_set(
            self.termination_evidence_mapping
        )
        if self.termination_constraint_set != expected_termination_set:
            raise ValueError("Termination constraint set does not replay from reviewed evidence.")
        expected_termination_evaluation = evaluate_termination_constraints(
            expected_termination_set,
            self.termination_evidence_mapping.facts,
        )
        if self.termination_evaluation != expected_termination_evaluation:
            raise ValueError("Termination evaluation does not replay from reviewed evidence.")
        if (
            self.termination_evidence_mapping.facts.contract_formed
            != self.formation_evaluation.contract_concluded_prerequisites
        ):
            raise ValueError("Termination contract status does not match formation result.")
        if (
            self.termination_evidence_mapping.facts.substantial_breach_proven
            and not self.constraint_evaluation.breach_issue
        ):
            raise ValueError("Substantial breach evidence requires an obligation breach.")
        if supply_facts.contract_terminated != self.termination_evaluation.effective_termination:
            raise ValueError("Supply termination status does not match termination evaluation.")
        if sale_facts.contract_terminated != self.termination_evaluation.effective_termination:
            raise ValueError("Sale termination status does not match termination evaluation.")
        if (
            self.sale_evaluation.sale_contract_refusal_effective
            and not self.termination_evaluation.effective_termination
        ):
            raise ValueError("Effective sale refusal must be reflected in termination evidence.")
        if (
            self.supply_evaluation.supply_unilateral_refusal_effective
            and not self.termination_evaluation.effective_termination
        ):
            raise ValueError("Effective supply refusal must be reflected in termination evidence.")
        expected_constraint_set = build_liability_constraint_set(self.liability_evidence_mapping)
        if self.liability_constraint_set != expected_constraint_set:
            raise ValueError("Liability constraint set does not replay from reviewed evidence.")
        if (
            self.liability_evidence_mapping.facts.breach_established
            != self.constraint_evaluation.breach_issue
        ):
            raise ValueError("Liability breach fact does not match obligation evaluation.")
        expected_evaluation = evaluate_liability_constraints(
            expected_constraint_set,
            self.liability_evidence_mapping.facts,
        )
        if self.liability_evaluation != expected_evaluation:
            raise ValueError("Liability evaluation does not replay from reviewed evidence.")
        return self


class ReviewedContractAnalysisArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer: str
    sources: list[LegalSource] = Field(default_factory=list)
    request: ReviewedContractAnalysisRequest
    result: ReviewedContractAnalysisResult


def _require_reviewed(
    *,
    artifact_name: str,
    review_status: BootstrapReviewStatus,
    reviewer_id: str | None,
) -> str:
    if review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError(f"{artifact_name} must be reviewed before analysis.")
    if not reviewer_id:
        raise ValueError(f"{artifact_name} requires a reviewer_id before analysis.")
    return reviewer_id


def _build_source_registry(sources: list[LegalSource]) -> dict[str, LegalSource]:
    source_ids = [source.id for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Source registry contains duplicate source ids.")
    return {source.id: source for source in sources}


def _validate_request_integrity(
    request: ReviewedContractAnalysisRequest,
    source_registry: dict[str, LegalSource],
) -> list[str]:
    if request.case_evidence.case_id != request.case_id:
        raise ValueError("Case evidence case_id does not match the analysis request.")
    if request.temporal_evidence.case_id != request.case_id:
        raise ValueError("Temporal evidence case_id does not match the analysis request.")
    if request.formation_evidence.case_id != request.case_id:
        raise ValueError("Formation evidence case_id does not match the analysis request.")
    if request.temporal_effect_evidence.case_id != request.case_id:
        raise ValueError("Temporal-effect evidence case_id does not match the analysis request.")
    if request.limitation_evidence.case_id != request.case_id:
        raise ValueError("Limitation evidence case_id does not match the analysis request.")
    if request.interpretation_evidence.case_id != request.case_id:
        raise ValueError("Interpretation evidence case_id does not match the analysis request.")
    if request.form_evidence.case_id != request.case_id:
        raise ValueError("Form evidence case_id does not match the analysis request.")
    if request.preliminary_evidence.case_id != request.case_id:
        raise ValueError("Preliminary evidence case_id does not match the analysis request.")
    if request.third_party_evidence.case_id != request.case_id:
        raise ValueError("Third-party evidence case_id does not match the analysis request.")
    if request.public_contract_evidence.case_id != request.case_id:
        raise ValueError("Public-contract evidence case_id does not match the analysis request.")
    if request.adhesion_evidence.case_id != request.case_id:
        raise ValueError("Adhesion evidence case_id does not match the analysis request.")
    if request.representations_evidence.case_id != request.case_id:
        raise ValueError("Representations evidence case_id does not match the analysis request.")
    if request.precontractual_evidence.case_id != request.case_id:
        raise ValueError("Precontractual evidence case_id does not match the analysis request.")
    if request.option_evidence.case_id != request.case_id:
        raise ValueError("Option evidence case_id does not match the analysis request.")
    if request.framework_evidence.case_id != request.case_id:
        raise ValueError("Framework evidence case_id does not match the analysis request.")
    if request.freedom_evidence.case_id != request.case_id:
        raise ValueError("Freedom evidence case_id does not match the analysis request.")
    if request.procedure_evidence.case_id != request.case_id:
        raise ValueError("Procedure evidence case_id does not match the analysis request.")
    if request.general_obligations_evidence.case_id != request.case_id:
        raise ValueError(
            "General obligations evidence case_id does not match the analysis request."
        )
    if request.retail_sale_evidence.case_id != request.case_id:
        raise ValueError("Retail sale evidence case_id does not match the analysis request.")
    if request.state_supply_evidence.case_id != request.case_id:
        raise ValueError("State supply evidence case_id does not match the analysis request.")
    if request.contractation_evidence.case_id != request.case_id:
        raise ValueError("Contractation evidence case_id does not match the analysis request.")
    if request.energy_supply_evidence.case_id != request.case_id:
        raise ValueError("Energy supply evidence case_id does not match the analysis request.")
    if request.real_estate_sale_evidence.case_id != request.case_id:
        raise ValueError("Real estate sale evidence case_id does not match the analysis request.")
    if request.enterprise_sale_evidence.case_id != request.case_id:
        raise ValueError("Enterprise sale evidence case_id does not match the analysis request.")
    if request.barter_evidence.case_id != request.case_id:
        raise ValueError("Barter evidence case_id does not match the analysis request.")
    if request.gift_evidence.case_id != request.case_id:
        raise ValueError("Gift evidence case_id does not match the analysis request.")
    if request.annuity_evidence.case_id != request.case_id:
        raise ValueError("Annuity evidence case_id does not match the analysis request.")
    if request.lease_evidence.case_id != request.case_id:
        raise ValueError("Lease evidence case_id does not match the analysis request.")
    if request.rental_evidence.case_id != request.case_id:
        raise ValueError("Rental evidence case_id does not match the analysis request.")
    if request.vehicle_lease_evidence.case_id != request.case_id:
        raise ValueError("Vehicle-lease evidence case_id does not match the analysis request.")
    if request.building_lease_evidence.case_id != request.case_id:
        raise ValueError("Building-lease evidence case_id does not match the analysis request.")
    if request.enterprise_lease_evidence.case_id != request.case_id:
        raise ValueError("Enterprise-lease evidence case_id does not match the analysis request.")
    if request.leasing_evidence.case_id != request.case_id:
        raise ValueError("Leasing evidence case_id does not match the analysis request.")
    if request.residential_lease_evidence.case_id != request.case_id:
        raise ValueError("Residential-lease evidence case_id does not match the analysis request.")
    if request.gratuitous_use_evidence.case_id != request.case_id:
        raise ValueError("Gratuitous-use evidence case_id does not match the analysis request.")
    if request.work_contract_evidence.case_id != request.case_id:
        raise ValueError("Work-contract evidence case_id does not match the analysis request.")
    if request.consumer_work_evidence.case_id != request.case_id:
        raise ValueError("Consumer-work evidence case_id does not match the analysis request.")
    if request.construction_contract_evidence.case_id != request.case_id:
        raise ValueError(
            "Construction-contract evidence case_id does not match the analysis request."
        )
    if request.design_work_evidence.case_id != request.case_id:
        raise ValueError("Design-work evidence case_id does not match the analysis request.")
    if request.state_work_evidence.case_id != request.case_id:
        raise ValueError("State-work evidence case_id does not match the analysis request.")
    if request.research_work_evidence.case_id != request.case_id:
        raise ValueError("Research-work evidence case_id does not match the analysis request.")
    if request.paid_services_evidence.case_id != request.case_id:
        raise ValueError("Paid-services evidence case_id does not match the analysis request.")
    if request.carriage_evidence.case_id != request.case_id:
        raise ValueError("Carriage evidence case_id does not match the analysis request.")
    if request.forwarding_evidence.case_id != request.case_id:
        raise ValueError("Forwarding evidence case_id does not match the analysis request.")
    if request.invalidity_evidence.case_id != request.case_id:
        raise ValueError("Invalidity evidence case_id does not match the analysis request.")
    if request.security_evidence.case_id != request.case_id:
        raise ValueError("Security evidence case_id does not match the analysis request.")
    if request.obligation_dynamics_evidence.case_id != request.case_id:
        raise ValueError(
            "Obligation-dynamics evidence case_id does not match the analysis request."
        )
    if request.performance_remedies_evidence.case_id != request.case_id:
        raise ValueError(
            "Performance-remedies evidence case_id does not match the analysis request."
        )
    if request.sale_evidence.case_id != request.case_id:
        raise ValueError("Sale evidence case_id does not match the analysis request.")
    if request.supply_evidence.case_id != request.case_id:
        raise ValueError("Supply evidence case_id does not match the analysis request.")
    if request.termination_evidence.case_id != request.case_id:
        raise ValueError("Termination evidence case_id does not match the analysis request.")
    if request.liability_evidence.case_id != request.case_id:
        raise ValueError("Liability evidence case_id does not match the analysis request.")
    if request.authority_input.evaluation_date != request.temporal_evidence.evaluation_date:
        raise ValueError("Authority and temporal evidence evaluation dates must match.")
    if request.reviewed_norm.schema_version != DEFAULT_BOOTSTRAP_SCHEMA_VERSION:
        raise ValueError("Reviewed norm uses an unsupported bootstrap schema version.")
    if request.case_evidence.schema_version != CASE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Case evidence uses an unsupported schema version.")
    if request.formation_evidence.schema_version != FORMATION_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Formation evidence uses an unsupported schema version.")
    if request.invalidity_evidence.schema_version != INVALIDITY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Invalidity evidence uses an unsupported schema version.")
    if request.security_evidence.schema_version != SECURITY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Security evidence uses an unsupported schema version.")
    if (
        request.obligation_dynamics_evidence.schema_version
        != OBLIGATION_DYNAMICS_EVIDENCE_SCHEMA_VERSION
    ):
        raise ValueError("Obligation-dynamics evidence uses an unsupported schema version.")
    if (
        request.performance_remedies_evidence.schema_version
        != PERFORMANCE_REMEDIES_EVIDENCE_SCHEMA_VERSION
    ):
        raise ValueError("Performance-remedies evidence uses an unsupported schema version.")
    if request.sale_evidence.schema_version != SALE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Sale evidence uses an unsupported schema version.")
    if request.supply_evidence.schema_version != SUPPLY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Supply evidence uses an unsupported schema version.")
    if request.termination_evidence.schema_version != TERMINATION_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Termination evidence uses an unsupported schema version.")
    if request.liability_evidence.schema_version != LIABILITY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Liability evidence uses an unsupported schema version.")
    if request.temporal_effect_evidence.schema_version != TEMPORAL_EFFECT_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Temporal-effect evidence uses an unsupported schema version.")
    if request.limitation_evidence.schema_version != LIMITATION_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Limitation evidence uses an unsupported schema version.")
    if request.interpretation_evidence.schema_version != INTERPRETATION_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Interpretation evidence uses an unsupported schema version.")
    if request.form_evidence.schema_version != FORM_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Form evidence uses an unsupported schema version.")
    if request.preliminary_evidence.schema_version != PRELIMINARY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Preliminary evidence uses an unsupported schema version.")
    if request.third_party_evidence.schema_version != THIRD_PARTY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Third-party evidence uses an unsupported schema version.")
    if request.public_contract_evidence.schema_version != PUBLIC_CONTRACT_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Public-contract evidence uses an unsupported schema version.")
    if request.adhesion_evidence.schema_version != ADHESION_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Adhesion evidence uses an unsupported schema version.")
    if request.representations_evidence.schema_version != REPRESENTATIONS_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Representations evidence uses an unsupported schema version.")
    if request.precontractual_evidence.schema_version != PRECONTRACTUAL_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Precontractual evidence uses an unsupported schema version.")
    if request.option_evidence.schema_version != OPTION_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Option evidence uses an unsupported schema version.")
    if request.framework_evidence.schema_version != FRAMEWORK_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Framework evidence uses an unsupported schema version.")
    if request.freedom_evidence.schema_version != FREEDOM_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Freedom evidence uses an unsupported schema version.")
    if request.procedure_evidence.schema_version != PROCEDURE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Procedure evidence uses an unsupported schema version.")
    if (
        request.general_obligations_evidence.schema_version
        != GENERAL_OBLIGATIONS_EVIDENCE_SCHEMA_VERSION
    ):
        raise ValueError("General obligations evidence uses an unsupported schema version.")
    if request.retail_sale_evidence.schema_version != RETAIL_SALE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Retail sale evidence uses an unsupported schema version.")
    if request.state_supply_evidence.schema_version != STATE_SUPPLY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("State supply evidence uses an unsupported schema version.")
    if request.contractation_evidence.schema_version != CONTRACTATION_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Contractation evidence uses an unsupported schema version.")
    if request.energy_supply_evidence.schema_version != ENERGY_SUPPLY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Energy supply evidence uses an unsupported schema version.")
    if request.real_estate_sale_evidence.schema_version != REAL_ESTATE_SALE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Real estate sale evidence uses an unsupported schema version.")
    if request.enterprise_sale_evidence.schema_version != ENTERPRISE_SALE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Enterprise sale evidence uses an unsupported schema version.")
    if request.barter_evidence.schema_version != BARTER_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Barter evidence uses an unsupported schema version.")
    if request.gift_evidence.schema_version != GIFT_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Gift evidence uses an unsupported schema version.")
    if request.annuity_evidence.schema_version != ANNUITY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Annuity evidence uses an unsupported schema version.")
    if request.lease_evidence.schema_version != LEASE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Lease evidence uses an unsupported schema version.")
    if request.rental_evidence.schema_version != RENTAL_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Rental evidence uses an unsupported schema version.")
    if request.vehicle_lease_evidence.schema_version != VEHICLE_LEASE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Vehicle-lease evidence uses an unsupported schema version.")
    if request.building_lease_evidence.schema_version != BUILDING_LEASE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Building-lease evidence uses an unsupported schema version.")
    if request.enterprise_lease_evidence.schema_version != ENTERPRISE_LEASE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Enterprise-lease evidence uses an unsupported schema version.")
    if request.leasing_evidence.schema_version != LEASING_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Leasing evidence uses an unsupported schema version.")
    if (
        request.residential_lease_evidence.schema_version
        != RESIDENTIAL_LEASE_EVIDENCE_SCHEMA_VERSION
    ):
        raise ValueError("Residential-lease evidence uses an unsupported schema version.")
    if request.gratuitous_use_evidence.schema_version != GRATUITOUS_USE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Gratuitous-use evidence uses an unsupported schema version.")
    if request.work_contract_evidence.schema_version != WORK_CONTRACT_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Work-contract evidence uses an unsupported schema version.")
    if request.consumer_work_evidence.schema_version != CONSUMER_WORK_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Consumer-work evidence uses an unsupported schema version.")
    if (
        request.construction_contract_evidence.schema_version
        != CONSTRUCTION_CONTRACT_EVIDENCE_SCHEMA_VERSION
    ):
        raise ValueError("Construction-contract evidence uses an unsupported schema version.")
    if request.design_work_evidence.schema_version != DESIGN_WORK_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Design-work evidence uses an unsupported schema version.")
    if request.state_work_evidence.schema_version != STATE_WORK_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("State-work evidence uses an unsupported schema version.")
    if request.research_work_evidence.schema_version != RESEARCH_WORK_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Research-work evidence uses an unsupported schema version.")
    if request.paid_services_evidence.schema_version != PAID_SERVICES_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Paid-services evidence uses an unsupported schema version.")
    if request.carriage_evidence.schema_version != CARRIAGE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Carriage evidence uses an unsupported schema version.")
    if request.forwarding_evidence.schema_version != FORWARDING_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Forwarding evidence uses an unsupported schema version.")
    if request.reviewed_norm.source_id not in request.authority_input.candidate_source_ids:
        raise ValueError("Reviewed norm source must be an authority candidate.")

    referenced_source_ids = {
        request.reviewed_norm.source_id,
        *request.temporal_evidence.source_refs,
        *request.authority_input.candidate_source_ids,
        *request.formation_evidence.legal_source_refs,
        *request.temporal_effect_evidence.legal_source_refs,
        *request.limitation_evidence.legal_source_refs,
        *request.interpretation_evidence.legal_source_refs,
        *request.form_evidence.legal_source_refs,
        *request.preliminary_evidence.legal_source_refs,
        *request.third_party_evidence.legal_source_refs,
        *request.public_contract_evidence.legal_source_refs,
        *request.adhesion_evidence.legal_source_refs,
        *request.representations_evidence.legal_source_refs,
        *request.precontractual_evidence.legal_source_refs,
        *request.option_evidence.legal_source_refs,
        *request.framework_evidence.legal_source_refs,
        *request.freedom_evidence.legal_source_refs,
        *request.procedure_evidence.legal_source_refs,
        *request.general_obligations_evidence.legal_source_refs,
        *request.retail_sale_evidence.legal_source_refs,
        *request.state_supply_evidence.legal_source_refs,
        *request.contractation_evidence.legal_source_refs,
        *request.energy_supply_evidence.legal_source_refs,
        *request.real_estate_sale_evidence.legal_source_refs,
        *request.enterprise_sale_evidence.legal_source_refs,
        *request.barter_evidence.legal_source_refs,
        *request.gift_evidence.legal_source_refs,
        *request.annuity_evidence.legal_source_refs,
        *request.lease_evidence.legal_source_refs,
        *request.rental_evidence.legal_source_refs,
        *request.vehicle_lease_evidence.legal_source_refs,
        *request.building_lease_evidence.legal_source_refs,
        *request.enterprise_lease_evidence.legal_source_refs,
        *request.leasing_evidence.legal_source_refs,
        *request.residential_lease_evidence.legal_source_refs,
        *request.gratuitous_use_evidence.legal_source_refs,
        *request.work_contract_evidence.legal_source_refs,
        *request.consumer_work_evidence.legal_source_refs,
        *request.construction_contract_evidence.legal_source_refs,
        *request.design_work_evidence.legal_source_refs,
        *request.state_work_evidence.legal_source_refs,
        *request.research_work_evidence.legal_source_refs,
        *request.paid_services_evidence.legal_source_refs,
        *request.carriage_evidence.legal_source_refs,
        *request.forwarding_evidence.legal_source_refs,
        *request.invalidity_evidence.legal_source_refs,
        *request.security_evidence.legal_source_refs,
        *request.obligation_dynamics_evidence.legal_source_refs,
        *request.performance_remedies_evidence.legal_source_refs,
        *request.sale_evidence.legal_source_refs,
        *request.supply_evidence.legal_source_refs,
        *request.termination_evidence.legal_source_refs,
        *request.liability_evidence.legal_source_refs,
    }
    for assertion in request.case_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.formation_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.temporal_effect_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.limitation_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.interpretation_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.form_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.preliminary_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.third_party_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.public_contract_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.adhesion_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.representations_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.precontractual_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.option_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.framework_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.freedom_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.procedure_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.general_obligations_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.retail_sale_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.state_supply_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.contractation_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.energy_supply_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.real_estate_sale_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.enterprise_sale_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.barter_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.gift_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.annuity_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.lease_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.rental_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.vehicle_lease_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.building_lease_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.enterprise_lease_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.leasing_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.residential_lease_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.gratuitous_use_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.work_contract_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.consumer_work_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.construction_contract_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.design_work_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.state_work_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.research_work_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.paid_services_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.carriage_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.forwarding_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.invalidity_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.security_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.obligation_dynamics_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.performance_remedies_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.sale_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.supply_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.termination_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.liability_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)

    missing_source_ids = sorted(referenced_source_ids - source_registry.keys())
    if missing_source_ids:
        raise ValueError(f"Unknown source references: {', '.join(missing_source_ids)}")
    invalid_liability_legal_sources = [
        source_id
        for source_id in request.liability_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_liability_legal_sources:
        raise ValueError(
            "Liability legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_liability_legal_sources))
        )
    invalid_formation_legal_sources = [
        source_id
        for source_id in request.formation_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_formation_legal_sources:
        raise ValueError(
            "Formation legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_formation_legal_sources))
        )
    invalid_temporal_effect_legal_sources = [
        source_id
        for source_id in request.temporal_effect_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_temporal_effect_legal_sources:
        raise ValueError(
            "Temporal-effect legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_temporal_effect_legal_sources))
        )
    invalid_limitation_legal_sources = [
        source_id
        for source_id in request.limitation_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_limitation_legal_sources:
        raise ValueError(
            "Limitation legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_limitation_legal_sources))
        )
    invalid_interpretation_legal_sources = [
        source_id
        for source_id in request.interpretation_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_interpretation_legal_sources:
        raise ValueError(
            "Interpretation legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_interpretation_legal_sources))
        )
    invalid_form_legal_sources = [
        source_id
        for source_id in request.form_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_form_legal_sources:
        raise ValueError(
            "Form legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_form_legal_sources))
        )
    invalid_preliminary_legal_sources = [
        source_id
        for source_id in request.preliminary_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_preliminary_legal_sources:
        raise ValueError(
            "Preliminary legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_preliminary_legal_sources))
        )
    invalid_third_party_legal_sources = [
        source_id
        for source_id in request.third_party_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_third_party_legal_sources:
        raise ValueError(
            "Third-party legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_third_party_legal_sources))
        )
    invalid_public_contract_legal_sources = [
        source_id
        for source_id in request.public_contract_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_public_contract_legal_sources:
        raise ValueError(
            "Public-contract legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_public_contract_legal_sources))
        )
    invalid_adhesion_legal_sources = [
        source_id
        for source_id in request.adhesion_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_adhesion_legal_sources:
        raise ValueError(
            "Adhesion legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_adhesion_legal_sources))
        )
    invalid_representations_legal_sources = [
        source_id
        for source_id in request.representations_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_representations_legal_sources:
        raise ValueError(
            "Representations legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_representations_legal_sources))
        )
    invalid_precontractual_legal_sources = [
        source_id
        for source_id in request.precontractual_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_precontractual_legal_sources:
        raise ValueError(
            "Precontractual legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_precontractual_legal_sources))
        )
    invalid_option_legal_sources = [
        source_id
        for source_id in request.option_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_option_legal_sources:
        raise ValueError(
            "Option legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_option_legal_sources))
        )
    invalid_framework_legal_sources = [
        source_id
        for source_id in request.framework_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_framework_legal_sources:
        raise ValueError(
            "Framework legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_framework_legal_sources))
        )
    invalid_freedom_legal_sources = [
        source_id
        for source_id in request.freedom_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_freedom_legal_sources:
        raise ValueError(
            "Freedom legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_freedom_legal_sources))
        )
    invalid_procedure_legal_sources = [
        source_id
        for source_id in request.procedure_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_procedure_legal_sources:
        raise ValueError(
            "Procedure legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_procedure_legal_sources))
        )
    invalid_general_obligations_legal_sources = [
        source_id
        for source_id in request.general_obligations_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_general_obligations_legal_sources:
        raise ValueError(
            "General obligations legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_general_obligations_legal_sources))
        )
    invalid_retail_sale_legal_sources = [
        source_id
        for source_id in request.retail_sale_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_retail_sale_legal_sources:
        raise ValueError(
            "Retail sale legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_retail_sale_legal_sources))
        )
    invalid_state_supply_legal_sources = [
        source_id
        for source_id in request.state_supply_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_state_supply_legal_sources:
        raise ValueError(
            "State supply legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_state_supply_legal_sources))
        )
    invalid_contractation_legal_sources = [
        source_id
        for source_id in request.contractation_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_contractation_legal_sources:
        raise ValueError(
            "Contractation legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_contractation_legal_sources))
        )
    invalid_energy_supply_legal_sources = [
        source_id
        for source_id in request.energy_supply_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_energy_supply_legal_sources:
        raise ValueError(
            "Energy supply legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_energy_supply_legal_sources))
        )
    invalid_real_estate_sale_legal_sources = [
        source_id
        for source_id in request.real_estate_sale_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_real_estate_sale_legal_sources:
        raise ValueError(
            "Real estate sale legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_real_estate_sale_legal_sources))
        )
    invalid_enterprise_sale_legal_sources = [
        source_id
        for source_id in request.enterprise_sale_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_enterprise_sale_legal_sources:
        raise ValueError(
            "Enterprise sale legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_enterprise_sale_legal_sources))
        )
    invalid_barter_legal_sources = [
        source_id
        for source_id in request.barter_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_barter_legal_sources:
        raise ValueError(
            "Barter legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_barter_legal_sources))
        )
    invalid_gift_legal_sources = [
        source_id
        for source_id in request.gift_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_gift_legal_sources:
        raise ValueError(
            "Gift legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_gift_legal_sources))
        )
    invalid_annuity_legal_sources = [
        source_id
        for source_id in request.annuity_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_annuity_legal_sources:
        raise ValueError(
            "Annuity legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_annuity_legal_sources))
        )
    invalid_lease_legal_sources = [
        source_id
        for source_id in request.lease_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_lease_legal_sources:
        raise ValueError(
            "Lease legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_lease_legal_sources))
        )
    invalid_rental_legal_sources = [
        source_id
        for source_id in request.rental_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_rental_legal_sources:
        raise ValueError(
            "Rental legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_rental_legal_sources))
        )
    invalid_vehicle_lease_legal_sources = [
        source_id
        for source_id in request.vehicle_lease_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_vehicle_lease_legal_sources:
        raise ValueError(
            "Vehicle-lease legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_vehicle_lease_legal_sources))
        )
    invalid_building_lease_legal_sources = [
        source_id
        for source_id in request.building_lease_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_building_lease_legal_sources:
        raise ValueError(
            "Building-lease legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_building_lease_legal_sources))
        )
    invalid_enterprise_lease_legal_sources = [
        source_id
        for source_id in request.enterprise_lease_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_enterprise_lease_legal_sources:
        raise ValueError(
            "Enterprise-lease legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_enterprise_lease_legal_sources))
        )
    invalid_leasing_legal_sources = [
        source_id
        for source_id in request.leasing_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_leasing_legal_sources:
        raise ValueError(
            "Leasing legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_leasing_legal_sources))
        )
    invalid_residential_lease_legal_sources = [
        source_id
        for source_id in request.residential_lease_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_residential_lease_legal_sources:
        raise ValueError(
            "Residential-lease legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_residential_lease_legal_sources))
        )
    invalid_gratuitous_use_legal_sources = [
        source_id
        for source_id in request.gratuitous_use_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_gratuitous_use_legal_sources:
        raise ValueError(
            "Gratuitous-use legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_gratuitous_use_legal_sources))
        )
    invalid_work_contract_legal_sources = [
        source_id
        for source_id in request.work_contract_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_work_contract_legal_sources:
        raise ValueError(
            "Work-contract legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_work_contract_legal_sources))
        )
    invalid_consumer_work_legal_sources = [
        source_id
        for source_id in request.consumer_work_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_consumer_work_legal_sources:
        raise ValueError(
            "Consumer-work legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_consumer_work_legal_sources))
        )
    invalid_construction_contract_legal_sources = [
        source_id
        for source_id in request.construction_contract_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_construction_contract_legal_sources:
        raise ValueError(
            "Construction-contract legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_construction_contract_legal_sources))
        )
    invalid_design_work_legal_sources = [
        source_id
        for source_id in request.design_work_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_design_work_legal_sources:
        raise ValueError(
            "Design-work legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_design_work_legal_sources))
        )
    invalid_state_work_legal_sources = [
        source_id
        for source_id in request.state_work_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_state_work_legal_sources:
        raise ValueError(
            "State-work legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_state_work_legal_sources))
        )
    invalid_research_work_legal_sources = [
        source_id
        for source_id in request.research_work_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_research_work_legal_sources:
        raise ValueError(
            "Research-work legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_research_work_legal_sources))
        )
    invalid_paid_services_legal_sources = [
        source_id
        for source_id in request.paid_services_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_paid_services_legal_sources:
        raise ValueError(
            "Paid-services legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_paid_services_legal_sources))
        )
    invalid_carriage_legal_sources = [
        source_id
        for source_id in request.carriage_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_carriage_legal_sources:
        raise ValueError(
            "Carriage legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_carriage_legal_sources))
        )
    invalid_forwarding_legal_sources = [
        source_id
        for source_id in request.forwarding_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_forwarding_legal_sources:
        raise ValueError(
            "Forwarding legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_forwarding_legal_sources))
        )
    invalid_invalidity_legal_sources = [
        source_id
        for source_id in request.invalidity_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_invalidity_legal_sources:
        raise ValueError(
            "Invalidity legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_invalidity_legal_sources))
        )
    invalid_security_legal_sources = [
        source_id
        for source_id in request.security_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_security_legal_sources:
        raise ValueError(
            "Security legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_security_legal_sources))
        )
    invalid_dynamics_legal_sources = [
        source_id
        for source_id in request.obligation_dynamics_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_dynamics_legal_sources:
        raise ValueError(
            "Obligation-dynamics legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_dynamics_legal_sources))
        )
    invalid_performance_remedies_legal_sources = [
        source_id
        for source_id in request.performance_remedies_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_performance_remedies_legal_sources:
        raise ValueError(
            "Performance-remedies legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_performance_remedies_legal_sources))
        )
    invalid_sale_legal_sources = [
        source_id
        for source_id in request.sale_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_sale_legal_sources:
        raise ValueError(
            "Sale legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_sale_legal_sources))
        )
    invalid_supply_legal_sources = [
        source_id
        for source_id in request.supply_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_supply_legal_sources:
        raise ValueError(
            "Supply legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_supply_legal_sources))
        )
    invalid_termination_legal_sources = [
        source_id
        for source_id in request.termination_evidence.legal_source_refs
        if source_registry[source_id].source_type == SourceType.FACT
        or not source_registry[source_id].metadata.get("legal_reference")
    ]
    if invalid_termination_legal_sources:
        raise ValueError(
            "Termination legal source refs must identify reviewed legal models: "
            + ", ".join(sorted(invalid_termination_legal_sources))
        )
    return sorted(referenced_source_ids)


def map_reviewed_case_evidence_to_facts(
    evidence: ReviewedCaseEvidence,
    temporal_evidence: ReviewedTemporalEvidence,
    formal_rule: FormalObligationRule,
) -> tuple[CaseEvidenceMappingResult, TemporalEvaluation]:
    _require_reviewed(
        artifact_name="Case evidence",
        review_status=evidence.review_status,
        reviewer_id=evidence.reviewer_id,
    )
    _require_reviewed(
        artifact_name="Temporal evidence",
        review_status=temporal_evidence.review_status,
        reviewer_id=temporal_evidence.reviewer_id,
    )

    assertions_by_predicate = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing_predicates = sorted(
        predicate.value
        for predicate in REQUIRED_EVIDENCE_PREDICATES - assertions_by_predicate.keys()
    )
    if missing_predicates:
        raise ValueError(
            "Reviewed case evidence is incomplete; missing predicates: "
            + ", ".join(missing_predicates)
        )

    temporal_facts = ContractTemporalFacts(
        agreed_due_date=temporal_evidence.agreed_due_date,
        actual_performance_date=temporal_evidence.actual_performance_date,
        evaluation_date=temporal_evidence.evaluation_date,
    )
    temporal_evaluation = evaluate_delivery_due_date(temporal_facts)
    predicate_values = {
        predicate.value: assertions_by_predicate[predicate].value
        for predicate in REQUIRED_EVIDENCE_PREDICATES
    }
    facts = ObligationFactSet(
        due_date_missed=temporal_evaluation.due_date_missed,
        **predicate_values,
    )
    provenance = [
        FactProvenance(
            fact_name="due_date_missed",
            assertion_id=temporal_evidence.id,
            source_refs=list(temporal_evidence.source_refs),
        ),
        *[
            FactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions_by_predicate[predicate].id,
                source_refs=list(assertions_by_predicate[predicate].source_refs),
                formal_atom_refs=(
                    [atom.id for atom in formal_rule.conditions]
                    if predicate == ContractEvidencePredicate.DUTY_EXISTS
                    else [atom.id for atom in formal_rule.exceptions]
                    if predicate == ContractEvidencePredicate.VALID_EXCEPTION_APPLIES
                    else []
                ),
            )
            for predicate in sorted(REQUIRED_EVIDENCE_PREDICATES, key=lambda item: item.value)
        ],
    ]
    return (
        CaseEvidenceMappingResult(
            evidence_id=evidence.id,
            schema_version=evidence.schema_version,
            mapping_version=EVIDENCE_MAPPING_VERSION,
            formal_rule_id=formal_rule.id,
            facts=facts,
            provenance=provenance,
        ),
        temporal_evaluation,
    )


def run_reviewed_contract_analysis(
    request: ReviewedContractAnalysisRequest,
    sources: list[LegalSource],
    *,
    counterfactual_budget: CounterfactualBudget | None = None,
) -> ReviewedContractAnalysisResult:
    norm_reviewer_id = _require_reviewed(
        artifact_name="Reviewed norm",
        review_status=request.reviewed_norm.review_status,
        reviewer_id=request.reviewed_norm.reviewer_id,
    )
    case_reviewer_id = _require_reviewed(
        artifact_name="Case evidence",
        review_status=request.case_evidence.review_status,
        reviewer_id=request.case_evidence.reviewer_id,
    )
    temporal_reviewer_id = _require_reviewed(
        artifact_name="Temporal evidence",
        review_status=request.temporal_evidence.review_status,
        reviewer_id=request.temporal_evidence.reviewer_id,
    )
    authority_reviewer_id = _require_reviewed(
        artifact_name="Authority input",
        review_status=request.authority_input.review_status,
        reviewer_id=request.authority_input.reviewer_id,
    )
    formation_reviewer_id = _require_reviewed(
        artifact_name="Formation evidence",
        review_status=request.formation_evidence.review_status,
        reviewer_id=request.formation_evidence.reviewer_id,
    )
    temporal_effect_reviewer_id = _require_reviewed(
        artifact_name="Temporal-effect evidence",
        review_status=request.temporal_effect_evidence.review_status,
        reviewer_id=request.temporal_effect_evidence.reviewer_id,
    )
    limitation_reviewer_id = _require_reviewed(
        artifact_name="Limitation evidence",
        review_status=request.limitation_evidence.review_status,
        reviewer_id=request.limitation_evidence.reviewer_id,
    )
    interpretation_reviewer_id = _require_reviewed(
        artifact_name="Interpretation evidence",
        review_status=request.interpretation_evidence.review_status,
        reviewer_id=request.interpretation_evidence.reviewer_id,
    )
    form_reviewer_id = _require_reviewed(
        artifact_name="Form evidence",
        review_status=request.form_evidence.review_status,
        reviewer_id=request.form_evidence.reviewer_id,
    )
    preliminary_reviewer_id = _require_reviewed(
        artifact_name="Preliminary evidence",
        review_status=request.preliminary_evidence.review_status,
        reviewer_id=request.preliminary_evidence.reviewer_id,
    )
    third_party_reviewer_id = _require_reviewed(
        artifact_name="Third-party evidence",
        review_status=request.third_party_evidence.review_status,
        reviewer_id=request.third_party_evidence.reviewer_id,
    )
    public_contract_reviewer_id = _require_reviewed(
        artifact_name="Public-contract evidence",
        review_status=request.public_contract_evidence.review_status,
        reviewer_id=request.public_contract_evidence.reviewer_id,
    )
    adhesion_reviewer_id = _require_reviewed(
        artifact_name="Adhesion evidence",
        review_status=request.adhesion_evidence.review_status,
        reviewer_id=request.adhesion_evidence.reviewer_id,
    )
    representations_reviewer_id = _require_reviewed(
        artifact_name="Representations evidence",
        review_status=request.representations_evidence.review_status,
        reviewer_id=request.representations_evidence.reviewer_id,
    )
    precontractual_reviewer_id = _require_reviewed(
        artifact_name="Precontractual evidence",
        review_status=request.precontractual_evidence.review_status,
        reviewer_id=request.precontractual_evidence.reviewer_id,
    )
    option_reviewer_id = _require_reviewed(
        artifact_name="Option evidence",
        review_status=request.option_evidence.review_status,
        reviewer_id=request.option_evidence.reviewer_id,
    )
    framework_reviewer_id = _require_reviewed(
        artifact_name="Framework evidence",
        review_status=request.framework_evidence.review_status,
        reviewer_id=request.framework_evidence.reviewer_id,
    )
    freedom_reviewer_id = _require_reviewed(
        artifact_name="Freedom evidence",
        review_status=request.freedom_evidence.review_status,
        reviewer_id=request.freedom_evidence.reviewer_id,
    )
    procedure_reviewer_id = _require_reviewed(
        artifact_name="Procedure evidence",
        review_status=request.procedure_evidence.review_status,
        reviewer_id=request.procedure_evidence.reviewer_id,
    )
    general_obligations_reviewer_id = _require_reviewed(
        artifact_name="General obligations evidence",
        review_status=request.general_obligations_evidence.review_status,
        reviewer_id=request.general_obligations_evidence.reviewer_id,
    )
    retail_sale_reviewer_id = _require_reviewed(
        artifact_name="Retail sale evidence",
        review_status=request.retail_sale_evidence.review_status,
        reviewer_id=request.retail_sale_evidence.reviewer_id,
    )
    state_supply_reviewer_id = _require_reviewed(
        artifact_name="State supply evidence",
        review_status=request.state_supply_evidence.review_status,
        reviewer_id=request.state_supply_evidence.reviewer_id,
    )
    contractation_reviewer_id = _require_reviewed(
        artifact_name="Contractation evidence",
        review_status=request.contractation_evidence.review_status,
        reviewer_id=request.contractation_evidence.reviewer_id,
    )
    energy_supply_reviewer_id = _require_reviewed(
        artifact_name="Energy supply evidence",
        review_status=request.energy_supply_evidence.review_status,
        reviewer_id=request.energy_supply_evidence.reviewer_id,
    )
    real_estate_sale_reviewer_id = _require_reviewed(
        artifact_name="Real estate sale evidence",
        review_status=request.real_estate_sale_evidence.review_status,
        reviewer_id=request.real_estate_sale_evidence.reviewer_id,
    )
    enterprise_sale_reviewer_id = _require_reviewed(
        artifact_name="Enterprise sale evidence",
        review_status=request.enterprise_sale_evidence.review_status,
        reviewer_id=request.enterprise_sale_evidence.reviewer_id,
    )
    barter_reviewer_id = _require_reviewed(
        artifact_name="Barter evidence",
        review_status=request.barter_evidence.review_status,
        reviewer_id=request.barter_evidence.reviewer_id,
    )
    gift_reviewer_id = _require_reviewed(
        artifact_name="Gift evidence",
        review_status=request.gift_evidence.review_status,
        reviewer_id=request.gift_evidence.reviewer_id,
    )
    annuity_reviewer_id = _require_reviewed(
        artifact_name="Annuity evidence",
        review_status=request.annuity_evidence.review_status,
        reviewer_id=request.annuity_evidence.reviewer_id,
    )
    lease_reviewer_id = _require_reviewed(
        artifact_name="Lease evidence",
        review_status=request.lease_evidence.review_status,
        reviewer_id=request.lease_evidence.reviewer_id,
    )
    rental_reviewer_id = _require_reviewed(
        artifact_name="Rental evidence",
        review_status=request.rental_evidence.review_status,
        reviewer_id=request.rental_evidence.reviewer_id,
    )
    vehicle_lease_reviewer_id = _require_reviewed(
        artifact_name="Vehicle-lease evidence",
        review_status=request.vehicle_lease_evidence.review_status,
        reviewer_id=request.vehicle_lease_evidence.reviewer_id,
    )
    building_lease_reviewer_id = _require_reviewed(
        artifact_name="Building-lease evidence",
        review_status=request.building_lease_evidence.review_status,
        reviewer_id=request.building_lease_evidence.reviewer_id,
    )
    enterprise_lease_reviewer_id = _require_reviewed(
        artifact_name="Enterprise-lease evidence",
        review_status=request.enterprise_lease_evidence.review_status,
        reviewer_id=request.enterprise_lease_evidence.reviewer_id,
    )
    leasing_reviewer_id = _require_reviewed(
        artifact_name="Leasing evidence",
        review_status=request.leasing_evidence.review_status,
        reviewer_id=request.leasing_evidence.reviewer_id,
    )
    residential_lease_reviewer_id = _require_reviewed(
        artifact_name="Residential-lease evidence",
        review_status=request.residential_lease_evidence.review_status,
        reviewer_id=request.residential_lease_evidence.reviewer_id,
    )
    gratuitous_use_reviewer_id = _require_reviewed(
        artifact_name="Gratuitous-use evidence",
        review_status=request.gratuitous_use_evidence.review_status,
        reviewer_id=request.gratuitous_use_evidence.reviewer_id,
    )
    work_contract_reviewer_id = _require_reviewed(
        artifact_name="Work-contract evidence",
        review_status=request.work_contract_evidence.review_status,
        reviewer_id=request.work_contract_evidence.reviewer_id,
    )
    consumer_work_reviewer_id = _require_reviewed(
        artifact_name="Consumer-work evidence",
        review_status=request.consumer_work_evidence.review_status,
        reviewer_id=request.consumer_work_evidence.reviewer_id,
    )
    construction_contract_reviewer_id = _require_reviewed(
        artifact_name="Construction-contract evidence",
        review_status=request.construction_contract_evidence.review_status,
        reviewer_id=request.construction_contract_evidence.reviewer_id,
    )
    design_work_reviewer_id = _require_reviewed(
        artifact_name="Design-work evidence",
        review_status=request.design_work_evidence.review_status,
        reviewer_id=request.design_work_evidence.reviewer_id,
    )
    state_work_reviewer_id = _require_reviewed(
        artifact_name="State-work evidence",
        review_status=request.state_work_evidence.review_status,
        reviewer_id=request.state_work_evidence.reviewer_id,
    )
    research_work_reviewer_id = _require_reviewed(
        artifact_name="Research-work evidence",
        review_status=request.research_work_evidence.review_status,
        reviewer_id=request.research_work_evidence.reviewer_id,
    )
    paid_services_reviewer_id = _require_reviewed(
        artifact_name="Paid-services evidence",
        review_status=request.paid_services_evidence.review_status,
        reviewer_id=request.paid_services_evidence.reviewer_id,
    )
    carriage_reviewer_id = _require_reviewed(
        artifact_name="Carriage evidence",
        review_status=request.carriage_evidence.review_status,
        reviewer_id=request.carriage_evidence.reviewer_id,
    )
    forwarding_reviewer_id = _require_reviewed(
        artifact_name="Forwarding evidence",
        review_status=request.forwarding_evidence.review_status,
        reviewer_id=request.forwarding_evidence.reviewer_id,
    )
    invalidity_reviewer_id = _require_reviewed(
        artifact_name="Invalidity evidence",
        review_status=request.invalidity_evidence.review_status,
        reviewer_id=request.invalidity_evidence.reviewer_id,
    )
    security_reviewer_id = _require_reviewed(
        artifact_name="Security evidence",
        review_status=request.security_evidence.review_status,
        reviewer_id=request.security_evidence.reviewer_id,
    )
    dynamics_reviewer_id = _require_reviewed(
        artifact_name="Obligation-dynamics evidence",
        review_status=request.obligation_dynamics_evidence.review_status,
        reviewer_id=request.obligation_dynamics_evidence.reviewer_id,
    )
    performance_remedies_reviewer_id = _require_reviewed(
        artifact_name="Performance-remedies evidence",
        review_status=request.performance_remedies_evidence.review_status,
        reviewer_id=request.performance_remedies_evidence.reviewer_id,
    )
    sale_reviewer_id = _require_reviewed(
        artifact_name="Sale evidence",
        review_status=request.sale_evidence.review_status,
        reviewer_id=request.sale_evidence.reviewer_id,
    )
    supply_reviewer_id = _require_reviewed(
        artifact_name="Supply evidence",
        review_status=request.supply_evidence.review_status,
        reviewer_id=request.supply_evidence.reviewer_id,
    )
    termination_reviewer_id = _require_reviewed(
        artifact_name="Termination evidence",
        review_status=request.termination_evidence.review_status,
        reviewer_id=request.termination_evidence.reviewer_id,
    )
    liability_reviewer_id = _require_reviewed(
        artifact_name="Liability evidence",
        review_status=request.liability_evidence.review_status,
        reviewer_id=request.liability_evidence.reviewer_id,
    )
    source_registry = _build_source_registry(sources)
    referenced_source_ids = _validate_request_integrity(request, source_registry)

    temporal_facts = ContractTemporalFacts(
        agreed_due_date=request.temporal_evidence.agreed_due_date,
        actual_performance_date=request.temporal_evidence.actual_performance_date,
        evaluation_date=request.temporal_evidence.evaluation_date,
    )
    authority_sources = [
        source_registry[source_id] for source_id in request.authority_input.candidate_source_ids
    ]
    authority_evaluation = evaluate_source_authority(
        authority_sources,
        moment=request.authority_input.evaluation_date,
    )
    source_applicability = evaluate_source_applicability(
        source_registry[request.reviewed_norm.source_id],
        request.temporal_evidence.evaluation_date,
    )
    if not source_applicability.applicable:
        raise ValueError("Reviewed norm source is not applicable at the evaluation date.")
    if (
        authority_evaluation.selected_source_id is not None
        and authority_evaluation.selected_source_id != request.reviewed_norm.source_id
    ):
        raise ValueError("Authority resolution selected a different source than the reviewed norm.")

    formal_translation = translate_reviewed_norm(request.reviewed_norm)
    evidence_mapping, temporal_evaluation = map_reviewed_case_evidence_to_facts(
        request.case_evidence,
        request.temporal_evidence,
        formal_translation.obligation_rule,
    )
    formation_evidence_mapping = map_reviewed_formation_evidence(request.formation_evidence)
    formation_constraint_set = build_formation_constraint_set(formation_evidence_mapping)
    formation_evaluation = evaluate_formation_constraints(
        formation_constraint_set,
        formation_evidence_mapping.facts,
    )
    temporal_effect_evidence_mapping = map_reviewed_temporal_effect_evidence(
        request.temporal_effect_evidence
    )
    temporal_effect_constraint_set = build_temporal_effect_constraint_set(
        temporal_effect_evidence_mapping
    )
    temporal_effect_evaluation = evaluate_temporal_effect_constraints(
        temporal_effect_constraint_set,
        temporal_effect_evidence_mapping.facts,
    )
    if (
        temporal_effect_evaluation.conclusion_moment_established
        and not formation_evaluation.contract_concluded_prerequisites
    ):
        raise ValueError("Temporal-effect conclusion moment does not match formation result.")
    limitation_evidence_mapping = map_reviewed_limitation_evidence(request.limitation_evidence)
    limitation_constraint_set = build_limitation_constraint_set(limitation_evidence_mapping)
    limitation_evaluation = evaluate_limitation_constraints(
        limitation_constraint_set,
        limitation_evidence_mapping.facts,
    )
    interpretation_evidence_mapping = map_reviewed_interpretation_evidence(
        request.interpretation_evidence
    )
    interpretation_constraint_set = build_interpretation_constraint_set(
        interpretation_evidence_mapping
    )
    interpretation_evaluation = evaluate_interpretation_constraints(
        interpretation_constraint_set,
        interpretation_evidence_mapping.facts,
    )
    form_evidence_mapping = map_reviewed_form_evidence(request.form_evidence)
    form_constraint_set = build_form_constraint_set(form_evidence_mapping)
    form_evaluation = evaluate_form_constraints(
        form_constraint_set,
        form_evidence_mapping.facts,
    )
    preliminary_evidence_mapping = map_reviewed_preliminary_evidence(request.preliminary_evidence)
    preliminary_constraint_set = build_preliminary_constraint_set(preliminary_evidence_mapping)
    preliminary_evaluation = evaluate_preliminary_constraints(
        preliminary_constraint_set,
        preliminary_evidence_mapping.facts,
    )
    third_party_evidence_mapping = map_reviewed_third_party_evidence(request.third_party_evidence)
    third_party_constraint_set = build_third_party_constraint_set(third_party_evidence_mapping)
    third_party_evaluation = evaluate_third_party_constraints(
        third_party_constraint_set,
        third_party_evidence_mapping.facts,
    )
    public_contract_evidence_mapping = map_reviewed_public_contract_evidence(
        request.public_contract_evidence
    )
    public_contract_constraint_set = build_public_contract_constraint_set(
        public_contract_evidence_mapping
    )
    public_contract_evaluation = evaluate_public_contract_constraints(
        public_contract_constraint_set,
        public_contract_evidence_mapping.facts,
    )
    adhesion_evidence_mapping = map_reviewed_adhesion_evidence(request.adhesion_evidence)
    adhesion_constraint_set = build_adhesion_constraint_set(adhesion_evidence_mapping)
    adhesion_evaluation = evaluate_adhesion_constraints(
        adhesion_constraint_set,
        adhesion_evidence_mapping.facts,
    )
    representations_evidence_mapping = map_reviewed_representations_evidence(
        request.representations_evidence
    )
    representations_constraint_set = build_representations_constraint_set(
        representations_evidence_mapping
    )
    representations_evaluation = evaluate_representations_constraints(
        representations_constraint_set,
        representations_evidence_mapping.facts,
    )
    precontractual_evidence_mapping = map_reviewed_precontractual_evidence(
        request.precontractual_evidence
    )
    precontractual_constraint_set = build_precontractual_constraint_set(
        precontractual_evidence_mapping
    )
    precontractual_evaluation = evaluate_precontractual_constraints(
        precontractual_constraint_set,
        precontractual_evidence_mapping.facts,
    )
    option_evidence_mapping = map_reviewed_option_evidence(request.option_evidence)
    option_constraint_set = build_option_constraint_set(option_evidence_mapping)
    option_evaluation = evaluate_option_constraints(
        option_constraint_set,
        option_evidence_mapping.facts,
    )
    framework_evidence_mapping = map_reviewed_framework_evidence(request.framework_evidence)
    framework_constraint_set = build_framework_constraint_set(framework_evidence_mapping)
    framework_evaluation = evaluate_framework_constraints(
        framework_constraint_set,
        framework_evidence_mapping.facts,
    )
    freedom_evidence_mapping = map_reviewed_freedom_evidence(request.freedom_evidence)
    freedom_constraint_set = build_freedom_constraint_set(freedom_evidence_mapping)
    freedom_evaluation = evaluate_freedom_constraints(
        freedom_constraint_set,
        freedom_evidence_mapping.facts,
    )
    procedure_evidence_mapping = map_reviewed_procedure_evidence(request.procedure_evidence)
    procedure_constraint_set = build_procedure_constraint_set(procedure_evidence_mapping)
    procedure_evaluation = evaluate_procedure_constraints(
        procedure_constraint_set,
        procedure_evidence_mapping.facts,
    )
    general_obligations_evidence_mapping = map_reviewed_general_obligations_evidence(
        request.general_obligations_evidence
    )
    general_obligations_constraint_set = build_general_obligations_constraint_set(
        general_obligations_evidence_mapping
    )
    general_obligations_evaluation = evaluate_general_obligations_constraints(
        general_obligations_constraint_set,
        general_obligations_evidence_mapping.facts,
    )
    retail_sale_evidence_mapping = map_reviewed_retail_sale_evidence(request.retail_sale_evidence)
    retail_sale_constraint_set = build_retail_sale_constraint_set(retail_sale_evidence_mapping)
    retail_sale_evaluation = evaluate_retail_sale_constraints(
        retail_sale_constraint_set,
        retail_sale_evidence_mapping.facts,
    )
    state_supply_evidence_mapping = map_reviewed_state_supply_evidence(
        request.state_supply_evidence
    )
    state_supply_constraint_set = build_state_supply_constraint_set(state_supply_evidence_mapping)
    state_supply_evaluation = evaluate_state_supply_constraints(
        state_supply_constraint_set,
        state_supply_evidence_mapping.facts,
    )
    contractation_evidence_mapping = map_reviewed_contractation_evidence(
        request.contractation_evidence
    )
    contractation_constraint_set = build_contractation_constraint_set(
        contractation_evidence_mapping
    )
    contractation_evaluation = evaluate_contractation_constraints(
        contractation_constraint_set,
        contractation_evidence_mapping.facts,
    )
    energy_supply_evidence_mapping = map_reviewed_energy_supply_evidence(
        request.energy_supply_evidence
    )
    energy_supply_constraint_set = build_energy_supply_constraint_set(
        energy_supply_evidence_mapping
    )
    energy_supply_evaluation = evaluate_energy_supply_constraints(
        energy_supply_constraint_set,
        energy_supply_evidence_mapping.facts,
    )
    real_estate_sale_evidence_mapping = map_reviewed_real_estate_sale_evidence(
        request.real_estate_sale_evidence
    )
    real_estate_sale_constraint_set = build_real_estate_sale_constraint_set(
        real_estate_sale_evidence_mapping
    )
    real_estate_sale_evaluation = evaluate_real_estate_sale_constraints(
        real_estate_sale_constraint_set,
        real_estate_sale_evidence_mapping.facts,
    )
    enterprise_sale_evidence_mapping = map_reviewed_enterprise_sale_evidence(
        request.enterprise_sale_evidence
    )
    enterprise_sale_constraint_set = build_enterprise_sale_constraint_set(
        enterprise_sale_evidence_mapping
    )
    enterprise_sale_evaluation = evaluate_enterprise_sale_constraints(
        enterprise_sale_constraint_set,
        enterprise_sale_evidence_mapping.facts,
    )
    barter_evidence_mapping = map_reviewed_barter_evidence(request.barter_evidence)
    barter_constraint_set = build_barter_constraint_set(barter_evidence_mapping)
    barter_evaluation = evaluate_barter_constraints(
        barter_constraint_set,
        barter_evidence_mapping.facts,
    )
    gift_evidence_mapping = map_reviewed_gift_evidence(request.gift_evidence)
    gift_constraint_set = build_gift_constraint_set(gift_evidence_mapping)
    gift_evaluation = evaluate_gift_constraints(
        gift_constraint_set,
        gift_evidence_mapping.facts,
    )
    annuity_evidence_mapping = map_reviewed_annuity_evidence(request.annuity_evidence)
    annuity_constraint_set = build_annuity_constraint_set(annuity_evidence_mapping)
    annuity_evaluation = evaluate_annuity_constraints(
        annuity_constraint_set,
        annuity_evidence_mapping.facts,
    )
    lease_evidence_mapping = map_reviewed_lease_evidence(request.lease_evidence)
    lease_constraint_set = build_lease_constraint_set(lease_evidence_mapping)
    lease_evaluation = evaluate_lease_constraints(
        lease_constraint_set,
        lease_evidence_mapping.facts,
    )
    rental_evidence_mapping = map_reviewed_rental_evidence(request.rental_evidence)
    rental_constraint_set = build_rental_constraint_set(rental_evidence_mapping)
    rental_evaluation = evaluate_rental_constraints(
        rental_constraint_set,
        rental_evidence_mapping.facts,
    )
    vehicle_lease_evidence_mapping = map_reviewed_vehicle_lease_evidence(
        request.vehicle_lease_evidence
    )
    vehicle_lease_constraint_set = build_vehicle_lease_constraint_set(
        vehicle_lease_evidence_mapping
    )
    vehicle_lease_evaluation = evaluate_vehicle_lease_constraints(
        vehicle_lease_constraint_set,
        vehicle_lease_evidence_mapping.facts,
    )
    building_lease_evidence_mapping = map_reviewed_building_lease_evidence(
        request.building_lease_evidence
    )
    building_lease_constraint_set = build_building_lease_constraint_set(
        building_lease_evidence_mapping
    )
    building_lease_evaluation = evaluate_building_lease_constraints(
        building_lease_constraint_set,
        building_lease_evidence_mapping.facts,
    )
    enterprise_lease_evidence_mapping = map_reviewed_enterprise_lease_evidence(
        request.enterprise_lease_evidence
    )
    enterprise_lease_constraint_set = build_enterprise_lease_constraint_set(
        enterprise_lease_evidence_mapping
    )
    enterprise_lease_evaluation = evaluate_enterprise_lease_constraints(
        enterprise_lease_constraint_set,
        enterprise_lease_evidence_mapping.facts,
    )
    leasing_evidence_mapping = map_reviewed_leasing_evidence(request.leasing_evidence)
    leasing_constraint_set = build_leasing_constraint_set(leasing_evidence_mapping)
    leasing_evaluation = evaluate_leasing_constraints(
        leasing_constraint_set,
        leasing_evidence_mapping.facts,
    )
    residential_lease_evidence_mapping = map_reviewed_residential_lease_evidence(
        request.residential_lease_evidence
    )
    residential_lease_constraint_set = build_residential_lease_constraint_set(
        residential_lease_evidence_mapping
    )
    residential_lease_evaluation = evaluate_residential_lease_constraints(
        residential_lease_constraint_set,
        residential_lease_evidence_mapping.facts,
    )
    gratuitous_use_evidence_mapping = map_reviewed_gratuitous_use_evidence(
        request.gratuitous_use_evidence
    )
    gratuitous_use_constraint_set = build_gratuitous_use_constraint_set(
        gratuitous_use_evidence_mapping
    )
    gratuitous_use_evaluation = evaluate_gratuitous_use_constraints(
        gratuitous_use_constraint_set,
        gratuitous_use_evidence_mapping.facts,
    )
    work_contract_evidence_mapping = map_reviewed_work_contract_evidence(
        request.work_contract_evidence
    )
    work_contract_constraint_set = build_work_contract_constraint_set(
        work_contract_evidence_mapping
    )
    work_contract_evaluation = evaluate_work_contract_constraints(
        work_contract_constraint_set,
        work_contract_evidence_mapping.facts,
    )
    consumer_work_evidence_mapping = map_reviewed_consumer_work_evidence(
        request.consumer_work_evidence
    )
    consumer_work_constraint_set = build_consumer_work_constraint_set(
        consumer_work_evidence_mapping
    )
    consumer_work_evaluation = evaluate_consumer_work_constraints(
        consumer_work_constraint_set,
        consumer_work_evidence_mapping.facts,
    )
    construction_contract_evidence_mapping = map_reviewed_construction_contract_evidence(
        request.construction_contract_evidence
    )
    construction_contract_constraint_set = build_construction_contract_constraint_set(
        construction_contract_evidence_mapping
    )
    construction_contract_evaluation = evaluate_construction_contract_constraints(
        construction_contract_constraint_set,
        construction_contract_evidence_mapping.facts,
    )
    design_work_evidence_mapping = map_reviewed_design_work_evidence(request.design_work_evidence)
    design_work_constraint_set = build_design_work_constraint_set(design_work_evidence_mapping)
    design_work_evaluation = evaluate_design_work_constraints(
        design_work_constraint_set,
        design_work_evidence_mapping.facts,
    )
    state_work_evidence_mapping = map_reviewed_state_work_evidence(request.state_work_evidence)
    state_work_constraint_set = build_state_work_constraint_set(state_work_evidence_mapping)
    state_work_evaluation = evaluate_state_work_constraints(
        state_work_constraint_set,
        state_work_evidence_mapping.facts,
    )
    research_work_evidence_mapping = map_reviewed_research_work_evidence(
        request.research_work_evidence
    )
    research_work_constraint_set = build_research_work_constraint_set(
        research_work_evidence_mapping
    )
    research_work_evaluation = evaluate_research_work_constraints(
        research_work_constraint_set,
        research_work_evidence_mapping.facts,
    )
    paid_services_evidence_mapping = map_reviewed_paid_services_evidence(
        request.paid_services_evidence
    )
    paid_services_constraint_set = build_paid_services_constraint_set(
        paid_services_evidence_mapping
    )
    paid_services_evaluation = evaluate_paid_services_constraints(
        paid_services_constraint_set,
        paid_services_evidence_mapping.facts,
    )
    carriage_evidence_mapping = map_reviewed_carriage_evidence(request.carriage_evidence)
    carriage_constraint_set = build_carriage_constraint_set(carriage_evidence_mapping)
    carriage_evaluation = evaluate_carriage_constraints(
        carriage_constraint_set,
        carriage_evidence_mapping.facts,
    )
    forwarding_evidence_mapping = map_reviewed_forwarding_evidence(request.forwarding_evidence)
    forwarding_constraint_set = build_forwarding_constraint_set(forwarding_evidence_mapping)
    forwarding_evaluation = evaluate_forwarding_constraints(
        forwarding_constraint_set,
        forwarding_evidence_mapping.facts,
    )
    invalidity_evidence_mapping = map_reviewed_invalidity_evidence(request.invalidity_evidence)
    invalidity_constraint_set = build_invalidity_constraint_set(invalidity_evidence_mapping)
    invalidity_evaluation = evaluate_invalidity_constraints(
        invalidity_constraint_set,
        invalidity_evidence_mapping.facts,
    )
    if (
        invalidity_evidence_mapping.facts.transaction_concluded
        != formation_evaluation.contract_concluded_prerequisites
    ):
        raise ValueError("Invalidity transaction status does not match formation result.")
    expected_contractual_duty = (
        formation_evaluation.contract_concluded_prerequisites
        and not invalidity_evaluation.contractual_effect_displaced
    )
    if expected_contractual_duty != evidence_mapping.facts.duty_exists:
        raise ValueError("Formation and invalidity results do not match contractual duty evidence.")
    constraint_set = build_obligation_constraint_set(formal_translation.obligation_rule)
    constraint_evaluation = evaluate_obligation_constraints(
        constraint_set,
        evidence_mapping.facts,
    )
    dynamics_evidence_mapping = map_reviewed_obligation_dynamics_evidence(
        request.obligation_dynamics_evidence
    )
    if dynamics_evidence_mapping.facts.obligation_exists != evidence_mapping.facts.duty_exists:
        raise ValueError("Obligation-dynamics obligation status does not match duty evidence.")
    if dynamics_evidence_mapping.facts.obligation_breached != constraint_evaluation.breach_issue:
        raise ValueError("Obligation-dynamics breach status does not match obligation evaluation.")
    if (
        dynamics_evidence_mapping.facts.performance_rendered
        != evidence_mapping.facts.performance_completed
    ):
        raise ValueError(
            "Obligation-dynamics performance status does not match performance evidence."
        )
    expected_proper_performance = (
        evidence_mapping.facts.performance_completed
        and not evidence_mapping.facts.performance_nonconforming
    )
    if (
        dynamics_evidence_mapping.facts.performance_accepted_as_proper
        != expected_proper_performance
    ):
        raise ValueError(
            "Obligation-dynamics proper-performance status does not match case evidence."
        )
    dynamics_constraint_set = build_obligation_dynamics_constraint_set(dynamics_evidence_mapping)
    dynamics_evaluation = evaluate_obligation_dynamics_constraints(
        dynamics_constraint_set,
        dynamics_evidence_mapping.facts,
    )
    performance_remedies_evidence_mapping = map_reviewed_performance_remedies_evidence(
        request.performance_remedies_evidence
    )
    performance_facts = performance_remedies_evidence_mapping.facts
    if performance_facts.obligation_exists != evidence_mapping.facts.duty_exists:
        raise ValueError("Performance-remedies obligation status does not match duty evidence.")
    if performance_facts.breach_established != constraint_evaluation.breach_issue:
        raise ValueError("Performance-remedies breach status does not match obligation evaluation.")
    if (
        performance_facts.performance_tendered
        != dynamics_evidence_mapping.facts.performance_rendered
    ):
        raise ValueError(
            "Performance-remedies tender status does not match obligation-dynamics evidence."
        )
    if performance_facts.loss_claimed != evidence_mapping.facts.loss_claimed:
        raise ValueError("Performance-remedies loss claim does not match case evidence.")
    if performance_facts.causation_proven != evidence_mapping.facts.causation_established:
        raise ValueError("Performance-remedies causation does not match case evidence.")
    expected_monetary_delay = (
        evidence_mapping.facts.payment_duty_exists
        and evidence_mapping.facts.payment_due
        and evidence_mapping.facts.payment_missed
        and not evidence_mapping.facts.payment_defense_applies
    )
    if performance_facts.monetary_delay != expected_monetary_delay:
        raise ValueError(
            "Performance-remedies monetary-delay status does not match payment evidence."
        )
    performance_remedies_constraint_set = build_performance_remedies_constraint_set(
        performance_remedies_evidence_mapping
    )
    performance_remedies_evaluation = evaluate_performance_remedies_constraints(
        performance_remedies_constraint_set,
        performance_facts,
    )
    sale_evidence_mapping = map_reviewed_sale_evidence(request.sale_evidence)
    sale_facts = sale_evidence_mapping.facts
    if sale_facts.contract_concluded != formation_evaluation.contract_concluded_prerequisites:
        raise ValueError("Sale contract status does not match formation result.")
    if sale_facts.goods_transfer_completed != evidence_mapping.facts.performance_completed:
        raise ValueError("Sale transfer status does not match performance evidence.")
    if sale_facts.delivery_late != temporal_evaluation.due_date_missed:
        raise ValueError("Sale delay status does not match temporal evaluation.")
    sale_basic_nonconforming = (
        sale_facts.quantity_shortfall or sale_facts.quality_defect or sale_facts.incomplete_goods
    )
    if sale_basic_nonconforming != evidence_mapping.facts.performance_nonconforming:
        raise ValueError("Sale nonconformity does not match performance evidence.")
    if sale_facts.loss_claimed != evidence_mapping.facts.loss_claimed:
        raise ValueError("Sale loss claim does not match case evidence.")
    if sale_facts.causation_proven != evidence_mapping.facts.causation_established:
        raise ValueError("Sale causation does not match case evidence.")
    if sale_facts.payment_due != evidence_mapping.facts.payment_due:
        raise ValueError("Sale payment due status does not match case evidence.")
    sale_constraint_set = build_sale_constraint_set(sale_evidence_mapping)
    sale_evaluation = evaluate_sale_constraints(sale_constraint_set, sale_facts)
    if sale_evaluation.sale_breach_established != constraint_evaluation.breach_issue:
        raise ValueError("Sale breach status does not match obligation evaluation.")
    supply_evidence_mapping = map_reviewed_supply_evidence(request.supply_evidence)
    supply_facts = supply_evidence_mapping.facts
    if supply_facts.contract_concluded != formation_evaluation.contract_concluded_prerequisites:
        raise ValueError("Supply contract status does not match formation result.")
    if supply_facts.delivery_completed != evidence_mapping.facts.performance_completed:
        raise ValueError("Supply delivery status does not match performance evidence.")
    if supply_facts.delivery_late != temporal_evaluation.due_date_missed:
        raise ValueError("Supply delay status does not match temporal evaluation.")
    supply_nonconforming = (
        supply_facts.quantity_shortfall
        or supply_facts.quality_defect
        or supply_facts.incomplete_goods
    )
    if supply_nonconforming != evidence_mapping.facts.performance_nonconforming:
        raise ValueError("Supply nonconformity does not match performance evidence.")
    if supply_facts.loss_claimed != evidence_mapping.facts.loss_claimed:
        raise ValueError("Supply loss claim does not match case evidence.")
    if supply_facts.causation_proven != evidence_mapping.facts.causation_established:
        raise ValueError("Supply causation does not match case evidence.")
    if supply_facts.payment_due != evidence_mapping.facts.payment_due:
        raise ValueError("Supply payment due status does not match case evidence.")
    supply_constraint_set = build_supply_constraint_set(supply_evidence_mapping)
    supply_evaluation = evaluate_supply_constraints(supply_constraint_set, supply_facts)
    sale_supply_pairs = (
        (sale_facts.contract_concluded, supply_facts.contract_concluded, "contract"),
        (sale_facts.goods_transfer_completed, supply_facts.delivery_completed, "delivery"),
        (sale_facts.delivery_late, supply_facts.delivery_late, "delay"),
        (sale_facts.quantity_shortfall, supply_facts.quantity_shortfall, "quantity"),
        (sale_facts.quality_defect, supply_facts.quality_defect, "quality"),
        (sale_facts.incomplete_goods, supply_facts.incomplete_goods, "completeness"),
        (sale_facts.buyer_received_goods, supply_facts.buyer_received_goods, "receipt"),
        (sale_facts.inspection_timely, supply_facts.inspection_timely, "inspection"),
        (sale_facts.discrepancy_found, supply_facts.discrepancy_found, "discrepancy"),
        (sale_facts.prompt_notice_given, supply_facts.prompt_written_notice, "notice"),
        (sale_facts.payment_due, supply_facts.payment_due, "payment due"),
        (sale_facts.buyer_paid, supply_facts.buyer_paid, "payment"),
        (sale_facts.contract_terminated, supply_facts.contract_terminated, "termination"),
    )
    for sale_value, supply_value, label in sale_supply_pairs:
        if sale_value != supply_value:
            raise ValueError(f"Sale and supply {label} facts do not match.")
    if sale_evaluation.sale_contract_qualified != supply_evaluation.supply_contract_qualified:
        raise ValueError("Sale and supply qualification results do not match.")
    if supply_evaluation.supply_breach_established != constraint_evaluation.breach_issue:
        raise ValueError("Supply breach status does not match obligation evaluation.")
    security_evidence_mapping = map_reviewed_security_evidence(request.security_evidence)
    if (
        security_evidence_mapping.facts.main_obligation_exists
        != formation_evaluation.contract_concluded_prerequisites
    ):
        raise ValueError("Security main obligation status does not match formation result.")
    if (
        security_evidence_mapping.facts.main_obligation_invalid
        != invalidity_evaluation.contractual_effect_displaced
    ):
        raise ValueError("Security invalidity status does not match invalidity result.")
    if (
        security_evidence_mapping.facts.main_obligation_breached
        != constraint_evaluation.breach_issue
    ):
        raise ValueError("Security breach status does not match obligation evaluation.")
    security_constraint_set = build_security_constraint_set(security_evidence_mapping)
    security_evaluation = evaluate_security_constraints(
        security_constraint_set,
        security_evidence_mapping.facts,
    )
    termination_evidence_mapping = map_reviewed_termination_evidence(request.termination_evidence)
    termination_constraint_set = build_termination_constraint_set(termination_evidence_mapping)
    termination_evaluation = evaluate_termination_constraints(
        termination_constraint_set,
        termination_evidence_mapping.facts,
    )
    if (
        termination_evidence_mapping.facts.contract_formed
        != formation_evaluation.contract_concluded_prerequisites
    ):
        raise ValueError("Termination contract status does not match formation result.")
    if (
        termination_evidence_mapping.facts.substantial_breach_proven
        and not constraint_evaluation.breach_issue
    ):
        raise ValueError("Substantial breach evidence requires an obligation breach.")
    if supply_facts.contract_terminated != termination_evaluation.effective_termination:
        raise ValueError("Supply termination status does not match termination evaluation.")
    if sale_facts.contract_terminated != termination_evaluation.effective_termination:
        raise ValueError("Sale termination status does not match termination evaluation.")
    if (
        sale_evaluation.sale_contract_refusal_effective
        and not termination_evaluation.effective_termination
    ):
        raise ValueError("Effective sale refusal must be reflected in termination evidence.")
    if (
        supply_evaluation.supply_unilateral_refusal_effective
        and not termination_evaluation.effective_termination
    ):
        raise ValueError("Effective supply refusal must be reflected in termination evidence.")
    liability_evidence_mapping = map_reviewed_liability_evidence(request.liability_evidence)
    if liability_evidence_mapping.facts.breach_established != constraint_evaluation.breach_issue:
        raise ValueError("Liability breach fact does not match obligation evaluation.")
    liability_constraint_set = build_liability_constraint_set(liability_evidence_mapping)
    liability_evaluation = evaluate_liability_constraints(
        liability_constraint_set,
        liability_evidence_mapping.facts,
    )
    counterfactual_sensitivity = run_contract_counterfactual_sensitivity(
        trace_id=f"analysis:{request.id}",
        constraint_set=constraint_set,
        baseline_facts=evidence_mapping.facts,
        budget=counterfactual_budget,
    )
    requires_human_resolution = (
        authority_evaluation.selected_source_id is None
        or formation_evaluation.requires_human_formation_assessment
        or temporal_effect_evaluation.requires_human_temporal_effect_assessment
        or limitation_evaluation.requires_human_limitation_assessment
        or interpretation_evaluation.requires_human_interpretation_assessment
        or form_evaluation.requires_human_form_assessment
        or preliminary_evaluation.requires_human_preliminary_assessment
        or third_party_evaluation.requires_human_third_party_assessment
        or public_contract_evaluation.requires_human_public_contract_assessment
        or adhesion_evaluation.requires_human_adhesion_assessment
        or representations_evaluation.requires_human_representations_assessment
        or precontractual_evaluation.requires_human_precontractual_assessment
        or option_evaluation.requires_human_option_assessment
        or framework_evaluation.requires_human_framework_assessment
        or freedom_evaluation.requires_human_freedom_assessment
        or procedure_evaluation.requires_human_procedure_assessment
        or general_obligations_evaluation.requires_human_general_obligations_assessment
        or retail_sale_evaluation.requires_human_retail_sale_assessment
        or state_supply_evaluation.requires_human_state_supply_assessment
        or contractation_evaluation.requires_human_contractation_assessment
        or energy_supply_evaluation.requires_human_energy_supply_assessment
        or real_estate_sale_evaluation.requires_human_real_estate_sale_assessment
        or enterprise_sale_evaluation.requires_human_enterprise_sale_assessment
        or barter_evaluation.requires_human_barter_assessment
        or gift_evaluation.requires_human_gift_assessment
        or annuity_evaluation.requires_human_annuity_assessment
        or lease_evaluation.requires_human_lease_assessment
        or rental_evaluation.requires_human_rental_assessment
        or vehicle_lease_evaluation.requires_human_vehicle_lease_assessment
        or building_lease_evaluation.requires_human_building_lease_assessment
        or enterprise_lease_evaluation.requires_human_enterprise_lease_assessment
        or leasing_evaluation.requires_human_leasing_assessment
        or residential_lease_evaluation.requires_human_residential_lease_assessment
        or gratuitous_use_evaluation.requires_human_gratuitous_use_assessment
        or work_contract_evaluation.requires_human_work_contract_assessment
        or consumer_work_evaluation.requires_human_consumer_work_assessment
        or construction_contract_evaluation.requires_human_construction_contract_assessment
        or design_work_evaluation.requires_human_design_work_assessment
        or state_work_evaluation.requires_human_state_work_assessment
        or research_work_evaluation.requires_human_research_work_assessment
        or paid_services_evaluation.requires_human_paid_services_assessment
        or carriage_evaluation.requires_human_carriage_assessment
        or forwarding_evaluation.requires_human_forwarding_assessment
        or invalidity_evaluation.requires_human_invalidity_assessment
        or security_evaluation.requires_human_security_assessment
        or dynamics_evaluation.requires_human_dynamics_assessment
        or performance_remedies_evaluation.requires_human_performance_remedies_assessment
        or sale_evaluation.requires_human_sale_assessment
        or supply_evaluation.requires_human_supply_assessment
        or termination_evaluation.requires_human_termination_assessment
    )

    return ReviewedContractAnalysisResult(
        request_id=request.id,
        case_id=request.case_id,
        pipeline_version=ANALYSIS_PIPELINE_VERSION,
        reviewer_ids=sorted(
            {
                norm_reviewer_id,
                case_reviewer_id,
                temporal_reviewer_id,
                authority_reviewer_id,
                formation_reviewer_id,
                temporal_effect_reviewer_id,
                limitation_reviewer_id,
                interpretation_reviewer_id,
                form_reviewer_id,
                preliminary_reviewer_id,
                third_party_reviewer_id,
                public_contract_reviewer_id,
                adhesion_reviewer_id,
                representations_reviewer_id,
                precontractual_reviewer_id,
                option_reviewer_id,
                framework_reviewer_id,
                freedom_reviewer_id,
                procedure_reviewer_id,
                general_obligations_reviewer_id,
                retail_sale_reviewer_id,
                state_supply_reviewer_id,
                contractation_reviewer_id,
                energy_supply_reviewer_id,
                real_estate_sale_reviewer_id,
                enterprise_sale_reviewer_id,
                barter_reviewer_id,
                gift_reviewer_id,
                annuity_reviewer_id,
                lease_reviewer_id,
                rental_reviewer_id,
                vehicle_lease_reviewer_id,
                building_lease_reviewer_id,
                enterprise_lease_reviewer_id,
                leasing_reviewer_id,
                residential_lease_reviewer_id,
                gratuitous_use_reviewer_id,
                work_contract_reviewer_id,
                consumer_work_reviewer_id,
                construction_contract_reviewer_id,
                design_work_reviewer_id,
                state_work_reviewer_id,
                research_work_reviewer_id,
                paid_services_reviewer_id,
                carriage_reviewer_id,
                forwarding_reviewer_id,
                invalidity_reviewer_id,
                security_reviewer_id,
                dynamics_reviewer_id,
                performance_remedies_reviewer_id,
                sale_reviewer_id,
                supply_reviewer_id,
                termination_reviewer_id,
                liability_reviewer_id,
            }
        ),
        source_ids=referenced_source_ids,
        formal_translation=formal_translation,
        temporal_facts=temporal_facts,
        temporal_evaluation=temporal_evaluation,
        source_applicability=source_applicability,
        evidence_mapping=evidence_mapping,
        constraint_set=constraint_set,
        constraint_evaluation=constraint_evaluation,
        temporal_effect_evidence_mapping=temporal_effect_evidence_mapping,
        temporal_effect_constraint_set=temporal_effect_constraint_set,
        temporal_effect_evaluation=temporal_effect_evaluation,
        limitation_evidence_mapping=limitation_evidence_mapping,
        limitation_constraint_set=limitation_constraint_set,
        limitation_evaluation=limitation_evaluation,
        interpretation_evidence_mapping=interpretation_evidence_mapping,
        interpretation_constraint_set=interpretation_constraint_set,
        interpretation_evaluation=interpretation_evaluation,
        form_evidence_mapping=form_evidence_mapping,
        form_constraint_set=form_constraint_set,
        form_evaluation=form_evaluation,
        preliminary_evidence_mapping=preliminary_evidence_mapping,
        preliminary_constraint_set=preliminary_constraint_set,
        preliminary_evaluation=preliminary_evaluation,
        third_party_evidence_mapping=third_party_evidence_mapping,
        third_party_constraint_set=third_party_constraint_set,
        third_party_evaluation=third_party_evaluation,
        public_contract_evidence_mapping=public_contract_evidence_mapping,
        public_contract_constraint_set=public_contract_constraint_set,
        public_contract_evaluation=public_contract_evaluation,
        adhesion_evidence_mapping=adhesion_evidence_mapping,
        adhesion_constraint_set=adhesion_constraint_set,
        adhesion_evaluation=adhesion_evaluation,
        representations_evidence_mapping=representations_evidence_mapping,
        representations_constraint_set=representations_constraint_set,
        representations_evaluation=representations_evaluation,
        precontractual_evidence_mapping=precontractual_evidence_mapping,
        precontractual_constraint_set=precontractual_constraint_set,
        precontractual_evaluation=precontractual_evaluation,
        option_evidence_mapping=option_evidence_mapping,
        option_constraint_set=option_constraint_set,
        option_evaluation=option_evaluation,
        framework_evidence_mapping=framework_evidence_mapping,
        framework_constraint_set=framework_constraint_set,
        framework_evaluation=framework_evaluation,
        freedom_evidence_mapping=freedom_evidence_mapping,
        freedom_constraint_set=freedom_constraint_set,
        freedom_evaluation=freedom_evaluation,
        procedure_evidence_mapping=procedure_evidence_mapping,
        procedure_constraint_set=procedure_constraint_set,
        procedure_evaluation=procedure_evaluation,
        general_obligations_evidence_mapping=general_obligations_evidence_mapping,
        general_obligations_constraint_set=general_obligations_constraint_set,
        general_obligations_evaluation=general_obligations_evaluation,
        retail_sale_evidence_mapping=retail_sale_evidence_mapping,
        retail_sale_constraint_set=retail_sale_constraint_set,
        retail_sale_evaluation=retail_sale_evaluation,
        state_supply_evidence_mapping=state_supply_evidence_mapping,
        state_supply_constraint_set=state_supply_constraint_set,
        state_supply_evaluation=state_supply_evaluation,
        contractation_evidence_mapping=contractation_evidence_mapping,
        contractation_constraint_set=contractation_constraint_set,
        contractation_evaluation=contractation_evaluation,
        energy_supply_evidence_mapping=energy_supply_evidence_mapping,
        energy_supply_constraint_set=energy_supply_constraint_set,
        energy_supply_evaluation=energy_supply_evaluation,
        real_estate_sale_evidence_mapping=real_estate_sale_evidence_mapping,
        real_estate_sale_constraint_set=real_estate_sale_constraint_set,
        real_estate_sale_evaluation=real_estate_sale_evaluation,
        enterprise_sale_evidence_mapping=enterprise_sale_evidence_mapping,
        enterprise_sale_constraint_set=enterprise_sale_constraint_set,
        enterprise_sale_evaluation=enterprise_sale_evaluation,
        barter_evidence_mapping=barter_evidence_mapping,
        barter_constraint_set=barter_constraint_set,
        barter_evaluation=barter_evaluation,
        gift_evidence_mapping=gift_evidence_mapping,
        gift_constraint_set=gift_constraint_set,
        gift_evaluation=gift_evaluation,
        annuity_evidence_mapping=annuity_evidence_mapping,
        annuity_constraint_set=annuity_constraint_set,
        annuity_evaluation=annuity_evaluation,
        lease_evidence_mapping=lease_evidence_mapping,
        lease_constraint_set=lease_constraint_set,
        lease_evaluation=lease_evaluation,
        rental_evidence_mapping=rental_evidence_mapping,
        rental_constraint_set=rental_constraint_set,
        rental_evaluation=rental_evaluation,
        vehicle_lease_evidence_mapping=vehicle_lease_evidence_mapping,
        vehicle_lease_constraint_set=vehicle_lease_constraint_set,
        vehicle_lease_evaluation=vehicle_lease_evaluation,
        building_lease_evidence_mapping=building_lease_evidence_mapping,
        building_lease_constraint_set=building_lease_constraint_set,
        building_lease_evaluation=building_lease_evaluation,
        enterprise_lease_evidence_mapping=enterprise_lease_evidence_mapping,
        enterprise_lease_constraint_set=enterprise_lease_constraint_set,
        enterprise_lease_evaluation=enterprise_lease_evaluation,
        leasing_evidence_mapping=leasing_evidence_mapping,
        leasing_constraint_set=leasing_constraint_set,
        leasing_evaluation=leasing_evaluation,
        residential_lease_evidence_mapping=residential_lease_evidence_mapping,
        residential_lease_constraint_set=residential_lease_constraint_set,
        residential_lease_evaluation=residential_lease_evaluation,
        gratuitous_use_evidence_mapping=gratuitous_use_evidence_mapping,
        gratuitous_use_constraint_set=gratuitous_use_constraint_set,
        gratuitous_use_evaluation=gratuitous_use_evaluation,
        work_contract_evidence_mapping=work_contract_evidence_mapping,
        work_contract_constraint_set=work_contract_constraint_set,
        work_contract_evaluation=work_contract_evaluation,
        consumer_work_evidence_mapping=consumer_work_evidence_mapping,
        consumer_work_constraint_set=consumer_work_constraint_set,
        consumer_work_evaluation=consumer_work_evaluation,
        construction_contract_evidence_mapping=construction_contract_evidence_mapping,
        construction_contract_constraint_set=construction_contract_constraint_set,
        construction_contract_evaluation=construction_contract_evaluation,
        design_work_evidence_mapping=design_work_evidence_mapping,
        design_work_constraint_set=design_work_constraint_set,
        design_work_evaluation=design_work_evaluation,
        state_work_evidence_mapping=state_work_evidence_mapping,
        state_work_constraint_set=state_work_constraint_set,
        state_work_evaluation=state_work_evaluation,
        research_work_evidence_mapping=research_work_evidence_mapping,
        research_work_constraint_set=research_work_constraint_set,
        research_work_evaluation=research_work_evaluation,
        paid_services_evidence_mapping=paid_services_evidence_mapping,
        paid_services_constraint_set=paid_services_constraint_set,
        paid_services_evaluation=paid_services_evaluation,
        carriage_evidence_mapping=carriage_evidence_mapping,
        carriage_constraint_set=carriage_constraint_set,
        carriage_evaluation=carriage_evaluation,
        forwarding_evidence_mapping=forwarding_evidence_mapping,
        forwarding_constraint_set=forwarding_constraint_set,
        forwarding_evaluation=forwarding_evaluation,
        formation_evidence_mapping=formation_evidence_mapping,
        formation_constraint_set=formation_constraint_set,
        formation_evaluation=formation_evaluation,
        invalidity_evidence_mapping=invalidity_evidence_mapping,
        invalidity_constraint_set=invalidity_constraint_set,
        invalidity_evaluation=invalidity_evaluation,
        security_evidence_mapping=security_evidence_mapping,
        security_constraint_set=security_constraint_set,
        security_evaluation=security_evaluation,
        obligation_dynamics_evidence_mapping=dynamics_evidence_mapping,
        obligation_dynamics_constraint_set=dynamics_constraint_set,
        obligation_dynamics_evaluation=dynamics_evaluation,
        performance_remedies_evidence_mapping=performance_remedies_evidence_mapping,
        performance_remedies_constraint_set=performance_remedies_constraint_set,
        performance_remedies_evaluation=performance_remedies_evaluation,
        sale_evidence_mapping=sale_evidence_mapping,
        sale_constraint_set=sale_constraint_set,
        sale_evaluation=sale_evaluation,
        supply_evidence_mapping=supply_evidence_mapping,
        supply_constraint_set=supply_constraint_set,
        supply_evaluation=supply_evaluation,
        termination_evidence_mapping=termination_evidence_mapping,
        termination_constraint_set=termination_constraint_set,
        termination_evaluation=termination_evaluation,
        liability_evidence_mapping=liability_evidence_mapping,
        liability_constraint_set=liability_constraint_set,
        liability_evaluation=liability_evaluation,
        counterfactual_sensitivity=counterfactual_sensitivity,
        authority_evaluation=authority_evaluation,
        requires_human_resolution=requires_human_resolution,
        warnings=[
            "Synthetic reviewed inputs only.",
            "Narrow deterministic analysis; substantive legal assessment remains human-reviewed.",
            "Not legal advice.",
        ],
        warnings_ru=[
            "Используются только синтетические проверенные входные данные.",
            "Детерминированный анализ ограничен узким набором правил; "
            "содержательная правовая оценка остается за экспертом.",
            *formation_evaluation.warnings_ru,
            *invalidity_evaluation.warnings_ru,
            *security_evaluation.warnings_ru,
            *dynamics_evaluation.warnings_ru,
            *performance_remedies_evaluation.warnings_ru,
            *sale_evaluation.warnings_ru,
            *supply_evaluation.warnings_ru,
            *termination_evaluation.warnings_ru,
            *liability_evaluation.warnings_ru,
            "Не является юридической консультацией.",
        ],
    )
