# Verdict / Causa Workspace

## Русскоязычный правовой контур

Вердикт — инфраструктура эволюционирующего юридического интеллекта, первое полноценное приложение которой создается для российской правовой системы на институте договорных отношений. Юридически значимые объяснения, причины выводов, предупреждения, governance-решения и audit-артефакты первого пакета формируются на русском языке. Английские machine IDs и поля API сохраняются только там, где это необходимо для совместимости и воспроизводимости.

Правило закреплено в [политике русского языка](docs/russian-language-policy.md).

Verdict / Causa Workspace is an early-stage open-source infrastructure project for auditable legal AI. It explores an evolving legal intelligence: a universal legal core, institutional packages, legal ontology, GraphRAG/RAG, governance workflows, a Management Plane, and formal consistency checks.

## What this project is

This project is a foundation for building legal AI systems whose reasoning can be inspected, challenged, versioned, and rolled back. It is designed around structured legal sources, candidate hypotheses, governance stages, institutional packages, and reproducible checks.

The long-term goal is not a single assistant, but infrastructure for legal reasoning systems that can evolve under explicit governance while preserving auditability, predictability, and rollback.

## What this project is not

This is not a generic legal chatbot, not a wrapper around an LLM, and not a production legal advice system.

It does not provide legal advice. It should not be used as a substitute for professional legal review.

## Core idea

Verdict / Causa Workspace separates legal AI infrastructure into a universal core and institution-specific packages. The core captures shared concepts such as sources, formalized norms, doctrine/meta-principles, case graphs, authority, temporal validity, confidence, auditability, and reproducibility.

Institutional packages provide vocabulary, authority model, temporal model, JSON schema, deterministic JSON-to-Z3 mapping rules, contradiction taxonomy, benchmark cases, red-team scenarios, confidence policies, and activation policies for specific legal institutes.

The governing concept is preserved in [docs/verdict-concept-v2-5.md](docs/verdict-concept-v2-5.md).

The first institutional package targets the Russian legal system. Stable machine IDs and API fields remain in English, while legally significant explanations, reasons, warnings, governance decisions, and audit artifacts are produced in Russian. See [docs/russian-language-policy.md](docs/russian-language-policy.md).

## Universal core and institutional packages

The universal core is intentionally jurisdiction-aware but not tied to a single legal domain. It is meant to support:

- legal source modeling;
- temporal validity;
- source hierarchy and authority;
- candidate legal hypotheses;
- GraphRAG/RAG retrieval;
- formal consistency checks;
- governance and rollback.

Institutional packages extend the core with domain-specific schemas, vocabularies, benchmark tasks, and review workflows.

## First institutional package: contractual relations

The first institutional package focuses on contractual relations: formation, change and termination, the general part of obligations, sale, supply, and liability for breach.

Релиз `contracts-ru-v0@0.18.0` добавляет контур допуска пилотных данных, который доказывает Этап 0 на максимально реалистичном споре о поставке, не обрабатывая реальные клиентские документы. Контур хранит только псевдонимные ссылки и хэши содержимого, фиксирует проверенное законное основание обработки и требует четырёх независимых согласований. Правила описаны в русской [спецификации допуска пилотных данных](docs/pilot-data-admission-spec.md).

Релиз `contracts-ru-v0@0.19.0` добавляет формальную модель действия договора во времени по статьям 425 и 433 ГК РФ: момент заключения, вступление в силу, обратное действие, истечение срока и сохранение ответственности за нарушение. Правила описаны в русской [спецификации действия договора во времени](docs/contract-temporal-effect-spec.md).

Релиз `contracts-ru-v0@0.20.0` добавляет формальную модель исковой давности по статьям 195–208 ГК РФ: начало течения, общий и специальный срок, предельный десятилетний срок, приостановление, перерыв, заявление стороны, восстановление и исключения. Правила описаны в русской [спецификации исковой давности](docs/contract-limitation-spec.md).

This is the first proving ground for the infrastructure, not the full scope of the project.

## Architecture

The initial architecture is organized around:

- Operational and generative contours;
- Universal Core;
- Knowledge Plane;
- Management Plane;
- Institutional Package Layer;
- Reasoning Layer;
- Governance Layer;
- Evaluation and Red Team Layer;
- Privacy and Tenant Safety Layer.

See [docs/architecture.md](docs/architecture.md) for details.

For Phase 0 implementation detail, see:

