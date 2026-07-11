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

The current bootstrap translator emits a deterministic structured `FormalObligationRule` for a narrow contractual subset. The contracts package now accepts separate reviewed case, temporal, authority, and liability inputs. It rejects draft inputs, missing reviewer coordinates, incomplete or duplicate predicates, unknown source references, mismatched case/date coordinates, unsupported schema versions, inapplicable norm sources, and a different authority winner.

Reviewed case evidence uses `contracts.case-evidence.v1`. The deterministic `contracts-reviewed-evidence-to-facts-v0` mapper produces the complete narrow `ObligationFactSet`: no absent predicate is silently treated as false. Every mapped fact retains its evidence assertion and source references. Duty and exception facts also retain links to the relevant formal condition or exception atoms from the reviewed norm.

Reviewed liability evidence uses `contracts.liability-evidence.v0` and contains all 20 predicates required by the narrow articles 333/401 model. Its facts and legal source references are validated independently and mapped by `contracts-reviewed-liability-to-facts-v0`. Missing liability predicates are never inferred from the general breach result.

For the Russian-law package, every expert-facing temporal, source-applicability, authority, and formal result includes Russian reasons in `reasons_ru`. Stable English `reasons` remain as a compatibility layer and are not the primary legal-audit presentation.

The reasoning layer builds a solver-backed `ConstraintSet` for six distinct patterns: late performance, confirmed nonconforming performance, payment default, basic damages remedy availability, causation-evidence gap, and limitation bar. Each pattern has its own required facts; the aggregate breach flag is only a traceable disjunction of the three breach patterns. The remedy patterns do not calculate loss, establish causation, or compute limitation dates; they consume explicitly supplied, reviewed facts.

This is still not complete legal formalization. It is a deliberately narrow Phase 0 solver-ready layer.

## Acceptance tests

- Draft JSON cannot be translated.
- Reviewed JSON can be accepted by the translation interface.
- Invalid JSON fails schema validation.
- Translation output includes source id and schema version.
- Translation is deterministic.
- Draft case, temporal, authority, or liability inputs cannot be analyzed.
- Every required formal fact has assertion and source provenance.
- Unknown sources, incomplete evidence, and coordinate mismatches fail closed.
- Authority resolution runs before formal constraint evaluation.
