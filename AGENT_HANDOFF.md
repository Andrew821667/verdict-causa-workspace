# Инструкция агенту для продолжения Verdict Causa

## 1. Рабочая область

- Репозиторий: `/Users/andrew/Мои AI проекты/verdict-causa-workspace`
- Стабильная ветка: `main`
- WIP-ветка для продолжения: `agent/pilot-0.18-handoff`
- Последний опубликованный коммит: `97b7343 Add reviewed sale contract model`
- Концепция: `/Users/andrew/Downloads/verdict-concept-v2-5.md`
- Текущее состояние проекта: `Current.md`

Подключи репозиторий `Andrew821667/verdict-causa-workspace` и checkout ветки
`agent/pilot-0.18-handoff`. Затем начни с чтения `Current.md`, этого файла,
концепции и `git status`. В ветке находится незавершенная реализация следующего
релиза. Не удаляй, не откатывай и не переписывай эти изменения.

## 2. Правила работы с пользователем

- Пользователь просит работать крупными законченными блоками.
- Юридически значимые материалы и объяснения должны быть на русском языке.
- Система в первую очередь создается для российской правовой системы.
- Не останавливайся на плане: доводи согласованный блок до кода, тестов,
  артефактов, документации, коммита, push и успешного GitHub Actions.
- Не выдавай формальный результат за судебный вывод или юридическую консультацию.
- Используй существующие архитектурные паттерны репозитория и `.venv/bin/...`.
- Для ручных правок используй `apply_patch`.
- Не трогай несвязанные изменения и старые 25 файлов, которые глобальный
  `ruff format --check` считает неформатированными.

## 3. Завершенное стабильное состояние

Релиз `contracts-ru-v0@0.17.0` опубликован в `main`.

- Общая модель купли-продажи по статьям 454-491 ГК РФ: 152 факта,
  67 результатов, 48/48 benchmark и 51/51 red-team.
- Интеграция в `contracts.case-evidence.v9`,
  `contracts-reviewed-analysis-v9`, Translation Layer `ru-v11` и Phase 0.
- Последний полный локальный прогон до начала текущего черновика:
  `297 passed`.
- GitHub Actions для коммита `97b7343` завершился успешно.

## 4. Почему выбран текущий блок

Не переходи пока ко второму институту права. Раздел 14.1 концепции требует до
этого доказать Этап 0 на реальном или максимально приближенном к реальному
пилотном кейсе.

Текущий блок: **безопасный, минимизированный и воспроизводимый пилотный контур
для спора о поставке**.

Цель релиза `contracts-ru-v0@0.18.0`:

1. Не допускать несинтетические наблюдения без отдельного admission gate.
2. Не хранить в артефактах тексты документов, имена файлов и идентификаторы.
3. Связать каждое наблюдение полезности с gate decision и decision trace.
4. Отделить согласие субъекта от других законных оснований обработки.
5. Проверять минимизацию, срок хранения, tenant isolation и четыре sign-off.
6. Сохранить статус `ready_for_production=false` до настоящего пилота.

## 5. Уже реализовано в незакоммиченном черновике

Новые файлы:

- `src/causa/pilot.py`
  - схемы `pilot.intake.v1`, `pilot-admission-gate-v1`,
    `pilot.rehearsal.v1`;
  - псевдонимный document manifest;
  - lawful basis, privacy/legal/security/domain sign-off;
  - детерминированный fingerprint;
  - fail-closed gate и связанный run manifest.
- `src/causa/institutional/contracts/pilot_fixtures.py`
  - максимально реалистичная синтетическая поставка;
  - одобренные обезличенные маршруты разных законных оснований.
- `src/causa/institutional/contracts/pilot_evaluation.py`
  - 6 допустимых benchmark-маршрутов;
  - 32 red-team сценария.
- `src/causa/institutional/contracts/synthetic_pilot.py`
  - сборка связанного rehearsal artifact.
- `scripts/export_synthetic_pilot_rehearsal.py`
- `tests/test_pilot_admission.py`
- `examples/migrations/contracts-ru-v0-0.17.0-phase0-trace.json`

Изменено:

- `src/causa/evaluation.py`
  - utility observation v1 требует lawful basis, минимизацию, gate и trace;
  - отчет проверяет собственные агрегаты.
- `src/causa/institutional/contracts/pilot_utility.py`
  - схема обновлена до `privacy-safe-pilot-utility.v1`;
  - согласие требуется только при соответствующем основании.
- пакет, compatibility и migration начали переводиться на `0.18.0`.
- тесты package version/migration и privacy-safe utility частично обновлены.

Последняя точечная проверка:

```text
PilotAdmissionStatus.APPROVED
benchmark: 6/6
red-team: 32/32
policy-snapshot:phase0-standard-t3@1
```

Полный Pytest после этих изменений еще не запускался.

## 6. Обязательные инварианты pilot gate

