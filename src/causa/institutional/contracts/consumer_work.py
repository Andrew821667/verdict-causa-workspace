from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


CONSUMER_WORK_EVIDENCE_SCHEMA_VERSION = "contracts.consumer-work-evidence.v0"
CONSUMER_WORK_MAPPING_VERSION = "contracts-reviewed-consumer-work-to-facts-v0"
CONSUMER_WORK_MODEL_VERSION = "contracts-consumer-work-articles-730-739-v0"


class ConsumerWorkEvidencePredicate(str, Enum):
    # Понятие бытового подряда и права заказчика (статьи 730 и 731 ГК РФ).
    WORK_FOR_PERSONAL_CONSUMER_NEEDS = "work_for_personal_consumer_needs"
    ADDITIONAL_WORK_IMPOSED_WITHOUT_CONSENT = "additional_work_imposed_without_consent"
    WITHDRAWAL_RIGHT_BEFORE_DELIVERY_DENIED = "withdrawal_right_before_delivery_denied"
    # Информация о работе и материал подрядчика (статьи 732 и 733 ГК РФ).
    CONSUMER_INFORMATION_NOT_PROVIDED = "consumer_information_not_provided"
    CONTRACTOR_MATERIAL_DEFECTIVE = "contractor_material_defective"
    # Цена, оплата и сведения об эксплуатации (статьи 735 и 736 ГК РФ).
    PAYMENT_DEMANDED_BEFORE_ACCEPTANCE_WITHOUT_CONSENT = (
        "payment_demanded_before_acceptance_without_consent"
    )
    OPERATION_INFORMATION_NOT_PROVIDED = "operation_information_not_provided"
    # Недостатки результата работы и десятилетний срок (статья 737 ГК РФ).
    WORK_RESULT_HAS_SIGNIFICANT_DEFECT = "work_result_has_significant_defect"
    SIGNIFICANT_DEFECT_FOUND_WITHIN_TEN_YEARS = "significant_defect_found_within_ten_years"
    # Неявка заказчика за результатом работы (статья 738 ГК РФ).
    RESULT_SOLD_WITHOUT_TWO_MONTH_NOTICE = "result_sold_without_two_month_notice"


REQUIRED_CONSUMER_WORK_PREDICATES = frozenset(ConsumerWorkEvidencePredicate)


class ConsumerWorkEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ConsumerWorkEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedConsumerWorkEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CONSUMER_WORK_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ConsumerWorkEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedConsumerWorkEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Consumer-work evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Consumer-work evidence contains duplicate legal source refs.")
        return self


class ConsumerWorkFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    work_for_personal_consumer_needs: bool
    additional_work_imposed_without_consent: bool
    withdrawal_right_before_delivery_denied: bool
    consumer_information_not_provided: bool
    contractor_material_defective: bool
    payment_demanded_before_acceptance_without_consent: bool
    operation_information_not_provided: bool
    work_result_has_significant_defect: bool
    significant_defect_found_within_ten_years: bool
    result_sold_without_two_month_notice: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ConsumerWorkFactSet":
        if (
            self.significant_defect_found_within_ten_years
            and not self.work_result_has_significant_defect
        ):
            raise ValueError(
                "Обнаружение существенного недостатка в течение десяти лет относится только к "
                "случаю, когда существенный недостаток результата работы установлен."
            )
        if (
            self.withdrawal_right_before_delivery_denied
            and not self.work_for_personal_consumer_needs
        ):
            raise ValueError(
                "Отказ в праве прекратить договор до сдачи работы относится только к договору "
                "бытового подряда."
            )
        return self


class ConsumerWorkFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ConsumerWorkEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ConsumerWorkFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ConsumerWorkFactProvenance] = Field(default_factory=list)


