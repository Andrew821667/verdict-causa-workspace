from pydantic import BaseModel

from causa.core.knowledge_graph import (
    DecisionTrace,
    KnowledgeEdge,
    KnowledgeLayer,
    KnowledgeNode,
    VersionCoordinates,
)
from causa.core.models import CandidateHypothesis, LegalClaim, LegalSource
from causa.evaluation import RedTeamScenario
from causa.governance.candidate_types import CandidateType
from causa.governance.failure_taxonomy import FailureType
from causa.governance.engine import GovernanceRecord
from causa.governance.profiles import GovernanceProfile, get_governance_profile
from causa.governance.synthetic_lifecycle import (
    SYNTHETIC_POLICY_VERSION,
    build_synthetic_gap_governance_record,
)
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisRequest,
    ReviewedContractAnalysisResult,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
)
from causa.management.policy_matrix import PolicyMatrixEntry, build_policy_matrix_entry
from causa.management.risk_tiers import RiskTier
from causa.management.sla_modes import SLAMode
from causa.localization.ru import GOVERNANCE_STAGE_LABELS_RU, label_ru
from causa.reasoning.formal_checks import check_basic_contradiction
from causa.translation import TranslationArtifact, TranslationLevel


class Phase0DemoTrace(BaseModel):
    locale: str = "ru-RU"
    disclaimer: str
    legal_sources: list[LegalSource]
    analysis_request: ReviewedContractAnalysisRequest
    analysis_result: ReviewedContractAnalysisResult
    formal_contradiction_detected: bool
    claim: LegalClaim
    candidate: CandidateHypothesis
    candidate_type: CandidateType
    governance_profile: GovernanceProfile
    governance_record: GovernanceRecord
    policy: PolicyMatrixEntry
    red_team_scenario: RedTeamScenario
    translation: TranslationArtifact
    decision_trace: DecisionTrace

    @property
    def legal_source(self) -> LegalSource:
        source_id = self.analysis_request.reviewed_norm.source_id
        return next(source for source in self.legal_sources if source.id == source_id)

    @property
    def reviewed_norm(self):
        return self.analysis_request.reviewed_norm

    @property
    def formal_translation(self):
        return self.analysis_result.formal_translation

    @property
    def temporal_facts(self):
        return self.analysis_result.temporal_facts

    @property
    def temporal_evaluation(self):
        return self.analysis_result.temporal_evaluation

    @property
    def source_applicability(self):
        return self.analysis_result.source_applicability

    @property
    def obligation_facts(self):
        return self.analysis_result.evidence_mapping.facts

    @property
    def constraint_set(self):
        return self.analysis_result.constraint_set

    @property
    def constraint_evaluation(self):
        return self.analysis_result.constraint_evaluation


