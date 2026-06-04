from pydantic import BaseModel

from causa.core.bootstrap import (
    BootstrapReviewStatus,
    FormalTranslationResult,
    NormCondition,
    NormConsequence,
    ReviewedNormJSON,
    translate_reviewed_norm,
)
from causa.core.knowledge_graph import (
    DecisionTrace,
    KnowledgeEdge,
    KnowledgeLayer,
    KnowledgeNode,
    VersionCoordinates,
)
from causa.core.models import CandidateHypothesis, LegalClaim, LegalSource, SourceType
from causa.evaluation import RedTeamScenario
from causa.governance.candidate_types import CandidateType
from causa.governance.failure_taxonomy import FailureType
from causa.governance.profiles import GovernanceProfile, get_governance_profile
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.management.policy_matrix import PolicyMatrixEntry, build_policy_matrix_entry
from causa.management.risk_tiers import RiskTier
from causa.management.sla_modes import SLAMode
from causa.reasoning.formal_checks import check_basic_contradiction
from causa.translation import TranslationArtifact, TranslationLevel


class Phase0DemoTrace(BaseModel):
    disclaimer: str
    legal_source: LegalSource
    reviewed_norm: ReviewedNormJSON
    formal_translation: FormalTranslationResult
    formal_contradiction_detected: bool
    claim: LegalClaim
    candidate: CandidateHypothesis
    candidate_type: CandidateType
    governance_profile: GovernanceProfile
    policy: PolicyMatrixEntry
    red_team_scenario: RedTeamScenario
    translation: TranslationArtifact
    decision_trace: DecisionTrace


