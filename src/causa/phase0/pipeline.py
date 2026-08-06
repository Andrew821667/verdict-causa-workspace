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
from causa.institutional.contracts.synthetic_temporal_effect import (
    build_synthetic_temporal_effect_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_limitation import (
    build_synthetic_limitation_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_interpretation import (
    build_synthetic_interpretation_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_form import (
    build_synthetic_form_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_preliminary import (
    build_synthetic_preliminary_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_adhesion import (
    build_synthetic_adhesion_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_public_contract import (
    build_synthetic_public_contract_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_framework import (
    build_synthetic_framework_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_freedom import (
    build_synthetic_freedom_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_general_obligations import (
    build_synthetic_general_obligations_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_retail_sale import (
    build_synthetic_retail_sale_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_contractation import (
    build_synthetic_contractation_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_energy_supply import (
    build_synthetic_energy_supply_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_barter import (
    build_synthetic_barter_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_annuity import (
    build_synthetic_annuity_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_lease import (
    build_synthetic_lease_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_rental import (
    build_synthetic_rental_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_vehicle_lease import (
    build_synthetic_vehicle_lease_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_building_lease import (
    build_synthetic_building_lease_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_enterprise_lease import (
    build_synthetic_enterprise_lease_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_leasing import (
    build_synthetic_leasing_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_residential_lease import (
    build_synthetic_residential_lease_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_gratuitous_use import (
    build_synthetic_gratuitous_use_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_construction_contract import (
    build_synthetic_construction_contract_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_design_work import (
    build_synthetic_design_work_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_carriage import (
    build_synthetic_carriage_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_forwarding import (
    build_synthetic_forwarding_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_commercial_credit import (
    build_synthetic_commercial_credit_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_bank_account import (
    build_synthetic_bank_account_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_settlements import (
    build_synthetic_settlements_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_storage import (
    build_synthetic_storage_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_insurance import (
    build_synthetic_insurance_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_insurance_settlement import (
    build_synthetic_insurance_settlement_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_mandate import (
    build_synthetic_mandate_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_agency import (
    build_synthetic_agency_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_franchise import (
    build_synthetic_franchise_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_partnership import (
    build_synthetic_partnership_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_games import (
    build_synthetic_games_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_tort_general import (
    build_synthetic_tort_general_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_moral_harm import (
    build_synthetic_moral_harm_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_general_effects import (
    build_synthetic_general_effects_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_property_rights import (
    build_synthetic_property_rights_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_representation import (
    build_synthetic_representation_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_unjust_enrichment import (
    build_synthetic_unjust_enrichment_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_product_liability import (
    build_synthetic_product_liability_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_tort_life_health import (
    build_synthetic_tort_life_health_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_public_promise import (
    build_synthetic_public_promise_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_trust_management import (
    build_synthetic_trust_management_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_commission import (
    build_synthetic_commission_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_negotiorum_gestio import (
    build_synthetic_negotiorum_gestio_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_special_storage import (
    build_synthetic_special_storage_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_warehouse_storage import (
    build_synthetic_warehouse_storage_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_bank_deposit import (
    build_synthetic_bank_deposit_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_factoring import (
    build_synthetic_factoring_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_credit import (
    build_synthetic_credit_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_loan import (
    build_synthetic_loan_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_paid_services import (
    build_synthetic_paid_services_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_research_work import (
    build_synthetic_research_work_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_state_work import (
    build_synthetic_state_work_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_consumer_work import (
    build_synthetic_consumer_work_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_work_contract import (
    build_synthetic_work_contract_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_gift import (
    build_synthetic_gift_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_enterprise_sale import (
    build_synthetic_enterprise_sale_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_real_estate_sale import (
    build_synthetic_real_estate_sale_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_state_supply import (
    build_synthetic_state_supply_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_procedure import (
    build_synthetic_procedure_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_option import (
    build_synthetic_option_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_precontractual import (
    build_synthetic_precontractual_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_representations import (
    build_synthetic_representations_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_third_party import (
    build_synthetic_third_party_evaluation_artifact,
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
from causa.institutional.contracts.synthetic_pilot import (
    build_synthetic_pilot_rehearsal_artifact,
)
from causa.institutional.contracts.synthetic_sale import (
    build_synthetic_sale_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_supply import (
    build_synthetic_supply_evaluation_artifact,
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
            id="evaluate-contract-temporal-effect",
            title="Проверка действия договора во времени",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.temporal_effect_evidence_mapping.evidence_id,
                trace.analysis_result.temporal_effect_constraint_set.id,
                *trace.analysis_result.temporal_effect_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.temporal_effect_evaluation.reasons_ru,
                "Момент заключения, вступление в силу, обратное действие и окончание срока проверяются раздельно по статьям 425 и 433 ГК РФ.",
                "Окончание срока действия не отменяет ответственности за нарушение и не подменяет судебную оценку.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-limitation-period",
            title="Проверка исковой давности",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.limitation_evidence_mapping.evidence_id,
                trace.analysis_result.limitation_constraint_set.id,
                *trace.analysis_result.limitation_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.limitation_evaluation.reasons_ru,
                "Начало течения, общий и специальный срок, приостановление, перерыв и заявление стороны проверяются раздельно по статьям 195–208 ГК РФ.",
                "Давность применяется судом только по заявлению стороны и не подменяет судебную оценку.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-contract-interpretation",
            title="Проверка толкования условий договора",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.interpretation_evidence_mapping.evidence_id,
                trace.analysis_result.interpretation_constraint_set.id,
                *trace.analysis_result.interpretation_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.interpretation_evaluation.reasons_ru,
                "Буквальное значение, сопоставление с договором в целом и действительная общая воля сторон проверяются последовательно по статье 431 ГК РФ.",
                "Действительный смысл условия и воля сторон устанавливаются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-transaction-form",
            title="Проверка формы сделки",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.form_evidence_mapping.evidence_id,
                trace.analysis_result.form_constraint_set.id,
                *trace.analysis_result.form_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.form_evaluation.reasons_ru,
                "Устная, простая письменная и нотариальная форма, способы её соблюдения и последствия несоблюдения проверяются раздельно по статьям 158–165 и 434 ГК РФ.",
                "Достаточность доказательств формы и её последствия оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-preliminary-contract",
            title="Проверка предварительного договора",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.preliminary_evidence_mapping.evidence_id,
                trace.analysis_result.preliminary_constraint_set.id,
                *trace.analysis_result.preliminary_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.preliminary_evaluation.reasons_ru,
                "Заключение и форма предварительного договора, срок заключения основного договора, понуждение к заключению и прекращение обязательств проверяются раздельно по статье 429 ГК РФ.",
                "Определённость предмета основного договора и добросовестность сторон оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-third-party-contract",
            title="Проверка договора в пользу третьего лица",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.third_party_evidence_mapping.evidence_id,
                trace.analysis_result.third_party_constraint_set.id,
                *trace.analysis_result.third_party_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.third_party_evaluation.reasons_ru,
                "Право третьего лица требовать исполнения, связанность сторон после выражения намерения и последствия отказа третьего лица проверяются раздельно по статье 430 ГК РФ.",
                "Возражения должника против требования третьего лица и пределы права оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-public-contract",
            title="Проверка публичного договора",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.public_contract_evidence_mapping.evidence_id,
                trace.analysis_result.public_contract_constraint_set.id,
                *trace.analysis_result.public_contract_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.public_contract_evaluation.reasons_ru,
                "Обязанность заключить договор с каждым обратившимся, недопустимость предпочтения и различия условий без оснований и ничтожность противоречащих условий проверяются раздельно по статье 426 ГК РФ.",
                "Наличие законных оснований для отказа и различия условий оценивается экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-adhesion-contract",
            title="Проверка договора присоединения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.adhesion_evidence_mapping.evidence_id,
                trace.analysis_result.adhesion_constraint_set.id,
                *trace.analysis_result.adhesion_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.adhesion_evaluation.reasons_ru,
                "Режим присоединения, основания для изменения или расторжения и ограничение для присоединившегося предпринимателя проверяются раздельно по статье 428 ГК РФ.",
                "Обременительность условий и неравенство переговорных возможностей оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-representations",
            title="Проверка заверений об обстоятельствах",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.representations_evidence_mapping.evidence_id,
                trace.analysis_result.representations_constraint_set.id,
                *trace.analysis_result.representations_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.representations_evaluation.reasons_ru,
                "Недостоверность и значение заверения, основание ответственности, право на отказ от договора и оспаривание при обмане проверяются раздельно по статье 431.2 ГК РФ.",
                "Существенность заверения и обоснованность доверия оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-precontractual-liability",
            title="Проверка преддоговорной ответственности",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.precontractual_evidence_mapping.evidence_id,
                trace.analysis_result.precontractual_constraint_set.id,
                *trace.analysis_result.precontractual_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.precontractual_evaluation.reasons_ru,
                "Недобросовестное ведение и прекращение переговоров, нарушение конфиденциальности, возмещение убытков и ничтожность ограничения ответственности проверяются раздельно по статье 434.1 ГК РФ.",
                "Добросовестность сторон и оправданность прекращения переговоров оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-option-constructions",
            title="Проверка опциона и опционного договора",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.option_evidence_mapping.evidence_id,
                trace.analysis_result.option_constraint_set.id,
                *trace.analysis_result.option_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.option_evaluation.reasons_ru,
                "Безотзывная оферта и акцепт в срок, право требовать по опционному договору, прекращение по истечении срока и невозвратность платежа проверяются раздельно по статьям 429.2 и 429.3 ГК РФ.",
                "Определённость условий, возмездность и соблюдение сроков оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-framework-constructions",
            title="Проверка рамочного и абонентского договора",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.framework_evidence_mapping.evidence_id,
                trace.analysis_result.framework_constraint_set.id,
                *trace.analysis_result.framework_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.framework_evaluation.reasons_ru,
                "Общие условия рамочного договора, их конкретизация и применение к неурегулированным отношениям, а также плата по абонентскому договору независимо от требования проверяются раздельно по статьям 429.1 и 429.4 ГК РФ.",
                "Существо обязательства, содержание общих условий и условия о плате оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-freedom-and-price",
            title="Проверка свободы договора и цены",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.freedom_evidence_mapping.evidence_id,
                trace.analysis_result.freedom_constraint_set.id,
                *trace.analysis_result.freedom_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.freedom_evaluation.reasons_ru,
                "Свобода заключения, непоименованный и смешанный договор, соответствие императивным нормам, действие нового закона, презумпция возмездности и определение цены проверяются раздельно по статьям 421–424 ГК РФ.",
                "Квалификация непоименованного и смешанного договора, императивность норм и размер цены оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-conclusion-procedure",
            title="Проверка обязательного заключения и торгов",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.procedure_evidence_mapping.evidence_id,
                trace.analysis_result.procedure_constraint_set.id,
                *trace.analysis_result.procedure_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.procedure_evaluation.reasons_ru,
                "Понуждение обязанной стороны, определение условий судом, заключение на торгах, уклонение победителя и недействительность торгов проверяются раздельно по статьям 445–449 ГК РФ.",
                "Обязательность заключения, соблюдение правил торгов и размер убытков оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-general-obligations",
            title="Проверка общих положений об обязательствах",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.general_obligations_evidence_mapping.evidence_id,
                trace.analysis_result.general_obligations_constraint_set.id,
                *trace.analysis_result.general_obligations_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.general_obligations_evaluation.reasons_ru,
                "Понятие и стороны обязательства, добросовестность, альтернативные и факультативные обязательства и защита прав кредитора проверяются раздельно по статьям 307–308.3 ГК РФ.",
                "Добросовестность сторон, возможность исполнения в натуре и размер судебной неустойки оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-retail-sale",
            title="Проверка розничной купли-продажи",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.retail_sale_evidence_mapping.evidence_id,
                trace.analysis_result.retail_sale_constraint_set.id,
                *trace.analysis_result.retail_sale_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.retail_sale_evaluation.reasons_ru,
                "Публичность договора, форма и информация, обмен товара и права при ненадлежащем качестве проверяются раздельно по статьям 492–505 ГК РФ.",
                "Качество товара, достоверность информации и условия обмена оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-state-supply",
            title="Проверка поставки для государственных нужд",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.state_supply_evidence_mapping.evidence_id,
                trace.analysis_result.state_supply_constraint_set.id,
                *trace.analysis_result.state_supply_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.state_supply_evaluation.reasons_ru,
                "Обязательность заключения контракта, прикрепление покупателя, оплата по ценам контракта и возмещение убытков проверяются раздельно по статьям 525–534 ГК РФ.",
                "Обязательность заключения контракта, размер убытков и порядок размещения заказа оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-contractation",
            title="Проверка контрактации",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.contractation_evidence_mapping.evidence_id,
                trace.analysis_result.contractation_constraint_set.id,
                *trace.analysis_result.contractation_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.contractation_evaluation.reasons_ru,
                "Квалификация контрактации, обязанности заготовителя, возврат отходов и виновная ответственность производителя проверяются раздельно по статьям 535–538 ГК РФ.",
                "Соответствие продукции, вина производителя и условия возврата отходов оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-energy-supply",
            title="Проверка энергоснабжения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.energy_supply_evidence_mapping.evidence_id,
                trace.analysis_result.energy_supply_constraint_set.id,
                *trace.analysis_result.energy_supply_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.energy_supply_evaluation.reasons_ru,
                "Квалификация энергоснабжения, количество и качество энергии, содержание сетей, оплата по учёту и правомерность перерыва подачи проверяются раздельно по статьям 539–548 ГК РФ.",
                "Качество энергии, вина сторон и размер реального ущерба оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-real-estate-sale",
            title="Проверка продажи недвижимости",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.real_estate_sale_evidence_mapping.evidence_id,
                trace.analysis_result.real_estate_sale_constraint_set.id,
                *trace.analysis_result.real_estate_sale_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.real_estate_sale_evaluation.reasons_ru,
                "Квалификация продажи недвижимости, письменная форма, определённость предмета и цены, регистрация перехода права, передача по акту и качество проверяются раздельно по статьям 549–558 ГК РФ.",
                "Определённость предмета, размер убытков и государственная регистрация оцениваются экспертом и регистрирующим органом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-enterprise-sale",
            title="Проверка продажи предприятия",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.enterprise_sale_evidence_mapping.evidence_id,
                trace.analysis_result.enterprise_sale_constraint_set.id,
                *trace.analysis_result.enterprise_sale_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.enterprise_sale_evaluation.reasons_ru,
                "Квалификация продажи предприятия, письменная форма и регистрация договора, удостоверение состава, права кредиторов, передача по акту, регистрация перехода права и уменьшение цены проверяются раздельно по статьям 559–566 ГК РФ.",
                "Состав предприятия, размер долгов и убытков и государственная регистрация оцениваются экспертом, аудитором и регистрирующим органом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-barter",
            title="Проверка мены",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.barter_evidence_mapping.evidence_id,
                trace.analysis_result.barter_constraint_set.id,
                *trace.analysis_result.barter_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.barter_evaluation.reasons_ru,
                "Квалификация мены, применение правил о купле-продаже, равноценность и разница в цене, встречное исполнение, одновременный переход права и ответственность за изъятие проверяются раздельно по статьям 567–571 ГК РФ.",
                "Равноценность товаров, размер разницы в цене и основания изъятия оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-gift",
            title="Проверка дарения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.gift_evidence_mapping.evidence_id,
                trace.analysis_result.gift_constraint_set.id,
                *trace.analysis_result.gift_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.gift_evaluation.reasons_ru,
                "Квалификация дарения, притворность при встречном предоставлении, форма, запрещение и ограничения, отказ одаряемого, отмена дарения и пожертвование проверяются раздельно по статьям 572–582 ГК РФ.",
                "Стоимость дара, основания отмены и возмещение вреда от недостатков подаренной вещи оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-annuity",
            title="Проверка ренты и пожизненного содержания",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.annuity_evidence_mapping.evidence_id,
                trace.analysis_result.annuity_constraint_set.id,
                *trace.analysis_result.annuity_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.annuity_evaluation.reasons_ru,
                "Квалификация ренты, нотариальная форма, обеспечение и проценты за просрочку, выкуп постоянной ренты, расторжение пожизненной ренты и обременение имущества пожизненного содержания проверяются раздельно по статьям 583–605 ГК РФ.",
                "Размер ренты и содержания, выкупная цена и существенность нарушения оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-lease",
            title="Проверка общих положений об аренде",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.lease_evidence_mapping.evidence_id,
                trace.analysis_result.lease_constraint_set.id,
                *trace.analysis_result.lease_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.lease_evaluation.reasons_ru,
                "Квалификация аренды, определённость объекта, форма и регистрация, ответственность за недостатки, права третьих лиц, субаренда, капитальный ремонт, расторжение, преимущественное право и улучшения проверяются раздельно по статьям 606–625 ГК РФ.",
                "Размер арендной платы, существенность нарушения и стоимость улучшений оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-rental",
            title="Проверка проката",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.rental_evidence_mapping.evidence_id,
                trace.analysis_result.rental_constraint_set.id,
                *trace.analysis_result.rental_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.rental_evaluation.reasons_ru,
                "Квалификация проката, письменная форма, предельный срок, неприменение преимущественного права, распределение расходов на недостатки, срок устранения недостатков, возврат части платы, ремонт и запрет распоряжения проверяются раздельно по статьям 626–631 ГК РФ.",
                "Размер арендной платы, характер недостатков и объём возврата платы оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-vehicle-lease",
            title="Проверка аренды транспортных средств",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.vehicle_lease_evidence_mapping.evidence_id,
                trace.analysis_result.vehicle_lease_constraint_set.id,
                *trace.analysis_result.vehicle_lease_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.vehicle_lease_evaluation.reasons_ru,
                "Квалификация аренды транспортного средства, письменная форма, неприменение преимущественного права, содержание и ремонт, услуги экипажа, расходы по эксплуатации, страхование, субаренда и ответственность за вред третьим лицам проверяются раздельно по статьям 632–649 ГК РФ.",
                "Размер платы, распределение конкретных расходов и объём ответственности оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-building-lease",
            title="Проверка аренды зданий и сооружений",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.building_lease_evidence_mapping.evidence_id,
                trace.analysis_result.building_lease_constraint_set.id,
                *trace.analysis_result.building_lease_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.building_lease_evaluation.reasons_ru,
                "Квалификация аренды здания, форма одного документа и её недействительность, государственная регистрация при сроке не менее года, права на земельный участок, сохранение права пользования при смене собственника, существенное условие о плате и оформление передачи и возврата актом проверяются раздельно по статьям 650–655 ГК РФ.",
                "Размер арендной платы, состав передаваемых прав на участок и последствия уклонения от подписания акта оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-enterprise-lease",
            title="Проверка аренды предприятий",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.enterprise_lease_evidence_mapping.evidence_id,
                trace.analysis_result.enterprise_lease_constraint_set.id,
                *trace.analysis_result.enterprise_lease_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.enterprise_lease_evaluation.reasons_ru,
                "Квалификация аренды предприятия, форма одного документа и её недействительность, государственная регистрация, уведомление кредиторов и согласие на перевод долгов, передача по акту и подготовка за счёт арендодателя, право распоряжения ценностями, содержание предприятия и подготовка к возврату проверяются раздельно по статьям 656–664 ГК РФ.",
                "Состав предприятия, стоимость передаваемых ценностей и объём обязанностей по содержанию оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-leasing",
            title="Проверка финансовой аренды (лизинга)",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.leasing_evidence_mapping.evidence_id,
                trace.analysis_result.leasing_constraint_set.id,
                *trace.analysis_result.leasing_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.leasing_evaluation.reasons_ru,
                "Квалификация финансовой аренды, допустимость предмета лизинга, уведомление продавца, последствия непередачи предмета по вине лизингодателя, переход риска в момент передачи, прямые требования арендатора к продавцу и солидарная ответственность при выборе продавца лизингодателем проверяются раздельно по статьям 665–670 ГК РФ.",
                "Размер лизинговых платежей, распределение конкретных рисков и объём требований к продавцу оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-residential-lease",
            title="Проверка найма жилого помещения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.residential_lease_evidence_mapping.evidence_id,
                trace.analysis_result.residential_lease_constraint_set.id,
                *trace.analysis_result.residential_lease_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.residential_lease_evaluation.reasons_ru,
                "Квалификация найма жилого помещения, письменная форма, пригодность и изолированность помещения, обязанности наймодателя по эксплуатации, нарушения нанимателя, одностороннее изменение платы, преимущественное право на новый срок, судебный порядок расторжения и срок для устранения нарушения проверяются раздельно по статьям 671–688 ГК РФ.",
                "Размер платы, пригодность помещения, существенность нарушения и достаточность срока для его устранения оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-gratuitous-use",
            title="Проверка безвозмездного пользования (ссуды)",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.gratuitous_use_evidence_mapping.evidence_id,
                trace.analysis_result.gratuitous_use_constraint_set.id,
                *trace.analysis_result.gratuitous_use_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.gratuitous_use_evaluation.reasons_ru,
                "Квалификация ссуды, запрет передачи вещи инсайдеру организации, предоставление вещи с принадлежностями, ответственность за умышленно скрытые недостатки, права третьих лиц, содержание вещи, риск случайной гибели, досрочное расторжение, месячный срок извещения при отказе и сохранение прав при отчуждении проверяются раздельно по статьям 689–701 ГК РФ.",
                "Состояние вещи, характер недостатков, объём расходов на содержание и основания досрочного расторжения оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-work-contract",
            title="Проверка подряда (общие положения)",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.work_contract_evidence_mapping.evidence_id,
                trace.analysis_result.work_contract_constraint_set.id,
                *trace.analysis_result.work_contract_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.work_contract_evaluation.reasons_ru,
                "Квалификация подряда, обязанность выполнить работу лично, согласование начального и конечного сроков, предупреждение о существенном превышении сметы, непригодность материала заказчика, предупреждение об обстоятельствах, угрожающих годности работы, ответственность за недостатки результата, срок их обнаружения, обязанность осмотреть и принять результат и оплата при одностороннем отказе заказчика проверяются раздельно по статьям 702–729 ГК РФ.",
                "Существенность превышения сметы, качество результата работы, разумность сроков и объём выполненной части работы оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-consumer-work",
            title="Проверка бытового подряда",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.consumer_work_evidence_mapping.evidence_id,
                trace.analysis_result.consumer_work_constraint_set.id,
                *trace.analysis_result.consumer_work_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.consumer_work_evaluation.reasons_ru,
                "Квалификация бытового подряда, запрет навязывать дополнительную работу, право заказчика прекратить договор до сдачи работы, обязанность сообщить информацию о работе, недоброкачественный материал подрядчика, порядок оплаты после сдачи работы, сведения об использовании результата, существенные недостатки, десятилетний срок их обнаружения и двухмесячное предупреждение перед продажей невостребованного результата проверяются раздельно по статьям 730–739 ГК РФ.",
                "Существенность недостатка, достоверность и полнота информации и размер расходов заказчика оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-construction-contract",
            title="Проверка строительного подряда",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.construction_contract_evidence_mapping.evidence_id,
                trace.analysis_result.construction_contract_constraint_set.id,
                *trace.analysis_result.construction_contract_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.construction_contract_evaluation.reasons_ru,
                "Квалификация строительного подряда, страхование риска случайной гибели объекта, согласование технической документации и сметы, сообщение заказчику о не учтённых работах, предоставление участка и услуг, контроль заказчика за ходом работ, расчёты при консервации строительства, односторонний акт приёмки, отступления от документации и обязательных норм и предельный пятилетний срок обнаружения недостатков проверяются раздельно по статьям 740–757 ГК РФ.",
                "Существенность отступлений от документации, обоснованность отказа от подписания акта и объём расходов при консервации оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-design-work",
            title="Проверка проектных и изыскательских работ",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.design_work_evidence_mapping.evidence_id,
                trace.analysis_result.design_work_constraint_set.id,
                *trace.analysis_result.design_work_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.design_work_evaluation.reasons_ru,
                "Квалификация договора на проектные и изыскательские работы, передача задания и исходных данных, отступление от требований задания без согласия заказчика, согласование документации с заказчиком и компетентными органами, запрет передачи документации третьим лицам, гарантия отсутствия у третьих лиц права воспрепятствовать работам, ответственность за недостатки документации, их выявление в ходе строительства или эксплуатации, оплата и содействие заказчика и возмещение дополнительных расходов проверяются раздельно по статьям 758–762 ГК РФ.",
                "Полнота исходных данных, характер недостатков документации и объём дополнительных расходов оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-state-work",
            title="Проверка подрядных работ для государственных нужд",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.state_work_evidence_mapping.evidence_id,
                trace.analysis_result.state_work_constraint_set.id,
                *trace.analysis_result.state_work_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.state_work_evaluation.reasons_ru,
                "Квалификация работ для государственных или муниципальных нужд, требование государственного или муниципального контракта, статус заказчика как получателя бюджетных средств, порядок заключения контракта, условия об объёме и стоимости работ, сроках начала и окончания, размере и порядке финансирования и оплаты, способах обеспечения исполнения обязательств, согласование новых условий при уменьшении бюджетных средств и возмещение убытков подрядчика проверяются раздельно по статьям 763–768 ГК РФ.",
                "Достаточность бюджетного финансирования, соблюдение закупочных процедур и размер убытков подрядчика оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-research-work",
            title="Проверка научно-исследовательских и опытно-конструкторских работ",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.research_work_evidence_mapping.evidence_id,
                trace.analysis_result.research_work_constraint_set.id,
                *trace.analysis_result.research_work_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.research_work_evaluation.reasons_ru,
                "Квалификация договора на выполнение научно-исследовательских, опытно-конструкторских и технологических работ, обязанность провести исследования лично, конфиденциальность сведений, пределы и условия использования результатов, гарантия ненарушения исключительных прав других лиц, незамедлительное сообщение о невозможности получить результат, обязанности заказчика, последствия невозможности достижения результата и ответственность исполнителя проверяются раздельно по статьям 769–778 ГК РФ.",
                "Достижимость научного результата, наличие вины исполнителя и размер понесённых затрат оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-paid-services",
            title="Проверка возмездного оказания услуг",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.paid_services_evidence_mapping.evidence_id,
                trace.analysis_result.paid_services_constraint_set.id,
                *trace.analysis_result.paid_services_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.paid_services_evaluation.reasons_ru,
                "Квалификация возмездного оказания услуг, исключение услуг по договорам отдельных глав Кодекса, обязанность оказать услуги лично, сроки и порядок оплаты, полная оплата при невозможности по вине заказчика, возмещение фактически понесённых расходов при невозможности без вины сторон, отказ заказчика с оплатой расходов, отказ исполнителя с полным возмещением убытков и правила приостановления услуг связи проверяются раздельно по статьям 779–783.1 ГК РФ.",
                "Качество оказанных услуг, наличие вины стороны и размер фактически понесённых расходов оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-carriage",
            title="Проверка перевозки",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.carriage_evidence_mapping.evidence_id,
                trace.analysis_result.carriage_constraint_set.id,
                *trace.analysis_result.carriage_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.carriage_evaluation.reasons_ru,
                "Квалификация перевозки, оформление транспортной накладной, билета и багажной квитанции, публичный характер перевозки транспортом общего пользования, провозная плата и удержание груза, подача транспортных средств и их использование, сроки доставки, задержка отправления пассажира, утрата и повреждение груза и недействительность соглашений об ограничении ответственности перевозчика проверяются раздельно по статьям 784–800 ГК РФ.",
                "Транспортные уставы и кодексы, размер возмещения и обстоятельства, которые перевозчик не мог предотвратить, оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-forwarding",
            title="Проверка транспортной экспедиции",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.forwarding_evidence_mapping.evidence_id,
                trace.analysis_result.forwarding_constraint_set.id,
                *trace.analysis_result.forwarding_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.forwarding_evaluation.reasons_ru,
                "Квалификация транспортной экспедиции, письменная форма договора и доверенность, выполнение и организация экспедиционных услуг, ответственность, связанная с договором перевозки, предоставление клиентом документов и информации о грузе, сообщение экспедитора о неполноте сведений, привлечение третьих лиц, предупреждение об отказе в разумный срок, возмещение убытков от расторжения и штраф проверяются раздельно по статьям 801–806 ГК РФ.",
                "Разумность срока предупреждения, состав экспедиционных услуг и размер убытков и затрат оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-loan",
            title="Проверка займа",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.loan_evidence_mapping.evidence_id,
                trace.analysis_result.loan_constraint_set.id,
                *trace.analysis_result.loan_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.loan_evaluation.reasons_ru,
                "Квалификация займа, письменная форма договора, правила о процентах и беспроцентном займе, уменьшение ростовщических процентов, обязанность возврата суммы займа, проценты за просрочку, оспаривание по безденежности, последствия утраты обеспечения, контроль за использованием целевого займа и новация долга в заёмное обязательство проверяются раздельно по статьям 807–818 ГК РФ.",
                "Обычно взимаемый размер процентов, обременительность условий и достаточность доказательств безденежности оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-credit",
            title="Проверка кредита",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.credit_evidence_mapping.evidence_id,
                trace.analysis_result.credit_constraint_set.id,
                *trace.analysis_result.credit_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.credit_evaluation.reasons_ru,
                "Квалификация кредитного договора, статус кредитора как банка или иной кредитной организации, проценты и иные платежи, применение правил о потребительском кредите, обязательная письменная форма под страхом ничтожности, отказ кредитора при обстоятельствах невозврата, уведомление заёмщика об отказе от получения, нецелевое использование кредита и требование досрочного возврата проверяются раздельно по статьям 819–821.1 ГК РФ.",
                "Достаточность обстоятельств, свидетельствующих о невозврате, применимость закона о потребительском кредите и основания досрочного возврата оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-commercial-credit",
            title="Проверка товарного и коммерческого кредита",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.commercial_credit_evidence_mapping.evidence_id,
                trace.analysis_result.commercial_credit_constraint_set.id,
                *trace.analysis_result.commercial_credit_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.commercial_credit_evaluation.reasons_ru,
                "Квалификация товарного кредита, предоставление вещей, определённых родовыми признаками, условия о количестве, ассортименте, комплектности, качестве, таре и упаковке, применение правил о займе, квалификация коммерческого кредита в виде аванса, предварительной оплаты, отсрочки и рассрочки, согласование его условий, проценты, пределы применения правил главы и установленный законом запрет проверяются раздельно по статьям 822 и 823 ГК РФ.",
                "Существо обязательства, применимость правил основного договора и размер процентов оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-factoring",
            title="Проверка финансирования под уступку денежного требования",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.factoring_evidence_mapping.evidence_id,
                trace.analysis_result.factoring_constraint_set.id,
                *trace.analysis_result.factoring_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.factoring_evaluation.reasons_ru,
                "Квалификация договора факторинга, определённость уступаемого денежного требования, право финансового агента осуществлять такую деятельность, недействительность договорного запрета уступки против агента, ответственность клиента за действительность требования, допустимость последующей уступки, уведомление должника об уступке, зачёт встречных требований должника, расчёты финансового агента с клиентом и надлежащий адресат требования должника о возврате сумм проверяются раздельно по статьям 824–833 ГК РФ.",
                "Действительность уступленного требования, содержание уведомления должника и состав встречных требований оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-bank-deposit",
            title="Проверка банковского вклада",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.bank_deposit_evidence_mapping.evidence_id,
                trace.analysis_result.bank_deposit_constraint_set.id,
                *trace.analysis_result.bank_deposit_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.bank_deposit_evaluation.reasons_ru,
                "Квалификация договора банковского вклада, право банка привлекать денежные средства во вклады, обязательная письменная форма под страхом ничтожности, выдача вклада по первому требованию вкладчика, размер процентов при досрочном возврате, выплата процентов на сумму вклада, запрет одностороннего уменьшения ставки по срочному вкладу гражданина, обеспечение возврата вклада, зачисление средств третьих лиц и права по вкладу в пользу третьего лица, а также правила о сберегательной книжке и сберегательном сертификате проверяются раздельно по статьям 834–844 ГК РФ.",
                "Наличие у банка права привлекать вклады, достаточность обеспечения возврата и содержание условий о процентах оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-bank-account",
            title="Проверка банковского счёта",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.bank_account_evidence_mapping.evidence_id,
                trace.analysis_result.bank_account_constraint_set.id,
                *trace.analysis_result.bank_account_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.bank_account_evaluation.reasons_ru,
                "Квалификация договора банковского счёта, заключение договора на объявленных банком условиях, удостоверение прав распоряжения счётом, сроки операций по счёту, ответственность банка за ненадлежащее совершение операций, кредитование счёта, оплата услуг банка и проценты за пользование средствами, списание средств без распоряжения клиента и очерёдность списания, банковская тайна и ограничение распоряжения счётом, расторжение договора и возврат остатка проверяются раздельно по статьям 845–860 ГК РФ.",
                "Основания отказа в заключении договора, законность списания без распоряжения клиента и наличие оснований для ограничения распоряжения счётом оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-settlements",
            title="Проверка расчётов",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.settlements_evidence_mapping.evidence_id,
                trace.analysis_result.settlements_constraint_set.id,
                *trace.analysis_result.settlements_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.settlements_evaluation.reasons_ru,
                "Осуществление безналичных расчётов, допустимость применённой формы расчётов, исполнение платёжного поручения и ответственность банка за его неисполнение, условия аккредитива и порядок его закрытия, исполнение инкассового поручения, обязательные реквизиты чека, его оплата и гарантия платежа авалем, а также удостоверение отказа от оплаты чека проверяются раздельно по статьям 861–885 ГК РФ.",
                "Соответствие представленных документов условиям аккредитива, основания неисполнения поручений и достаточность средств оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-storage",
            title="Проверка хранения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.storage_evidence_mapping.evidence_id,
                trace.analysis_result.storage_constraint_set.id,
                *trace.analysis_result.storage_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.storage_evaluation.reasons_ru,
                "Квалификация договора хранения, письменная форма договора, обязанность принять вещь на хранение, срок хранения, принятие мер по обеспечению сохранности вещи, запрет пользоваться вещью без согласия поклажедателя, уведомление об изменении условий хранения и передаче вещи третьему лицу, вознаграждение и расходы на хранение, возврат вещи и ответственность хранителя проверяются раздельно по статьям 886–906 ГК РФ.",
                "Достаточность принятых мер по обеспечению сохранности, необходимость чрезвычайных расходов и наличие вины хранителя оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-warehouse-storage",
            title="Проверка хранения на товарном складе",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.warehouse_storage_evidence_mapping.evidence_id,
                trace.analysis_result.warehouse_storage_constraint_set.id,
                *trace.analysis_result.warehouse_storage_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.warehouse_storage_evaluation.reasons_ru,
                "Квалификация договора складского хранения, публичный характер договора склада общего пользования, осмотр товаров и определение их количества при приёме, фиксация выявленных расхождений, право товаровладельца осматривать товары и брать пробы, уведомление об изменении условий хранения, проверка товаров при их возвращении, выдача складских документов, правила о двойном складском свидетельстве и выдача товара по нему проверяются раздельно по статьям 907–918 ГК РФ.",
                "Существенность изменения условий хранения, достаточность осмотра товаров и правомерность выдачи товара по складским документам оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-special-storage",
            title="Проверка специальных видов хранения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.special_storage_evidence_mapping.evidence_id,
                trace.analysis_result.special_storage_constraint_set.id,
                *trace.analysis_result.special_storage_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.special_storage_evaluation.reasons_ru,
                "Квалификация специального вида хранения, хранение вещи в ломбарде, хранение ценностей в банке и в индивидуальном банковском сейфе, хранение в камерах хранения транспортных организаций и судьба невостребованных вещей, хранение в гардеробах организаций, ответственность гостиницы за вещи постояльца, секвестр спорной вещи и пределы ответственности хранителя проверяются раздельно по статьям 919–926 ГК РФ.",
                "Оценка вещи, состав внесённых в гостиницу вещей и управомоченность получателя при секвестре оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-insurance",
            title="Проверка страхования",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.insurance_evidence_mapping.evidence_id,
                trace.analysis_result.insurance_constraint_set.id,
                *trace.analysis_result.insurance_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.insurance_evaluation.reasons_ru,
                "Квалификация договора страхования, право страховщика осуществлять страхование данного вида, наличие и правомерность страхового интереса, обязательная письменная форма договора, согласование существенных условий, применение правил страхования, пределы имущественного и личного страхования, права выгодоприобретателя и исполнение обязанности по обязательному страхованию проверяются раздельно по статьям 927–943 ГК РФ.",
                "Наличие страхового интереса, характер страхового случая и содержание правил страхования оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-insurance-settlement",
            title="Проверка исполнения страхового обязательства",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.insurance_settlement_evidence_mapping.evidence_id,
                trace.analysis_result.insurance_settlement_constraint_set.id,
                *trace.analysis_result.insurance_settlement_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.insurance_settlement_evaluation.reasons_ru,
                "Сообщение существенных сведений при заключении договора, страховая сумма и страховая стоимость, порядок уплаты страховой премии, увеличение страхового риска и досрочное прекращение договора, уведомление о страховом случае и последствия его несвоевременности, меры по уменьшению убытков, основания освобождения страховщика, суброгация и исковая давность проверяются раздельно по статьям 944–970 ГК РФ.",
                "Существенность несообщённых сведений, разумность мер по уменьшению убытков и наличие оснований освобождения страховщика оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-mandate",
            title="Проверка поручения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.mandate_evidence_mapping.evidence_id,
                trace.analysis_result.mandate_constraint_set.id,
                *trace.analysis_result.mandate_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.mandate_evaluation.reasons_ru,
                "Квалификация договора поручения, вознаграждение поверенного, исполнение поручения в соответствии с указаниями доверителя, уведомление о допущенных отступлениях, личное исполнение поручения и передоверие, обязанности поверенного сообщать сведения и представить отчёт, обязанности доверителя, прекращение договора поручения, его последствия и обязанности правопреемников поверенного проверяются раздельно по статьям 971–979 ГК РФ.",
                "Правомерность и осуществимость указаний доверителя, необходимость отступления от них и соразмерность вознаграждения оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-negotiorum-gestio",
            title="Проверка действий в чужом интересе без поручения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.negotiorum_gestio_evidence_mapping.evidence_id,
                trace.analysis_result.negotiorum_gestio_constraint_set.id,
                *trace.analysis_result.negotiorum_gestio_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.negotiorum_gestio_evaluation.reasons_ru,
                "Условия совершения действий в чужом интересе, сообщение заинтересованному лицу и ожидание его решения, последствия одобрения и неодобрения действий, возмещение необходимых расходов и реального ущерба, вознаграждение, переход последствий сделки, заключённой в чужом интересе, и отчёт действовавшего лица проверяются раздельно по статьям 980–989 ГК РФ.",
                "Очевидность выгоды, действительные намерения заинтересованного лица и необходимость понесённых расходов оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-commission",
            title="Проверка комиссии",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.commission_evidence_mapping.evidence_id,
                trace.analysis_result.commission_constraint_set.id,
                *trace.analysis_result.commission_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.commission_evaluation.reasons_ru,
                "Квалификация договора комиссии, комиссионное вознаграждение и делькредере, исполнение поручения на наиболее выгодных условиях и отступление от указаний с уведомлением, ответственность за неисполнение сделки третьим лицом, субкомиссия, права комитента на вещи и удержание комиссионера, отчёт комиссионера и передача полученного, обязанности комитента и прекращение договора проверяются раздельно по статьям 990–1004 ГК РФ.",
                "Выгодность условий сделки, необходимая осмотрительность при выборе третьего лица и обоснованность отступления от указаний оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-agency",
            title="Проверка агентирования",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.agency_evidence_mapping.evidence_id,
                trace.analysis_result.agency_constraint_set.id,
                *trace.analysis_result.agency_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.agency_evaluation.reasons_ru,
                "Квалификация агентского договора, определение стороны сделки в зависимости от того, от чьего имени действует агент, агентское вознаграждение, допустимые ограничения прав принципала и агента, ничтожность условий об исключительном круге покупателей, отчёты агента и возражения принципала, субагентский договор, прекращение договора и применение правил о поручении или комиссии проверяются раздельно по статьям 1005–1011 ГК РФ.",
                "Существо агентского договора, допустимость договорных ограничений и обоснованность возражений по отчёту оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-trust-management",
            title="Проверка доверительного управления имуществом",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.trust_management_evidence_mapping.evidence_id,
                trace.analysis_result.trust_management_constraint_set.id,
                *trace.analysis_result.trust_management_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.trust_management_evaluation.reasons_ru,
                "Квалификация договора доверительного управления, допустимость объекта управления, требования к доверительному управляющему, существенные условия и форма договора с государственной регистрацией передачи недвижимости, обособление имущества, предупреждение об обременении залогом, права и отчёт управляющего, его ответственность, вознаграждение и прекращение договора проверяются раздельно по статьям 1012–1026 ГК РФ.",
                "Состав переданного имущества, должная заботливость управляющего и обоснованность расходов оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-franchise",
            title="Проверка коммерческой концессии",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.franchise_evidence_mapping.evidence_id,
                trace.analysis_result.franchise_constraint_set.id,
                *trace.analysis_result.franchise_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.franchise_evaluation.reasons_ru,
                "Квалификация договора коммерческой концессии, объём предоставленного комплекса исключительных прав и состав сторон, письменная форма договора и государственная регистрация предоставления права, ничтожность при пороке формы, коммерческая субконцессия, вознаграждение правообладателя, обязанности правообладателя и пользователя, допустимые ограничения прав сторон и ничтожные условия, ответственность правообладателя и прекращение договора проверяются раздельно по статьям 1027–1040 ГК РФ.",
                "Объём переданных исключительных прав, качество товаров пользователя и добросовестность сторон оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-partnership",
            title="Проверка простого товарищества",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.partnership_evidence_mapping.evidence_id,
                trace.analysis_result.partnership_constraint_set.id,
                *trace.analysis_result.partnership_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.partnership_evaluation.reasons_ru,
                "Квалификация договора простого товарищества, состав сторон и цель совместной деятельности, вклады товарищей и режим общего имущества, ведение общих дел, право на информацию и распределение общих расходов и убытков, ответственность товарищей по общим обязательствам, распределение прибыли и ничтожность отстранения товарища от участия в ней, выдел доли, прекращение договора и выход товарища, а также негласное товарищество проверяются раздельно по статьям 1041–1054 ГК РФ.",
                "Стоимость вкладов товарищей, содержание общей цели и добросовестность ведения общих дел оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-public-promise",
            title="Проверка публичного обещания награды и конкурса",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.public_promise_evidence_mapping.evidence_id,
                trace.analysis_result.public_promise_constraint_set.id,
                *trace.analysis_result.public_promise_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.public_promise_evaluation.reasons_ru,
                "Квалификация публичного обещания награды и публичного конкурса, требования к объявлению, размер и распределение награды, форма и пределы отмены обещания с возмещением расходов отозвавшимся лицам, обязательные условия объявления о конкурсе, его направленность на общественно полезные цели, изменение условий и отмена конкурса, решение о выплате награды и возврат участникам представленных работ проверяются раздельно по статьям 1055–1061 ГК РФ.",
                "Существо конкурсного задания, общественная полезность цели конкурса и обоснованность оценки работ оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-games",
            title="Проверка проведения игр и пари",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.games_evidence_mapping.evidence_id,
                trace.analysis_result.games_constraint_set.id,
                *trace.analysis_result.games_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.games_evaluation.reasons_ru,
                "Квалификация отношений, связанных с организацией игр и пари, отказ в судебной защите требований из них, исключение для лиц, участвовавших под влиянием обмана, насилия или угрозы, условия судебной защиты требований из расчётных сделок, статус и разрешение организатора игр, оформление договора с участником, правила проведения игр, объявленные условия о сроке и порядке определения выигрыша, срок его выплаты и право участника требовать возмещения убытков проверяются раздельно по статьям 1062 и 1063 ГК РФ.",
                "Наличие обмана, насилия или угрозы при участии в играх, характер расчётной сделки и содержание правил проведения игр оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-tort-general",
            title="Проверка общих правил о возмещении вреда",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.tort_general_evidence_mapping.evidence_id,
                trace.analysis_result.tort_general_constraint_set.id,
                *trace.analysis_result.tort_general_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.tort_general_evaluation.reasons_ru,
                "Установление причинения вреда, правило о возмещении вреда в полном объёме, презумпция вины причинителя, вред в состоянии необходимой обороны и крайней необходимости, ответственность за вред, причинённый работником, органами власти, несовершеннолетними и недееспособными, ответственность владельца источника повышенной опасности, солидарная ответственность и регресс, способ и размер возмещения, учёт умысла и грубой неосторожности потерпевшего проверяются раздельно по статьям 1064–1083 ГК РФ.",
                "Наличие вины причинителя, причинная связь, степень вины потерпевшего и размер убытков оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-tort-life-health",
            title="Проверка возмещения вреда жизни и здоровью",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.tort_life_health_evidence_mapping.evidence_id,
                trace.analysis_result.tort_life_health_constraint_set.id,
                *trace.analysis_result.tort_life_health_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.tort_life_health_evaluation.reasons_ru,
                "Установление вреда жизни или здоровью гражданина, объём и характер возмещения, расчёт утраченного заработка, особенности возмещения несовершеннолетнему потерпевшему, круг лиц, имеющих право на возмещение по случаю смерти кормильца, размер выплат им, изменение размера возмещения и его индексация, порядок ежемесячных платежей и капитализация при ликвидации должника, а также возмещение расходов на погребение проверяются раздельно по статьям 1084–1094 ГК РФ.",
                "Степень утраты трудоспособности, нуждаемость в дополнительных видах помощи, состав иждивенцев и размер заработка потерпевшего оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-product-liability",
            title="Проверка вреда вследствие недостатков товаров и услуг",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.product_liability_evidence_mapping.evidence_id,
                trace.analysis_result.product_liability_constraint_set.id,
                *trace.analysis_result.product_liability_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.product_liability_evaluation.reasons_ru,
                "Установление вреда вследствие недостатков товара, работы или услуги, возмещение независимо от вины и наличия договорных отношений, требование о приобретении в потребительских целях, право потерпевшего выбрать продавца или изготовителя, ответственность исполнителя работы и услуги, ответственность за непредоставление полной и достоверной информации, сроки возмещения по сроку годности и службы, исключение при неустановленном сроке и основания освобождения от ответственности проверяются раздельно по статьям 1095–1098 ГК РФ.",
                "Наличие недостатка, его причинная связь с вредом, цель приобретения товара и соблюдение потребителем правил пользования оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-moral-harm",
            title="Проверка компенсации морального вреда",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.moral_harm_evidence_mapping.evidence_id,
                trace.analysis_result.moral_harm_constraint_set.id,
                *trace.analysis_result.moral_harm_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.moral_harm_evaluation.reasons_ru,
                "Установление морального вреда, компенсация при посягательстве на нематериальные блага, компенсация при нарушении имущественных прав только в предусмотренных законом случаях, независимость компенсации от возмещения имущественного вреда, основания компенсации независимо от вины причинителя, вред источником повышенной опасности, незаконное привлечение к ответственности, распространение порочащих сведений, денежная форма и размер компенсации проверяются раздельно по статьям 1099–1101 ГК РФ.",
                "Характер и степень физических и нравственных страданий, индивидуальные особенности потерпевшего и требования разумности и справедливости оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-unjust-enrichment",
            title="Проверка неосновательного обогащения",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.unjust_enrichment_evidence_mapping.evidence_id,
                trace.analysis_result.unjust_enrichment_constraint_set.id,
                *trace.analysis_result.unjust_enrichment_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.unjust_enrichment_evaluation.reasons_ru,
                "Установление неосновательного обогащения, обязанность его возврата, независимость правил от причин обогащения, их применение к требованиям о возврате исполненного по недействительной сделке и об истребовании имущества, возврат обогащения в натуре, возмещение действительной стоимости, восстановление прежнего положения при неосновательной передаче права, возврат доходов с начислением процентов, возмещение затрат на содержание имущества и перечень имущества, не подлежащего возврату, проверяются раздельно по статьям 1102–1109 ГК РФ.",
                "Наличие правового основания приобретения имущества, его действительная стоимость и добросовестность приобретателя оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-property-rights",
            title="Проверка права собственности и его защиты",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.property_rights_evidence_mapping.evidence_id,
                trace.analysis_result.property_rights_constraint_set.id,
                *trace.analysis_result.property_rights_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.property_rights_evaluation.reasons_ru,
                "Содержание права собственности, распоряжение неуправомоченным лицом, бремя содержания и риск случайной гибели, момент возникновения права у приобретателя, приобретательная давность, режим общей собственности, истребование имущества из чужого незаконного владения, защита добросовестного приобретателя и негаторная защита проверяются раздельно по статьям 209–305 ГК РФ.",
                "Добросовестность приобретателя, обстоятельства выбытия имущества из владения собственника и давностное владение оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-representation",
            title="Проверка представительства и доверенности",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.representation_evidence_mapping.evidence_id,
                trace.analysis_result.representation_constraint_set.id,
                *trace.analysis_result.representation_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.representation_evaluation.reasons_ru,
                "Квалификация представительства, основание полномочия, запрет совершения представителем сделок в отношении себя лично, коммерческое представительство, форма, удостоверение и срок доверенности, передоверие, прекращение доверенности и извещение о нём, а также совершение сделки неуполномоченным лицом и последующее одобрение проверяются раздельно по статьям 182–189 ГК РФ.",
                "Объём полномочий представителя, явствование полномочия из обстановки и факт последующего одобрения сделки оцениваются экспертом и судом.",
            ],
        ),
        PipelineStepResult(
            id="apply-general-part-effects",
            title="Применение общих положений ГК к выводам институтов",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.general_effects_constraint_set.id,
                *trace.analysis_result.general_effects_constraint_set.source_evaluations,
            ],
            notes=[
                *trace.analysis_result.general_effects_evaluation.reasons_ru,
                "Слой выводит из результатов якорных моделей общей части, действует ли договор как основание требований, доступна ли судебная защита, сохраняют ли выводы специальных институтов правовой эффект, может ли установленное нарушение обосновать присуждение и подлежат ли применению последствия недействительности (статьи 167, 199 и 432 ГК РФ).",
                "Наличие оснований недействительности, уважительность причин пропуска срока исковой давности и состав подлежащего возврату оцениваются экспертом и судом.",
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
            id="evaluate-general-sale-rules",
            title="Проверка общих правил договора купли-продажи",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.sale_evidence_mapping.evidence_id,
                trace.analysis_result.sale_constraint_set.id,
                *trace.analysis_result.sale_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.sale_evaluation.reasons_ru,
                "Правила статей 454–491 ГК РФ проверяются до специальных правил поставки.",
                "Передача, риск, права третьих лиц, соответствие товара, приемка и оплата не смешиваются.",
            ],
        ),
        PipelineStepResult(
            id="evaluate-special-supply-rules",
            title="Проверка специальных правил договора поставки",
            status=PipelineStepStatus.PASSED,
            artifact_refs=[
                trace.analysis_result.supply_evidence_mapping.evidence_id,
                trace.analysis_result.supply_constraint_set.id,
                *trace.analysis_result.supply_constraint_set.legal_source_refs,
            ],
            notes=[
                *trace.analysis_result.supply_evaluation.reasons_ru,
                "Правила статей 506–524 ГК РФ проверяются отдельно от общих норм обязательственного права.",
                "Недопоставка, приемка, дефекты, односторонний отказ и ценовые убытки не смешиваются.",
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
    temporal_effect_artifact = build_synthetic_temporal_effect_evaluation_artifact()
    limitation_artifact = build_synthetic_limitation_evaluation_artifact()
    interpretation_artifact = build_synthetic_interpretation_evaluation_artifact()
    form_artifact = build_synthetic_form_evaluation_artifact()
    preliminary_artifact = build_synthetic_preliminary_evaluation_artifact()
    third_party_artifact = build_synthetic_third_party_evaluation_artifact()
    public_contract_artifact = build_synthetic_public_contract_evaluation_artifact()
    adhesion_artifact = build_synthetic_adhesion_evaluation_artifact()
    representations_artifact = build_synthetic_representations_evaluation_artifact()
    precontractual_artifact = build_synthetic_precontractual_evaluation_artifact()
    option_artifact = build_synthetic_option_evaluation_artifact()
    framework_artifact = build_synthetic_framework_evaluation_artifact()
    freedom_artifact = build_synthetic_freedom_evaluation_artifact()
    procedure_artifact = build_synthetic_procedure_evaluation_artifact()
    general_obligations_artifact = build_synthetic_general_obligations_evaluation_artifact()
    retail_sale_artifact = build_synthetic_retail_sale_evaluation_artifact()
    state_supply_artifact = build_synthetic_state_supply_evaluation_artifact()
    contractation_artifact = build_synthetic_contractation_evaluation_artifact()
    energy_supply_artifact = build_synthetic_energy_supply_evaluation_artifact()
    real_estate_sale_artifact = build_synthetic_real_estate_sale_evaluation_artifact()
    enterprise_sale_artifact = build_synthetic_enterprise_sale_evaluation_artifact()
    barter_artifact = build_synthetic_barter_evaluation_artifact()
    gift_artifact = build_synthetic_gift_evaluation_artifact()
    annuity_artifact = build_synthetic_annuity_evaluation_artifact()
    lease_artifact = build_synthetic_lease_evaluation_artifact()
    rental_artifact = build_synthetic_rental_evaluation_artifact()
    vehicle_lease_artifact = build_synthetic_vehicle_lease_evaluation_artifact()
    building_lease_artifact = build_synthetic_building_lease_evaluation_artifact()
    enterprise_lease_artifact = build_synthetic_enterprise_lease_evaluation_artifact()
    leasing_artifact = build_synthetic_leasing_evaluation_artifact()
    residential_lease_artifact = build_synthetic_residential_lease_evaluation_artifact()
    gratuitous_use_artifact = build_synthetic_gratuitous_use_evaluation_artifact()
    work_contract_artifact = build_synthetic_work_contract_evaluation_artifact()
    consumer_work_artifact = build_synthetic_consumer_work_evaluation_artifact()
    construction_contract_artifact = build_synthetic_construction_contract_evaluation_artifact()
    design_work_artifact = build_synthetic_design_work_evaluation_artifact()
    state_work_artifact = build_synthetic_state_work_evaluation_artifact()
    research_work_artifact = build_synthetic_research_work_evaluation_artifact()
    paid_services_artifact = build_synthetic_paid_services_evaluation_artifact()
    carriage_artifact = build_synthetic_carriage_evaluation_artifact()
    forwarding_artifact = build_synthetic_forwarding_evaluation_artifact()
    loan_artifact = build_synthetic_loan_evaluation_artifact()
    credit_artifact = build_synthetic_credit_evaluation_artifact()
    commercial_credit_artifact = build_synthetic_commercial_credit_evaluation_artifact()
    factoring_artifact = build_synthetic_factoring_evaluation_artifact()
    bank_deposit_artifact = build_synthetic_bank_deposit_evaluation_artifact()
    bank_account_artifact = build_synthetic_bank_account_evaluation_artifact()
    settlements_artifact = build_synthetic_settlements_evaluation_artifact()
    storage_artifact = build_synthetic_storage_evaluation_artifact()
    warehouse_storage_artifact = build_synthetic_warehouse_storage_evaluation_artifact()
    special_storage_artifact = build_synthetic_special_storage_evaluation_artifact()
    insurance_artifact = build_synthetic_insurance_evaluation_artifact()
    insurance_settlement_artifact = build_synthetic_insurance_settlement_evaluation_artifact()
    mandate_artifact = build_synthetic_mandate_evaluation_artifact()
    negotiorum_gestio_artifact = build_synthetic_negotiorum_gestio_evaluation_artifact()
    commission_artifact = build_synthetic_commission_evaluation_artifact()
    agency_artifact = build_synthetic_agency_evaluation_artifact()
    property_rights_artifact = build_synthetic_property_rights_evaluation_artifact()
    representation_artifact = build_synthetic_representation_evaluation_artifact()
    general_effects_artifact = build_synthetic_general_effects_evaluation_artifact()
    unjust_enrichment_artifact = build_synthetic_unjust_enrichment_evaluation_artifact()
    moral_harm_artifact = build_synthetic_moral_harm_evaluation_artifact()
    product_liability_artifact = build_synthetic_product_liability_evaluation_artifact()
    tort_life_health_artifact = build_synthetic_tort_life_health_evaluation_artifact()
    tort_general_artifact = build_synthetic_tort_general_evaluation_artifact()
    games_artifact = build_synthetic_games_evaluation_artifact()
    public_promise_artifact = build_synthetic_public_promise_evaluation_artifact()
    partnership_artifact = build_synthetic_partnership_evaluation_artifact()
    franchise_artifact = build_synthetic_franchise_evaluation_artifact()
    trust_management_artifact = build_synthetic_trust_management_evaluation_artifact()
    termination_artifact = build_synthetic_termination_evaluation_artifact()
    invalidity_artifact = build_synthetic_invalidity_evaluation_artifact()
    security_artifact = build_synthetic_security_evaluation_artifact()
    dynamics_artifact = build_synthetic_obligation_dynamics_evaluation_artifact()
    performance_remedies_artifact = build_synthetic_performance_remedies_evaluation_artifact()
    sale_artifact = build_synthetic_sale_evaluation_artifact()
    supply_artifact = build_synthetic_supply_evaluation_artifact()
    pilot_rehearsal_artifact = build_synthetic_pilot_rehearsal_artifact()

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
                "src/causa/institutional/contracts/temporal_effect.py",
                "docs/contract-temporal-effect-spec.md",
                "src/causa/institutional/contracts/limitation.py",
                "docs/contract-limitation-spec.md",
                "src/causa/institutional/contracts/interpretation.py",
                "docs/contract-interpretation-spec.md",
                "src/causa/institutional/contracts/form.py",
                "docs/contract-form-spec.md",
                "src/causa/institutional/contracts/preliminary.py",
                "docs/contract-preliminary-spec.md",
                "src/causa/institutional/contracts/third_party.py",
                "docs/contract-third-party-spec.md",
                "src/causa/institutional/contracts/public_contract.py",
                "docs/contract-public-spec.md",
                "src/causa/institutional/contracts/adhesion.py",
                "docs/contract-adhesion-spec.md",
                "src/causa/institutional/contracts/representations.py",
                "docs/contract-representations-spec.md",
                "src/causa/institutional/contracts/precontractual.py",
                "docs/contract-precontractual-spec.md",
                "src/causa/institutional/contracts/option.py",
                "docs/contract-option-spec.md",
                "src/causa/institutional/contracts/framework.py",
                "docs/contract-framework-spec.md",
                "src/causa/institutional/contracts/freedom.py",
                "docs/contract-freedom-spec.md",
                "src/causa/institutional/contracts/procedure.py",
                "docs/contract-procedure-spec.md",
                "src/causa/institutional/contracts/general_obligations.py",
                "docs/contract-general-obligations-spec.md",
                "src/causa/institutional/contracts/retail_sale.py",
                "docs/contract-retail-sale-spec.md",
                "src/causa/institutional/contracts/state_supply.py",
                "docs/contract-state-supply-spec.md",
                "src/causa/institutional/contracts/contractation.py",
                "docs/contract-contractation-spec.md",
                "src/causa/institutional/contracts/energy_supply.py",
                "docs/contract-energy-supply-spec.md",
                "src/causa/institutional/contracts/real_estate_sale.py",
                "docs/contract-real-estate-sale-spec.md",
                "src/causa/institutional/contracts/enterprise_sale.py",
                "docs/contract-enterprise-sale-spec.md",
                "src/causa/institutional/contracts/barter.py",
                "docs/contract-barter-spec.md",
                "src/causa/institutional/contracts/gift.py",
                "docs/contract-gift-spec.md",
                "src/causa/institutional/contracts/annuity.py",
                "docs/contract-annuity-spec.md",
                "src/causa/institutional/contracts/lease.py",
                "docs/contract-lease-spec.md",
                "src/causa/institutional/contracts/rental.py",
                "docs/contract-rental-spec.md",
                "src/causa/institutional/contracts/vehicle_lease.py",
                "docs/contract-vehicle-lease-spec.md",
                "src/causa/institutional/contracts/building_lease.py",
                "docs/contract-building-lease-spec.md",
                "src/causa/institutional/contracts/enterprise_lease.py",
                "docs/contract-enterprise-lease-spec.md",
                "src/causa/institutional/contracts/leasing.py",
                "docs/contract-leasing-spec.md",
                "src/causa/institutional/contracts/residential_lease.py",
                "docs/contract-residential-lease-spec.md",
                "src/causa/institutional/contracts/gratuitous_use.py",
                "docs/contract-gratuitous-use-spec.md",
                "src/causa/institutional/contracts/work_contract.py",
                "docs/contract-work-contract-spec.md",
                "src/causa/institutional/contracts/consumer_work.py",
                "docs/contract-consumer-work-spec.md",
                "src/causa/institutional/contracts/construction_contract.py",
                "docs/contract-construction-contract-spec.md",
                "src/causa/institutional/contracts/design_work.py",
                "docs/contract-design-work-spec.md",
                "src/causa/institutional/contracts/state_work.py",
                "docs/contract-state-work-spec.md",
                "src/causa/institutional/contracts/research_work.py",
                "docs/contract-research-work-spec.md",
                "src/causa/institutional/contracts/paid_services.py",
                "docs/contract-paid-services-spec.md",
                "src/causa/institutional/contracts/carriage.py",
                "docs/contract-carriage-spec.md",
                "src/causa/institutional/contracts/forwarding.py",
                "docs/contract-forwarding-spec.md",
                "src/causa/institutional/contracts/loan.py",
                "docs/contract-loan-spec.md",
                "src/causa/institutional/contracts/credit.py",
                "docs/contract-credit-spec.md",
                "src/causa/institutional/contracts/commercial_credit.py",
                "docs/contract-commercial-credit-spec.md",
                "src/causa/institutional/contracts/factoring.py",
                "docs/contract-factoring-spec.md",
                "src/causa/institutional/contracts/bank_deposit.py",
                "docs/contract-bank-deposit-spec.md",
                "src/causa/institutional/contracts/bank_account.py",
                "docs/contract-bank-account-spec.md",
                "src/causa/institutional/contracts/settlements.py",
                "docs/contract-settlements-spec.md",
                "src/causa/institutional/contracts/storage.py",
                "docs/contract-storage-spec.md",
                "src/causa/institutional/contracts/warehouse_storage.py",
                "docs/contract-warehouse-storage-spec.md",
                "src/causa/institutional/contracts/special_storage.py",
                "docs/contract-special-storage-spec.md",
                "src/causa/institutional/contracts/insurance.py",
                "docs/contract-insurance-spec.md",
                "src/causa/institutional/contracts/insurance_settlement.py",
                "docs/contract-insurance-settlement-spec.md",
                "src/causa/institutional/contracts/mandate.py",
                "docs/contract-mandate-spec.md",
                "src/causa/institutional/contracts/negotiorum_gestio.py",
                "docs/contract-negotiorum-gestio-spec.md",
                "src/causa/institutional/contracts/commission.py",
                "docs/contract-commission-spec.md",
                "src/causa/institutional/contracts/agency.py",
                "docs/contract-agency-spec.md",
                "src/causa/institutional/contracts/property_rights.py",
                "docs/contract-property-rights-spec.md",
                "src/causa/institutional/contracts/representation.py",
                "docs/contract-representation-spec.md",
                "src/causa/institutional/contracts/general_effects.py",
                "docs/contract-general-effects-spec.md",
                "src/causa/institutional/contracts/unjust_enrichment.py",
                "docs/contract-unjust-enrichment-spec.md",
                "src/causa/institutional/contracts/moral_harm.py",
                "docs/contract-moral-harm-spec.md",
                "src/causa/institutional/contracts/product_liability.py",
                "docs/contract-product-liability-spec.md",
                "src/causa/institutional/contracts/tort_life_health.py",
                "docs/contract-tort-life-health-spec.md",
                "src/causa/institutional/contracts/tort_general.py",
                "docs/contract-tort-general-spec.md",
                "src/causa/institutional/contracts/games.py",
                "docs/contract-games-spec.md",
                "src/causa/institutional/contracts/public_promise.py",
                "docs/contract-public-promise-spec.md",
                "src/causa/institutional/contracts/partnership.py",
                "docs/contract-partnership-spec.md",
                "src/causa/institutional/contracts/franchise.py",
                "docs/contract-franchise-spec.md",
                "src/causa/institutional/contracts/trust_management.py",
                "docs/contract-trust-management-spec.md",
                "src/causa/institutional/contracts/invalidity.py",
                "docs/contract-invalidity-spec.md",
                "src/causa/institutional/contracts/security.py",
                "docs/contract-security-spec.md",
                "src/causa/institutional/contracts/obligation_dynamics.py",
                "docs/contract-obligation-dynamics-spec.md",
                "src/causa/institutional/contracts/performance_remedies.py",
                "docs/contract-performance-remedies-spec.md",
                "src/causa/institutional/contracts/sale.py",
                "docs/contract-sale-spec.md",
                "src/causa/institutional/contracts/supply.py",
                "docs/contract-supply-spec.md",
                "src/causa/institutional/contracts/termination.py",
                "docs/contract-change-termination-spec.md",
                "src/causa/institutional/contracts/liability.py",
                "docs/contract-liability-spec.md",
                "examples/synthetic_counterfactual_evaluation_report.json",
                "examples/synthetic_liability_evaluation_report.json",
                "examples/synthetic_formation_evaluation_report.json",
                "examples/synthetic_temporal_effect_evaluation_report.json",
                "examples/synthetic_limitation_evaluation_report.json",
                "examples/synthetic_interpretation_evaluation_report.json",
                "examples/synthetic_form_evaluation_report.json",
                "examples/synthetic_preliminary_evaluation_report.json",
                "examples/synthetic_third_party_evaluation_report.json",
                "examples/synthetic_public_contract_evaluation_report.json",
                "examples/synthetic_adhesion_evaluation_report.json",
                "examples/synthetic_representations_evaluation_report.json",
                "examples/synthetic_precontractual_evaluation_report.json",
                "examples/synthetic_option_evaluation_report.json",
                "examples/synthetic_framework_evaluation_report.json",
                "examples/synthetic_freedom_evaluation_report.json",
                "examples/synthetic_procedure_evaluation_report.json",
                "examples/synthetic_general_obligations_evaluation_report.json",
                "examples/synthetic_retail_sale_evaluation_report.json",
                "examples/synthetic_state_supply_evaluation_report.json",
                "examples/synthetic_contractation_evaluation_report.json",
                "examples/synthetic_energy_supply_evaluation_report.json",
                "examples/synthetic_real_estate_sale_evaluation_report.json",
                "examples/synthetic_enterprise_sale_evaluation_report.json",
                "examples/synthetic_barter_evaluation_report.json",
                "examples/synthetic_gift_evaluation_report.json",
                "examples/synthetic_annuity_evaluation_report.json",
                "examples/synthetic_lease_evaluation_report.json",
                "examples/synthetic_rental_evaluation_report.json",
                "examples/synthetic_vehicle_lease_evaluation_report.json",
                "examples/synthetic_building_lease_evaluation_report.json",
                "examples/synthetic_enterprise_lease_evaluation_report.json",
                "examples/synthetic_leasing_evaluation_report.json",
                "examples/synthetic_residential_lease_evaluation_report.json",
                "examples/synthetic_gratuitous_use_evaluation_report.json",
                "examples/synthetic_work_contract_evaluation_report.json",
                "examples/synthetic_consumer_work_evaluation_report.json",
                "examples/synthetic_construction_contract_evaluation_report.json",
                "examples/synthetic_design_work_evaluation_report.json",
                "examples/synthetic_state_work_evaluation_report.json",
                "examples/synthetic_research_work_evaluation_report.json",
                "examples/synthetic_paid_services_evaluation_report.json",
                "examples/synthetic_carriage_evaluation_report.json",
                "examples/synthetic_forwarding_evaluation_report.json",
                "examples/synthetic_loan_evaluation_report.json",
                "examples/synthetic_credit_evaluation_report.json",
                "examples/synthetic_commercial_credit_evaluation_report.json",
                "examples/synthetic_factoring_evaluation_report.json",
                "examples/synthetic_bank_deposit_evaluation_report.json",
                "examples/synthetic_bank_account_evaluation_report.json",
                "examples/synthetic_settlements_evaluation_report.json",
                "examples/synthetic_storage_evaluation_report.json",
                "examples/synthetic_warehouse_storage_evaluation_report.json",
                "examples/synthetic_special_storage_evaluation_report.json",
                "examples/synthetic_insurance_evaluation_report.json",
                "examples/synthetic_insurance_settlement_evaluation_report.json",
                "examples/synthetic_mandate_evaluation_report.json",
                "examples/synthetic_negotiorum_gestio_evaluation_report.json",
                "examples/synthetic_commission_evaluation_report.json",
                "examples/synthetic_agency_evaluation_report.json",
                "examples/synthetic_property_rights_evaluation_report.json",
                "examples/synthetic_representation_evaluation_report.json",
                "examples/synthetic_general_effects_evaluation_report.json",
                "examples/synthetic_unjust_enrichment_evaluation_report.json",
                "examples/synthetic_moral_harm_evaluation_report.json",
                "examples/synthetic_product_liability_evaluation_report.json",
                "examples/synthetic_tort_life_health_evaluation_report.json",
                "examples/synthetic_tort_general_evaluation_report.json",
                "examples/synthetic_games_evaluation_report.json",
                "examples/synthetic_public_promise_evaluation_report.json",
                "examples/synthetic_partnership_evaluation_report.json",
                "examples/synthetic_franchise_evaluation_report.json",
                "examples/synthetic_trust_management_evaluation_report.json",
                "examples/synthetic_invalidity_evaluation_report.json",
                "examples/synthetic_security_evaluation_report.json",
                "examples/synthetic_obligation_dynamics_evaluation_report.json",
                "examples/synthetic_performance_remedies_evaluation_report.json",
                "examples/synthetic_sale_articles_454_491_report.json",
                "examples/synthetic_supply_articles_506_524_report.json",
                "examples/synthetic_termination_evaluation_report.json",
                *(
                    f"examples/migrations/contracts-ru-v0-{version}-to-0.62.0-migration-report.json"
                    for version in (
                        "0.1.0",
                        "0.3.0",
                        "0.4.0",
                        *(f"0.{minor}.0" for minor in range(5, 62)),
                    )
                ),
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
                temporal_effect_artifact.benchmark_report.id,
                temporal_effect_artifact.red_team_report.id,
                limitation_artifact.benchmark_report.id,
                limitation_artifact.red_team_report.id,
                interpretation_artifact.benchmark_report.id,
                interpretation_artifact.red_team_report.id,
                form_artifact.benchmark_report.id,
                form_artifact.red_team_report.id,
                preliminary_artifact.benchmark_report.id,
                preliminary_artifact.red_team_report.id,
                third_party_artifact.benchmark_report.id,
                third_party_artifact.red_team_report.id,
                public_contract_artifact.benchmark_report.id,
                public_contract_artifact.red_team_report.id,
                adhesion_artifact.benchmark_report.id,
                adhesion_artifact.red_team_report.id,
                representations_artifact.benchmark_report.id,
                representations_artifact.red_team_report.id,
                precontractual_artifact.benchmark_report.id,
                precontractual_artifact.red_team_report.id,
                option_artifact.benchmark_report.id,
                option_artifact.red_team_report.id,
                framework_artifact.benchmark_report.id,
                framework_artifact.red_team_report.id,
                freedom_artifact.benchmark_report.id,
                freedom_artifact.red_team_report.id,
                procedure_artifact.benchmark_report.id,
                procedure_artifact.red_team_report.id,
                general_obligations_artifact.benchmark_report.id,
                general_obligations_artifact.red_team_report.id,
                retail_sale_artifact.benchmark_report.id,
                retail_sale_artifact.red_team_report.id,
                state_supply_artifact.benchmark_report.id,
                state_supply_artifact.red_team_report.id,
                contractation_artifact.benchmark_report.id,
                contractation_artifact.red_team_report.id,
                energy_supply_artifact.benchmark_report.id,
                energy_supply_artifact.red_team_report.id,
                real_estate_sale_artifact.benchmark_report.id,
                real_estate_sale_artifact.red_team_report.id,
                enterprise_sale_artifact.benchmark_report.id,
                enterprise_sale_artifact.red_team_report.id,
                barter_artifact.benchmark_report.id,
                barter_artifact.red_team_report.id,
                gift_artifact.benchmark_report.id,
                gift_artifact.red_team_report.id,
                annuity_artifact.benchmark_report.id,
                annuity_artifact.red_team_report.id,
                lease_artifact.benchmark_report.id,
                lease_artifact.red_team_report.id,
                rental_artifact.benchmark_report.id,
                rental_artifact.red_team_report.id,
                vehicle_lease_artifact.benchmark_report.id,
                vehicle_lease_artifact.red_team_report.id,
                building_lease_artifact.benchmark_report.id,
                building_lease_artifact.red_team_report.id,
                enterprise_lease_artifact.benchmark_report.id,
                enterprise_lease_artifact.red_team_report.id,
                leasing_artifact.benchmark_report.id,
                leasing_artifact.red_team_report.id,
                residential_lease_artifact.benchmark_report.id,
                residential_lease_artifact.red_team_report.id,
                gratuitous_use_artifact.benchmark_report.id,
                gratuitous_use_artifact.red_team_report.id,
                work_contract_artifact.benchmark_report.id,
                work_contract_artifact.red_team_report.id,
                consumer_work_artifact.benchmark_report.id,
                consumer_work_artifact.red_team_report.id,
                construction_contract_artifact.benchmark_report.id,
                construction_contract_artifact.red_team_report.id,
                design_work_artifact.benchmark_report.id,
                design_work_artifact.red_team_report.id,
                state_work_artifact.benchmark_report.id,
                state_work_artifact.red_team_report.id,
                research_work_artifact.benchmark_report.id,
                research_work_artifact.red_team_report.id,
                paid_services_artifact.benchmark_report.id,
                paid_services_artifact.red_team_report.id,
                carriage_artifact.benchmark_report.id,
                carriage_artifact.red_team_report.id,
                forwarding_artifact.benchmark_report.id,
                forwarding_artifact.red_team_report.id,
                loan_artifact.benchmark_report.id,
                loan_artifact.red_team_report.id,
                credit_artifact.benchmark_report.id,
                credit_artifact.red_team_report.id,
                commercial_credit_artifact.benchmark_report.id,
                commercial_credit_artifact.red_team_report.id,
                factoring_artifact.benchmark_report.id,
                factoring_artifact.red_team_report.id,
                bank_deposit_artifact.benchmark_report.id,
                bank_deposit_artifact.red_team_report.id,
                bank_account_artifact.benchmark_report.id,
                bank_account_artifact.red_team_report.id,
                settlements_artifact.benchmark_report.id,
                settlements_artifact.red_team_report.id,
                storage_artifact.benchmark_report.id,
                storage_artifact.red_team_report.id,
                warehouse_storage_artifact.benchmark_report.id,
                warehouse_storage_artifact.red_team_report.id,
                special_storage_artifact.benchmark_report.id,
                special_storage_artifact.red_team_report.id,
                insurance_artifact.benchmark_report.id,
                insurance_artifact.red_team_report.id,
                insurance_settlement_artifact.benchmark_report.id,
                insurance_settlement_artifact.red_team_report.id,
                mandate_artifact.benchmark_report.id,
                mandate_artifact.red_team_report.id,
                negotiorum_gestio_artifact.benchmark_report.id,
                negotiorum_gestio_artifact.red_team_report.id,
                commission_artifact.benchmark_report.id,
                commission_artifact.red_team_report.id,
                agency_artifact.benchmark_report.id,
                agency_artifact.red_team_report.id,
                property_rights_artifact.benchmark_report.id,
                property_rights_artifact.red_team_report.id,
                representation_artifact.benchmark_report.id,
                representation_artifact.red_team_report.id,
                general_effects_artifact.benchmark_report.id,
                general_effects_artifact.red_team_report.id,
                unjust_enrichment_artifact.benchmark_report.id,
                unjust_enrichment_artifact.red_team_report.id,
                moral_harm_artifact.benchmark_report.id,
                moral_harm_artifact.red_team_report.id,
                product_liability_artifact.benchmark_report.id,
                product_liability_artifact.red_team_report.id,
                tort_life_health_artifact.benchmark_report.id,
                tort_life_health_artifact.red_team_report.id,
                tort_general_artifact.benchmark_report.id,
                tort_general_artifact.red_team_report.id,
                games_artifact.benchmark_report.id,
                games_artifact.red_team_report.id,
                public_promise_artifact.benchmark_report.id,
                public_promise_artifact.red_team_report.id,
                partnership_artifact.benchmark_report.id,
                partnership_artifact.red_team_report.id,
                franchise_artifact.benchmark_report.id,
                franchise_artifact.red_team_report.id,
                trust_management_artifact.benchmark_report.id,
                trust_management_artifact.red_team_report.id,
                invalidity_artifact.benchmark_report.id,
                invalidity_artifact.red_team_report.id,
                security_artifact.benchmark_report.id,
                security_artifact.red_team_report.id,
                dynamics_artifact.benchmark_report.id,
                dynamics_artifact.red_team_report.id,
                performance_remedies_artifact.benchmark_report.id,
                performance_remedies_artifact.red_team_report.id,
                sale_artifact.benchmark_report.id,
                sale_artifact.red_team_report.id,
                supply_artifact.benchmark_report.id,
                supply_artifact.red_team_report.id,
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
                "examples/synthetic_temporal_effect_evaluation_report.json",
                "examples/synthetic_limitation_evaluation_report.json",
                "examples/synthetic_interpretation_evaluation_report.json",
                "examples/synthetic_form_evaluation_report.json",
                "examples/synthetic_preliminary_evaluation_report.json",
                "examples/synthetic_third_party_evaluation_report.json",
                "examples/synthetic_public_contract_evaluation_report.json",
                "examples/synthetic_adhesion_evaluation_report.json",
                "examples/synthetic_representations_evaluation_report.json",
                "examples/synthetic_precontractual_evaluation_report.json",
                "examples/synthetic_option_evaluation_report.json",
                "examples/synthetic_framework_evaluation_report.json",
                "examples/synthetic_freedom_evaluation_report.json",
                "examples/synthetic_procedure_evaluation_report.json",
                "examples/synthetic_general_obligations_evaluation_report.json",
                "examples/synthetic_retail_sale_evaluation_report.json",
                "examples/synthetic_state_supply_evaluation_report.json",
                "examples/synthetic_contractation_evaluation_report.json",
                "examples/synthetic_energy_supply_evaluation_report.json",
                "examples/synthetic_real_estate_sale_evaluation_report.json",
                "examples/synthetic_enterprise_sale_evaluation_report.json",
                "examples/synthetic_barter_evaluation_report.json",
                "examples/synthetic_gift_evaluation_report.json",
                "examples/synthetic_annuity_evaluation_report.json",
                "examples/synthetic_lease_evaluation_report.json",
                "examples/synthetic_rental_evaluation_report.json",
                "examples/synthetic_vehicle_lease_evaluation_report.json",
                "examples/synthetic_building_lease_evaluation_report.json",
                "examples/synthetic_enterprise_lease_evaluation_report.json",
                "examples/synthetic_leasing_evaluation_report.json",
                "examples/synthetic_residential_lease_evaluation_report.json",
                "examples/synthetic_gratuitous_use_evaluation_report.json",
                "examples/synthetic_work_contract_evaluation_report.json",
                "examples/synthetic_consumer_work_evaluation_report.json",
                "examples/synthetic_construction_contract_evaluation_report.json",
                "examples/synthetic_design_work_evaluation_report.json",
                "examples/synthetic_state_work_evaluation_report.json",
                "examples/synthetic_research_work_evaluation_report.json",
                "examples/synthetic_paid_services_evaluation_report.json",
                "examples/synthetic_carriage_evaluation_report.json",
                "examples/synthetic_forwarding_evaluation_report.json",
                "examples/synthetic_loan_evaluation_report.json",
                "examples/synthetic_credit_evaluation_report.json",
                "examples/synthetic_commercial_credit_evaluation_report.json",
                "examples/synthetic_factoring_evaluation_report.json",
                "examples/synthetic_bank_deposit_evaluation_report.json",
                "examples/synthetic_bank_account_evaluation_report.json",
                "examples/synthetic_settlements_evaluation_report.json",
                "examples/synthetic_storage_evaluation_report.json",
                "examples/synthetic_warehouse_storage_evaluation_report.json",
                "examples/synthetic_special_storage_evaluation_report.json",
                "examples/synthetic_insurance_evaluation_report.json",
                "examples/synthetic_insurance_settlement_evaluation_report.json",
                "examples/synthetic_mandate_evaluation_report.json",
                "examples/synthetic_negotiorum_gestio_evaluation_report.json",
                "examples/synthetic_commission_evaluation_report.json",
                "examples/synthetic_agency_evaluation_report.json",
                "examples/synthetic_property_rights_evaluation_report.json",
                "examples/synthetic_representation_evaluation_report.json",
                "examples/synthetic_general_effects_evaluation_report.json",
                "examples/synthetic_unjust_enrichment_evaluation_report.json",
                "examples/synthetic_moral_harm_evaluation_report.json",
                "examples/synthetic_product_liability_evaluation_report.json",
                "examples/synthetic_tort_life_health_evaluation_report.json",
                "examples/synthetic_tort_general_evaluation_report.json",
                "examples/synthetic_games_evaluation_report.json",
                "examples/synthetic_public_promise_evaluation_report.json",
                "examples/synthetic_partnership_evaluation_report.json",
                "examples/synthetic_franchise_evaluation_report.json",
                "examples/synthetic_trust_management_evaluation_report.json",
                "examples/synthetic_invalidity_evaluation_report.json",
                "examples/synthetic_security_evaluation_report.json",
                "examples/synthetic_obligation_dynamics_evaluation_report.json",
                "examples/synthetic_performance_remedies_evaluation_report.json",
                "examples/synthetic_sale_articles_454_491_report.json",
                "examples/synthetic_supply_articles_506_524_report.json",
                "examples/synthetic_termination_evaluation_report.json",
                pipeline.id,
            ],
            remaining_work=["Расширить синтетический набор источников и перечень пилотных задач."],
        ),
        ReadinessItem(
            id="ws10-pilot-admission",
            title="Контур допуска и минимизации пилотных данных",
            status=PipelineStepStatus.WARNING,
            evidence_refs=[
                "src/causa/pilot.py",
                "src/causa/institutional/contracts/pilot_fixtures.py",
                "src/causa/institutional/contracts/pilot_evaluation.py",
                "src/causa/institutional/contracts/synthetic_pilot.py",
                "docs/pilot-data-admission-spec.md",
                "examples/synthetic_pilot_rehearsal_report.json",
                # Допуск связывает синтетическую репетицию, gate-решение и наблюдения полезности.
                pilot_rehearsal_artifact.gate_decision.id,
                pilot_rehearsal_artifact.benchmark_report.id,
                pilot_rehearsal_artifact.red_team_report.id,
                pilot_rehearsal_artifact.utility_report.id,
            ],
            remaining_work=[
                # Синтетическая репетиция подтверждает архитектуру допуска, но не заменяет реальный пилот.
                "Получить независимые privacy, legal, security и domain-согласования реального кейса.",
                "Собрать несинтетические наблюдения полезности только после одобренного gate v1.",
                "Сохранять ready_for_production=false до подтвержденного пилота на данных заказчика.",
            ],
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
