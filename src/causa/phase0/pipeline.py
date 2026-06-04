from enum import Enum

from pydantic import BaseModel, Field

from causa.phase0.demo_trace import Phase0DemoTrace, build_supply_dispute_demo_trace


class PipelineStepStatus(str, Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class PipelineStepResult(BaseModel):
    id: str
    title: str
    status: PipelineStepStatus
    artifact_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class Phase0PipelineResult(BaseModel):
    id: str
    scenario: str
    trace: Phase0DemoTrace
    steps: list[PipelineStepResult]

    @property
    def passed(self) -> bool:
        return all(step.status != PipelineStepStatus.FAILED for step in self.steps)


class ReadinessItem(BaseModel):
    id: str
    title: str
    status: PipelineStepStatus
    evidence_refs: list[str] = Field(default_factory=list)
    remaining_work: list[str] = Field(default_factory=list)


class Phase0ReadinessReport(BaseModel):
    id: str
    project_stage: str
    ready_for_production: bool
    summary: str
    items: list[ReadinessItem]

    @property
    def warning_count(self) -> int:
        return sum(item.status == PipelineStepStatus.WARNING for item in self.items)

    @property
    def failed_count(self) -> int:
        return sum(item.status == PipelineStepStatus.FAILED for item in self.items)


def run_supply_dispute_pipeline() -> Phase0PipelineResult:
    trace = build_supply_dispute_demo_trace()

    steps = [
        PipelineStepResult(
            id="select-source",
            title="Select synthetic legal source",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.legal_source.id],
            notes=["Synthetic source is explicitly marked non-authoritative."],
        ),
        PipelineStepResult(
            id="review-bootstrap-json",
            title="Validate reviewed bootstrap JSON",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.reviewed_norm.id],
            notes=[f"Review status: {trace.reviewed_norm.review_status.value}."],
        ),
        PipelineStepResult(
            id="translate-structured-formal-output",
            title="Translate reviewed JSON to structured obligation rule",
            status=PipelineStepStatus.WARNING,
            artifact_refs=[trace.formal_translation.obligation_rule.id],
            notes=[
                "Current translation is deterministic and structured.",
                "It is not yet a Z3 formula or complete legal formalization.",
            ],
        ),
        PipelineStepResult(
            id="build-case-graph",
            title="Build four-layer decision trace",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.decision_trace.id],
            notes=[
                "Trace includes source, formal_norm, case, and doctrine layers.",
            ],
        ),
        PipelineStepResult(
            id="ground-claim",
            title="Create source-grounded claim",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.claim.id, *trace.claim.sources],
            notes=["Claim references the synthetic source."],
        ),
        PipelineStepResult(
            id="classify-candidate",
            title="Apply candidate type and governance profile",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.candidate.id, trace.candidate_type.value],
            notes=[
                "Candidate is a gap heuristic.",
                "Profile requires type classification and expert review.",
            ],
        ),
        PipelineStepResult(
            id="record-policy",
            title="Record Management Plane policy",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.policy.mode.value, trace.policy.risk_tier.value],
            notes=["Policy matrix entry is standard x T3."],
        ),
        PipelineStepResult(
            id="attach-red-team",
            title="Attach red-team scenario",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.red_team_scenario.id],
            notes=["Scenario targets overbroad candidate principle risk."],
        ),
        PipelineStepResult(
            id="produce-translation",
            title="Produce professional translation artifact",
            status=PipelineStepStatus.WARNING,
            artifact_refs=[trace.translation.id],
            notes=[
                "Translation artifact exists.",
                "Faithfulness and usability checks are not implemented yet.",
            ],
        ),
        PipelineStepResult(
            id="export-decision-trace",
            title="Export decision trace with version coordinates",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.decision_trace.id],
            notes=[
                f"Knowledge version: {trace.decision_trace.versions.knowledge_version}.",
                f"Policy version: {trace.decision_trace.versions.policy_version}.",
            ],
        ),
    ]

    return Phase0PipelineResult(
        id="phase0-supply-dispute-pipeline-v0",
        scenario="Synthetic supply delivery dispute",
        trace=trace,
        steps=steps,
    )


def build_phase0_readiness_report() -> Phase0ReadinessReport:
    pipeline = run_supply_dispute_pipeline()

    items = [
        ReadinessItem(
            id="ws1-universal-core",
            title="Universal core data model",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[
                "src/causa/core/models.py",
                "src/causa/core/knowledge_graph.py",
                pipeline.trace.decision_trace.id,
            ],
            remaining_work=["Expand provenance and audit metadata."],
        ),
        ReadinessItem(
            id="ws2-knowledge-plane",
            title="Knowledge Plane skeleton",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[pipeline.trace.decision_trace.id],
            remaining_work=["Add graph persistence and retrieval behavior."],
        ),
        ReadinessItem(
            id="ws3-bootstrap",
            title="Neuro-symbolic bootstrap pipeline",
            status=PipelineStepStatus.WARNING,
            evidence_refs=[
                "src/causa/core/bootstrap.py",
                pipeline.trace.reviewed_norm.id,
            ],
            remaining_work=[
                "Translate structured obligation rules to a first solver-ready representation.",
                "Add richer contractual norm schema for exceptions and temporal applicability.",
            ],
        ),
        ReadinessItem(
            id="ws4-contracts-package",
            title="Contractual institutional package",
            status=PipelineStepStatus.WARNING,
            evidence_refs=[
                "src/causa/institutional/contracts/package.py",
                "docs/first-institution-contracts.md",
            ],
            remaining_work=[
                "Expand vocabulary, authority rules, temporal rules, legal operators, benchmarks, and red-team scenarios.",
            ],
        ),
        ReadinessItem(
            id="ws5-management-plane",
            title="Management Plane",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[
                "src/causa/management/policy_matrix.py",
                pipeline.trace.decision_trace.versions.policy_version,
            ],
            remaining_work=["Add policy version persistence and rollback records."],
        ),
        ReadinessItem(
            id="ws6-governance",
            title="Governance pipeline",
            status=PipelineStepStatus.WARNING,
            evidence_refs=[
                "src/causa/governance/profiles.py",
                pipeline.trace.candidate.id,
            ],
            remaining_work=[
                "Execute stage transitions with stored decisions.",
                "Add sandbox and revalidation records.",
            ],
        ),
        ReadinessItem(
            id="ws7-translation",
            title="Translation and explainability layer",
            status=PipelineStepStatus.WARNING,
            evidence_refs=[pipeline.trace.translation.id],
            remaining_work=[
                "Implement faithfulness checks.",
                "Implement usability checks.",
                "Add executive and forensic examples.",
            ],
        ),
        ReadinessItem(
            id="ws8-evaluation-red-team",
            title="Evaluation and Red Team",
            status=PipelineStepStatus.WARNING,
            evidence_refs=[pipeline.trace.red_team_scenario.id],
            remaining_work=[
                "Add benchmark suite.",
                "Add multiple red-team scenarios.",
                "Separate benchmark quality and practice utility metrics.",
            ],
        ),
        ReadinessItem(
            id="ws9-zero-to-value",
            title="Zero-to-Value synthetic path",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[
                "examples/phase0_supply_dispute_trace.json",
                pipeline.id,
            ],
            remaining_work=["Add synthetic source set and pilot-style task list."],
        ),
    ]

    return Phase0ReadinessReport(
        id="phase0-readiness-report-v0",
        project_stage="architectural_prototype",
        ready_for_production=False,
        summary=(
            "Phase 0 has a working synthetic path, but formal translation, package depth, "
            "governance execution, translation testing, and evaluation coverage remain incomplete."
        ),
        items=items,
    )
