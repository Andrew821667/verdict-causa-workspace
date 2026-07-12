from enum import Enum

from pydantic import BaseModel, Field

from causa import __version__ as CORE_VERSION
from causa.core.bootstrap import (
    DEFAULT_BOOTSTRAP_SCHEMA_VERSION,
    DEFAULT_TRANSLATOR_VERSION,
)
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.institutional.contracts.reviewed_analysis import (
    ANALYSIS_PIPELINE_VERSION,
    CASE_EVIDENCE_SCHEMA_VERSION,
)


class CompatibilityStatus(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


class PackageCompatibilityEntry(BaseModel):
    package_version: str
    core_version: str
    bootstrap_schema_versions: list[str] = Field(default_factory=list)
    translator_versions: list[str] = Field(default_factory=list)
    case_evidence_schema_versions: list[str] = Field(default_factory=list)
    analysis_pipeline_versions: list[str] = Field(default_factory=list)
    status: CompatibilityStatus
    notes: list[str] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


class PackageCompatibilityCheck(BaseModel):
    package_id: str
    package_version: str
    core_version: str
    bootstrap_schema_version: str
    translator_version: str
    case_evidence_schema_version: str
    analysis_pipeline_version: str
    supported: bool
    reasons: list[str] = Field(default_factory=list)
    reasons_ru: list[str] = Field(default_factory=list)


CONTRACTS_PACKAGE_COMPATIBILITY = [
    PackageCompatibilityEntry(
        package_version="0.11.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v3"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v3"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed change-and-termination evidence is mandatory for the Phase 0 path.",
            "Formal boundaries cover Civil Code articles 450 through 453 and article 310.",
            "Judicial prerequisites remain distinct from an effective court judgment.",
        ],
        notes_ru=[
            "Проверенные данные об изменении и расторжении обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 450–453 и статью 310 ГК РФ.",
            "Судебные предпосылки отделены от вступившего в силу решения суда.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.10.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v2"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v2"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed contract-formation evidence is mandatory before obligation analysis.",
            "Formal boundaries cover Civil Code articles 432, 435, 438, and 443.",
            "The model does not determine evidence weight or a court outcome.",
        ],
        notes_ru=[
            "Проверенные данные о заключении договора обязательны до анализа обязательства.",
            "Формальные границы охватывают статьи 432, 435, 438 и 443 ГК РФ.",
            "Модель не определяет вес доказательств и результат суда.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.9.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v1"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v1"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed liability evidence is mandatory for the synthetic Phase 0 path.",
            "Formal models cover narrow prerequisites under Civil Code articles 333 and 401.",
            "The model does not determine evidence weight, penalty amount, or a court outcome.",
        ],
        notes_ru=[
            "Проверенные данные об ответственности обязательны для синтетического пути Этапа 0.",
            "Формальная модель покрывает узкие предпосылки статей 333 и 401 ГК РФ.",
            "Модель не определяет вес доказательств, размер снижения или результат суда.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.8.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v0"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "A versioned legal-operator library provides bounded contractual counterfactuals.",
            "Counterfactual branches preserve baseline facts and enforce fact and scenario budgets.",
            "Dedicated benchmark and red-team suites cover operator behavior and bypass attempts.",
        ],
        notes_ru=[
            "Версионированная библиотека legal operators реализует ограниченные договорные контрфакты.",
            "Контрфактические ветви сохраняют исходные факты и соблюдают бюджеты изменений и сценариев.",
            "Отдельные benchmark и Red Team покрывают поведение операторов и попытки обхода ограничений.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.7.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v0"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Russian legal explanations are rendered at executive, professional, and forensic levels.",
            "Template and policy hashes support deterministic faithfulness checks.",
            "Human usability still requires a lawyer pilot.",
        ],
        notes_ru=[
            "Русские юридические объяснения формируются на кратком, профессиональном и forensic-уровнях.",
            "Hash шаблонов и политики обеспечивает детерминированную проверку верности.",
            "Практическая понятность по-прежнему требует пилотной проверки юристами.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.6.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v0"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Decision traces bind policy snapshot id and SHA-256 content hash.",
            "Management Plane policy registration, activation, diff, and rollback are auditable.",
            "No production or real-client-data compatibility claim is implied.",
        ],
        notes_ru=[
            "Трассировка связывает ID снимка политики и SHA-256 hash его содержимого.",
            "Регистрация, активация, semantic diff и откат политик Management Plane аудируемы.",
            "Совместимость с промышленной эксплуатацией и реальными клиентскими данными не заявляется.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.5.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v0"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Russian human-readable reasons are additive to stable machine contracts.",
            "Governance execution records are exported in ru-RU for the Russian-law package.",
            "No production or real-client-data compatibility claim is implied.",
        ],
        notes_ru=[
            "Русские человекочитаемые причины добавлены без изменения стабильных машинных контрактов.",
            "Governance-записи экспортируются с локалью ru-RU для российского правового пакета.",
            "Совместимость с промышленной эксплуатацией и реальными клиентскими данными не заявляется.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.4.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v0"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Synthetic Phase 0 analysis requires reviewed case, temporal, and authority inputs.",
            "Every mapped formal fact retains assertion and source provenance.",
            "No production or real-client-data compatibility claim is implied.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.3.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Synthetic Phase 0 formal checks add damages remedy, causation, and limitation predicates.",
            "No production or real-client-data compatibility claim is implied.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.2.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Synthetic Phase 0 authority policy adds constitutional and regulatory levels.",
            "No production or real-client-data compatibility claim is implied.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.1.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Phase 0 synthetic contractual package only.",
            "No production or real-client-data compatibility claim is implied.",
        ],
    ),
]


def evaluate_contracts_package_compatibility(
    core_version: str = CORE_VERSION,
    bootstrap_schema_version: str = DEFAULT_BOOTSTRAP_SCHEMA_VERSION,
    translator_version: str = DEFAULT_TRANSLATOR_VERSION,
    case_evidence_schema_version: str = CASE_EVIDENCE_SCHEMA_VERSION,
    analysis_pipeline_version: str = ANALYSIS_PIPELINE_VERSION,
) -> PackageCompatibilityCheck:
    matching_entries = [
        entry
        for entry in CONTRACTS_PACKAGE_COMPATIBILITY
        if entry.package_version == CONTRACTS_PACKAGE_MANIFEST.version
        and entry.core_version == core_version
        and bootstrap_schema_version in entry.bootstrap_schema_versions
        and translator_version in entry.translator_versions
        and case_evidence_schema_version in entry.case_evidence_schema_versions
        and analysis_pipeline_version in entry.analysis_pipeline_versions
        and entry.status == CompatibilityStatus.SUPPORTED
    ]
    supported = bool(matching_entries)
    reasons = (
        ["Package, core, schemas, translator, and analysis pipeline coordinates are supported."]
        if supported
        else ["No supported compatibility entry matches the supplied coordinates."]
    )
    reasons_ru = (
        ["Координаты пакета, ядра, схем, транслятора и analysis pipeline поддерживаются."]
        if supported
        else ["Для переданных координат отсутствует поддерживаемая запись совместимости."]
    )

    return PackageCompatibilityCheck(
        package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        package_version=CONTRACTS_PACKAGE_MANIFEST.version,
        core_version=core_version,
        bootstrap_schema_version=bootstrap_schema_version,
        translator_version=translator_version,
        case_evidence_schema_version=case_evidence_schema_version,
        analysis_pipeline_version=analysis_pipeline_version,
        supported=supported,
        reasons=reasons,
        reasons_ru=reasons_ru,
    )
