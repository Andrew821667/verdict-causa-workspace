# Contracts RU v0 Changelog

## 0.30.0 - 2026-07-25

- Добавляет отдельный проверенный контракт данных о рамочном договоре (договоре с открытыми условиями) и абонентском договоре (договоре с исполнением по требованию) и формальную модель статей 429.1 и 429.4 ГК РФ (`src/causa/institutional/contracts/framework.py`).
- Разделяет определение общих условий обязательственных взаимоотношений, их конкретизацию отдельными договорами или заявками, применение общих условий рамочного договора к неурегулированным отношениям, право абонента требовать исполнение и его обязанность вносить плату независимо от того, было ли исполнение затребовано.
- Различает рамочный договор (статья 429.1) и абонентский договор (статья 429.4).
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-framework-constructions` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-framework-spec.md`](contract-framework-spec.md) и синтетический артефакт `examples/synthetic_framework_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.29.0 → 0.30.0` относится к допуску данных о рамочном и абонентском договоре, а не к изменению прежних юридических выводов.

## 0.29.0 - 2026-07-25

- Добавляет отдельный проверенный контракт данных об опционе на заключение договора и опционном договоре и формальную модель статей 429.2 и 429.3 ГК РФ (`src/causa/institutional/contracts/option.py`).
- Разделяет действительность безотзывной оферты (определённость условий, возмездность), заключение основного договора акцептом в срок, прекращение опциона при пропуске срока, передаваемость права, право требовать по опционному договору, его прекращение по истечении срока и невозвратность платежа.
- Различает опцион на заключение договора (статья 429.2) и опционный договор (статья 429.3).
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-option-constructions` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-option-spec.md`](contract-option-spec.md) и синтетический артефакт `examples/synthetic_option_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.28.0 → 0.29.0` относится к допуску данных об опционных конструкциях, а не к изменению прежних юридических выводов.

## 0.28.0 - 2026-07-25

- Добавляет отдельный проверенный контракт данных о преддоговорной ответственности и формальную модель статьи 434.1 ГК РФ (`src/causa/institutional/contracts/precontractual.py`).
- Разделяет недобросовестное ведение переговоров (неполная или недостоверная информация, внезапное и неоправданное прекращение), нарушение конфиденциальности сведений, полученных в переговорах, возмещение убытков и ничтожность соглашений об ограничении такой ответственности.
- Различает ответственность независимо от заключения договора (пункты 3 и 7 статьи 434.1) и ничтожность ограничения ответственности за недобросовестные действия (пункт 5).
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-precontractual-liability` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-precontractual-spec.md`](contract-precontractual-spec.md) и синтетический артефакт `examples/synthetic_precontractual_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.27.0 → 0.28.0` относится к допуску данных о преддоговорной ответственности, а не к изменению прежних юридических выводов.

## 0.27.0 - 2026-07-25

- Добавляет отдельный проверенный контракт данных о заверениях об обстоятельствах и формальную модель статьи 431.2 ГК РФ (`src/causa/institutional/contracts/representations.py`).
- Разделяет недостоверное заверение, имеющее значение для договора, основание ответственности (предпринимательский или корпоративный контекст либо знание о недостоверности), доверие полагавшейся стороны и последствия — возмещение убытков или неустойку, право на отказ от договора и оспаривание при обмане.
- Различает ответственность независимо от признания договора незаключённым или недействительным (пункт 1 статьи 431.2), отказ от договора при существенном значении (пункт 2) и оспаривание по статье 179 (пункт 3).
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-representations` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-representations-spec.md`](contract-representations-spec.md) и синтетический артефакт `examples/synthetic_representations_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.26.0 → 0.27.0` относится к допуску данных о заверениях об обстоятельствах, а не к изменению прежних юридических выводов.

## 0.26.0 - 2026-07-25

