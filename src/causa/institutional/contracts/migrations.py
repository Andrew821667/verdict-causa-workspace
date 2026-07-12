from enum import Enum

from pydantic import BaseModel, Field

from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST


class MigrationDisposition(str, Enum):
    NOT_REQUIRED = "not_required"
    REQUIRES_REGENERATION = "requires_regeneration"
    UNSUPPORTED = "unsupported"


class PackageArtifactEnvelope(BaseModel):
    id: str
    artifact_type: str
    package_id: str
    package_version: str
    payload: dict[str, object] = Field(default_factory=dict)


class PackageMigrationStep(BaseModel):
    from_version: str
    to_version: str
    reasons: list[str] = Field(default_factory=list)
    reasons_ru: list[str] = Field(default_factory=list)
    replay_commands: list[str] = Field(default_factory=list)


class PackageMigrationReport(BaseModel):
    id: str
    artifact_id: str
    artifact_type: str
    source_package_version: str
    target_package_version: str
    disposition: MigrationDisposition
    disposition_label_ru: str = ""
    steps: list[PackageMigrationStep] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    reasons_ru: list[str] = Field(default_factory=list)
    payload_preserved_without_interpretation: bool


CONTRACTS_PACKAGE_MIGRATION_STEPS = [
    PackageMigrationStep(
        from_version="0.1.0",
        to_version="0.2.0",
        reasons=[
            "Authority policy gained constitutional and regulatory levels.",
            "Authority outcomes must be replayed against the expanded candidate model.",
        ],
        reasons_ru=[
            "Модель юридической силы дополнена конституционным и подзаконным уровнями.",
            "Выводы о приоритете источников должны быть повторно получены на расширенной модели.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_supply_benchmarks.py",
            "python scripts/export_synthetic_supply_red_team.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.2.0",
        to_version="0.3.0",
        reasons=[
            "Constraint results gained remedy, causation, and limitation fields.",
            "Formal outcomes must be regenerated instead of inferred from prior output.",
        ],
        reasons_ru=[
            "Результаты формальной проверки дополнены полями убытков, причинной связи и исковой давности.",
            "Формальные выводы должны быть пересчитаны, а не выведены из прежнего результата.",
        ],
        replay_commands=[
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_synthetic_supply_benchmarks.py",
            "python scripts/export_synthetic_supply_red_team.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.3.0",
        to_version="0.4.0",
        reasons=[
            "Analysis inputs gained reviewed case, temporal, and authority contracts.",
            "Decision traces now retain fact provenance and the complete reviewed analysis result.",
        ],
        reasons_ru=[
            "Входы анализа дополнены проверенными фактами дела, временными данными и источниками-кандидатами.",
            "Трассировка теперь сохраняет происхождение фактов и полный результат проверенного анализа.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_reviewed_contract_analysis.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.4.0",
        to_version="0.5.0",
        reasons=[
            "Russian human-readable legal reasons were added to exported evaluations.",
            "Phase 0 traces now include an executed governance record and ru-RU audit text.",
        ],
        reasons_ru=[
            "В экспортируемые результаты добавлены русские юридически значимые причины.",
            "Трассировка Этапа 0 теперь содержит исполненный governance-журнал и аудит на русском языке.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_reviewed_contract_analysis.py",
            "python scripts/export_synthetic_governance_lifecycle.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
            "python scripts/export_synthetic_supply_benchmarks.py",
            "python scripts/export_synthetic_supply_red_team.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.5.0",
        to_version="0.6.0",
        reasons=[
            "Policy coordinates now require an immutable snapshot id and content hash.",
            "Phase 0 traces embed the active registry state and replayable policy lifecycle.",
        ],
        reasons_ru=[
            "Координаты политики теперь требуют ID неизменяемого снимка и hash содержимого.",
            "Трассировка Этапа 0 включает активное состояние реестра и воспроизводимый жизненный цикл политики.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_management_policy_registry.py",
            "python scripts/export_synthetic_governance_lifecycle.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.6.0",
        to_version="0.7.0",
        reasons=[
            "Translation policy coordinates now bind the template version and content hash.",
            "A three-level Russian translation bundle and its checks must be regenerated from the trace.",
        ],
        reasons_ru=[
            "Координаты Translation Layer теперь связывают версию шаблонов и hash их содержимого.",
            "Трехуровневый русский bundle и его проверки должны быть повторно сформированы из трассировки.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_management_policy_registry.py",
            "python scripts/export_synthetic_translation_bundle.py",
            "python scripts/export_synthetic_governance_lifecycle.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.7.0",
        to_version="0.8.0",
        reasons=[
            "Reviewed analysis now includes bounded counterfactual sensitivity results.",
            "The legal-operator library and revised translation templates are hash-addressed artifacts.",
        ],
        reasons_ru=[
            "Проверенный анализ теперь включает результаты ограниченной контрфактической чувствительности.",
            "Библиотека legal operators и обновленные шаблоны объяснения стали hash-addressed артефактами.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_counterfactual_evaluation.py",
            "python scripts/export_synthetic_reviewed_contract_analysis.py",
            "python scripts/export_synthetic_management_policy_registry.py",
            "python scripts/export_synthetic_translation_bundle.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.8.0",
        to_version="0.9.0",
        reasons=[
            "Reviewed inputs now require a separate liability-evidence contract.",
            "Analysis and translation outputs include formal article 333 and 401 prerequisites.",
        ],
        reasons_ru=[
            "Проверенные входы теперь требуют отдельный контракт данных об ответственности.",
            "Анализ и объяснение включают формальные предпосылки статей 333 и 401 ГК РФ.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_liability_evaluation.py",
            "python scripts/export_synthetic_reviewed_contract_analysis.py",
            "python scripts/export_synthetic_management_policy_registry.py",
            "python scripts/export_synthetic_translation_bundle.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.9.0",
        to_version="0.10.0",
        reasons=[
            "Reviewed inputs now require a separate contract-formation evidence contract.",
            "Analysis and Russian translation outputs include formal articles 432, 435, 438, and 443 boundaries.",
        ],
        reasons_ru=[
            "Проверенные входы теперь требуют отдельный контракт данных о заключении договора.",
            "Анализ и русское объяснение включают формальные границы статей 432, 435, 438 и 443 ГК РФ.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_formation_evaluation.py",
            "python scripts/export_synthetic_reviewed_contract_analysis.py",
            "python scripts/export_synthetic_translation_bundle.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.10.0",
        to_version="0.11.0",
        reasons=[
            "Reviewed inputs now require a separate change-and-termination evidence contract.",
            "Analysis and Russian translation distinguish agreement, judicial, and unilateral paths under articles 450 through 453.",
        ],
        reasons_ru=[
            "Проверенные входы теперь требуют отдельный контракт данных об изменении и расторжении.",
            "Анализ и русское объяснение разделяют соглашение, судебный путь и односторонний отказ по статьям 450–453 ГК РФ.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_termination_evaluation.py",
            "python scripts/export_synthetic_reviewed_contract_analysis.py",
            "python scripts/export_synthetic_translation_bundle.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.11.0",
        to_version="0.12.0",
        reasons=[
            "Reviewed inputs now require a separate transaction-invalidity evidence contract.",
            "Analysis and Russian translation distinguish void and voidable grounds, procedure, and effects under articles 166 through 181.",
        ],
        reasons_ru=[
            "Проверенные входы теперь требуют отдельный контракт данных о недействительности сделки.",
            "Анализ и русское объяснение разделяют ничтожность, оспоримость, процедуру и последствия по статьям 166–181 ГК РФ.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_invalidity_evaluation.py",
            "python scripts/export_synthetic_reviewed_contract_analysis.py",
            "python scripts/export_synthetic_translation_bundle.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
        ],
    ),
    PackageMigrationStep(
        from_version="0.12.0",
        to_version="0.13.0",
        reasons=[
            "Reviewed inputs now require a separate performance-security evidence contract.",
            "Analysis and Russian translation distinguish the security mechanisms and enforcement paths under articles 329 through 381.2.",
        ],
        reasons_ru=[
            "Проверенные входы теперь требуют отдельный контракт данных об обеспечении исполнения обязательств.",
            "Анализ и русское объяснение разделяют способы обеспечения и маршруты их реализации по статьям 329–381.2 ГК РФ.",
        ],
        replay_commands=[
            "python scripts/export_synthetic_security_evaluation.py",
            "python scripts/export_synthetic_reviewed_contract_analysis.py",
            "python scripts/export_synthetic_translation_bundle.py",
            "python scripts/export_phase0_demo_trace.py",
            "python scripts/export_phase0_readiness_report.py",
        ],
    ),
]


MIGRATION_DISPOSITION_LABELS_RU = {
    MigrationDisposition.NOT_REQUIRED: "Миграция не требуется",
    MigrationDisposition.REQUIRES_REGENERATION: "Требуется повторное формирование",
    MigrationDisposition.UNSUPPORTED: "Миграция не поддерживается",
}


def build_contracts_package_migration_report(
    artifact: PackageArtifactEnvelope,
) -> PackageMigrationReport:
    target_version = CONTRACTS_PACKAGE_MANIFEST.version
    if artifact.package_id != CONTRACTS_PACKAGE_MANIFEST.id:
        return PackageMigrationReport(
            id=f"migration:{artifact.id}:unsupported",
            artifact_id=artifact.id,
            artifact_type=artifact.artifact_type,
            source_package_version=artifact.package_version,
            target_package_version=target_version,
            disposition=MigrationDisposition.UNSUPPORTED,
            disposition_label_ru=MIGRATION_DISPOSITION_LABELS_RU[MigrationDisposition.UNSUPPORTED],
            reasons=["Artifact package id does not match contracts-ru-v0."],
            reasons_ru=["Идентификатор пакета артефакта не соответствует contracts-ru-v0."],
            payload_preserved_without_interpretation=True,
        )

    if artifact.package_version == target_version:
        return PackageMigrationReport(
            id=f"migration:{artifact.id}:current",
            artifact_id=artifact.id,
            artifact_type=artifact.artifact_type,
            source_package_version=artifact.package_version,
            target_package_version=target_version,
            disposition=MigrationDisposition.NOT_REQUIRED,
            disposition_label_ru=MIGRATION_DISPOSITION_LABELS_RU[MigrationDisposition.NOT_REQUIRED],
            reasons=["Artifact already uses the current package version."],
            reasons_ru=["Артефакт уже использует текущую версию пакета."],
            payload_preserved_without_interpretation=True,
        )

    steps: list[PackageMigrationStep] = []
    current_version = artifact.package_version
    while current_version != target_version:
        step = next(
            (
                candidate
                for candidate in CONTRACTS_PACKAGE_MIGRATION_STEPS
                if candidate.from_version == current_version
            ),
            None,
        )
        if step is None:
            return PackageMigrationReport(
                id=f"migration:{artifact.id}:unsupported",
                artifact_id=artifact.id,
                artifact_type=artifact.artifact_type,
                source_package_version=artifact.package_version,
                target_package_version=target_version,
                disposition=MigrationDisposition.UNSUPPORTED,
                disposition_label_ru=MIGRATION_DISPOSITION_LABELS_RU[
                    MigrationDisposition.UNSUPPORTED
                ],
                steps=steps,
                reasons=["No ordered migration path reaches the current package version."],
                reasons_ru=["Отсутствует последовательный путь миграции к текущей версии пакета."],
                payload_preserved_without_interpretation=True,
            )
        steps.append(step)
        current_version = step.to_version

    return PackageMigrationReport(
        id=f"migration:{artifact.id}:to-{target_version}",
        artifact_id=artifact.id,
        artifact_type=artifact.artifact_type,
        source_package_version=artifact.package_version,
        target_package_version=target_version,
        disposition=MigrationDisposition.REQUIRES_REGENERATION,
        disposition_label_ru=MIGRATION_DISPOSITION_LABELS_RU[
            MigrationDisposition.REQUIRES_REGENERATION
        ],
        steps=steps,
        reasons=[
            "Legacy artifact is retained as input evidence only.",
            "Replay is required because package analysis or artifact semantics changed.",
        ],
        reasons_ru=[
            "Прежний артефакт сохраняется только как входное доказательство.",
            "Требуется повторное формирование, поскольку изменились семантика анализа или форма артефакта.",
        ],
        payload_preserved_without_interpretation=True,
    )
