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


CASE_EVIDENCE_SCHEMA_VERSION = "contracts.case-evidence.v1"
EVIDENCE_MAPPING_VERSION = "contracts-reviewed-evidence-to-facts-v0"
ANALYSIS_PIPELINE_VERSION = "contracts-reviewed-analysis-v1"


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
    liability_evidence_mapping: LiabilityEvidenceMappingResult
    liability_constraint_set: LiabilityConstraintSet
    liability_evaluation: LiabilityEvaluation
    counterfactual_sensitivity: ContractCounterfactualSensitivityReport
    authority_evaluation: AuthorityEvaluation
    requires_human_resolution: bool
    warnings: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_liability_replay(self) -> "ReviewedContractAnalysisResult":
        expected_constraint_set = build_liability_constraint_set(
            self.liability_evidence_mapping
        )
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
    if request.liability_evidence.case_id != request.case_id:
        raise ValueError("Liability evidence case_id does not match the analysis request.")
    if request.authority_input.evaluation_date != request.temporal_evidence.evaluation_date:
        raise ValueError("Authority and temporal evidence evaluation dates must match.")
    if request.reviewed_norm.schema_version != DEFAULT_BOOTSTRAP_SCHEMA_VERSION:
        raise ValueError("Reviewed norm uses an unsupported bootstrap schema version.")
    if request.case_evidence.schema_version != CASE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Case evidence uses an unsupported schema version.")
    if request.liability_evidence.schema_version != LIABILITY_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("Liability evidence uses an unsupported schema version.")
    if request.reviewed_norm.source_id not in request.authority_input.candidate_source_ids:
        raise ValueError("Reviewed norm source must be an authority candidate.")

    referenced_source_ids = {
        request.reviewed_norm.source_id,
        *request.temporal_evidence.source_refs,
        *request.authority_input.candidate_source_ids,
        *request.liability_evidence.legal_source_refs,
    }
    for assertion in request.case_evidence.assertions:
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

    assertions_by_predicate = {
        assertion.predicate: assertion for assertion in evidence.assertions
    }
    missing_predicates = sorted(
        predicate.value for predicate in REQUIRED_EVIDENCE_PREDICATES - assertions_by_predicate.keys()
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
        source_registry[source_id]
        for source_id in request.authority_input.candidate_source_ids
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
    constraint_set = build_obligation_constraint_set(formal_translation.obligation_rule)
    constraint_evaluation = evaluate_obligation_constraints(
        constraint_set,
        evidence_mapping.facts,
    )
    liability_evidence_mapping = map_reviewed_liability_evidence(
        request.liability_evidence
    )
    if (
        liability_evidence_mapping.facts.breach_established
        != constraint_evaluation.breach_issue
    ):
        raise ValueError("Liability breach fact does not match obligation evaluation.")
    liability_constraint_set = build_liability_constraint_set(
        liability_evidence_mapping
    )
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
    requires_human_resolution = authority_evaluation.selected_source_id is None

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
            *liability_evaluation.warnings_ru,
            "Не является юридической консультацией.",
        ],
    )