- Добавляет отдельный проверенный контракт данных о договоре присоединения и формальную модель статьи 428 ГК РФ (`src/causa/institutional/contracts/adhesion.py`).
- Разделяет режим договора присоединения (включая распространение при явном неравенстве переговорных возможностей), основания для изменения или расторжения (лишение обычных прав, исключение ответственности другой стороны, явно обременительные условия) и ограничение для присоединившегося предпринимателя, знавшего условия.
- Различает доступность изменения или расторжения по требованию присоединившейся стороны и ограничение по пункту 2 статьи 428 для предпринимателя.
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-adhesion-contract` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-adhesion-spec.md`](contract-adhesion-spec.md) и синтетический артефакт `examples/synthetic_adhesion_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.25.0 → 0.26.0` относится к допуску данных о договоре присоединения, а не к изменению прежних юридических выводов.

## 0.25.0 - 2026-07-25

- Добавляет отдельный проверенный контракт данных о публичном договоре и формальную модель статьи 426 ГК РФ (`src/causa/institutional/contracts/public_contract.py`).
- Разделяет обязанность заключить договор с каждым обратившимся, недопустимость необоснованного отказа, недопустимость предпочтения, единство условий для соответствующей категории и ничтожность условий, противоречащих публичному режиму.
- Различает понуждение к заключению и возмещение убытков при необоснованном уклонении (пункт 3 статьи 426, пункт 4 статьи 445) и ничтожность условий (пункт 5 статьи 426).
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-public-contract` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-public-spec.md`](contract-public-spec.md) и синтетический артефакт `examples/synthetic_public_contract_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.24.0 → 0.25.0` относится к допуску данных о публичном договоре, а не к изменению прежних юридических выводов.

## 0.24.0 - 2026-07-25

- Добавляет отдельный проверенный контракт данных о договоре в пользу третьего лица и формальную модель статьи 430 ГК РФ (`src/causa/institutional/contracts/third_party.py`).
- Разделяет заключение и действительность договора в пользу третьего лица, право третьего лица требовать исполнения, связанность сторон после выражения намерения и последствия отказа третьего лица от права.
- Различает необходимость согласия третьего лица на изменение и расторжение после выражения им намерения (пункт 2 статьи 430) и переход права к кредитору при отказе третьего лица (пункт 4 статьи 430).
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-third-party-contract` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-third-party-spec.md`](contract-third-party-spec.md) и синтетический артефакт `examples/synthetic_third_party_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.23.0 → 0.24.0` относится к допуску данных о договоре в пользу третьего лица, а не к изменению прежних юридических выводов.

## 0.23.0 - 2026-07-25

- Добавляет отдельный проверенный контракт данных о предварительном договоре и формальную модель статьи 429 и пункта 4 статьи 445 ГК РФ (`src/causa/institutional/contracts/preliminary.py`).
- Разделяет заключение и действительность предварительного договора (форма, определённость предмета основного договора, согласование спорных условий), срок заключения основного договора, уклонение стороны, понуждение к заключению и возмещение убытков, а также прекращение обязательств.
- Различает ничтожность при несоблюдении формы (пункт 2 статьи 429), понуждение к заключению при своевременном требовании в течение шести месяцев (пункт 5 статьи 429, пункт 4 статьи 445) и прекращение обязательств по истечении срока (пункт 6 статьи 429).
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-preliminary-contract` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-preliminary-spec.md`](contract-preliminary-spec.md) и синтетический артефакт `examples/synthetic_preliminary_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.22.0 → 0.23.0` относится к допуску данных о предварительном договоре, а не к изменению прежних юридических выводов.

## 0.22.0 - 2026-07-24

