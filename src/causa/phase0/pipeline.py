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
                "examples/migrations/contracts-ru-v0-0.1.0-to-0.7.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.3.0-to-0.7.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.4.0-to-0.7.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.5.0-to-0.7.0-migration-report.json",
                "examples/migrations/contracts-ru-v0-0.6.0-to-0.7.0-migration-report.json",
                f"{compatibility_check.package_id}@{compatibility_check.package_version}",
            ],
            remaining_work=[
                "Расширить словарь, правила юридической силы, временные правила, правовые операторы и контрольные сценарии.",
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
