# Contracts RU v0 Compatibility

## Compatibility Matrix

| Package version | Core | Norm schema | Evidence schema | Translator | Analysis pipeline | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `0.5.0` | `0.1.0` | `contracts.norm.v0` | `contracts.case-evidence.v0` | `contracts-json-to-formal-v0` | `contracts-reviewed-analysis-v0` | supported synthetic release with ru-RU audit layer |
| `0.4.0` | `0.1.0` | `contracts.norm.v0` | `contracts.case-evidence.v0` | `contracts-json-to-formal-v0` | `contracts-reviewed-analysis-v0` | supported for synthetic Phase 0 |
| `0.3.0` | `0.1.0` | `contracts.norm.v0` | n/a | `contracts-json-to-formal-v0` | n/a | historical synthetic release |
| `0.2.0` | `0.1.0` | `contracts.norm.v0` | n/a | `contracts-json-to-formal-v0` | n/a | historical synthetic release |
| `0.1.0` | `0.1.0` | `contracts.norm.v0` | n/a | `contracts-json-to-formal-v0` | n/a | historical synthetic release |

This matrix is intentionally exact rather than a claim that every `0.5.x` combination is compatible. The current coordinates are checked by `src/causa/institutional/contracts/versioning.py`.

## Migration Guide

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

If `0.5.0` proves unsafe or incompatible, pin `0.4.0` together with core `0.1.0`, norm schema `contracts.norm.v0`, evidence schema `contracts.case-evidence.v0`, translator `contracts-json-to-formal-v0`, and pipeline `contracts-reviewed-analysis-v0`. Russian audit fields and governance records from `0.5.0` must not be silently imported into `0.4.0`. No package version is production-approved in Phase 0.
