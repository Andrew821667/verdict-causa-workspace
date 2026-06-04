# Security Model

This repository is an early prototype and does not process production data.

## Data boundaries

The repository must not contain:

- real client documents;
- personal data;
- production secrets;
- private legal matter files;
- real confidential court or transaction materials.

## Future tenant safety

Future implementations should provide:

- strict tenant isolation;
- separate public legal knowledge and private matter knowledge;
- data minimization;
- customer-specific doctrine boundaries;
- encrypted storage for sensitive artifacts;
- audit trails for retrieval, reasoning, governance, and export operations.

## Secrets

Secrets should be provided through environment variables or secret stores and never committed.
