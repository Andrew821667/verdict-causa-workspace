# Contracts RU v0 Compatibility

## Compatibility Matrix

| Package version | Core version | Bootstrap schema | Translator | Status |
| --- | --- | --- | --- | --- |
| `0.3.0` | `0.1.0` | `contracts.norm.v0` | `contracts-json-to-formal-v0` | supported for synthetic Phase 0 |
| `0.2.0` | `0.1.0` | `contracts.norm.v0` | `contracts-json-to-formal-v0` | supported for synthetic Phase 0 |
| `0.1.0` | `0.1.0` | `contracts.norm.v0` | `contracts-json-to-formal-v0` | supported for synthetic Phase 0 |

This matrix is intentionally exact rather than a claim that every `0.3.x` combination is compatible. It is checked by `src/causa/institutional/contracts/versioning.py`.

## Migration Guide

For `0.2.0` to `0.3.0`, regenerate all synthetic reports and decision traces so their package coordinates and formal result shape are current. Reviewed norm JSON does not change; new formal result fields are additive.

For `0.1.0` to `0.2.0`, regenerate all synthetic reports and decision traces so their package coordinates and authority outcomes are current. Reviewed norm JSON and formal predicate names do not change in that release.

A future release that changes the reviewed norm schema, formal predicates, authority order, or benchmark result shape must provide:

1. a migration note for persisted reviewed JSON and exported traces;
2. a compatibility entry for the prior release;
3. benchmark and red-team deltas;
4. a rollback target.

## Rollback Path

If `0.3.0` proves unsafe or incompatible, pin `0.2.0` together with core `0.1.0`, schema `contracts.norm.v0`, and translator `contracts-json-to-formal-v0`, then regenerate the synthetic reports. No package version is production-approved in Phase 0.
