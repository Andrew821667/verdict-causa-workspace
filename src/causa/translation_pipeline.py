from enum import Enum

from pydantic import BaseModel, Field, model_validator

from causa.governance.engine import GovernanceRecord
from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisRequest,
    ReviewedContractAnalysisResult,
)
from causa.management.policy_registry import PolicySnapshot
from causa.translation import (
    TranslationArtifact,
    TranslationAssertion,
    TranslationAssertionCode,
    TranslationLevel,
)
from causa.translation_templates import (
    TranslationTemplateSet,
    build_russian_translation_template_set,
)


TRANSLATION_PIPELINE_VERSION = "translation-pipeline-ru-v0"
TRANSLATION_DISCLAIMER_RU = (
    "Синтетический результат. Не является юридической консультацией и требует проверки юристом."
)


class TranslationCheckSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class TranslationCheckIssue(BaseModel):
    code: str
    severity: TranslationCheckSeverity
    level: TranslationLevel | None = None
    message_ru: str


class TranslationFaithfulnessReport(BaseModel):
    id: str
    trace_id: str
    passed: bool
    checked_levels: list[TranslationLevel] = Field(default_factory=list)
    issues: list[TranslationCheckIssue] = Field(default_factory=list)
    summary_ru: list[str] = Field(default_factory=list)


class TranslationUsabilityReport(BaseModel):
    id: str
    trace_id: str
    structural_checks_passed: bool
    requires_human_pilot: bool = True
    checked_levels: list[TranslationLevel] = Field(default_factory=list)
    issues: list[TranslationCheckIssue] = Field(default_factory=list)
    scope_ru: str
    summary_ru: list[str] = Field(default_factory=list)


class ReasoningPathComparison(BaseModel):
    id: str
    active_path_ru: list[str] = Field(default_factory=list)
    alternative_path_ru: list[str] = Field(default_factory=list)
    material_differences_ru: list[str] = Field(default_factory=list)
    selected_path: str
    selection_reason_ru: str


class TranslationBundle(BaseModel):
    id: str
    trace_id: str
    locale: str = "ru-RU"
    pipeline_version: str = TRANSLATION_PIPELINE_VERSION
    template_set_id: str
    template_version: str
    template_content_hash: str
    policy_snapshot_id: str
    policy_content_hash: str
    artifacts: list[TranslationArtifact] = Field(default_factory=list)
    path_comparisons: list[ReasoningPathComparison] = Field(default_factory=list)
    faithfulness_report: TranslationFaithfulnessReport
    usability_report: TranslationUsabilityReport
    ready_for_human_review: bool

    @model_validator(mode="after")
    def validate_bundle_integrity(self) -> "TranslationBundle":
        levels = [artifact.level for artifact in self.artifacts]
        if set(levels) != set(TranslationLevel) or len(levels) != len(set(levels)):
            raise ValueError("Bundle должен содержать ровно по одному артефакту каждого уровня.")
        for artifact in self.artifacts:
            if artifact.trace_id != self.trace_id:
                raise ValueError("Артефакт Translation Layer относится к другой трассировке.")
            if (
                artifact.template_version != self.template_version
                or artifact.template_content_hash != self.template_content_hash
            ):
                raise ValueError("Координаты шаблонов в bundle не согласованы.")
            if (
                artifact.policy_snapshot_id != self.policy_snapshot_id
                or artifact.policy_content_hash != self.policy_content_hash
            ):
                raise ValueError("Координаты политики в bundle не согласованы.")
            if not artifact.faithfulness_checked or not artifact.usability_checked:
                raise ValueError("Артефакт в bundle должен пройти обе автоматические проверки.")
            if artifact.faithfulness_passed != self.faithfulness_report.passed:
                raise ValueError("Флаг верности артефакта не согласован с отчетом.")
            if artifact.usability_passed != self.usability_report.structural_checks_passed:
                raise ValueError("Флаг usability артефакта не согласован с отчетом.")
        if (
            self.faithfulness_report.trace_id != self.trace_id
            or self.usability_report.trace_id != self.trace_id
        ):
            raise ValueError("Отчеты Translation Layer относятся к другой трассировке.")
        expected_ready = (
            self.faithfulness_report.passed and self.usability_report.structural_checks_passed
        )
        if self.ready_for_human_review != expected_ready:
            raise ValueError("Готовность bundle не согласована с результатами проверок.")
        return self

    def artifact_for(self, level: TranslationLevel) -> TranslationArtifact:
        return next(artifact for artifact in self.artifacts if artifact.level == level)


class TranslationBundleArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str = TRANSLATION_DISCLAIMER_RU
    bundle: TranslationBundle


def _yes_no(value: bool) -> str:
    return "Да" if value else "Нет"


def _provenance_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        source_ref
        for item in result.evidence_mapping.provenance
        if item.fact_name in fact_names
        for source_ref in item.source_refs
    }
    return sorted(references)


def _liability_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        *result.liability_evidence_mapping.legal_source_refs,
        *(
            source_ref
            for item in result.liability_evidence_mapping.provenance
            if item.fact_name in fact_names
            for source_ref in item.source_refs
        ),
    }
    return sorted(references)


def _formation_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        *result.formation_evidence_mapping.legal_source_refs,
        *(
            source_ref
            for item in result.formation_evidence_mapping.provenance
            if item.fact_name in fact_names
            for source_ref in item.source_refs
        ),
    }
    return sorted(references)


def _termination_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        *result.termination_evidence_mapping.legal_source_refs,
        *(
            source_ref
            for item in result.termination_evidence_mapping.provenance
            if item.fact_name in fact_names
            for source_ref in item.source_refs
        ),
    }
    return sorted(references)


def _invalidity_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        *result.invalidity_evidence_mapping.legal_source_refs,
        *(
            source_ref
            for item in result.invalidity_evidence_mapping.provenance
            if item.fact_name in fact_names
            for source_ref in item.source_refs
        ),
    }
    return sorted(references)


def _security_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        *result.security_evidence_mapping.legal_source_refs,
        *(
            source_ref
            for item in result.security_evidence_mapping.provenance
            if item.fact_name in fact_names
            for source_ref in item.source_refs
        ),
    }
    return sorted(references)


def _dynamics_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        *result.obligation_dynamics_evidence_mapping.legal_source_refs,
        *(
            source_ref
            for item in result.obligation_dynamics_evidence_mapping.provenance
            if item.fact_name in fact_names
            for source_ref in item.source_refs
        ),
    }
    return sorted(references)


def _performance_remedies_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        *result.performance_remedies_evidence_mapping.legal_source_refs,
        *(
            source_ref
            for item in result.performance_remedies_evidence_mapping.provenance
            if item.fact_name in fact_names
            for source_ref in item.source_refs
        ),
    }
    return sorted(references)


def _sale_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        *result.sale_evidence_mapping.legal_source_refs,
        *(
            source_ref
            for item in result.sale_evidence_mapping.provenance
            if item.fact_name in fact_names
            for source_ref in item.source_refs
        ),
    }
    return sorted(references)


def _supply_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        *result.supply_evidence_mapping.legal_source_refs,
        *(
            source_ref
            for item in result.supply_evidence_mapping.provenance
            if item.fact_name in fact_names
            for source_ref in item.source_refs
        ),
    }
    return sorted(references)


