from dataclasses import dataclass
from datetime import date

from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.institutional.contracts.pilot_fixtures import (
    PILOT_REHEARSAL_DATE,
    build_approved_anonymized_pilot_intake,
    build_maximally_realistic_pilot_intake,
)
from causa.pilot import (
    PilotAdmissionStatus,
    PilotGateCaseResult,
    PilotGateSuiteKind,
    PilotGateSuiteReport,
    PilotIntakeRequest,
    PilotLawfulBasis,
    PilotReviewRole,
    evaluate_pilot_intake,
)


@dataclass(frozen=True)
class PilotGateCase:
    id: str
    title_ru: str
    request: PilotIntakeRequest
    expected_status: PilotAdmissionStatus
    expected_reason_fragment_ru: str | None = None


def _document_update(
    request: PilotIntakeRequest,
    document_index: int = 0,
    **updates: object,
) -> PilotIntakeRequest:
    documents = tuple(
        document.model_copy(update=updates) if idx == document_index else document
        for idx, document in enumerate(request.documents)
    )
    return request.model_copy(update={"documents": documents})


def _signoff_update(
    request: PilotIntakeRequest,
    role: PilotReviewRole,
    **updates: object,
) -> PilotIntakeRequest:
    signoffs = tuple(
        signoff.model_copy(update=updates) if signoff.role == role else signoff
        for signoff in request.signoffs
    )
    return request.model_copy(update={"signoffs": signoffs})


def _benchmark_cases() -> tuple[PilotGateCase, ...]:
    return (
        PilotGateCase(
            id="pilot-benchmark-synthetic",
            title_ru="Синтетическая репетиция без персональных данных",
            request=build_maximally_realistic_pilot_intake(),
            expected_status=PilotAdmissionStatus.APPROVED,
        ),
        PilotGateCase(
            id="pilot-benchmark-consent",
            title_ru="Обезличенный пилот с проверенным согласием",
            request=build_approved_anonymized_pilot_intake(),
            expected_status=PilotAdmissionStatus.APPROVED,
        ),
        PilotGateCase(
            id="pilot-benchmark-contract",
            title_ru="Обезличенный пилот на основании договора с субъектом",
            request=build_approved_anonymized_pilot_intake(
                lawful_basis=PilotLawfulBasis.CONTRACT_WITH_SUBJECT
            ),
            expected_status=PilotAdmissionStatus.APPROVED,
        ),
        PilotGateCase(
            id="pilot-benchmark-statutory-duty",
            title_ru="Обезличенный пилот на основании обязанности по закону",
            request=build_approved_anonymized_pilot_intake(
                lawful_basis=PilotLawfulBasis.STATUTORY_DUTY
            ),
            expected_status=PilotAdmissionStatus.APPROVED,
        ),
        PilotGateCase(
            id="pilot-benchmark-rights",
            title_ru="Обезличенный пилот для осуществления прав и законных интересов",
            request=build_approved_anonymized_pilot_intake(
                lawful_basis=PilotLawfulBasis.RIGHTS_AND_LEGITIMATE_INTERESTS
            ),
            expected_status=PilotAdmissionStatus.APPROVED,
        ),
        PilotGateCase(
            id="pilot-benchmark-commercial-secret",
            title_ru="Пилот с разрешенной владельцем коммерческой тайной",
            request=build_approved_anonymized_pilot_intake(
                lawful_basis=PilotLawfulBasis.CONTRACT_WITH_SUBJECT,
                contains_commercial_secret=True,
            ),
            expected_status=PilotAdmissionStatus.APPROVED,
        ),
    )


