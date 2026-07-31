from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


CONSTRUCTION_CONTRACT_EVIDENCE_SCHEMA_VERSION = "contracts.construction-contract-evidence.v0"
CONSTRUCTION_CONTRACT_MAPPING_VERSION = "contracts-reviewed-construction-contract-to-facts-v0"
CONSTRUCTION_CONTRACT_MODEL_VERSION = "contracts-construction-contract-articles-740-757-v0"


class ConstructionContractEvidencePredicate(str, Enum):
    # Понятие строительного подряда и распределение рисков (статьи 740 и 742 ГК РФ).
    CONSTRUCTION_WORK_PERFORMED_AND_ACCEPTED_FOR_PRICE = (
        "construction_work_performed_and_accepted_for_price"
    )
    RISK_INSURANCE_DUTY_UNMET = "risk_insurance_duty_unmet"
    # Техническая документация и смета (статьи 743 и 744 ГК РФ).
    TECHNICAL_DOCUMENTATION_OR_ESTIMATE_NOT_AGREED = (
        "technical_documentation_or_estimate_not_agreed"
    )
    ADDITIONAL_WORK_DISCOVERED_WITHOUT_NOTICE = "additional_work_discovered_without_notice"
    # Обязанности заказчика и его контроль (статьи 747 и 748 ГК РФ).
    CUSTOMER_FAILED_TO_PROVIDE_SITE_OR_SERVICES = "customer_failed_to_provide_site_or_services"
    CUSTOMER_SUPERVISION_OBSTRUCTED = "customer_supervision_obstructed"
    # Консервация строительства и приёмка результата (статьи 752 и 753 ГК РФ).
    CONSTRUCTION_SUSPENDED_AND_CONSERVED = "construction_suspended_and_conserved"
    ACCEPTANCE_ACT_SIGNING_REFUSED_WITHOUT_GROUNDS = (
        "acceptance_act_signing_refused_without_grounds"
    )
    # Качество работ и предельный срок обнаружения недостатков (статьи 754 и 756 ГК РФ).
    WORK_DEVIATES_FROM_DOCUMENTATION_OR_REQUIREMENTS = (
        "work_deviates_from_documentation_or_requirements"
    )
    DEFECT_FOUND_WITHIN_FIVE_YEAR_PERIOD = "defect_found_within_five_year_period"


REQUIRED_CONSTRUCTION_CONTRACT_PREDICATES = frozenset(ConstructionContractEvidencePredicate)


class ConstructionContractEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ConstructionContractEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedConstructionContractEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CONSTRUCTION_CONTRACT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ConstructionContractEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedConstructionContractEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Construction-contract evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Construction-contract evidence contains duplicate legal source refs.")
        return self


class ConstructionContractFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    construction_work_performed_and_accepted_for_price: bool
    risk_insurance_duty_unmet: bool
    technical_documentation_or_estimate_not_agreed: bool
    additional_work_discovered_without_notice: bool
    customer_failed_to_provide_site_or_services: bool
    customer_supervision_obstructed: bool
    construction_suspended_and_conserved: bool
    acceptance_act_signing_refused_without_grounds: bool
    work_deviates_from_documentation_or_requirements: bool
    defect_found_within_five_year_period: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ConstructionContractFactSet":
        if self.defect_found_within_five_year_period and not (
            self.work_deviates_from_documentation_or_requirements
        ):
            raise ValueError(
                "Обнаружение недостатка в пределах пятилетнего срока относится только к случаю, "
                "когда отступление от технической документации или обязательных требований "
                "установлено."
            )
        if self.additional_work_discovered_without_notice and not (
            self.construction_work_performed_and_accepted_for_price
        ):
            raise ValueError(
                "Обнаружение не учтённых в технической документации работ относится только к "
                "договору строительного подряда."
            )
        return self


class ConstructionContractFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ConstructionContractEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ConstructionContractFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ConstructionContractFactProvenance] = Field(default_factory=list)


