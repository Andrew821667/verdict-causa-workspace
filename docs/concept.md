# Verdict / Causa Workspace Concept v2.5 Summary

## Concept status

Verdict / Causa Workspace is at the architectural and prototype stage. The full source concept is preserved in [verdict-concept-v2-5.md](verdict-concept-v2-5.md). This file is the implementation-facing summary.

The project does not claim production readiness, legal-advice capability, adoption metrics, or user traction. The purpose of this repository is to provide a public OSS foundation for auditable legal AI infrastructure.

## Universal legal core

The universal core models the shared legal reasoning substrate:

- legal sources and source hierarchy;
- Source / Formal Norm / Doctrine / Case graph layers;
- facts, claims, candidate hypotheses, and candidate principles;
- temporal validity;
- authority and jurisdiction;
- confidence and risk;
- audit trail, reproducibility, and rollback.

The core should remain separate from any specific legal institution. Institutional specialization is how the universal core proves itself; it is not a replacement for universality.

## First institution of law

The first institutional package covers contractual relations: general obligations and contract law, sale, supply, and liability for breach of obligations. It is a full proving ground for the architecture, not a narrow domain or a small demo.

The first package boundary includes:

- general obligations and performance;
- general provisions on contracts;
- sale;
- supply;
- liability for breach, including penalty reduction and fault/liability questions.

Invalidity of transactions, unjust enrichment, torts, other special contract types, and procedural institutes are outside Phase 0.

## Knowledge Plane

The Knowledge Plane stores what the system knows: source graph, formal norm graph, doctrine/meta-principle graph, case graph, source hierarchy, provenance, retrieval graphs, institutional vocabularies, and benchmark corpora. It should be queryable, versioned, and auditable.

## Management Plane

The Management Plane stores how the system acts: confidence policies, activation rules, autonomy boundaries, escalation rules, routing rules, cost budgets, SLA/depth modes, risk tiers, prompt templates, and translation templates.

Knowledge evolution and behavior evolution are separate processes. Both require governance, versioning, diffs, auditability, and rollback.

## Two-contour architecture

The operational contour applies the current state of the system to concrete cases. The generative contour works in the background on internal models of law and argumentation.

Raw generative outputs cannot directly affect operational behavior. Candidate knowledge must pass governance before becoming active.

Only anonymized patterns, aggregate metrics, and calibrated signals may move from operational work to generative improvement. Raw client facts, documents, and positions stay out of the generative contour.

## Governance pipeline

Candidate legal hypotheses and candidate principles should pass through explicit lifecycle stages:

- proposed;
- type classification;
- formal check;
- source check;
- benchmark check;
- red-team testing;
- expert review;
- cross-review when required;
- sandbox;
- active;
- post-activation monitoring;
- revalidation;
- rejected;
- rolled back.

Candidate principle types include `meta_principle`, `calibration_rule`, `gap_heuristic`, `conflict_resolution_pattern`, `counterfactual_sensitivity_pattern`, `argument_template`, and `translation_pattern`.

## Institutional packages

Institutional packages describe legal domains through structured schema, vocabulary, source hierarchy, contradiction taxonomy, benchmarks, red-team cases, and governance-specific requirements.

The first package is `contracts`.

## Neuro-symbolic bootstrap pipeline

The concept rejects direct LLM-to-Z3 generation. The intended pipeline is:

1. LLM parses legal text into strict, human-readable JSON.
2. A Domain Owner reviews and corrects that JSON.
3. Deterministic code translates validated JSON into Z3.

The current Z3 code is only a placeholder for this future deterministic translation layer.

## Privacy and tenant safety

The project should avoid storing real client materials in the repository. Future implementations must support data minimization, tenant isolation, customer-specific doctrine boundaries, audit trails, and explicit handling of sensitive documents.

## Roadmap

The roadmap starts with repository foundation, then moves through Phase 0: universal core plus the first institutional package for contractual relations. Later phases add the operational contour, expert resonance, contradiction engine, audit/replay and Translation Layer, bounded counterfactual engine, reasoning profiles, enterprise readiness, multi-tenant operation, and longer-horizon research.

## MVP definition

MVP v2.5 is an auditable contradiction-aware legal reasoning engine with:

- working universal core;
- first institutional package for contractual relations;
- explicit Management Plane;
- bootstrap pipeline into Formal Norm Graph;
- Case Graph bound to source graph and policy version;
- contradiction detection and candidate resolution governance;
- Translation Layer with executive, professional, and forensic representations;
- reproducible decision trace;
- cost budgets, SLA/depth modes, and risk tiers.

## Phase 0 completion criteria

Phase 0 is complete when the repository has:

- honest public README and docs;
- Apache-2.0 license;
- Python package skeleton;
- first contractual institutional package;
- governance pipeline skeleton;
- formal-check placeholder;
- tests and CI;
- first GitHub issues;
- Codex for OSS application draft.

The broader concept defines stronger Phase 0 completion criteria for the real system: end-to-end bootstrap, representative contractual norms, full decision traces, Management Plane tests, sandboxed candidate principles, and at least one realistic pilot-style case.
