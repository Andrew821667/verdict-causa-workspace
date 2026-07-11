# First Institutional Package: Contractual Relations

The first institutional package focuses on contractual relations as a proving ground for the universal legal AI infrastructure.

## Scope

- General obligations: emergence, performance, transfer of parties, security, breach liability.
- General contract provisions: concept, conclusion, amendment, termination.
- Sale: general provisions.
- Supply as a special form of sale.
- Liability for breach, including penalty reduction and fault/liability issues.

## Why this package

Contractual disputes provide a practical testbed for source hierarchy, temporal validity, facts, claims, candidate hypotheses, contradiction checks, and governance.

They also exercise defeasible reasoning, principles and balancing, lex specialis questions, dispositive and mandatory norms, acceptance, payment, delivery defects, and limitation-period scenarios.

## Out of scope for Phase 0

- Invalidity of transactions.
- Unjust enrichment.
- Tort liability.
- Special contract types other than supply.
- Procedural institutes.

## Initial code

The current package contains a small schema for parties, obligations, relation type, and contract cases. It is intentionally minimal and should be expanded through governed changes.

The current executable subset includes reviewed contracts for case evidence, temporal evidence, and authority candidates. A fail-closed deterministic pipeline validates reviewer coordinates, source references, schema versions, case/date consistency, source applicability, and authority selection before running the narrow formal layer. Every formal input retains evidence provenance; duty and exception inputs also point back to reviewed norm atoms.

The package uses Russian for expert-facing legal text, reasons, warnings, governance decisions, and audit reports. Stable schema fields, enum values, and artifact IDs remain in English and have Russian labels where they are legally significant.

The package includes source revision conflicts with `valid_to` and an auditable authority resolver for constitutional, statutory, regulatory, judicial, contractual, and factual sources. It excludes temporally inapplicable sources first, applies the synthetic Phase 0 hierarchy second, and applies `lex specialis` only between equally authoritative sources. The formal layer separately records late performance, defect, payment default, basic damages-remedy availability, causation-evidence gaps, and stated limitation bars. Equal authority candidates and all substantive legal assessment remain for human review. This is a Phase 0 rule set, not a complete conflict-resolution engine.