class ConstructionContractConstraintSet(BaseModel):
    id: str
    model_version: str = CONSTRUCTION_CONTRACT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ConstructionContractEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    construction_contract_qualified: bool
    risk_insurance_duty_breached: bool
    documentation_or_estimate_condition_missing: bool
    additional_work_notice_duty_breached: bool
    customer_cooperation_duty_breached: bool
    supervision_right_obstructed: bool
    conservation_settlement_due: bool
    acceptance_act_dispute: bool
    construction_quality_breached: bool
    five_year_defect_claim_available: bool
    requires_human_construction_contract_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_construction_contract_evidence(
    evidence: ReviewedConstructionContractEvidence,
) -> ConstructionContractEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Construction-contract evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Construction-contract evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value
        for predicate in REQUIRED_CONSTRUCTION_CONTRACT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed construction-contract evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_CONSTRUCTION_CONTRACT_PREDICATES
    }
    return ConstructionContractEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CONSTRUCTION_CONTRACT_MAPPING_VERSION,
        facts=ConstructionContractFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ConstructionContractFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_CONSTRUCTION_CONTRACT_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_construction_contract_constraint_set(
    mapping: ConstructionContractEvidenceMappingResult,
) -> ConstructionContractConstraintSet:
    return ConstructionContractConstraintSet(
        id=f"construction-contract-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "construction_contract_qualified == construction_work_performed_and_accepted_for_price",
            "risk_insurance_duty_breached == construction_contract_qualified AND risk_insurance_duty_unmet",
            "documentation_or_estimate_condition_missing == construction_contract_qualified AND technical_documentation_or_estimate_not_agreed",
            "additional_work_notice_duty_breached == construction_contract_qualified AND additional_work_discovered_without_notice",
            "customer_cooperation_duty_breached == construction_contract_qualified AND customer_failed_to_provide_site_or_services",
            "supervision_right_obstructed == construction_contract_qualified AND customer_supervision_obstructed",
            "conservation_settlement_due == construction_contract_qualified AND construction_suspended_and_conserved",
            "acceptance_act_dispute == construction_contract_qualified AND acceptance_act_signing_refused_without_grounds",
            "construction_quality_breached == construction_contract_qualified AND work_deviates_from_documentation_or_requirements",
            "five_year_defect_claim_available == construction_contract_qualified AND work_deviates_from_documentation_or_requirements AND defect_found_within_five_year_period",
            "requires_human_construction_contract_assessment == risk_insurance_duty_breached OR documentation_or_estimate_condition_missing OR additional_work_notice_duty_breached OR customer_cooperation_duty_breached OR supervision_right_obstructed OR conservation_settlement_due OR acceptance_act_dispute OR construction_quality_breached",
        ],
    )