class ConsumerWorkConstraintSet(BaseModel):
    id: str
    model_version: str = CONSUMER_WORK_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ConsumerWorkEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    consumer_work_qualified: bool
    imposed_additional_work_not_payable: bool
    withdrawal_right_denied: bool
    consumer_information_duty_breached: bool
    contractor_material_liability: bool
    payment_order_breached: bool
    operation_information_duty_breached: bool
    significant_defect_remedy_available: bool
    ten_year_claim_available: bool
    sale_notice_period_breached: bool
    requires_human_consumer_work_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_consumer_work_evidence(
    evidence: ReviewedConsumerWorkEvidence,
) -> ConsumerWorkEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Consumer-work evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Consumer-work evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_CONSUMER_WORK_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed consumer-work evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_CONSUMER_WORK_PREDICATES
    }
    return ConsumerWorkEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CONSUMER_WORK_MAPPING_VERSION,
        facts=ConsumerWorkFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ConsumerWorkFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_CONSUMER_WORK_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_consumer_work_constraint_set(
    mapping: ConsumerWorkEvidenceMappingResult,
) -> ConsumerWorkConstraintSet:
    return ConsumerWorkConstraintSet(
        id=f"consumer-work-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "consumer_work_qualified == work_for_personal_consumer_needs",
            "imposed_additional_work_not_payable == consumer_work_qualified AND additional_work_imposed_without_consent",
            "withdrawal_right_denied == consumer_work_qualified AND withdrawal_right_before_delivery_denied",
            "consumer_information_duty_breached == consumer_work_qualified AND consumer_information_not_provided",
            "contractor_material_liability == consumer_work_qualified AND contractor_material_defective",
            "payment_order_breached == consumer_work_qualified AND payment_demanded_before_acceptance_without_consent",
            "operation_information_duty_breached == consumer_work_qualified AND operation_information_not_provided",
            "significant_defect_remedy_available == consumer_work_qualified AND work_result_has_significant_defect",
            "ten_year_claim_available == consumer_work_qualified AND work_result_has_significant_defect AND significant_defect_found_within_ten_years",
            "sale_notice_period_breached == consumer_work_qualified AND result_sold_without_two_month_notice",
            "requires_human_consumer_work_assessment == imposed_additional_work_not_payable OR withdrawal_right_denied OR consumer_information_duty_breached OR contractor_material_liability OR payment_order_breached OR operation_information_duty_breached OR significant_defect_remedy_available OR sale_notice_period_breached",
        ],
    )


