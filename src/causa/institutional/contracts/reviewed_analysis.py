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


CASE_EVIDENCE_SCHEMA_VERSION = "contracts.case-evidence.v6"
EVIDENCE_MAPPING_VERSION = "contracts-reviewed-evidence-to-facts-v0"
ANALYSIS_PIPELINE_VERSION = "contracts-reviewed-analysis-v6"


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
    invalidity_evidence: ReviewedInvalidityEvidence
    security_evidence: ReviewedSecurityEvidence
    obligation_dynamics_evidence: ReviewedObligationDynamicsEvidence
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
    invalidity_evidence_mapping: InvalidityEvidenceMappingResult
    invalidity_constraint_set: InvalidityConstraintSet
    invalidity_evaluation: InvalidityEvaluation
    security_evidence_mapping: SecurityEvidenceMappingResult
    security_constraint_set: SecurityConstraintSet
    security_evaluation: SecurityEvaluation
    obligation_dynamics_evidence_mapping: ObligationDynamicsEvidenceMappingResult
    obligation_dynamics_constraint_set: ObligationDynamicsConstraintSet
    obligation_dynamics_evaluation: ObligationDynamicsEvaluation
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
    if request.invalidity_evidence.case_id != request.case_id:
        raise ValueError("Invalidity evidence case_id does not match the analysis request.")
    if request.security_evidence.case_id != request.case_id:
        raise ValueError("Security evidence case_id does not match the analysis request.")
    if request.obligation_dynamics_evidence.case_id != request.case_id:
        raise ValueError(
            "Obligation-dynamics evidence case_id does not match the analysis request."
        )
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
    if request.termination_evidence.schema_version != TERMINATION_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Termination evidence uses an unsupported schema version.")
    if request.liability_evidence.schema_version != LIABILITY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Liability evidence uses an unsupported schema version.")
    if request.reviewed_norm.source_id not in request.authority_input.candidate_source_ids:
        raise ValueError("Reviewed norm source must be an authority candidate.")

    referenced_source_ids = {
        request.reviewed_norm.source_id,
        *request.temporal_evidence.source_refs,
        *request.authority_input.candidate_source_ids,
        *request.formation_evidence.legal_source_refs,
        *request.invalidity_evidence.legal_source_refs,
        *request.security_evidence.legal_source_refs,
        *request.obligation_dynamics_evidence.legal_source_refs,
        *request.termination_evidence.legal_source_refs,
        *request.liability_evidence.legal_source_refs,
    }
    for assertion in request.case_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.formation_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.invalidity_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.security_evidence.assertions:
        referenced_source_ids.update(assertion.source_refs)
    for assertion in request.obligation_dynamics_evidence.assertions:
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
        or invalidity_evaluation.requires_human_invalidity_assessment
        or security_evaluation.requires_human_security_assessment
        or dynamics_evaluation.requires_human_dynamics_assessment
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
                invalidity_reviewer_id,
                security_reviewer_id,
                dynamics_reviewer_id,
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
            *termination_evaluation.warnings_ru,
            *liability_evaluation.warnings_ru,
            "Не является юридической консультацией.",
        ],
    )