- Только псевдонимные `case_ref`, `tenant_ref`, `reviewer_ref` и SHA-256.
- Любое дополнительное поле с raw/free text отклоняется Pydantic.
- Для персональных данных обязательно проверенное законное основание.
- `consent_ref` обязателен только для `SUBJECT_CONSENT`.
- В gate v1 запрещены:
  - внешняя модель;
  - трансграничная передача;
  - специальные категории и биометрия;
  - данные несовершеннолетних;
  - учетные данные;
  - государственная тайна.
- Для персональных данных обязательны удаление прямых идентификаторов,
  обобщение косвенных идентификаторов и удаление избыточных сведений.
- Коммерческая тайна требует разрешения владельца.
- Хранение только в подтвержденном российском контуре, не более 90 дней.
- Обязательны шифрование, RBAC, audit log и план удаления.
- Privacy, legal basis, information security и Domain Owner должны быть
  одобрены разными проверяющими.
- Одобренный запуск всегда требует human review и не хранит raw content.

Правовая опора текущего дизайна:

- Федеральный закон от 27.07.2006 N 152-ФЗ, в частности статьи 5, 6, 7,
  9-12 и 19.
- Приказ Роскомнадзора от 19.06.2025 N 140 о требованиях и методах
  обезличивания.

Не заявляй, что gate автоматически гарантирует соответствие закону. Он
фиксирует технические предпосылки и требует отдельного юридического review.

## 7. Что нужно завершить

### Интеграция

1. Импортировать `build_synthetic_pilot_rehearsal_artifact` в
   `src/causa/phase0/pipeline.py`.
2. Добавить в readiness отдельный пункт пилотного допуска и ссылки на:
   - `examples/synthetic_pilot_rehearsal_report.json`;
   - benchmark `contracts-pilot-gate-benchmark-v1`;
   - red-team `contracts-pilot-gate-red-team-v1`;
   - utility report v1.
3. Обновить migration paths в Phase 0 с target `0.18.0`, включая источник
   `0.17.0`.
4. Не менять `ready_for_production=false`.

### Артефакты и релиз

1. Запустить новый exporter и обновленный utility exporter.
2. Сгенерировать migration reports от `0.1.0`, `0.3.0`, всех версий
   `0.4.0-0.17.0` к `0.18.0`.
3. Пересобрать все артефакты, в которые входит package manifest или readiness.
4. Старые migration reports не удалять: это исторические артефакты.

### Русская документация

Создать `docs/pilot-data-admission-spec.md` и описать:

- границу между синтетической репетицией и реальным пилотом;
- data minimization;
- lawful basis и условное требование согласия;
- запрещенные категории gate v1;
- tenant isolation, retention, processor instruction;
- четыре роли согласования;
- replay и utility observation;
- ограничения: gate не заменяет юриста, ИБ и privacy review.

Обновить:

- `README.md`;
- `docs/evaluation-and-red-team-spec.md`;
- `docs/phase-0-execution-plan.md`;
- `docs/contracts-ru-v0-changelog.md`;
- `docs/contracts-ru-v0-compatibility.md`;
- при необходимости `docs/first-institution-contracts.md`.

### Версионирование

- Итоговая версия: `contracts-ru-v0@0.18.0`.
- Evidence остается `contracts.case-evidence.v9`.
- Analysis остается `contracts-reviewed-analysis-v9`.
- Translation templates остаются `translation-template-ru-v11`.
- Migration `0.17.0 -> 0.18.0` относится к pilot admission/utility, а не к
  изменению юридических выводов.

### Тесты и QA

Сначала исправь ожидаемые временные падения из-за отсутствующего JSON и
незавершенной Phase 0 интеграции. Затем выполни:

```bash
.venv/bin/ruff format <только измененные Python-файлы>
.venv/bin/ruff check src tests scripts
.venv/bin/ruff format --check <только измененные Python-файлы>
.venv/bin/pytest
git diff --check
```

Отдельно проверь:

- benchmark `6/6`;
- red-team `32/32`;
- точное воспроизведение JSON pilot artifact;
- точное воспроизведение всех migration reports;
- отсутствие raw text и прямых идентификаторов в pilot JSON;
- чистую рабочую копию после коммита;
- GitHub Actions для опубликованного SHA.

## 8. Известное промежуточное состояние

- `tests/test_pilot_admission.py` уже ожидает пакет `0.18.0`.
- `examples/synthetic_pilot_rehearsal_report.json` еще не создан.
- `src/causa/phase0/pipeline.py` еще не интегрирован с pilot artifact.
- Документация и readiness еще описывают прежний pilot schema demo.
- Migration exporter переключен на `0.18.0`, но отчеты еще не сгенерированы.
- `Current.md` новый и пока не закоммичен.
- Не коммить частичный результат до полного зеленого QA.

## 9. Завершение передачи

После успешного QA:

1. Обнови `Current.md`: версия `0.18.0`, выполненные пункты и историю.
2. Проверь `git status` и staged diff.
3. Сделай один содержательный коммит.
4. Push в `origin/main`.
5. Дождись GitHub Actions.
6. Отчитайся пользователю на русском: что реализовано, точные счетчики,
   тесты, SHA и оставшееся условие настоящего пилота.
