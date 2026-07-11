# Contracts RU v0 Changelog

## 0.6.0 - 2026-07-11

- Adds immutable Management Plane policy snapshots with canonical SHA-256 content hashes.
- Adds typed Russian semantic diffs for policy tightening, relaxation, and behavioral changes.
- Adds append-only registration, activation, and rollback events with optimistic revision checks.
- Adds an atomic JSON persistence backend with stale-write protection for local replay.
- Binds Phase 0 decision traces and governance records to the active snapshot ID and content hash.
- Adds replay-required migration fixtures from `0.1.0`, `0.3.0`, `0.4.0`, and `0.5.0`.

## 0.5.0 - 2026-07-11

- Adds mandatory Russian human-readable labels for governance, risk, failure, and policy values.
- Adds parallel Russian reasons for temporal, source-applicability, authority, and formal evaluations.
- Adds an executable governance engine with stored decisions, sandbox, activation, revalidation, and rollback records.
- Converts the key synthetic legal sources, claims, candidate, explanation, readiness report, and warnings to Russian.
- Keeps stable machine IDs and English compatibility fields unchanged.
- Adds replay-required migration fixtures from `0.1.0`, `0.3.0`, and `0.4.0`.

## 0.4.0 - 2026-07-11

- Adds reviewed case-evidence, temporal-evidence, and authority-input contracts.
- Adds a fail-closed end-to-end analysis pipeline with source, case, date, schema, and review validation.
- Maps every narrow formal fact from an explicit reviewed assertion and retains source provenance.
- Links duty and exception facts to reviewed formal atoms.
- Adds a standalone synthetic reviewed-analysis artifact and migrates the Phase 0 trace to it.
- Adds replay-required migration fixtures from both `0.1.0` and `0.3.0`.

## 0.3.0 - 2026-07-11

- Adds synthetic formal predicates for basic damages remedy availability, causation-evidence gaps, and stated limitation bars.
- Adds benchmark and adversarial checks that reject remedies without causation or despite a stated limitation bar.
- Does not calculate loss, establish causation, or compute limitation dates.

## 0.2.0 - 2026-07-11

- Adds a synthetic-reviewed authority policy with constitutional and regulatory levels.
- Adds benchmark and adversarial checks for constitutional/statutory/regulatory ordering.
- Adds migration and rollback guidance for the preceding package release.

## 0.1.0 - 2026-07-11

- Initial Phase 0 contractual package release.
- Adds synthetic supply sources, temporal applicability, and source-revision cases.
- Adds statutory, judicial, contractual, and factual authority resolution with scoped `lex specialis`.
- Adds narrow formal checks for late performance, confirmed defect, and payment default.
- Adds benchmark, practice-utility baseline, and hybrid adversarial red-team artifacts.

## Versioning policy

- Package releases use semantic versioning.
- A package release must update the compatibility matrix, migration guide, and rollback notes.
- Changes to authority, formal rules, or evaluation semantics require benchmark and red-team evidence.
