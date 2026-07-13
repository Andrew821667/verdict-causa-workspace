# Contracts RU v0 Changelog

## 0.16.0 - 2026-07-13

- Adds mandatory reviewed special-supply evidence with 82 provenance-backed predicates for articles 506–524 of the Russian Civil Code.
- Separates qualification, disagreement handling, periods, shipment orders, transport, short delivery, acceptance, responsible custody, selection, payment, containers, defects, completeness, cover purchase, penalty, allocation, unilateral refusal, and price damages.
- Enforces cross-model agreement for formation, delivery, delay, nonconformity, payment, breach, termination, loss, and causation.
- Preserves the contractual-only status of Instructions P-6 and P-7 in accordance with Plenum of the Supreme Arbitration Court Resolution No. 18.
- Adds 32 benchmarks, 32 adversarial checks, source metadata, and Russian professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v8`, analysis to `contracts-reviewed-analysis-v8`, and Russian templates to `ru-v10`.

## 0.15.0 - 2026-07-12

- Adds mandatory reviewed performance-remedies evidence with 96 provenance-backed predicates.
- Covers proper, partial, early, third-party, demand, alternative, facultative, solidary, and reciprocal performance under articles 309–328.
- Separates damages, replacement transactions, specific performance, article 395 interest, subsidiary and limited liability, debtor and creditor delay, and article 406.1 indemnity.
- Enforces cross-model agreement for obligation, breach, tender, loss, causation, and monetary-delay facts.
- Adds 27 benchmarks, 30 adversarial checks, official-source metadata, and Russian professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v7`, analysis to `contracts-reviewed-analysis-v7`, and Russian templates to `ru-v9`.

## 0.14.0 - 2026-07-12

- Adds mandatory reviewed obligation-dynamics evidence with 83 provenance-backed predicates.
- Covers assignment, debt transfer, contract transfer, performance, notary deposit, accord and satisfaction, set-off, novation, forgiveness, merger, impossibility, government act, death, and liquidation under articles 382–419.
- Keeps a party change distinct from discharge and separates full discharge, partial discharge, remaining debt, and accrued claims.
- Preserves debtor defenses, original-creditor performance before notice, cedent warranty issues, and third-party security effects.
- Adds 21 benchmarks, 22 adversarial checks, official-source metadata, and Russian professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v6`, analysis to `contracts-reviewed-analysis-v6`, and Russian templates to `ru-v8`.

## 0.13.0 - 2026-07-12

- Adds mandatory reviewed performance-security evidence with 60 provenance-backed predicates.
- Covers general accessory rules, penalty, pledge, retention, suretyship, independent guarantee, deposit, and security payment under Civil Code articles 329–381.2.
- Separates creation, third-party opposability, enforcement prerequisites, judicial and extrajudicial pledge routes, termination, regress, credit, and return issues.
- Preserves the independent nature of guarantees and the main obligation when a security instrument itself is defective.
- Adds 16 benchmarks, 16 adversarial checks, official-source metadata, and Russian professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v5`, analysis to `contracts-reviewed-analysis-v5`, and Russian templates to `ru-v7`.

## 0.12.0 - 2026-07-12

- Adds mandatory reviewed transaction-invalidity evidence with 51 provenance-backed predicates.
- Separates void and voidable grounds, standing, judgment, limitation, estoppel, and legal effects under Civil Code articles 166–181.
- Covers qualified illegality, immoral purpose, sham and feigned transactions, consent, authority, capacity, mistake, deception, threat, and adverse circumstances.
- Models partial invalidity, disguised-transaction rules, restitution, public-recovery issues, and additional damages without deciding a court outcome.
- Adds 14 benchmarks, 14 adversarial checks, Russian vocabulary, and professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v4`, analysis to `contracts-reviewed-analysis-v4`, and Russian templates to `ru-v6`.

## 0.11.0 - 2026-07-12

- Adds mandatory reviewed change-and-termination evidence with 36 provenance-backed predicates.
- Separates mutual agreement, judicial relief, unilateral action, and changed-circumstances paths under Civil Code articles 310 and 450–453.
- Keeps judicial prerequisites distinct from an effective judgment and validates delivery, pretrial procedure, form, good faith, and prior waiver.
- Models future-obligation termination, accrued-claim preservation, restitution issues, and termination-loss issues without deciding a court outcome.
- Adds 12 benchmarks, 12 adversarial checks, Russian vocabulary, and professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v3`, analysis to `contracts-reviewed-analysis-v3`, and Russian templates to `ru-v5`.

## 0.10.0 - 2026-07-12

- Adds mandatory reviewed contract-formation evidence with 17 provenance-backed predicates.
- Adds narrow formal boundaries for Civil Code articles 432, 435, 438, and 443 and Supreme Court Plenum Resolution No. 49.
- Separates essential terms, offer, express acceptance, acceptance by conduct, silence, counteroffer, required form, and bad-faith non-conclusion objections.
- Enforces agreement between formation results and contractual-duty evidence before breach and liability analysis.
- Adds ten formation benchmarks, ten adversarial checks, Russian vocabulary, and a Russian formation explanation section.
- Upgrades evidence to `contracts.case-evidence.v2`, analysis to `contracts-reviewed-analysis-v2`, and Russian templates to `ru-v4`.

## 0.9.0 - 2026-07-11

- Adds mandatory reviewed liability evidence with 20 provenance-backed predicates.
- Adds narrow formal prerequisite models for Civil Code articles 401 and 333.
- Separates fault rebuttal, force majeure, excluded commercial risks, notice, and intentional breach clauses.
- Separates procedural and substantive prerequisites for judicial penalty reduction without calculating an amount.
- Adds ten liability benchmarks and ten adversarial overreach checks.
- Upgrades evidence to `contracts.case-evidence.v1`, analysis to `contracts-reviewed-analysis-v1`, and Russian templates to `ru-v3`.

## 0.8.0 - 2026-07-11

- Adds a hash-addressed library of seven typed contractual legal operators.
- Adds deterministic one-step sensitivity analysis with immutable baseline facts.
- Enforces policy-controlled scenario and fact-change budgets, preconditions, and mandatory human review.
- Adds seven counterfactual benchmarks and seven adversarial bypass checks.
- Adds operator-library coordinates to decision traces and Russian professional/forensic explanations.
- Adds replay migration from `0.7.0` and updates the Translation Layer templates to `ru-v2`.

## 0.7.0 - 2026-07-11

- Adds versioned Russian templates for executive, professional, and forensic legal explanations.
- Adds shared structured legal assertions with exact source references across all three levels.
- Adds deterministic faithfulness checks by exact re-rendering from the reviewed trace.
- Adds structural usability checks while explicitly retaining the requirement for a lawyer pilot.
- Binds the translation template version and SHA-256 hash to the active policy and decision trace.
- Adds reasoning-path comparison, a standalone translation bundle, and replay migration from `0.6.0`.

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
