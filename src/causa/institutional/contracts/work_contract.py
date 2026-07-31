from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


WORK_CONTRACT_EVIDENCE_SCHEMA_VERSION = "contracts.work-contract-evidence.v0"
WORK_CONTRACT_MAPPING_VERSION = "contracts-reviewed-work-contract-to-facts-v0"
WORK_CONTRACT_MODEL_VERSION = "contracts-work-contract-articles-702-729-v0"


class WorkContractEvidencePredicate(str, Enum):
    # Понятие подряда и личное исполнение (статьи 702 и 706 ГК РФ).
    WORK_PERFORMED_AND_RESULT_DELIVERED_FOR_FEE = "work_performed_and_result_delivered_for_fee"
    SUBCONTRACTOR_ENGAGED_DESPITE_PERSONAL_DUTY = "subcontractor_engaged_despite_personal_duty"
    # Сроки, цена и смета (статьи 708 и 709 ГК РФ).
    START_OR_COMPLETION_TERM_NOT_AGREED = "start_or_completion_term_not_agreed"
    ESTIMATE_EXCEEDED_WITHOUT_TIMELY_NOTICE = "estimate_exceeded_without_timely_notice"
    # Материал заказчика и предупреждение о рисках (статьи 713 и 716 ГК РФ).
    CUSTOMER_MATERIAL_UNSUITABLE = "customer_material_unsuitable"
    CONTRACTOR_FAILED_TO_WARN_OF_RISK = "contractor_failed_to_warn_of_risk"
    # Качество работы и сроки обнаружения недостатков (статьи 721, 723 и 724 ГК РФ).
    WORK_RESULT_DEFECTIVE = "work_result_defective"
    DEFECT_FOUND_WITHIN_STATUTORY_PERIOD = "defect_found_within_statutory_period"
    # Приёмка и односторонний отказ заказчика (статьи 717 и 720 ГК РФ).
    ACCEPTANCE_AVOIDED_OR_INSPECTION_OMITTED = "acceptance_avoided_or_inspection_omitted"
    CUSTOMER_WITHDREW_BEFORE_COMPLETION_WITHOUT_PAYMENT = (
        "customer_withdrew_before_completion_without_payment"
    )


REQUIRED_WORK_CONTRACT_PREDICATES = frozenset(WorkContractEvidencePredicate)


class WorkContractEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: WorkContractEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedWorkContractEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = WORK_CONTRACT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[WorkContractEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedWorkContractEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Work-contract evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Work-contract evidence contains duplicate legal source refs.")
        return self


class WorkContractFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    work_performed_and_result_delivered_for_fee: bool
    subcontractor_engaged_despite_personal_duty: bool
    start_or_completion_term_not_agreed: bool
    estimate_exceeded_without_timely_notice: bool
    customer_material_unsuitable: bool
    contractor_failed_to_warn_of_risk: bool
    work_result_defective: bool
    defect_found_within_statutory_period: bool
    acceptance_avoided_or_inspection_omitted: bool
    customer_withdrew_before_completion_without_payment: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "WorkContractFactSet":
        if self.defect_found_within_statutory_period and not self.work_result_defective:
            raise ValueError(
                "Обнаружение недостатка в установленный срок относится только к случаю, когда "
                "недостаток результата работы установлен."
            )
        if (
            self.subcontractor_engaged_despite_personal_duty
            and not self.work_performed_and_result_delivered_for_fee
        ):
            raise ValueError(
                "Привлечение субподрядчика вопреки обязанности выполнить работу лично относится "
                "только к договору подряда."
            )
        return self


class WorkContractFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class WorkContractEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: WorkContractFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[WorkContractFactProvenance] = Field(default_factory=list)


class WorkContractConstraintSet(BaseModel):
    id: str
    model_version: str = WORK_CONTRACT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class WorkContractEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    work_contract_qualified: bool
    personal_performance_duty_breached: bool
    term_condition_not_agreed: bool
    estimate_notice_duty_breached: bool
    customer_material_liability: bool
    risk_warning_duty_breached: bool
    contractor_liable_for_defects: bool
    defect_claim_within_period: bool
    acceptance_duty_breached: bool
    withdrawal_compensation_due: bool
    requires_human_work_contract_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_work_contract_evidence(
    evidence: ReviewedWorkContractEvidence,
) -> WorkContractEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Work-contract evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Work-contract evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_WORK_CONTRACT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed work-contract evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_WORK_CONTRACT_PREDICATES
    }
    return WorkContractEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=WORK_CONTRACT_MAPPING_VERSION,
        facts=WorkContractFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            WorkContractFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_WORK_CONTRACT_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_work_contract_constraint_set(
    mapping: WorkContractEvidenceMappingResult,
) -> WorkContractConstraintSet:
    return WorkContractConstraintSet(
        id=f"work-contract-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "work_contract_qualified == work_performed_and_result_delivered_for_fee",
            "personal_performance_duty_breached == work_contract_qualified AND subcontractor_engaged_despite_personal_duty",
            "term_condition_not_agreed == work_contract_qualified AND start_or_completion_term_not_agreed",
            "estimate_notice_duty_breached == work_contract_qualified AND estimate_exceeded_without_timely_notice",
            "customer_material_liability == work_contract_qualified AND customer_material_unsuitable",
            "risk_warning_duty_breached == work_contract_qualified AND contractor_failed_to_warn_of_risk",
            "contractor_liable_for_defects == work_contract_qualified AND work_result_defective",
            "defect_claim_within_period == work_contract_qualified AND work_result_defective AND defect_found_within_statutory_period",
            "acceptance_duty_breached == work_contract_qualified AND acceptance_avoided_or_inspection_omitted",
            "withdrawal_compensation_due == work_contract_qualified AND customer_withdrew_before_completion_without_payment",
            "requires_human_work_contract_assessment == personal_performance_duty_breached OR term_condition_not_agreed OR estimate_notice_duty_breached OR customer_material_liability OR risk_warning_duty_breached OR contractor_liable_for_defects OR acceptance_duty_breached OR withdrawal_compensation_due",
        ],
    )


