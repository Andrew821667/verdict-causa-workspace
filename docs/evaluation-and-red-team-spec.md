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

## Red Team

The Red Team component tries to use a candidate principle to justify unacceptable outcomes.

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

## Phase 0 artifacts

- benchmark task schema;
- red-team scenario schema;
- incident record schema;
- synthetic supply benchmark suite;
- synthetic supply practice-utility report;
- synthetic supply red-team suite.

The current suite is exported to `examples/synthetic_supply_benchmark_report.json`.
The current practice-utility report is exported to
`examples/synthetic_supply_practice_utility_report.json`.
The current red-team report is exported to `examples/synthetic_supply_red_team_report.json`.

For the contractual package, authority benchmarks record the rule used to resolve a candidate set: temporal applicability, higher authority, `lex specialis`, or unresolved equal authority. The initial resolver applies temporal validity before the package hierarchy `statutory > judicial > contractual > factual`; it does not use `lex specialis` across those levels.