- [Phase 0 execution plan](docs/phase-0-execution-plan.md);
- [Universal core specification](docs/universal-core-spec.md);
- [Bootstrap pipeline specification](docs/bootstrap-pipeline-spec.md);
- [Management Plane specification](docs/management-plane-spec.md);
- [Translation Layer specification](docs/translation-layer-spec.md);
- [Bounded contractual counterfactual specification](docs/contract-counterfactual-spec.md);
- [Contract-formation prerequisite specification](docs/contract-formation-spec.md);
- [Transaction-invalidity specification](docs/contract-invalidity-spec.md);
- [Performance-security specification](docs/contract-security-spec.md);
- [Obligation-dynamics specification](docs/contract-obligation-dynamics-spec.md);
- [Performance and remedies specification](docs/contract-performance-remedies-spec.md);
- [General sale-contract specification](docs/contract-sale-spec.md);
- [Special supply-contract specification](docs/contract-supply-spec.md);
- [Contract change-and-termination specification](docs/contract-change-termination-spec.md);
- [Contractual liability and penalty prerequisite specification](docs/contract-liability-spec.md);
- [Evaluation and Red Team specification](docs/evaluation-and-red-team-spec.md);
- [Contracts RU v0 changelog](docs/contracts-ru-v0-changelog.md);
- [Contracts RU v0 compatibility matrix](docs/contracts-ru-v0-compatibility.md);
- [Phase 0 backlog](docs/phase-0-backlog.md).

## Governance and auditability

New legal hypotheses should not become active knowledge by default. They move through a governance pipeline that includes type classification, formal checks, source checks, benchmark checks, red-team testing, expert review, cross-review for high-impact candidates, sandboxing, activation, monitoring, revalidation, rejection, and rollback.

The current repository contains only the first skeleton of this workflow.

## Current status

This repository is at the early architectural/prototype stage. The project is not production-ready and should not be used as a substitute for legal advice. The current goal is to build an open-source foundation for auditable legal AI infrastructure.

## Roadmap

The roadmap starts with repository foundation and architecture, then moves toward Phase 0: universal core plus the first full institutional package for contractual relations. The true MVP is an auditable contradiction-aware legal reasoning engine with a working universal core, explicit Management Plane, and first institutional package.

See [docs/roadmap.md](docs/roadmap.md).

## Repository structure