def build_supply_dispute_demo_trace() -> Phase0DemoTrace:
    source = LegalSource(
        id="synthetic-ru-gk-supply-delivery-duty",
        title="Synthetic civil-law supply delivery duty",
        source_type=SourceType.STATUTE,
        jurisdiction="RU",
        text=(
            "Synthetic non-authoritative source: under a supply relation, "
            "the supplier must deliver goods by the agreed date unless a valid "
            "contractual or statutory excuse applies."
        ),
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "purpose": "Phase 0 demo trace only",
        },
    )
    reviewed_norm = ReviewedNormJSON(
        id="norm-supply-delivery-duty-v0",
        source_id=source.id,
        subjects=["supplier", "buyer"],
        actions=["deliver goods by the agreed date"],
        conditions=[
            NormCondition(
                id="condition-supply-relation",
                text="A supply relation exists between supplier and buyer.",
            ),
            NormCondition(
                id="condition-agreed-date",
                text="The parties agreed on a delivery date.",
            ),
        ],
        exceptions=[
            NormCondition(
                id="exception-valid-excuse",
                text="A valid contractual or statutory excuse applies.",
            )
        ],
        consequences=[
            NormConsequence(
                id="consequence-breach-risk",
                text="Missing the agreed date creates a candidate breach issue.",
            )
        ],
        temporal_notes=["Assess performance against the agreed delivery date."],
        review_status=BootstrapReviewStatus.REVIEWED,
        reviewer_id="synthetic-domain-owner",
    )
    formal_translation = translate_reviewed_norm(reviewed_norm)
    formal_contradiction_detected = check_basic_contradiction(True, False)
    claim = LegalClaim(
        id="claim-supply-late-delivery",
        text=(
            "The supplier may have breached the delivery obligation if the agreed "
            "delivery date was missed and no valid excuse applies."
        ),
        sources=[source.id],
        confidence=0.62,
    )
    candidate = CandidateHypothesis(
        id="candidate-supply-excuse-scope",
        statement=(
            "When delivery is late, the system should ask whether the supplier "
            "has a contractual or statutory excuse before treating delay as breach."
        ),
        supporting_sources=[source.id],
        risk_level="medium",
        status="proposed",
    )
    candidate_type = CandidateType.GAP_HEURISTIC
    governance_profile = get_governance_profile(candidate_type)
    policy = build_policy_matrix_entry(SLAMode.STANDARD, RiskTier.T3_DRAFT_LETTER)
    trace_id = "trace-phase0-supply-dispute-v0"
    translation = TranslationArtifact(
        id="translation-phase0-supply-dispute-v0",
        trace_id=trace_id,
        level=TranslationLevel.PROFESSIONAL,
        template_version="translation-template-v0",
        text=(
            "Synthetic professional explanation: the current trace treats late "
            "delivery as a candidate breach issue, but the reasoning must first "
            "check whether a valid excuse exists. This is a non-production demo "
            "and not legal advice."
        ),
        faithfulness_checked=False,
        usability_checked=False,
    )
    red_team_scenario = RedTeamScenario(
        id="red-team-supply-delay-excuse-overreach",
        title="Overbroad excuse for late delivery",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Use a vague alleged acceptance delay to erase all delivery liability "
            "without checking source support."
        ),
        target_failure_type=FailureType.OVERBROAD_CANDIDATE_PRINCIPLE,
    )
    decision_trace = DecisionTrace(
        id=trace_id,
        case_id="case-supply-1",
        versions=VersionCoordinates(
            knowledge_version="knowledge-demo-v0",
            institutional_package_version=(
                f"{CONTRACTS_PACKAGE_MANIFEST.id}@{CONTRACTS_PACKAGE_MANIFEST.version}"
            ),
            policy_version="policy-demo-v0",
            translation_template_version=translation.template_version,
            model_profile="no-llm-synthetic-demo",
        ),
        nodes=[
            KnowledgeNode(
                id=source.id,
                layer=KnowledgeLayer.SOURCE,
                label=source.title,
                metadata=source.metadata,
            ),
            KnowledgeNode(
                id=reviewed_norm.id,
                layer=KnowledgeLayer.FORMAL_NORM,
                label="Structured supply delivery obligation rule",
                source_refs=[source.id],
                metadata={
                    "review_status": reviewed_norm.review_status.value,
                    "translator_version": formal_translation.translator_version,
                    "formal_rule_id": formal_translation.obligation_rule.id,
                },
            ),
            KnowledgeNode(
                id="case-supply-1",
                layer=KnowledgeLayer.CASE,
                label="Synthetic disputed supply delivery case",
                source_refs=[source.id],
                metadata={"relation_type": "supply", "synthetic": True},
            ),
            KnowledgeNode(
                id=candidate.id,
                layer=KnowledgeLayer.DOCTRINE,
                label="Candidate gap heuristic for valid excuse check",
                source_refs=[source.id],
                metadata={
                    "candidate_type": candidate_type.value,
                    "status": candidate.status,
                    "required_stages": [
                        stage.value for stage in governance_profile.required_stages
                    ],
                },
            ),
        ],
        edges=[
            KnowledgeEdge(source_id=source.id, target_id=reviewed_norm.id, relation="parsed_to"),
            KnowledgeEdge(source_id=reviewed_norm.id, target_id="case-supply-1", relation="applies_to"),
            KnowledgeEdge(source_id="case-supply-1", target_id=claim.id, relation="supports_claim"),
            KnowledgeEdge(source_id=claim.id, target_id=candidate.id, relation="raises_candidate"),
        ],
        claims=[claim.id],
        warnings=[
            "Synthetic demo only.",
            "Not legal advice.",
            "Formal translation is a first structured output, not full legal formalization.",
        ],
    )

    return Phase0DemoTrace(
        disclaimer="Synthetic Phase 0 trace. Not production-ready and not legal advice.",
        legal_source=source,
        reviewed_norm=reviewed_norm,
        formal_translation=formal_translation,
        formal_contradiction_detected=formal_contradiction_detected,
        claim=claim,
        candidate=candidate,
        candidate_type=candidate_type,
        governance_profile=governance_profile,
        policy=policy,
        red_team_scenario=red_team_scenario,
        translation=translation,
        decision_trace=decision_trace,
    )
