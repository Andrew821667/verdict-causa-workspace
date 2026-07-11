# Evaluation and Red Team Specification

Evaluation separates benchmark quality from practice utility.

## Benchmark quality

Measures whether the system reasons correctly on controlled tasks:

- source grounding accuracy;
- temporal applicability;
- authority ranking;
- contradiction detection;
- formal-check consistency;
- answer completeness.

## Practice utility

Measures whether the system helps a lawyer work better:

- time to useful draft;
- number of accepted arguments;
- number of human corrections;
- reviewer usefulness rating;
- number of "formally smart but practically useless" outputs.

The repository stores these separately in `PracticeUtilityObservation` and
`PracticeUtilityReport`. The initial contractual report is a synthetic Phase 0
baseline: it records time to useful draft, accepted arguments, human corrections,
reviewer usefulness rating, and explicitly retained examples of formally sound but
practically unhelpful output. It does not set production thresholds or claim pilot
evidence.

The repository also contains a separate privacy-safe pilot schema. It permits only an
opaque observation token, broad task category, collection date, consent/privacy flags,
and aggregate utility metrics. It forbids free text, client or tenant IDs, case IDs,
documents, and source excerpts. The exported report is a synthetic schema demo, not
real pilot data.

## Red Team

The Red Team component tries to use a candidate principle to justify unacceptable outcomes.

The current contractual suite uses a hybrid adversarial executor. Every scenario makes a
concrete attack attempt and retains the attempted and observed outcome. Where a narrow
formal or authority rule exists, the executor runs that rule against attack facts or
candidate sources. Source-grounding attacks query the source registry. Guardrail-fragment
checks remain only as a fallback for risks that have not yet been formalized, such as
penalty-reduction scope.

Attack wording is generated through a provider-neutral interface. CI uses a deterministic
template generator; deployments may inject a model callback, whose generated text is stored
as a review-required artifact. Model output is never executed as code and never translated
directly into formal constraints, authority inputs, or source references.

For contractual relations, initial scenario families include:

- using a broad fairness argument to ignore an explicit payment duty;
- using acceptance ambiguity to justify bad-faith non-payment;
- using a penalty-reduction pattern to erase all liability;
- using delivery defects to justify unrelated counterparty pressure;
- using limitation-period uncertainty to suppress a valid claim.

## Failure taxonomy

Operational failures should be classified as:

- hallucinated source grounding;
- bad formalization;
- wrong temporal applicability;
- wrong authority ranking;
- overbroad candidate principle;
- translation distortion;
- escalation failure;
- false confidence inflation;
- privacy leakage risk;
- benchmark overfitting.

Translation distortion is checked by rebuilding the shared structured assertions and exactly re-rendering all three Russian representation levels from the reviewed trace. Structural usability is evaluated separately; actual reviewer comprehension requires a lawyer pilot and cannot be inferred from deterministic faithfulness.

## Phase 0 artifacts

- benchmark task schema;
- red-team scenario schema;
- incident record schema;
- synthetic supply benchmark suite;
- synthetic supply practice-utility report;
- synthetic privacy-safe pilot utility schema demo;
- synthetic supply red-team suite.

The current suite is exported to `examples/synthetic_supply_benchmark_report.json`.
The current practice-utility report is exported to
`examples/synthetic_supply_practice_utility_report.json`.
The synthetic privacy-safe pilot utility schema demo is exported to
`examples/synthetic_privacy_safe_pilot_utility_report.json`.
The current red-team report is exported to `examples/synthetic_supply_red_team_report.json`.

For the contractual package, authority benchmarks record the rule used to resolve a candidate set: temporal applicability, higher authority, `lex specialis`, or unresolved equal authority. The synthetic Phase 0 resolver applies temporal validity before the policy `constitutional > statutory > regulatory > judicial > contractual > factual`; it does not use `lex specialis` across those levels.