- Добавляет отдельный проверенный контракт данных о форме сделки и формальную модель статей 158–165 и 434 ГК РФ (`src/causa/institutional/contracts/form.py`).
- Разделяет требуемую форму (устная, простая письменная, нотариальная), допустимые способы соблюдения письменной формы (подписанный сторонами документ, обмен документами, действительная электронная подпись) и последствия несоблюдения формы.
- Различает лишение права ссылаться на свидетельские показания (пункт 1 статьи 162) и ничтожность сделки при несоблюдении нотариальной формы либо письменной формы, когда закон или соглашение прямо связывают с этим недействительность (пункт 2 статьи 162, пункт 3 статьи 163).
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-transaction-form` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-form-spec.md`](contract-form-spec.md) и синтетический артефакт `examples/synthetic_form_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.21.0 → 0.22.0` относится к допуску данных о форме сделки, а не к изменению прежних юридических выводов.

## 0.21.0 - 2026-07-24

- Добавляет отдельный проверенный контракт данных о толковании договора и формальную модель статьи 431 ГК РФ (`src/causa/institutional/contracts/interpretation.py`).
- Разделяет буквальное толкование, сопоставление с другими условиями и смыслом договора в целом, установление действительной общей воли сторон с учётом цели, переговоров, практики, обычаев и последующего поведения, а также толкование против стороны, подготовившей условие.
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-contract-interpretation` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-interpretation-spec.md`](contract-interpretation-spec.md) и синтетический артефакт `examples/synthetic_interpretation_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.20.0 → 0.21.0` относится к допуску данных о толковании, а не к изменению прежних юридических выводов.

## 0.20.0 - 2026-07-24

- Добавляет отдельный проверенный контракт данных об исковой давности и формальную модель статей 195–208 ГК РФ (`src/causa/institutional/contracts/limitation.py`).
- Разделяет начало течения (200), общий и специальный срок (196/197), предельный десятилетний срок, приостановление (202), перерыв признанием долга (203), период судебной защиты (204), заявление стороны (199), восстановление срока (205), дополнительные требования (207) и исключения (208).
- Интегрирует институт в reviewed analysis с проверками схемы, источников, `case_id` и воспроизводимости; добавляет шаг `evaluate-limitation-period` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-limitation-spec.md`](contract-limitation-spec.md) и синтетический артефакт `examples/synthetic_limitation_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.19.0 → 0.20.0` относится к допуску данных об исковой давности, а не к изменению прежних юридических выводов.

## 0.19.0 - 2026-07-24

- Добавляет отдельный проверенный контракт данных о действии договора во времени и формальную модель статей 425 и 433 ГК РФ (`src/causa/institutional/contracts/temporal_effect.py`).
- Разделяет момент заключения (консенсуальный, реальный и подлежащий регистрации договор), вступление в силу, отлагательное вступление, обратное действие, истечение срока и сохранение ответственности за нарушение.
- Требует согласованности момента заключения с формальными предпосылками заключения договора (статьи 432–443) и добавляет проверки схемы, источников и `case_id`.
- Интегрирует институт в reviewed analysis, добавляет шаг `evaluate-contract-temporal-effect` в Phase 0 и benchmark (`10/10`) и red-team (`10/10`).
- Добавляет русскую спецификацию [`docs/contract-temporal-effect-spec.md`](contract-temporal-effect-spec.md) и синтетический артефакт `examples/synthetic_temporal_effect_evaluation_report.json`.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; миграция `0.18.0 → 0.19.0` относится к допуску данных о действии договора во времени, а не к изменению прежних юридических выводов.

## 0.18.0 - 2026-07-23

- Добавляет контур допуска пилотных данных `pilot-admission-gate-v1` (`src/causa/pilot.py`) с псевдонимным intake, fail-closed gate и связанным воспроизводимым run-манифестом.
- Требует проверенное законное основание для персональных данных и трактует согласие субъекта как одно из оснований: `consent_ref` обязателен только для основания `subject_consent`.
- Требует минимизацию данных, tenant isolation, предельный срок хранения 90 дней, подтверждённое хранение в российском контуре, поручение обработчику и четыре независимых согласования: privacy, законное основание, информационная безопасность и владелец предметной области.
- В gate v1 блокирует внешнюю модель, трансграничную передачу, специальные категории и биометрию, данные несовершеннолетних, учётные данные и государственную тайну; коммерческая тайна требует разрешения владельца.
- Переводит наблюдения полезности пилота на `privacy-safe-pilot-utility.v1`, требуя связанное решение gate и decision trace и запрещая исходный текст и прямые идентификаторы.
- Интегрирует синтетическую пилотную репетицию в readiness Этапа 0 отдельным пунктом `ws10-pilot-admission` и добавляет benchmark (`6/6`) и red-team (`32/32`) пилотного gate.
- Сохраняет evidence `contracts.case-evidence.v9`, analysis `contracts-reviewed-analysis-v9` и русские шаблоны `ru-v11`; `ready_for_production` остаётся `false` до настоящего пилота.
- Добавляет русскую спецификацию [`docs/pilot-data-admission-spec.md`](pilot-data-admission-spec.md) с опорой на Федеральный закон № 152-ФЗ и Приказ Роскомнадзора от 19.06.2025 № 140.

## 0.17.0 - 2026-07-13

- Adds mandatory reviewed general-sale evidence with 152 provenance-backed predicates for articles 454–491 of the Russian Civil Code.
- Separates qualification, future goods and property rights, transfer, documents, risk, third-party rights, eviction, quantity, assortment, quality, warranty, shelf life, completeness, packaging, notice, acceptance, price, payment, credit, installment, insurance, and retained title.
- Enforces agreement between general sale, special supply, formation, temporal, performance, termination, payment, loss, and causation facts.
- Preserves the warranty burden and post-repair remedy boundaries reflected in the 2024 Supreme Court reviews.
- Adds 48 benchmarks, 51 adversarial checks, official-source metadata, and Russian professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v9`, analysis to `contracts-reviewed-analysis-v9`, and Russian templates to `ru-v11`.