```text
docs/       Architecture, concept, governance, security, roadmap.
examples/   Small example payloads for early prototypes.
scripts/    Repository and developer helper scripts.
src/causa/  Python package skeleton.
tests/      Minimal tests for the first models and pipeline.
```

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest
ruff check src tests
```

## Phase 0 synthetic trace

Generate the current synthetic supply-dispute trace:

```bash
python scripts/export_phase0_demo_trace.py
```

The output is written to `examples/phase0_supply_dispute_trace.json`. It is a non-production architecture demo, not legal advice.

Generate the standalone synthetic reviewed-input contract analysis:

```bash
python scripts/export_synthetic_reviewed_contract_analysis.py
```

The output is written to `examples/synthetic_reviewed_contract_analysis.json`.

Generate the synthetic Russian-language governance lifecycle report:

```bash
python scripts/export_synthetic_governance_lifecycle.py
```

The output is written to `examples/synthetic_governance_lifecycle_report.json`.

Generate the synthetic Russian-language Management Plane policy registry:

```bash
python scripts/export_synthetic_management_policy_registry.py
```

The output is written to `examples/synthetic_management_policy_registry_report.json`.

Generate the three-level Russian legal explanation with faithfulness and structural usability reports:

```bash
python scripts/export_synthetic_translation_bundle.py
```

The output is written to `examples/synthetic_translation_bundle_report.json`. Human usability still requires a lawyer pilot.

Generate the bounded contractual counterfactual report with dedicated benchmark and Red Team results:

```bash
python scripts/export_synthetic_counterfactual_evaluation.py
```

The output is written to `examples/synthetic_counterfactual_evaluation_report.json`. Every branch is hypothetical, budget-limited, and subject to lawyer review.

Generate the reviewed liability and penalty-reduction prerequisite report:

```bash
python scripts/export_synthetic_liability_evaluation.py
```

The output is written to `examples/synthetic_liability_evaluation_report.json`. It does not calculate a penalty reduction or predict a court outcome.

Generate the reviewed contract-formation prerequisite report:

```bash
python scripts/export_synthetic_formation_evaluation.py
```

The output is written to `examples/synthetic_formation_evaluation_report.json`. It checks offer, essential terms, form, and acceptance boundaries without deciding a court outcome.

Сформировать отчёт о действии договора во времени:

```bash
python scripts/export_synthetic_temporal_effect_evaluation.py
```

Результат записывается в `examples/synthetic_temporal_effect_evaluation_report.json`. Отчёт проверяет момент заключения, вступление в силу, обратное действие и окончание срока по статьям 425 и 433 ГК РФ и не подменяет судебную оценку.

Сформировать отчёт об исковой давности:

```bash
python scripts/export_synthetic_limitation_evaluation.py
```

Результат записывается в `examples/synthetic_limitation_evaluation_report.json`. Отчёт проверяет начало течения, срок, приостановление, перерыв и применение давности по статьям 195–208 ГК РФ и не подменяет судебную оценку.

Generate the reviewed contract change-and-termination report:

```bash
python scripts/export_synthetic_termination_evaluation.py
```

The output is written to `examples/synthetic_termination_evaluation_report.json`. It keeps agreement, judicial, and unilateral paths separate and does not predict a court outcome.

Generate the reviewed transaction-invalidity report:

```bash
python scripts/export_synthetic_invalidity_evaluation.py
```

The output is written to `examples/synthetic_invalidity_evaluation_report.json`. It distinguishes void and voidable grounds, procedure, and effects without replacing judicial assessment.

Generate the reviewed performance-security report:

```bash
python scripts/export_synthetic_security_evaluation.py
```

The output is written to `examples/synthetic_security_evaluation_report.json`. It keeps accessory security, independent guarantee, enforcement routes, and return consequences separate without deciding a court outcome.

Generate the reviewed obligation-dynamics report:

```bash
python scripts/export_synthetic_obligation_dynamics_evaluation.py
```

The output is written to `examples/synthetic_obligation_dynamics_evaluation_report.json`. It separates party changes from full and partial discharge paths without replacing judicial assessment.

Generate the reviewed performance-remedies report:

```bash
python scripts/export_synthetic_performance_remedies_evaluation.py
```

The output is written to `examples/synthetic_performance_remedies_evaluation_report.json`. It separates performance, delay, damages, interest, specific relief, and indemnity without calculating a court award.

Generate the reviewed general sale report for articles 454–491 of the Russian Civil Code:

```bash
python scripts/export_synthetic_sale_evaluation.py
```

The output is written to `examples/synthetic_sale_articles_454_491_report.json`. It separates transfer, risk, third-party rights, conformity, acceptance, payment, and remedies without deciding a court outcome.

Generate the reviewed special-supply report for articles 506–524 of the Russian Civil Code:

```bash
python scripts/export_synthetic_supply_evaluation.py
```

The output is written to `examples/synthetic_supply_articles_506_524_report.json`. It separates qualification, acceptance, short delivery, defects, unilateral refusal, and price damages without deciding a court outcome.

Generate the current Phase 0 readiness report:

```bash
python scripts/export_phase0_readiness_report.py
```

The output is written to `examples/phase0_readiness_report.json`.

Generate the synthetic supply benchmark report:

```bash
python scripts/export_synthetic_supply_benchmarks.py
```

The output is written to `examples/synthetic_supply_benchmark_report.json`.

Generate the synthetic supply practice-utility report:

```bash
python scripts/export_synthetic_supply_practice_utility.py
```

The output is written to `examples/synthetic_supply_practice_utility_report.json`.

Generate the synthetic privacy-safe pilot utility schema demo:

```bash
python scripts/export_privacy_safe_pilot_utility.py
```

The output is written to `examples/synthetic_privacy_safe_pilot_utility_report.json`.

Сформировать синтетическую репетицию допуска пилотных данных:

```bash
python scripts/export_synthetic_pilot_rehearsal.py
```

Результат записывается в `examples/synthetic_pilot_rehearsal_report.json`. Артефакт содержит только псевдонимный манифест и хэши содержимого; правила допуска описаны в [спецификации допуска пилотных данных](docs/pilot-data-admission-spec.md).

Generate the synthetic supply red-team report:

```bash
python scripts/export_synthetic_supply_red_team.py
```

The output is written to `examples/synthetic_supply_red_team_report.json`.

Generate the replay-required report for the legacy `contracts-ru-v0@0.1.0` fixture:

```bash
python scripts/export_contracts_package_migration_report.py
```

Команда формирует отчёты о необходимости replay для прежних релизов и пересобирает их относительно `0.20.0`. Отчёты сохраняются как `examples/migrations/contracts-ru-v0-<source>-to-0.20.0-migration-report.json` для `0.1.0`, `0.3.0` и каждого релиза с `0.4.0` по `0.19.0`. Прежние отчёты `*-to-0.17.0`, `*-to-0.18.0` и `*-to-0.19.0` сохраняются как исторические артефакты.

## License

Apache-2.0. See [LICENSE](LICENSE).
