# Phase 0 Execution Plan

Phase 0 is the proof that the universal core works when loaded with the first full institutional package. It is not a demo chatbot and not a narrow contract helper. It is the first end-to-end validation of the architecture described in [verdict-concept-v2-5.md](verdict-concept-v2-5.md).

## Goal

Build enough of the universal core and the contractual relations institutional package to produce reproducible, source-grounded, policy-aware, contradiction-aware decision traces on representative contractual cases.

## Non-goals

- Production legal advice.
- Real client document storage.
- Full autonomous legal reasoning.
- Broad coverage of many legal institutes.
- Direct LLM-to-Z3 translation.
- Silent activation of generated principles.
- Per-user customization of reasoning behavior.

## Phase 0 workstreams

### WS0. Repository and contributor foundation

Deliverables:

- public repository;
- Apache-2.0 license;
- contribution and maintainer workflow docs;
- CI for tests and linting;
- issue backlog and labels;
- honest project status.

Acceptance criteria:

- CI passes on `main`;
- README and docs explicitly state prototype status;
- no production-readiness or legal-advice claims.

### WS1. Universal core data model

Deliverables:

- legal source model;
- source hierarchy and temporal validity;
- legal claim and candidate hypothesis model;
- four graph-layer model: Source, Formal Norm, Doctrine, Case;
- provenance and audit metadata;
- version identifiers for Knowledge Plane and Management Plane.

Acceptance criteria:

- models validate with Pydantic;
- tests cover invalid confidence, graph-layer typing, and source references;
- every decision trace can point to knowledge and policy versions.

### WS2. Knowledge Plane skeleton

Deliverables:

- Source Graph node types;
- Formal Norm Graph placeholder representation;
- Doctrine / Meta-Principle Graph candidate representation;
- Case Graph representation;
- basic graph-building utility;
- source-grounding links from claims to sources.

Acceptance criteria:

- a sample contractual case can be represented as a Case Graph;
- claims can link to legal sources;
- graph nodes preserve provenance metadata.

### WS3. Neuro-symbolic bootstrap pipeline

Deliverables:

- JSON schema for reviewed legal norm representations;
- Domain Owner review status;
- deterministic translation interface from reviewed JSON to formal checks;
- explicit ban on direct LLM-to-Z3 generation;
- tests for schema validation and review gating.

Acceptance criteria:

- unreviewed JSON cannot be translated;
- one sample contractual norm representation can be validated;
- the current Z3 code remains clearly marked as placeholder.

### WS4. First institutional package: contractual relations

Deliverables:

- package manifest;
- vocabulary;
- authority model;
- temporal model;
- contradiction taxonomy;
- typed legal operators;
- benchmark suite outline;
- red-team scenario library outline;
- confidence policies;
- activation policies;
- Domain Owner responsibility document.

Acceptance criteria:

- package manifest is machine-readable;
- all required package sections are present;
- tests verify package completeness.

### WS5. Management Plane

Deliverables:

- SLA/depth modes: `draft`, `standard`, `deep`, `research`;
- risk tiers T1-T6;
- policy matrix for `mode x tier`;
- cost budget model;
- rollback classes;
- versioned policy identifier.

Acceptance criteria:

- a case policy can bind mode, tier, cost budget, and review requirements;
- high-risk tiers require replayable trace and human review;
- policy changes are modeled separately from knowledge changes.

### WS6. Governance pipeline

Deliverables:

- candidate type taxonomy;
- governance stages;
- governance profile per candidate type;
- red-team check stage;
- cross-review requirement for high-impact candidates;
- pre-activation sandbox model;
- expiration and revalidation metadata;
- rollback metadata.

Acceptance criteria:

- each candidate type has a governance profile;
- `meta_principle` and `conflict_resolution_pattern` require sandbox;
- rejected candidates preserve reasons;
- terminal stages are stable.

### WS7. Translation and explainability layer

Deliverables:

- representation levels: `executive`, `professional`, `forensic`;
- translation bundle with shared structured assertions;
- comparison of the reviewed path and an unsafe shortcut;
- deterministic faithfulness and structural usability reports;
- template version and content hash in Management Plane.

Acceptance criteria:

- governance review artifacts can include all three representation levels;
- Translation Layer templates are treated as policy artifacts, not casual UI copy;
- human usability remains subject to a lawyer pilot.

### WS8. Evaluation, benchmark, and red-team

Deliverables:

- benchmark task format;
- red-team scenario format;
- failure taxonomy;
- incident record model;
- separation of benchmark quality and practice utility.

Acceptance criteria:

- at least one benchmark task and one red-team scenario exist for supply disputes;
- failures can be classified using the taxonomy;
- benchmark and practice-utility metrics are stored separately.

### WS9. Zero-to-Value track

Deliverables:

- pilot-style task selection;
- initial 15-30 norm bootstrap target list;
- basic case graph demonstration;
- source grounding demonstration;
- formal contradiction demonstration;
- three-level Russian translation demonstration with deterministic checks.

Acceptance criteria:

- a non-confidential, synthetic case can run through the skeleton;
- the result is clearly marked non-production and non-legal-advice;
- gaps are recorded as engineering backlog, not hidden.

## Phase 0 done means

Phase 0 is not done when the repository looks polished. It is done when the system can run a representative contractual case through an auditable path:

