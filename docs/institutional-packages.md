# Institutional Packages

Institutional packages extend the universal core with domain-specific legal structure.

Each package should define:

- schema;
- vocabulary;
- authority model;
- temporal model;
- JSON schema for bootstrap pipeline;
- deterministic JSON-to-Z3 mapping rules;
- contradiction taxonomy;
- typed legal operators;
- benchmark tasks;
- red-team scenarios;
- confidence policies;
- activation policies;
- governance requirements.

## First package

The first package is contractual relations. It covers general obligations and contract law, sale, supply, and liability for breach of obligations.

The package lives under `src/causa/institutional/contracts`.

Its current [changelog](contracts-ru-v0-changelog.md) and
[compatibility matrix](contracts-ru-v0-compatibility.md) are Phase 0 artifacts.

## Package lifecycle

Each institutional package should have a version tag, changelog, compatibility matrix with the universal core, migration guide, and rollback path.

## What does not belong inside a package

Translation templates and reasoning profiles are common infrastructure. A package may configure their use, but should not fork them into package-specific private systems.
