# Contracts RU v0 Compatibility

## Compatibility Matrix

| Package version | Core version | Bootstrap schema | Translator | Status |
| --- | --- | --- | --- | --- |
| `0.1.0` | `0.1.0` | `contracts.norm.v0` | `contracts-json-to-formal-v0` | supported for synthetic Phase 0 |

This matrix is intentionally exact rather than a claim that every `0.1.x` combination is compatible. It is checked by `src/causa/institutional/contracts/versioning.py`.

## Migration Guide

There is no earlier public package release to migrate from. A future release that changes the reviewed norm schema, formal predicates, authority order, or benchmark result shape must provide:

1. a migration note for persisted reviewed JSON and exported traces;
2. a compatibility entry for the prior release;
3. benchmark and red-team deltas;
4. a rollback target.

## Rollback Path

If a package release proves unsafe or incompatible, pin the previous package version together with its matching core, schema, and translator coordinates. Re-run the synthetic benchmark, practice-utility, and red-team reports before restoring activation. No package version is production-approved in Phase 0.