def _red_team_cases() -> tuple[PilotGateCase, ...]:
    base = build_approved_anonymized_pilot_intake()
    synthetic = build_maximally_realistic_pilot_intake()
    first_hash = base.documents[0].content_sha256
    return (
        PilotGateCase(
            id="pilot-red-package",
            title_ru="Подмена версии институционального пакета",
            request=base.model_copy(update={"institutional_package_version": "0.0.0"}),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="Координаты институционального пакета",
        ),
        PilotGateCase(
            id="pilot-red-raw-content",
            title_ru="Включение исходного текста в артефакт",
            request=base.model_copy(update={"raw_content_embedded": True}),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="исходное содержимое документов",
        ),
        PilotGateCase(
            id="pilot-red-expired",
            title_ru="Истекший срок хранения",
            request=base.model_copy(update={"retention_until": PILOT_REHEARSAL_DATE}),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="Срок хранения пилотных данных истек",
        ),
        PilotGateCase(
            id="pilot-red-long-retention",
            title_ru="Избыточный срок хранения",
            request=base.model_copy(update={"retention_until": date(2027, 1, 1)}),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="превышает предельные 90 дней",
        ),
        PilotGateCase(
            id="pilot-red-storage",
            title_ru="Неподтвержденный российский контур хранения",
            request=base.model_copy(update={"local_storage_confirmed": False}),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="Хранение данных в российском контуре",
        ),
        PilotGateCase(
            id="pilot-red-cross-border",
            title_ru="Запрос трансграничной передачи",
            request=base.model_copy(update={"cross_border_transfer_requested": True}),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="Трансграничная передача запрещена",
        ),
        PilotGateCase(
            id="pilot-red-external-model",
            title_ru="Передача внешнему модельному провайдеру",
            request=base.model_copy(update={"external_model_access_requested": True}),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="внешнему модельному провайдеру запрещена",
        ),
        *(
            PilotGateCase(
                id=f"pilot-red-control-{field_name}",
                title_ru=f"Отключение обязательного контроля: {label_ru}",
                request=base.model_copy(update={field_name: False}),
                expected_status=PilotAdmissionStatus.BLOCKED,
                expected_reason_fragment_ru=label_ru,
            )
            for field_name, label_ru in (
                ("encryption_at_rest", "шифрование при хранении"),
                ("encryption_in_transit", "шифрование при передаче"),
                ("role_based_access", "ролевой контроль доступа"),
                ("audit_log_enabled", "журналирование доступа"),
                ("deletion_plan_approved", "утвержденный план удаления"),
            )
        ),
        PilotGateCase(
            id="pilot-red-processor",
            title_ru="Обработчик без поручения",
            request=base.model_copy(
                update={"processor_engaged": True, "processor_instruction_ref": None}
            ),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="не зафиксировано поручение",
        ),
        PilotGateCase(
            id="pilot-red-missing-privacy",
            title_ru="Отсутствует privacy-согласование",
            request=base.model_copy(
                update={
                    "signoffs": tuple(
                        item for item in base.signoffs if item.role != PilotReviewRole.PRIVACY
                    )
                }
            ),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="privacy",
        ),
        PilotGateCase(
            id="pilot-red-legal-rejected",
            title_ru="Юридическая роль отклонила запуск",
            request=_signoff_update(base, PilotReviewRole.LEGAL_BASIS, approved=False),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="не одобрила пилотный запуск",
        ),
        PilotGateCase(
            id="pilot-red-future-signoff",
            title_ru="Согласование датировано будущим",
            request=_signoff_update(
                base,
                PilotReviewRole.INFORMATION_SECURITY,
                signed_on=date(2026, 7, 24),
            ),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="датировано будущим числом",
        ),
        PilotGateCase(
            id="pilot-red-same-reviewer",
            title_ru="Совмещение независимых ролей одним проверяющим",
            request=_signoff_update(
                base,
                PilotReviewRole.DOMAIN_OWNER,
                reviewer_ref="reviewer-5a1e0001",
            ),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="назначены одному проверяющему",
        ),
        PilotGateCase(
            id="pilot-red-duplicate-content",
            title_ru="Дублирование документа",
            request=_document_update(base, 1, content_sha256=first_hash),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="повторяющееся содержимое",
        ),
        PilotGateCase(
            id="pilot-red-no-basis",
            title_ru="Персональные данные без основания",
            request=base.model_copy(
                update={
                    "lawful_basis": PilotLawfulBasis.NOT_APPLICABLE,
                    "legal_basis_review_ref": None,
                    "consent_ref": None,
                }
            ),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="не зафиксировано законное основание",
        ),
        PilotGateCase(
            id="pilot-red-no-basis-review",
            title_ru="Основание без юридической проверки",
            request=base.model_copy(update={"legal_basis_review_ref": None}),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="юридическую проверку основания",
        ),
        PilotGateCase(
            id="pilot-red-no-consent",
            title_ru="Согласие выбрано, но не зафиксировано",
            request=base.model_copy(update={"consent_ref": None}),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="запись согласия отсутствует",
        ),
        PilotGateCase(
            id="pilot-red-basis-without-personal-data",
            title_ru="Основание персональных данных для неперсонального набора",
            request=synthetic.model_copy(
                update={
                    "lawful_basis": PilotLawfulBasis.CONTRACT_WITH_SUBJECT,
                    "legal_basis_review_ref": "synthetic-extra-basis",
                }
            ),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="для набора без таких данных",
        ),
        PilotGateCase(
            id="pilot-red-cross-tenant",
            title_ru="Документ другого клиента",
            request=_document_update(base, tenant_ref="tenant-deadbeef"),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="относится к другому tenant",
        ),
        *(
            PilotGateCase(
                id=f"pilot-red-prohibited-{field_name}",
                title_ru=f"Запрещенная категория: {label_ru}",
                request=_document_update(base, **{field_name: True}),
                expected_status=PilotAdmissionStatus.BLOCKED,
                expected_reason_fragment_ru=label_ru,
            )
            for field_name, label_ru in (
                ("contains_special_category_data", "специальные категории данных"),
                ("contains_biometric_data", "биометрические данные"),
                ("contains_minor_data", "данные несовершеннолетних"),
                ("contains_credentials", "учетные данные и секреты доступа"),
                (
                    "contains_state_secret",
                    "сведения, составляющие государственную тайну",
                ),
            )
        ),
        *(
            PilotGateCase(
                id=f"pilot-red-minimization-{field_name}",
                title_ru=f"Неполная минимизация: {label_ru}",
                request=_document_update(base, **{field_name: False}),
                expected_status=PilotAdmissionStatus.BLOCKED,
                expected_reason_fragment_ru=label_ru,
            )
            for field_name, label_ru in (
                ("direct_identifiers_removed", "удаление прямых идентификаторов"),
                (
                    "quasi_identifiers_generalized",
                    "обобщение косвенных идентификаторов",
                ),
                (
                    "irrelevant_content_removed",
                    "удаление не относящихся к цели сведений",
                ),
            )
        ),
        PilotGateCase(
            id="pilot-red-commercial-secret",
            title_ru="Коммерческая тайна без разрешения владельца",
            request=_document_update(
                base,
                contains_commercial_secret=True,
                commercial_secret_owner_approval_ref=None,
            ),
            expected_status=PilotAdmissionStatus.BLOCKED,
            expected_reason_fragment_ru="нет разрешения владельца коммерческой тайны",
        ),
    )