def evaluate_work_contract_constraints(
    constraint_set: WorkContractConstraintSet,
    facts: WorkContractFactSet,
) -> WorkContractEvaluation:
    variables = {field_name: Bool(field_name) for field_name in WorkContractFactSet.model_fields}
    work_contract_qualified = Bool("work_contract_qualified")
    personal_performance_duty_breached = Bool("personal_performance_duty_breached")
    term_condition_not_agreed = Bool("term_condition_not_agreed")
    estimate_notice_duty_breached = Bool("estimate_notice_duty_breached")
    customer_material_liability = Bool("customer_material_liability")
    risk_warning_duty_breached = Bool("risk_warning_duty_breached")
    contractor_liable_for_defects = Bool("contractor_liable_for_defects")
    defect_claim_within_period = Bool("defect_claim_within_period")
    acceptance_duty_breached = Bool("acceptance_duty_breached")
    withdrawal_compensation_due = Bool("withdrawal_compensation_due")
    requires_human_work_contract_assessment = Bool("requires_human_work_contract_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(work_contract_qualified == variables["work_performed_and_result_delivered_for_fee"])
    solver.add(
        personal_performance_duty_breached
        == And(work_contract_qualified, variables["subcontractor_engaged_despite_personal_duty"])
    )
    solver.add(
        term_condition_not_agreed
        == And(work_contract_qualified, variables["start_or_completion_term_not_agreed"])
    )
    solver.add(
        estimate_notice_duty_breached
        == And(work_contract_qualified, variables["estimate_exceeded_without_timely_notice"])
    )
    solver.add(
        customer_material_liability
        == And(work_contract_qualified, variables["customer_material_unsuitable"])
    )
    solver.add(
        risk_warning_duty_breached
        == And(work_contract_qualified, variables["contractor_failed_to_warn_of_risk"])
    )
    solver.add(
        contractor_liable_for_defects
        == And(work_contract_qualified, variables["work_result_defective"])
    )
    solver.add(
        defect_claim_within_period
        == And(
            work_contract_qualified,
            variables["work_result_defective"],
            variables["defect_found_within_statutory_period"],
        )
    )
    solver.add(
        acceptance_duty_breached
        == And(work_contract_qualified, variables["acceptance_avoided_or_inspection_omitted"])
    )
    solver.add(
        withdrawal_compensation_due
        == And(
            work_contract_qualified,
            variables["customer_withdrew_before_completion_without_payment"],
        )
    )
    solver.add(
        requires_human_work_contract_assessment
        == Or(
            personal_performance_duty_breached,
            term_condition_not_agreed,
            estimate_notice_duty_breached,
            customer_material_liability,
            risk_warning_duty_breached,
            contractor_liable_for_defects,
            acceptance_duty_breached,
            withdrawal_compensation_due,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return WorkContractEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            work_contract_qualified=False,
            personal_performance_duty_breached=False,
            term_condition_not_agreed=False,
            estimate_notice_duty_breached=False,
            customer_material_liability=False,
            risk_warning_duty_breached=False,
            contractor_liable_for_defects=False,
            defect_claim_within_period=False,
            acceptance_duty_breached=False,
            withdrawal_compensation_due=False,
            requires_human_work_contract_assessment=True,
            reasons_ru=["Набор фактов о подряде противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как подряд: подрядчик обязуется выполнить по заданию "
            "заказчика определённую работу и сдать её результат, а заказчик обязуется принять "
            "результат и оплатить его (статья 702 ГК РФ)."
            if truth(work_contract_qualified)
            else "Отношения не квалифицированы как договор подряда."
        ),
    ]
    if truth(personal_performance_duty_breached):
        reasons_ru.append(
            "Подрядчик привлёк субподрядчика вопреки вытекающей из закона или договора "
            "обязанности выполнить работу лично; он несёт ответственность за убытки, вызванные "
            "участием субподрядчика (статья 706 ГК РФ)."
        )
    if truth(term_condition_not_agreed):
        reasons_ru.append(
            "В договоре подряда указываются начальный и конечный сроки выполнения работы; при "
            "отсутствии согласования этого условия договор не считается заключённым "
            "(статья 708 ГК РФ)."
        )
    if truth(estimate_notice_duty_breached):
        reasons_ru.append(
            "Подрядчик, обнаруживший необходимость существенно превысить приблизительную смету, "
            "обязан своевременно предупредить заказчика; при нарушении этой обязанности он "
            "сохраняет право на оплату только по первоначально согласованной цене "
            "(статья 709 ГК РФ)."
        )
    if truth(customer_material_liability):
        reasons_ru.append(
            "Материал или оборудование, предоставленные заказчиком, непригодны или недоброкачественны; "
            "подрядчик обязан немедленно предупредить об этом и вправе отказаться от договора с "
            "возмещением убытков (статьи 713 и 716 ГК РФ)."
        )
    if truth(risk_warning_duty_breached):
        reasons_ru.append(
            "Подрядчик не предупредил заказчика об обстоятельствах, угрожающих годности или "
            "прочности результата работы либо создающих невозможность её завершения в срок, и "
            "лишается права ссылаться на них (статья 716 ГК РФ)."
        )
    if truth(contractor_liable_for_defects):
        reasons_ru.append(
            "Результат работы не соответствует условиям договора о качестве; заказчик вправе "
            "требовать безвозмездного устранения недостатков, соразмерного уменьшения цены или "
            "возмещения своих расходов на их устранение (статьи 721 и 723 ГК РФ)."
        )
    if truth(defect_claim_within_period):
        reasons_ru.append(
            "Недостаток обнаружен в пределах гарантийного либо иного установленного срока, что "
            "сохраняет за заказчиком право предъявить требования по качеству (статьи 722 и 724 "
            "ГК РФ)."
        )
    if truth(acceptance_duty_breached):
        reasons_ru.append(
            "Заказчик уклонился от приёмки результата работы либо не осмотрел его и не заявил о "
            "явных недостатках при приёмке (статья 720 ГК РФ)."
        )
    if truth(withdrawal_compensation_due):
        reasons_ru.append(
            "Заказчик отказался от договора до сдачи результата работы: он обязан уплатить "
            "подрядчику часть цены пропорционально выполненной работе и возместить убытки в "
            "пределах разницы между ценой договора и уплаченной суммой (статья 717 ГК РФ)."
        )
    return WorkContractEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        work_contract_qualified=truth(work_contract_qualified),
        personal_performance_duty_breached=truth(personal_performance_duty_breached),
        term_condition_not_agreed=truth(term_condition_not_agreed),
        estimate_notice_duty_breached=truth(estimate_notice_duty_breached),
        customer_material_liability=truth(customer_material_liability),
        risk_warning_duty_breached=truth(risk_warning_duty_breached),
        contractor_liable_for_defects=truth(contractor_liable_for_defects),
        defect_claim_within_period=truth(defect_claim_within_period),
        acceptance_duty_breached=truth(acceptance_duty_breached),
        withdrawal_compensation_due=truth(withdrawal_compensation_due),
        requires_human_work_contract_assessment=truth(requires_human_work_contract_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные общие положения о подряде и не заменяет судебную "
            "оценку.",
            "Существенность превышения сметы, характер недостатков, соразмерность уменьшения цены "
            "и размер убытков оцениваются экспертом и судом (статьи 709, 717 и 723 ГК РФ).",
        ],
    )
