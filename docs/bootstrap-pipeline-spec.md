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

The current bootstrap translator emits a deterministic structured `FormalObligationRule` for a narrow contractual subset. The contracts package now accepts separate reviewed case, temporal, authority, formation, invalidity, security, obligation-dynamics, performance-remedies, change-and-termination, and liability inputs. It rejects draft inputs, missing reviewer coordinates, incomplete or duplicate predicates, unknown source references, mismatched case/date coordinates, unsupported schema versions, inapplicable norm sources, and a different authority winner.

Reviewed formation evidence uses `contracts.formation-evidence.v0` and contains all 17 predicates required by the narrow articles 432/435/438/443 model. It establishes whether a transaction was concluded, not whether invalidity later displaces its ordinary effects.

Reviewed invalidity evidence uses `contracts.invalidity-evidence.v0` with 51 mandatory predicates. A contractual duty requires both a concluded transaction and the absence of a formal displacement of its ordinary effects.

Reviewed security evidence uses `contracts.security-evidence.v0` with 60 mandatory predicates. Main-obligation existence, invalidity, and breach must replay from the formation, invalidity, and obligation stages. Security evidence cannot create or erase the underlying obligation.

Reviewed obligation-dynamics evidence uses `contracts.obligation-dynamics-evidence.v0` with 83 mandatory predicates. Obligation, breach, rendered performance, and proper-performance facts must replay from the general evidence and constraint stages. A party change is not treated as a discharge.

Reviewed performance-remedies evidence uses `contracts.performance-remedies-evidence.v0` with 96 mandatory predicates. Obligation, breach, tender, loss, causation, and monetary-delay facts are checked against the general evidence and obligation-dynamics stages. The model keeps proper, partial, early, third-party and reciprocal performance separate from damages, article 395 interest, specific relief, creditor delay, and article 406.1 indemnity.

Reviewed change-and-termination evidence uses `contracts.termination-evidence.v0` and contains all 36 predicates required by the narrow articles 310/450–453 model. Contract status must match the formation result, while proven substantial breach requires a breach in the obligation model.

Reviewed case evidence uses `contracts.case-evidence.v8`. The deterministic `contracts-reviewed-evidence-to-facts-v0` mapper produces the complete narrow `ObligationFactSet`: no absent predicate is silently treated as false. Every mapped fact retains its evidence assertion and source references. Duty and exception facts also retain links to the relevant formal condition or exception atoms from the reviewed norm.

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
- Draft case, temporal, authority, formation, invalidity, security, obligation-dynamics, performance-remedies, change-and-termination, or liability inputs cannot be analyzed.
- Every required formal fact has assertion and source provenance.
- Unknown sources, incomplete evidence, and coordinate mismatches fail closed.
- Authority resolution runs before formal constraint evaluation.
