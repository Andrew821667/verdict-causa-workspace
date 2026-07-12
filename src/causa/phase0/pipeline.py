from enum import Enum

from pydantic import BaseModel, Field

from causa.institutional.contracts.benchmark_runner import run_synthetic_supply_benchmark_suite
from causa.institutional.contracts.practice_utility import (
    build_synthetic_supply_practice_utility_report,
)
from causa.institutional.contracts.pilot_utility import (
    build_privacy_safe_pilot_utility_report,
)
from causa.institutional.contracts.red_team_runner import run_synthetic_supply_red_team_suite
from causa.institutional.contracts.synthetic_counterfactual import (
    build_synthetic_counterfactual_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_liability import (
    build_synthetic_liability_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_formation import (
    build_synthetic_formation_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_termination import (
    build_synthetic_termination_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_invalidity import (
    build_synthetic_invalidity_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_security import (
    build_synthetic_security_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_obligation_dynamics import (
    build_synthetic_obligation_dynamics_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_performance_remedies import (
    build_synthetic_performance_remedies_evaluation_artifact,
)
from causa.institutional.contracts.versioning import (
    evaluate_contracts_package_compatibility,
)
from causa.phase0.demo_trace import Phase0DemoTrace, build_supply_dispute_demo_trace


class PipelineStepStatus(str, Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class PipelineStepResult(BaseModel):
    id: str
    title: str
    status: PipelineStepStatus
    artifact_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class Phase0PipelineResult(BaseModel):
    id: str
    locale: str = "ru-RU"
    scenario: str
    trace: Phase0DemoTrace
    steps: list[PipelineStepResult]

    @property
    def passed(self) -> bool:
        return all(step.status != PipelineStepStatus.FAILED for step in self.steps)


class ReadinessItem(BaseModel):
    id: str
    title: str
    status: PipelineStepStatus
    evidence_refs: list[str] = Field(default_factory=list)
    remaining_work: list[str] = Field(default_factory=list)


class Phase0ReadinessReport(BaseModel):
    id: str
    locale: str = "ru-RU"
    project_stage: str
    project_stage_label_ru: str
    ready_for_production: bool
    summary: str
    items: list[ReadinessItem]

    @property
    def warning_count(self) -> int:
        return sum(item.status == PipelineStepStatus.WARNING for item in self.items)

    @property
    def failed_count(self) -> int:
        return sum(item.status == PipelineStepStatus.FAILED for item in self.items)


def run_supply_dispute_pipeline() -> Phase0PipelineResult:
    trace = build_supply_dispute_demo_trace()

    steps = [
        PipelineStepResult(
            id="select-source",
            title="Выбор синтетического правового источника",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.legal_source.id],
            notes=["Источник явно помечен как синтетический и неофициальный."],
        ),
        PipelineStepResult(
            id="review-bootstrap-json",
            title="Проверка структурированного представления нормы",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.reviewed_norm.id],
            notes=[f"Статус проверки: {trace.reviewed_norm.review_status.value}."],
        ),
        PipelineStepResult(
            id="translate-structured-formal-output",
            title="Детерминированный перевод проверенной нормы в формальное правило",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.formal_translation.obligation_rule.id],
            notes=[
                "Перевод детерминирован и воспроизводим.",
                "Формальный результат ограничен узким набором правил об обязательствах.",
            ],
        ),
        PipelineStepResult(
            id="validate-reviewed-analysis-inputs",
            title="Проверка фактов дела, временных данных и источников-кандидатов",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_request.case_evidence.id,
                trace.analysis_request.temporal_evidence.id,
                trace.analysis_request.authority_input.id,
            ],
            notes=[
                f"Проверяющие: {', '.join(trace.analysis_result.reviewer_ids)}.",
                "Неизвестные источники и неполный набор доказательственных утверждений отклоняются.",
            ],
        ),
        PipelineStepResult(
            id="map-reviewed-evidence",
            title="Преобразование проверенных доказательств в типизированные формальные факты",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.evidence_mapping.mapping_version,
                trace.analysis_result.evidence_mapping.formal_rule_id,
            ],
            notes=[
                "Каждый формальный факт связан с утверждением и его источниками.",
                "Факты об обязанности и исключении связаны с атомами проверенной нормы.",
            ],
        ),
        PipelineStepResult(
            id="resolve-reviewed-authority",
            title="Разрешение конкуренции проверенных источников",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.authority_evaluation.selected_source_id
                or "human-resolution-required"
            ],
            notes=trace.analysis_result.authority_evaluation.reasons_ru,
        ),
        PipelineStepResult(
            id="evaluate-contract-formation",
            title="Проверка формальных предпосылок заключения договора",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.formation_evidence_mapping.evidence_id,
                trace.analysis_result.formation_constraint_set.id,
                *trace.analysis_result.formation_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.formation_evaluation.reasons_ru,
                "Проверяются оферта, существенные условия, форма и допустимый способ акцепта.",
                "Судебная квалификация доказательств не автоматизируется.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-transaction-invalidity",
            title="Проверка действительности сделки",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.invalidity_evidence_mapping.evidence_id,
                trace.analysis_result.invalidity_constraint_set.id,
                *trace.analysis_result.invalidity_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.invalidity_evaluation.reasons_ru,
                "Ничтожность и оспоримость проверяются раздельно до обычных договорных последствий.",
                "Система не признает сделку недействительной без требуемого судебного эффекта.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-obligation-constraints",
            title="Формальная проверка узкого набора правил об обязательстве",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.constraint_set.id],
            notes=[
                *trace.temporal_evaluation.reasons_ru,
                *trace.constraint_evaluation.reasons_ru,
                "Используется формальный решатель, но только для узкого подмножества Этапа 0.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-performance-remedies",
            title="Проверка исполнения обязательств и средств защиты",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.performance_remedies_evidence_mapping.evidence_id,
                trace.analysis_result.performance_remedies_constraint_set.id,
                *trace.analysis_result.performance_remedies_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.performance_remedies_evaluation.reasons_ru,
                "Частичное, досрочное, третьелицевое и встречное исполнение проверяются раздельно.",
                "Убытки, проценты, исполнение в натуре, просрочка и возмещение потерь не смешиваются.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-obligation-dynamics",
            title="Проверка перемены лиц и прекращения обязательств",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.obligation_dynamics_evidence_mapping.evidence_id,
                trace.analysis_result.obligation_dynamics_constraint_set.id,
                *trace.analysis_result.obligation_dynamics_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.obligation_dynamics_evaluation.reasons_ru,
                "Перемена лиц не смешивается с прекращением самого обязательства.",
                "Исполнение, отступное, зачет, новация и объективные основания проверяются отдельными путями.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-performance-security",
            title="Проверка способов обеспечения исполнения обязательств",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.security_evidence_mapping.evidence_id,
                trace.analysis_result.security_constraint_set.id,
                *trace.analysis_result.security_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.security_evaluation.reasons_ru,
                "Неустойка, залог, удержание, поручительство, независимая гарантия, задаток и обеспечительный платеж проверяются раздельно.",
                "Реализация обеспечения и оценочные стандарты не подменяют решение юриста или суда.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-contract-change-and-termination",
            title="Проверка изменения и расторжения договора",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.termination_evidence_mapping.evidence_id,
                trace.analysis_result.termination_constraint_set.id,
                *trace.analysis_result.termination_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.termination_evaluation.reasons_ru,
                "Соглашение, судебный путь и односторонний отказ проверяются раздельно.",
                "Судебные предпосылки не выдаются за вступившее в силу расторжение.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-counterfactual-sensitivity",
            title="Проверка контрфактической чувствительности договорного вывода",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.counterfactual_sensitivity.id,
                trace.analysis_result.counterfactual_sensitivity.operator_library_id,
                trace.analysis_result.counterfactual_sensitivity.operator_library_hash,
                *trace.analysis_result.counterfactual_sensitivity.critical_scenario_ids,
            ],
            notes=[
                "Применяются только типизированные legal operators договорного пакета.",
                "Исходные проверенные факты не изменяются; все ветви явно гипотетические.",
                "Число сценариев и изменений фактов ограничено воспроизводимым бюджетом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-liability-prerequisites",
            title="Проверка предпосылок ответственности и снижения неустойки",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.liability_evidence_mapping.evidence_id,
                trace.analysis_result.liability_constraint_set.id,
                *trace.analysis_result.liability_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.liability_evaluation.reasons_ru,
                "Проверяются только формальные предпосылки статей 333 и 401 ГК РФ.",
                "Размер снижения неустойки и оценка доказательств не автоматизируются.",
            ],
        ),
        PipelineStepResult(
            id="build-case-graph",
            title="Построение четырехслойной трассировки решения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.decision_trace.id],
            notes=[
                "Трассировка включает источник, формальную норму, дело и доктринальный слой.",
            ],
        ),
        PipelineStepResult(
            id="ground-claim",
            title="Формирование правового утверждения с привязкой к источнику",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.claim.id, *trace.claim.sources],
            notes=["Правовое утверждение содержит ссылку на синтетический источник."],
        ),
        PipelineStepResult(
            id="classify-candidate",
            title="Классификация кандидата и выбор governance-профиля",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.candidate.id, trace.candidate_type.value],
            notes=[
                "Кандидат классифицирован как эвристика пробела.",
                "Профиль требует классификации типа и экспертной проверки.",
            ],
        ),
        PipelineStepResult(
            id="execute-governance-lifecycle",
            title="Исполнение governance-жизненного цикла кандидата",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.governance_record.id,
                *[decision.id for decision in trace.governance_record.decisions],
            ],
            notes=[
                f"Текущая стадия: {trace.governance_record.current_stage_label_ru}.",
                f"Активная версия: {trace.governance_record.active_candidate_version}.",
                "Каждый переход содержит русские причины, доказательства и версию политики.",
            ],
        ),
        PipelineStepResult(
            id="record-policy",
            title="Фиксация активного снимка политики Management Plane",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.policy_snapshot.id,
                trace.policy_snapshot.content_hash,
                *[event.id for event in trace.policy_registry.events],
            ],
            notes=[
                "Применена активная политика: стандартный режим × уровень риска T3.",
                f"Ревизия реестра политик: {trace.policy_registry.revision}.",
                "ID и content hash снимка сохранены в координатах трассировки.",
                "Политика разрешает bounded counterfactual и фиксирует оба его бюджета.",
            ],
        ),
        PipelineStepResult(
            id="attach-red-team",
            title="Подключение сценария Red Team",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.red_team_scenario.id],
            notes=["Сценарий проверяет риск чрезмерно широкого принципа-кандидата."],
        ),
        PipelineStepResult(
            id="produce-translation",
            title="Формирование трехуровневого русского юридического объяснения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.translation_bundle.id,
                *[artifact.id for artifact in trace.translation_bundle.artifacts],
                trace.translation_bundle.faithfulness_report.id,
                trace.translation_bundle.usability_report.id,
            ],
            notes=[
                "Сформированы краткий, профессиональный и forensic-уровни на русском языке.",
                "Детерминированная проверка верности трассировке пройдена.",
                "Структурные usability-проверки пройдены; понимание требует пилота с юристами.",
            ],
        ),
        PipelineStepResult(
            id="export-decision-trace",
            title="Экспорт трассировки с координатами версий",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[trace.decision_trace.id],
            notes=[
                f"Версия знаний: {trace.decision_trace.versions.knowledge_version}.",
                f"Версия политики: {trace.decision_trace.versions.policy_version}.",
            ],
        ),
    ]

    return Phase0PipelineResult(
        id="phase0-supply-dispute-pipeline-v0",
        scenario="Синтетический спор о просрочке поставки",
        trace=trace,
        steps=steps,
    )


