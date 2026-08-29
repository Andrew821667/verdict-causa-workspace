from causa.core.bootstrap import (
    BootstrapReviewStatus,
    NormCondition,
    NormConsequence,
    ReviewedNormJSON,
)
from causa.core.models import LegalSource
from causa.institutional.contracts.reviewed_analysis import (
    CaseEvidenceAssertion,
    ContractEvidencePredicate,
    ReviewedAuthorityInput,
    ReviewedCaseEvidence,
    ReviewedContractAnalysisArtifact,
    ReviewedContractAnalysisRequest,
    ReviewedTemporalEvidence,
    run_reviewed_contract_analysis,
)
from causa.institutional.contracts.liability import (
    LiabilityEvidenceAssertion,
    LiabilityEvidencePredicate,
    ReviewedLiabilityEvidence,
)
from causa.institutional.contracts.formation import (
    FormationEvidenceAssertion,
    FormationEvidencePredicate,
    ReviewedFormationEvidence,
)
from causa.institutional.contracts.temporal_effect import (
    ReviewedTemporalEffectEvidence,
    TemporalEffectEvidenceAssertion,
    TemporalEffectEvidencePredicate,
)
from causa.institutional.contracts.limitation import (
    LimitationEvidenceAssertion,
    LimitationEvidencePredicate,
    ReviewedLimitationEvidence,
)
from causa.institutional.contracts.interpretation import (
    InterpretationEvidenceAssertion,
    InterpretationEvidencePredicate,
    ReviewedInterpretationEvidence,
)
from causa.institutional.contracts.form import (
    FormEvidenceAssertion,
    FormEvidencePredicate,
    ReviewedFormEvidence,
)
from causa.institutional.contracts.preliminary import (
    PreliminaryEvidenceAssertion,
    PreliminaryEvidencePredicate,
    ReviewedPreliminaryEvidence,
)
from causa.institutional.contracts.adhesion import (
    AdhesionEvidenceAssertion,
    AdhesionEvidencePredicate,
    ReviewedAdhesionEvidence,
)
from causa.institutional.contracts.representations import (
    RepresentationsEvidenceAssertion,
    RepresentationsEvidencePredicate,
    ReviewedRepresentationsEvidence,
)
from causa.institutional.contracts.precontractual import (
    PrecontractualEvidenceAssertion,
    PrecontractualEvidencePredicate,
    ReviewedPrecontractualEvidence,
)
from causa.institutional.contracts.framework import (
    FrameworkEvidenceAssertion,
    FrameworkEvidencePredicate,
    ReviewedFrameworkEvidence,
)
from causa.institutional.contracts.freedom import (
    FreedomEvidenceAssertion,
    FreedomEvidencePredicate,
    ReviewedFreedomEvidence,
)
from causa.institutional.contracts.general_obligations import (
    GeneralObligationsEvidenceAssertion,
    GeneralObligationsEvidencePredicate,
    ReviewedGeneralObligationsEvidence,
)
from causa.institutional.contracts.retail_sale import (
    ReviewedRetailSaleEvidence,
    RetailSaleEvidenceAssertion,
    RetailSaleEvidencePredicate,
)
from causa.institutional.contracts.contractation import (
    ContractationEvidenceAssertion,
    ContractationEvidencePredicate,
    ReviewedContractationEvidence,
)
from causa.institutional.contracts.energy_supply import (
    EnergySupplyEvidenceAssertion,
    EnergySupplyEvidencePredicate,
    ReviewedEnergySupplyEvidence,
)
from causa.institutional.contracts.annuity import (
    AnnuityEvidenceAssertion,
    AnnuityEvidencePredicate,
    ReviewedAnnuityEvidence,
)
from causa.institutional.contracts.lease import (
    LeaseEvidenceAssertion,
    LeaseEvidencePredicate,
    ReviewedLeaseEvidence,
)
from causa.institutional.contracts.rental import (
    RentalEvidenceAssertion,
    RentalEvidencePredicate,
    ReviewedRentalEvidence,
)
from causa.institutional.contracts.vehicle_lease import (
    ReviewedVehicleLeaseEvidence,
    VehicleLeaseEvidenceAssertion,
    VehicleLeaseEvidencePredicate,
)
from causa.institutional.contracts.building_lease import (
    BuildingLeaseEvidenceAssertion,
    BuildingLeaseEvidencePredicate,
    ReviewedBuildingLeaseEvidence,
)
from causa.institutional.contracts.enterprise_lease import (
    EnterpriseLeaseEvidenceAssertion,
    EnterpriseLeaseEvidencePredicate,
    ReviewedEnterpriseLeaseEvidence,
)
from causa.institutional.contracts.leasing import (
    LeasingEvidenceAssertion,
    LeasingEvidencePredicate,
    ReviewedLeasingEvidence,
)
from causa.institutional.contracts.residential_lease import (
    ResidentialLeaseEvidenceAssertion,
    ResidentialLeaseEvidencePredicate,
    ReviewedResidentialLeaseEvidence,
)
from causa.institutional.contracts.gratuitous_use import (
    GratuitousUseEvidenceAssertion,
    GratuitousUseEvidencePredicate,
    ReviewedGratuitousUseEvidence,
)
from causa.institutional.contracts.construction_contract import (
    ConstructionContractEvidenceAssertion,
    ConstructionContractEvidencePredicate,
    ReviewedConstructionContractEvidence,
)
from causa.institutional.contracts.objects import (
    ObjectsEvidenceAssertion,
    ObjectsEvidencePredicate,
    ReviewedObjectsEvidence,
)
from causa.institutional.contracts.persons import (
    PersonsEvidenceAssertion,
    PersonsEvidencePredicate,
    ReviewedPersonsEvidence,
)
from causa.institutional.contracts.messages import (
    MessagesEvidenceAssertion,
    MessagesEvidencePredicate,
    ReviewedMessagesEvidence,
)
from causa.institutional.contracts.special_accounts import (
    ReviewedSpecialAccountsEvidence,
    SpecialAccountsEvidenceAssertion,
    SpecialAccountsEvidencePredicate,
)
from causa.institutional.contracts.escrow_deposit import (
    EscrowDepositEvidenceAssertion,
    EscrowDepositEvidencePredicate,
    ReviewedEscrowDepositEvidence,
)
from causa.institutional.contracts.bankruptcy_claims import (
    BankruptcyClaimsEvidenceAssertion,
    BankruptcyClaimsEvidencePredicate,
    ReviewedBankruptcyClaimsEvidence,
)
from causa.institutional.contracts.bankruptcy_ranking import (
    BankruptcyRankingEvidenceAssertion,
    BankruptcyRankingEvidencePredicate,
    ReviewedBankruptcyRankingEvidence,
)
from causa.institutional.contracts.bankruptcy_contest import (
    BankruptcyContestEvidenceAssertion,
    BankruptcyContestEvidencePredicate,
    ReviewedBankruptcyContestEvidence,
)
from causa.institutional.contracts.bankruptcy_setoff import (
    BankruptcySetoffEvidenceAssertion,
    BankruptcySetoffEvidencePredicate,
    ReviewedBankruptcySetoffEvidence,
)
from causa.institutional.contracts.attribution_delay import (
    AttributionDelayEvidenceAssertion,
    AttributionDelayEvidencePredicate,
    ReviewedAttributionDelayEvidence,
)
from causa.institutional.contracts.meeting_decisions import (
    MeetingDecisionsEvidenceAssertion,
    MeetingDecisionsEvidencePredicate,
    ReviewedMeetingDecisionsEvidence,
)
from causa.institutional.contracts.terms import (
    ReviewedTermsEvidence,
    TermsEvidenceAssertion,
    TermsEvidencePredicate,
)
from causa.institutional.contracts.transactions import (
    ReviewedTransactionsEvidence,
    TransactionsEvidenceAssertion,
    TransactionsEvidencePredicate,
)
from causa.institutional.contracts.civil_principles import (
    CivilPrinciplesEvidenceAssertion,
    CivilPrinciplesEvidencePredicate,
    ReviewedCivilPrinciplesEvidence,
)
from causa.institutional.contracts.property_rights import (
    PropertyRightsEvidenceAssertion,
    PropertyRightsEvidencePredicate,
    ReviewedPropertyRightsEvidence,
)
from causa.institutional.contracts.representation import (
    RepresentationEvidenceAssertion,
    RepresentationEvidencePredicate,
    ReviewedRepresentationEvidence,
)
from causa.institutional.contracts.unjust_enrichment import (
    ReviewedUnjustEnrichmentEvidence,
    UnjustEnrichmentEvidenceAssertion,
    UnjustEnrichmentEvidencePredicate,
)
from causa.institutional.contracts.moral_harm import (
    MoralHarmEvidenceAssertion,
    MoralHarmEvidencePredicate,
    ReviewedMoralHarmEvidence,
)
from causa.institutional.contracts.product_liability import (
    ProductLiabilityEvidenceAssertion,
    ProductLiabilityEvidencePredicate,
    ReviewedProductLiabilityEvidence,
)
from causa.institutional.contracts.tort_life_health import (
    ReviewedTortLifeHealthEvidence,
    TortLifeHealthEvidenceAssertion,
    TortLifeHealthEvidencePredicate,
)
from causa.institutional.contracts.tort_general import (
    ReviewedTortGeneralEvidence,
    TortGeneralEvidenceAssertion,
    TortGeneralEvidencePredicate,
)
from causa.institutional.contracts.games import (
    GamesEvidenceAssertion,
    GamesEvidencePredicate,
    ReviewedGamesEvidence,
)
from causa.institutional.contracts.public_promise import (
    PublicPromiseEvidenceAssertion,
    PublicPromiseEvidencePredicate,
    ReviewedPublicPromiseEvidence,
)
from causa.institutional.contracts.partnership import (
    PartnershipEvidenceAssertion,
    PartnershipEvidencePredicate,
    ReviewedPartnershipEvidence,
)
from causa.institutional.contracts.franchise import (
    FranchiseEvidenceAssertion,
    FranchiseEvidencePredicate,
    ReviewedFranchiseEvidence,
)
from causa.institutional.contracts.trust_management import (
    ReviewedTrustManagementEvidence,
    TrustManagementEvidenceAssertion,
    TrustManagementEvidencePredicate,
)
from causa.institutional.contracts.agency import (
    AgencyEvidenceAssertion,
    AgencyEvidencePredicate,
    ReviewedAgencyEvidence,
)
from causa.institutional.contracts.commission import (
    CommissionEvidenceAssertion,
    CommissionEvidencePredicate,
    ReviewedCommissionEvidence,
)
from causa.institutional.contracts.negotiorum_gestio import (
    NegotiorumGestioEvidenceAssertion,
    NegotiorumGestioEvidencePredicate,
    ReviewedNegotiorumGestioEvidence,
)
from causa.institutional.contracts.mandate import (
    MandateEvidenceAssertion,
    MandateEvidencePredicate,
    ReviewedMandateEvidence,
)
from causa.institutional.contracts.insurance_settlement import (
    InsuranceSettlementEvidenceAssertion,
    InsuranceSettlementEvidencePredicate,
    ReviewedInsuranceSettlementEvidence,
)
from causa.institutional.contracts.insurance import (
    InsuranceEvidenceAssertion,
    InsuranceEvidencePredicate,
    ReviewedInsuranceEvidence,
)
from causa.institutional.contracts.special_storage import (
    ReviewedSpecialStorageEvidence,
    SpecialStorageEvidenceAssertion,
    SpecialStorageEvidencePredicate,
)
from causa.institutional.contracts.warehouse_storage import (
    ReviewedWarehouseStorageEvidence,
    WarehouseStorageEvidenceAssertion,
    WarehouseStorageEvidencePredicate,
)
from causa.institutional.contracts.storage import (
    ReviewedStorageEvidence,
    StorageEvidenceAssertion,
    StorageEvidencePredicate,
)
from causa.institutional.contracts.settlements import (
    ReviewedSettlementsEvidence,
    SettlementsEvidenceAssertion,
    SettlementsEvidencePredicate,
)
from causa.institutional.contracts.bank_account import (
    BankAccountEvidenceAssertion,
    BankAccountEvidencePredicate,
    ReviewedBankAccountEvidence,
)
from causa.institutional.contracts.bank_deposit import (
    BankDepositEvidenceAssertion,
    BankDepositEvidencePredicate,
    ReviewedBankDepositEvidence,
)
from causa.institutional.contracts.factoring import (
    FactoringEvidenceAssertion,
    FactoringEvidencePredicate,
    ReviewedFactoringEvidence,
)
from causa.institutional.contracts.commercial_credit import (
    CommercialCreditEvidenceAssertion,
    CommercialCreditEvidencePredicate,
    ReviewedCommercialCreditEvidence,
)
from causa.institutional.contracts.credit import (
    CreditEvidenceAssertion,
    CreditEvidencePredicate,
    ReviewedCreditEvidence,
)
from causa.institutional.contracts.loan import (
    LoanEvidenceAssertion,
    LoanEvidencePredicate,
    ReviewedLoanEvidence,
)
from causa.institutional.contracts.forwarding import (
    ForwardingEvidenceAssertion,
    ForwardingEvidencePredicate,
    ReviewedForwardingEvidence,
)
from causa.institutional.contracts.carriage import (
    CarriageEvidenceAssertion,
    CarriageEvidencePredicate,
    ReviewedCarriageEvidence,
)
from causa.institutional.contracts.paid_services import (
    PaidServicesEvidenceAssertion,
    PaidServicesEvidencePredicate,
    ReviewedPaidServicesEvidence,
)
from causa.institutional.contracts.research_work import (
    ResearchWorkEvidenceAssertion,
    ResearchWorkEvidencePredicate,
    ReviewedResearchWorkEvidence,
)
from causa.institutional.contracts.state_work import (
    ReviewedStateWorkEvidence,
    StateWorkEvidenceAssertion,
    StateWorkEvidencePredicate,
)
from causa.institutional.contracts.design_work import (
    DesignWorkEvidenceAssertion,
    DesignWorkEvidencePredicate,
    ReviewedDesignWorkEvidence,
)
from causa.institutional.contracts.consumer_work import (
    ConsumerWorkEvidenceAssertion,
    ConsumerWorkEvidencePredicate,
    ReviewedConsumerWorkEvidence,
)
from causa.institutional.contracts.work_contract import (
    ReviewedWorkContractEvidence,
    WorkContractEvidenceAssertion,
    WorkContractEvidencePredicate,
)
from causa.institutional.contracts.barter import (
    BarterEvidenceAssertion,
    BarterEvidencePredicate,
    ReviewedBarterEvidence,
)
from causa.institutional.contracts.gift import (
    GiftEvidenceAssertion,
    GiftEvidencePredicate,
    ReviewedGiftEvidence,
)
from causa.institutional.contracts.enterprise_sale import (
    EnterpriseSaleEvidenceAssertion,
    EnterpriseSaleEvidencePredicate,
    ReviewedEnterpriseSaleEvidence,
)
from causa.institutional.contracts.real_estate_sale import (
    RealEstateSaleEvidenceAssertion,
    RealEstateSaleEvidencePredicate,
    ReviewedRealEstateSaleEvidence,
)
from causa.institutional.contracts.state_supply import (
    ReviewedStateSupplyEvidence,
    StateSupplyEvidenceAssertion,
    StateSupplyEvidencePredicate,
)
from causa.institutional.contracts.procedure import (
    ProcedureEvidenceAssertion,
    ProcedureEvidencePredicate,
    ReviewedProcedureEvidence,
)
from causa.institutional.contracts.option import (
    OptionEvidenceAssertion,
    OptionEvidencePredicate,
    ReviewedOptionEvidence,
)
from causa.institutional.contracts.public_contract import (
    PublicContractEvidenceAssertion,
    PublicContractEvidencePredicate,
    ReviewedPublicContractEvidence,
)
from causa.institutional.contracts.third_party import (
    ReviewedThirdPartyEvidence,
    ThirdPartyEvidenceAssertion,
    ThirdPartyEvidencePredicate,
)
from causa.institutional.contracts.termination import (
    ReviewedTerminationEvidence,
    TerminationEvidenceAssertion,
    TerminationEvidencePredicate,
)
from causa.institutional.contracts.invalidity import (
    InvalidityEvidenceAssertion,
    InvalidityEvidencePredicate,
    ReviewedInvalidityEvidence,
)
from causa.institutional.contracts.security import (
    ReviewedSecurityEvidence,
    SecurityEvidenceAssertion,
    SecurityEvidencePredicate,
)
from causa.institutional.contracts.obligation_dynamics import (
    ObligationDynamicsEvidenceAssertion,
    ObligationDynamicsEvidencePredicate,
    ReviewedObligationDynamicsEvidence,
)
from causa.institutional.contracts.performance_remedies import (
    PerformanceRemediesEvidenceAssertion,
    PerformanceRemediesEvidencePredicate,
    ReviewedPerformanceRemediesEvidence,
)
from causa.institutional.contracts.sale import (
    ReviewedSaleEvidence,
    SaleEvidenceAssertion,
    SaleEvidencePredicate,
)
from causa.institutional.contracts.supply import (
    ReviewedSupplyEvidence,
    SupplyEvidenceAssertion,
    SupplyEvidencePredicate,
)
from causa.institutional.contracts.synthetic_sources import (
    get_synthetic_contract_source,
)
from causa.reasoning.counterfactual import CounterfactualBudget


