# Architecture

## 1. Two-Contour Architecture

The system has two separated contours.

The operational contour works with concrete cases, documents, source grounding, active retrieval, agentic reasoning, versioned knowledge, and versioned policies.

The generative contour works in the background on internal models of law and argumentation. It proposes candidate principles, contradiction-resolution patterns, calibration rules, and argument templates.

Raw generative results do not directly influence operational behavior. Governance sits between the contours.

## 2. Universal Core

The Universal Core defines common legal AI primitives: legal sources, legal claims, candidate hypotheses, authority, jurisdiction, temporal validity, confidence, risk, and audit metadata.

## 3. Knowledge Plane

The Knowledge Plane is responsible for what the system knows:

- Source Graph;
- Formal Norm Graph;
- Doctrine / Meta-Principle Graph;
- Case Graph;
- provenance and authority metadata;
- retrieval indexes;
- institutional vocabularies;
- benchmark corpora.

It should make legal reasoning reproducible by preserving references, versions, and provenance.

## 4. Management Plane

The Management Plane controls how the system behaves. It includes confidence policies, activation rules, autonomy boundaries, routing rules, escalation rules, cost budgets, SLA/depth modes, risk tiers, prompt templates, translation templates, and rollback classes.

Knowledge Plane evolution and Management Plane evolution are separate. Both require explicit versions and audit trails.

## 5. Institutional Package Layer

Institutional packages add domain-specific schema and evaluation material. The first package is contractual relations, covering obligations, sale, supply, and breach liability.

An institutional package contains vocabulary, authority model, temporal model, JSON schema, deterministic JSON-to-Z3 mapping rules, contradiction taxonomy, legal operators, benchmarks, red-team scenarios, confidence policies, activation policies, and Domain Owner responsibilities.

## 6. Reasoning Layer

The Reasoning Layer includes RAG, GraphRAG, candidate hypothesis construction, source-grounded explanation, and formal consistency checks.

The formal-check component currently contains only a small placeholder and should evolve toward deterministic JSON-to-Z3 translation for narrowly defined legal representations.

The hybrid reasoning model routes each problem to the appropriate layer:

- Hard Constraint Layer;
- Defeasible Argumentation Layer;
- Principles & Balancing Layer;
- Provenance & Authority Layer.

## 7. Governance Layer

The Governance Layer moves candidate hypotheses and candidate principles through type classification, formal checks, source grounding, benchmark evaluation, red-team testing, expert review, cross-review, sandbox, controlled activation, post-activation monitoring, revalidation, rejection, and rollback.

## 8. Evaluation and Red Team Layer

The evaluation layer should include benchmark tasks, adversarial cases, regression suites, contradiction checks, and source-grounding tests. Contractual disputes are the first target area.

Failure Taxonomy classifies system failures such as hallucinated source grounding, bad formalization, wrong temporal applicability, wrong authority ranking, overbroad candidate principles, translation distortion, escalation failure, false confidence inflation, privacy leakage risk, and benchmark overfitting.

## 9. Privacy and Tenant Safety Layer

Future implementations must protect tenant boundaries, avoid cross-customer leakage, separate public legal knowledge from private matter-specific doctrine, and keep audit trails for sensitive operations.