PILOT_GATE_BENCHMARKS = _benchmark_cases()
PILOT_GATE_RED_TEAM_CASES = _red_team_cases()


def _run_case(case: PilotGateCase) -> PilotGateCaseResult:
    decision = evaluate_pilot_intake(
        case.request,
        evaluated_on=PILOT_REHEARSAL_DATE,
        expected_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        expected_package_version=CONTRACTS_PACKAGE_MANIFEST.version,
    )
    matched = case.expected_reason_fragment_ru is None or any(
        case.expected_reason_fragment_ru in reason for reason in decision.reasons_ru
    )
    return PilotGateCaseResult(
        case_id=case.id,
        expected_status=case.expected_status,
        observed_status=decision.status,
        passed=decision.status == case.expected_status and matched,
        matched_reason_fragment_ru=(case.expected_reason_fragment_ru if matched else None),
        reasons_ru=decision.reasons_ru,
    )


def run_pilot_gate_benchmark_suite() -> PilotGateSuiteReport:
    results = tuple(_run_case(case) for case in PILOT_GATE_BENCHMARKS)
    passed = sum(item.passed for item in results)
    return PilotGateSuiteReport(
        id="contracts-pilot-gate-benchmark-v1",
        suite_kind=PilotGateSuiteKind.BENCHMARK,
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_pilot_gate_red_team_suite() -> PilotGateSuiteReport:
    results = tuple(_run_case(case) for case in PILOT_GATE_RED_TEAM_CASES)
    passed = sum(item.passed for item in results)
    return PilotGateSuiteReport(
        id="contracts-pilot-gate-red-team-v1",
        suite_kind=PilotGateSuiteKind.RED_TEAM,
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )
