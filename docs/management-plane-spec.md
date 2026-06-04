# Management Plane Specification

The Management Plane stores how the system acts. It is separate from the Knowledge Plane, which stores what the system knows.

## Why this matters

Policy changes can alter behavior as much as knowledge changes. Changing a confidence threshold, prompt template, escalation rule, or translation template can change legal outputs without changing a single source or formal norm.

Therefore Management Plane artifacts are versioned, audited, governed, and rollback-capable.

## Required sublayers

### Confidence and activation policies

Define:

- confidence thresholds;
- whether candidate principles can be used;
- expiration checks;
- activation requirements by candidate type.

### Autonomy boundaries

Define what the system may do without human review by mode and risk tier.

### Routing and escalation rules

Define:

- when to use heavier reasoning;
- when to run Red Team;
- when to trigger cross-review;
- when to stop due to budget.

### Cost and SLA policies

Define mode-level budgets:

- `draft`;
- `standard`;
- `deep`;
- `research`.

Each mode should specify expected depth, latency tolerance, allowed agent passes, retrieval depth, formal-check usage, red-team usage, and review requirements.

### Risk tier policies

Risk tiers:

- T1 reference / orientation;
- T2 internal memo;
- T3 draft letter or legal position;
- T4 procedural draft;
- T5 high-stakes recommendation;
- T6 ready-to-file document.

The `mode x tier` matrix determines the actual behavior.

### Prompt and translation templates

Prompt templates and translation templates are policy artifacts. They must be versioned and reviewable.

## Rollback classes

- candidate rollback;
- activation decision rollback;
- policy rollback;
- translation template rollback;
- institutional package version rollback.

## Phase 0 implementation scope

The initial implementation should provide:

- `SLAMode`;
- `RiskTier`;
- `CasePolicy`;
- `PolicyMatrixEntry`;
- cost budget model;
- review requirements model;
- tests showing that T4-T6 require stronger review than T1-T3.