def build_phase0_readiness_report() -> Phase0ReadinessReport:
    pipeline = run_supply_dispute_pipeline()
    benchmark_report = run_synthetic_supply_benchmark_suite()
    practice_utility_report = build_synthetic_supply_practice_utility_report()
    privacy_safe_pilot_report = build_privacy_safe_pilot_utility_report()
    red_team_report = run_synthetic_supply_red_team_suite()
    compatibility_check = evaluate_contracts_package_compatibility()
    counterfactual_artifact = build_synthetic_counterfactual_evaluation_artifact()
    liability_artifact = build_synthetic_liability_evaluation_artifact()
    formation_artifact = build_synthetic_formation_evaluation_artifact()
    termination_artifact = build_synthetic_termination_evaluation_artifact()
    invalidity_artifact = build_synthetic_invalidity_evaluation_artifact()
    security_artifact = build_synthetic_security_evaluation_artifact()
    dynamics_artifact = build_synthetic_obligation_dynamics_evaluation_artifact()
    performance_remedies_artifact = build_synthetic_performance_remedies_evaluation_artifact()

    items = [
        ReadinessItem(
            id="ws1-universal-core",
            title="Универсальная модель данных ядра",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[
                "src/causa/core/models.py",
                "src/causa/core/knowledge_graph.py",
                pipeline.trace.decision_trace.id,
            ],
            remaining_work=["Расширить метаданные происхождения и аудита."],
        ),
        ReadinessItem(
            id="ws2-knowledge-plane",
            title="Базовый контур Knowledge Plane",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[pipeline.trace.decision_trace.id],
            remaining_work=["Добавить хранение графа и механизмы извлечения."],
        ),
        ReadinessItem(
            id="ws3-bootstrap",
            title="Нейросимвольный bootstrap-конвейер",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[
                "src/causa/core/bootstrap.py",
                "src/causa/institutional/contracts/reviewed_analysis.py",
                "examples/synthetic_reviewed_contract_analysis.json",
                pipeline.trace.reviewed_norm.id,
                pipeline.trace.analysis_result.evidence_mapping.mapping_version,
            ],
            remaining_work=[
                "Расширить проверенные отображения за пределы текущего узкого набора договорных фактов.",
            ],
        ),
        ReadinessItem(
            id="ws4-contracts-package",
            title="Институциональный пакет договорного права",
            status=PipelineStepStatus.WARNING,
            evidence_refs=[
                "src/causa/institutional/contracts/package.py",
                "docs/first-institution-contracts.md",
                "docs/contracts-ru-v0-changelog.md",
                "docs/contracts-ru-v0-compatibility.md",
                "src/causa/institutional/contracts/versioning.py",
                "src/causa/institutional/contracts/migrations.py",
                "src/causa/institutional/contracts/legal_operators.py",
                "src/causa/institutional/contracts/formation.py",
                "docs/contract-formation-spec.md",
                "src/causa/institutional/contracts/invalidity.py",
                "docs/contract-invalidity-spec.md",
                "src/causa/institutional/contracts/security.py",
                "docs/contract-security-spec.md",
                "src/causa/institutional/contracts/obligation_dynamics.py",
                "docs/contract-obligation-dynamics-spec.md",
                "src/causa/institutional/contracts/performance_remedies.py",
                "docs/contract-performance-remedies-spec.md",
                "src/causa/institutional/contracts/termination.py",
                "docs/contract-change-termination-spec.md",
                "src/causa/institutional/contracts/liability.py",
                "docs/contract-liability-spec.md",
                "examples/synthetic_counterfactual_evaluation_report.json",
                "examples/synthetic_liability_evaluation_report.json",
                "examples/synthetic_formation_evaluation_report.json",
                "examples/synthetic_invalidity_evaluation_report.json",
                "examples/synthetic_security_evaluation_report.json",
                "examples/synthetic_obligation_dynamics_evaluation_report.json",
                "examples/synthetic_performance_remedies_evaluation_report.json",
                "examples/synthetic_termination_evaluation_report.json",
                "examples/migrations/contracts-ru-v0-0.1.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.3.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.4.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.5.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.6.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.7.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.8.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.9.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.10.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.11.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.12.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.13.0-to-0.15.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.14.0-to-0.15.0-migration-report.json",
                f"{compatibility_check.package_id}@{compatibility_check.package_version}",
            ],
            remaining_work=[
                "Расширить правила юридической силы и временные правила за пределы поставки.",
                "Расширить legal operators на изменение и расторжение договора.",
                "Добавлять replay-миграцию для каждого семантического релиза пакета.",
            ],
        ),
        ReadinessItem(
            id="ws5-management-plane",
            title="Контур управления Management Plane",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[
                "src/causa/management/policy_matrix.py",
                "src/causa/management/policy_registry.py",
                "examples/synthetic_management_policy_registry_report.json",
                pipeline.trace.decision_trace.versions.policy_version,
                pipeline.trace.policy_snapshot.content_hash,
            ],
            remaining_work=[
                "Заменить локальное атомарное JSON-хранилище транзакционным production backend.",
            ],
        ),
        ReadinessItem(
            id="ws6-governance",
            title="Governance-жизненный цикл кандидатов",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[
                "src/causa/governance/engine.py",
                "src/causa/governance/profiles.py",
                "examples/synthetic_governance_lifecycle_report.json",
                pipeline.trace.candidate.id,
                pipeline.trace.governance_record.id,
            ],
            remaining_work=[
                "Подключить постоянное хранилище governance-записей и конкурентный контроль версий.",
            ],
        ),
        ReadinessItem(
            id="ws7-translation",
            title="Слой юридического объяснения и интерпретируемости",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[
                "src/causa/translation_pipeline.py",
                "examples/synthetic_translation_bundle_report.json",
                pipeline.trace.translation_bundle.id,
                pipeline.trace.translation_bundle.faithfulness_report.id,
                pipeline.trace.translation_bundle.usability_report.id,
            ],
            remaining_work=[
                "Провести пилотную оценку понятности и практической полезности с российскими юристами.",
            ],
        ),
        ReadinessItem(
            id="ws8-evaluation-red-team",
            title="Оценка качества и Red Team",
            status=PipelineStepStatus.WARNING,
            evidence_refs=[
                pipeline.trace.red_team_scenario.id,
                benchmark_report.id,
                practice_utility_report.id,
                privacy_safe_pilot_report.id,
                red_team_report.id,
                counterfactual_artifact.benchmark_report.id,
                counterfactual_artifact.red_team_report.id,
                liability_artifact.benchmark_report.id,
                liability_artifact.red_team_report.id,
                formation_artifact.benchmark_report.id,
                formation_artifact.red_team_report.id,
                invalidity_artifact.benchmark_report.id,
                invalidity_artifact.red_team_report.id,
                security_artifact.benchmark_report.id,
                security_artifact.red_team_report.id,
                dynamics_artifact.benchmark_report.id,
                dynamics_artifact.red_team_report.id,
                performance_remedies_artifact.benchmark_report.id,
                performance_remedies_artifact.red_team_report.id,
                termination_artifact.benchmark_report.id,
                termination_artifact.red_team_report.id,
            ],
            remaining_work=[
                "Получить privacy- и экспертное одобрение до сбора несинтетических пилотных наблюдений.",
                "Подключить проверенного модельного провайдера для формулировки атак с учетом privacy-контролей.",
            ],
        ),
        ReadinessItem(
            id="ws9-zero-to-value",
            title="Синтетический путь Zero-to-Value",
            status=PipelineStepStatus.PASSED,
            evidence_refs=[
                "examples/phase0_supply_dispute_trace.json",
                "examples/synthetic_reviewed_contract_analysis.json",
                "examples/synthetic_translation_bundle_report.json",
                "examples/synthetic_counterfactual_evaluation_report.json",
                "examples/synthetic_liability_evaluation_report.json",
                "examples/synthetic_formation_evaluation_report.json",
                "examples/synthetic_invalidity_evaluation_report.json",
                "examples/synthetic_security_evaluation_report.json",
                "examples/synthetic_obligation_dynamics_evaluation_report.json",
                "examples/synthetic_performance_remedies_evaluation_report.json",
                "examples/synthetic_termination_evaluation_report.json",
                pipeline.id,
            ],
            remaining_work=["Расширить синтетический набор источников и перечень пилотных задач."],
        ),
    ]

    return Phase0ReadinessReport(
        id="phase0-readiness-report-v0",
        project_stage="architectural_prototype",
        project_stage_label_ru="Архитектурный прототип",
        ready_for_production=False,
        summary=(
            "Этап 0 содержит работающий синтетический путь и исполняемый governance-цикл, "
            "но глубина институционального пакета, несинтетическая пилотная проверка "
            "и полнота оценки качества остаются недостаточными для промышленной эксплуатации."
        ),
        items=items,
    )