def evaluate_consumer_work_constraints(
    constraint_set: ConsumerWorkConstraintSet,
    facts: ConsumerWorkFactSet,
) -> ConsumerWorkEvaluation:
    variables = {field_name: Bool(field_name) for field_name in ConsumerWorkFactSet.model_fields}
    consumer_work_qualified = Bool("consumer_work_qualified")
    imposed_additional_work_not_payable = Bool("imposed_additional_work_not_payable")
    withdrawal_right_denied = Bool("withdrawal_right_denied")
    consumer_information_duty_breached = Bool("consumer_information_duty_breached")
    contractor_material_liability = Bool("contractor_material_liability")
    payment_order_breached = Bool("payment_order_breached")
    operation_information_duty_breached = Bool("operation_information_duty_breached")
    significant_defect_remedy_available = Bool("significant_defect_remedy_available")
    ten_year_claim_available = Bool("ten_year_claim_available")
    sale_notice_period_breached = Bool("sale_notice_period_breached")
    requires_human_consumer_work_assessment = Bool("requires_human_consumer_work_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(consumer_work_qualified == variables["work_for_personal_consumer_needs"])
    solver.add(
        imposed_additional_work_not_payable
        == And(consumer_work_qualified, variables["additional_work_imposed_without_consent"])
    )
    solver.add(
        withdrawal_right_denied
        == And(consumer_work_qualified, variables["withdrawal_right_before_delivery_denied"])
    )
    solver.add(
        consumer_information_duty_breached
        == And(consumer_work_qualified, variables["consumer_information_not_provided"])
    )
    solver.add(
        contractor_material_liability
        == And(consumer_work_qualified, variables["contractor_material_defective"])
    )
    solver.add(
        payment_order_breached
        == And(
            consumer_work_qualified,
            variables["payment_demanded_before_acceptance_without_consent"],
        )
    )
    solver.add(
        operation_information_duty_breached
        == And(consumer_work_qualified, variables["operation_information_not_provided"])
    )
    solver.add(
        significant_defect_remedy_available
        == And(consumer_work_qualified, variables["work_result_has_significant_defect"])
    )
    solver.add(
        ten_year_claim_available
        == And(
            consumer_work_qualified,
            variables["work_result_has_significant_defect"],
            variables["significant_defect_found_within_ten_years"],
        )
    )
    solver.add(
        sale_notice_period_breached
        == And(consumer_work_qualified, variables["result_sold_without_two_month_notice"])
    )
    solver.add(
        requires_human_consumer_work_assessment
        == Or(
            imposed_additional_work_not_payable,
            withdrawal_right_denied,
            consumer_information_duty_breached,
            contractor_material_liability,
            payment_order_breached,
            operation_information_duty_breached,
            significant_defect_remedy_available,
            sale_notice_period_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ConsumerWorkEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            consumer_work_qualified=False,
            imposed_additional_work_not_payable=False,
            withdrawal_right_denied=False,
            consumer_information_duty_breached=False,
            contractor_material_liability=False,
            payment_order_breached=False,
            operation_information_duty_breached=False,
            significant_defect_remedy_available=False,
            ten_year_claim_available=False,
            sale_notice_period_breached=False,
            requires_human_consumer_work_assessment=True,
            reasons_ru=["Набор фактов о бытовом подряде противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как бытовой подряд: подрядчик, осуществляющий "
            "соответствующую предпринимательскую деятельность, выполняет по заданию гражданина "
            "работу для удовлетворения бытовых или других личных потребностей заказчика "
            "(статья 730 ГК РФ)."
            if truth(consumer_work_qualified)
            else "Отношения не квалифицированы как договор бытового подряда."
        ),
    ]
    if truth(imposed_additional_work_not_payable):
        reasons_ru.append(
            "Подрядчик не вправе навязывать заказчику включение в договор бытового подряда "
            "дополнительной работы или услуги; заказчик вправе отказаться от их оплаты "
            "(статья 731 ГК РФ)."
        )
    if truth(withdrawal_right_denied):
        reasons_ru.append(
            "Заказчик вправе в любое время до сдачи ему работы отказаться от договора, уплатив "
            "часть цены пропорционально выполненной работе и возместив расходы подрядчика; "
            "условия, лишающие заказчика этого права, ничтожны (статья 731 ГК РФ)."
        )
    if truth(consumer_information_duty_breached):
        reasons_ru.append(
            "Подрядчик обязан до заключения договора сообщить заказчику необходимую и достоверную "
            "информацию о предлагаемой работе, её видах и особенностях, цене и форме оплаты "
            "(статья 732 ГК РФ)."
        )
    if truth(contractor_material_liability):
        reasons_ru.append(
            "Работа выполнена из недоброкачественного материала подрядчика; наступают "
            "последствия, предусмотренные для выполнения работы с недостатками "
            "(статьи 733 и 739 ГК РФ)."
        )
    if truth(payment_order_breached):
        reasons_ru.append(
            "Работа оплачивается заказчиком после её окончательной сдачи подрядчиком; с согласия "
            "заказчика работа может быть оплачена при заключении договора полностью или путём "
            "выдачи аванса (статья 735 ГК РФ)."
        )
    if truth(operation_information_duty_breached):
        reasons_ru.append(
            "При сдаче работы подрядчик обязан сообщить заказчику о требованиях, которые "
            "необходимо соблюдать для эффективного и безопасного использования результата, и о "
            "возможных последствиях их несоблюдения (статья 736 ГК РФ)."
        )
    if truth(significant_defect_remedy_available):
        reasons_ru.append(
            "Результат работы имеет существенный недостаток: заказчик вправе требовать его "
            "безвозмездного устранения либо возмещения расходов на устранение своими силами или "
            "третьим лицом (статья 737 ГК РФ)."
        )
    if truth(ten_year_claim_available):
        reasons_ru.append(
            "Существенный недостаток обнаружен по истечении гарантийного срока, но в пределах "
            "десяти лет с момента принятия результата работы, что сохраняет требование к "
            "подрядчику (статья 737 ГК РФ)."
        )
    if truth(sale_notice_period_breached):
        reasons_ru.append(
            "При неявке заказчика за результатом работы подрядчик вправе продать его только по "
            "истечении двух месяцев со дня письменного предупреждения заказчика "
            "(статья 738 ГК РФ)."
        )
    return ConsumerWorkEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        consumer_work_qualified=truth(consumer_work_qualified),
        imposed_additional_work_not_payable=truth(imposed_additional_work_not_payable),
        withdrawal_right_denied=truth(withdrawal_right_denied),
        consumer_information_duty_breached=truth(consumer_information_duty_breached),
        contractor_material_liability=truth(contractor_material_liability),
        payment_order_breached=truth(payment_order_breached),
        operation_information_duty_breached=truth(operation_information_duty_breached),
        significant_defect_remedy_available=truth(significant_defect_remedy_available),
        ten_year_claim_available=truth(ten_year_claim_available),
        sale_notice_period_breached=truth(sale_notice_period_breached),
        requires_human_consumer_work_assessment=truth(requires_human_consumer_work_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о бытовом подряде и не заменяет судебную "
            "оценку.",
            "Существенность недостатка, достоверность и полнота предоставленной информации и "
            "размер расходов заказчика оцениваются экспертом и судом (статьи 732, 737 и 739 "
            "ГК РФ).",
        ],
    )