SYNTHETIC_ANALYSIS_SOURCE_IDS = (
    "synthetic-ru-contract-supply-delivery-duty-v1",
    "synthetic-ru-contract-supply-delivery-duty-v2",
    "synthetic-ru-contract-supply-delivery-term",
    "synthetic-case-supply-1-reviewed-evidence",
    "synthetic-ru-gk432-contract-formation-model-v1",
    "synthetic-ru-gk435-offer-model-v1",
    "synthetic-ru-gk438-443-acceptance-model-v1",
    "synthetic-ru-plenum49-formation-guidance-v1",
    "synthetic-case-supply-1-formation-evidence",
    "synthetic-ru-gk425-contract-effect-model-v1",
    "synthetic-ru-gk433-conclusion-moment-model-v1",
    "synthetic-case-supply-1-temporal-effect-evidence",
    "synthetic-ru-gk195-200-limitation-framework-v1",
    "synthetic-ru-gk202-208-limitation-effects-v1",
    "synthetic-case-supply-1-limitation-evidence",
    "synthetic-ru-gk431-interpretation-model-v1",
    "synthetic-ru-gk431-common-intent-model-v1",
    "synthetic-case-supply-1-interpretation-evidence",
    "synthetic-ru-gk158-165-form-framework-v1",
    "synthetic-ru-gk160-434-written-form-model-v1",
    "synthetic-case-supply-1-form-evidence",
    "synthetic-ru-gk429-preliminary-framework-v1",
    "synthetic-ru-gk429-445-preliminary-compulsion-v1",
    "synthetic-case-supply-1-preliminary-evidence",
    "synthetic-ru-gk430-third-party-framework-v1",
    "synthetic-ru-gk430-third-party-change-v1",
    "synthetic-case-supply-1-third-party-evidence",
    "synthetic-ru-gk426-public-contract-framework-v1",
    "synthetic-ru-gk426-public-contract-terms-v1",
    "synthetic-case-supply-1-public-contract-evidence",
    "synthetic-ru-gk428-adhesion-framework-v1",
    "synthetic-ru-gk428-adhesion-relief-v1",
    "synthetic-case-supply-1-adhesion-evidence",
    "synthetic-ru-gk431-2-representations-framework-v1",
    "synthetic-ru-gk431-2-representations-remedies-v1",
    "synthetic-case-supply-1-representations-evidence",
    "synthetic-ru-gk434-1-precontractual-framework-v1",
    "synthetic-ru-gk434-1-precontractual-remedies-v1",
    "synthetic-case-supply-1-precontractual-evidence",
    "synthetic-ru-gk429-2-option-framework-v1",
    "synthetic-ru-gk429-3-option-contract-v1",
    "synthetic-case-supply-1-option-evidence",
    "synthetic-ru-gk429-1-framework-agreement-v1",
    "synthetic-ru-gk429-4-subscription-agreement-v1",
    "synthetic-case-supply-1-framework-evidence",
    "synthetic-ru-gk421-422-freedom-of-contract-v1",
    "synthetic-ru-gk423-424-onerousness-and-price-v1",
    "synthetic-ru-gk427-standard-terms-v1",
    "synthetic-case-supply-1-freedom-evidence",
    "synthetic-ru-gk445-446-mandatory-conclusion-v1",
    "synthetic-ru-gk447-449-auction-v1",
    "synthetic-ru-gk449-1-public-auction-v1",
    "synthetic-case-supply-1-procedure-evidence",
    "synthetic-ru-gk307-308-obligation-concept-v1",
    "synthetic-ru-gk3081-3083-obligation-types-and-protection-v1",
    "synthetic-case-supply-1-general-obligations-evidence",
    "synthetic-ru-gk492-495-retail-sale-concept-v1",
    "synthetic-ru-gk502-504-retail-exchange-and-quality-v1",
    "synthetic-case-supply-1-retail-sale-evidence",
    "synthetic-ru-gk525-528-state-contract-v1",
    "synthetic-ru-gk529-534-state-supply-performance-v1",
    "synthetic-case-supply-1-state-supply-evidence",
    "synthetic-ru-gk535-536-contractation-concept-v1",
    "synthetic-ru-gk537-538-contractation-duties-and-liability-v1",
    "synthetic-case-supply-1-contractation-evidence",
    "synthetic-ru-gk539-542-energy-supply-concept-v1",
    "synthetic-ru-gk543-547-energy-supply-duties-and-interruption-v1",
    "synthetic-case-supply-1-energy-supply-evidence",
    "synthetic-ru-gk549-552-real-estate-sale-concept-v1",
    "synthetic-ru-gk554-558-real-estate-sale-terms-and-transfer-v1",
    "synthetic-case-supply-1-real-estate-sale-evidence",
    "synthetic-ru-gk559-561-enterprise-sale-concept-v1",
    "synthetic-ru-gk562-566-enterprise-sale-creditors-and-transfer-v1",
    "synthetic-case-supply-1-enterprise-sale-evidence",
    "synthetic-ru-gk567-568-barter-concept-and-price-v1",
    "synthetic-ru-gk569-571-barter-performance-and-eviction-v1",
    "synthetic-case-supply-1-barter-evidence",
    "synthetic-ru-gk572-576-gift-concept-and-form-v1",
    "synthetic-ru-gk573-582-gift-refusal-revocation-and-donation-v1",
    "synthetic-case-supply-1-gift-evidence",
    "synthetic-ru-gk583-593-annuity-general-and-permanent-v1",
    "synthetic-ru-gk596-605-annuity-life-and-maintenance-v1",
    "synthetic-case-supply-1-annuity-evidence",
    "synthetic-ru-gk606-614-lease-concept-object-and-rent-v1",
    "synthetic-ru-gk615-625-lease-use-repair-and-renewal-v1",
    "synthetic-case-supply-1-lease-evidence",
    "synthetic-ru-gk626-628-rental-concept-form-and-term-v1",
    "synthetic-ru-gk629-631-rental-defects-payment-and-repair-v1",
    "synthetic-case-supply-1-rental-evidence",
    "synthetic-ru-gk632-641-vehicle-lease-with-crew-v1",
    "synthetic-ru-gk642-649-vehicle-lease-without-crew-v1",
    "synthetic-case-supply-1-vehicle-lease-evidence",
    "synthetic-ru-gk650-651-building-lease-concept-form-and-registration-v1",
    "synthetic-ru-gk652-655-building-lease-land-rent-and-transfer-v1",
    "synthetic-case-supply-1-building-lease-evidence",
    "synthetic-ru-gk656-659-enterprise-lease-concept-form-and-creditors-v1",
    "synthetic-ru-gk660-664-enterprise-lease-use-maintenance-and-return-v1",
    "synthetic-case-supply-1-enterprise-lease-evidence",
    "synthetic-ru-gk665-667-leasing-concept-object-and-notice-v1",
    "synthetic-ru-gk668-670-leasing-delivery-risk-and-seller-claims-v1",
    "synthetic-case-supply-1-leasing-evidence",
    "synthetic-ru-gk671-678-residential-lease-concept-form-and-duties-v1",
    "synthetic-ru-gk682-688-residential-lease-rent-renewal-and-termination-v1",
    "synthetic-case-supply-1-residential-lease-evidence",
    "synthetic-ru-gk689-694-gratuitous-use-concept-limits-and-defects-v1",
    "synthetic-ru-gk695-701-gratuitous-use-maintenance-risk-and-termination-v1",
    "synthetic-case-supply-1-gratuitous-use-evidence",
    "synthetic-ru-gk702-716-work-contract-concept-terms-and-materials-v1",
    "synthetic-ru-gk717-729-work-contract-quality-acceptance-and-withdrawal-v1",
    "synthetic-case-supply-1-work-contract-evidence",
    "synthetic-ru-gk730-736-consumer-work-concept-information-and-payment-v1",
    "synthetic-ru-gk737-739-consumer-work-defects-and-uncollected-result-v1",
    "synthetic-case-supply-1-consumer-work-evidence",
    "synthetic-ru-gk740-749-construction-contract-concept-documentation-and-duties-v1",
    "synthetic-ru-gk752-757-construction-contract-conservation-acceptance-and-quality-v1",
    "synthetic-case-supply-1-construction-contract-evidence",
    "synthetic-ru-gk758-760-design-work-concept-initial-data-and-approval-v1",
    "synthetic-ru-gk761-762-design-work-liability-and-customer-duties-v1",
    "synthetic-case-supply-1-design-work-evidence",
    "synthetic-ru-gk763-766-state-work-contract-basis-parties-and-terms-v1",
    "synthetic-ru-gk767-768-state-work-budget-changes-and-special-law-v1",
    "synthetic-case-supply-1-state-work-evidence",
    "synthetic-ru-gk769-774-research-work-concept-confidentiality-and-duties-v1",
    "synthetic-ru-gk775-778-research-work-impossibility-and-liability-v1",
    "synthetic-case-supply-1-research-work-evidence",
    "synthetic-ru-gk779-781-paid-services-concept-personal-performance-and-payment-v1",
    "synthetic-ru-gk782-783-1-paid-services-withdrawal-and-communication-v1",
    "synthetic-case-supply-1-paid-services-evidence",
    "synthetic-ru-gk784-792-carriage-concept-documents-and-obligations-v1",
    "synthetic-ru-gk793-800-carriage-liability-and-claims-v1",
    "synthetic-case-supply-1-carriage-evidence",
    "synthetic-ru-gk801-804-forwarding-concept-form-and-information-v1",
    "synthetic-ru-gk805-806-forwarding-third-parties-and-withdrawal-v1",
    "synthetic-case-supply-1-forwarding-evidence",
    "synthetic-ru-gk807-811-loan-concept-form-interest-and-repayment-v1",
    "synthetic-ru-gk812-818-loan-challenge-security-purpose-and-novation-v1",
    "synthetic-case-supply-1-loan-evidence",
    "synthetic-ru-gk819-820-credit-concept-parties-and-form-v1",
    "synthetic-ru-gk821-821-1-credit-refusal-and-early-repayment-v1",
    "synthetic-case-supply-1-credit-evidence",
    "synthetic-ru-gk822-goods-credit-concept-and-sale-rules-v1",
    "synthetic-ru-gk823-commercial-credit-forms-and-applicable-rules-v1",
    "synthetic-case-supply-1-commercial-credit-evidence",
    "synthetic-ru-gk824-829-factoring-concept-parties-and-assignment-v1",
    "synthetic-ru-gk830-833-factoring-debtor-performance-and-settlements-v1",
    "synthetic-case-supply-1-factoring-evidence",
    "synthetic-ru-gk834-839-bank-deposit-concept-form-and-interest-v1",
    "synthetic-ru-gk840-844-bank-deposit-security-third-parties-and-documents-v1",
    "synthetic-ru-gk844-1-precious-metal-deposit-v1",
    "synthetic-case-supply-1-bank-deposit-evidence",
    "synthetic-ru-gk845-853-bank-account-concept-operations-and-payment-v1",
    "synthetic-ru-gk854-860-bank-account-debiting-secrecy-and-termination-v1",
    "synthetic-case-supply-1-bank-account-evidence",
    "synthetic-ru-gk861-876-settlements-forms-orders-credit-and-collection-v1",
    "synthetic-ru-gk877-885-settlements-cheque-rules-v1",
    "synthetic-case-supply-1-settlements-evidence",
    "synthetic-ru-gk886-895-storage-concept-form-period-and-safekeeping-v1",
    "synthetic-ru-gk896-906-storage-remuneration-return-and-liability-v1",
    "synthetic-case-supply-1-storage-evidence",
    "synthetic-ru-gk907-911-warehouse-storage-concept-and-inspection-v1",
    "synthetic-ru-gk912-918-warehouse-documents-and-goods-release-v1",
    "synthetic-case-supply-1-warehouse-storage-evidence",
    "synthetic-ru-gk919-923-special-storage-pawnshop-bank-and-lockers-v1",
    "synthetic-ru-gk924-926-special-storage-cloakroom-hotel-and-sequestration-v1",
    "synthetic-case-supply-1-special-storage-evidence",
    "synthetic-ru-gk927-938-insurance-forms-interests-and-parties-v1",
    "synthetic-ru-gk939-943-insurance-contract-form-and-terms-v1",
    "synthetic-case-supply-1-insurance-evidence",
    "synthetic-ru-gk944-959-insurance-settlement-disclosure-sum-and-premium-v1",
    "synthetic-ru-gk960-970-insurance-settlement-notice-release-and-subrogation-v1",
    "synthetic-case-supply-1-insurance-settlement-evidence",
    "synthetic-ru-gk971-976-mandate-concept-instructions-and-duties-v1",
    "synthetic-ru-gk977-979-mandate-termination-and-consequences-v1",
    "synthetic-case-supply-1-mandate-evidence",
    "synthetic-ru-gk980-983-gestio-conditions-notice-and-approval-v1",
    "synthetic-ru-gk984-989-gestio-expenses-remuneration-and-reporting-v1",
    "synthetic-case-supply-1-negotiorum-gestio-evidence",
    "synthetic-ru-gk990-998-commission-concept-execution-and-property-v1",
    "synthetic-ru-gk999-1004-commission-report-duties-and-termination-v1",
    "synthetic-case-supply-1-commission-evidence",
    "synthetic-ru-gk1005-1008-agency-concept-remuneration-and-reports-v1",
    "synthetic-ru-gk1009-1011-agency-subagency-termination-and-rules-v1",
    "synthetic-case-supply-1-agency-evidence",
    "synthetic-ru-gk128-136-objects-circulation-and-kinds-of-things-v1",
    "synthetic-ru-gk140-152-money-securities-and-intangible-benefits-v1",
    "synthetic-case-supply-1-objects-evidence",
    "synthetic-ru-gk17-30-legal-and-active-capacity-of-citizens-v1",
    "synthetic-ru-gk49-53-capacity-registration-and-bodies-of-legal-entities-v1",
    "synthetic-case-supply-1-persons-evidence",
    "synthetic-ru-gk190-193-term-definition-start-and-end-v1",
    "synthetic-ru-gk194-actions-on-the-last-day-of-a-term-v1",
    "synthetic-case-supply-1-terms-evidence",
    "synthetic-ru-gk402-404-attribution-of-liability-and-creditor-fault-v1",
    "synthetic-ru-gk405-406-delay-of-the-debtor-and-of-the-creditor-v1",
    "synthetic-case-supply-1-attribution-delay-evidence",
    "synthetic-ru-gk1651-legally-significant-messages-v1",
    "synthetic-ru-plenum25-63-67-message-delivery-risk-v1",
    "synthetic-case-supply-1-messages-evidence",
    "synthetic-ru-gk8601-8606-nominal-account-v1",
    "synthetic-ru-gk8607-86010-escrow-account-v1",
    "synthetic-ru-gk86011-86015-public-deposit-account-v1",
    "synthetic-case-supply-1-special-accounts-evidence",
    "synthetic-ru-gk9261-9268-escrow-deposit-v1",
    "synthetic-case-supply-1-escrow-deposit-evidence",
    "synthetic-ru-127fz-5-current-payments-v1",
    "synthetic-ru-127fz-63-observation-effects-v1",
    "synthetic-ru-127fz-134-creditor-ranking-v1",
    "synthetic-ru-127fz-135-first-rank-claims-v1",
    "synthetic-ru-127fz-138-secured-creditor-claims-v1",
    "synthetic-ru-127fz-61.1-contest-transactions-general-v1",
    "synthetic-ru-127fz-61.2-contest-suspicious-transaction-v1",
    "synthetic-ru-127fz-61.3-contest-preference-transaction-v1",
    "synthetic-ru-127fz-61.9-contest-standing-v1",
    "synthetic-case-supply-1-bankruptcy-claims-evidence",
    "synthetic-case-supply-1-bankruptcy-ranking-evidence",
    "synthetic-case-supply-1-bankruptcy-contest-evidence",
    "synthetic-case-supply-1-bankruptcy-setoff-evidence",
    "synthetic-ru-gk1811-1812-meeting-decision-effect-and-adoption-v1",
    "synthetic-ru-gk1813-1815-meeting-decision-invalidity-v1",
    "synthetic-case-supply-1-meeting-decisions-evidence",
    "synthetic-ru-gk153-157-transaction-concept-kinds-and-conditions-v1",
    "synthetic-ru-gk157-1-consent-to-a-transaction-v1",
    "synthetic-case-supply-1-transactions-evidence",
    "synthetic-ru-gk1-10-civil-principles-and-limits-of-exercise-v1",
    "synthetic-ru-gk12-16-1-protection-methods-damages-and-authority-liability-v1",
    "synthetic-case-supply-1-civil-principles-evidence",
    "synthetic-ru-gk209-234-ownership-content-acquisition-and-prescription-v1",
    "synthetic-ru-gk244-305-common-property-and-protection-of-rights-v1",
    "synthetic-ru-gk306-statutory-termination-compensation-v1",
    "synthetic-case-supply-1-property-rights-evidence",
    "synthetic-ru-gk182-184-representation-authority-and-limits-v1",
    "synthetic-ru-gk185-189-power-of-attorney-form-term-and-termination-v1",
    "synthetic-case-supply-1-representation-evidence",
    "synthetic-ru-gk1102-1105-unjust-enrichment-duty-and-return-v1",
    "synthetic-ru-gk1106-1109-unjust-enrichment-income-costs-and-exceptions-v1",
    "synthetic-case-supply-1-unjust-enrichment-evidence",
    "synthetic-ru-gk1099-1100-moral-harm-grounds-and-no-fault-cases-v1",
    "synthetic-ru-gk1101-moral-harm-form-and-amount-of-compensation-v1",
    "synthetic-case-supply-1-moral-harm-evidence",
    "synthetic-ru-gk1095-1096-product-defect-harm-and-liable-persons-v1",
    "synthetic-ru-gk1097-1098-product-liability-periods-and-exculpation-v1",
    "synthetic-case-supply-1-product-liability-evidence",
    "synthetic-ru-gk1084-1087-life-health-harm-scope-and-earnings-v1",
    "synthetic-ru-gk1088-1094-dependants-indexation-and-funeral-expenses-v1",
    "synthetic-case-supply-1-tort-life-health-evidence",
    "synthetic-ru-gk1064-1070-tort-general-grounds-and-liability-for-others-v1",
    "synthetic-ru-gk1073-1083-tort-high-risk-source-recourse-and-victim-fault-v1",
    "synthetic-case-supply-1-tort-general-evidence",
    "synthetic-ru-gk1062-judicial-protection-of-claims-from-games-and-betting-v1",
    "synthetic-ru-gk1063-organization-of-lotteries-and-payment-of-winnings-v1",
    "synthetic-case-supply-1-games-evidence",
    "synthetic-ru-gk1055-1056-public-promise-of-reward-and-revocation-v1",
    "synthetic-ru-gk1057-1061-public-contest-terms-award-and-works-v1",
    "synthetic-case-supply-1-public-promise-evidence",
    "synthetic-ru-gk1041-1046-partnership-concept-contributions-and-common-affairs-v1",
    "synthetic-ru-gk1047-1054-partnership-liability-profit-and-termination-v1",
    "synthetic-case-supply-1-partnership-evidence",
    "synthetic-ru-gk1027-1029-franchise-concept-form-and-subconcession-v1",
    "synthetic-ru-gk1030-1040-franchise-obligations-restrictions-and-termination-v1",
    "synthetic-case-supply-1-franchise-evidence",
    "synthetic-ru-gk1012-1019-trust-management-concept-terms-and-property-v1",
    "synthetic-ru-gk1020-1026-trust-management-duties-liability-and-termination-v1",
    "synthetic-case-supply-1-trust-management-evidence",
    "synthetic-ru-gk166-168-invalidity-framework-v1",
    "synthetic-ru-gk169-172-void-transactions-v1",
    "synthetic-ru-gk173-179-voidable-transactions-v1",
    "synthetic-ru-gk180-181-invalidity-effects-v1",
    "synthetic-ru-gk4311-entrepreneurial-estoppel-v1",
    "synthetic-ru-plenum25-invalidity-guidance-v1",
    "synthetic-case-supply-1-invalidity-evidence",
    "synthetic-ru-gk329-333-security-framework-v1",
    "synthetic-ru-gk334-360-pledge-retention-v1",
    "synthetic-ru-gk361-367-suretyship-v1",
    "synthetic-ru-gk368-379-independent-guarantee-v1",
    "synthetic-ru-gk380-3812-deposit-security-payment-v1",
    "synthetic-ru-plenum54-security-guidance-v1",
    "synthetic-ru-plenum23-pledge-guidance-v1",
    "synthetic-ru-plenum45-suretyship-guidance-v1",
    "synthetic-case-supply-1-security-evidence",
    "synthetic-ru-gk382-390-assignment-v1",
    "synthetic-ru-gk391-3923-debt-transfer-v1",
    "synthetic-ru-gk407-413-discharge-v1",
    "synthetic-ru-gk414-419-discharge-v1",
    "synthetic-ru-plenum54-party-change-guidance-v1",
    "synthetic-ru-plenum6-discharge-guidance-v1",
    "synthetic-case-supply-1-obligation-dynamics-evidence",
    "synthetic-ru-gk309-328-performance-v1",
    "synthetic-ru-gk393-4061-remedies-v1",
    "synthetic-ru-plenum54-performance-guidance-v1",
    "synthetic-ru-plenum7-remedies-guidance-v1",
    "synthetic-case-supply-1-performance-remedies-evidence",
    "synthetic-ru-gk454-464-sale-transfer-v1",
    "synthetic-ru-gk465-477-sale-conformity-v1",
    "synthetic-ru-gk478-491-sale-payment-v1",
    "synthetic-ru-vs-review2024-sale-quality-v1",
    "synthetic-case-supply-1-general-sale-evidence",
    "synthetic-ru-gk506-512-supply-framework-v1",
    "synthetic-ru-gk513-517-supply-acceptance-v1",
    "synthetic-ru-gk518-524-supply-remedies-v1",
    "synthetic-ru-plenum18-supply-guidance-v1",
    "synthetic-case-supply-1-special-supply-evidence",
    "synthetic-ru-gk450-453-termination-model-v1",
    "synthetic-ru-gk310-4501-unilateral-model-v1",
    "synthetic-ru-plenum54-unilateral-guidance-v1",
    "synthetic-ru-plenum18-pretrial-guidance-v1",
    "synthetic-case-supply-1-termination-evidence",
    "synthetic-ru-gk401-liability-model-v1",
    "synthetic-ru-gk333-penalty-model-v1",
    "synthetic-ru-plenum7-liability-guidance-v1",
    "synthetic-case-supply-1-liability-evidence",
)


def build_synthetic_supply_analysis_sources() -> list[LegalSource]:
    return [get_synthetic_contract_source(source_id) for source_id in SYNTHETIC_ANALYSIS_SOURCE_IDS]


