# Neuro-Symbolic Bootstrap Pipeline Specification

The bootstrap pipeline is the bridge between natural-language legal sources and formal checks.

## Hard rule

The project must not directly translate legal text to Z3 using an LLM.

## Pipeline

### Step 1. Structured JSON extraction

An LLM may produce a structured JSON representation of a legal norm.

This representation is not a formal proof object. It is a human-readable intermediate form containing:

- source reference;
- subjects;
- actions;
- conditions;
- exceptions;
- consequences;
- temporal bounds;
- related norms;
- natural-language notes.

### Step 2. Domain Owner review

A Domain Owner reviews the JSON and marks it as:

- `draft`;
- `needs_revision`;
- `reviewed`;
- `rejected`.

Only reviewed JSON can move to deterministic translation.

### Step 3. Deterministic translation

Code translates reviewed JSON into formal structures. The same JSON must always produce the same formal output.

This layer is tested as software. It is not a model prompt.

## Why this structure exists

LLM hallucination is tolerable only where a human can see and correct it. It is not tolerable inside formal logic. A solver can be strictly correct over a false formalization, which is worse than a normal model error because it creates false certainty.

## Phase 0 scope

Phase 0 should define a small reviewed JSON subset for contractual norms:

- obligation creation;
- debtor and creditor;
- performance duty;
- due date or triggering condition;
- exception;
- consequence of breach.

## Translation status

The current bootstrap translator emits a deterministic structured `FormalObligationRule` for a narrow contractual subset. The contracts package can compute source applicability and due-date miss status from temporal facts, and the reasoning layer can build a solver-backed `ConstraintSet` from that rule for three distinct patterns: late performance, confirmed nonconforming performance, and payment default. Each pattern has its own required facts; the aggregate breach flag is only a traceable disjunction of those narrow results.

This is still not complete legal formalization. It is a deliberately narrow Phase 0 solver-ready layer.

## Acceptance tests

- Draft JSON cannot be translated.
- Reviewed JSON can be accepted by the translation interface.
- Invalid JSON fails schema validation.
- Translation output includes source id and schema version.
- Translation is deterministic.