def build_translation_assertions(
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
) -> list[TranslationAssertion]:
    evaluation = result.constraint_evaluation
    authority = result.authority_evaluation
    authority_refs = list(request.authority_input.candidate_source_ids)
    counterfactual_report = result.counterfactual_sensitivity
    liability = result.liability_evaluation
    formation = result.formation_evaluation
    invalidity = result.invalidity_evaluation
    security = result.security_evaluation
    dynamics = result.obligation_dynamics_evaluation
    performance_remedies = result.performance_remedies_evaluation
    sale = result.sale_evaluation
    supply = result.supply_evaluation
    termination = result.termination_evaluation
    critical_scenario = (
        next(
            scenario
            for scenario in counterfactual_report.scenarios
            if scenario.id == counterfactual_report.critical_scenario_ids[0]
        )
        if counterfactual_report.critical_scenario_ids
        else None
    )
    assertions = [
        TranslationAssertion(
            code=TranslationAssertionCode.SOURCE_APPLICABLE,
            value=result.source_applicability.applicable,
            text_ru=(
                "Источник проверенной нормы применим на дату оценки."
                if result.source_applicability.applicable
                else "Источник проверенной нормы не применим на дату оценки."
            ),
            source_refs=[request.reviewed_norm.source_id],
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.VALID_OFFER,
            value=formation.valid_offer,
            text_ru=(
                "Формальные признаки оферты подтверждены."
                if formation.valid_offer
                else "Полный набор формальных признаков оферты не подтвержден."
            ),
            source_refs=_formation_refs(
                result,
                "proposal_made",
                "proposal_addressed_to_counterparty",
                "intent_to_be_bound",
                "subject_matter_defined_in_offer",
                "statutory_essential_terms_defined_in_offer",
                "party_declared_essential_terms_defined_in_offer",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.CONTRACT_CONCLUDED_PREREQUISITES,
            value=formation.contract_concluded_prerequisites,
            text_ru=(
                "Формальные предпосылки заключения договора подтверждены."
                if formation.contract_concluded_prerequisites
                else "Формальные предпосылки заключения договора подтверждены не полностью."
            ),
            source_refs=_formation_refs(
                result,
                *[item.fact_name for item in result.formation_evidence_mapping.provenance],
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.CONDUCT_ACCEPTANCE_VALID,
            value=formation.conduct_acceptance_valid,
            text_ru=(
                "Акцепт подтвержден своевременными действиями по исполнению."
                if formation.conduct_acceptance_valid
                else "Своевременный акцепт действиями не подтвержден."
            ),
            source_refs=_formation_refs(
                result,
                "acceptance_by_conduct",
                "performance_conduct_started_in_time",
                "acceptance_on_other_terms",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.COUNTEROFFER_DETECTED,
            value=formation.counteroffer_detected,
            text_ru=(
                "Выявлен ответ на иных условиях, требующий оценки как встречной оферты."
                if formation.counteroffer_detected
                else "Ответ на иных условиях не выявлен."
            ),
            source_refs=_formation_refs(result, "acceptance_on_other_terms"),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.NON_CONCLUSION_OBJECTION_BARRED,
            value=formation.non_conclusion_objection_barred,
            text_ru=(
                "Есть формальные предпосылки отклонить недобросовестное возражение о незаключенности."
                if formation.non_conclusion_objection_barred
                else "Формальный запрет возражения о незаключенности не установлен."
            ),
            source_refs=_formation_refs(
                result,
                "performance_accepted_without_objection",
                "bad_faith_non_conclusion_objection",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.TRANSACTION_PRESUMED_EFFECTIVE,
            value=invalidity.transaction_presumed_effective,
            text_ru=(
                "Обычные договорные последствия сделки текущей моделью не устранены."
                if invalidity.transaction_presumed_effective
                else "Действие обычных договорных последствий поставлено под вопрос."
            ),
            source_refs=_invalidity_refs(result, "transaction_concluded"),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.VOID_GROUND_DETECTED,
            value=invalidity.void_ground_detected,
            text_ru=(
                "Выявлено формальное основание ничтожности сделки."
                if invalidity.void_ground_detected
                else "Формальное основание ничтожности не выявлено."
            ),
            source_refs=_invalidity_refs(
                result,
                "violates_law",
                "public_interests_or_third_rights_affected",
                "law_expressly_makes_void",
                "immoral_purpose_proven",
                "sham_intent_proven",
                "feigned_intent_proven",
                "incapacitated_person_transaction",
                "minor_under_14_transaction",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.VOIDABLE_GROUND_DETECTED,
            value=invalidity.voidable_ground_detected,
            text_ru=(
                "Выявлено формальное основание оспоримости сделки."
                if invalidity.voidable_ground_detected
                else "Формальное основание оспоримости не выявлено."
            ),
            source_refs=_invalidity_refs(
                result,
                *[item.fact_name for item in result.invalidity_evidence_mapping.provenance],
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.VOIDABLE_INVALIDITY_EFFECTIVE,
            value=invalidity.voidable_invalidity_effective,
            text_ru=(
                "Оспоримая сделка признана недействительной вступившим в силу решением."
                if invalidity.voidable_invalidity_effective
                else "Вступивший в силу судебный эффект оспоримости не установлен."
            ),
            source_refs=_invalidity_refs(
                result,
                "invalidity_claim_made",
                "claimant_rights_or_interests_affected",
                "court_decision_entered_into_force",
                "voidable_limitation_period_expired",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.INVALIDITY_ESTOPPEL_BAR,
            value=invalidity.estoppel_bar,
            text_ru=(
                "Выявлен запрет противоречивой ссылки на недействительность."
                if invalidity.estoppel_bar
                else "Запрет противоречивой ссылки на недействительность не активирован."
            ),
            source_refs=_invalidity_refs(
                result,
                "good_faith_reliance_created",
                "party_confirmed_voidable_transaction",
                "ground_known_at_confirmation",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.PARTIAL_INVALIDITY_ONLY,
            value=invalidity.partial_invalidity_only,
            text_ru=(
                "Недействительность ограничена отделимой частью сделки."
                if invalidity.partial_invalidity_only
                else "Основание для сохранения сделки за вычетом отдельной части не установлено."
            ),
            source_refs=_invalidity_refs(
                result,
                "invalid_part_separable",
                "remainder_preserves_transaction_purpose",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DISGUISED_TRANSACTION_RULES,
            value=invalidity.disguised_transaction_rules_required,
            text_ru=(
                "Требуется применить правила об идентифицированной прикрываемой сделке."
                if invalidity.disguised_transaction_rules_required
                else "Идентифицированная прикрываемая сделка не установлена."
            ),
            source_refs=_invalidity_refs(
                result,
                "feigned_intent_proven",
                "disguised_transaction_identified",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.INVALIDITY_RESTITUTION_REQUIRED,
            value=invalidity.restitution_required,
            text_ru=(
                "Исполнение по недействительной сделке формирует реституционный вопрос."
                if invalidity.restitution_required
                else "Реституционный вопрос по текущим фактам не активирован."
            ),
            source_refs=_invalidity_refs(
                result,
                "party_a_performed",
                "party_b_performed",
                "return_in_kind_possible",
                "value_of_performance_proven",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SECURITY_MECHANISM_DETECTED,
            value=security.security_mechanism_detected,
            text_ru=(
                "В деле выявлен формально действующий способ обеспечения исполнения."
                if security.security_mechanism_detected
                else "Действующий способ обеспечения исполнения не подтвержден."
            ),
            source_refs=_security_refs(
                result,
                *[item.fact_name for item in result.security_evidence_mapping.provenance],
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SECURITY_ENFORCEMENT_AVAILABLE,
            value=security.security_enforcement_available,
            text_ru=(
                "Подтвержден как минимум один формальный маршрут реализации обеспечения."
                if security.security_enforcement_available
                else "Полный набор условий реализации обеспечения не подтвержден."
            ),
            source_refs=_security_refs(result, "main_obligation_breached", "secured_amount_proven"),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.PLEDGE_FORECLOSURE_PREREQUISITES,
            value=security.pledge_foreclosure_prerequisites,
            text_ru=(
                "Формальные предпосылки обращения взыскания на предмет залога подтверждены."
                if security.pledge_foreclosure_prerequisites
                else "Предпосылки обращения взыскания на предмет залога подтверждены не полностью."
            ),
            source_refs=_security_refs(
                result,
                "pledge_created",
                "pledged_asset_identified",
                "foreclosure_ground_exists",
                "breach_insignificant",
                "secured_claim_manifestly_disproportionate",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.RETENTION_AVAILABLE,
            value=security.retention_available,
            text_ru=(
                "Формальные условия удержания вещи подтверждены."
                if security.retention_available
                else "Формальные условия удержания вещи не подтверждены."
            ),
            source_refs=_security_refs(
                result,
                "asset_lawfully_in_creditor_possession",
                "asset_return_due",
                "retention_secured_claim_due",
                "claim_related_to_asset",
                "parties_acting_in_business",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SURETY_ENFORCEABLE,
            value=security.surety_enforceable,
            text_ru=(
                "Формальные условия требования к поручителю подтверждены."
                if security.surety_enforceable
                else "Требование к поручителю не прошло полный набор формальных условий."
            ),
            source_refs=_security_refs(
                result,
                "suretyship_created",
                "suretyship_writing_observed",
                "surety_scope_proven",
                "surety_term_expired",
                "debt_transferred",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.GUARANTEE_DEMAND_PAYABLE,
            value=security.guarantee_demand_payable,
            text_ru=(
                "Требование по независимой гарантии формально соответствует условиям выплаты."
                if security.guarantee_demand_payable
                else "Условия выплаты по независимой гарантии подтверждены не полностью."
            ),
            source_refs=_security_refs(
                result,
                "independent_guarantee_issued",
                "guarantee_demand_timely",
                "guarantee_demand_complies",
                "guarantee_expired",
                "beneficiary_abuse_proven",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DEPOSIT_PROVEN,
            value=security.deposit_proven,
            text_ru=(
                "Платеж формально квалифицирован как задаток."
                if security.deposit_proven
                else "Квалификация платежа как задатка не подтверждена; возможна квалификация аванса."
            ),
            source_refs=_security_refs(
                result,
                "payment_transferred_at_conclusion",
                "payment_identified_as_deposit_in_writing",
                "deposit_nature_doubtful",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SECURITY_PAYMENT_CREDIT_AVAILABLE,
            value=security.security_payment_credit_available,
            text_ru=(
                "Наступили формальные условия зачета обеспечительного платежа."
                if security.security_payment_credit_available
                else "Условия зачета обеспечительного платежа не подтверждены."
            ),
            source_refs=_security_refs(
                result,
                "security_payment_agreed",
                "security_payment_funded",
                "secured_circumstance_occurred",
                "security_payment_credited",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.ASSIGNMENT_EFFECTIVE,
            value=dynamics.assignment_effective,
            text_ru=(
                "Формальные условия перехода требования к новому кредитору подтверждены."
                if dynamics.assignment_effective
                else "Полный набор условий действительной уступки требования не подтвержден."
            ),
            source_refs=_dynamics_refs(
                result,
                "assignment_agreement_concluded",
                "assignment_form_observed",
                "assigned_claim_exists",
                "assigned_claim_identified",
                "future_claim_determinable",
                "claim_personal_to_creditor",
                "assignment_prohibited_by_law",
                "debtor_consent_required",
                "debtor_consent_obtained",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DEBT_TRANSFER_EFFECTIVE,
            value=dynamics.debt_transfer_effective,
            text_ru=(
                "Формальные условия перевода долга подтверждены."
                if dynamics.debt_transfer_effective
                else "Перевод долга с требуемым согласием кредитора не подтвержден."
            ),
            source_refs=_dynamics_refs(
                result,
                "debt_transfer_agreement_concluded",
                "debt_transfer_form_observed",
                "new_debtor_identified",
                "creditor_consented_debt_transfer",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.CONTRACT_TRANSFER_EFFECTIVE,
            value=dynamics.contract_transfer_effective,
            text_ru=(
                "Передача договора с согласованной заменой сторон формально подтверждена."
                if dynamics.contract_transfer_effective
                else "Передача договора с согласием всех сторон не подтверждена."
            ),
            source_refs=_dynamics_refs(
                result,
                "contract_transfer_agreed",
                "all_parties_consented_contract_transfer",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.PARTIES_CHANGED_NOT_DISCHARGED,
            value=dynamics.parties_changed_not_discharged,
            text_ru=(
                "Состав участников изменился, но само обязательство не прекратилось."
                if dynamics.parties_changed_not_discharged
                else "Перемена лица без прекращения обязательства не установлена."
            ),
            source_refs=_dynamics_refs(
                result,
                *[
                    item.fact_name
                    for item in result.obligation_dynamics_evidence_mapping.provenance
                ],
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.PROPER_PERFORMANCE_DISCHARGE,
            value=dynamics.proper_performance_discharge,
            text_ru=(
                "Основная обязанность прекращена надлежащим полным исполнением."
                if dynamics.proper_performance_discharge
                else "Полное прекращение надлежащим исполнением не подтверждено."
            ),
            source_refs=_dynamics_refs(
                result,
                "performance_rendered",
                "performance_accepted_as_proper",
                "performance_partial",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.ACCORD_DISCHARGE,
            value=dynamics.accord_discharge,
            text_ru=(
                "Первоначальное обязательство прекращено предоставленным отступным."
                if dynamics.accord_discharge
                else "Предоставление отступного, прекращающее первоначальный долг, не подтверждено."
            ),
            source_refs=_dynamics_refs(
                result,
                "accord_agreed",
                "accord_form_observed",
                "accord_performance_provided",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SETOFF_EFFECTIVE,
            value=dynamics.setoff_effective,
            text_ru=(
                "Встречные требования формально прекращены зачетом."
                if dynamics.setoff_effective
                else "Полный набор условий и доставленное заявление о зачете не подтверждены."
            ),
            source_refs=_dynamics_refs(
                result,
                "set_off_declared",
                "set_off_notice_delivered",
                "counterclaims_mutual",
                "counterclaims_homogeneous",
                "active_claim_due",
                "set_off_prohibited",
                "active_claim_limitation_expired",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.NOVATION_EFFECTIVE,
            value=dynamics.novation_effective,
            text_ru=(
                "Подтверждена ясная замена первоначального обязательства новым."
                if dynamics.novation_effective
                else "Формальные признаки новации не подтверждены полностью."
            ),
            source_refs=_dynamics_refs(
                result,
                "novation_agreed",
                "novation_intent_clear",
                "new_subject_or_basis",
                "new_obligation_terms_agreed",
                "novation_form_observed",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DEBT_FORGIVENESS_EFFECTIVE,
            value=dynamics.debt_forgiveness_effective,
            text_ru=(
                "Прощение долга формально прекратило обязательство."
                if dynamics.debt_forgiveness_effective
                else "Действующее прощение долга без возражений и нарушения чужих прав не подтверждено."
            ),
            source_refs=_dynamics_refs(
                result,
                "debt_forgiveness_declared",
                "debt_forgiveness_notice_delivered",
                "debtor_objected_forgiveness",
                "third_party_rights_prejudiced",
                "forgiveness_gift_intent",
                "commercial_parties",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.IMPOSSIBILITY_DISCHARGE,
            value=dynamics.impossibility_discharge,
            text_ru=(
                "Обязательство прекращено объективной постоянной невозможностью исполнения."
                if dynamics.impossibility_discharge
                else "Основание прекращения объективной невозможностью не подтверждено."
            ),
            source_refs=_dynamics_refs(
                result,
                "objective_permanent_impossibility",
                "impossibility_risk_on_debtor",
                "debtor_in_delay_at_impossibility",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.OBLIGATION_DISCHARGED_FULL,
            value=dynamics.obligation_discharged_full,
            text_ru=(
                "Выявлено формальное основание полного прекращения основной обязанности."
                if dynamics.obligation_discharged_full
                else "Полное прекращение основной обязанности не подтверждено."
            ),
            source_refs=_dynamics_refs(
                result,
                *[
                    item.fact_name
                    for item in result.obligation_dynamics_evidence_mapping.provenance
                ],
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DYNAMICS_ACCRUED_CLAIMS_PRESERVED,
            value=dynamics.accrued_claims_preserved,
            text_ru=(
                "Прекращение основной обязанности не устранило ранее возникшие требования из нарушения."
                if dynamics.accrued_claims_preserved
                else "Сохранение ранее возникших требований текущим путем прекращения не подтверждено."
            ),
            source_refs=_dynamics_refs(
                result,
                "obligation_breached",
                "accrued_claims_exist",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.PERFORMANCE_PROPER,
            value=performance_remedies.proper_performance,
            text_ru=(
                "Предмет, качество, количество, срок, место и получатель исполнения формально надлежащие."
                if performance_remedies.proper_performance
                else "Полный набор признаков надлежащего исполнения не подтвержден."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "performance_tendered",
                "subject_conforms",
                "quality_quantity_conform",
                "performance_at_due_time",
                "performance_at_proper_place",
                "performance_to_proper_recipient",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.PARTIAL_PERFORMANCE_ACCEPTANCE_REQUIRED,
            value=performance_remedies.partial_performance_acceptance_required,
            text_ru=(
                "Выявлено основание, обязывающее кредитора принять частичное исполнение."
                if performance_remedies.partial_performance_acceptance_required
                else "Обязанность кредитора принять частичное исполнение не подтверждена."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "partial_performance_tendered",
                "partial_performance_allowed",
                "monetary_obligation",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.THIRD_PARTY_PERFORMANCE_ACCEPTANCE_REQUIRED,
            value=performance_remedies.third_party_performance_acceptance_required,
            text_ru=(
                "Кредитор формально обязан принять предложенное третьим лицом исполнение."
                if performance_remedies.third_party_performance_acceptance_required
                else "Полный набор оснований обязательного принятия исполнения третьего лица не установлен."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "third_party_performance_tendered",
                "debtor_assigned_third_party_performance",
                "debtor_monetary_delay",
                "third_party_property_right_at_risk",
                "personal_performance_required",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SOLIDARY_OBLIGATION,
            value=performance_remedies.solidary_obligation,
            text_ru=(
                "Множественность должников формально квалифицирована как солидарная."
                if performance_remedies.solidary_obligation
                else "Законное или договорное основание солидарности не подтверждено."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "multiple_debtors",
                "solidarity_by_law_or_contract",
                "joint_business_obligation",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.COUNTERPERFORMANCE_SUSPENSION_AVAILABLE,
            value=performance_remedies.counterperformance_suspension_available,
            text_ru=(
                "Подтверждены формальные предпосылки приостановления встречного исполнения."
                if performance_remedies.counterperformance_suspension_available
                else "Предпосылки приостановления встречного исполнения подтверждены не полностью."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "reciprocal_obligations",
                "counterperformance_due",
                "counterparty_failed_due_performance",
                "clear_future_nonperformance",
                "suspension_notice_delivered",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.PERFORMANCE_DAMAGES_AVAILABLE,
            value=performance_remedies.damages_prerequisites_satisfied,
            text_ru=(
                "Подтверждены нарушение, потери, причинная связь и разумная основа размера убытков."
                if performance_remedies.damages_prerequisites_satisfied
                else "Формальные предпосылки взыскания убытков подтверждены не полностью."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "breach_established",
                "loss_claimed",
                "actual_loss_proven",
                "lost_profit_claimed",
                "causation_proven",
                "reasonable_amount_basis",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SPECIFIC_PERFORMANCE_AVAILABLE,
            value=performance_remedies.specific_performance_available,
            text_ru=(
                "Формальные предпосылки требования исполнения обязательства в натуре подтверждены."
                if performance_remedies.specific_performance_available
                else "Доступность исполнения в натуре не подтверждена полностью."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "specific_performance_claimed",
                "performance_objectively_possible",
                "creditor_lost_interest_due_delay",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.ARTICLE_395_INTEREST_AVAILABLE,
            value=performance_remedies.article_395_interest_available,
            text_ru=(
                "Подтверждены формальные предпосылки процентов по статье 395 ГК РФ."
                if performance_remedies.article_395_interest_available
                else "Проценты по статье 395 ГК РФ недоступны либо требуют дополнительных фактов."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "monetary_delay",
                "article_395_claimed",
                "penalty_for_same_monetary_delay",
                "article_395_contract_override",
                "statutory_rate_basis_proven",
                "interest_period_proven",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.CREDITOR_IN_DELAY,
            value=performance_remedies.creditor_in_delay,
            text_ru=(
                "Выявлены формальные признаки просрочки кредитора."
                if performance_remedies.creditor_in_delay
                else "Просрочка кредитора не подтверждена."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "creditor_refused_proper_performance",
                "creditor_omitted_required_action",
                "creditor_prerequisite_action_required",
                "creditor_prerequisite_action_completed",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.INDEMNITY_PREREQUISITES,
            value=performance_remedies.indemnity_prerequisites_satisfied,
            text_ru=(
                "Подтверждены формальные предпосылки предпринимательского возмещения потерь."
                if performance_remedies.indemnity_prerequisites_satisfied
                else "Предпосылки возмещения потерь по статье 406.1 ГК РФ подтверждены не полностью."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "indemnity_agreement",
                "indemnity_business_context",
                "indemnity_clear",
                "indemnity_trigger_unrelated_to_breach",
                "indemnity_loss_occurred",
                "indemnity_amount_or_method_agreed",
                "indemnity_bad_faith_event_caused",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.INTENTIONAL_LIABILITY_EXCLUSION_INVALID,
            value=performance_remedies.intentional_liability_exclusion_invalid,
            text_ru=(
                "Заранее установленное исключение ответственности за умышленное нарушение формально недействительно."
                if performance_remedies.intentional_liability_exclusion_invalid
                else "Недействительное исключение ответственности за умышленное нарушение не выявлено."
            ),
            source_refs=_performance_remedies_refs(
                result,
                "intentional_breach",
                "liability_limit_clause_or_law",
                "advance_intentional_liability_exclusion",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SALE_CONTRACT_QUALIFIED,
            value=sale.sale_contract_qualified,
            text_ru=(
                "Подтверждены формальные признаки договора купли-продажи по статье 454 ГК РФ."
                if sale.sale_contract_qualified
                else "Полный набор формальных признаков договора купли-продажи не подтвержден."
            ),
            source_refs=_sale_refs(
                result,
                "contract_concluded",
                "seller_transfer_ownership_duty",
                "buyer_acceptance_duty",
                "buyer_payment_duty",
                "goods_existing_or_future",
                "goods_name_agreed",
                "quantity_determinable",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SALE_TRANSFER_DUTY_PERFORMED,
            value=sale.transfer_duty_performed,
            text_ru=(
                "Передача товара формально исполнена с учетом применимого способа вручения."
                if sale.transfer_duty_performed
                else "Надлежащее исполнение обязанности передать товар подтверждено не полностью."
            ),
            source_refs=_sale_refs(
                result,
                "goods_transfer_completed",
                "delivery_obligation",
                "goods_delivered_to_buyer",
                "goods_made_available",
                "shipment_contract",
                "goods_handed_to_carrier",
                "accessories_required",
                "accessories_transferred",
                "documents_required",
                "documents_transferred",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SALE_THIRD_PARTY_OR_EVICTION_ISSUE,
            value=(
                sale.third_party_rights_breach
                or sale.eviction_loss_remedy_available
                or sale.buyer_eviction_procedure_gap
            ),
            text_ru=(
                "Выявлен вопрос о правах третьих лиц, эвикции или процессуальном участии продавца."
                if (
                    sale.third_party_rights_breach
                    or sale.eviction_loss_remedy_available
                    or sale.buyer_eviction_procedure_gap
                )
                else "Проблема прав третьих лиц или эвикции текущими фактами не подтверждена."
            ),
            source_refs=_sale_refs(
                result,
                "third_party_rights_exist",
                "buyer_consented_third_party_rights",
                "goods_withdrawn_by_third_party",
                "withdrawal_ground_predates_transfer",
                "buyer_knew_withdrawal_ground",
                "third_party_eviction_claim_filed",
                "buyer_joined_seller_to_eviction_case",
                "loss_claimed",
                "causation_proven",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SALE_QUALITY_REMEDIES_AVAILABLE,
            value=(sale.quality_remedies_available or sale.material_defect_remedies_available),
            text_ru=(
                "Подтверждены формальные предпосылки требований покупателя из недостатков товара."
                if (sale.quality_remedies_available or sale.material_defect_remedies_available)
                else "Средства защиты из недостатков товара текущими фактами не активированы."
            ),
            source_refs=_sale_refs(
                result,
                "quality_defect",
                "defect_material",
                "seller_warranty_given",
                "warranty_period_active",
                "buyer_proved_pretransfer_defect_cause",
                "seller_proved_posttransfer_defect_cause",
                "defect_discovered_within_applicable_period",
                "buyer_chose_price_reduction",
                "buyer_chose_free_repair",
                "buyer_chose_repair_costs",
                "buyer_chose_replacement",
                "buyer_chose_contract_refusal_for_defect",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SALE_PAYMENT_DEFAULT,
            value=(sale.payment_default or sale.prepayment_default or sale.credit_payment_default),
            text_ru=(
                "Выявлена просрочка оплаты, предварительной оплаты или платежа за товар в кредит."
                if (sale.payment_default or sale.prepayment_default or sale.credit_payment_default)
                else "Просрочка оплаты по общим правилам купли-продажи не подтверждена."
            ),
            source_refs=_sale_refs(
                result,
                "payment_due",
                "buyer_paid",
                "prepayment_required",
                "prepayment_due",
                "prepayment_made",
                "credit_sale",
                "credit_payment_due",
                "credit_payment_made",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SALE_TITLE_RETENTION_REMEDY,
            value=sale.title_return_remedy,
            text_ru=(
                "Подтверждена формальная предпосылка требования вернуть товар при сохранении права собственности."
                if sale.title_return_remedy
                else "Требование о возврате товара из сохранения права собственности не активировано."
            ),
            source_refs=_sale_refs(
                result,
                "title_retention_agreed",
                "title_condition_met",
                "buyer_disposed_before_title",
                "title_early_disposal_permitted",
                "seller_required_goods_return",
                "title_return_contract_bar",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SUPPLY_CONTRACT_QUALIFIED,
            value=supply.supply_contract_qualified,
            text_ru=(
                "Отношения формально квалифицированы как договор поставки по статье 506 ГК РФ."
                if supply.supply_contract_qualified
                else "Полный набор квалифицирующих признаков договора поставки не подтвержден."
            ),
            source_refs=_supply_refs(
                result,
                "contract_concluded",
                "supplier_business",
                "supplier_produced_or_procured_goods",
                "goods_nonpersonal_use",
                "retail_sale_context",
                "transfer_term_defined",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SUPPLY_ACCEPTANCE_DUTIES_SATISFIED,
            value=supply.acceptance_duties_satisfied,
            text_ru=(
                "Проверка товара и письменное извещение соответствуют формальной модели приемки."
                if supply.acceptance_duties_satisfied
                else "Исполнение обязанностей по приемке и извещению подтверждено не полностью."
            ),
            source_refs=_supply_refs(
                result,
                "buyer_received_goods",
                "inspection_timely",
                "discrepancy_found",
                "prompt_written_notice",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SUPPLY_MAKEUP_DELIVERY_REQUIRED,
            value=supply.makeup_delivery_required,
            text_ru=(
                "Недопоставка подлежит восполнению в пределах срока договора."
                if supply.makeup_delivery_required
                else "Специальная обязанность восполнить недопоставку текущими фактами не активирована."
            ),
            source_refs=_supply_refs(
                result,
                "quantity_shortfall",
                "contract_term_continues",
                "buyer_refused_late_makeup_by_notice",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SUPPLY_UNILATERAL_REFUSAL_EFFECTIVE,
            value=supply.supply_unilateral_refusal_effective,
            text_ru=(
                "Подтверждены специальные предпосылки одностороннего отказа по статье 523 ГК РФ."
                if supply.supply_unilateral_refusal_effective
                else "Специальный односторонний отказ по статье 523 ГК РФ не подтвержден."
            ),
            source_refs=_supply_refs(
                result,
                "repeated_late_delivery",
                "irremediable_defect",
                "repeated_payment_default",
                "repeated_selection_failure",
                "unilateral_refusal_notice_delivered",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.SUPPLY_PRICE_DAMAGES_AVAILABLE,
            value=(
                supply.concrete_price_damages_available
                or supply.abstract_current_price_damages_available
            ),
            text_ru=(
                "Подтвержден специальный ценовой расчет убытков после прекращения поставки."
                if (
                    supply.concrete_price_damages_available
                    or supply.abstract_current_price_damages_available
                )
                else "Специальный расчет убытков по статье 524 ГК РФ подтвержден не полностью."
            ),
            source_refs=_supply_refs(
                result,
                "contract_terminated",
                "replacement_transaction_made",
                "replacement_transaction_reasonable",
                "replacement_transaction_timely",
                "contract_price_proven",
                "replacement_price_proven",
                "current_price_available",
                "current_price_proven",
                "current_price_time_place_adjusted",
                "loss_claimed",
                "causation_proven",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.CONTRACT_CONTINUES_UNCHANGED,
            value=termination.contract_continues_unchanged,
            text_ru=(
                "Договор продолжает действовать без подтвержденного изменения."
                if termination.contract_continues_unchanged
                else "Неизменное продолжение договора текущей моделью не подтверждено."
            ),
            source_refs=_termination_refs(
                result,
                "contract_formed",
                "mutual_agreement_reached",
                "judicial_request_made",
                "unilateral_action_declared",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.EFFECTIVE_MODIFICATION,
            value=termination.effective_modification,
            text_ru=(
                "Установлен формальный путь вступившего в силу изменения договора."
                if termination.effective_modification
                else "Вступившее в силу изменение договора не установлено."
            ),
            source_refs=_termination_refs(
                result,
                *[item.fact_name for item in result.termination_evidence_mapping.provenance],
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.EFFECTIVE_TERMINATION,
            value=termination.effective_termination,
            text_ru=(
                "Установлен формальный путь состоявшегося прекращения договора."
                if termination.effective_termination
                else "Состоявшееся прекращение договора не установлено."
            ),
            source_refs=_termination_refs(
                result,
                *[item.fact_name for item in result.termination_evidence_mapping.provenance],
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.JUDICIAL_TERMINATION_PREREQUISITES,
            value=termination.judicial_termination_prerequisites,
            text_ru=(
                "Формальные предпосылки судебного требования о расторжении подтверждены."
                if termination.judicial_termination_prerequisites
                else "Полный набор предпосылок судебного требования о расторжении не подтвержден."
            ),
            source_refs=_termination_refs(
                result,
                "judicial_request_made",
                "substantial_breach_proven",
                "expectation_deprivation_proven",
                "other_legal_or_contractual_ground_proven",
                "pretrial_proposal_delivered",
                "pretrial_refusal_received",
                "pretrial_response_period_expired",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.CHANGED_CIRCUMSTANCES_GROUND,
            value=termination.changed_circumstances_ground_satisfied,
            text_ru=(
                "Формальные предпосылки существенного изменения обстоятельств подтверждены."
                if termination.changed_circumstances_ground_satisfied
                else "Полный набор предпосылок статьи 451 ГК РФ не подтвержден."
            ),
            source_refs=_termination_refs(
                result,
                "circumstances_substantially_changed",
                "change_unforeseeable_at_conclusion",
                "causes_not_overcome_with_due_care",
                "continued_performance_upsets_balance",
                "changed_circumstances_risk_not_assumed",
                "adjustment_negotiations_failed",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.INVALID_UNILATERAL_ACTION,
            value=termination.invalid_unilateral_action,
            text_ru=(
                "Одностороннее действие не прошло формальную проверку правомерности."
                if termination.invalid_unilateral_action
                else "Неправомерное одностороннее изменение или прекращение не выявлено."
            ),
            source_refs=_termination_refs(
                result,
                "unilateral_action_declared",
                "unilateral_right_exists",
                "unilateral_notice_delivered",
                "unilateral_requirements_observed",
                "unilateral_exercise_good_faith",
                "same_ground_previously_waived",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.ACCRUED_CLAIMS_PRESERVED,
            value=termination.accrued_claims_preserved,
            text_ru=(
                "Ранее возникшие требования сохранены после прекращения договора."
                if termination.accrued_claims_preserved
                else "Сохранение ранее возникших требований не активировано без прекращения договора."
            ),
            source_refs=_termination_refs(result, "accrued_claims_exist"),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DUE_DATE_MISSED,
            value=result.temporal_evaluation.due_date_missed,
            text_ru=result.temporal_evaluation.reasons_ru[0],
            source_refs=_provenance_refs(result, "due_date_missed"),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.BREACH_ISSUE,
            value=evaluation.breach_issue,
            text_ru=(
                "Формальная модель выявила вопрос о нарушении обязательства."
                if evaluation.breach_issue
                else "Формальная модель не выявила нарушения обязательства."
            ),
            source_refs=_provenance_refs(
                result,
                "duty_exists",
                "due_date_missed",
                "valid_exception_applies",
                "performance_completed",
                "performance_nonconforming",
                "payment_duty_exists",
                "payment_due",
                "payment_missed",
                "payment_defense_applies",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.LATE_PERFORMANCE_ISSUE,
            value=evaluation.late_performance_issue,
            text_ru=(
                "Установлены формальные признаки просрочки исполнения."
                if evaluation.late_performance_issue
                else "Формальные признаки просрочки исполнения не установлены."
            ),
            source_refs=_provenance_refs(
                result,
                "duty_exists",
                "due_date_missed",
                "valid_exception_applies",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DEFECT_ISSUE,
            value=evaluation.defect_issue,
            text_ru=(
                "Установлены формальные признаки ненадлежащего исполнения."
                if evaluation.defect_issue
                else "Формальные признаки ненадлежащего исполнения не установлены."
            ),
            source_refs=_provenance_refs(
                result,
                "duty_exists",
                "performance_completed",
                "performance_nonconforming",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.PAYMENT_DEFAULT_ISSUE,
            value=evaluation.payment_default_issue,
            text_ru=(
                "Установлены формальные признаки просрочки платежа."
                if evaluation.payment_default_issue
                else "Формальные признаки просрочки платежа не установлены."
            ),
            source_refs=_provenance_refs(
                result,
                "payment_duty_exists",
                "payment_due",
                "payment_missed",
                "payment_defense_applies",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DAMAGES_REMEDY_AVAILABLE,
            value=evaluation.damages_remedy_available,
            text_ru=(
                "Формальные предпосылки требования убытков установлены."
                if evaluation.damages_remedy_available
                else "Текущий набор фактов не подтверждает все формальные предпосылки требования убытков."
            ),
            source_refs=_provenance_refs(
                result,
                "loss_claimed",
                "causation_established",
                "remedy_requested",
                "limitation_period_expired",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.CAUSATION_EVIDENCE_GAP,
            value=evaluation.causation_evidence_gap,
            text_ru=(
                "Выявлен пробел в доказательствах причинной связи."
                if evaluation.causation_evidence_gap
                else "Формальный пробел причинной связи для заявленного требования не выявлен."
            ),
            source_refs=_provenance_refs(
                result,
                "loss_claimed",
                "causation_established",
                "remedy_requested",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.LIMITATION_BAR,
            value=evaluation.limitation_bar,
            text_ru=(
                "Установлен формальный барьер исковой давности."
                if evaluation.limitation_bar
                else "Формальный барьер исковой давности не установлен."
            ),
            source_refs=_provenance_refs(
                result,
                "remedy_requested",
                "limitation_period_expired",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.AUTHORITY_WINNER,
            value=authority.selected_source_id or "human_resolution_required",
            text_ru=(
                f"По модели юридической силы выбран источник {authority.selected_source_id}."
                if authority.selected_source_id
                else "Модель юридической силы не выбрала единственный источник."
            ),
            source_refs=authority_refs,
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.HUMAN_RESOLUTION_REQUIRED,
            value=result.requires_human_resolution,
            text_ru=(
                "Для разрешения вопроса об источниках или заключении договора требуется решение эксперта."
                if result.requires_human_resolution
                else "Вопросы источников и формальных предпосылок заключения разрешены текущей синтетической моделью."
            ),
            source_refs=authority_refs,
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.COUNTERFACTUAL_SENSITIVITY,
            value=(
                critical_scenario.operator_code.value
                if critical_scenario
                else "no_material_sensitivity"
            ),
            text_ru=(
                "Минимальная гипотеза чувствительности «"
                f"{critical_scenario.title_ru}» изменяет формальный результат."
                if critical_scenario
                else "В пределах бюджета материальная контрфактическая чувствительность не выявлена."
            ),
            source_refs=[],
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.FAULT_REBUTTED,
            value=liability.fault_rebutted,
            text_ru=(
                "Формальные предпосылки опровержения вины подтверждены."
                if liability.fault_rebutted
                else "Формальные предпосылки опровержения вины не подтверждены."
            ),
            source_refs=_liability_refs(
                result,
                "fault_rebuttal_asserted",
                "reasonable_care_proven",
                "all_reasonable_measures_proven",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.FORCE_MAJEURE_QUALIFIED,
            value=liability.force_majeure_qualified,
            text_ru=(
                "Формальные признаки непреодолимой силы подтверждены."
                if liability.force_majeure_qualified
                else "Полный набор формальных признаков непреодолимой силы не подтвержден."
            ),
            source_refs=_liability_refs(
                result,
                "force_majeure_claimed",
                "extraordinary_event_proven",
                "unavoidable_event_proven",
                "beyond_debtor_control_proven",
                "force_majeure_causal_link_proven",
                "excluded_commercial_risk_only",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.LIABILITY_EXEMPTION_PREREQUISITES,
            value=liability.exemption_prerequisites_satisfied,
            text_ru=(
                "Формальные предпосылки освобождения от ответственности подтверждены."
                if liability.exemption_prerequisites_satisfied
                else "Формальные предпосылки освобождения от ответственности не подтверждены."
            ),
            source_refs=_liability_refs(
                result, *[item.fact_name for item in result.liability_evidence_mapping.provenance]
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.LIABILITY_ISSUE,
            value=liability.liability_issue,
            text_ru=(
                "Формальная модель сохраняет вопрос об ответственности за нарушение."
                if liability.liability_issue
                else "Текущая формальная модель не сохраняет вопрос об ответственности."
            ),
            source_refs=_liability_refs(result, "breach_established"),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.PENALTY_REDUCTION_PREREQUISITES,
            value=liability.penalty_reduction_prerequisites_satisfied,
            text_ru=(
                "Формальные предпосылки постановки вопроса о снижении неустойки подтверждены."
                if liability.penalty_reduction_prerequisites_satisfied
                else "Полный набор формальных предпосылок снижения неустойки не подтвержден."
            ),
            source_refs=_liability_refs(
                result,
                "penalty_claimed",
                "contractual_penalty",
                "penalty_reduction_requested",
                "manifest_disproportionality_proven",
                "unjustified_benefit_risk_proven",
                "only_excluded_reduction_reasons",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.INTENTIONAL_EXCLUSION_INVALID,
            value=liability.intentional_exclusion_invalid,
            text_ru=(
                "Выявлена недопустимая оговорка об исключении умышленной ответственности."
                if liability.intentional_exclusion_invalid
                else "Недопустимая оговорка об исключении умышленной ответственности не выявлена."
            ),
            source_refs=_liability_refs(
                result,
                "intentional_breach",
                "advance_liability_exclusion_clause",
            ),
        ),
    ]
    return assertions


def build_reasoning_path_comparison(
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
) -> ReasoningPathComparison:
    return ReasoningPathComparison(
        id=f"path-comparison:{request.case_id}:active-vs-shortcut",
        active_path_ru=[
            "Проверить временную применимость источников.",
            "Разрешить юридическую силу источников-кандидатов.",
            "Преобразовать только проверенные факты в формальные предикаты.",
            "Проверить оферту, существенные условия, форму и способ акцепта.",
            "Проверить обязанность, срок и применимое исключение в constraint set.",
            "Разделить соглашение, судебный путь и односторонний отказ при проверке прекращения.",
        ],
        alternative_path_ru=[
            "Считать любую просрочку нарушением без проверки источника и исключений.",
        ],
        material_differences_ru=[
            "Альтернативный путь не сохраняет provenance фактов.",
            "Альтернативный путь не проверяет применимость и юридическую силу источника.",
            "Альтернативный путь способен необоснованно исключить основание освобождения.",
            "Альтернативный путь способен принять заявление об отказе за состоявшееся расторжение.",
        ],
        selected_path="active_reviewed_path",
        selection_reason_ru=(
            "Выбран воспроизводимый путь с проверенными входами; shortcut отклонен "
            f"независимо от совпадения итогового breach_issue={evaluation_value(result)}."
        ),
    )


def evaluation_value(result: ReviewedContractAnalysisResult) -> str:
    return _yes_no(result.constraint_evaluation.breach_issue)


def _assertion_map(assertions: list[TranslationAssertion]) -> dict[str, TranslationAssertion]:
    return {assertion.code.value: assertion for assertion in assertions}


def _render_context(
    trace_id: str,
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
    governance: GovernanceRecord,
    policy_snapshot: PolicySnapshot,
    assertions: list[TranslationAssertion],
    comparison: ReasoningPathComparison,
    template_set: TranslationTemplateSet,
) -> dict[str, str]:
    by_code = _assertion_map(assertions)
    evaluation = result.constraint_evaluation
    conclusion_ru = by_code[TranslationAssertionCode.BREACH_ISSUE.value].text_ru
    if evaluation.late_performance_issue:
        conclusion_ru += " Основной выявленный паттерн — просрочка поставки."
    key_basis_ru = " ".join(
        [
            by_code[TranslationAssertionCode.DUE_DATE_MISSED.value].text_ru,
            by_code[TranslationAssertionCode.AUTHORITY_WINNER.value].text_ru,
        ]
    )
    risk_and_next_step_ru = (
        "Содержательная квалификация, расчет последствий и выбор способа защиты "
        "остаются за юристом; необходимо проверить первичные документы и актуальные источники."
    )
    facts_ru = "\n".join(
        [
            f"- Согласованный срок: {result.temporal_facts.agreed_due_date}.",
            f"- Фактическое исполнение: {result.temporal_facts.actual_performance_date}.",
            f"- Дата оценки: {result.temporal_facts.evaluation_date}.",
            f"- Срок пропущен: {_yes_no(result.temporal_evaluation.due_date_missed)}.",
            f"- Применимое исключение: {_yes_no(result.evidence_mapping.facts.valid_exception_applies)}.",
        ]
    )
    rule_and_authority_ru = "\n".join(
        [
            f"- Норма: {request.reviewed_norm.id}; действие: {result.formal_translation.obligation_rule.action}.",
            f"- Источник нормы: {request.reviewed_norm.source_id}.",
            *[f"- {reason}" for reason in result.authority_evaluation.reasons_ru],
        ]
    )
    formal_result_ru = "\n".join(f"- {assertion.text_ru}" for assertion in assertions[:9])
    limitations_ru = "\n".join(f"- {warning}" for warning in result.warnings_ru)
    coordinates_ru = "\n".join(
        [
            f"- Trace: {trace_id}.",
            f"- Дело: {request.case_id}.",
            f"- Analysis pipeline: {result.pipeline_version}.",
            f"- Policy snapshot: {policy_snapshot.id}.",
            f"- Policy hash: {policy_snapshot.content_hash}.",
            f"- Translation template: {template_set.version}.",
            f"- Translation template hash: {template_set.content_hash}.",
        ]
    )
    provenance_ru = "\n".join(
        (
            f"- {item.fact_name}: assertion={item.assertion_id}; "
            f"sources={', '.join(item.source_refs) or 'нет'}; "
            f"formal_atoms={', '.join(item.formal_atom_refs) or 'нет'}."
        )
        for item in result.evidence_mapping.provenance
    )
    formal_rule_ru = "\n".join(
        [
            f"- Formal rule: {result.formal_translation.obligation_rule.id}.",
            f"- Constraint set: {result.constraint_set.id}.",
            *[f"- {expression}." for expression in result.constraint_set.expressions],
        ]
    )
    authority_trace_ru = "\n".join(
        [
            f"- Кандидаты: {', '.join(result.authority_evaluation.candidate_source_ids)}.",
            f"- Исключены: {', '.join(result.authority_evaluation.excluded_source_ids) or 'нет'}.",
            *[f"- {reason}" for reason in result.authority_evaluation.reasons_ru],
        ]
    )
    all_assertions_ru = "\n".join(
        (
            f"- {assertion.code.value}={assertion.value}: {assertion.text_ru}\n"
            f"  Источники: {', '.join(assertion.source_refs) or 'нет'}."
        )
        for assertion in assertions
    )
    governance_ru = "\n".join(
        (
            f"- {decision.from_stage_label_ru} → {decision.to_stage_label_ru}: "
            f"{' '.join(decision.reasons_ru)} [policy={decision.policy_version}; "
            f"hash={decision.policy_content_hash}]"
        )
        for decision in governance.decisions
    )
    path_comparison_ru = "\n".join(
        [
            *[f"- Активный путь: {step}" for step in comparison.active_path_ru],
            *[f"- Отклоненный путь: {step}" for step in comparison.alternative_path_ru],
            *[f"- Различие: {item}" for item in comparison.material_differences_ru],
            f"- Причина выбора: {comparison.selection_reason_ru}",
        ]
    )
    counterfactual_report = result.counterfactual_sensitivity
    critical_scenarios = [
        scenario
        for scenario_id in counterfactual_report.critical_scenario_ids
        for scenario in counterfactual_report.scenarios
        if scenario.id == scenario_id
    ]
    counterfactual_professional_ru = (
        "\n".join(
            (
                f"- {scenario.title_ru}: меняются выводы — "
                + ", ".join(delta.field_label_ru for delta in scenario.outcome_deltas)
                + "."
            )
            for scenario in critical_scenarios[:3]
        )
        or "- В пределах установленного бюджета материальные изменения не выявлены."
    )
    counterfactual_forensic_ru = "\n".join(
        [
            f"- Engine: {counterfactual_report.engine_version}.",
            f"- Operator library: {counterfactual_report.operator_library_version}.",
            f"- Operator library hash: {counterfactual_report.operator_library_hash}.",
            f"- Baseline fact hash: {counterfactual_report.baseline_fact_hash}.",
            f"- Budget: scenarios={counterfactual_report.budget.max_scenarios}; "
            f"changed_facts={counterfactual_report.budget.max_changed_facts_per_scenario}.",
            *[
                (
                    f"- {scenario.operator_code.value}: факты ["
                    + "; ".join(
                        f"{delta.field_name}={delta.before}->{delta.after}"
                        for delta in scenario.fact_deltas
                    )
                    + "]; выводы ["
                    + "; ".join(
                        f"{delta.field_name}={delta.before}->{delta.after}"
                        for delta in scenario.outcome_deltas
                    )
                    + f"]; hypothetical_hash={scenario.hypothetical_fact_hash}."
                )
                for scenario in counterfactual_report.scenarios
            ],
            f"- {counterfactual_report.disclaimer_ru}",
        ]
    )
    liability = result.liability_evaluation
    formation = result.formation_evaluation
    invalidity = result.invalidity_evaluation
    security = result.security_evaluation
    dynamics = result.obligation_dynamics_evaluation
    performance_remedies = result.performance_remedies_evaluation
    sale = result.sale_evaluation
    supply = result.supply_evaluation
    termination = result.termination_evaluation
    formation_professional_ru = "\n".join(
        [
            *[f"- {reason}" for reason in formation.reasons_ru],
            "- Судебная квалификация переписки, поведения сторон и формы договора остается за юристом.",
        ]
    )
    formation_forensic_ru = "\n".join(
        [
            f"- Constraint set: {result.formation_constraint_set.id}.",
            f"- Model version: {result.formation_constraint_set.model_version}.",
            f"- Evidence mapping: {result.formation_evidence_mapping.mapping_version}.",
            f"- Legal sources: {', '.join(result.formation_evidence_mapping.legal_source_refs)}.",
            *[
                f"- Rule: {expression}."
                for expression in result.formation_constraint_set.expressions
            ],
            *[
                f"- Fact {item.fact_name}: assertion={item.assertion_id}; "
                f"sources={', '.join(item.source_refs)}."
                for item in result.formation_evidence_mapping.provenance
            ],
            *[f"- Результат: {reason}" for reason in formation.reasons_ru],
            *[f"- Ограничение: {warning}" for warning in formation.warnings_ru],
        ]
    )
    invalidity_professional_ru = "\n".join(
        [
            *[f"- {reason}" for reason in invalidity.reasons_ru],
            "- Ничтожность и оспоримость имеют разные основания, заявителей и момент эффекта.",
            "- Реституция, убытки и судьба отделимой части требуют самостоятельной оценки.",
        ]
    )
    invalidity_forensic_ru = "\n".join(
        [
            f"- Набор ограничений: {result.invalidity_constraint_set.id}.",
            f"- Версия модели: {result.invalidity_constraint_set.model_version}.",
            f"- Отображение доказательств: {result.invalidity_evidence_mapping.mapping_version}.",
            f"- Правовые источники: {', '.join(result.invalidity_evidence_mapping.legal_source_refs)}.",
            *[
                f"- Правило: {expression}."
                for expression in result.invalidity_constraint_set.expressions
            ],
            *[
                f"- Факт {item.fact_name}: assertion={item.assertion_id}; "
                f"источники={', '.join(item.source_refs)}."
                for item in result.invalidity_evidence_mapping.provenance
            ],
            *[f"- Результат: {reason}" for reason in invalidity.reasons_ru],
            *[f"- Ограничение: {warning}" for warning in invalidity.warnings_ru],
        ]
    )
    security_professional_ru = "\n".join(
        [
            *[f"- {reason}" for reason in security.reasons_ru],
            "- Неустойка, залог, удержание, поручительство, независимая гарантия, задаток и обеспечительный платеж проверены раздельно.",
            "- Стоимость обеспечения, добросовестность и процессуальный порядок реализации требуют оценки юриста.",
        ]
    )
    security_forensic_ru = "\n".join(
        [
            f"- Набор ограничений: {result.security_constraint_set.id}.",
            f"- Версия модели: {result.security_constraint_set.model_version}.",
            f"- Отображение доказательств: {result.security_evidence_mapping.mapping_version}.",
            f"- Правовые источники: {', '.join(result.security_evidence_mapping.legal_source_refs)}.",
            *[
                f"- Правило формальной модели обеспечения: {expression}."
                for expression in result.security_constraint_set.expressions
            ],
            *[
                f"- Проверенный факт {item.fact_name}: исходное утверждение="
                f"{item.assertion_id}; доказательственные источники="
                f"{', '.join(item.source_refs)}."
                for item in result.security_evidence_mapping.provenance
            ],
            *[f"- Результат: {reason}" for reason in security.reasons_ru],
            *[f"- Ограничение: {warning}" for warning in security.warnings_ru],
        ]
    )
    dynamics_professional_ru = "\n".join(
        [
            *[f"- {reason}" for reason in dynamics.reasons_ru],
            "- Уступка, перевод долга и передача договора меняют участников, но сами по себе не прекращают обязательство.",
            "- Исполнение, отступное, зачет, новация, прощение долга и объективные основания прекращения проверены раздельно.",
            "- Размер остатка, толкование соглашений и специальные последствия требуют оценки юриста.",
        ]
    )
    dynamics_forensic_ru = "\n".join(
        [
            f"- Набор ограничений: {result.obligation_dynamics_constraint_set.id}.",
            f"- Версия модели: {result.obligation_dynamics_constraint_set.model_version}.",
            f"- Отображение доказательств: {result.obligation_dynamics_evidence_mapping.mapping_version}.",
            f"- Правовые источники: {', '.join(result.obligation_dynamics_evidence_mapping.legal_source_refs)}.",
            *[
                f"- Правило формальной модели динамики обязательства: {expression}."
                for expression in result.obligation_dynamics_constraint_set.expressions
            ],
            *[
                f"- Проверенный факт {item.fact_name}: исходное утверждение="
                f"{item.assertion_id}; доказательственные источники="
                f"{', '.join(item.source_refs)}."
                for item in result.obligation_dynamics_evidence_mapping.provenance
            ],
            *[f"- Результат: {reason}" for reason in dynamics.reasons_ru],
            *[f"- Ограничение: {warning}" for warning in dynamics.warnings_ru],
        ]
    )
    performance_remedies_professional_ru = "\n".join(
        [
            *[f"- {reason}" for reason in performance_remedies.reasons_ru],
            "- Надлежащее, частичное, досрочное, третьелицевое и встречное исполнение проверены раздельно.",
            "- Убытки, проценты, исполнение в натуре, просрочка сторон и возмещение потерь не взаимозаменяемы.",
            "- Размер денежных требований, разумность расходов и причинная связь требуют оценки доказательств юристом.",
        ]
    )
    performance_remedies_forensic_ru = "\n".join(
        [
            f"- Набор ограничений: {result.performance_remedies_constraint_set.id}.",
            f"- Версия модели: {result.performance_remedies_constraint_set.model_version}.",
            f"- Отображение доказательств: {result.performance_remedies_evidence_mapping.mapping_version}.",
            f"- Правовые источники: {', '.join(result.performance_remedies_evidence_mapping.legal_source_refs)}.",
            *[
                f"- Правило модели исполнения и средств защиты: {expression}."
                for expression in result.performance_remedies_constraint_set.expressions
            ],
            *[
                f"- Проверенный факт {item.fact_name}: исходное утверждение="
                f"{item.assertion_id}; доказательственные источники="
                f"{', '.join(item.source_refs)}."
                for item in result.performance_remedies_evidence_mapping.provenance
            ],
            *[f"- Результат: {reason}" for reason in performance_remedies.reasons_ru],
            *[f"- Ограничение: {warning}" for warning in performance_remedies.warnings_ru],
        ]
    )
    sale_professional_ru = "\n".join(
        [
            *[f"- {reason}" for reason in sale.reasons_ru],
            "- Предмет, передача, риск, права третьих лиц, количество, ассортимент, качество, комплектность, упаковка, приемка и оплата проверены раздельно.",
            "- Для поставки общие правила купли-продажи действуют постольку, поскольку специальные нормы не устанавливают иное.",
            "- Существенность недостатка, разумность срока, причинная связь и выбор средства защиты требуют оценки юриста.",
        ]
    )
    sale_forensic_ru = "\n".join(
        [
            f"- Набор ограничений: {result.sale_constraint_set.id}.",
            f"- Версия модели: {result.sale_constraint_set.model_version}.",
            f"- Отображение доказательств: {result.sale_evidence_mapping.mapping_version}.",
            f"- Правовые источники: {', '.join(result.sale_evidence_mapping.legal_source_refs)}.",
            *[
                f"- Правило общей модели купли-продажи: {expression}."
                for expression in result.sale_constraint_set.expressions
            ],
            *[
                f"- Проверенный факт {item.fact_name}: исходное утверждение="
                f"{item.assertion_id}; доказательственные источники="
                f"{', '.join(item.source_refs)}."
                for item in result.sale_evidence_mapping.provenance
            ],
            *[f"- Результат: {reason}" for reason in sale.reasons_ru],
            *[f"- Ограничение: {warning}" for warning in sale.warnings_ru],
        ]
    )
    supply_professional_ru = "\n".join(
        [
            *[f"- {reason}" for reason in supply.reasons_ru],
            "- Квалификация, периоды и порядок поставки, приемка, недопоставка, качество, комплектность и тара проверены раздельно.",
            "- Односторонний отказ и ценовые убытки требуют доказательств повторности, существенности, доставки уведомления и рыночной цены.",
            "- Инструкции П-6 и П-7 применяются как порядок приемки только при договорной отсылке.",
        ]
    )
    supply_forensic_ru = "\n".join(
        [
            f"- Набор ограничений: {result.supply_constraint_set.id}.",
            f"- Версия модели: {result.supply_constraint_set.model_version}.",
            f"- Отображение доказательств: {result.supply_evidence_mapping.mapping_version}.",
            f"- Правовые источники: {', '.join(result.supply_evidence_mapping.legal_source_refs)}.",
            *[
                f"- Правило специальной модели поставки: {expression}."
                for expression in result.supply_constraint_set.expressions
            ],
            *[
                f"- Проверенный факт {item.fact_name}: исходное утверждение="
                f"{item.assertion_id}; доказательственные источники="
                f"{', '.join(item.source_refs)}."
                for item in result.supply_evidence_mapping.provenance
            ],
            *[f"- Результат: {reason}" for reason in supply.reasons_ru],
            *[f"- Ограничение: {warning}" for warning in supply.warnings_ru],
        ]
    )
    termination_professional_ru = "\n".join(
        [
            *[f"- {reason}" for reason in termination.reasons_ru],
            "- Наличие судебных предпосылок не означает расторжения до вступления решения в силу.",
            "- Специальные основания для конкретного вида договора проверяются юристом отдельно.",
        ]
    )
    termination_forensic_ru = "\n".join(
        [
            f"- Набор ограничений: {result.termination_constraint_set.id}.",
            f"- Версия модели: {result.termination_constraint_set.model_version}.",
            f"- Отображение доказательств: {result.termination_evidence_mapping.mapping_version}.",
            f"- Правовые источники: {', '.join(result.termination_evidence_mapping.legal_source_refs)}.",
            *[
                f"- Правило: {expression}."
                for expression in result.termination_constraint_set.expressions
            ],
            *[
                f"- Факт {item.fact_name}: assertion={item.assertion_id}; "
                f"источники={', '.join(item.source_refs)}."
                for item in result.termination_evidence_mapping.provenance
            ],
            *[f"- Результат: {reason}" for reason in termination.reasons_ru],
            *[f"- Ограничение: {warning}" for warning in termination.warnings_ru],
        ]
    )
    liability_professional_ru = "\n".join(
        [
            *[f"- {reason}" for reason in liability.reasons_ru],
            "- Снижение неустойки не рассчитывается автоматически и не устраняет ответственность.",
            "- Оценка доказательств и размер возможного снижения относятся к компетенции суда.",
        ]
    )
    liability_forensic_ru = "\n".join(
        [
            f"- Constraint set: {result.liability_constraint_set.id}.",
            f"- Model version: {result.liability_constraint_set.model_version}.",
            f"- Evidence mapping: {result.liability_evidence_mapping.mapping_version}.",
            f"- Legal sources: {', '.join(result.liability_evidence_mapping.legal_source_refs)}.",
            *[
                f"- Rule: {expression}."
                for expression in result.liability_constraint_set.expressions
            ],
            *[
                f"- Fact {item.fact_name}: assertion={item.assertion_id}; "
                f"sources={', '.join(item.source_refs)}."
                for item in result.liability_evidence_mapping.provenance
            ],
            *[f"- Результат: {reason}" for reason in liability.reasons_ru],
            *[f"- Ограничение: {warning}" for warning in liability.warnings_ru],
        ]
    )
    return {
        "conclusion_ru": conclusion_ru,
        "key_basis_ru": key_basis_ru,
        "risk_and_next_step_ru": risk_and_next_step_ru,
        "facts_ru": facts_ru,
        "rule_and_authority_ru": rule_and_authority_ru,
        "formal_result_ru": formal_result_ru,
        "limitations_ru": limitations_ru,
        "coordinates_ru": coordinates_ru,
        "provenance_ru": provenance_ru,
        "formal_rule_ru": formal_rule_ru,
        "authority_trace_ru": authority_trace_ru,
        "all_assertions_ru": all_assertions_ru,
        "governance_ru": governance_ru,
        "path_comparison_ru": path_comparison_ru,
        "counterfactual_professional_ru": counterfactual_professional_ru,
        "counterfactual_forensic_ru": counterfactual_forensic_ru,
        "formation_professional_ru": formation_professional_ru,
        "formation_forensic_ru": formation_forensic_ru,
        "invalidity_professional_ru": invalidity_professional_ru,
        "invalidity_forensic_ru": invalidity_forensic_ru,
        "security_professional_ru": security_professional_ru,
        "security_forensic_ru": security_forensic_ru,
        "dynamics_professional_ru": dynamics_professional_ru,
        "dynamics_forensic_ru": dynamics_forensic_ru,
        "performance_remedies_professional_ru": performance_remedies_professional_ru,
        "performance_remedies_forensic_ru": performance_remedies_forensic_ru,
        "sale_professional_ru": sale_professional_ru,
        "sale_forensic_ru": sale_forensic_ru,
        "supply_professional_ru": supply_professional_ru,
        "supply_forensic_ru": supply_forensic_ru,
        "termination_professional_ru": termination_professional_ru,
        "termination_forensic_ru": termination_forensic_ru,
        "liability_professional_ru": liability_professional_ru,
        "liability_forensic_ru": liability_forensic_ru,
        "disclaimer_ru": TRANSLATION_DISCLAIMER_RU,
    }


def _render_artifact(
    level: TranslationLevel,
    *,
    trace_id: str,
    template_set: TranslationTemplateSet,
    policy_snapshot: PolicySnapshot,
    assertions: list[TranslationAssertion],
    source_refs: list[str],
    context: dict[str, str],
) -> TranslationArtifact:
    template = template_set.template_for(level)
    return TranslationArtifact(
        id=f"translation:{trace_id}:{level.value}",
        trace_id=trace_id,
        level=level,
        template_version=template_set.version,
        template_content_hash=template_set.content_hash,
        policy_snapshot_id=policy_snapshot.id,
        policy_content_hash=policy_snapshot.content_hash,
        text=template.template_text_ru.format(**context),
        assertions=assertions,
        source_refs=source_refs,
    )


def evaluate_translation_faithfulness(
    *,
    trace_id: str,
    artifacts: list[TranslationArtifact],
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
    governance: GovernanceRecord,
    policy_snapshot: PolicySnapshot,
    template_set: TranslationTemplateSet,
) -> TranslationFaithfulnessReport:
    expected_assertions = build_translation_assertions(request, result)
    comparison = build_reasoning_path_comparison(request, result)
    context = _render_context(
        trace_id,
        request,
        result,
        governance,
        policy_snapshot,
        expected_assertions,
        comparison,
        template_set,
    )
    issues: list[TranslationCheckIssue] = []
    artifacts_by_level = {artifact.level: artifact for artifact in artifacts}
    if len(artifacts_by_level) != len(artifacts):
        issues.append(
            TranslationCheckIssue(
                code="duplicate_level",
                severity=TranslationCheckSeverity.ERROR,
                message_ru="Набор содержит повторяющийся уровень представления.",
            )
        )
    for level in TranslationLevel:
        artifact = artifacts_by_level.get(level)
        if artifact is None:
            issues.append(
                TranslationCheckIssue(
                    code="missing_level",
                    severity=TranslationCheckSeverity.ERROR,
                    level=level,
                    message_ru="Отсутствует обязательный уровень представления.",
                )
            )
            continue
        expected = _render_artifact(
            level,
            trace_id=trace_id,
            template_set=template_set,
            policy_snapshot=policy_snapshot,
            assertions=expected_assertions,
            source_refs=result.source_ids,
            context=context,
        )
        checks = [
            (artifact.trace_id == trace_id, "trace_mismatch", "Неверная ссылка на trace."),
            (
                artifact.template_version == template_set.version
                and artifact.template_content_hash == template_set.content_hash,
                "template_mismatch",
                "Координаты шаблона не совпадают с проверяемым набором.",
            ),
            (
                artifact.policy_snapshot_id == policy_snapshot.id
                and artifact.policy_content_hash == policy_snapshot.content_hash,
                "policy_mismatch",
                "Координаты политики не совпадают с decision trace.",
            ),
            (
                artifact.assertions == expected_assertions,
                "assertion_distortion",
                "Структурированные юридические утверждения искажены.",
            ),
            (
                artifact.source_refs == result.source_ids,
                "source_distortion",
                "Набор ссылок на источники изменен.",
            ),
            (
                artifact.text == expected.text,
                "text_distortion",
                "Текст не воспроизводится из проверенного trace и шаблона.",
            ),
            (
                TRANSLATION_DISCLAIMER_RU in artifact.text,
                "missing_disclaimer",
                "Отсутствует обязательное предупреждение.",
            ),
        ]
        for passed, code, message_ru in checks:
            if not passed:
                issues.append(
                    TranslationCheckIssue(
                        code=code,
                        severity=TranslationCheckSeverity.ERROR,
                        level=level,
                        message_ru=message_ru,
                    )
                )
    passed = not any(issue.severity == TranslationCheckSeverity.ERROR for issue in issues)
    return TranslationFaithfulnessReport(
        id=f"translation-faithfulness:{trace_id}",
        trace_id=trace_id,
        passed=passed,
        checked_levels=list(TranslationLevel),
        issues=issues,
        summary_ru=[
            (
                "Все три уровня точно воспроизводятся из проверенного trace и шаблонов."
                if passed
                else "Обнаружено искажение между trace и юридическим объяснением."
            )
        ],
    )


def _cyrillic_ratio(text: str) -> float:
    letters = [character for character in text.lower() if character.isalpha()]
    if not letters:
        return 0.0
    cyrillic = sum("а" <= character <= "я" or character == "ё" for character in letters)
    return cyrillic / len(letters)


def evaluate_translation_usability(
    *,
    trace_id: str,
    artifacts: list[TranslationArtifact],
    template_set: TranslationTemplateSet,
) -> TranslationUsabilityReport:
    issues: list[TranslationCheckIssue] = []
    artifacts_by_level = {artifact.level: artifact for artifact in artifacts}
    for level in TranslationLevel:
        artifact = artifacts_by_level.get(level)
        template = template_set.template_for(level)
        if artifact is None:
            issues.append(
                TranslationCheckIssue(
                    code="missing_level",
                    severity=TranslationCheckSeverity.ERROR,
                    level=level,
                    message_ru="Отсутствует обязательный уровень представления.",
                )
            )
            continue
        if not template.min_characters <= len(artifact.text) <= template.max_characters:
            issues.append(
                TranslationCheckIssue(
                    code="length_out_of_bounds",
                    severity=TranslationCheckSeverity.ERROR,
                    level=level,
                    message_ru="Длина текста не соответствует уровню представления.",
                )
            )
        for heading in template.required_headings_ru:
            if heading not in artifact.text:
                issues.append(
                    TranslationCheckIssue(
                        code="missing_heading",
                        severity=TranslationCheckSeverity.ERROR,
                        level=level,
                        message_ru=f"Отсутствует раздел «{heading}».",
                    )
                )
        minimum_cyrillic_ratio = 0.20 if level == TranslationLevel.FORENSIC else 0.55
        if _cyrillic_ratio(artifact.text) < minimum_cyrillic_ratio:
            issues.append(
                TranslationCheckIssue(
                    code="insufficient_russian_text",
                    severity=TranslationCheckSeverity.ERROR,
                    level=level,
                    message_ru="В тексте недостаточно русского человекочитаемого содержания.",
                )
            )
        if max(len(line) for line in artifact.text.splitlines()) > 240:
            issues.append(
                TranslationCheckIssue(
                    code="line_too_long",
                    severity=TranslationCheckSeverity.WARNING,
                    level=level,
                    message_ru="Отдельная строка слишком длинна для удобного аудита.",
                )
            )
        if level != TranslationLevel.FORENSIC and any(
            marker in artifact.text for marker in ("=True", "=False", "sha256:")
        ):
            issues.append(
                TranslationCheckIssue(
                    code="machine_detail_leak",
                    severity=TranslationCheckSeverity.ERROR,
                    level=level,
                    message_ru="Машинные детали попали в человекочитаемый уровень.",
                )
            )
    if set(artifacts_by_level) == set(TranslationLevel):
        lengths = [
            len(artifacts_by_level[level].text)
            for level in (
                TranslationLevel.EXECUTIVE,
                TranslationLevel.PROFESSIONAL,
                TranslationLevel.FORENSIC,
            )
        ]
        if not lengths[0] < lengths[1] < lengths[2]:
            issues.append(
                TranslationCheckIssue(
                    code="level_depth_order",
                    severity=TranslationCheckSeverity.ERROR,
                    message_ru="Глубина представления не возрастает от краткого к forensic.",
                )
            )
    passed = not any(issue.severity == TranslationCheckSeverity.ERROR for issue in issues)
    return TranslationUsabilityReport(
        id=f"translation-usability:{trace_id}",
        trace_id=trace_id,
        structural_checks_passed=passed,
        checked_levels=list(TranslationLevel),
        issues=issues,
        scope_ru=(
            "Автоматическая проверка оценивает структуру, русский язык, глубину уровней "
            "и отсутствие машинных деталей. Она не доказывает понимание текста юристом."
        ),
        summary_ru=[
            (
                "Структурные usability-проверки пройдены; требуется пилотная оценка юристом."
                if passed
                else "Структурные usability-проверки выявили блокирующие проблемы."
            )
        ],
    )


def build_translation_bundle(
    *,
    trace_id: str,
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
    governance: GovernanceRecord,
    policy_snapshot: PolicySnapshot,
    template_set: TranslationTemplateSet | None = None,
) -> TranslationBundle:
    selected_template_set = template_set or build_russian_translation_template_set()
    if policy_snapshot.payload.translation_template_version != selected_template_set.version:
        raise ValueError("Policy snapshot требует другую версию шаблонов Translation Layer.")
    if policy_snapshot.payload.translation_template_hash != selected_template_set.content_hash:
        raise ValueError("Policy snapshot содержит другой hash шаблонов Translation Layer.")
    assertions = build_translation_assertions(request, result)
    comparison = build_reasoning_path_comparison(request, result)
    context = _render_context(
        trace_id,
        request,
        result,
        governance,
        policy_snapshot,
        assertions,
        comparison,
        selected_template_set,
    )
    artifacts = [
        _render_artifact(
            level,
            trace_id=trace_id,
            template_set=selected_template_set,
            policy_snapshot=policy_snapshot,
            assertions=assertions,
            source_refs=result.source_ids,
            context=context,
        )
        for level in TranslationLevel
    ]
    faithfulness = evaluate_translation_faithfulness(
        trace_id=trace_id,
        artifacts=artifacts,
        request=request,
        result=result,
        governance=governance,
        policy_snapshot=policy_snapshot,
        template_set=selected_template_set,
    )
    usability = evaluate_translation_usability(
        trace_id=trace_id,
        artifacts=artifacts,
        template_set=selected_template_set,
    )
    checked_artifacts = [
        artifact.model_copy(
            update={
                "faithfulness_checked": True,
                "faithfulness_passed": faithfulness.passed,
                "usability_checked": True,
                "usability_passed": usability.structural_checks_passed,
            }
        )
        for artifact in artifacts
    ]
    return TranslationBundle(
        id=f"translation-bundle:{trace_id}",
        trace_id=trace_id,
        template_set_id=selected_template_set.id,
        template_version=selected_template_set.version,
        template_content_hash=selected_template_set.content_hash,
        policy_snapshot_id=policy_snapshot.id,
        policy_content_hash=policy_snapshot.content_hash,
        artifacts=checked_artifacts,
        path_comparisons=[comparison],
        faithfulness_report=faithfulness,
        usability_report=usability,
        ready_for_human_review=(faithfulness.passed and usability.structural_checks_passed),
    )
