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
    "synthetic-case-supply-1-freedom-evidence",
    "synthetic-ru-gk445-446-mandatory-conclusion-v1",
    "synthetic-ru-gk447-449-auction-v1",
    "synthetic-case-supply-1-procedure-evidence",
    "synthetic-ru-gk166-168-invalidity-framework-v1",
    "synthetic-ru-gk169-172-void-transactions-v1",
    "synthetic-ru-gk173-179-voidable-transactions-v1",
    "synthetic-ru-gk180-181-invalidity-effects-v1",
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
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk421-422-freedom-of-contract-v1",
                "synthetic-ru-gk423-424-onerousness-and-price-v1",
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
                )
            ),
            legal_source_refs=(
                "synthetic-ru-gk445-446-mandatory-conclusion-v1",
                "synthetic-ru-gk447-449-auction-v1",
            ),
            review_status=BootstrapReviewStatus.REVIEWED,
            reviewer_id="synthetic-procedure-reviewer",
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