def build_supply_dispute_demo_trace() -> Phase0DemoTrace:
    analysis_artifact = build_synthetic_supply_analysis_artifact()
    sources = analysis_artifact.sources
    analysis_request = analysis_artifact.request
    analysis_result = analysis_artifact.result
    source = next(
        source
        for source in sources
        if source.id == analysis_request.reviewed_norm.source_id
    )
    reviewed_norm = analysis_request.reviewed_norm
    formal_translation = analysis_result.formal_translation
    temporal_evaluation = analysis_result.temporal_evaluation
    source_applicability = analysis_result.source_applicability
    constraint_set = analysis_result.constraint_set
    constraint_evaluation = analysis_result.constraint_evaluation
    formal_contradiction_detected = check_basic_contradiction(True, False)
    claim = LegalClaim(
        id="claim-supply-late-delivery",
        text=(
            "Поставщик мог нарушить обязательство по поставке, если согласованный "
            "срок был пропущен и применимое основание освобождения не установлено."
        ),
        sources=[source.id],
        confidence=0.62,
    )
    candidate = CandidateHypothesis(
        id="candidate-supply-excuse-scope",
        statement=(
            "При просрочке поставки система должна проверить наличие договорного "
            "или предусмотренного законом основания освобождения до вывода о нарушении."
        ),
        supporting_sources=[source.id],
        risk_level="medium",
        status="active",
    )
    candidate_type = CandidateType.GAP_HEURISTIC
    governance_profile = get_governance_profile(candidate_type)
    governance_record = build_synthetic_gap_governance_record(candidate.id)
    policy = build_policy_matrix_entry(SLAMode.STANDARD, RiskTier.T3_DRAFT_LETTER)
    trace_id = "trace-phase0-supply-dispute-v0"
    translation = TranslationArtifact(
        id="translation-phase0-supply-dispute-v0",
        trace_id=trace_id,
        level=TranslationLevel.PROFESSIONAL,
        template_version="translation-template-v0",
        text=(
            "Синтетическое профессиональное объяснение: текущая трассировка выявляет "
            "возможную просрочку поставки, поскольку обязанность существовала, срок "
            "исполнения пропущен, а применимое основание освобождения не установлено. "
            "Это демонстрационный вывод, а не юридическая консультация."
        ),
        faithfulness_checked=False,
        usability_checked=False,
    )
    red_team_scenario = RedTeamScenario(
        id="red-team-supply-delay-excuse-overreach",
        title="Чрезмерно широкое оправдание просрочки поставки",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Использовать неопределенную ссылку на задержку приемки для полного "
            "исключения ответственности без проверки правовых и фактических оснований."
        ),
        target_failure_type=FailureType.OVERBROAD_CANDIDATE_PRINCIPLE,
    )
    evidence_source_refs = sorted(
        {
            *analysis_request.temporal_evidence.source_refs,
            *(
                source_ref
                for assertion in analysis_request.case_evidence.assertions
                for source_ref in assertion.source_refs
            ),
        }
    )
    source_nodes = [
        KnowledgeNode(
            id=registered_source.id,
            layer=KnowledgeLayer.SOURCE,
            label=registered_source.title,
            metadata=registered_source.metadata,
        )
        for registered_source in sources
    ]
    source_edges = [
        KnowledgeEdge(
            source_id=source_id,
            target_id=reviewed_norm.id,
            relation="authority_candidate_for",
        )
        for source_id in analysis_request.authority_input.candidate_source_ids
    ]
    evidence_edges = [
        KnowledgeEdge(
            source_id=source_id,
            target_id=analysis_request.case_id,
            relation="supports_reviewed_fact",
        )
        for source_id in evidence_source_refs
    ]
    decision_trace = DecisionTrace(
        id=trace_id,
        case_id="case-supply-1",
        versions=VersionCoordinates(
            knowledge_version="knowledge-demo-v0",
            institutional_package_version=(
                f"{CONTRACTS_PACKAGE_MANIFEST.id}@{CONTRACTS_PACKAGE_MANIFEST.version}"
            ),
            policy_version=SYNTHETIC_POLICY_VERSION,
            translation_template_version=translation.template_version,
            model_profile="no-llm-synthetic-demo",
        ),
        nodes=[
            *source_nodes,
            KnowledgeNode(
                id=reviewed_norm.id,
                layer=KnowledgeLayer.FORMAL_NORM,
                label="Формализованное обязательство по сроку поставки",
                source_refs=[source.id],
                metadata={
                    "review_status": reviewed_norm.review_status.value,
                    "translator_version": formal_translation.translator_version,
                    "analysis_pipeline_version": analysis_result.pipeline_version,
                    "case_evidence_schema_version": (
                        analysis_result.evidence_mapping.schema_version
                    ),
                    "evidence_mapping_version": (
                        analysis_result.evidence_mapping.mapping_version
                    ),
                    "reviewer_ids": analysis_result.reviewer_ids,
                    "governance_record_id": governance_record.id,
                    "formal_rule_id": formal_translation.obligation_rule.id,
                    "constraint_set_id": constraint_set.id,
                    "source_applicable": source_applicability.applicable,
                    "authority_winner": (
                        analysis_result.authority_evaluation.selected_source_id
                    ),
                    "authority_rules": [
                        rule.value
                        for rule in analysis_result.authority_evaluation.applied_rules
                    ],
                    "requires_human_resolution": (
                        analysis_result.requires_human_resolution
                    ),
                    "due_date_missed": temporal_evaluation.due_date_missed,
                    "breach_issue": constraint_evaluation.breach_issue,
                    "late_performance_issue": constraint_evaluation.late_performance_issue,
                    "defect_issue": constraint_evaluation.defect_issue,
                    "payment_default_issue": constraint_evaluation.payment_default_issue,
                    "damages_remedy_available": constraint_evaluation.damages_remedy_available,
                    "causation_evidence_gap": constraint_evaluation.causation_evidence_gap,
                    "limitation_bar": constraint_evaluation.limitation_bar,
                },
            ),
            KnowledgeNode(
                id="case-supply-1",
                layer=KnowledgeLayer.CASE,
                label="Синтетический спор о сроке поставки",
                source_refs=evidence_source_refs,
                metadata={
                    "relation_type": "supply",
                    "synthetic": True,
                    "case_evidence_id": analysis_request.case_evidence.id,
                    "case_evidence_review_status": (
                        analysis_request.case_evidence.review_status.value
                    ),
                    "temporal_evidence_id": analysis_request.temporal_evidence.id,
                    "temporal_evidence_review_status": (
                        analysis_request.temporal_evidence.review_status.value
                    ),
                },
            ),
            KnowledgeNode(
                id=candidate.id,
                layer=KnowledgeLayer.DOCTRINE,
                label="Эвристика проверки основания освобождения при просрочке",
                source_refs=[source.id],
                metadata={
                    "candidate_type": candidate_type.value,
                    "status": candidate.status,
                    "governance_stage": governance_record.current_stage.value,
                    "governance_stage_label_ru": (
                        governance_record.current_stage_label_ru
                    ),
                    "governance_decision_ids": [
                        decision.id for decision in governance_record.decisions
                    ],
                    "required_stages": [
                        stage.value for stage in governance_profile.required_stages
                    ],
                    "required_stage_labels_ru": [
                        label_ru(stage, GOVERNANCE_STAGE_LABELS_RU)
                        for stage in governance_profile.required_stages
                    ],
                },
            ),
        ],
        edges=[
            *source_edges,
            *evidence_edges,
            KnowledgeEdge(source_id=source.id, target_id=reviewed_norm.id, relation="parsed_to"),
            KnowledgeEdge(source_id=reviewed_norm.id, target_id="case-supply-1", relation="applies_to"),
            KnowledgeEdge(source_id="case-supply-1", target_id=claim.id, relation="supports_claim"),
            KnowledgeEdge(source_id=claim.id, target_id=candidate.id, relation="raises_candidate"),
        ],
        claims=[claim.id],
        warnings=[
            *analysis_result.warnings_ru,
            "Формальная модель покрывает только узкие сценарии просрочки, недостатков, "
            "неисполнения платежа и отдельных предпосылок требования убытков.",
        ],
    )

    return Phase0DemoTrace(
        disclaimer=(
            "Синтетическая трассировка Этапа 0. Не готова к промышленной эксплуатации "
            "и не является юридической консультацией."
        ),
        legal_sources=sources,
        analysis_request=analysis_request,
        analysis_result=analysis_result,
        formal_contradiction_detected=formal_contradiction_detected,
        claim=claim,
        candidate=candidate,
        candidate_type=candidate_type,
        governance_profile=governance_profile,
        governance_record=governance_record,
        policy=policy,
        red_team_scenario=red_team_scenario,
        translation=translation,
        decision_trace=decision_trace,
    )
