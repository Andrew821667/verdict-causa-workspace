import hashlib
import json
from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causa.evaluation import (
    PilotDataOrigin,
    PilotTaskCategory,
    PrivacySafePilotUtilityReport,
)


PILOT_INTAKE_SCHEMA_VERSION = "pilot.intake.v1"
PILOT_GATE_VERSION = "pilot-admission-gate-v1"
PILOT_REHEARSAL_SCHEMA_VERSION = "pilot.rehearsal.v1"


class PilotAdmissionStatus(str, Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"


class PilotPurpose(str, Enum):
    CONTRACT_DISPUTE_EVALUATION = "contract_dispute_evaluation"


class PilotLawfulBasis(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    SUBJECT_CONSENT = "subject_consent"
    CONTRACT_WITH_SUBJECT = "contract_with_subject"
    STATUTORY_DUTY = "statutory_duty"
    RIGHTS_AND_LEGITIMATE_INTERESTS = "rights_and_legitimate_interests"


class PilotDocumentKind(str, Enum):
    CONTRACT = "contract"
    SPECIFICATION = "specification"
    DELIVERY_DOCUMENT = "delivery_document"
    ACCEPTANCE_DOCUMENT = "acceptance_document"
    PAYMENT_DOCUMENT = "payment_document"
    CLAIM = "claim"
    BUSINESS_CORRESPONDENCE = "business_correspondence"
    EXPERT_REPORT = "expert_report"


class PilotReviewRole(str, Enum):
    PRIVACY = "privacy"
    LEGAL_BASIS = "legal_basis"
    INFORMATION_SECURITY = "information_security"
    DOMAIN_OWNER = "domain_owner"


class PilotGateSuiteKind(str, Enum):
    BENCHMARK = "benchmark"
    RED_TEAM = "red_team"


class PilotDocumentManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^pilot-doc-[a-f0-9]{8}$")
    tenant_ref: str = Field(pattern=r"^tenant-[a-f0-9]{8}$")
    kind: PilotDocumentKind
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    page_count: int = Field(ge=1, le=500)
    extracted_fact_count: int = Field(ge=0)
    contains_personal_data: bool
    contains_special_category_data: bool
    contains_biometric_data: bool
    contains_minor_data: bool
    contains_credentials: bool
    contains_state_secret: bool
    contains_commercial_secret: bool
    direct_identifiers_removed: bool
    quasi_identifiers_generalized: bool
    irrelevant_content_removed: bool
    commercial_secret_owner_approval_ref: str | None = None


class PilotReviewSignoff(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: PilotReviewRole
    reviewer_ref: str = Field(pattern=r"^reviewer-[a-f0-9]{8}$")
    approved: bool
    signed_on: date
    record_ref: str = Field(min_length=1, max_length=160)


class PilotIntakeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^pilot-intake-[a-f0-9]{8}$")
    schema_version: str = PILOT_INTAKE_SCHEMA_VERSION
    case_ref: str = Field(pattern=r"^case-[a-f0-9]{8}$")
    tenant_ref: str = Field(pattern=r"^tenant-[a-f0-9]{8}$")
    institutional_package_id: str
    institutional_package_version: str
    data_origin: PilotDataOrigin
    task_category: PilotTaskCategory
    purpose: PilotPurpose
    lawful_basis: PilotLawfulBasis
    legal_basis_review_ref: str | None = None
    consent_ref: str | None = None
    processor_engaged: bool
    processor_instruction_ref: str | None = None
    local_storage_confirmed: bool
    cross_border_transfer_requested: bool
    external_model_access_requested: bool
    encryption_at_rest: bool
    encryption_in_transit: bool
    role_based_access: bool
    audit_log_enabled: bool
    deletion_plan_approved: bool
    raw_content_embedded: bool
    retention_until: date
    documents: tuple[PilotDocumentManifestEntry, ...] = Field(min_length=1)
    signoffs: tuple[PilotReviewSignoff, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_manifest_items(self) -> "PilotIntakeRequest":
        document_ids = [item.id for item in self.documents]
        if len(document_ids) != len(set(document_ids)):
            raise ValueError("Pilot document manifest contains duplicate ids.")
        roles = [item.role for item in self.signoffs]
        if len(roles) != len(set(roles)):
            raise ValueError("Pilot intake contains duplicate review roles.")
        return self


class PilotGateDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    gate_version: str = PILOT_GATE_VERSION
    intake_id: str
    intake_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    evaluated_on: date
    status: PilotAdmissionStatus
    execution_allowed: bool
    reasons: tuple[str, ...]
    reasons_ru: tuple[str, ...]
    required_actions_ru: tuple[str, ...]
    warnings_ru: tuple[str, ...]
    control_refs: tuple[str, ...]

    @model_validator(mode="after")
    def require_consistent_status(self) -> "PilotGateDecision":
        if self.execution_allowed != (self.status == PilotAdmissionStatus.APPROVED):
            raise ValueError("Pilot gate status and execution flag disagree.")
        if self.status == PilotAdmissionStatus.BLOCKED and not self.reasons_ru:
            raise ValueError("Blocked pilot decision requires reasons.")
        return self


class PilotRunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^pilot-run-[a-f0-9]{8}$")
    intake_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    gate_decision_id: str
    institutional_package_id: str
    institutional_package_version: str
    decision_trace_ref: str
    reviewed_analysis_ref: str
    translation_bundle_ref: str
    policy_snapshot_ref: str
    policy_content_hash: str = Field(pattern=r"^(sha256:)?[a-f0-9]{64}$")
    source_hashes: tuple[str, ...] = Field(min_length=1)
    executed_on: date
    raw_content_retained: bool = False
    human_review_required: bool = True

    @model_validator(mode="after")
    def preserve_pilot_boundaries(self) -> "PilotRunManifest":
        if self.raw_content_retained:
            raise ValueError("Pilot run manifest cannot retain raw content.")
        if not self.human_review_required:
            raise ValueError("Pilot run must require human review.")
        if len(self.source_hashes) != len(set(self.source_hashes)):
            raise ValueError("Pilot run source hashes must be unique.")
        return self


class PilotGateCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    expected_status: PilotAdmissionStatus
    observed_status: PilotAdmissionStatus
    passed: bool
    matched_reason_fragment_ru: str | None = None
    reasons_ru: tuple[str, ...]


class PilotGateSuiteReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    suite_kind: PilotGateSuiteKind
    total: int
    passed: int
    failed: int
    results: tuple[PilotGateCaseResult, ...]

    @model_validator(mode="after")
    def validate_totals(self) -> "PilotGateSuiteReport":
        if self.total != len(self.results):
            raise ValueError("Pilot gate suite total does not match results.")
        passed = sum(item.passed for item in self.results)
        if self.passed != passed or self.failed != self.total - passed:
            raise ValueError("Pilot gate suite counters do not match results.")
        return self


class PilotRehearsalArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    schema_version: str = PILOT_REHEARSAL_SCHEMA_VERSION
    locale: str = "ru-RU"
    disclaimer_ru: str
    intake: PilotIntakeRequest
    gate_decision: PilotGateDecision
    run_manifest: PilotRunManifest | None
    utility_report: PrivacySafePilotUtilityReport
    benchmark_report: PilotGateSuiteReport
    red_team_report: PilotGateSuiteReport

    @model_validator(mode="after")
    def validate_rehearsal_links(self) -> "PilotRehearsalArtifact":
        fingerprint = build_pilot_intake_fingerprint(self.intake)
        if self.gate_decision.intake_id != self.intake.id:
            raise ValueError("Pilot gate decision references another intake.")
        if self.gate_decision.intake_fingerprint != fingerprint:
            raise ValueError("Pilot gate decision fingerprint is stale.")
        if self.gate_decision.execution_allowed:
            if self.run_manifest is None:
                raise ValueError("Approved pilot intake requires a run manifest.")
            if self.run_manifest.intake_fingerprint != fingerprint:
                raise ValueError("Pilot run manifest fingerprint is stale.")
            if self.run_manifest.gate_decision_id != self.gate_decision.id:
                raise ValueError("Pilot run manifest references another gate decision.")
            if (
                self.run_manifest.institutional_package_id != self.intake.institutional_package_id
                or self.run_manifest.institutional_package_version
                != self.intake.institutional_package_version
            ):
                raise ValueError("Pilot run package coordinates disagree with intake.")
            expected_hashes = {item.content_sha256 for item in self.intake.documents}
            if set(self.run_manifest.source_hashes) != expected_hashes:
                raise ValueError("Pilot run source hashes disagree with intake manifest.")
        elif self.run_manifest is not None:
            raise ValueError("Blocked pilot intake cannot have a run manifest.")
        if any(
            item.gate_decision_ref != self.gate_decision.id
            for item in self.utility_report.observations
        ):
            raise ValueError("Pilot utility observation references another gate decision.")
        if self.run_manifest is not None and any(
            item.decision_trace_ref != self.run_manifest.decision_trace_ref
            for item in self.utility_report.observations
        ):
            raise ValueError("Pilot utility observation references another decision trace.")
        if self.utility_report.data_origin != self.intake.data_origin:
            raise ValueError("Pilot utility report data origin disagrees with intake.")
        if self.benchmark_report.suite_kind != PilotGateSuiteKind.BENCHMARK:
            raise ValueError("Pilot benchmark report has the wrong suite kind.")
        if self.red_team_report.suite_kind != PilotGateSuiteKind.RED_TEAM:
            raise ValueError("Pilot red-team report has the wrong suite kind.")
        return self


def build_pilot_intake_fingerprint(request: PilotIntakeRequest) -> str:
    payload = json.dumps(
        request.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evaluate_pilot_intake(
    request: PilotIntakeRequest,
    *,
    evaluated_on: date,
    expected_package_id: str,
    expected_package_version: str,
) -> PilotGateDecision:
    reasons: list[str] = []
    reasons_ru: list[str] = []
    actions_ru: list[str] = []
    warnings_ru: list[str] = []

    def block(reason: str, reason_ru: str, action_ru: str) -> None:
        reasons.append(reason)
        reasons_ru.append(reason_ru)
        actions_ru.append(action_ru)

    if request.schema_version != PILOT_INTAKE_SCHEMA_VERSION:
        block(
            "Unsupported pilot intake schema.",
            "Версия схемы пилотного допуска не поддерживается.",
            "Повторно сформировать intake по действующей схеме.",
        )
    if (
        request.institutional_package_id != expected_package_id
        or request.institutional_package_version != expected_package_version
    ):
        block(
            "Institutional package coordinates do not match the active package.",
            "Координаты институционального пакета не совпадают с активной версией.",
            "Повторить анализ на активной версии пакета.",
        )
    if request.raw_content_embedded:
        block(
            "Raw content is embedded in the pilot artifact.",
            "В пилотный артефакт включено исходное содержимое документов.",
            "Удалить исходный текст и оставить только безопасный манифест.",
        )
    if request.retention_until <= evaluated_on:
        block(
            "Pilot retention period has expired.",
            "Срок хранения пилотных данных истек.",
            "Удалить данные либо оформить новый ограниченный срок хранения.",
        )
    elif (request.retention_until - evaluated_on).days > 90:
        block(
            "Pilot retention period exceeds the v1 limit.",
            "Срок хранения превышает предельные 90 дней для пилотного контура v1.",
            "Сократить срок хранения до 90 дней или менее.",
        )
    if not request.local_storage_confirmed:
        block(
            "Local storage is not confirmed.",
            "Хранение данных в российском контуре не подтверждено.",
            "Подтвердить допустимый локальный контур хранения.",
        )
    if request.cross_border_transfer_requested:
        block(
            "Cross-border transfer is disabled in pilot gate v1.",
            "Трансграничная передача запрещена пилотным контуром v1.",
            "Использовать российский контур без трансграничной передачи.",
        )
    if request.external_model_access_requested:
        block(
            "External model access is disabled in pilot gate v1.",
            "Передача пилотных данных внешнему модельному провайдеру запрещена.",
            "Использовать утвержденный изолированный вычислительный контур.",
        )
    security_controls = (
        (request.encryption_at_rest, "шифрование при хранении"),
        (request.encryption_in_transit, "шифрование при передаче"),
        (request.role_based_access, "ролевой контроль доступа"),
        (request.audit_log_enabled, "журналирование доступа"),
        (request.deletion_plan_approved, "утвержденный план удаления"),
    )
    for enabled, label_ru in security_controls:
        if not enabled:
            block(
                f"Required security control is missing: {label_ru}.",
                f"Не подтвержден обязательный контроль: {label_ru}.",
                f"Подтвердить контроль «{label_ru}».",
            )
    if request.processor_engaged and not request.processor_instruction_ref:
        block(
            "Processor instruction is missing.",
            "Для привлеченного обработчика не зафиксировано поручение на обработку.",
            "Добавить ссылку на проверенное поручение обработчику.",
        )

    required_roles = set(PilotReviewRole)
    signoffs = {item.role: item for item in request.signoffs}
    for role in sorted(required_roles, key=lambda item: item.value):
        if role not in signoffs:
            block(
                f"Required review signoff is missing: {role.value}.",
                f"Отсутствует обязательное согласование роли «{role.value}».",
                "Получить недостающее согласование до запуска.",
            )
            continue
        signoff = signoffs[role]
        if not signoff.approved:
            block(
                f"Review signoff rejected intake: {role.value}.",
                f"Роль «{role.value}» не одобрила пилотный запуск.",
                "Устранить замечания и пройти согласование повторно.",
            )
        if signoff.signed_on > evaluated_on:
            block(
                f"Review signoff is dated in the future: {role.value}.",
                f"Согласование роли «{role.value}» датировано будущим числом.",
                "Исправить дату и подтвердить согласование.",
            )
    approved_reviewers = [item.reviewer_ref for item in request.signoffs if item.approved]
    if len(approved_reviewers) != len(set(approved_reviewers)):
        block(
            "Independent review roles use the same reviewer.",
            "Независимые роли согласования назначены одному проверяющему.",
            "Разделить privacy, legal, security и domain-review между разными лицами.",
        )

    content_hashes = [item.content_sha256 for item in request.documents]
    if len(content_hashes) != len(set(content_hashes)):
        block(
            "Pilot document manifest contains duplicate content.",
            "Манифест содержит повторяющееся содержимое документов.",
            "Удалить дубликаты до запуска.",
        )

    contains_personal_data = any(item.contains_personal_data for item in request.documents)
    if contains_personal_data:
        if request.lawful_basis == PilotLawfulBasis.NOT_APPLICABLE:
            block(
                "Personal data has no recorded lawful basis.",
                "Для персональных данных не зафиксировано законное основание обработки.",
                "Юридически проверить и зафиксировать применимое основание.",
            )
        if not request.legal_basis_review_ref:
            block(
                "Personal data legal-basis review is missing.",
                "Отсутствует ссылка на юридическую проверку основания обработки.",
                "Добавить запись юридической проверки основания.",
            )
        if request.lawful_basis == PilotLawfulBasis.SUBJECT_CONSENT and not request.consent_ref:
            block(
                "Consent is the selected basis but no consent record is linked.",
                "Выбрано согласие субъекта, но запись согласия отсутствует.",
                "Добавить проверенную запись согласия субъекта.",
            )
    elif request.lawful_basis != PilotLawfulBasis.NOT_APPLICABLE:
        block(
            "A personal-data lawful basis is set for a non-personal dataset.",
            "Основание обработки персональных данных указано для набора без таких данных.",
            "Установить основание `not_applicable` либо исправить классификацию.",
        )

    for document in request.documents:
        if document.tenant_ref != request.tenant_ref:
            block(
                f"Document {document.id} belongs to another tenant.",
                f"Документ {document.id} относится к другому tenant.",
                "Исключить межклиентское смешение документов.",
            )
        prohibited_flags = (
            (document.contains_special_category_data, "специальные категории данных"),
            (document.contains_biometric_data, "биометрические данные"),
            (document.contains_minor_data, "данные несовершеннолетних"),
            (document.contains_credentials, "учетные данные и секреты доступа"),
            (document.contains_state_secret, "сведения, составляющие государственную тайну"),
        )
        for enabled, label_ru in prohibited_flags:
            if enabled:
                block(
                    f"Document {document.id} contains prohibited data: {label_ru}.",
                    f"Документ {document.id} содержит запрещенную категорию: {label_ru}.",
                    f"Исключить из пилота {label_ru}.",
                )
        if document.contains_personal_data:
            minimization_controls = (
                (
                    document.direct_identifiers_removed,
                    "удаление прямых идентификаторов",
                ),
                (
                    document.quasi_identifiers_generalized,
                    "обобщение косвенных идентификаторов",
                ),
                (
                    document.irrelevant_content_removed,
                    "удаление не относящихся к цели сведений",
                ),
            )
            for enabled, label_ru in minimization_controls:
                if not enabled:
                    block(
                        f"Document {document.id} is not minimized: {label_ru}.",
                        f"Для документа {document.id} не подтверждено: {label_ru}.",
                        f"Выполнить действие «{label_ru}».",
                    )
        if (
            document.contains_commercial_secret
            and not document.commercial_secret_owner_approval_ref
        ):
            block(
                f"Document {document.id} lacks commercial-secret owner approval.",
                f"Для документа {document.id} нет разрешения владельца коммерческой тайны.",
                "Получить и связать разрешение владельца конфиденциальной информации.",
            )

    required_document_kinds = {
        PilotTaskCategory.SUPPLY_DELIVERY: {
            PilotDocumentKind.CONTRACT,
            PilotDocumentKind.SPECIFICATION,
            PilotDocumentKind.DELIVERY_DOCUMENT,
            PilotDocumentKind.CLAIM,
        },
        PilotTaskCategory.PAYMENT: {
            PilotDocumentKind.CONTRACT,
            PilotDocumentKind.PAYMENT_DOCUMENT,
            PilotDocumentKind.CLAIM,
        },
        PilotTaskCategory.DEFECTS: {
            PilotDocumentKind.CONTRACT,
            PilotDocumentKind.ACCEPTANCE_DOCUMENT,
            PilotDocumentKind.CLAIM,
        },
        PilotTaskCategory.AUTHORITY: {PilotDocumentKind.CONTRACT},
    }
    actual_kinds = {item.kind for item in request.documents}
    missing_kinds = required_document_kinds[request.task_category] - actual_kinds
    if missing_kinds:
        missing = ", ".join(sorted(item.value for item in missing_kinds))
        warnings_ru.append(
            "Для полноты пилотного анализа не хватает типов документов: "
            f"{missing}. Запуск допустим, но evidence gaps должны быть показаны юристу."
        )
    if request.data_origin == PilotDataOrigin.SYNTHETIC_SCHEMA_DEMO:
        warnings_ru.append(
            "Синтетическая репетиция проверяет архитектуру допуска, но не подтверждает "
            "полезность на данных пилотного заказчика."
        )

    fingerprint = build_pilot_intake_fingerprint(request)
    status = PilotAdmissionStatus.BLOCKED if reasons_ru else PilotAdmissionStatus.APPROVED
    control_refs = {
        *(item.record_ref for item in request.signoffs),
        *(
            item.commercial_secret_owner_approval_ref
            for item in request.documents
            if item.commercial_secret_owner_approval_ref
        ),
    }
    if request.legal_basis_review_ref:
        control_refs.add(request.legal_basis_review_ref)
    if request.consent_ref:
        control_refs.add(request.consent_ref)
    if request.processor_instruction_ref:
        control_refs.add(request.processor_instruction_ref)
    return PilotGateDecision(
        id=f"pilot-gate:{request.id}:{fingerprint[:12]}",
        intake_id=request.id,
        intake_fingerprint=fingerprint,
        evaluated_on=evaluated_on,
        status=status,
        execution_allowed=status == PilotAdmissionStatus.APPROVED,
        reasons=tuple(reasons),
        reasons_ru=tuple(reasons_ru),
        required_actions_ru=tuple(dict.fromkeys(actions_ru)),
        warnings_ru=tuple(warnings_ru),
        control_refs=tuple(sorted(control_refs)),
    )
