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
from causa.institutional.contracts.synthetic_sources import (
    get_synthetic_contract_source,
)
from causa.reasoning.counterfactual import CounterfactualBudget


SYNTHETIC_ANALYSIS_SOURCE_IDS = (
    "synthetic-ru-contract-supply-delivery-duty-v1",
    "synthetic-ru-contract-supply-delivery-duty-v2",
    "synthetic-ru-contract-supply-delivery-term",
    "synthetic-case-supply-1-reviewed-evidence",
)


def build_synthetic_supply_analysis_sources() -> list[LegalSource]:
    return [get_synthetic_contract_source(source_id) for source_id in SYNTHETIC_ANALYSIS_SOURCE_IDS]


def build_synthetic_supply_analysis_request() -> ReviewedContractAnalysisRequest:
    norm_source_id = "synthetic-ru-contract-supply-delivery-duty-v2"
    evidence_source_id = "synthetic-case-supply-1-reviewed-evidence"
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
