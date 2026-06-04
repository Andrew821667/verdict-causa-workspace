# Translation and Explainability Layer Specification

The Translation Layer is not cosmetic UI. It is the bridge that lets a legal reviewer understand and govern machine-produced structures.

## Core function

Translate internal reasoning artifacts into faithful legal explanations without changing their meaning.

## Representation levels

### Executive

Short version for quick orientation:

- essential conclusion;
- main risk;
- key source;
- next action.

### Professional

Normal legal working explanation:

- legal terminology;
- source references;
- argument structure;
- caveats;
- disputed points.

### Forensic

Deep audit view:

- full provenance;
- rejected alternatives;
- formal constraints;
- graph references;
- policy version;
- candidate history;
- reasoning path comparison.

## Compare reasoning paths

The layer should compare:

- active logic vs candidate logic;
- standard profile vs conservative profile;
- without conflict resolution vs with conflict resolution;
- without counterfactual operator vs with counterfactual operator.

## Dual testing

### Faithfulness testing

Checks whether the explanation preserves the meaning of the underlying structure.

### Usability testing

Checks whether reviewers understand the candidate quickly and correctly.

Both are required. A faithful but unusable explanation fails. A usable but distorted explanation also fails.

## Phase 0 scope

Phase 0 should define:

- translation representation enum;
- translation artifact model;
- template version field;
- review note field;
- acceptance-test placeholders for faithfulness and usability.