def build_synthetic_supply_analysis_request() -> ReviewedContractAnalysisRequest:
    norm_source_id = "synthetic-ru-contract-supply-delivery-duty-v2"
    evidence_source_id = "synthetic-case-supply-1-reviewed-evidence"
    termination_values = {predicate: False for predicate in TerminationEvidencePredicate}
    termination_values[TerminationEvidencePredicate.CONTRACT_FORMED] = True
    termination_values[TerminationEvidencePredicate.ACCRUED_CLAIMS_EXIST] = True
    invalidity_values = {predicate: False for predicate in InvalidityEvidencePredicate}
    invalidity_values[InvalidityEvidencePredicate.TRANSACTION_CONCLUDED] = True
    security_values = {predicate: False for predicate in SecurityEvidencePredicate}
    security_values[SecurityEvidencePredicate.MAIN_OBLIGATION_EXISTS] = True
    security_values[SecurityEvidencePredicate.MAIN_OBLIGATION_BREACHED] = True
    security_values[SecurityEvidencePredicate.CREDITOR_GOOD_FAITH] = True
    dynamics_values = {predicate: False for predicate in ObligationDynamicsEvidencePredicate}
    dynamics_values[ObligationDynamicsEvidencePredicate.OBLIGATION_EXISTS] = True
    dynamics_values[ObligationDynamicsEvidencePredicate.OBLIGATION_BREACHED] = True
    dynamics_values[ObligationDynamicsEvidencePredicate.ACCRUED_CLAIMS_EXIST] = True
    dynamics_values[ObligationDynamicsEvidencePredicate.PERFORMANCE_RENDERED] = True
    dynamics_values[ObligationDynamicsEvidencePredicate.PERFORMANCE_ACCEPTED_AS_PROPER] = True
    dynamics_values[ObligationDynamicsEvidencePredicate.CREDITOR_ISSUED_RECEIPT] = True
    performance_remedies_values = {
        predicate: False for predicate in PerformanceRemediesEvidencePredicate
    }
    performance_remedies_values[PerformanceRemediesEvidencePredicate.OBLIGATION_EXISTS] = True
    performance_remedies_values[PerformanceRemediesEvidencePredicate.BREACH_ESTABLISHED] = True
    performance_remedies_values[PerformanceRemediesEvidencePredicate.PERFORMANCE_TENDERED] = True
    performance_remedies_values[PerformanceRemediesEvidencePredicate.SUBJECT_CONFORMS] = True
    performance_remedies_values[PerformanceRemediesEvidencePredicate.QUALITY_QUANTITY_CONFORM] = (
        True
    )
    performance_remedies_values[
        PerformanceRemediesEvidencePredicate.PERFORMANCE_AT_PROPER_PLACE
    ] = True
    performance_remedies_values[
        PerformanceRemediesEvidencePredicate.PERFORMANCE_TO_PROPER_RECIPIENT
    ] = True
    performance_remedies_values[PerformanceRemediesEvidencePredicate.CREDITOR_MITIGATION_TAKEN] = (
        True
    )
    performance_remedies_values[PerformanceRemediesEvidencePredicate.DEBTOR_DELAY] = True
    sale_values = {predicate: False for predicate in SaleEvidencePredicate}
    for predicate in (
        SaleEvidencePredicate.CONTRACT_CONCLUDED,
        SaleEvidencePredicate.SELLER_TRANSFER_OWNERSHIP_DUTY,
        SaleEvidencePredicate.BUYER_ACCEPTANCE_DUTY,
        SaleEvidencePredicate.BUYER_PAYMENT_DUTY,
        SaleEvidencePredicate.GOODS_EXISTING_OR_FUTURE,
        SaleEvidencePredicate.GOODS_NAME_AGREED,
        SaleEvidencePredicate.QUANTITY_DETERMINABLE,
        SaleEvidencePredicate.TRANSFER_TERM_DUE,
        SaleEvidencePredicate.DELIVERY_LATE,
        SaleEvidencePredicate.DELIVERY_OBLIGATION,
        SaleEvidencePredicate.GOODS_DELIVERED_TO_BUYER,
        SaleEvidencePredicate.GOODS_TRANSFER_COMPLETED,
        SaleEvidencePredicate.BUYER_RECEIVED_GOODS,
        SaleEvidencePredicate.INSPECTION_REQUIRED,
        SaleEvidencePredicate.INSPECTION_TIMELY,
        SaleEvidencePredicate.INSPECTION_METHOD_COMPLIED,
        SaleEvidencePredicate.BUYER_ACCEPTANCE_COMPLETED,
        SaleEvidencePredicate.PRICE_AGREED,
    ):
        sale_values[predicate] = True
    supply_values = {predicate: False for predicate in SupplyEvidencePredicate}
    supply_values[SupplyEvidencePredicate.CONTRACT_CONCLUDED] = True
    supply_values[SupplyEvidencePredicate.SUPPLIER_BUSINESS] = True
    supply_values[SupplyEvidencePredicate.SUPPLIER_PRODUCED_OR_PROCURED_GOODS] = True
    supply_values[SupplyEvidencePredicate.GOODS_NONPERSONAL_USE] = True
    supply_values[SupplyEvidencePredicate.TRANSFER_TERM_DEFINED] = True
    supply_values[SupplyEvidencePredicate.DELIVERY_COMPLETED] = True
    supply_values[SupplyEvidencePredicate.DELIVERY_LATE] = True
    supply_values[SupplyEvidencePredicate.BUYER_RECEIVED_GOODS] = True
    supply_values[SupplyEvidencePredicate.INSPECTION_TIMELY] = True
    return ReviewedContractAnalysisRequest(
        id="analysis-request-case-supply-1-v0",
        case_id="case-supply-1",
        reviewed_norm=ReviewedNormJSON(
            id="norm-supply-delivery-duty-v0",
            source_id=norm_source_id,
            subjects=["поставщик", "покупатель"],
            actions=["поставить товар в согласованный срок"],
            conditions=[
                NormCondition(
                    id="condition-supply-relation",
                    text="Между поставщиком и покупателем существуют отношения поставки.",
                ),
                NormCondition(
                    id="condition-agreed-date",
                    text="Стороны согласовали срок поставки.",
                ),
            ],
            exceptions=[
                NormCondition(
                    id="exception-valid-excuse",
                    text="Применяется договорное или предусмотренное законом основание освобождения.",
                )
            ],
            consequences=[
                NormConsequence(
                    id="consequence-breach-risk",
                    text="Пропуск согласованного срока создает вопрос о нарушении обязательства.",
                )
            ],
            temporal_notes=["Оценить исполнение относительно согласованного срока поставки."],
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-norm-reviewer",
        ),
        case_evidence=ReviewedCaseEvidence(
            id="reviewed-case-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                CaseEvidenceAssertion(
                    id=f"evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=(evidence_source_id,),
                )
                for predicate, value in (
                    (ContractEvidencePredicate.DUTY_EXISTS, True),
                    (ContractEvidencePredicate.VALID_EXCEPTION_APPLIES, False),
                    (ContractEvidencePredicate.PERFORMANCE_COMPLETED, True),
                    (ContractEvidencePredicate.PERFORMANCE_NONCONFORMING, False),
                    (ContractEvidencePredicate.PAYMENT_DUTY_EXISTS, False),
                    (ContractEvidencePredicate.PAYMENT_DUE, False),
                    (ContractEvidencePredicate.PAYMENT_MISSED, False),
                    (ContractEvidencePredicate.PAYMENT_DEFENSE_APPLIES, False),
                    (ContractEvidencePredicate.LOSS_CLAIMED, False),
                    (ContractEvidencePredicate.CAUSATION_ESTABLISHED, False),
                    (ContractEvidencePredicate.REMEDY_REQUESTED, False),
                    (ContractEvidencePredicate.LIMITATION_PERIOD_EXPIRED, False),
                )
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-case-evidence-reviewer",
        ),
        temporal_evidence=ReviewedTemporalEvidence(
            id="reviewed-temporal-evidence-supply-1-v0",
            case_id="case-supply-1",
            agreed_due_date="2026-01-15",
            actual_performance_date="2026-01-20",
            evaluation_date="2026-01-21",
            source_refs=(
                "synthetic-ru-contract-supply-delivery-term",
                evidence_source_id,
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-temporal-reviewer",
        ),
        authority_input=ReviewedAuthorityInput(
            id="reviewed-authority-input-supply-1-v0",
            candidate_source_ids=(
                "synthetic-ru-contract-supply-delivery-duty-v1",
                norm_source_id,
            ),
            evaluation_date="2026-01-21",
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-authority-reviewer",
        ),
        formation_evidence=ReviewedFormationEvidence(
            id="reviewed-formation-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                FormationEvidenceAssertion(
                    id=f"formation-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-formation-evidence",),
                )
                for predicate, value in (
                    (FormationEvidencePredicate.PROPOSAL_MADE, True),
                    (FormationEvidencePredicate.PROPOSAL_ADDRESSED_TO_COUNTERPARTY, True),
                    (FormationEvidencePredicate.INTENT_TO_BE_BOUND, True),
                    (FormationEvidencePredicate.SUBJECT_MATTER_DEFINED_IN_OFFER, True),
                    (FormationEvidencePredicate.STATUTORY_ESSENTIAL_TERMS_DEFINED_IN_OFFER, True),
                    (
                        FormationEvidencePredicate.PARTY_DECLARED_ESSENTIAL_TERMS_DEFINED_IN_OFFER,
                        True,
                    ),
                    (FormationEvidencePredicate.REQUIRED_FORM_OBSERVED, True),
                    (FormationEvidencePredicate.ACCEPTANCE_RECEIVED, False),
                    (FormationEvidencePredicate.ACCEPTANCE_FULL_AND_UNCONDITIONAL, False),
                    (FormationEvidencePredicate.ACCEPTANCE_WITHIN_PERIOD, True),
                    (FormationEvidencePredicate.ACCEPTANCE_BY_CONDUCT, True),
                    (FormationEvidencePredicate.PERFORMANCE_CONDUCT_STARTED_IN_TIME, True),
                    (FormationEvidencePredicate.SILENCE_ONLY, False),
                    (FormationEvidencePredicate.SILENCE_ACCEPTANCE_BASIS_EXISTS, False),
                    (FormationEvidencePredicate.ACCEPTANCE_ON_OTHER_TERMS, False),
                    (FormationEvidencePredicate.PERFORMANCE_ACCEPTED_WITHOUT_OBJECTION, True),
                    (FormationEvidencePredicate.BAD_FAITH_NON_CONCLUSION_OBJECTION, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk432-contract-formation-model-v1",
                "synthetic-ru-gk435-offer-model-v1",
                "synthetic-ru-gk438-443-acceptance-model-v1",
                "synthetic-ru-plenum49-formation-guidance-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-formation-reviewer",
        ),
        temporal_effect_evidence=ReviewedTemporalEffectEvidence(
            id="reviewed-temporal-effect-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                TemporalEffectEvidenceAssertion(
                    id=f"temporal-effect-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-temporal-effect-evidence",),
                )
                for predicate, value in (
                    (TemporalEffectEvidencePredicate.ACCEPTANCE_RECEIVED_BY_OFFEROR, True),
                    (TemporalEffectEvidencePredicate.CONTRACT_REQUIRES_PROPERTY_DELIVERY, False),
                    (TemporalEffectEvidencePredicate.PROPERTY_DELIVERED, False),
                    (TemporalEffectEvidencePredicate.CONTRACT_REQUIRES_STATE_REGISTRATION, False),
                    (TemporalEffectEvidencePredicate.STATE_REGISTRATION_COMPLETED, False),
                    (TemporalEffectEvidencePredicate.EFFECTIVENESS_DEFERRED_BY_TERMS, False),
                    (TemporalEffectEvidencePredicate.DEFERRED_EFFECTIVENESS_CONDITION_MET, False),
                    (TemporalEffectEvidencePredicate.RETROACTIVE_APPLICATION_AGREED, False),
                    (TemporalEffectEvidencePredicate.PRIOR_RELATIONS_EXIST, False),
                    (TemporalEffectEvidencePredicate.TERM_END_DEFINED, True),
                    (TemporalEffectEvidencePredicate.TERM_END_REACHED, True),
                    (TemporalEffectEvidencePredicate.TERMS_PROVIDE_OBLIGATIONS_END_ON_TERM, False),
                    (TemporalEffectEvidencePredicate.PERFORMANCE_COMPLETED, True),
                    (TemporalEffectEvidencePredicate.BREACH_COMMITTED_DURING_TERM, True),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk425-contract-effect-model-v1",
                "synthetic-ru-gk433-conclusion-moment-model-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-temporal-effect-reviewer",
        ),
        limitation_evidence=ReviewedLimitationEvidence(
            id="reviewed-limitation-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                LimitationEvidenceAssertion(
                    id=f"limitation-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-limitation-evidence",),
                )
                for predicate, value in (
                    (LimitationEvidencePredicate.CLAIM_SUBJECT_TO_LIMITATION, True),
                    (LimitationEvidencePredicate.RIGHT_VIOLATION_AND_DEFENDANT_KNOWN, True),
                    (LimitationEvidencePredicate.FIXED_PERFORMANCE_TERM_EXPIRED, False),
                    (LimitationEvidencePredicate.GENERAL_THREE_YEAR_TERM_ELAPSED, False),
                    (LimitationEvidencePredicate.SPECIAL_TERM_APPLIES, False),
                    (LimitationEvidencePredicate.SPECIAL_TERM_ELAPSED, False),
                    (LimitationEvidencePredicate.OBJECTIVE_TEN_YEAR_LIMIT_EXCEEDED, False),
                    (LimitationEvidencePredicate.SUSPENSION_GROUND_IN_FINAL_SIX_MONTHS, False),
                    (LimitationEvidencePredicate.DEBTOR_ACKNOWLEDGED_DEBT, False),
                    (LimitationEvidencePredicate.JUDICIAL_PROTECTION_PERIOD_ONGOING, False),
                    (
                        LimitationEvidencePredicate.LIMITATION_PLEADED_BY_PARTY_BEFORE_JUDGMENT,
                        False,
                    ),
                    (LimitationEvidencePredicate.CLAIMANT_IS_INDIVIDUAL_WITH_VALID_EXCUSE, False),
                    (LimitationEvidencePredicate.IS_ADDITIONAL_CLAIM, False),
                    (LimitationEvidencePredicate.MAIN_CLAIM_TIME_BARRED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk195-200-limitation-framework-v1",
                "synthetic-ru-gk202-208-limitation-effects-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-limitation-reviewer",
        ),
        interpretation_evidence=ReviewedInterpretationEvidence(
            id="reviewed-interpretation-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                InterpretationEvidenceAssertion(
                    id=f"interpretation-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-interpretation-evidence",),
                )
                for predicate, value in (
                    (InterpretationEvidencePredicate.DISPUTED_TERM_PRESENT, True),
                    (InterpretationEvidencePredicate.LITERAL_MEANING_CLEAR, True),
                    (InterpretationEvidencePredicate.CONSISTENT_WITH_OTHER_TERMS, True),
                    (InterpretationEvidencePredicate.CONSISTENT_WITH_WHOLE_CONTRACT, True),
                    (InterpretationEvidencePredicate.COMMON_INTENT_ESTABLISHED, False),
                    (InterpretationEvidencePredicate.PURPOSE_CONSIDERED, False),
                    (InterpretationEvidencePredicate.PRELIMINARY_NEGOTIATIONS_CONSIDERED, False),
                    (InterpretationEvidencePredicate.ESTABLISHED_PRACTICE_CONSIDERED, False),
                    (InterpretationEvidencePredicate.USAGES_CONSIDERED, False),
                    (InterpretationEvidencePredicate.SUBSEQUENT_CONDUCT_CONSIDERED, False),
                    (InterpretationEvidencePredicate.TERM_DRAFTED_BY_ONE_PARTY, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk431-interpretation-model-v1",
                "synthetic-ru-gk431-common-intent-model-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-interpretation-reviewer",
        ),
        form_evidence=ReviewedFormEvidence(
            id="reviewed-form-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                FormEvidenceAssertion(
                    id=f"form-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-form-evidence",),
                )
                for predicate, value in (
                    (FormEvidencePredicate.ORAL_FORM_PERMITTED, False),
                    (FormEvidencePredicate.SIMPLE_WRITTEN_FORM_REQUIRED, True),
                    (FormEvidencePredicate.NOTARIAL_FORM_REQUIRED, False),
                    (FormEvidencePredicate.SIMPLE_WRITTEN_FORM_OBSERVED, True),
                    (FormEvidencePredicate.DOCUMENT_SIGNED_BY_PARTIES, True),
                    (FormEvidencePredicate.EXCHANGE_OF_DOCUMENTS, False),
                    (FormEvidencePredicate.ELECTRONIC_SIGNATURE_VALID, False),
                    (FormEvidencePredicate.WRITTEN_OFFER_MADE, False),
                    (FormEvidencePredicate.OFFER_TERMS_PERFORMED_AS_ACCEPTANCE, False),
                    (FormEvidencePredicate.NOTARIAL_FORM_OBSERVED, False),
                    (
                        FormEvidencePredicate.WRITTEN_NONCOMPLIANCE_INVALIDATES_BY_LAW_OR_AGREEMENT,
                        False,
                    ),
                    (FormEvidencePredicate.PERFORMANCE_OR_WRITTEN_PROOF_AVAILABLE, True),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk158-165-form-framework-v1",
                "synthetic-ru-gk160-434-written-form-model-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-form-reviewer",
        ),
        preliminary_evidence=ReviewedPreliminaryEvidence(
            id="reviewed-preliminary-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                PreliminaryEvidenceAssertion(
                    id=f"preliminary-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-preliminary-evidence",),
                )
                for predicate, value in (
                    (PreliminaryEvidencePredicate.PRELIMINARY_CONTRACT_CONCLUDED, True),
                    (PreliminaryEvidencePredicate.FORM_REQUIREMENT_OBSERVED, True),
                    (PreliminaryEvidencePredicate.MAIN_CONTRACT_SUBJECT_DEFINED, True),
                    (PreliminaryEvidencePredicate.DISPUTED_TERMS_AGREED, True),
                    (PreliminaryEvidencePredicate.WITHIN_CONCLUSION_TERM, True),
                    (
                        PreliminaryEvidencePredicate.MAIN_CONTRACT_CONCLUDED_OR_PROPOSAL_MADE,
                        False,
                    ),
                    (PreliminaryEvidencePredicate.PARTY_EVADES_CONCLUSION, False),
                    (PreliminaryEvidencePredicate.DEMAND_TO_CONCLUDE_MADE, False),
                    (PreliminaryEvidencePredicate.DEMAND_WITHIN_SIX_MONTHS, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk429-preliminary-framework-v1",
                "synthetic-ru-gk429-445-preliminary-compulsion-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-preliminary-reviewer",
        ),
        third_party_evidence=ReviewedThirdPartyEvidence(
            id="reviewed-third-party-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ThirdPartyEvidenceAssertion(
                    id=f"third-party-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-third-party-evidence",),
                )
                for predicate, value in (
                    (ThirdPartyEvidencePredicate.THIRD_PARTY_BENEFICIARY_CONTRACT, True),
                    (ThirdPartyEvidencePredicate.THIRD_PARTY_IDENTIFIED_OR_DETERMINABLE, True),
                    (ThirdPartyEvidencePredicate.THIRD_PARTY_GRANTED_RIGHT_TO_DEMAND, True),
                    (ThirdPartyEvidencePredicate.THIRD_PARTY_INTENT_EXPRESSED, False),
                    (
                        ThirdPartyEvidencePredicate.STATUTE_OR_CONTRACT_ALLOWS_CHANGE_WITHOUT_CONSENT,
                        False,
                    ),
                    (
                        ThirdPartyEvidencePredicate.PARTIES_SEEK_MODIFICATION_OR_TERMINATION,
                        False,
                    ),
                    (ThirdPartyEvidencePredicate.THIRD_PARTY_CONSENTS_TO_CHANGE, False),
                    (ThirdPartyEvidencePredicate.THIRD_PARTY_WAIVED_RIGHT, False),
                    (ThirdPartyEvidencePredicate.CREDITOR_RECLAIMS_RIGHT, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk430-third-party-framework-v1",
                "synthetic-ru-gk430-third-party-change-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-third-party-reviewer",
        ),
        public_contract_evidence=ReviewedPublicContractEvidence(
            id="reviewed-public-contract-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                PublicContractEvidenceAssertion(
                    id=f"public-contract-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-public-contract-evidence",),
                )
                for predicate, value in (
                    (PublicContractEvidencePredicate.PUBLIC_CONTRACT_REGIME, True),
                    (PublicContractEvidencePredicate.COUNTERPARTY_REQUESTED_CONTRACT, True),
                    (PublicContractEvidencePredicate.PERFORMANCE_POSSIBLE, True),
                    (PublicContractEvidencePredicate.REFUSAL_WITHOUT_LAWFUL_GROUND, False),
                    (
                        PublicContractEvidencePredicate.PREFERENCE_GIVEN_WITHOUT_LEGAL_BASIS,
                        False,
                    ),
                    (PublicContractEvidencePredicate.LAWFUL_DIFFERENTIATION, False),
                    (PublicContractEvidencePredicate.TERMS_UNIFORM_FOR_CATEGORY, True),
                    (PublicContractEvidencePredicate.COMPULSION_DEMANDED, False),
                    (PublicContractEvidencePredicate.TERMS_CONFLICT_WITH_PUBLIC_RULES, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk426-public-contract-framework-v1",
                "synthetic-ru-gk426-public-contract-terms-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-public-contract-reviewer",
        ),
        adhesion_evidence=ReviewedAdhesionEvidence(
            id="reviewed-adhesion-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                AdhesionEvidenceAssertion(
                    id=f"adhesion-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-adhesion-evidence",),
                )
                for predicate, value in (
                    (AdhesionEvidencePredicate.ADHESION_CONTRACT, True),
                    (AdhesionEvidencePredicate.UNEQUAL_BARGAINING_POWER, False),
                    (AdhesionEvidencePredicate.TERMS_INDIVIDUALLY_NEGOTIATED, False),
                    (AdhesionEvidencePredicate.DEPRIVES_USUAL_RIGHTS, False),
                    (
                        AdhesionEvidencePredicate.EXCLUDES_OR_LIMITS_OTHER_PARTY_LIABILITY,
                        False,
                    ),
                    (AdhesionEvidencePredicate.MANIFESTLY_ONEROUS_TERMS, False),
                    (AdhesionEvidencePredicate.ADHERING_PARTY_BUSINESS_ACTOR, False),
                    (AdhesionEvidencePredicate.ADHERING_PARTY_KNEW_TERMS, False),
                    (AdhesionEvidencePredicate.MODIFICATION_OR_TERMINATION_DEMANDED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk428-adhesion-framework-v1",
                "synthetic-ru-gk428-adhesion-relief-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-adhesion-reviewer",
        ),
        representations_evidence=ReviewedRepresentationsEvidence(
            id="reviewed-representations-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                RepresentationsEvidenceAssertion(
                    id=f"representations-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-representations-evidence",),
                )
                for predicate, value in (
                    (RepresentationsEvidencePredicate.REPRESENTATION_GIVEN, True),
                    (RepresentationsEvidencePredicate.REPRESENTATION_MATERIAL, True),
                    (RepresentationsEvidencePredicate.REPRESENTATION_FALSE, False),
                    (RepresentationsEvidencePredicate.RELIANCE_BY_OTHER_PARTY, True),
                    (
                        RepresentationsEvidencePredicate.GIVEN_IN_BUSINESS_OR_CORPORATE_CONTEXT,
                        True,
                    ),
                    (
                        RepresentationsEvidencePredicate.REPRESENTOR_KNEW_OR_SHOULD_HAVE_KNOWN,
                        False,
                    ),
                    (RepresentationsEvidencePredicate.DAMAGES_OR_PENALTY_CLAIMED, False),
                    (RepresentationsEvidencePredicate.REPRESENTATION_SIGNIFICANT, False),
                    (
                        RepresentationsEvidencePredicate.DECEPTION_BY_FALSE_REPRESENTATION,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk431-2-representations-framework-v1",
                "synthetic-ru-gk431-2-representations-remedies-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-representations-reviewer",
        ),
        precontractual_evidence=ReviewedPrecontractualEvidence(
            id="reviewed-precontractual-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                PrecontractualEvidenceAssertion(
                    id=f"precontractual-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-precontractual-evidence",),
                )
                for predicate, value in (
                    (PrecontractualEvidencePredicate.NEGOTIATIONS_ENTERED, True),
                    (
                        PrecontractualEvidencePredicate.INCOMPLETE_OR_FALSE_INFORMATION_PROVIDED,
                        False,
                    ),
                    (PrecontractualEvidencePredicate.ABRUPT_UNJUSTIFIED_BREAKOFF, False),
                    (
                        PrecontractualEvidencePredicate.COUNTERPARTY_COULD_NOT_REASONABLY_EXPECT_BREAKOFF,
                        False,
                    ),
                    (PrecontractualEvidencePredicate.CONFIDENTIAL_INFORMATION_RECEIVED, False),
                    (PrecontractualEvidencePredicate.CONFIDENTIAL_INFORMATION_MISUSED, False),
                    (PrecontractualEvidencePredicate.LOSSES_INCURRED, False),
                    (PrecontractualEvidencePredicate.DAMAGES_CLAIMED, False),
                    (
                        PrecontractualEvidencePredicate.LIABILITY_LIMITATION_AGREEMENT_PRESENT,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk434-1-precontractual-framework-v1",
                "synthetic-ru-gk434-1-precontractual-remedies-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-precontractual-reviewer",
        ),
        option_evidence=ReviewedOptionEvidence(
            id="reviewed-option-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                OptionEvidenceAssertion(
                    id=f"option-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-option-evidence",),
                )
                for predicate, value in (
                    (OptionEvidencePredicate.OPTION_TO_CONCLUDE_GRANTED, True),
                    (OptionEvidencePredicate.OPTION_ESSENTIAL_TERMS_DEFINED, True),
                    (OptionEvidencePredicate.OPTION_CONSIDERATION_VALID, True),
                    (OptionEvidencePredicate.OPTION_ACCEPTANCE_WITHIN_TERM, True),
                    (OptionEvidencePredicate.OPTION_RIGHT_ASSIGNED, False),
                    (OptionEvidencePredicate.ASSIGNMENT_PROHIBITED, False),
                    (OptionEvidencePredicate.OPTION_CONTRACT_CONCLUDED, False),
                    (OptionEvidencePredicate.OPTION_CONTRACT_DEMAND_WITHIN_TERM, False),
                    (OptionEvidencePredicate.OPTION_CONTRACT_PAYMENT_MADE, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk429-2-option-framework-v1",
                "synthetic-ru-gk429-3-option-contract-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-option-reviewer",
        ),
        framework_evidence=ReviewedFrameworkEvidence(
            id="reviewed-framework-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                FrameworkEvidenceAssertion(
                    id=f"framework-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-framework-evidence",),
                )
                for predicate, value in (
                    (FrameworkEvidencePredicate.FRAMEWORK_AGREEMENT_CONCLUDED, True),
                    (FrameworkEvidencePredicate.FRAMEWORK_GENERAL_CONDITIONS_DEFINED, True),
                    (FrameworkEvidencePredicate.SPECIFYING_AGREEMENT_CONCLUDED, True),
                    (FrameworkEvidencePredicate.SPECIFYING_AGREEMENT_OVERRIDES, False),
                    (FrameworkEvidencePredicate.SUBSCRIPTION_AGREEMENT_CONCLUDED, False),
                    (FrameworkEvidencePredicate.SUBSCRIPTION_PAYMENT_AGREED, False),
                    (FrameworkEvidencePredicate.SUBSCRIBER_DEMANDED_PERFORMANCE, False),
                    (FrameworkEvidencePredicate.SUBSCRIPTION_PAYMENT_EXCUSED_BY_CONTRACT, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk429-1-framework-agreement-v1",
                "synthetic-ru-gk429-4-subscription-agreement-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-framework-reviewer",
        ),
        freedom_evidence=ReviewedFreedomEvidence(
            id="reviewed-freedom-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                FreedomEvidenceAssertion(
                    id=f"freedom-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-freedom-evidence",),
                )
                for predicate, value in (
                    (FreedomEvidencePredicate.CONTRACT_CONCLUSION_COMPELLED_BY_LAW, False),
                    (FreedomEvidencePredicate.CONTRACT_TYPE_UNNAMED, False),
                    (FreedomEvidencePredicate.MIXED_CONTRACT_ELEMENTS, False),
                    (FreedomEvidencePredicate.TERMS_PRESCRIBED_BY_MANDATORY_NORM, False),
                    (FreedomEvidencePredicate.CONTRACT_CONFORMS_MANDATORY_RULES, True),
                    (FreedomEvidencePredicate.NEW_MANDATORY_LAW_AFTER_CONCLUSION, False),
                    (FreedomEvidencePredicate.NEW_LAW_GIVEN_RETROACTIVE_EFFECT, False),
                    (FreedomEvidencePredicate.CONTRACT_GRATUITOUS_BY_NATURE, False),
                    (FreedomEvidencePredicate.PRICE_AGREED_BY_PARTIES, True),
                    (FreedomEvidencePredicate.REGULATED_PRICE_MANDATED, False),
                    (FreedomEvidencePredicate.COMPARABLE_PRICE_AVAILABLE, False),
                    (FreedomEvidencePredicate.TERM_NOT_DETERMINED_BY_PARTIES, False),
                    (FreedomEvidencePredicate.TERM_NOT_COVERED_BY_DISPOSITIVE_NORM, False),
                    (FreedomEvidencePredicate.STANDARD_TERMS_ASSERTED, False),
                    (
                        FreedomEvidencePredicate.STANDARD_TERMS_PUBLISHED_FOR_CONTRACT_TYPE,
                        False,
                    ),
                    (FreedomEvidencePredicate.CONTRACT_REFERS_TO_STANDARD_TERMS, False),
                    (
                        FreedomEvidencePredicate.STANDARD_TERMS_MEET_CUSTOM_REQUIREMENTS,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk421-422-freedom-of-contract-v1",
                "synthetic-ru-gk423-424-onerousness-and-price-v1",
                "synthetic-ru-gk427-standard-terms-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-freedom-reviewer",
        ),
        procedure_evidence=ReviewedProcedureEvidence(
            id="reviewed-procedure-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ProcedureEvidenceAssertion(
                    id=f"procedure-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-procedure-evidence",),
                )
                for predicate, value in (
                    (ProcedureEvidencePredicate.CONCLUSION_MANDATORY_FOR_PARTY, False),
                    (ProcedureEvidencePredicate.OFFER_OR_DRAFT_SENT, False),
                    (ProcedureEvidencePredicate.OBLIGED_PARTY_EVADED, False),
                    (ProcedureEvidencePredicate.PRECONTRACTUAL_DISPUTE_SUBMITTED_TO_COURT, False),
                    (ProcedureEvidencePredicate.CONTRACT_CONCLUDED_AT_AUCTION, False),
                    (ProcedureEvidencePredicate.AUCTION_NOTICE_TIMELY, False),
                    (ProcedureEvidencePredicate.WINNER_DETERMINED, False),
                    (ProcedureEvidencePredicate.RESULTS_PROTOCOL_SIGNED, False),
                    (ProcedureEvidencePredicate.WINNER_EVADED_SIGNING, False),
                    (ProcedureEvidencePredicate.AUCTION_RULES_VIOLATED, False),
                    (ProcedureEvidencePredicate.INTERESTED_PARTY_CHALLENGE, False),
                    (ProcedureEvidencePredicate.PUBLIC_AUCTION_ASSERTED, False),
                    (ProcedureEvidencePredicate.PUBLIC_AUCTION_ORGANISER_AUTHORISED, False),
                    (ProcedureEvidencePredicate.PUBLIC_AUCTION_NOTICE_NAMES_OWNER, False),
                    (ProcedureEvidencePredicate.BARRED_PERSON_PARTICIPATED, False),
                    (ProcedureEvidencePredicate.PUBLIC_AUCTION_PROTOCOL_LISTS_BIDS, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk445-446-mandatory-conclusion-v1",
                "synthetic-ru-gk447-449-auction-v1",
                "synthetic-ru-gk449-1-public-auction-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-procedure-reviewer",
        ),
        general_obligations_evidence=ReviewedGeneralObligationsEvidence(
            id="reviewed-general-obligations-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                GeneralObligationsEvidenceAssertion(
                    id=f"general-obligations-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-general-obligations-evidence",),
                )
                for predicate, value in (
                    (GeneralObligationsEvidencePredicate.OBLIGATION_ESTABLISHED, True),
                    (GeneralObligationsEvidencePredicate.GOOD_FAITH_OBSERVED, True),
                    (
                        GeneralObligationsEvidencePredicate.OBLIGATION_BINDS_THIRD_PARTY_CLAIMED,
                        False,
                    ),
                    (GeneralObligationsEvidencePredicate.ALTERNATIVE_OBLIGATION, False),
                    (GeneralObligationsEvidencePredicate.CHOICE_MADE_IN_ALTERNATIVE, False),
                    (GeneralObligationsEvidencePredicate.FACULTATIVE_OBLIGATION, False),
                    (GeneralObligationsEvidencePredicate.FACULTATIVE_SUBSTITUTION_PROVIDED, False),
                    (GeneralObligationsEvidencePredicate.SPECIFIC_PERFORMANCE_DEMANDED, True),
                    (GeneralObligationsEvidencePredicate.PERFORMANCE_UNIQUELY_PERSONAL, False),
                    (GeneralObligationsEvidencePredicate.JUDICIAL_ACT_NON_COMPLIANCE, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk307-308-obligation-concept-v1",
                "synthetic-ru-gk3081-3083-obligation-types-and-protection-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-general-obligations-reviewer",
        ),
        retail_sale_evidence=ReviewedRetailSaleEvidence(
            id="reviewed-retail-sale-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                RetailSaleEvidenceAssertion(
                    id=f"retail-sale-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-retail-sale-evidence",),
                )
                for predicate, value in (
                    (RetailSaleEvidencePredicate.RETAIL_CONSUMER_SALE, False),
                    (RetailSaleEvidencePredicate.PUBLIC_OFFER_MADE, False),
                    (RetailSaleEvidencePredicate.RECEIPT_OR_CONFIRMATION_ISSUED, False),
                    (RetailSaleEvidencePredicate.REQUIRED_INFORMATION_PROVIDED, False),
                    (RetailSaleEvidencePredicate.GOODS_DEFECTIVE, False),
                    (RetailSaleEvidencePredicate.BUYER_QUALITY_REMEDY_DEMANDED, False),
                    (RetailSaleEvidencePredicate.QUALITY_EXCHANGE_DEMANDED_IN_TERM, False),
                    (RetailSaleEvidencePredicate.GOODS_UNUSED_AND_DOCUMENTED, False),
                    (RetailSaleEvidencePredicate.SIMILAR_GOODS_AVAILABLE, False),
                    (RetailSaleEvidencePredicate.PRICE_INCREASED_BEFORE_REPLACEMENT, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk492-495-retail-sale-concept-v1",
                "synthetic-ru-gk502-504-retail-exchange-and-quality-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-retail-sale-reviewer",
        ),
        state_supply_evidence=ReviewedStateSupplyEvidence(
            id="reviewed-state-supply-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                StateSupplyEvidenceAssertion(
                    id=f"state-supply-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-state-supply-evidence",),
                )
                for predicate, value in (
                    (StateSupplyEvidencePredicate.STATE_CONTRACT_CONCLUDED, False),
                    (StateSupplyEvidencePredicate.ORDER_PLACED_BY_PROCEDURE, False),
                    (StateSupplyEvidencePredicate.CONCLUSION_MANDATORY_FOR_SUPPLIER, False),
                    (StateSupplyEvidencePredicate.CONTRACT_CAUSES_SUPPLIER_LOSS, False),
                    (StateSupplyEvidencePredicate.SUPPLIER_EVADED_CONCLUSION, False),
                    (StateSupplyEvidencePredicate.ATTACHMENT_NOTICE_ISSUED, False),
                    (StateSupplyEvidencePredicate.BUYER_REFUSED_GOODS, False),
                    (StateSupplyEvidencePredicate.GOODS_DELIVERED_TO_BUYER, False),
                    (StateSupplyEvidencePredicate.BUYER_PAID_AT_CONTRACT_PRICE, False),
                    (StateSupplyEvidencePredicate.STATE_CUSTOMER_REFUSED_GOODS, False),
                    (StateSupplyEvidencePredicate.SUPPLIER_INCURRED_LOSSES, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk525-528-state-contract-v1",
                "synthetic-ru-gk529-534-state-supply-performance-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-state-supply-reviewer",
        ),
        contractation_evidence=ReviewedContractationEvidence(
            id="reviewed-contractation-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ContractationEvidenceAssertion(
                    id=f"contractation-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-contractation-evidence",),
                )
                for predicate, value in (
                    (ContractationEvidencePredicate.AGRICULTURAL_PRODUCER_CONTRACT, False),
                    (ContractationEvidencePredicate.GOODS_ARE_OWN_GROWN_PRODUCE, False),
                    (
                        ContractationEvidencePredicate.PROCURER_TOOK_DELIVERY_AT_PRODUCER_LOCATION,
                        False,
                    ),
                    (ContractationEvidencePredicate.GOODS_CONFORM_AND_TIMELY, False),
                    (ContractationEvidencePredicate.PROCURER_REFUSED_CONFORMING_GOODS, False),
                    (ContractationEvidencePredicate.PROCESSING_WASTE_RETURN_AGREED, False),
                    (ContractationEvidencePredicate.PROCURER_RETURNED_WASTE, False),
                    (
                        ContractationEvidencePredicate.PRODUCER_DELIVERED_QUANTITY_AND_ASSORTMENT,
                        False,
                    ),
                    (ContractationEvidencePredicate.PRODUCER_BREACHED, False),
                    (ContractationEvidencePredicate.PRODUCER_AT_FAULT, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk535-536-contractation-concept-v1",
                "synthetic-ru-gk537-538-contractation-duties-and-liability-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-contractation-reviewer",
        ),
        energy_supply_evidence=ReviewedEnergySupplyEvidence(
            id="reviewed-energy-supply-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                EnergySupplyEvidenceAssertion(
                    id=f"energy-supply-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-energy-supply-evidence",),
                )
                for predicate, value in (
                    (
                        EnergySupplyEvidencePredicate.ENERGY_SUPPLIED_THROUGH_ATTACHED_NETWORK,
                        False,
                    ),
                    (
                        EnergySupplyEvidencePredicate.SUBSCRIBER_HAS_COMPLIANT_RECEIVING_DEVICE,
                        False,
                    ),
                    (
                        EnergySupplyEvidencePredicate.ENERGY_QUANTITY_CONFORMS_TO_CONTRACT,
                        False,
                    ),
                    (EnergySupplyEvidencePredicate.ENERGY_QUALITY_DEFECTIVE, False),
                    (EnergySupplyEvidencePredicate.SUBSCRIBER_IS_HOUSEHOLD_CONSUMER, False),
                    (
                        EnergySupplyEvidencePredicate.SUBSCRIBER_MAINTAINED_NETWORKS_AND_REGIME,
                        False,
                    ),
                    (EnergySupplyEvidencePredicate.SUBSCRIBER_PAID_FOR_METERED_ENERGY, False),
                    (EnergySupplyEvidencePredicate.SUPPLY_INTERRUPTED, False),
                    (EnergySupplyEvidencePredicate.SUPPLY_INTERRUPTION_AGREED, False),
                    (
                        EnergySupplyEvidencePredicate.UNAGREED_INTERRUPTION_FOR_EMERGENCY_WITH_NOTICE,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk539-542-energy-supply-concept-v1",
                "synthetic-ru-gk543-547-energy-supply-duties-and-interruption-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-energy-supply-reviewer",
        ),
        real_estate_sale_evidence=ReviewedRealEstateSaleEvidence(
            id="reviewed-real-estate-sale-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                RealEstateSaleEvidenceAssertion(
                    id=f"real-estate-sale-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-real-estate-sale-evidence",),
                )
                for predicate, value in (
                    (RealEstateSaleEvidencePredicate.REAL_ESTATE_TRANSFER_CONTRACT, False),
                    (RealEstateSaleEvidencePredicate.WRITTEN_SINGLE_DOCUMENT_SIGNED, False),
                    (RealEstateSaleEvidencePredicate.PROPERTY_DEFINITIVELY_IDENTIFIED, False),
                    (RealEstateSaleEvidencePredicate.PRICE_AGREED_IN_CONTRACT, False),
                    (RealEstateSaleEvidencePredicate.OWNERSHIP_TRANSFER_REGISTERED, False),
                    (RealEstateSaleEvidencePredicate.PROPERTY_HANDED_OVER_BY_DEED, False),
                    (RealEstateSaleEvidencePredicate.PARTY_EVADED_TRANSFER_DEED, False),
                    (RealEstateSaleEvidencePredicate.PROPERTY_QUALITY_DEFECTIVE, False),
                    (RealEstateSaleEvidencePredicate.RESIDENTIAL_PREMISES, False),
                    (RealEstateSaleEvidencePredicate.OCCUPANT_RIGHTS_LIST_INCLUDED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk549-552-real-estate-sale-concept-v1",
                "synthetic-ru-gk554-558-real-estate-sale-terms-and-transfer-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-real-estate-sale-reviewer",
        ),
        enterprise_sale_evidence=ReviewedEnterpriseSaleEvidence(
            id="reviewed-enterprise-sale-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                EnterpriseSaleEvidenceAssertion(
                    id=f"enterprise-sale-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-enterprise-sale-evidence",),
                )
                for predicate, value in (
                    (
                        EnterpriseSaleEvidencePredicate.ENTERPRISE_AS_GOING_CONCERN_CONTRACT,
                        False,
                    ),
                    (
                        EnterpriseSaleEvidencePredicate.WRITTEN_SINGLE_DOCUMENT_WITH_ANNEXES,
                        False,
                    ),
                    (EnterpriseSaleEvidencePredicate.SALE_CONTRACT_REGISTERED, False),
                    (EnterpriseSaleEvidencePredicate.COMPOSITION_DOCUMENTS_PREPARED, False),
                    (EnterpriseSaleEvidencePredicate.CREDITORS_NOTIFIED_IN_WRITING, False),
                    (
                        EnterpriseSaleEvidencePredicate.DEBT_TRANSFERRED_WITHOUT_CREDITOR_CONSENT,
                        False,
                    ),
                    (EnterpriseSaleEvidencePredicate.ENTERPRISE_TRANSFERRED_BY_DEED, False),
                    (EnterpriseSaleEvidencePredicate.OWNERSHIP_TRANSFER_REGISTERED, False),
                    (EnterpriseSaleEvidencePredicate.UNDISCLOSED_DEBTS_IN_COMPOSITION, False),
                    (
                        EnterpriseSaleEvidencePredicate.RESCISSION_HARMS_CREDITORS_OR_PUBLIC,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk559-561-enterprise-sale-concept-v1",
                "synthetic-ru-gk562-566-enterprise-sale-creditors-and-transfer-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-enterprise-sale-reviewer",
        ),
        barter_evidence=ReviewedBarterEvidence(
            id="reviewed-barter-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                BarterEvidenceAssertion(
                    id=f"barter-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-barter-evidence",),
                )
                for predicate, value in (
                    (BarterEvidencePredicate.MUTUAL_GOODS_FOR_GOODS_EXCHANGE, False),
                    (BarterEvidencePredicate.CONTRARY_TO_BARTER_ESSENCE, False),
                    (BarterEvidencePredicate.GOODS_TREATED_AS_EQUAL_VALUE, False),
                    (BarterEvidencePredicate.GOODS_UNEQUAL_VALUE, False),
                    (BarterEvidencePredicate.LOWER_PRICE_PARTY_PAID_DIFFERENCE, False),
                    (BarterEvidencePredicate.TRANSFER_DEADLINES_DIFFER, False),
                    (BarterEvidencePredicate.FIRST_PARTY_PERFORMED_ITS_TRANSFER, False),
                    (BarterEvidencePredicate.BOTH_PARTIES_TRANSFERRED_GOODS, False),
                    (BarterEvidencePredicate.RECEIVED_GOOD_EVICTED_BY_THIRD_PARTY, False),
                    (BarterEvidencePredicate.EVICTION_GROUND_AROSE_BEFORE_PERFORMANCE, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk567-568-barter-concept-and-price-v1",
                "synthetic-ru-gk569-571-barter-performance-and-eviction-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-barter-reviewer",
        ),
        gift_evidence=ReviewedGiftEvidence(
            id="reviewed-gift-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                GiftEvidenceAssertion(
                    id=f"gift-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-gift-evidence",),
                )
                for predicate, value in (
                    (GiftEvidencePredicate.GRATUITOUS_TRANSFER_OR_PROMISE, False),
                    (GiftEvidencePredicate.COUNTER_OBLIGATION_PRESENT, False),
                    (GiftEvidencePredicate.WRITTEN_FORM_REQUIRED, False),
                    (GiftEvidencePredicate.WRITTEN_FORM_SATISFIED, False),
                    (GiftEvidencePredicate.DONATION_STATUTORILY_PROHIBITED, False),
                    (GiftEvidencePredicate.RESTRICTION_CONSENT_MISSING, False),
                    (GiftEvidencePredicate.DONEE_REFUSED_BEFORE_DELIVERY, False),
                    (GiftEvidencePredicate.DONOR_REVOCATION_GROUND_PRESENT, False),
                    (GiftEvidencePredicate.ORDINARY_LOW_VALUE_GIFT, False),
                    (GiftEvidencePredicate.CHARITABLE_DONATION_PURPOSE_VIOLATED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk572-576-gift-concept-and-form-v1",
                "synthetic-ru-gk573-582-gift-refusal-revocation-and-donation-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-gift-reviewer",
        ),
        annuity_evidence=ReviewedAnnuityEvidence(
            id="reviewed-annuity-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                AnnuityEvidenceAssertion(
                    id=f"annuity-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-annuity-evidence",),
                )
                for predicate, value in (
                    (AnnuityEvidencePredicate.PROPERTY_TRANSFERRED_FOR_PERIODIC_RENT, False),
                    (AnnuityEvidencePredicate.NOTARIZATION_MISSING, False),
                    (AnnuityEvidencePredicate.RENT_SECURITY_MISSING, False),
                    (AnnuityEvidencePredicate.RENT_PAYMENT_OVERDUE, False),
                    (AnnuityEvidencePredicate.PERMANENT_RENT, False),
                    (AnnuityEvidencePredicate.PAYER_WAIVED_REDEMPTION_RIGHT, False),
                    (AnnuityEvidencePredicate.RECIPIENT_REDEMPTION_GROUND_PRESENT, False),
                    (AnnuityEvidencePredicate.LIFE_ANNUITY_OR_MAINTENANCE, False),
                    (AnnuityEvidencePredicate.PAYER_MATERIALLY_BREACHED, False),
                    (
                        AnnuityEvidencePredicate.MAINTENANCE_PROPERTY_ENCUMBERED_WITHOUT_CONSENT,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk583-593-annuity-general-and-permanent-v1",
                "synthetic-ru-gk596-605-annuity-life-and-maintenance-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-annuity-reviewer",
        ),
        lease_evidence=ReviewedLeaseEvidence(
            id="reviewed-lease-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                LeaseEvidenceAssertion(
                    id=f"lease-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-lease-evidence",),
                )
                for predicate, value in (
                    (LeaseEvidencePredicate.PROPERTY_LEASED_FOR_TEMPORARY_USE, False),
                    (LeaseEvidencePredicate.LEASE_OBJECT_NOT_IDENTIFIABLE, False),
                    (LeaseEvidencePredicate.LEASE_FORM_OR_REGISTRATION_MISSING, False),
                    (LeaseEvidencePredicate.LEASED_PROPERTY_DEFECTIVE_OR_INCOMPLETE, False),
                    (LeaseEvidencePredicate.THIRD_PARTY_RIGHTS_NOT_DISCLOSED, False),
                    (LeaseEvidencePredicate.SUBLEASE_WITHOUT_LESSOR_CONSENT, False),
                    (LeaseEvidencePredicate.LESSOR_FAILED_CAPITAL_REPAIR, False),
                    (LeaseEvidencePredicate.TENANT_MATERIALLY_BREACHED, False),
                    (LeaseEvidencePredicate.TENANT_SEEKS_RENEWAL_WITH_PRIORITY, False),
                    (LeaseEvidencePredicate.INSEPARABLE_IMPROVEMENTS_WITH_CONSENT, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk606-614-lease-concept-object-and-rent-v1",
                "synthetic-ru-gk615-625-lease-use-repair-and-renewal-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-lease-reviewer",
        ),
        rental_evidence=ReviewedRentalEvidence(
            id="reviewed-rental-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                RentalEvidenceAssertion(
                    id=f"rental-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-rental-evidence",),
                )
                for predicate, value in (
                    (
                        RentalEvidencePredicate.MOVABLE_PROPERTY_RENTED_BY_PROFESSIONAL_LESSOR,
                        False,
                    ),
                    (RentalEvidencePredicate.WRITTEN_FORM_MISSING, False),
                    (RentalEvidencePredicate.LEASE_TERM_EXCEEDS_ONE_YEAR, False),
                    (RentalEvidencePredicate.RENEWAL_OR_PRIORITY_RIGHT_CLAIMED, False),
                    (RentalEvidencePredicate.DEFECT_PRESENT, False),
                    (RentalEvidencePredicate.DEFECT_FROM_TENANT_MISUSE, False),
                    (RentalEvidencePredicate.LESSOR_FAILED_TO_REMEDY_DEFECT, False),
                    (RentalEvidencePredicate.EARLY_RETURN_REFUND_DENIED, False),
                    (RentalEvidencePredicate.REPAIR_OBLIGATION_NEGLECTED, False),
                    (RentalEvidencePredicate.SUBLEASE_OR_RIGHTS_TRANSFER_ATTEMPTED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk626-628-rental-concept-form-and-term-v1",
                "synthetic-ru-gk629-631-rental-defects-payment-and-repair-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-rental-reviewer",
        ),
        vehicle_lease_evidence=ReviewedVehicleLeaseEvidence(
            id="reviewed-vehicle-lease-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                VehicleLeaseEvidenceAssertion(
                    id=f"vehicle-lease-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-vehicle-lease-evidence",),
                )
                for predicate, value in (
                    (VehicleLeaseEvidencePredicate.VEHICLE_LEASED_FOR_TEMPORARY_USE, False),
                    (VehicleLeaseEvidencePredicate.LEASE_WITH_CREW, False),
                    (VehicleLeaseEvidencePredicate.WRITTEN_FORM_MISSING, False),
                    (VehicleLeaseEvidencePredicate.RENEWAL_OR_PRIORITY_RIGHT_CLAIMED, False),
                    (VehicleLeaseEvidencePredicate.MAINTENANCE_OR_REPAIR_NEGLECTED, False),
                    (VehicleLeaseEvidencePredicate.CREW_SERVICE_NOT_PROVIDED, False),
                    (VehicleLeaseEvidencePredicate.OPERATING_COSTS_MISALLOCATED, False),
                    (VehicleLeaseEvidencePredicate.INSURANCE_OBLIGATION_BREACHED, False),
                    (VehicleLeaseEvidencePredicate.SUBLEASE_WRONGLY_RESTRICTED, False),
                    (
                        VehicleLeaseEvidencePredicate.THIRD_PARTY_HARM_LIABILITY_MISASSIGNED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk632-641-vehicle-lease-with-crew-v1",
                "synthetic-ru-gk642-649-vehicle-lease-without-crew-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-vehicle-lease-reviewer",
        ),
        building_lease_evidence=ReviewedBuildingLeaseEvidence(
            id="reviewed-building-lease-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                BuildingLeaseEvidenceAssertion(
                    id=f"building-lease-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-building-lease-evidence",),
                )
                for predicate, value in (
                    (BuildingLeaseEvidencePredicate.BUILDING_LEASED_FOR_TEMPORARY_USE, False),
                    (BuildingLeaseEvidencePredicate.SINGLE_WRITTEN_DOCUMENT_MISSING, False),
                    (BuildingLeaseEvidencePredicate.LEASE_TERM_AT_LEAST_ONE_YEAR, False),
                    (BuildingLeaseEvidencePredicate.STATE_REGISTRATION_MISSING, False),
                    (BuildingLeaseEvidencePredicate.LAND_RIGHTS_NOT_TRANSFERRED, False),
                    (BuildingLeaseEvidencePredicate.LAND_OWNERSHIP_CHANGED, False),
                    (BuildingLeaseEvidencePredicate.LAND_USE_RIGHT_DENIED_AFTER_CHANGE, False),
                    (BuildingLeaseEvidencePredicate.AGREED_RENT_AMOUNT_MISSING, False),
                    (BuildingLeaseEvidencePredicate.TRANSFER_DEED_MISSING, False),
                    (BuildingLeaseEvidencePredicate.RETURN_DEED_MISSING, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk650-651-building-lease-concept-form-and-registration-v1",
                "synthetic-ru-gk652-655-building-lease-land-rent-and-transfer-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-building-lease-reviewer",
        ),
        enterprise_lease_evidence=ReviewedEnterpriseLeaseEvidence(
            id="reviewed-enterprise-lease-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                EnterpriseLeaseEvidenceAssertion(
                    id=f"enterprise-lease-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-enterprise-lease-evidence",),
                )
                for predicate, value in (
                    (EnterpriseLeaseEvidencePredicate.ENTERPRISE_LEASED_AS_COMPLEX, False),
                    (EnterpriseLeaseEvidencePredicate.SINGLE_WRITTEN_DOCUMENT_MISSING, False),
                    (EnterpriseLeaseEvidencePredicate.STATE_REGISTRATION_MISSING, False),
                    (EnterpriseLeaseEvidencePredicate.CREDITORS_NOT_NOTIFIED, False),
                    (
                        EnterpriseLeaseEvidencePredicate.DEBT_TRANSFERRED_WITHOUT_CREDITOR_CONSENT,
                        False,
                    ),
                    (EnterpriseLeaseEvidencePredicate.TRANSFER_DEED_MISSING, False),
                    (EnterpriseLeaseEvidencePredicate.LESSOR_FAILED_TRANSFER_PREPARATION, False),
                    (
                        EnterpriseLeaseEvidencePredicate.TENANT_DISPOSAL_RIGHT_WRONGLY_RESTRICTED,
                        False,
                    ),
                    (EnterpriseLeaseEvidencePredicate.MAINTENANCE_OR_REPAIR_NEGLECTED, False),
                    (EnterpriseLeaseEvidencePredicate.RETURN_PREPARATION_NEGLECTED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk656-659-enterprise-lease-concept-form-and-creditors-v1",
                "synthetic-ru-gk660-664-enterprise-lease-use-maintenance-and-return-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-enterprise-lease-reviewer",
        ),
        leasing_evidence=ReviewedLeasingEvidence(
            id="reviewed-leasing-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                LeasingEvidenceAssertion(
                    id=f"leasing-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-leasing-evidence",),
                )
                for predicate, value in (
                    (LeasingEvidencePredicate.PROPERTY_ACQUIRED_FOR_LESSEE_AND_LEASED, False),
                    (LeasingEvidencePredicate.LEASED_OBJECT_IS_NON_CONSUMABLE_THING, False),
                    (LeasingEvidencePredicate.OBJECT_EXCLUDED_FROM_LEASING, False),
                    (LeasingEvidencePredicate.SELLER_NOT_NOTIFIED_OF_LEASING_PURPOSE, False),
                    (LeasingEvidencePredicate.LESSOR_SELECTED_SELLER, False),
                    (LeasingEvidencePredicate.OBJECT_NOT_DELIVERED_IN_TIME, False),
                    (LeasingEvidencePredicate.DELAY_ATTRIBUTABLE_TO_LESSOR, False),
                    (LeasingEvidencePredicate.RISK_ALLOCATION_DISPUTED_BEFORE_TRANSFER, False),
                    (
                        LeasingEvidencePredicate.LESSEE_DENIED_DIRECT_CLAIM_AGAINST_SELLER,
                        False,
                    ),
                    (LeasingEvidencePredicate.SELLER_BREACHED_OBLIGATIONS, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk665-667-leasing-concept-object-and-notice-v1",
                "synthetic-ru-gk668-670-leasing-delivery-risk-and-seller-claims-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-leasing-reviewer",
        ),
        residential_lease_evidence=ReviewedResidentialLeaseEvidence(
            id="reviewed-residential-lease-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ResidentialLeaseEvidenceAssertion(
                    id=f"residential-lease-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-residential-lease-evidence",),
                )
                for predicate, value in (
                    (
                        ResidentialLeaseEvidencePredicate.DWELLING_PROVIDED_FOR_RESIDENCE_FOR_FEE,
                        False,
                    ),
                    (ResidentialLeaseEvidencePredicate.WRITTEN_FORM_MISSING, False),
                    (ResidentialLeaseEvidencePredicate.DWELLING_NOT_ISOLATED_OR_UNFIT, False),
                    (ResidentialLeaseEvidencePredicate.SHORT_TERM_LEASE_UP_TO_ONE_YEAR, False),
                    (ResidentialLeaseEvidencePredicate.LESSOR_FAILED_OPERATION_DUTIES, False),
                    (ResidentialLeaseEvidencePredicate.TENANT_BREACHED_USE_OR_PAYMENT, False),
                    (ResidentialLeaseEvidencePredicate.RENT_UNILATERALLY_CHANGED, False),
                    (
                        ResidentialLeaseEvidencePredicate.RENEWAL_OFFER_NOT_MADE_BEFORE_EXPIRY,
                        False,
                    ),
                    (ResidentialLeaseEvidencePredicate.LESSOR_TERMINATED_WITHOUT_COURT, False),
                    (ResidentialLeaseEvidencePredicate.TENANT_DENIED_REMEDY_PERIOD, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk671-678-residential-lease-concept-form-and-duties-v1",
                "synthetic-ru-gk682-688-residential-lease-rent-renewal-and-termination-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-residential-lease-reviewer",
        ),
        gratuitous_use_evidence=ReviewedGratuitousUseEvidence(
            id="reviewed-gratuitous-use-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                GratuitousUseEvidenceAssertion(
                    id=f"gratuitous-use-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-gratuitous-use-evidence",),
                )
                for predicate, value in (
                    (
                        GratuitousUseEvidencePredicate.THING_PROVIDED_FOR_FREE_TEMPORARY_USE,
                        False,
                    ),
                    (
                        GratuitousUseEvidencePredicate.LENDER_IS_ORGANIZATION_TRANSFERRING_TO_INSIDER,
                        False,
                    ),
                    (GratuitousUseEvidencePredicate.THING_NOT_PROVIDED_OR_INCOMPLETE, False),
                    (
                        GratuitousUseEvidencePredicate.DEFECT_INTENTIONALLY_OR_GROSSLY_CONCEALED,
                        False,
                    ),
                    (GratuitousUseEvidencePredicate.THIRD_PARTY_RIGHTS_NOT_DISCLOSED, False),
                    (GratuitousUseEvidencePredicate.MAINTENANCE_DUTY_NEGLECTED, False),
                    (GratuitousUseEvidencePredicate.ACCIDENTAL_LOSS_RISK_MISALLOCATED, False),
                    (GratuitousUseEvidencePredicate.EARLY_TERMINATION_GROUND_PRESENT, False),
                    (
                        GratuitousUseEvidencePredicate.WITHDRAWAL_NOTICE_PERIOD_NOT_OBSERVED,
                        False,
                    ),
                    (
                        GratuitousUseEvidencePredicate.THING_ALIENATED_WITHOUT_PRESERVING_USE,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk689-694-gratuitous-use-concept-limits-and-defects-v1",
                "synthetic-ru-gk695-701-gratuitous-use-maintenance-risk-and-termination-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-gratuitous-use-reviewer",
        ),
        work_contract_evidence=ReviewedWorkContractEvidence(
            id="reviewed-work-contract-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                WorkContractEvidenceAssertion(
                    id=f"work-contract-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-work-contract-evidence",),
                )
                for predicate, value in (
                    (
                        WorkContractEvidencePredicate.WORK_PERFORMED_AND_RESULT_DELIVERED_FOR_FEE,
                        False,
                    ),
                    (
                        WorkContractEvidencePredicate.SUBCONTRACTOR_ENGAGED_DESPITE_PERSONAL_DUTY,
                        False,
                    ),
                    (WorkContractEvidencePredicate.START_OR_COMPLETION_TERM_NOT_AGREED, False),
                    (
                        WorkContractEvidencePredicate.ESTIMATE_EXCEEDED_WITHOUT_TIMELY_NOTICE,
                        False,
                    ),
                    (WorkContractEvidencePredicate.CUSTOMER_MATERIAL_UNSUITABLE, False),
                    (WorkContractEvidencePredicate.CONTRACTOR_FAILED_TO_WARN_OF_RISK, False),
                    (WorkContractEvidencePredicate.WORK_RESULT_DEFECTIVE, False),
                    (WorkContractEvidencePredicate.DEFECT_FOUND_WITHIN_STATUTORY_PERIOD, False),
                    (
                        WorkContractEvidencePredicate.ACCEPTANCE_AVOIDED_OR_INSPECTION_OMITTED,
                        False,
                    ),
                    (
                        WorkContractEvidencePredicate.CUSTOMER_WITHDREW_BEFORE_COMPLETION_WITHOUT_PAYMENT,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk702-716-work-contract-concept-terms-and-materials-v1",
                "synthetic-ru-gk717-729-work-contract-quality-acceptance-and-withdrawal-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-work-contract-reviewer",
        ),
        consumer_work_evidence=ReviewedConsumerWorkEvidence(
            id="reviewed-consumer-work-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ConsumerWorkEvidenceAssertion(
                    id=f"consumer-work-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-consumer-work-evidence",),
                )
                for predicate, value in (
                    (ConsumerWorkEvidencePredicate.WORK_FOR_PERSONAL_CONSUMER_NEEDS, False),
                    (
                        ConsumerWorkEvidencePredicate.ADDITIONAL_WORK_IMPOSED_WITHOUT_CONSENT,
                        False,
                    ),
                    (
                        ConsumerWorkEvidencePredicate.WITHDRAWAL_RIGHT_BEFORE_DELIVERY_DENIED,
                        False,
                    ),
                    (ConsumerWorkEvidencePredicate.CONSUMER_INFORMATION_NOT_PROVIDED, False),
                    (ConsumerWorkEvidencePredicate.CONTRACTOR_MATERIAL_DEFECTIVE, False),
                    (
                        ConsumerWorkEvidencePredicate.PAYMENT_DEMANDED_BEFORE_ACCEPTANCE_WITHOUT_CONSENT,
                        False,
                    ),
                    (ConsumerWorkEvidencePredicate.OPERATION_INFORMATION_NOT_PROVIDED, False),
                    (ConsumerWorkEvidencePredicate.WORK_RESULT_HAS_SIGNIFICANT_DEFECT, False),
                    (
                        ConsumerWorkEvidencePredicate.SIGNIFICANT_DEFECT_FOUND_WITHIN_TEN_YEARS,
                        False,
                    ),
                    (ConsumerWorkEvidencePredicate.RESULT_SOLD_WITHOUT_TWO_MONTH_NOTICE, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk730-736-consumer-work-concept-information-and-payment-v1",
                "synthetic-ru-gk737-739-consumer-work-defects-and-uncollected-result-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-consumer-work-reviewer",
        ),
        construction_contract_evidence=ReviewedConstructionContractEvidence(
            id="reviewed-construction-contract-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ConstructionContractEvidenceAssertion(
                    id=f"construction-contract-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-construction-contract-evidence",),
                )
                for predicate, value in (
                    (
                        ConstructionContractEvidencePredicate.CONSTRUCTION_WORK_PERFORMED_AND_ACCEPTED_FOR_PRICE,
                        False,
                    ),
                    (ConstructionContractEvidencePredicate.RISK_INSURANCE_DUTY_UNMET, False),
                    (
                        ConstructionContractEvidencePredicate.TECHNICAL_DOCUMENTATION_OR_ESTIMATE_NOT_AGREED,
                        False,
                    ),
                    (
                        ConstructionContractEvidencePredicate.ADDITIONAL_WORK_DISCOVERED_WITHOUT_NOTICE,
                        False,
                    ),
                    (
                        ConstructionContractEvidencePredicate.CUSTOMER_FAILED_TO_PROVIDE_SITE_OR_SERVICES,
                        False,
                    ),
                    (ConstructionContractEvidencePredicate.CUSTOMER_SUPERVISION_OBSTRUCTED, False),
                    (
                        ConstructionContractEvidencePredicate.CONSTRUCTION_SUSPENDED_AND_CONSERVED,
                        False,
                    ),
                    (
                        ConstructionContractEvidencePredicate.ACCEPTANCE_ACT_SIGNING_REFUSED_WITHOUT_GROUNDS,
                        False,
                    ),
                    (
                        ConstructionContractEvidencePredicate.WORK_DEVIATES_FROM_DOCUMENTATION_OR_REQUIREMENTS,
                        False,
                    ),
                    (
                        ConstructionContractEvidencePredicate.DEFECT_FOUND_WITHIN_FIVE_YEAR_PERIOD,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk740-749-construction-contract-concept-documentation-and-duties-v1",
                "synthetic-ru-gk752-757-construction-contract-conservation-acceptance-and-quality-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-construction-contract-reviewer",
        ),
        design_work_evidence=ReviewedDesignWorkEvidence(
            id="reviewed-design-work-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                DesignWorkEvidenceAssertion(
                    id=f"design-work-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-design-work-evidence",),
                )
                for predicate, value in (
                    (DesignWorkEvidencePredicate.DESIGN_OR_SURVEY_WORK_PERFORMED_FOR_FEE, False),
                    (DesignWorkEvidencePredicate.ASSIGNMENT_OR_INITIAL_DATA_NOT_PROVIDED, False),
                    (
                        DesignWorkEvidencePredicate.ASSIGNMENT_REQUIREMENTS_DEVIATED_WITHOUT_CONSENT,
                        False,
                    ),
                    (
                        DesignWorkEvidencePredicate.DOCUMENTATION_NOT_AGREED_WITH_AUTHORITIES,
                        False,
                    ),
                    (
                        DesignWorkEvidencePredicate.DOCUMENTATION_DISCLOSED_TO_THIRD_PARTY_WITHOUT_CONSENT,
                        False,
                    ),
                    (DesignWorkEvidencePredicate.THIRD_PARTY_RIGHT_OBSTRUCTS_WORK, False),
                    (DesignWorkEvidencePredicate.DOCUMENTATION_OR_SURVEY_DEFECTIVE, False),
                    (
                        DesignWorkEvidencePredicate.DEFECT_REVEALED_DURING_CONSTRUCTION_OR_USE,
                        False,
                    ),
                    (
                        DesignWorkEvidencePredicate.CUSTOMER_PAYMENT_OR_ASSISTANCE_DUTY_UNMET,
                        False,
                    ),
                    (
                        DesignWorkEvidencePredicate.EXTRA_COSTS_FROM_CHANGED_INITIAL_DATA_NOT_COMPENSATED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk758-760-design-work-concept-initial-data-and-approval-v1",
                "synthetic-ru-gk761-762-design-work-liability-and-customer-duties-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-design-work-reviewer",
        ),
        state_work_evidence=ReviewedStateWorkEvidence(
            id="reviewed-state-work-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                StateWorkEvidenceAssertion(
                    id=f"state-work-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-state-work-evidence",),
                )
                for predicate, value in (
                    (StateWorkEvidencePredicate.WORK_FOR_STATE_OR_MUNICIPAL_NEEDS, False),
                    (StateWorkEvidencePredicate.STATE_CONTRACT_NOT_CONCLUDED, False),
                    (StateWorkEvidencePredicate.CUSTOMER_NOT_AUTHORIZED_BUDGET_RECIPIENT, False),
                    (StateWorkEvidencePredicate.CONTRACT_CONCLUSION_PROCEDURE_BREACHED, False),
                    (StateWorkEvidencePredicate.SCOPE_OR_COST_TERMS_NOT_AGREED, False),
                    (StateWorkEvidencePredicate.START_OR_COMPLETION_DATES_NOT_AGREED, False),
                    (StateWorkEvidencePredicate.FUNDING_AND_PAYMENT_TERMS_NOT_AGREED, False),
                    (StateWorkEvidencePredicate.PERFORMANCE_SECURITY_NOT_AGREED, False),
                    (StateWorkEvidencePredicate.BUDGET_REDUCED_WITHOUT_AGREED_NEW_TERMS, False),
                    (
                        StateWorkEvidencePredicate.CONTRACTOR_LOSSES_FROM_CHANGED_TERMS_NOT_COMPENSATED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk763-766-state-work-contract-basis-parties-and-terms-v1",
                "synthetic-ru-gk767-768-state-work-budget-changes-and-special-law-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-state-work-reviewer",
        ),
        research_work_evidence=ReviewedResearchWorkEvidence(
            id="reviewed-research-work-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ResearchWorkEvidenceAssertion(
                    id=f"research-work-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-research-work-evidence",),
                )
                for predicate, value in (
                    (
                        ResearchWorkEvidencePredicate.RESEARCH_OR_DEVELOPMENT_WORK_PERFORMED_FOR_FEE,
                        False,
                    ),
                    (
                        ResearchWorkEvidencePredicate.THIRD_PARTY_ENGAGED_WITHOUT_CONSENT_IN_RESEARCH,
                        False,
                    ),
                    (
                        ResearchWorkEvidencePredicate.CONFIDENTIALITY_OR_PUBLICATION_DUTY_BREACHED,
                        False,
                    ),
                    (ResearchWorkEvidencePredicate.RESULT_USE_RIGHTS_NOT_AGREED, False),
                    (ResearchWorkEvidencePredicate.THIRD_PARTY_EXCLUSIVE_RIGHTS_INFRINGED, False),
                    (ResearchWorkEvidencePredicate.IMPOSSIBILITY_NOT_REPORTED_IMMEDIATELY, False),
                    (
                        ResearchWorkEvidencePredicate.CUSTOMER_INFORMATION_OR_ACCEPTANCE_DUTY_UNMET,
                        False,
                    ),
                    (
                        ResearchWorkEvidencePredicate.RESULT_UNACHIEVABLE_WITHOUT_PERFORMER_FAULT,
                        False,
                    ),
                    (ResearchWorkEvidencePredicate.PRE_IMPOSSIBILITY_COSTS_NOT_PAID, False),
                    (
                        ResearchWorkEvidencePredicate.PERFORMER_BREACH_WITHOUT_PROOF_OF_ABSENT_FAULT,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk769-774-research-work-concept-confidentiality-and-duties-v1",
                "synthetic-ru-gk775-778-research-work-impossibility-and-liability-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-research-work-reviewer",
        ),
        paid_services_evidence=ReviewedPaidServicesEvidence(
            id="reviewed-paid-services-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                PaidServicesEvidenceAssertion(
                    id=f"paid-services-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-paid-services-evidence",),
                )
                for predicate, value in (
                    (
                        PaidServicesEvidencePredicate.SERVICES_RENDERED_FOR_FEE_BY_ASSIGNMENT,
                        False,
                    ),
                    (PaidServicesEvidencePredicate.CONTRACT_COVERED_BY_SPECIAL_CHAPTER, False),
                    (
                        PaidServicesEvidencePredicate.THIRD_PARTY_PERFORMED_WITHOUT_CONTRACT_PERMISSION,
                        False,
                    ),
                    (PaidServicesEvidencePredicate.PAYMENT_TERMS_OR_DEADLINE_BREACHED, False),
                    (PaidServicesEvidencePredicate.IMPOSSIBILITY_CAUSED_BY_CUSTOMER, False),
                    (PaidServicesEvidencePredicate.IMPOSSIBILITY_WITHOUT_PARTY_FAULT, False),
                    (PaidServicesEvidencePredicate.ACTUAL_EXPENSES_NOT_REIMBURSED, False),
                    (
                        PaidServicesEvidencePredicate.CUSTOMER_WITHDREW_WITHOUT_COVERING_EXPENSES,
                        False,
                    ),
                    (
                        PaidServicesEvidencePredicate.PERFORMER_WITHDREW_WITHOUT_FULL_COMPENSATION,
                        False,
                    ),
                    (
                        PaidServicesEvidencePredicate.COMMUNICATION_SUSPENSION_RULES_BREACHED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk779-781-paid-services-concept-personal-performance-and-payment-v1",
                "synthetic-ru-gk782-783-1-paid-services-withdrawal-and-communication-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-paid-services-reviewer",
        ),
        carriage_evidence=ReviewedCarriageEvidence(
            id="reviewed-carriage-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                CarriageEvidenceAssertion(
                    id=f"carriage-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-carriage-evidence",),
                )
                for predicate, value in (
                    (CarriageEvidencePredicate.CARRIAGE_OF_GOODS_OR_PASSENGER_FOR_FEE, False),
                    (CarriageEvidencePredicate.TRANSPORT_DOCUMENT_NOT_ISSUED, False),
                    (CarriageEvidencePredicate.PUBLIC_CARRIER_REFUSED_WITHOUT_GROUNDS, False),
                    (
                        CarriageEvidencePredicate.CARRIAGE_CHARGE_OR_RETENTION_RULES_BREACHED,
                        False,
                    ),
                    (CarriageEvidencePredicate.VEHICLE_NOT_SUPPLIED_OR_NOT_USED, False),
                    (CarriageEvidencePredicate.DELIVERY_DEADLINE_MISSED, False),
                    (CarriageEvidencePredicate.PASSENGER_DEPARTURE_DELAYED, False),
                    (CarriageEvidencePredicate.CARGO_LOST_SHORT_OR_DAMAGED, False),
                    (
                        CarriageEvidencePredicate.CARRIER_FAULT_NOT_DISPROVED_FOR_CARGO_LOSS,
                        False,
                    ),
                    (CarriageEvidencePredicate.LIABILITY_LIMITATION_AGREEMENT_PRESENT, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk784-792-carriage-concept-documents-and-obligations-v1",
                "synthetic-ru-gk793-800-carriage-liability-and-claims-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-carriage-reviewer",
        ),
        forwarding_evidence=ReviewedForwardingEvidence(
            id="reviewed-forwarding-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ForwardingEvidenceAssertion(
                    id=f"forwarding-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-forwarding-evidence",),
                )
                for predicate, value in (
                    (
                        ForwardingEvidencePredicate.FORWARDING_SERVICES_FOR_FEE_AT_CLIENT_EXPENSE,
                        False,
                    ),
                    (
                        ForwardingEvidencePredicate.WRITTEN_FORM_OR_POWER_OF_ATTORNEY_MISSING,
                        False,
                    ),
                    (
                        ForwardingEvidencePredicate.FORWARDER_FAILED_TO_PERFORM_AGREED_SERVICES,
                        False,
                    ),
                    (
                        ForwardingEvidencePredicate.CARRIER_BREACH_CAUSED_FORWARDER_LIABILITY,
                        False,
                    ),
                    (
                        ForwardingEvidencePredicate.CLIENT_DOCUMENTS_OR_INFORMATION_NOT_PROVIDED,
                        False,
                    ),
                    (
                        ForwardingEvidencePredicate.FORWARDER_DID_NOT_REPORT_INCOMPLETE_INFORMATION,
                        False,
                    ),
                    (
                        ForwardingEvidencePredicate.THIRD_PARTY_ENGAGED_DESPITE_PERSONAL_DUTY,
                        False,
                    ),
                    (ForwardingEvidencePredicate.WITHDRAWAL_WITHOUT_REASONABLE_NOTICE, False),
                    (ForwardingEvidencePredicate.WITHDRAWAL_LOSSES_NOT_COMPENSATED, False),
                    (
                        ForwardingEvidencePredicate.STATUTORY_PENALTY_NOT_PAID_ON_WITHDRAWAL,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk801-804-forwarding-concept-form-and-information-v1",
                "synthetic-ru-gk805-806-forwarding-third-parties-and-withdrawal-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-forwarding-reviewer",
        ),
        loan_evidence=ReviewedLoanEvidence(
            id="reviewed-loan-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                LoanEvidenceAssertion(
                    id=f"loan-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-loan-evidence",),
                )
                for predicate, value in (
                    (LoanEvidencePredicate.MONEY_OR_FUNGIBLES_TRANSFERRED_FOR_RETURN, False),
                    (LoanEvidencePredicate.WRITTEN_FORM_REQUIRED_BUT_MISSING, False),
                    (LoanEvidencePredicate.INTEREST_TERMS_NOT_COMPLIANT, False),
                    (LoanEvidencePredicate.USURIOUS_INTEREST_RATE, False),
                    (LoanEvidencePredicate.REPAYMENT_DEADLINE_BREACHED, False),
                    (LoanEvidencePredicate.LATE_PAYMENT_INTEREST_NOT_ACCRUED, False),
                    (LoanEvidencePredicate.LOAN_CHALLENGED_AS_UNFUNDED, False),
                    (LoanEvidencePredicate.SECURITY_LOST_OR_DETERIORATED, False),
                    (LoanEvidencePredicate.TARGETED_LOAN_MISUSED_OR_CONTROL_OBSTRUCTED, False),
                    (LoanEvidencePredicate.NOVATION_INTO_LOAN_REQUIREMENTS_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk807-811-loan-concept-form-interest-and-repayment-v1",
                "synthetic-ru-gk812-818-loan-challenge-security-purpose-and-novation-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-loan-reviewer",
        ),
        credit_evidence=ReviewedCreditEvidence(
            id="reviewed-credit-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                CreditEvidenceAssertion(
                    id=f"credit-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-credit-evidence",),
                )
                for predicate, value in (
                    (CreditEvidencePredicate.CREDIT_PROVIDED_FOR_RETURN_WITH_INTEREST, False),
                    (CreditEvidencePredicate.LENDER_NOT_A_CREDIT_ORGANISATION, False),
                    (CreditEvidencePredicate.INTEREST_OR_OTHER_PAYMENTS_TERMS_BREACHED, False),
                    (CreditEvidencePredicate.CONSUMER_CREDIT_RULES_APPLICABLE, False),
                    (CreditEvidencePredicate.WRITTEN_FORM_MISSING, False),
                    (CreditEvidencePredicate.LENDER_REFUSED_WITHOUT_INSOLVENCY_GROUNDS, False),
                    (
                        CreditEvidencePredicate.BORROWER_NOTICE_OF_REFUSAL_NOT_GIVEN_IN_TIME,
                        False,
                    ),
                    (CreditEvidencePredicate.TARGETED_CREDIT_MISUSED, False),
                    (CreditEvidencePredicate.EARLY_REPAYMENT_DEMANDED_WITHOUT_GROUNDS, False),
                    (
                        CreditEvidencePredicate.EARLY_REPAYMENT_FROM_CITIZEN_WITHOUT_STATUTORY_GROUND,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk819-820-credit-concept-parties-and-form-v1",
                "synthetic-ru-gk821-821-1-credit-refusal-and-early-repayment-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-credit-reviewer",
        ),
        commercial_credit_evidence=ReviewedCommercialCreditEvidence(
            id="reviewed-commercial-credit-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                CommercialCreditEvidenceAssertion(
                    id=f"commercial-credit-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-commercial-credit-evidence",),
                )
                for predicate, value in (
                    (
                        CommercialCreditEvidencePredicate.GOODS_CREDIT_OBLIGATION_TO_PROVIDE_FUNGIBLES,
                        False,
                    ),
                    (CommercialCreditEvidencePredicate.GOODS_CREDIT_ITEMS_NOT_PROVIDED, False),
                    (
                        CommercialCreditEvidencePredicate.QUANTITY_ASSORTMENT_OR_COMPLETENESS_TERMS_BREACHED,
                        False,
                    ),
                    (
                        CommercialCreditEvidencePredicate.QUALITY_PACKAGING_OR_CONTAINER_TERMS_BREACHED,
                        False,
                    ),
                    (
                        CommercialCreditEvidencePredicate.LOAN_RULES_APPLICATION_EXCLUDED_WITHOUT_GROUND,
                        False,
                    ),
                    (
                        CommercialCreditEvidencePredicate.COMMERCIAL_CREDIT_GRANTED_IN_MAIN_CONTRACT,
                        False,
                    ),
                    (
                        CommercialCreditEvidencePredicate.COMMERCIAL_CREDIT_TERMS_NOT_AGREED_IN_MAIN_CONTRACT,
                        False,
                    ),
                    (
                        CommercialCreditEvidencePredicate.COMMERCIAL_CREDIT_INTEREST_TERMS_BREACHED,
                        False,
                    ),
                    (
                        CommercialCreditEvidencePredicate.CHAPTER_RULES_APPLIED_CONTRARY_TO_MAIN_CONTRACT,
                        False,
                    ),
                    (
                        CommercialCreditEvidencePredicate.STATUTORY_PROHIBITION_ON_COMMERCIAL_CREDIT,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk822-goods-credit-concept-and-sale-rules-v1",
                "synthetic-ru-gk823-commercial-credit-forms-and-applicable-rules-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-commercial-credit-reviewer",
        ),
        factoring_evidence=ReviewedFactoringEvidence(
            id="reviewed-factoring-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                FactoringEvidenceAssertion(
                    id=f"factoring-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-factoring-evidence",),
                )
                for predicate, value in (
                    (FactoringEvidencePredicate.MONETARY_CLAIM_ASSIGNED_FOR_FINANCING, False),
                    (FactoringEvidencePredicate.ASSIGNED_CLAIM_NOT_IDENTIFIED, False),
                    (FactoringEvidencePredicate.FACTOR_NOT_ENTITLED_TO_ACT, False),
                    (
                        FactoringEvidencePredicate.CONTRACTUAL_ASSIGNMENT_BAN_INVOKED_AGAINST_FACTOR,
                        False,
                    ),
                    (FactoringEvidencePredicate.CLIENT_CLAIM_VALIDITY_WARRANTY_BREACHED, False),
                    (
                        FactoringEvidencePredicate.SUBSEQUENT_ASSIGNMENT_MADE_WITHOUT_PERMISSION,
                        False,
                    ),
                    (FactoringEvidencePredicate.DEBTOR_NOT_NOTIFIED_OF_ASSIGNMENT, False),
                    (FactoringEvidencePredicate.DEBTOR_SET_OFF_CLAIMS_DISREGARDED, False),
                    (FactoringEvidencePredicate.FACTOR_SETTLEMENT_WITH_CLIENT_BREACHED, False),
                    (FactoringEvidencePredicate.DEBTOR_REFUND_CLAIM_MISDIRECTED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk824-829-factoring-concept-parties-and-assignment-v1",
                "synthetic-ru-gk830-833-factoring-debtor-performance-and-settlements-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-factoring-reviewer",
        ),
        bank_deposit_evidence=ReviewedBankDepositEvidence(
            id="reviewed-bank-deposit-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                BankDepositEvidenceAssertion(
                    id=f"bank-deposit-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-bank-deposit-evidence",),
                )
                for predicate, value in (
                    (
                        BankDepositEvidencePredicate.DEPOSIT_ACCEPTED_FOR_RETURN_WITH_INTEREST,
                        False,
                    ),
                    (BankDepositEvidencePredicate.DEPOSIT_TAKEN_BY_UNAUTHORISED_PERSON, False),
                    (BankDepositEvidencePredicate.DEPOSIT_WRITTEN_FORM_NOT_OBSERVED, False),
                    (
                        BankDepositEvidencePredicate.CITIZEN_DEPOSIT_ON_DEMAND_REPAYMENT_BREACHED,
                        False,
                    ),
                    (BankDepositEvidencePredicate.EARLY_REPAYMENT_INTEREST_MISCALCULATED, False),
                    (BankDepositEvidencePredicate.DEPOSIT_INTEREST_NOT_PAID_AS_AGREED, False),
                    (
                        BankDepositEvidencePredicate.TERM_DEPOSIT_INTEREST_RATE_UNILATERALLY_REDUCED,
                        False,
                    ),
                    (BankDepositEvidencePredicate.DEPOSIT_REPAYMENT_SECURITY_NOT_ENSURED, False),
                    (BankDepositEvidencePredicate.THIRD_PARTY_DEPOSIT_RIGHTS_DISREGARDED, False),
                    (BankDepositEvidencePredicate.SAVINGS_DOCUMENT_RULES_BREACHED, False),
                    (BankDepositEvidencePredicate.PRECIOUS_METAL_DEPOSIT_ASSERTED, False),
                    (BankDepositEvidencePredicate.PRECIOUS_METAL_DEPOSIT_TERMS_AGREED, False),
                    (BankDepositEvidencePredicate.PRECIOUS_METAL_RETURN_BREACHED, False),
                    (
                        BankDepositEvidencePredicate.INSURANCE_EXCLUSION_NOT_DISCLOSED_TO_CITIZEN,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk834-839-bank-deposit-concept-form-and-interest-v1",
                "synthetic-ru-gk840-844-bank-deposit-security-third-parties-and-documents-v1",
                "synthetic-ru-gk844-1-precious-metal-deposit-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-bank-deposit-reviewer",
        ),
        bank_account_evidence=ReviewedBankAccountEvidence(
            id="reviewed-bank-account-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                BankAccountEvidenceAssertion(
                    id=f"bank-account-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-bank-account-evidence",),
                )
                for predicate, value in (
                    (BankAccountEvidencePredicate.BANK_ACCOUNT_OPENED_FOR_CLIENT_FUNDS, False),
                    (BankAccountEvidencePredicate.ACCOUNT_OPENING_TERMS_BREACHED, False),
                    (BankAccountEvidencePredicate.DISPOSAL_RIGHTS_CERTIFICATION_BREACHED, False),
                    (BankAccountEvidencePredicate.OPERATION_DEADLINES_BREACHED, False),
                    (
                        BankAccountEvidencePredicate.IMPROPER_OPERATION_LIABILITY_NOT_APPLIED,
                        False,
                    ),
                    (BankAccountEvidencePredicate.ACCOUNT_CREDIT_TERMS_BREACHED, False),
                    (BankAccountEvidencePredicate.ACCOUNT_SERVICE_PAYMENT_TERMS_BREACHED, False),
                    (BankAccountEvidencePredicate.FUNDS_DEBITED_WITHOUT_CLIENT_ORDER, False),
                    (BankAccountEvidencePredicate.BANK_SECRECY_OR_RESTRICTION_BREACHED, False),
                    (
                        BankAccountEvidencePredicate.ACCOUNT_TERMINATION_AND_BALANCE_RETURN_BREACHED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk845-853-bank-account-concept-operations-and-payment-v1",
                "synthetic-ru-gk854-860-bank-account-debiting-secrecy-and-termination-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-bank-account-reviewer",
        ),
        settlements_evidence=ReviewedSettlementsEvidence(
            id="reviewed-settlements-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                SettlementsEvidenceAssertion(
                    id=f"settlements-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-settlements-evidence",),
                )
                for predicate, value in (
                    (SettlementsEvidencePredicate.CASHLESS_SETTLEMENTS_PERFORMED, False),
                    (SettlementsEvidencePredicate.SETTLEMENT_FORM_NOT_PROVIDED_BY_LAW, False),
                    (SettlementsEvidencePredicate.PAYMENT_ORDER_EXECUTION_BREACHED, False),
                    (SettlementsEvidencePredicate.PAYMENT_ORDER_LIABILITY_NOT_APPLIED, False),
                    (SettlementsEvidencePredicate.LETTER_OF_CREDIT_TERMS_BREACHED, False),
                    (SettlementsEvidencePredicate.LETTER_OF_CREDIT_CLOSURE_RULES_BREACHED, False),
                    (SettlementsEvidencePredicate.COLLECTION_ORDER_EXECUTION_BREACHED, False),
                    (SettlementsEvidencePredicate.CHEQUE_REQUISITES_BREACHED, False),
                    (SettlementsEvidencePredicate.CHEQUE_PAYMENT_AND_WARRANTY_BREACHED, False),
                    (
                        SettlementsEvidencePredicate.CHEQUE_NON_PAYMENT_CERTIFICATION_BREACHED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk861-876-settlements-forms-orders-credit-and-collection-v1",
                "synthetic-ru-gk877-885-settlements-cheque-rules-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-settlements-reviewer",
        ),
        storage_evidence=ReviewedStorageEvidence(
            id="reviewed-storage-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                StorageEvidenceAssertion(
                    id=f"storage-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-storage-evidence",),
                )
                for predicate, value in (
                    (StorageEvidencePredicate.THING_ACCEPTED_FOR_STORAGE_AND_RETURN, False),
                    (StorageEvidencePredicate.STORAGE_WRITTEN_FORM_NOT_OBSERVED, False),
                    (
                        StorageEvidencePredicate.ACCEPTANCE_OF_THING_REFUSED_WITHOUT_GROUNDS,
                        False,
                    ),
                    (StorageEvidencePredicate.STORAGE_PERIOD_RULES_BREACHED, False),
                    (StorageEvidencePredicate.SAFEKEEPING_MEASURES_NOT_TAKEN, False),
                    (StorageEvidencePredicate.CUSTODIAN_USED_THING_WITHOUT_CONSENT, False),
                    (StorageEvidencePredicate.STORAGE_CHANGE_OR_TRANSFER_NOT_NOTIFIED, False),
                    (
                        StorageEvidencePredicate.STORAGE_REMUNERATION_AND_EXPENSES_BREACHED,
                        False,
                    ),
                    (StorageEvidencePredicate.THING_RETURN_DUTY_BREACHED, False),
                    (StorageEvidencePredicate.CUSTODIAN_LIABILITY_RULES_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk886-895-storage-concept-form-period-and-safekeeping-v1",
                "synthetic-ru-gk896-906-storage-remuneration-return-and-liability-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-storage-reviewer",
        ),
        warehouse_storage_evidence=ReviewedWarehouseStorageEvidence(
            id="reviewed-warehouse-storage-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                WarehouseStorageEvidenceAssertion(
                    id=f"warehouse-storage-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-warehouse-storage-evidence",),
                )
                for predicate, value in (
                    (
                        WarehouseStorageEvidencePredicate.GOODS_ACCEPTED_BY_WAREHOUSE_FOR_STORAGE,
                        False,
                    ),
                    (
                        WarehouseStorageEvidencePredicate.GENERAL_WAREHOUSE_PUBLIC_DUTY_BREACHED,
                        False,
                    ),
                    (
                        WarehouseStorageEvidencePredicate.GOODS_INSPECTION_ON_ACCEPTANCE_BREACHED,
                        False,
                    ),
                    (
                        WarehouseStorageEvidencePredicate.ACCEPTANCE_DISCREPANCY_NOT_RECORDED,
                        False,
                    ),
                    (WarehouseStorageEvidencePredicate.OWNER_INSPECTION_RIGHTS_BREACHED, False),
                    (
                        WarehouseStorageEvidencePredicate.STORAGE_CONDITIONS_CHANGE_NOT_NOTIFIED,
                        False,
                    ),
                    (
                        WarehouseStorageEvidencePredicate.RETURN_INSPECTION_AND_REPORT_BREACHED,
                        False,
                    ),
                    (WarehouseStorageEvidencePredicate.WAREHOUSE_DOCUMENT_NOT_ISSUED, False),
                    (WarehouseStorageEvidencePredicate.DOUBLE_CERTIFICATE_RULES_BREACHED, False),
                    (
                        WarehouseStorageEvidencePredicate.GOODS_RELEASE_AND_COMMINGLING_RULES_BREACHED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk907-911-warehouse-storage-concept-and-inspection-v1",
                "synthetic-ru-gk912-918-warehouse-documents-and-goods-release-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-warehouse-storage-reviewer",
        ),
        special_storage_evidence=ReviewedSpecialStorageEvidence(
            id="reviewed-special-storage-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                SpecialStorageEvidenceAssertion(
                    id=f"special-storage-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-special-storage-evidence",),
                )
                for predicate, value in (
                    (SpecialStorageEvidencePredicate.SPECIAL_STORAGE_SERVICE_PROVIDED, False),
                    (SpecialStorageEvidencePredicate.PAWNSHOP_STORAGE_RULES_BREACHED, False),
                    (
                        SpecialStorageEvidencePredicate.BANK_VALUABLES_STORAGE_RULES_BREACHED,
                        False,
                    ),
                    (SpecialStorageEvidencePredicate.SAFE_DEPOSIT_BOX_RULES_BREACHED, False),
                    (
                        SpecialStorageEvidencePredicate.TRANSPORT_LOCKER_STORAGE_RULES_BREACHED,
                        False,
                    ),
                    (SpecialStorageEvidencePredicate.LOCKER_OVERDUE_GOODS_RULES_BREACHED, False),
                    (SpecialStorageEvidencePredicate.CLOAKROOM_STORAGE_RULES_BREACHED, False),
                    (SpecialStorageEvidencePredicate.HOTEL_GUEST_PROPERTY_RULES_BREACHED, False),
                    (SpecialStorageEvidencePredicate.SEQUESTRATION_RULES_BREACHED, False),
                    (
                        SpecialStorageEvidencePredicate.SPECIAL_STORAGE_LIABILITY_LIMITS_BREACHED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk919-923-special-storage-pawnshop-bank-and-lockers-v1",
                "synthetic-ru-gk924-926-special-storage-cloakroom-hotel-and-sequestration-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-special-storage-reviewer",
        ),
        insurance_evidence=ReviewedInsuranceEvidence(
            id="reviewed-insurance-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                InsuranceEvidenceAssertion(
                    id=f"insurance-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-insurance-evidence",),
                )
                for predicate, value in (
                    (InsuranceEvidencePredicate.INSURANCE_CONTRACT_CONCLUDED, False),
                    (InsuranceEvidencePredicate.INSURER_NOT_ENTITLED_TO_ACT, False),
                    (InsuranceEvidencePredicate.INSURED_INTEREST_ABSENT_OR_UNLAWFUL, False),
                    (InsuranceEvidencePredicate.INSURANCE_WRITTEN_FORM_NOT_OBSERVED, False),
                    (InsuranceEvidencePredicate.ESSENTIAL_TERMS_NOT_AGREED, False),
                    (InsuranceEvidencePredicate.INSURANCE_RULES_APPLICATION_BREACHED, False),
                    (InsuranceEvidencePredicate.PROPERTY_INSURANCE_SCOPE_BREACHED, False),
                    (InsuranceEvidencePredicate.PERSONAL_INSURANCE_SCOPE_BREACHED, False),
                    (InsuranceEvidencePredicate.BENEFICIARY_RIGHTS_DISREGARDED, False),
                    (InsuranceEvidencePredicate.COMPULSORY_INSURANCE_DUTY_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk927-938-insurance-forms-interests-and-parties-v1",
                "synthetic-ru-gk939-943-insurance-contract-form-and-terms-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-insurance-reviewer",
        ),
        insurance_settlement_evidence=ReviewedInsuranceSettlementEvidence(
            id="reviewed-insurance-settlement-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                InsuranceSettlementEvidenceAssertion(
                    id=f"insurance-settlement-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-insurance-settlement-evidence",),
                )
                for predicate, value in (
                    (
                        InsuranceSettlementEvidencePredicate.INSURED_EVENT_SETTLEMENT_STARTED,
                        False,
                    ),
                    (
                        InsuranceSettlementEvidencePredicate.MATERIAL_INFORMATION_NOT_DISCLOSED,
                        False,
                    ),
                    (InsuranceSettlementEvidencePredicate.INSURED_SUM_RULES_BREACHED, False),
                    (InsuranceSettlementEvidencePredicate.PREMIUM_PAYMENT_RULES_BREACHED, False),
                    (
                        InsuranceSettlementEvidencePredicate.RISK_INCREASE_OR_EARLY_TERMINATION_BREACHED,
                        False,
                    ),
                    (
                        InsuranceSettlementEvidencePredicate.INSURED_EVENT_NOTICE_NOT_GIVEN,
                        False,
                    ),
                    (
                        InsuranceSettlementEvidencePredicate.NOTICE_DELAY_CONSEQUENCES_NOT_APPLIED,
                        False,
                    ),
                    (InsuranceSettlementEvidencePredicate.LOSS_MITIGATION_DUTY_BREACHED, False),
                    (
                        InsuranceSettlementEvidencePredicate.INSURER_RELEASE_GROUNDS_MISAPPLIED,
                        False,
                    ),
                    (
                        InsuranceSettlementEvidencePredicate.SUBROGATION_OR_LIMITATION_RULES_BREACHED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk944-959-insurance-settlement-disclosure-sum-and-premium-v1",
                "synthetic-ru-gk960-970-insurance-settlement-notice-release-and-subrogation-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-insurance-settlement-reviewer",
        ),
        mandate_evidence=ReviewedMandateEvidence(
            id="reviewed-mandate-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                MandateEvidenceAssertion(
                    id=f"mandate-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-mandate-evidence",),
                )
                for predicate, value in (
                    (MandateEvidencePredicate.MANDATE_CONTRACT_CONCLUDED, False),
                    (MandateEvidencePredicate.MANDATE_REMUNERATION_RULES_BREACHED, False),
                    (MandateEvidencePredicate.MANDATE_INSTRUCTIONS_NOT_FOLLOWED, False),
                    (MandateEvidencePredicate.DEVIATION_NOTICE_NOT_GIVEN, False),
                    (MandateEvidencePredicate.ATTORNEY_PERSONAL_PERFORMANCE_BREACHED, False),
                    (MandateEvidencePredicate.ATTORNEY_REPORTING_DUTY_BREACHED, False),
                    (MandateEvidencePredicate.PRINCIPAL_DUTIES_BREACHED, False),
                    (MandateEvidencePredicate.MANDATE_TERMINATION_RULES_BREACHED, False),
                    (MandateEvidencePredicate.TERMINATION_CONSEQUENCES_NOT_APPLIED, False),
                    (MandateEvidencePredicate.SUCCESSOR_DUTIES_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk971-976-mandate-concept-instructions-and-duties-v1",
                "synthetic-ru-gk977-979-mandate-termination-and-consequences-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-mandate-reviewer",
        ),
        negotiorum_gestio_evidence=ReviewedNegotiorumGestioEvidence(
            id="reviewed-negotiorum-gestio-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                NegotiorumGestioEvidenceAssertion(
                    id=f"negotiorum-gestio-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-negotiorum-gestio-evidence",),
                )
                for predicate, value in (
                    (
                        NegotiorumGestioEvidencePredicate.ACTION_IN_ANOTHER_INTEREST_PERFORMED,
                        False,
                    ),
                    (NegotiorumGestioEvidencePredicate.ACTION_CONDITIONS_BREACHED, False),
                    (
                        NegotiorumGestioEvidencePredicate.INTERESTED_PERSON_NOTICE_NOT_GIVEN,
                        False,
                    ),
                    (NegotiorumGestioEvidencePredicate.NOTICE_WAITING_DUTY_BREACHED, False),
                    (NegotiorumGestioEvidencePredicate.APPROVAL_EFFECTS_NOT_APPLIED, False),
                    (NegotiorumGestioEvidencePredicate.DISAPPROVED_ACTION_CONTINUED, False),
                    (NegotiorumGestioEvidencePredicate.NECESSARY_EXPENSES_NOT_REIMBURSED, False),
                    (NegotiorumGestioEvidencePredicate.REMUNERATION_RULES_BREACHED, False),
                    (
                        NegotiorumGestioEvidencePredicate.TRANSACTION_CONSEQUENCES_TRANSFER_BREACHED,
                        False,
                    ),
                    (NegotiorumGestioEvidencePredicate.GESTOR_REPORTING_DUTY_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk980-983-gestio-conditions-notice-and-approval-v1",
                "synthetic-ru-gk984-989-gestio-expenses-remuneration-and-reporting-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-negotiorum-gestio-reviewer",
        ),
        commission_evidence=ReviewedCommissionEvidence(
            id="reviewed-commission-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                CommissionEvidenceAssertion(
                    id=f"commission-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-commission-evidence",),
                )
                for predicate, value in (
                    (CommissionEvidencePredicate.COMMISSION_CONTRACT_CONCLUDED, False),
                    (CommissionEvidencePredicate.COMMISSION_REMUNERATION_RULES_BREACHED, False),
                    (CommissionEvidencePredicate.COMMISSION_INSTRUCTIONS_NOT_FOLLOWED, False),
                    (CommissionEvidencePredicate.DEVIATION_NOTICE_NOT_GIVEN, False),
                    (CommissionEvidencePredicate.THIRD_PARTY_TRANSACTION_RULES_BREACHED, False),
                    (CommissionEvidencePredicate.SUBCOMMISSION_RULES_BREACHED, False),
                    (CommissionEvidencePredicate.PRINCIPAL_PROPERTY_RIGHTS_DISREGARDED, False),
                    (CommissionEvidencePredicate.COMMISSION_REPORT_OR_TRANSFER_BREACHED, False),
                    (
                        CommissionEvidencePredicate.PRINCIPAL_ACCEPTANCE_AND_EXPENSES_BREACHED,
                        False,
                    ),
                    (CommissionEvidencePredicate.COMMISSION_TERMINATION_RULES_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk990-998-commission-concept-execution-and-property-v1",
                "synthetic-ru-gk999-1004-commission-report-duties-and-termination-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-commission-reviewer",
        ),
        agency_evidence=ReviewedAgencyEvidence(
            id="reviewed-agency-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                AgencyEvidenceAssertion(
                    id=f"agency-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-agency-evidence",),
                )
                for predicate, value in (
                    (AgencyEvidencePredicate.AGENCY_CONTRACT_CONCLUDED, False),
                    (AgencyEvidencePredicate.AGENT_ACTING_CAPACITY_MISIDENTIFIED, False),
                    (AgencyEvidencePredicate.AGENCY_REMUNERATION_RULES_BREACHED, False),
                    (AgencyEvidencePredicate.AGENCY_EXCLUSIVITY_RESTRICTIONS_BREACHED, False),
                    (AgencyEvidencePredicate.RESTRICTIONS_AGAINST_CONSUMERS_IMPOSED, False),
                    (AgencyEvidencePredicate.AGENT_REPORT_NOT_SUBMITTED, False),
                    (AgencyEvidencePredicate.REPORT_OBJECTIONS_PERIOD_DISREGARDED, False),
                    (AgencyEvidencePredicate.SUBAGENCY_RULES_BREACHED, False),
                    (AgencyEvidencePredicate.AGENCY_TERMINATION_RULES_BREACHED, False),
                    (AgencyEvidencePredicate.APPLICABLE_RULES_SELECTION_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1005-1008-agency-concept-remuneration-and-reports-v1",
                "synthetic-ru-gk1009-1011-agency-subagency-termination-and-rules-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-agency-reviewer",
        ),
        objects_evidence=ReviewedObjectsEvidence(
            id="reviewed-objects-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ObjectsEvidenceAssertion(
                    id=f"objects-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-objects-evidence",),
                )
                for predicate, value in (
                    (ObjectsEvidencePredicate.OBJECT_OF_RIGHTS_ASSERTED, False),
                    (ObjectsEvidencePredicate.OBJECT_CLASSIFICATION_BREACHED, False),
                    (ObjectsEvidencePredicate.OBJECT_NOT_IN_CIVIL_CIRCULATION, False),
                    (ObjectsEvidencePredicate.IMMOVABLE_CLASSIFICATION_BREACHED, False),
                    (ObjectsEvidencePredicate.DIVISIBILITY_OR_COMPLEX_THING_BREACHED, False),
                    (ObjectsEvidencePredicate.PRINCIPAL_AND_APPURTENANCE_BREACHED, False),
                    (ObjectsEvidencePredicate.FRUITS_PRODUCTS_INCOME_BREACHED, False),
                    (ObjectsEvidencePredicate.MONEY_OR_SECURITIES_RULES_BREACHED, False),
                    (ObjectsEvidencePredicate.INTANGIBLE_BENEFITS_PROTECTION_BREACHED, False),
                    (ObjectsEvidencePredicate.HONOUR_AND_REPUTATION_PROTECTION_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk128-136-objects-circulation-and-kinds-of-things-v1",
                "synthetic-ru-gk140-152-money-securities-and-intangible-benefits-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-objects-reviewer",
        ),
        persons_evidence=ReviewedPersonsEvidence(
            id="reviewed-persons-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                PersonsEvidenceAssertion(
                    id=f"persons-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-persons-evidence",),
                )
                for predicate, value in (
                    (PersonsEvidencePredicate.PARTY_CAPACITY_ASSERTED, False),
                    (PersonsEvidencePredicate.LEGAL_CAPACITY_RULES_BREACHED, False),
                    (PersonsEvidencePredicate.ACTIVE_CAPACITY_AGE_RULES_BREACHED, False),
                    (PersonsEvidencePredicate.INCAPACITY_DECLARED_BY_COURT, False),
                    (PersonsEvidencePredicate.LIMITED_CAPACITY_RULES_BREACHED, False),
                    (PersonsEvidencePredicate.GUARDIANSHIP_CONSENT_MISSING, False),
                    (PersonsEvidencePredicate.CAPACITY_RESTRICTION_BY_AGREEMENT, False),
                    (PersonsEvidencePredicate.ENTITY_CAPACITY_SCOPE_BREACHED, False),
                    (PersonsEvidencePredicate.ENTITY_REGISTRATION_OR_STATUS_BREACHED, False),
                    (PersonsEvidencePredicate.ENTITY_BODY_AUTHORITY_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk17-30-legal-and-active-capacity-of-citizens-v1",
                "synthetic-ru-gk49-53-capacity-registration-and-bodies-of-legal-entities-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-persons-reviewer",
        ),
        terms_evidence=ReviewedTermsEvidence(
            id="reviewed-terms-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                TermsEvidenceAssertion(
                    id=f"terms-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-terms-evidence",),
                )
                for predicate, value in (
                    (TermsEvidencePredicate.TERM_ASSERTED, False),
                    (TermsEvidencePredicate.TERM_DEFINITION_BREACHED, False),
                    (TermsEvidencePredicate.TERM_EVENT_CERTAINTY_BREACHED, False),
                    (TermsEvidencePredicate.TERM_START_RULES_BREACHED, False),
                    (TermsEvidencePredicate.TERM_END_RULES_BREACHED, False),
                    (TermsEvidencePredicate.NON_WORKING_DAY_RULE_BREACHED, False),
                    (TermsEvidencePredicate.LIMITATION_TERM_CALCULATION_BREACHED, False),
                    (TermsEvidencePredicate.PERFORMANCE_DEADLINE_BREACHED, False),
                    (TermsEvidencePredicate.ORGANISATION_OPERATING_HOURS_BREACHED, False),
                    (TermsEvidencePredicate.WRITTEN_NOTICE_DISPATCH_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk190-193-term-definition-start-and-end-v1",
                "synthetic-ru-gk194-actions-on-the-last-day-of-a-term-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-terms-reviewer",
        ),
        meeting_decisions_evidence=ReviewedMeetingDecisionsEvidence(
            id="reviewed-meeting-decisions-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                MeetingDecisionsEvidenceAssertion(
                    id=f"meeting-decisions-evidence-{predicate.value}",
                    predicate=predicate,
                    value=False,
                    source_refs=("synthetic-case-supply-1-meeting-decisions-evidence",),
                )
                for predicate in MeetingDecisionsEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-gk1811-1812-meeting-decision-effect-and-adoption-v1",
                "synthetic-ru-gk1813-1815-meeting-decision-invalidity-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-meeting-decisions-reviewer",
        ),
        messages_evidence=ReviewedMessagesEvidence(
            id="reviewed-messages-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                MessagesEvidenceAssertion(
                    id=f"messages-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-messages-evidence",),
                )
                for predicate, value in (
                    (MessagesEvidencePredicate.MESSAGE_ASSERTED, True),
                    (
                        MessagesEvidencePredicate.CONSEQUENCES_ATTACHED_BY_LAW_OR_TRANSACTION,
                        True,
                    ),
                    (
                        MessagesEvidencePredicate.SENT_TO_STATUTORY_OR_AGREED_ADDRESS,
                        True,
                    ),
                    (MessagesEvidencePredicate.SENDER_AND_ADDRESSEE_IDENTIFIABLE, True),
                    (MessagesEvidencePredicate.FORM_MATCHES_MESSAGE_NATURE, True),
                    (
                        MessagesEvidencePredicate.HANDED_TO_ADDRESSEE_OR_REPRESENTATIVE,
                        True,
                    ),
                    (MessagesEvidencePredicate.ARRIVED_AT_ADDRESSEE, True),
                    (MessagesEvidencePredicate.NON_RECEIPT_DUE_TO_ADDRESSEE, False),
                    (MessagesEvidencePredicate.LAW_SETS_OTHER_DELIVERY_RULE, False),
                    (
                        MessagesEvidencePredicate.TRANSACTION_SETS_OTHER_DELIVERY_RULE,
                        False,
                    ),
                    (
                        MessagesEvidencePredicate.CUSTOM_OR_PRACTICE_SETS_OTHER_DELIVERY_RULE,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1651-legally-significant-messages-v1",
                "synthetic-ru-plenum25-63-67-message-delivery-risk-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-messages-reviewer",
        ),
        special_accounts_evidence=ReviewedSpecialAccountsEvidence(
            id="reviewed-special-accounts-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                SpecialAccountsEvidenceAssertion(
                    id=f"special-accounts-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-special-accounts-evidence",),
                )
                for predicate, value in (
                    (SpecialAccountsEvidencePredicate.SPECIAL_ACCOUNT_ASSERTED, False),
                    (SpecialAccountsEvidencePredicate.NOMINAL_ACCOUNT, False),
                    (SpecialAccountsEvidencePredicate.ESCROW_ACCOUNT, False),
                    (SpecialAccountsEvidencePredicate.PUBLIC_DEPOSIT_ACCOUNT, False),
                    (
                        SpecialAccountsEvidencePredicate.BENEFICIARY_IDENTIFIED_OR_DETERMINABLE,
                        False,
                    ),
                    (SpecialAccountsEvidencePredicate.NOMINAL_FORM_SINGLE_SIGNED_DOCUMENT, False),
                    (SpecialAccountsEvidencePredicate.BANK_CONTROL_DUTY_AGREED, False),
                    (SpecialAccountsEvidencePredicate.BANK_CONTROL_DUTY_NOT_PERFORMED, False),
                    (
                        SpecialAccountsEvidencePredicate.BENEFICIARY_DENIED_ACCOUNT_INFORMATION,
                        False,
                    ),
                    (
                        SpecialAccountsEvidencePredicate.NOMINAL_CHANGE_WITHOUT_BENEFICIARY_CONSENT,
                        False,
                    ),
                    (SpecialAccountsEvidencePredicate.ESCROW_GROUNDS_DEFINED, False),
                    (SpecialAccountsEvidencePredicate.ESCROW_GROUNDS_OCCURRED, False),
                    (SpecialAccountsEvidencePredicate.ESCROW_PAYMENT_TO_BENEFICIARY_DELAYED, False),
                    (SpecialAccountsEvidencePredicate.DISPOSAL_ATTEMPTED_BEFORE_GROUNDS, False),
                    (SpecialAccountsEvidencePredicate.EXTRA_FUNDS_CREDITED_TO_ESCROW, False),
                    (SpecialAccountsEvidencePredicate.ESCROW_TERM_EXPIRED_WITHOUT_GROUNDS, False),
                    (
                        SpecialAccountsEvidencePredicate.ESCROW_BALANCE_WITHHELD_FROM_DEPOSITOR,
                        False,
                    ),
                    (SpecialAccountsEvidencePredicate.HOLDER_AUTHORISED_BY_LAW, False),
                    (SpecialAccountsEvidencePredicate.BANK_MEETS_CAPITAL_REQUIREMENT, False),
                    (SpecialAccountsEvidencePredicate.OWN_FUNDS_CREDITED_TO_PUBLIC_ACCOUNT, False),
                    (SpecialAccountsEvidencePredicate.INTEREST_WITHHELD_FROM_BENEFICIARY, False),
                    (SpecialAccountsEvidencePredicate.SEIZURE_OR_DEBIT_FOR_HOLDER_DEBT, False),
                    (SpecialAccountsEvidencePredicate.SEIZURE_PERMITTED_BY_LAW, False),
                    (
                        SpecialAccountsEvidencePredicate.SEIZURE_FOR_BENEFICIARY_OR_DEPOSITOR_DEBT,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk8601-8606-nominal-account-v1",
                "synthetic-ru-gk8607-86010-escrow-account-v1",
                "synthetic-ru-gk86011-86015-public-deposit-account-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-special-accounts-reviewer",
        ),
        escrow_deposit_evidence=ReviewedEscrowDepositEvidence(
            id="reviewed-escrow-deposit-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                EscrowDepositEvidenceAssertion(
                    id=f"escrow-deposit-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-escrow-deposit-evidence",),
                )
                for predicate, value in (
                    (EscrowDepositEvidencePredicate.ESCROW_DEPOSIT_ASSERTED, False),
                    (EscrowDepositEvidencePredicate.DEPOSITED_THINGS, False),
                    (EscrowDepositEvidencePredicate.DEPOSITED_CASHLESS_MONEY, False),
                    (EscrowDepositEvidencePredicate.DEPOSITED_UNCERTIFICATED_SECURITIES, False),
                    (EscrowDepositEvidencePredicate.DEPOSIT_TERM_MISSING_OR_EXCESSIVE, False),
                    (EscrowDepositEvidencePredicate.NOTARIZATION_PERFORMED, False),
                    (EscrowDepositEvidencePredicate.ESCROW_DEPOSIT_GROUNDS_DEFINED, False),
                    (EscrowDepositEvidencePredicate.GROUNDS_FOR_TRANSFER_OCCURRED, False),
                    (EscrowDepositEvidencePredicate.REMUNERATION_WAIVED_BY_CONTRACT, False),
                    (
                        EscrowDepositEvidencePredicate.REMUNERATION_LIABILITY_SEVERAL_BY_CONTRACT,
                        False,
                    ),
                    (EscrowDepositEvidencePredicate.AGENT_SETOFF_PERMITTED_BY_CONTRACT, False),
                    (
                        EscrowDepositEvidencePredicate.AGENT_WITHHELD_OR_SETOFF_DEPOSITED_PROPERTY,
                        False,
                    ),
                    (EscrowDepositEvidencePredicate.DOCUMENT_CHECK_REQUIRED_BY_CONTRACT, False),
                    (EscrowDepositEvidencePredicate.DOCUMENTS_FACIALLY_DOUBTFUL, False),
                    (
                        EscrowDepositEvidencePredicate.TRANSFER_DESPITE_DOUBT_PERMITTED_BY_CONTRACT,
                        False,
                    ),
                    (
                        EscrowDepositEvidencePredicate.AGENT_TRANSFERRED_PROPERTY_DESPITE_DOUBT,
                        False,
                    ),
                    (EscrowDepositEvidencePredicate.SUBSTANTIVE_CHECK_AGREED_BY_CONTRACT, False),
                    (
                        EscrowDepositEvidencePredicate.AGENT_TRANSFERRED_WITHOUT_VERIFYING_GROUNDS,
                        False,
                    ),
                    (
                        EscrowDepositEvidencePredicate.DEPOSITED_PROPERTY_COMMINGLED_WITH_AGENTS_OWN,
                        False,
                    ),
                    (
                        EscrowDepositEvidencePredicate.USE_OR_DISPOSAL_PERMITTED_BY_CONTRACT_OR_NATURE,
                        False,
                    ),
                    (
                        EscrowDepositEvidencePredicate.AGENT_USED_OR_DISPOSED_DEPOSITED_PROPERTY,
                        False,
                    ),
                    (EscrowDepositEvidencePredicate.THING_LOST_DAMAGED_OR_SHORT, False),
                    (EscrowDepositEvidencePredicate.AGENT_PROVED_FORCE_MAJEURE, False),
                    (
                        EscrowDepositEvidencePredicate.AGENT_PROVED_INHERENT_DEFECT_UNKNOWN_TO_AGENT,
                        False,
                    ),
                    (EscrowDepositEvidencePredicate.AGENT_PROVED_DEPOSITOR_FAULT, False),
                    (
                        EscrowDepositEvidencePredicate.SECURITIES_EXERCISE_PERMITTED_BY_CONTRACT,
                        False,
                    ),
                    (
                        EscrowDepositEvidencePredicate.AGENT_DISPOSED_OR_EXERCISED_RIGHTS_ON_SECURITIES,
                        False,
                    ),
                    (EscrowDepositEvidencePredicate.ESCROW_AGENT_IS_BANK, False),
                    (
                        EscrowDepositEvidencePredicate.SEIZURE_OR_DEBIT_FOR_AGENT_OR_DEPOSITOR_DEBT,
                        False,
                    ),
                    (EscrowDepositEvidencePredicate.SEIZURE_FOR_BENEFICIARY_DEBT, False),
                    (EscrowDepositEvidencePredicate.AGENT_PERSONAL_TERMINATION_GROUND, False),
                    (EscrowDepositEvidencePredicate.DEPOSIT_TERM_EXPIRED, False),
                    (
                        EscrowDepositEvidencePredicate.CONTRACT_TRANSFERRED_UNDER_ARTICLE_392_3,
                        False,
                    ),
                )
            ),
            legal_source_refs=("synthetic-ru-gk9261-9268-escrow-deposit-v1",),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-escrow-deposit-reviewer",
        ),
        bankruptcy_claims_evidence=ReviewedBankruptcyClaimsEvidence(
            id="reviewed-bankruptcy-claims-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                BankruptcyClaimsEvidenceAssertion(
                    id=f"bankruptcy-claims-evidence-{predicate.value}",
                    predicate=predicate,
                    value=False,
                    source_refs=("synthetic-case-supply-1-bankruptcy-claims-evidence",),
                )
                for predicate in BankruptcyClaimsEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-127fz-5-current-payments-v1",
                "synthetic-ru-127fz-63-observation-effects-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-bankruptcy-claims-reviewer",
        ),
        bankruptcy_ranking_evidence=ReviewedBankruptcyRankingEvidence(
            id="reviewed-bankruptcy-ranking-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                BankruptcyRankingEvidenceAssertion(
                    id=f"bankruptcy-ranking-evidence-{predicate.value}",
                    predicate=predicate,
                    value=False,
                    source_refs=("synthetic-case-supply-1-bankruptcy-ranking-evidence",),
                )
                for predicate in BankruptcyRankingEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-127fz-134-creditor-ranking-v1",
                "synthetic-ru-127fz-135-first-rank-claims-v1",
                "synthetic-ru-127fz-138-secured-creditor-claims-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-bankruptcy-ranking-reviewer",
        ),
        bankruptcy_contest_evidence=ReviewedBankruptcyContestEvidence(
            id="reviewed-bankruptcy-contest-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                BankruptcyContestEvidenceAssertion(
                    id=f"bankruptcy-contest-evidence-{predicate.value}",
                    predicate=predicate,
                    value=False,
                    source_refs=("synthetic-case-supply-1-bankruptcy-contest-evidence",),
                )
                for predicate in BankruptcyContestEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-127fz-61.1-contest-transactions-general-v1",
                "synthetic-ru-127fz-61.2-contest-suspicious-transaction-v1",
                "synthetic-ru-127fz-61.3-contest-preference-transaction-v1",
                "synthetic-ru-127fz-61.9-contest-standing-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-bankruptcy-contest-reviewer",
        ),
        bankruptcy_setoff_evidence=ReviewedBankruptcySetoffEvidence(
            id="reviewed-bankruptcy-setoff-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                BankruptcySetoffEvidenceAssertion(
                    id=f"bankruptcy-setoff-evidence-{predicate.value}",
                    predicate=predicate,
                    value=False,
                    source_refs=("synthetic-case-supply-1-bankruptcy-setoff-evidence",),
                )
                for predicate in BankruptcySetoffEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-127fz-63-observation-effects-v1",
                "synthetic-ru-127fz-134-creditor-ranking-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-bankruptcy-setoff-reviewer",
        ),
        attribution_delay_evidence=ReviewedAttributionDelayEvidence(
            id="reviewed-attribution-delay-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                AttributionDelayEvidenceAssertion(
                    id=f"attribution-delay-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-attribution-delay-evidence",),
                )
                for predicate, value in (
                    (AttributionDelayEvidencePredicate.OBLIGATION_BREACH_ASSERTED, True),
                    (
                        AttributionDelayEvidencePredicate.BREACH_CAUSED_BY_DEBTOR_EMPLOYEES,
                        False,
                    ),
                    (
                        AttributionDelayEvidencePredicate.PERFORMANCE_ENTRUSTED_TO_THIRD_PARTY,
                        False,
                    ),
                    (AttributionDelayEvidencePredicate.THIRD_PARTY_CAUSED_BREACH, False),
                    (
                        AttributionDelayEvidencePredicate.LAW_ASSIGNS_LIABILITY_TO_PERFORMER,
                        False,
                    ),
                    (
                        AttributionDelayEvidencePredicate.CREDITOR_FAULT_CONTRIBUTED_TO_BREACH,
                        False,
                    ),
                    (AttributionDelayEvidencePredicate.CREDITOR_FAILED_TO_MITIGATE_LOSS, False),
                    (AttributionDelayEvidencePredicate.DEBTOR_DELAY_ESTABLISHED, False),
                    (
                        AttributionDelayEvidencePredicate.PERFORMANCE_LOST_INTEREST_FOR_CREDITOR,
                        False,
                    ),
                    (AttributionDelayEvidencePredicate.CREDITOR_DELAY_ESTABLISHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk402-404-attribution-of-liability-and-creditor-fault-v1",
                "synthetic-ru-gk405-406-delay-of-the-debtor-and-of-the-creditor-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-attribution-delay-reviewer",
        ),
        transactions_evidence=ReviewedTransactionsEvidence(
            id="reviewed-transactions-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                TransactionsEvidenceAssertion(
                    id=f"transactions-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-transactions-evidence",),
                )
                for predicate, value in (
                    (TransactionsEvidencePredicate.TRANSACTION_ASSERTED, False),
                    (TransactionsEvidencePredicate.TRANSACTION_DEFINITION_BREACHED, False),
                    (TransactionsEvidencePredicate.PARTIES_COUNT_RULES_BREACHED, False),
                    (TransactionsEvidencePredicate.UNILATERAL_TRANSACTION_EFFECT_BREACHED, False),
                    (TransactionsEvidencePredicate.UNILATERAL_REGULATION_BREACHED, False),
                    (TransactionsEvidencePredicate.CONDITIONAL_TRANSACTION_RULES_BREACHED, False),
                    (TransactionsEvidencePredicate.CONDITION_INTERFERENCE_IN_BAD_FAITH, False),
                    (TransactionsEvidencePredicate.STATUTORY_CONSENT_NOT_OBTAINED, False),
                    (TransactionsEvidencePredicate.CONSENT_PROCEDURE_BREACHED, False),
                    (TransactionsEvidencePredicate.SILENCE_TREATED_AS_CONSENT, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk153-157-transaction-concept-kinds-and-conditions-v1",
                "synthetic-ru-gk157-1-consent-to-a-transaction-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-transactions-reviewer",
        ),
        civil_principles_evidence=ReviewedCivilPrinciplesEvidence(
            id="reviewed-civil-principles-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                CivilPrinciplesEvidenceAssertion(
                    id=f"civil-principles-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-civil-principles-evidence",),
                )
                for predicate, value in (
                    (CivilPrinciplesEvidencePredicate.CIVIL_RIGHTS_EXERCISE_ASSERTED, False),
                    (CivilPrinciplesEvidencePredicate.GOOD_FAITH_PRINCIPLE_BREACHED, False),
                    (
                        CivilPrinciplesEvidencePredicate.EQUALITY_OR_FREEDOM_PRINCIPLE_BREACHED,
                        False,
                    ),
                    (CivilPrinciplesEvidencePredicate.RIGHTS_ARISING_GROUNDS_BREACHED, False),
                    (CivilPrinciplesEvidencePredicate.ABUSE_OF_RIGHT_ESTABLISHED, False),
                    (CivilPrinciplesEvidencePredicate.PROTECTION_REFUSAL_NOT_APPLIED, False),
                    (CivilPrinciplesEvidencePredicate.PROTECTION_METHODS_BREACHED, False),
                    (CivilPrinciplesEvidencePredicate.SELF_HELP_LIMITS_BREACHED, False),
                    (
                        CivilPrinciplesEvidencePredicate.DAMAGES_COMPENSATION_RULES_BREACHED,
                        False,
                    ),
                    (
                        CivilPrinciplesEvidencePredicate.PUBLIC_AUTHORITY_LIABILITY_BREACHED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1-10-civil-principles-and-limits-of-exercise-v1",
                "synthetic-ru-gk12-16-1-protection-methods-damages-and-authority-liability-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-civil-principles-reviewer",
        ),
        property_rights_evidence=ReviewedPropertyRightsEvidence(
            id="reviewed-property-rights-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                PropertyRightsEvidenceAssertion(
                    id=f"property-rights-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-property-rights-evidence",),
                )
                for predicate, value in (
                    (PropertyRightsEvidencePredicate.PROPERTY_RIGHT_ASSERTED, False),
                    (PropertyRightsEvidencePredicate.OWNERSHIP_POWERS_BREACHED, False),
                    (PropertyRightsEvidencePredicate.DISPOSAL_BY_NON_OWNER_DETECTED, False),
                    (PropertyRightsEvidencePredicate.RISK_AND_BURDEN_RULES_BREACHED, False),
                    (PropertyRightsEvidencePredicate.ACQUISITION_MOMENT_RULES_BREACHED, False),
                    (PropertyRightsEvidencePredicate.ACQUISITIVE_PRESCRIPTION_BREACHED, False),
                    (PropertyRightsEvidencePredicate.COMMON_PROPERTY_RULES_BREACHED, False),
                    (PropertyRightsEvidencePredicate.VINDICATION_RULES_BREACHED, False),
                    (
                        PropertyRightsEvidencePredicate.GOOD_FAITH_PURCHASER_PROTECTION_DISREGARDED,
                        False,
                    ),
                    (
                        PropertyRightsEvidencePredicate.NEGATORY_OR_POSSESSOR_CLAIM_BREACHED,
                        False,
                    ),
                    (
                        PropertyRightsEvidencePredicate.OWNERSHIP_TERMINATED_BY_FEDERAL_LAW,
                        False,
                    ),
                    (
                        PropertyRightsEvidencePredicate.LOSSES_FROM_STATUTORY_TERMINATION_PROVEN,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk209-234-ownership-content-acquisition-and-prescription-v1",
                "synthetic-ru-gk244-305-common-property-and-protection-of-rights-v1",
                "synthetic-ru-gk306-statutory-termination-compensation-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-property-rights-reviewer",
        ),
        representation_evidence=ReviewedRepresentationEvidence(
            id="reviewed-representation-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                RepresentationEvidenceAssertion(
                    id=f"representation-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-representation-evidence",),
                )
                for predicate, value in (
                    (RepresentationEvidencePredicate.REPRESENTATION_RELATION_ESTABLISHED, False),
                    (RepresentationEvidencePredicate.AUTHORITY_BASIS_INVALID, False),
                    (RepresentationEvidencePredicate.PROHIBITED_SELF_DEALING, False),
                    (
                        RepresentationEvidencePredicate.COMMERCIAL_REPRESENTATION_RULES_BREACHED,
                        False,
                    ),
                    (RepresentationEvidencePredicate.POWER_OF_ATTORNEY_FORM_BREACHED, False),
                    (RepresentationEvidencePredicate.POWER_OF_ATTORNEY_TERM_BREACHED, False),
                    (RepresentationEvidencePredicate.SUBSTITUTION_RULES_BREACHED, False),
                    (RepresentationEvidencePredicate.TERMINATION_OR_NOTICE_BREACHED, False),
                    (
                        RepresentationEvidencePredicate.UNAUTHORIZED_ACT_WITHOUT_RATIFICATION,
                        False,
                    ),
                    (RepresentationEvidencePredicate.RATIFICATION_EFFECT_DISREGARDED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk182-184-representation-authority-and-limits-v1",
                "synthetic-ru-gk185-189-power-of-attorney-form-term-and-termination-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-representation-reviewer",
        ),
        unjust_enrichment_evidence=ReviewedUnjustEnrichmentEvidence(
            id="reviewed-unjust-enrichment-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                UnjustEnrichmentEvidenceAssertion(
                    id=f"unjust-enrichment-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-unjust-enrichment-evidence",),
                )
                for predicate, value in (
                    (UnjustEnrichmentEvidencePredicate.UNJUST_ENRICHMENT_ESTABLISHED, False),
                    (UnjustEnrichmentEvidencePredicate.RESTITUTION_DUTY_BREACHED, False),
                    (UnjustEnrichmentEvidencePredicate.IRRELEVANCE_OF_CAUSE_DISREGARDED, False),
                    (
                        UnjustEnrichmentEvidencePredicate.SUBSIDIARY_APPLICATION_RULES_BREACHED,
                        False,
                    ),
                    (UnjustEnrichmentEvidencePredicate.RETURN_IN_KIND_RULES_BREACHED, False),
                    (UnjustEnrichmentEvidencePredicate.VALUE_COMPENSATION_RULES_BREACHED, False),
                    (
                        UnjustEnrichmentEvidencePredicate.TRANSFERRED_RIGHT_RESTORATION_BREACHED,
                        False,
                    ),
                    (UnjustEnrichmentEvidencePredicate.INCOME_AND_INTEREST_RULES_BREACHED, False),
                    (
                        UnjustEnrichmentEvidencePredicate.MAINTENANCE_COSTS_REIMBURSEMENT_BREACHED,
                        False,
                    ),
                    (
                        UnjustEnrichmentEvidencePredicate.NON_RETURNABLE_ENRICHMENT_NOT_APPLIED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1102-1105-unjust-enrichment-duty-and-return-v1",
                "synthetic-ru-gk1106-1109-unjust-enrichment-income-costs-and-exceptions-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-unjust-enrichment-reviewer",
        ),
        moral_harm_evidence=ReviewedMoralHarmEvidence(
            id="reviewed-moral-harm-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                MoralHarmEvidenceAssertion(
                    id=f"moral-harm-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-moral-harm-evidence",),
                )
                for predicate, value in (
                    (MoralHarmEvidencePredicate.MORAL_HARM_CLAIM_ESTABLISHED, False),
                    (MoralHarmEvidencePredicate.NON_MATERIAL_BENEFITS_SCOPE_BREACHED, False),
                    (
                        MoralHarmEvidencePredicate.PROPERTY_RIGHTS_COMPENSATION_LIMITS_BREACHED,
                        False,
                    ),
                    (
                        MoralHarmEvidencePredicate.INDEPENDENT_FROM_PROPERTY_DAMAGE_BREACHED,
                        False,
                    ),
                    (MoralHarmEvidencePredicate.NO_FAULT_GROUNDS_DISREGARDED, False),
                    (MoralHarmEvidencePredicate.HIGH_RISK_SOURCE_GROUND_BREACHED, False),
                    (MoralHarmEvidencePredicate.UNLAWFUL_PROSECUTION_GROUND_BREACHED, False),
                    (MoralHarmEvidencePredicate.DEFAMATION_GROUND_BREACHED, False),
                    (MoralHarmEvidencePredicate.COMPENSATION_FORM_OR_AMOUNT_BREACHED, False),
                    (MoralHarmEvidencePredicate.VICTIM_INDIVIDUAL_FEATURES_DISREGARDED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1099-1100-moral-harm-grounds-and-no-fault-cases-v1",
                "synthetic-ru-gk1101-moral-harm-form-and-amount-of-compensation-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-moral-harm-reviewer",
        ),
        product_liability_evidence=ReviewedProductLiabilityEvidence(
            id="reviewed-product-liability-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ProductLiabilityEvidenceAssertion(
                    id=f"product-liability-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-product-liability-evidence",),
                )
                for predicate, value in (
                    (
                        ProductLiabilityEvidencePredicate.PRODUCT_OR_SERVICE_DEFECT_HARM_ESTABLISHED,
                        False,
                    ),
                    (
                        ProductLiabilityEvidencePredicate.COMPENSATION_REGARDLESS_OF_FAULT_BREACHED,
                        False,
                    ),
                    (
                        ProductLiabilityEvidencePredicate.CONSUMER_PURPOSE_REQUIREMENT_BREACHED,
                        False,
                    ),
                    (ProductLiabilityEvidencePredicate.LIABLE_PERSON_CHOICE_BREACHED, False),
                    (
                        ProductLiabilityEvidencePredicate.WORK_OR_SERVICE_PROVIDER_LIABILITY_BREACHED,
                        False,
                    ),
                    (ProductLiabilityEvidencePredicate.INFORMATION_LIABILITY_BREACHED, False),
                    (
                        ProductLiabilityEvidencePredicate.SERVICE_LIFE_PERIOD_RULES_BREACHED,
                        False,
                    ),
                    (
                        ProductLiabilityEvidencePredicate.SERVICE_LIFE_ABSENCE_EXCEPTION_DISREGARDED,
                        False,
                    ),
                    (ProductLiabilityEvidencePredicate.EXCULPATION_GROUNDS_BREACHED, False),
                    (
                        ProductLiabilityEvidencePredicate.VICTIM_RULES_VIOLATION_NOT_APPLIED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1095-1096-product-defect-harm-and-liable-persons-v1",
                "synthetic-ru-gk1097-1098-product-liability-periods-and-exculpation-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-product-liability-reviewer",
        ),
        tort_life_health_evidence=ReviewedTortLifeHealthEvidence(
            id="reviewed-tort-life-health-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                TortLifeHealthEvidenceAssertion(
                    id=f"tort-life-health-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-tort-life-health-evidence",),
                )
                for predicate, value in (
                    (TortLifeHealthEvidencePredicate.LIFE_OR_HEALTH_HARM_ESTABLISHED, False),
                    (TortLifeHealthEvidencePredicate.HARM_SCOPE_RULES_BREACHED, False),
                    (TortLifeHealthEvidencePredicate.LOST_EARNINGS_CALCULATION_BREACHED, False),
                    (TortLifeHealthEvidencePredicate.MINOR_VICTIM_RULES_BREACHED, False),
                    (TortLifeHealthEvidencePredicate.DEPENDANTS_ENTITLEMENT_BREACHED, False),
                    (TortLifeHealthEvidencePredicate.DEPENDANTS_PAYMENT_AMOUNT_BREACHED, False),
                    (TortLifeHealthEvidencePredicate.COMPENSATION_ADJUSTMENT_BREACHED, False),
                    (TortLifeHealthEvidencePredicate.INDEXATION_NOT_APPLIED, False),
                    (
                        TortLifeHealthEvidencePredicate.PAYMENT_ORDER_OR_SUCCESSION_BREACHED,
                        False,
                    ),
                    (TortLifeHealthEvidencePredicate.FUNERAL_EXPENSES_RULES_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1084-1087-life-health-harm-scope-and-earnings-v1",
                "synthetic-ru-gk1088-1094-dependants-indexation-and-funeral-expenses-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-tort-life-health-reviewer",
        ),
        tort_general_evidence=ReviewedTortGeneralEvidence(
            id="reviewed-tort-general-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                TortGeneralEvidenceAssertion(
                    id=f"tort-general-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-tort-general-evidence",),
                )
                for predicate, value in (
                    (TortGeneralEvidencePredicate.HARM_CAUSED_ESTABLISHED, False),
                    (TortGeneralEvidencePredicate.FULL_COMPENSATION_RULE_BREACHED, False),
                    (TortGeneralEvidencePredicate.FAULT_PRESUMPTION_BREACHED, False),
                    (
                        TortGeneralEvidencePredicate.LAWFUL_OR_DEFENSIVE_HARM_RULES_BREACHED,
                        False,
                    ),
                    (TortGeneralEvidencePredicate.LIABILITY_FOR_OTHERS_BREACHED, False),
                    (TortGeneralEvidencePredicate.HIGH_RISK_SOURCE_LIABILITY_BREACHED, False),
                    (TortGeneralEvidencePredicate.JOINT_LIABILITY_AND_RECOURSE_BREACHED, False),
                    (TortGeneralEvidencePredicate.COMPENSATION_METHOD_OR_AMOUNT_BREACHED, False),
                    (
                        TortGeneralEvidencePredicate.VICTIM_FAULT_OR_CAUSER_MEANS_DISREGARDED,
                        False,
                    ),
                    (TortGeneralEvidencePredicate.GROSS_NEGLIGENCE_REDUCTION_NOT_APPLIED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1064-1070-tort-general-grounds-and-liability-for-others-v1",
                "synthetic-ru-gk1073-1083-tort-high-risk-source-recourse-and-victim-fault-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-tort-general-reviewer",
        ),
        games_evidence=ReviewedGamesEvidence(
            id="reviewed-games-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                GamesEvidenceAssertion(
                    id=f"games-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-games-evidence",),
                )
                for predicate, value in (
                    (GamesEvidencePredicate.GAMES_OR_BETTING_RELATION_ESTABLISHED, False),
                    (GamesEvidencePredicate.JUDICIAL_PROTECTION_EXCLUSION_BREACHED, False),
                    (GamesEvidencePredicate.COERCION_EXCEPTION_DISREGARDED, False),
                    (
                        GamesEvidencePredicate.DERIVATIVE_TRANSACTIONS_PROTECTION_BREACHED,
                        False,
                    ),
                    (GamesEvidencePredicate.ORGANIZER_STATUS_OR_LICENCE_BREACHED, False),
                    (GamesEvidencePredicate.GAME_CONTRACT_FORM_BREACHED, False),
                    (GamesEvidencePredicate.GAME_PARTICIPATION_RULES_BREACHED, False),
                    (GamesEvidencePredicate.PRIZE_TERMS_ANNOUNCEMENT_BREACHED, False),
                    (GamesEvidencePredicate.PRIZE_PAYMENT_PERIOD_BREACHED, False),
                    (GamesEvidencePredicate.PAYMENT_REFUSAL_DAMAGES_NOT_APPLIED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1062-judicial-protection-of-claims-from-games-and-betting-v1",
                "synthetic-ru-gk1063-organization-of-lotteries-and-payment-of-winnings-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-games-reviewer",
        ),
        public_promise_evidence=ReviewedPublicPromiseEvidence(
            id="reviewed-public-promise-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                PublicPromiseEvidenceAssertion(
                    id=f"public-promise-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-public-promise-evidence",),
                )
                for predicate, value in (
                    (PublicPromiseEvidencePredicate.PUBLIC_PROMISE_OR_CONTEST_DECLARED, False),
                    (
                        PublicPromiseEvidencePredicate.PROMISE_ANNOUNCEMENT_REQUIREMENTS_BREACHED,
                        False,
                    ),
                    (
                        PublicPromiseEvidencePredicate.REWARD_AMOUNT_OR_DISTRIBUTION_BREACHED,
                        False,
                    ),
                    (PublicPromiseEvidencePredicate.PROMISE_REVOCATION_RULES_BREACHED, False),
                    (
                        PublicPromiseEvidencePredicate.REVOCATION_EXPENSE_COMPENSATION_NOT_APPLIED,
                        False,
                    ),
                    (PublicPromiseEvidencePredicate.CONTEST_ANNOUNCEMENT_TERMS_BREACHED, False),
                    (PublicPromiseEvidencePredicate.CONTEST_PUBLIC_PURPOSE_BREACHED, False),
                    (
                        PublicPromiseEvidencePredicate.CONTEST_CHANGE_OR_CANCELLATION_BREACHED,
                        False,
                    ),
                    (PublicPromiseEvidencePredicate.CONTEST_AWARD_DECISION_BREACHED, False),
                    (PublicPromiseEvidencePredicate.CONTEST_WORKS_RETURN_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1055-1056-public-promise-of-reward-and-revocation-v1",
                "synthetic-ru-gk1057-1061-public-contest-terms-award-and-works-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-public-promise-reviewer",
        ),
        partnership_evidence=ReviewedPartnershipEvidence(
            id="reviewed-partnership-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                PartnershipEvidenceAssertion(
                    id=f"partnership-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-partnership-evidence",),
                )
                for predicate, value in (
                    (PartnershipEvidencePredicate.PARTNERSHIP_CONTRACT_CONCLUDED, False),
                    (PartnershipEvidencePredicate.PARTNERSHIP_PARTIES_OR_PURPOSE_BREACHED, False),
                    (
                        PartnershipEvidencePredicate.CONTRIBUTIONS_OR_COMMON_PROPERTY_BREACHED,
                        False,
                    ),
                    (PartnershipEvidencePredicate.COMMON_AFFAIRS_CONDUCT_BREACHED, False),
                    (PartnershipEvidencePredicate.INFORMATION_OR_EXPENSE_SHARING_BREACHED, False),
                    (PartnershipEvidencePredicate.PARTNERS_LIABILITY_RULES_BREACHED, False),
                    (PartnershipEvidencePredicate.PROFIT_DISTRIBUTION_RULES_BREACHED, False),
                    (PartnershipEvidencePredicate.PROFIT_EXCLUSION_VOID_NOT_APPLIED, False),
                    (
                        PartnershipEvidencePredicate.TERMINATION_OR_WITHDRAWAL_RULES_BREACHED,
                        False,
                    ),
                    (PartnershipEvidencePredicate.UNDISCLOSED_PARTNERSHIP_RULES_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1041-1046-partnership-concept-contributions-and-common-affairs-v1",
                "synthetic-ru-gk1047-1054-partnership-liability-profit-and-termination-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-partnership-reviewer",
        ),
        franchise_evidence=ReviewedFranchiseEvidence(
            id="reviewed-franchise-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                FranchiseEvidenceAssertion(
                    id=f"franchise-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-franchise-evidence",),
                )
                for predicate, value in (
                    (FranchiseEvidencePredicate.FRANCHISE_CONTRACT_CONCLUDED, False),
                    (FranchiseEvidencePredicate.FRANCHISE_SCOPE_OR_PARTIES_BREACHED, False),
                    (FranchiseEvidencePredicate.FRANCHISE_FORM_OR_REGISTRATION_BREACHED, False),
                    (FranchiseEvidencePredicate.FORM_INVALIDITY_NOT_APPLIED, False),
                    (FranchiseEvidencePredicate.COMMERCIAL_SUBCONCESSION_RULES_BREACHED, False),
                    (FranchiseEvidencePredicate.FRANCHISE_REMUNERATION_RULES_BREACHED, False),
                    (FranchiseEvidencePredicate.RIGHTHOLDER_OBLIGATIONS_BREACHED, False),
                    (FranchiseEvidencePredicate.USER_OBLIGATIONS_BREACHED, False),
                    (FranchiseEvidencePredicate.FRANCHISE_RESTRICTIONS_RULES_BREACHED, False),
                    (FranchiseEvidencePredicate.LIABILITY_OR_TERMINATION_RULES_BREACHED, False),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1027-1029-franchise-concept-form-and-subconcession-v1",
                "synthetic-ru-gk1030-1040-franchise-obligations-restrictions-and-termination-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-franchise-reviewer",
        ),
        trust_management_evidence=ReviewedTrustManagementEvidence(
            id="reviewed-trust-management-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                TrustManagementEvidenceAssertion(
                    id=f"trust-management-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-trust-management-evidence",),
                )
                for predicate, value in (
                    (
                        TrustManagementEvidencePredicate.TRUST_MANAGEMENT_CONTRACT_CONCLUDED,
                        False,
                    ),
                    (TrustManagementEvidencePredicate.TRUST_PROPERTY_SCOPE_BREACHED, False),
                    (TrustManagementEvidencePredicate.TRUSTEE_STATUS_INVALID, False),
                    (TrustManagementEvidencePredicate.ESSENTIAL_TERMS_OR_FORM_BREACHED, False),
                    (TrustManagementEvidencePredicate.FORM_INVALIDITY_NOT_APPLIED, False),
                    (TrustManagementEvidencePredicate.PROPERTY_SEPARATION_BREACHED, False),
                    (TrustManagementEvidencePredicate.ENCUMBERED_PROPERTY_NOTICE_BREACHED, False),
                    (TrustManagementEvidencePredicate.TRUSTEE_RIGHTS_AND_REPORT_BREACHED, False),
                    (TrustManagementEvidencePredicate.TRUSTEE_LIABILITY_RULES_BREACHED, False),
                    (
                        TrustManagementEvidencePredicate.REMUNERATION_OR_TERMINATION_RULES_BREACHED,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk1012-1019-trust-management-concept-terms-and-property-v1",
                "synthetic-ru-gk1020-1026-trust-management-duties-liability-and-termination-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-trust-management-reviewer",
        ),
        invalidity_evidence=ReviewedInvalidityEvidence(
            id="reviewed-invalidity-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                InvalidityEvidenceAssertion(
                    id=f"invalidity-evidence-{predicate.value}",
                    predicate=predicate,
                    value=invalidity_values[predicate],
                    source_refs=("synthetic-case-supply-1-invalidity-evidence",),
                )
                for predicate in InvalidityEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-gk166-168-invalidity-framework-v1",
                "synthetic-ru-gk169-172-void-transactions-v1",
                "synthetic-ru-gk173-179-voidable-transactions-v1",
                "synthetic-ru-gk180-181-invalidity-effects-v1",
                "synthetic-ru-gk4311-entrepreneurial-estoppel-v1",
                "synthetic-ru-plenum25-invalidity-guidance-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-invalidity-reviewer",
        ),
        security_evidence=ReviewedSecurityEvidence(
            id="reviewed-security-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                SecurityEvidenceAssertion(
                    id=f"security-evidence-{predicate.value}",
                    predicate=predicate,
                    value=security_values[predicate],
                    source_refs=("synthetic-case-supply-1-security-evidence",),
                )
                for predicate in SecurityEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-gk329-333-security-framework-v1",
                "synthetic-ru-gk334-360-pledge-retention-v1",
                "synthetic-ru-gk361-367-suretyship-v1",
                "synthetic-ru-gk368-379-independent-guarantee-v1",
                "synthetic-ru-gk380-3812-deposit-security-payment-v1",
                "synthetic-ru-plenum54-security-guidance-v1",
                "synthetic-ru-plenum23-pledge-guidance-v1",
                "synthetic-ru-plenum45-suretyship-guidance-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-security-reviewer",
        ),
        obligation_dynamics_evidence=ReviewedObligationDynamicsEvidence(
            id="reviewed-obligation-dynamics-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                ObligationDynamicsEvidenceAssertion(
                    id=f"obligation-dynamics-evidence-{predicate.value}",
                    predicate=predicate,
                    value=dynamics_values[predicate],
                    source_refs=("synthetic-case-supply-1-obligation-dynamics-evidence",),
                )
                for predicate in ObligationDynamicsEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-gk382-390-assignment-v1",
                "synthetic-ru-gk391-3923-debt-transfer-v1",
                "synthetic-ru-gk407-413-discharge-v1",
                "synthetic-ru-gk414-419-discharge-v1",
                "synthetic-ru-plenum54-party-change-guidance-v1",
                "synthetic-ru-plenum6-discharge-guidance-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-obligation-dynamics-reviewer",
        ),
        performance_remedies_evidence=ReviewedPerformanceRemediesEvidence(
            id="reviewed-performance-remedies-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                PerformanceRemediesEvidenceAssertion(
                    id=f"performance-remedies-evidence-{predicate.value}",
                    predicate=predicate,
                    value=performance_remedies_values[predicate],
                    source_refs=("synthetic-case-supply-1-performance-remedies-evidence",),
                )
                for predicate in PerformanceRemediesEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-gk309-328-performance-v1",
                "synthetic-ru-gk393-4061-remedies-v1",
                "synthetic-ru-plenum54-performance-guidance-v1",
                "synthetic-ru-plenum7-remedies-guidance-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-performance-remedies-reviewer",
        ),
        sale_evidence=ReviewedSaleEvidence(
            id="reviewed-general-sale-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                SaleEvidenceAssertion(
                    id=f"general-sale-evidence-{predicate.value}",
                    predicate=predicate,
                    value=sale_values[predicate],
                    source_refs=("synthetic-case-supply-1-general-sale-evidence",),
                )
                for predicate in SaleEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-gk454-464-sale-transfer-v1",
                "synthetic-ru-gk465-477-sale-conformity-v1",
                "synthetic-ru-gk478-491-sale-payment-v1",
                "synthetic-ru-vs-review2024-sale-quality-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-general-sale-reviewer",
        ),
        supply_evidence=ReviewedSupplyEvidence(
            id="reviewed-special-supply-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                SupplyEvidenceAssertion(
                    id=f"special-supply-evidence-{predicate.value}",
                    predicate=predicate,
                    value=supply_values[predicate],
                    source_refs=("synthetic-case-supply-1-special-supply-evidence",),
                )
                for predicate in SupplyEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-gk506-512-supply-framework-v1",
                "synthetic-ru-gk513-517-supply-acceptance-v1",
                "synthetic-ru-gk518-524-supply-remedies-v1",
                "synthetic-ru-plenum18-supply-guidance-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-special-supply-reviewer",
        ),
        termination_evidence=ReviewedTerminationEvidence(
            id="reviewed-termination-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                TerminationEvidenceAssertion(
                    id=f"termination-evidence-{predicate.value}",
                    predicate=predicate,
                    value=termination_values[predicate],
                    source_refs=("synthetic-case-supply-1-termination-evidence",),
                )
                for predicate in TerminationEvidencePredicate
            ),
            legal_source_refs=(
                "synthetic-ru-gk450-453-termination-model-v1",
                "synthetic-ru-gk310-4501-unilateral-model-v1",
                "synthetic-ru-plenum54-unilateral-guidance-v1",
                "synthetic-ru-plenum18-pretrial-guidance-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-termination-reviewer",
        ),
        liability_evidence=ReviewedLiabilityEvidence(
            id="reviewed-liability-evidence-supply-1-v0",
            case_id="case-supply-1",
            assertions=tuple(
                LiabilityEvidenceAssertion(
                    id=f"liability-evidence-{predicate.value}",
                    predicate=predicate,
                    value=value,
                    source_refs=("synthetic-case-supply-1-liability-evidence",),
                )
                for predicate, value in (
                    (LiabilityEvidencePredicate.BREACH_ESTABLISHED, True),
                    (LiabilityEvidencePredicate.DEBTOR_ACTING_IN_BUSINESS, True),
                    (LiabilityEvidencePredicate.FAULT_REBUTTAL_ASSERTED, True),
                    (LiabilityEvidencePredicate.REASONABLE_CARE_PROVEN, False),
                    (LiabilityEvidencePredicate.ALL_REASONABLE_MEASURES_PROVEN, False),
                    (LiabilityEvidencePredicate.FORCE_MAJEURE_CLAIMED, True),
                    (LiabilityEvidencePredicate.EXTRAORDINARY_EVENT_PROVEN, False),
                    (LiabilityEvidencePredicate.UNAVOIDABLE_EVENT_PROVEN, False),
                    (LiabilityEvidencePredicate.BEYOND_DEBTOR_CONTROL_PROVEN, False),
                    (LiabilityEvidencePredicate.FORCE_MAJEURE_CAUSAL_LINK_PROVEN, False),
                    (LiabilityEvidencePredicate.EXCLUDED_COMMERCIAL_RISK_ONLY, True),
                    (LiabilityEvidencePredicate.NOTICE_AND_MITIGATION_PROVEN, False),
                    (LiabilityEvidencePredicate.INTENTIONAL_BREACH, False),
                    (
                        LiabilityEvidencePredicate.ADVANCE_LIABILITY_EXCLUSION_CLAUSE,
                        False,
                    ),
                    (LiabilityEvidencePredicate.PENALTY_CLAIMED, True),
                    (LiabilityEvidencePredicate.CONTRACTUAL_PENALTY, True),
                    (LiabilityEvidencePredicate.PENALTY_REDUCTION_REQUESTED, True),
                    (
                        LiabilityEvidencePredicate.MANIFEST_DISPROPORTIONALITY_PROVEN,
                        True,
                    ),
                    (
                        LiabilityEvidencePredicate.UNJUSTIFIED_BENEFIT_RISK_PROVEN,
                        False,
                    ),
                    (
                        LiabilityEvidencePredicate.ONLY_EXCLUDED_REDUCTION_REASONS,
                        False,
                    ),
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk401-liability-model-v1",
                "synthetic-ru-gk333-penalty-model-v1",
                "synthetic-ru-plenum7-liability-guidance-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-liability-reviewer",
        ),
    )


def build_synthetic_supply_analysis_artifact(
    counterfactual_budget: CounterfactualBudget | None = None,
) -> ReviewedContractAnalysisArtifact:
    sources = build_synthetic_supply_analysis_sources()
    request = build_synthetic_supply_analysis_request()
    return ReviewedContractAnalysisArtifact(
        disclaimer=(
            "Синтетический артефакт анализа проверенных входных данных. "
            "Не готов к промышленной эксплуатации и не является юридической консультацией."
        ),
        sources=sources,
        request=request,
        result=run_reviewed_contract_analysis(
            request,
            sources,
            counterfactual_budget=counterfactual_budget,
        ),
    )