## 0.16.0 - 2026-07-13

- Adds mandatory reviewed special-supply evidence with 82 provenance-backed predicates for articles 506–524 of the Russian Civil Code.
- Separates qualification, disagreement handling, periods, shipment orders, transport, short delivery, acceptance, responsible custody, selection, payment, containers, defects, completeness, cover purchase, penalty, allocation, unilateral refusal, and price damages.
- Enforces cross-model agreement for formation, delivery, delay, nonconformity, payment, breach, termination, loss, and causation.
- Preserves the contractual-only status of Instructions P-6 and P-7 in accordance with Plenum of the Supreme Arbitration Court Resolution No. 18.
- Adds 32 benchmarks, 32 adversarial checks, source metadata, and Russian professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v8`, analysis to `contracts-reviewed-analysis-v8`, and Russian templates to `ru-v10`.

## 0.15.0 - 2026-07-12

- Adds mandatory reviewed performance-remedies evidence with 96 provenance-backed predicates.
- Covers proper, partial, early, third-party, demand, alternative, facultative, solidary, and reciprocal performance under articles 309–328.
- Separates damages, replacement transactions, specific performance, article 395 interest, subsidiary and limited liability, debtor and creditor delay, and article 406.1 indemnity.
- Enforces cross-model agreement for obligation, breach, tender, loss, causation, and monetary-delay facts.
- Adds 27 benchmarks, 30 adversarial checks, official-source metadata, and Russian professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v7`, analysis to `contracts-reviewed-analysis-v7`, and Russian templates to `ru-v9`.

## 0.14.0 - 2026-07-12

