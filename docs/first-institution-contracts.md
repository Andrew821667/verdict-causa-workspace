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

- Unjust enrichment.
- Tort liability.
- Special contract types other than supply.
- Procedural institutes.

## Initial code

The current package contains a small schema for parties, obligations, relation type, and contract cases. It is intentionally minimal and should be expanded through governed changes.

The current executable subset includes reviewed contracts for case evidence, temporal evidence, and authority candidates. A fail-closed deterministic pipeline validates reviewer coordinates, source references, schema versions, case/date consistency, source applicability, and authority selection before running the narrow formal layer. Every formal input retains evidence provenance; duty and exception inputs also point back to reviewed norm atoms.

The package uses Russian for expert-facing legal text, reasons, warnings, governance decisions, and audit reports. Stable schema fields, enum values, and artifact IDs remain in English and have Russian labels where they are legally significant.

The package includes source revision conflicts with `valid_to` and an auditable authority resolver for constitutional, statutory, regulatory, judicial, contractual, and factual sources. It excludes temporally inapplicable sources first, applies the synthetic Phase 0 hierarchy second, and applies `lex specialis` only between equally authoritative sources. The formal layer separately records late performance, defect, payment default, basic damages-remedy availability, causation-evidence gaps, and stated limitation bars. Equal authority candidates and all substantive legal assessment remain for human review. This is a Phase 0 rule set, not a complete conflict-resolution engine.

The current package also includes a hash-addressed library of seven typed contractual legal operators. It performs one-step bounded sensitivity analysis without mutating reviewed facts, reruns the narrow formal model for every hypothetical branch, and exposes material changes in Russian professional and forensic explanations. Policy controls whether the analysis is allowed and caps both evaluated scenarios and changed facts. This is not a factual finding, legal prediction, or full counterfactual search engine.

Release `0.9.0` adds a separately reviewed evidence contract and narrow formal models for liability and judicial penalty reduction under articles 401 and 333 of the Russian Civil Code. It distinguishes fault rebuttal, force majeure, excluded commercial risks, notice, intentional breach clauses, a business debtor's reduction request, manifest disproportionality, and unjustified-benefit risk. The model never calculates a reduction amount or predicts a judicial outcome.

Release `0.10.0` adds a separately reviewed contract-formation evidence contract and narrow formal boundaries for articles 432, 435, 438, and 443 of the Russian Civil Code. It distinguishes essential terms, offer, express acceptance, acceptance by conduct, legally qualified silence, counteroffer, required form, and bad-faith non-conclusion objections. The formation result must support the contractual-duty fact before breach and liability analysis proceeds.

Release `0.11.0` adds separately reviewed evidence and formal paths for agreement-based, judicial, and unilateral change or termination under articles 310 and 450–453 of the Russian Civil Code. It keeps grounds, procedure, effective legal consequences, surviving accrued claims, restitution issues, and termination losses separate. Judicial prerequisites never substitute for an effective court judgment.

Release `0.12.0` adds reviewed transaction-invalidity evidence and formal boundaries for articles 166–181 of the Russian Civil Code. It separates void and voidable grounds, standing, limitation, judgment, estoppel, partial invalidity, restitution, and additional damages before ordinary contractual effects are evaluated.

Release `0.13.0` adds reviewed performance-security evidence and formal boundaries for articles 329–381.2 of the Russian Civil Code. It separates penalty, pledge, retention, suretyship, independent guarantee, deposit, and security payment, including accessory effects, third-party opposability, enforcement routes, termination, regress, credit, and return issues.

Release `0.14.0` adds reviewed obligation-dynamics evidence and formal boundaries for articles 382–419 of the Russian Civil Code. It separates assignment, debt and contract transfer from performance, notary deposit, accord, set-off, novation, forgiveness, merger, impossibility, government act, death, and liquidation discharge paths.

Release `0.15.0` adds reviewed performance-remedies evidence and formal boundaries for articles 309–328 and 393–406.1 of the Russian Civil Code. It separates proper, partial, early, third-party, solidary and reciprocal performance from damages, replacement transactions, article 395 interest, specific performance, debtor and creditor delay, and business indemnity.

Release `0.16.0` adds reviewed special-supply evidence and formal boundaries for articles 506–524 of the Russian Civil Code. It separates qualification, delivery periods, shipment orders, short delivery, acceptance, responsible custody, selection, payment, containers, defects, completeness, cover purchase, penalty, contract allocation, unilateral refusal, and price damages. The integrated pipeline rejects conflicts between special-supply facts and the general formation, temporal, performance, termination, and damages layers.

Release `0.17.0` adds reviewed general-sale evidence and formal boundaries for articles 454–491 of the Russian Civil Code. It separates subject, future goods, transfer, risk, third-party rights and eviction, quantity, assortment, quality and warranty, completeness, packaging, notice, acceptance, price, payment, credit, installment, insurance, and retained title. General sale facts must agree with the special supply layer wherever both models describe the same event.

Релиз `0.18.0` добавляет контур допуска пилотных данных v1: псевдонимный intake, fail-closed admission gate и связанный воспроизводимый run-манифест, которые доказывают Этап 0 на максимально реалистичном деле без обработки реальных клиентских документов. Он фиксирует проверенное законное основание для персональных данных, требует согласие субъекта только для основания согласия, обеспечивает минимизацию данных, tenant isolation, предельный срок хранения 90 дней и четыре независимых согласования, а также блокирует внешние модели, трансграничную передачу и запрещённые категории данных. Контур фиксирует только технические предпосылки; он не заменяет юридическую экспертизу, оценку информационной безопасности и privacy review. См. русскую [спецификацию допуска пилотных данных](pilot-data-admission-spec.md).