def evaluate_construction_contract_constraints(
    constraint_set: ConstructionContractConstraintSet,
    facts: ConstructionContractFactSet,
) -> ConstructionContractEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in ConstructionContractFactSet.model_fields
    }
    construction_contract_qualified = Bool("construction_contract_qualified")
    risk_insurance_duty_breached = Bool("risk_insurance_duty_breached")
    documentation_or_estimate_condition_missing = Bool(
        "documentation_or_estimate_condition_missing"
    )
    additional_work_notice_duty_breached = Bool("additional_work_notice_duty_breached")
    customer_cooperation_duty_breached = Bool("customer_cooperation_duty_breached")
    supervision_right_obstructed = Bool("supervision_right_obstructed")
    conservation_settlement_due = Bool("conservation_settlement_due")
    acceptance_act_dispute = Bool("acceptance_act_dispute")
    construction_quality_breached = Bool("construction_quality_breached")
    five_year_defect_claim_available = Bool("five_year_defect_claim_available")
    requires_human_construction_contract_assessment = Bool(
        "requires_human_construction_contract_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        construction_contract_qualified
        == variables["construction_work_performed_and_accepted_for_price"]
    )
    solver.add(
        risk_insurance_duty_breached
        == And(construction_contract_qualified, variables["risk_insurance_duty_unmet"])
    )
    solver.add(
        documentation_or_estimate_condition_missing
        == And(
            construction_contract_qualified,
            variables["technical_documentation_or_estimate_not_agreed"],
        )
    )
    solver.add(
        additional_work_notice_duty_breached
        == And(
            construction_contract_qualified,
            variables["additional_work_discovered_without_notice"],
        )
    )
    solver.add(
        customer_cooperation_duty_breached
        == And(
            construction_contract_qualified,
            variables["customer_failed_to_provide_site_or_services"],
        )
    )
    solver.add(
        supervision_right_obstructed
        == And(construction_contract_qualified, variables["customer_supervision_obstructed"])
    )
    solver.add(
        conservation_settlement_due
        == And(construction_contract_qualified, variables["construction_suspended_and_conserved"])
    )
    solver.add(
        acceptance_act_dispute
        == And(
            construction_contract_qualified,
            variables["acceptance_act_signing_refused_without_grounds"],
        )
    )
    solver.add(
        construction_quality_breached
        == And(
            construction_contract_qualified,
            variables["work_deviates_from_documentation_or_requirements"],
        )
    )
    solver.add(
        five_year_defect_claim_available
        == And(
            construction_contract_qualified,
            variables["work_deviates_from_documentation_or_requirements"],
            variables["defect_found_within_five_year_period"],
        )
    )
    solver.add(
        requires_human_construction_contract_assessment
        == Or(
            risk_insurance_duty_breached,
            documentation_or_estimate_condition_missing,
            additional_work_notice_duty_breached,
            customer_cooperation_duty_breached,
            supervision_right_obstructed,
            conservation_settlement_due,
            acceptance_act_dispute,
            construction_quality_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ConstructionContractEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            construction_contract_qualified=False,
            risk_insurance_duty_breached=False,
            documentation_or_estimate_condition_missing=False,
            additional_work_notice_duty_breached=False,
            customer_cooperation_duty_breached=False,
            supervision_right_obstructed=False,
            conservation_settlement_due=False,
            acceptance_act_dispute=False,
            construction_quality_breached=False,
            five_year_defect_claim_available=False,
            requires_human_construction_contract_assessment=True,
            reasons_ru=["Набор фактов о строительном подряде противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как строительный подряд: подрядчик обязуется в установленный "
            "срок построить по заданию заказчика объект либо выполнить иные строительные работы, "
            "а заказчик — создать необходимые условия, принять результат и уплатить "
            "обусловленную цену (статья 740 ГК РФ)."
            if truth(construction_contract_qualified)
            else "Отношения не квалифицированы как договор строительного подряда."
        ),
    ]
    if truth(risk_insurance_duty_breached):
        reasons_ru.append(
            "Не исполнена принятая на себя стороной обязанность застраховать риск случайной "
            "гибели или случайного повреждения объекта строительства, материалов и оборудования "
            "(статья 742 ГК РФ)."
        )
    if truth(documentation_or_estimate_condition_missing):
        reasons_ru.append(
            "Не согласованы состав и содержание технической документации либо смета, "
            "определяющие объём, содержание работ и их цену (статьи 743 и 744 ГК РФ)."
        )
    if truth(additional_work_notice_duty_breached):
        reasons_ru.append(
            "Подрядчик обнаружил не учтённые в технической документации работы, но не сообщил об "
            "этом заказчику; он лишается права требовать оплаты дополнительных работ и "
            "возмещения вызванных ими убытков (статья 743 ГК РФ)."
        )
    if truth(customer_cooperation_duty_breached):
        reasons_ru.append(
            "Заказчик не предоставил земельный участок либо не обеспечил передачу зданий, "
            "сооружений и услуг, необходимых для выполнения работ (статья 747 ГК РФ)."
        )
    if truth(supervision_right_obstructed):
        reasons_ru.append(
            "Заказчику воспрепятствовали осуществлять контроль и надзор за ходом и качеством "
            "работ, соблюдением сроков и качеством используемых материалов "
            "(статьи 748 и 749 ГК РФ)."
        )
    if truth(conservation_settlement_due):
        reasons_ru.append(
            "Строительство приостановлено и объект законсервирован: заказчик обязан оплатить "
            "выполненные до консервации работы в полном объёме и возместить вызванные ею расходы "
            "с зачётом выгод подрядчика (статья 752 ГК РФ)."
        )
    if truth(acceptance_act_dispute):
        reasons_ru.append(
            "Сторона отказалась подписать акт сдачи или приёмки результата работ без обоснованных "
            "мотивов; акт подписывается другой стороной односторонне и признаётся судом "
            "недействительным лишь при обоснованности отказа (статья 753 ГК РФ)."
        )
    if truth(construction_quality_breached):
        reasons_ru.append(
            "Работы выполнены с отступлениями от технической документации или обязательных "
            "строительных норм и правил, что влечёт ответственность подрядчика за качество "
            "(статья 754 ГК РФ)."
        )
    if truth(five_year_defect_claim_available):
        reasons_ru.append(
            "Недостаток обнаружен в пределах предельного пятилетнего срока с момента передачи "
            "результата работ, что сохраняет требование заказчика к подрядчику "
            "(статья 756 ГК РФ)."
        )
    return ConstructionContractEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        construction_contract_qualified=truth(construction_contract_qualified),
        risk_insurance_duty_breached=truth(risk_insurance_duty_breached),
        documentation_or_estimate_condition_missing=truth(
            documentation_or_estimate_condition_missing
        ),
        additional_work_notice_duty_breached=truth(additional_work_notice_duty_breached),
        customer_cooperation_duty_breached=truth(customer_cooperation_duty_breached),
        supervision_right_obstructed=truth(supervision_right_obstructed),
        conservation_settlement_due=truth(conservation_settlement_due),
        acceptance_act_dispute=truth(acceptance_act_dispute),
        construction_quality_breached=truth(construction_quality_breached),
        five_year_defect_claim_available=truth(five_year_defect_claim_available),
        requires_human_construction_contract_assessment=truth(
            requires_human_construction_contract_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о строительном подряде и не заменяет "
            "судебную оценку.",
            "Существенность отступлений от документации, обоснованность отказа от подписания акта "
            "и объём расходов при консервации оцениваются экспертом и судом (статьи 752, 753 и "
            "754 ГК РФ).",
        ],
    )
