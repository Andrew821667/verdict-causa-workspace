# Universal Core Specification

The universal core is the reusable legal AI substrate. It is built once and configured through institutional packages.

## Design principle

The universal core must not encode contractual relations as privileged business logic. Contractual relations are the first institutional package, not the core itself.

## Required concepts

### Legal source

Represents a primary or secondary legal source.

Required fields:

- stable id;
- title;
- source type;
- jurisdiction;
- text or reference to text;
- valid-from and valid-to;
- authority metadata;
- provenance metadata.

### Legal claim

Represents a source-grounded assertion made by the system.

Required fields:

- stable id;
- text;
- source references;
- confidence score;
- risk level;
- trace reference.

### Candidate hypothesis

Represents a proposed legal conclusion or reasoning direction that is not yet active knowledge.

Required fields:

- stable id;
- statement;
- supporting sources;
- contradicting sources;
- risk level;
- status;
- governing policy version.

### Knowledge graph layers

The Knowledge Plane has four layers:

- `source`: primary legal sources, case law, doctrine, contracts, facts;
- `formal_norm`: reviewed and formalized norm representations;
- `doctrine`: candidate and active meta-principles, argument templates, calibration rules;
- `case`: facts, evidence, disputed points, claims, remedies, reasoning history.

Each layer has different privacy and lifecycle rules.

### Version coordinates

Every decision trace must identify:

- knowledge graph version;
- institutional package version;
- policy version;
- translation template version;
- model/provider profile if applicable.

## Source hierarchy

The core provides generic authority levels. Institutional packages define concrete ranking rules and conflict resolution rules.

The universal core should know that authority ranking exists. It should not know, by itself, how contractual lex specialis rules work.

## Temporal validity

The core provides validity windows and temporal checks. Institutional packages define how time matters in that legal institute.

Examples:

- contractual obligations may depend on the date the obligation arose;
- tax obligations may depend on tax-period rules;
- procedural rules may depend on filing or hearing dates.

## Confidence

Confidence is not a single model score. It is a governed artifact affected by:

- source authority;
- source completeness;
- temporal applicability;
- contradiction status;
- reviewer corrections;
- risk tier;
- policy version.

## Auditability

The core must support replay. A future replay should answer:

- what sources were used;
- what graph state was active;
- what policy state was active;
- what candidate principles were active;
- what checks passed or failed;
- what explanation template was used;
- what was rejected and why.

## Initial implementation scope

In the current repository, the universal core starts with:

- Pydantic models for sources, claims, hypotheses;
- validity window;
- authority level enum;
- confidence score;
- graph-layer model;
- trace version coordinates.

It is intentionally incomplete. The goal is to make the missing pieces explicit and testable.
