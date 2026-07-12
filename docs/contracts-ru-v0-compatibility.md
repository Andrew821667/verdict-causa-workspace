# Contracts RU v0 Compatibility

## Compatibility Matrix

| Package version | Core | Norm schema | Evidence schema | Translator | Analysis pipeline | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `0.10.0` | `0.1.0` | `contracts.norm.v0` | `contracts.case-evidence.v2` | `contracts-json-to-formal-v0` | `contracts-reviewed-analysis-v2` | supported synthetic release with reviewed contract-formation prerequisites |
| `0.9.0` | `0.1.0` | `contracts.norm.v0` | `contracts.case-evidence.v1` | `contracts-json-to-formal-v0` | `contracts-reviewed-analysis-v1` | supported synthetic release with reviewed liability prerequisites |
| `0.8.0` | `0.1.0` | `contracts.norm.v0` | `contracts.case-evidence.v0` | `contracts-json-to-formal-v0` | `contracts-reviewed-analysis-v0` | supported synthetic release with bounded contractual legal operators |
| `0.7.0` | `0.1.0` | `contracts.norm.v0` | `contracts.case-evidence.v0` | `contracts-json-to-formal-v0` | `contracts-reviewed-analysis-v0` | supported synthetic release with Russian three-level Translation Layer |
| `0.6.0` | `0.1.0` | `contracts.norm.v0` | `contracts.case-evidence.v0` | `contracts-json-to-formal-v0` | `contracts-reviewed-analysis-v0` | supported synthetic release with immutable policy coordinates |
| `0.5.0` | `0.1.0` | `contracts.norm.v0` | `contracts.case-evidence.v0` | `contracts-json-to-formal-v0` | `contracts-reviewed-analysis-v0` | supported synthetic release with ru-RU audit layer |
| `0.4.0` | `0.1.0` | `contracts.norm.v0` | `contracts.case-evidence.v0` | `contracts-json-to-formal-v0` | `contracts-reviewed-analysis-v0` | supported for synthetic Phase 0 |
| `0.3.0` | `0.1.0` | `contracts.norm.v0` | n/a | `contracts-json-to-formal-v0` | n/a | historical synthetic release |
| `0.2.0` | `0.1.0` | `contracts.norm.v0` | n/a | `contracts-json-to-formal-v0` | n/a | historical synthetic release |
| `0.1.0` | `0.1.0` | `contracts.norm.v0` | n/a | `contracts-json-to-formal-v0` | n/a | historical synthetic release |

This matrix is intentionally exact rather than a claim that every `0.10.x` combination is compatible. The current coordinates are checked by `src/causa/institutional/contracts/versioning.py`.

## Migration Guide

For `0.9.0` to `0.10.0`, preserve the old trace and collect separately reviewed `contracts.formation-evidence.v0` input. Do not infer offer, essential terms, acceptance, form, or bad faith from the former `duty_exists` value. Regenerate formation, analysis, translation, Phase 0 trace, readiness, benchmark, Red Team, and migration artifacts under evidence schema `v2` and pipeline `v2`.

For `0.8.0` to `0.9.0`, preserve the old trace and collect a separately reviewed `contracts.liability-evidence.v0` input. Do not infer fault, force majeure, disproportionality, unjustified benefit, or procedural statements from the former breach result. Regenerate analysis, policy, translation, liability evaluation, Phase 0 trace, and readiness artifacts under evidence schema `v1` and analysis pipeline `v1`.

For `0.7.0` to `0.8.0`, preserve the old reviewed trace and regenerate analysis, policy registry, Translation Layer, Phase 0 trace, and readiness artifacts. Counterfactual scenarios cannot be inferred from the former free-form explanation. They must be replayed against the hash-addressed operator library and the policy-controlled budget.

For `0.6.0` to `0.7.0`, preserve the old trace and regenerate the Management Plane registry, Translation Layer bundle, governance artifact, trace, and readiness report. A historical template version without its content hash cannot prove which text governed the explanation. Old free-form explanation text must not be promoted into the new structured assertions by inference.

For `0.5.0` to `0.6.0`, preserve the old trace and regenerate it through the Management Plane registry. A historical policy version string does not prove the policy payload and cannot be assigned a content hash retrospectively. The current trace must obtain its snapshot ID and hash from a replayed registry state.

For `0.4.0` to `0.5.0`, preserve the old reviewed-analysis artifact and regenerate all expert-facing reports. Russian reasons and governance decisions must be produced by the current code; they must not be inferred by translating historical English text. Machine IDs, norm schema, evidence schema, and translator coordinates remain compatible.

For `0.3.0` to `0.4.0`, preserve the old trace as evidence and regenerate it through the reviewed analysis pipeline. Direct, unversioned `ObligationFactSet` input is not upgraded by inference. Case, temporal, and authority inputs must be explicitly reviewed under the new schema.

For `0.2.0` to `0.3.0`, regenerate all synthetic reports and decision traces so their package coordinates and formal result shape are current. Reviewed norm JSON does not change; new formal result fields are additive.

For `0.1.0` to `0.2.0`, regenerate all synthetic reports and decision traces so their package coordinates and authority outcomes are current. Reviewed norm JSON and formal predicate names do not change in that release.

The replay-required path is exercised by the legacy fixture in
`examples/migrations/contracts-ru-v0-0.1.0-benchmark-report.json` and its
generated migration report. The migration preserves legacy payloads as evidence;
it never infers new authority or formal results from old output.

A future release that changes the reviewed norm schema, formal predicates, authority order, or benchmark result shape must provide:

1. a migration note for persisted reviewed JSON and exported traces;
2. a compatibility entry for the prior release;
3. benchmark and red-team deltas;
4. a rollback target.

## Rollback Path

If `0.10.0` proves unsafe or incompatible, pin `0.9.0` together with core `0.1.0`, norm schema `contracts.norm.v0`, evidence schema `contracts.case-evidence.v1`, translator `contracts-json-to-formal-v0`, and pipeline `contracts-reviewed-analysis-v1`. Preserve `0.10.0` formation evidence and evaluations as audit evidence, but do not backfill their conclusions into `0.9.0`. No package version is production-approved in Phase 0.
