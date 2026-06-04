# Governance

Verdict / Causa Workspace treats legal hypotheses as governed artifacts. A hypothesis is not active knowledge merely because a model proposed it.

## Candidate types

Candidate principle types:

- `meta_principle`;
- `calibration_rule`;
- `gap_heuristic`;
- `conflict_resolution_pattern`;
- `counterfactual_sensitivity_pattern`;
- `argument_template`;
- `translation_pattern`.

Each type has a governance profile: required checks, optional checks, expiration period, sandbox requirement, and cross-review requirement.

## Candidate lifecycle

The initial lifecycle is:

1. proposed;
2. type classification;
3. formal compatibility check;
4. source grounding check;
5. benchmark evaluation;
6. red-team adversarial testing;
7. expert review;
8. cross-review when required;
9. pre-activation sandbox;
10. controlled activation;
11. post-activation monitoring;
12. periodic revalidation;
13. rollback when needed.

## Design principles

- Every candidate should be source-grounded.
- Every promotion should be auditable.
- Failed checks should produce explicit reasons.
- Active knowledge should be reversible.
- Sandbox behavior should be separate from active production knowledge.
- Benchmark quality and practice utility should be measured separately.
- Quiet evolution should be architecturally impossible.

## Red Team and failure taxonomy

Red Team testing attempts to use a candidate to justify absurd, unlawful, or professionally unacceptable outcomes. A successful attack blocks normal activation and creates a structured review item.

Failure taxonomy should classify incidents by type: hallucinated source grounding, bad formalization, wrong temporal applicability, wrong authority ranking, overbroad candidate principle, translation distortion, escalation failure, false confidence inflation, privacy leakage risk, and benchmark overfitting.

## Current implementation

The repository contains only a minimal state-transition skeleton in `src/causa/governance/pipeline.py`.