- Adds mandatory reviewed obligation-dynamics evidence with 83 provenance-backed predicates.
- Covers assignment, debt transfer, contract transfer, performance, notary deposit, accord and satisfaction, set-off, novation, forgiveness, merger, impossibility, government act, death, and liquidation under articles 382–419.
- Keeps a party change distinct from discharge and separates full discharge, partial discharge, remaining debt, and accrued claims.
- Preserves debtor defenses, original-creditor performance before notice, cedent warranty issues, and third-party security effects.
- Adds 21 benchmarks, 22 adversarial checks, official-source metadata, and Russian professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v6`, analysis to `contracts-reviewed-analysis-v6`, and Russian templates to `ru-v8`.

## 0.13.0 - 2026-07-12

- Adds mandatory reviewed performance-security evidence with 60 provenance-backed predicates.
- Covers general accessory rules, penalty, pledge, retention, suretyship, independent guarantee, deposit, and security payment under Civil Code articles 329–381.2.
- Separates creation, third-party opposability, enforcement prerequisites, judicial and extrajudicial pledge routes, termination, regress, credit, and return issues.
- Preserves the independent nature of guarantees and the main obligation when a security instrument itself is defective.
- Adds 16 benchmarks, 16 adversarial checks, official-source metadata, and Russian professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v5`, analysis to `contracts-reviewed-analysis-v5`, and Russian templates to `ru-v7`.

## 0.12.0 - 2026-07-12