1. legal source selected;
2. source represented as reviewed bootstrap JSON;
3. first deterministic structured formal output and narrow constraint set attached;
4. case graph built;
5. claim generated with source grounding;
6. contradiction or gap classified;
7. candidate principle proposed;
8. governance profile applied;
9. Management Plane policy recorded;
10. three-level translation bundle and dual reports produced;
11. decision trace exported;
12. tests verify the path.

## Phase 0 risk register

| Risk | Signal | Response |
| --- | --- | --- |
| Bootstrap JSON too slow to review | Domain Owner review is not faster than writing formal rules manually | simplify schema and review UI assumptions |
| Translation Layer unusable | reviewer cannot understand candidate in 5-15 minutes | redesign representation levels and templates |
| Governance too expensive | candidate review cost exceeds expected value | narrow candidate types and reduce optional checks |
| Contract package too broad | package cannot reach coherent first coverage | split work into clearly versioned subpackages |
| Formal layer overreach | evaluative standards are forced into Z3 | route them to principles and balancing layer |
| Quiet policy drift | prompts or thresholds change without versioning | treat templates and policies as versioned artifacts |

## Immediate next milestones

1. Obtain privacy and human-review approval before collecting non-synthetic pilot observations.
2. Integrate a reviewed external model provider for attack wording under tenant and privacy controls.
3. Replace the synthetic authority policy with a jurisdiction-reviewed policy before using non-synthetic sources.
4. Expand reviewed evidence mappings beyond the current narrow boolean contractual subset.
5. Add migration fixtures for every future semantic package release.

## Current synthetic trace

The repository now includes:

- `examples/phase0_supply_dispute_trace.json`, generated by `scripts/export_phase0_demo_trace.py`;
- `examples/phase0_readiness_report.json`, generated by `scripts/export_phase0_readiness_report.py`;
- `examples/synthetic_reviewed_contract_analysis.json`, generated by `scripts/export_synthetic_reviewed_contract_analysis.py`;
- `examples/synthetic_governance_lifecycle_report.json`, generated by `scripts/export_synthetic_governance_lifecycle.py`;
- `examples/synthetic_management_policy_registry_report.json`, generated by `scripts/export_synthetic_management_policy_registry.py`;
- `examples/synthetic_translation_bundle_report.json`, generated by `scripts/export_synthetic_translation_bundle.py`;
- `examples/synthetic_counterfactual_evaluation_report.json`, generated by `scripts/export_synthetic_counterfactual_evaluation.py`;
- `examples/synthetic_liability_evaluation_report.json`, generated by `scripts/export_synthetic_liability_evaluation.py`;
- `examples/synthetic_formation_evaluation_report.json`, generated by `scripts/export_synthetic_formation_evaluation.py`;
- `examples/synthetic_invalidity_evaluation_report.json`, generated by `scripts/export_synthetic_invalidity_evaluation.py`;
- `examples/synthetic_security_evaluation_report.json`, generated by `scripts/export_synthetic_security_evaluation.py`;
- `examples/synthetic_obligation_dynamics_evaluation_report.json`, generated by `scripts/export_synthetic_obligation_dynamics_evaluation.py`;
- `examples/synthetic_termination_evaluation_report.json`, generated by `scripts/export_synthetic_termination_evaluation.py`;
- `examples/synthetic_supply_benchmark_report.json`, generated by `scripts/export_synthetic_supply_benchmarks.py`;
- `examples/synthetic_supply_practice_utility_report.json`, generated by `scripts/export_synthetic_supply_practice_utility.py`;
- `examples/synthetic_privacy_safe_pilot_utility_report.json`, generated by `scripts/export_privacy_safe_pilot_utility.py`;
- `examples/synthetic_supply_red_team_report.json`, generated by `scripts/export_synthetic_supply_red_team.py`;
- `examples/migrations/contracts-ru-v0-0.1.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.3.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.4.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.5.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.6.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.7.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.8.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.9.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.10.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.11.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.12.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.13.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.14.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/migrations/contracts-ru-v0-0.15.0-to-0.16.0-migration-report.json`, generated by `scripts/export_contracts_package_migration_report.py`;
- `examples/synthetic_performance_remedies_evaluation_report.json`, generated by `scripts/export_synthetic_performance_remedies_evaluation.py`.

It demonstrates the intended Phase 0 path:

1. synthetic legal source;
2. reviewed bootstrap JSON;
3. reviewed case, temporal, and authority inputs with complete source provenance;
4. deterministic formation, invalidity, obligation, performance-security, change-and-termination, and liability analysis with authority/source applicability checks and bounded counterfactual sensitivity;
5. source-grounded legal claim;
6. proposed candidate gap heuristic;
7. исполненный governance-жизненный цикл с русскими причинами решений;
8. governance profile;
9. активный hash-addressed snapshot политики `standard x T3` и журнал его версий;
10. red-team scenario;
11. three-level Russian translation bundle with faithfulness and usability reports;
12. decision trace with knowledge, package, policy, translation, legal-operator, and model-profile coordinates.

The trace is non-production and is not legal advice.

The readiness report is also intentionally conservative: it marks Phase 0 as an architectural prototype, records warnings for narrow institutional coverage and incomplete non-synthetic evaluation, and keeps `ready_for_production` set to `false`. WS7 is passed for the implemented synthetic scope, while real usability remains dependent on a lawyer pilot.