- Adds mandatory reviewed transaction-invalidity evidence with 51 provenance-backed predicates.
- Separates void and voidable grounds, standing, judgment, limitation, estoppel, and legal effects under Civil Code articles 166–181.
- Covers qualified illegality, immoral purpose, sham and feigned transactions, consent, authority, capacity, mistake, deception, threat, and adverse circumstances.
- Models partial invalidity, disguised-transaction rules, restitution, public-recovery issues, and additional damages without deciding a court outcome.
- Adds 14 benchmarks, 14 adversarial checks, Russian vocabulary, and professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v4`, analysis to `contracts-reviewed-analysis-v4`, and Russian templates to `ru-v6`.

## 0.11.0 - 2026-07-12

- Adds mandatory reviewed change-and-termination evidence with 36 provenance-backed predicates.
- Separates mutual agreement, judicial relief, unilateral action, and changed-circumstances paths under Civil Code articles 310 and 450–453.
- Keeps judicial prerequisites distinct from an effective judgment and validates delivery, pretrial procedure, form, good faith, and prior waiver.
- Models future-obligation termination, accrued-claim preservation, restitution issues, and termination-loss issues without deciding a court outcome.
- Adds 12 benchmarks, 12 adversarial checks, Russian vocabulary, and professional/forensic explanation sections.
- Upgrades evidence to `contracts.case-evidence.v3`, analysis to `contracts-reviewed-analysis-v3`, and Russian templates to `ru-v5`.

## 0.10.0 - 2026-07-12

- Adds mandatory reviewed contract-formation evidence with 17 provenance-backed predicates.
- Adds narrow formal boundaries for Civil Code articles 432, 435, 438, and 443 and Supreme Court Plenum Resolution No. 49.
- Separates essential terms, offer, express acceptance, acceptance by conduct, silence, counteroffer, required form, and bad-faith non-conclusion objections.
- Enforces agreement between formation results and contractual-duty evidence before breach and liability analysis.
- Adds ten formation benchmarks, ten adversarial checks, Russian vocabulary, and a Russian formation explanation section.
- Upgrades evidence to `contracts.case-evidence.v2`, analysis to `contracts-reviewed-analysis-v2`, and Russian templates to `ru-v4`.

## 0.9.0 - 2026-07-11

- Adds mandatory reviewed liability evidence with 20 provenance-backed predicates.
- Adds narrow formal prerequisite models for Civil Code articles 401 and 333.
- Separates fault rebuttal, force majeure, excluded commercial risks, notice, and intentional breach clauses.
- Separates procedural and substantive prerequisites for judicial penalty reduction without calculating an amount.
- Adds ten liability benchmarks and ten adversarial overreach checks.
- Upgrades evidence to `contracts.case-evidence.v1`, analysis to `contracts-reviewed-analysis-v1`, and Russian templates to `ru-v3`.

## 0.8.0 - 2026-07-11

- Adds a hash-addressed library of seven typed contractual legal operators.
- Adds deterministic one-step sensitivity analysis with immutable baseline facts.
- Enforces policy-controlled scenario and fact-change budgets, preconditions, and mandatory human review.
- Adds seven counterfactual benchmarks and seven adversarial bypass checks.
- Adds operator-library coordinates to decision traces and Russian professional/forensic explanations.
- Adds replay migration from `0.7.0` and updates the Translation Layer templates to `ru-v2`.

## 0.7.0 - 2026-07-11

- Adds versioned Russian templates for executive, professional, and forensic legal explanations.
- Adds shared structured legal assertions with exact source references across all three levels.
- Adds deterministic faithfulness checks by exact re-rendering from the reviewed trace.
- Adds structural usability checks while explicitly retaining the requirement for a lawyer pilot.
- Binds the translation template version and SHA-256 hash to the active policy and decision trace.
- Adds reasoning-path comparison, a standalone translation bundle, and replay migration from `0.6.0`.

## 0.6.0 - 2026-07-11

- Adds immutable Management Plane policy snapshots with canonical SHA-256 content hashes.
- Adds typed Russian semantic diffs for policy tightening, relaxation, and behavioral changes.
- Adds append-only registration, activation, and rollback events with optimistic revision checks.
- Adds an atomic JSON persistence backend with stale-write protection for local replay.
- Binds Phase 0 decision traces and governance records to the active snapshot ID and content hash.
- Adds replay-required migration fixtures from `0.1.0`, `0.3.0`, `0.4.0`, and `0.5.0`.

## 0.5.0 - 2026-07-11

- Adds mandatory Russian human-readable labels for governance, risk, failure, and policy values.
- Adds parallel Russian reasons for temporal, source-applicability, authority, and formal evaluations.
- Adds an executable governance engine with stored decisions, sandbox, activation, revalidation, and rollback records.
- Converts the key synthetic legal sources, claims, candidate, explanation, readiness report, and warnings to Russian.
- Keeps stable machine IDs and English compatibility fields unchanged.
- Adds replay-required migration fixtures from `0.1.0`, `0.3.0`, and `0.4.0`.

## 0.4.0 - 2026-07-11

- Adds reviewed case-evidence, temporal-evidence, and authority-input contracts.
- Adds a fail-closed end-to-end analysis pipeline with source, case, date, schema, and review validation.
- Maps every narrow formal fact from an explicit reviewed assertion and retains source provenance.
- Links duty and exception facts to reviewed formal atoms.
- Adds a standalone synthetic reviewed-analysis artifact and migrates the Phase 0 trace to it.
- Adds replay-required migration fixtures from both `0.1.0` and `0.3.0`.

## 0.3.0 - 2026-07-11

- Adds synthetic formal predicates for basic damages remedy availability, causation-evidence gaps, and stated limitation bars.
- Adds benchmark and adversarial checks that reject remedies without causation or despite a stated limitation bar.
- Does not calculate loss, establish causation, or compute limitation dates.

## 0.2.0 - 2026-07-11

- Adds a synthetic-reviewed authority policy with constitutional and regulatory levels.
- Adds benchmark and adversarial checks for constitutional/statutory/regulatory ordering.
- Adds migration and rollback guidance for the preceding package release.

## 0.1.0 - 2026-07-11

- Initial Phase 0 contractual package release.
- Adds synthetic supply sources, temporal applicability, and source-revision cases.
- Adds statutory, judicial, contractual, and factual authority resolution with scoped `lex specialis`.
- Adds narrow formal checks for late performance, confirmed defect, and payment default.
- Adds benchmark, practice-utility baseline, and hybrid adversarial red-team artifacts.

## Versioning policy

- Package releases use semantic versioning.
- A package release must update the compatibility matrix, migration guide, and rollback notes.
- Changes to authority, formal rules, or evaluation semantics require benchmark and red-team evidence.
