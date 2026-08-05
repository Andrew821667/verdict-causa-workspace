from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PRODUCT_LIABILITY_EVIDENCE_SCHEMA_VERSION = "contracts.product-liability-evidence.v0"
PRODUCT_LIABILITY_MAPPING_VERSION = "contracts-reviewed-product-liability-to-facts-v0"
PRODUCT_LIABILITY_MODEL_VERSION = "contracts-product-liability-articles-1095-1098-v0"


class ProductLiabilityEvidencePredicate(str, Enum):
    # Основания возмещения вреда, причинённого вследствие недостатков товара,
    # работы или услуги (статья 1095 ГК РФ).
    PRODUCT_OR_SERVICE_DEFECT_HARM_ESTABLISHED = "product_or_service_defect_harm_established"
    COMPENSATION_REGARDLESS_OF_FAULT_BREACHED = "compensation_regardless_of_fault_breached"
    CONSUMER_PURPOSE_REQUIREMENT_BREACHED = "consumer_purpose_requirement_breached"
    # Лица, ответственные за вред (статья 1096 ГК РФ).
    LIABLE_PERSON_CHOICE_BREACHED = "liable_person_choice_breached"
    WORK_OR_SERVICE_PROVIDER_LIABILITY_BREACHED = "work_or_service_provider_liability_breached"
    INFORMATION_LIABILITY_BREACHED = "information_liability_breached"
    # Сроки возмещения вреда (статья 1097 ГК РФ).
    SERVICE_LIFE_PERIOD_RULES_BREACHED = "service_life_period_rules_breached"
    SERVICE_LIFE_ABSENCE_EXCEPTION_DISREGARDED = "service_life_absence_exception_disregarded"
    # Основания освобождения от ответственности (статья 1098 ГК РФ).
    EXCULPATION_GROUNDS_BREACHED = "exculpation_grounds_breached"
    VICTIM_RULES_VIOLATION_NOT_APPLIED = "victim_rules_violation_not_applied"


REQUIRED_PRODUCT_LIABILITY_PREDICATES = frozenset(ProductLiabilityEvidencePredicate)


class ProductLiabilityEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ProductLiabilityEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedProductLiabilityEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PRODUCT_LIABILITY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ProductLiabilityEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedProductLiabilityEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Product-liability evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Product-liability evidence contains duplicate legal source refs.")
        return self


class ProductLiabilityFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    product_or_service_defect_harm_established: bool
    compensation_regardless_of_fault_breached: bool
    consumer_purpose_requirement_breached: bool
    liable_person_choice_breached: bool
    work_or_service_provider_liability_breached: bool
    information_liability_breached: bool
    service_life_period_rules_breached: bool
    service_life_absence_exception_disregarded: bool
    exculpation_grounds_breached: bool
    victim_rules_violation_not_applied: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ProductLiabilityFactSet":
        if self.victim_rules_violation_not_applied and not self.exculpation_grounds_breached:
            raise ValueError(
                "Неприменение нарушения потребителем правил пользования или хранения относится "
                "только к случаю, когда нарушение оснований освобождения от ответственности "
                "установлено."
            )
        if (
            self.compensation_regardless_of_fault_breached
            and not self.product_or_service_defect_harm_established
        ):
            raise ValueError(
                "Нарушение правила о возмещении вреда независимо от вины относится только к "
                "случаю, когда причинение вреда вследствие недостатков товара, работы или "
                "услуги установлено."
            )
        return self


class ProductLiabilityFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ProductLiabilityEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ProductLiabilityFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ProductLiabilityFactProvenance] = Field(default_factory=list)


class ProductLiabilityConstraintSet(BaseModel):
    id: str
    model_version: str = PRODUCT_LIABILITY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ProductLiabilityEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    product_liability_qualified: bool
    no_fault_compensation_duty_breached: bool
    consumer_purpose_duty_breached: bool
    liable_person_duty_breached: bool
    work_service_liability_duty_breached: bool
    information_duty_breached: bool
    service_life_duty_breached: bool
    service_life_exception_duty_breached: bool
    exculpation_duty_breached: bool
    victim_rules_violation_breached: bool
    requires_human_product_liability_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_product_liability_evidence(
    evidence: ReviewedProductLiabilityEvidence,
) -> ProductLiabilityEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Product-liability evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Product-liability evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_PRODUCT_LIABILITY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed product-liability evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_PRODUCT_LIABILITY_PREDICATES
    }
    return ProductLiabilityEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PRODUCT_LIABILITY_MAPPING_VERSION,
        facts=ProductLiabilityFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ProductLiabilityFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_PRODUCT_LIABILITY_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_product_liability_constraint_set(
    mapping: ProductLiabilityEvidenceMappingResult,
) -> ProductLiabilityConstraintSet:
    return ProductLiabilityConstraintSet(
        id=f"product-liability-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "product_liability_qualified == product_or_service_defect_harm_established",
            "no_fault_compensation_duty_breached == product_liability_qualified AND compensation_regardless_of_fault_breached",
            "consumer_purpose_duty_breached == product_liability_qualified AND consumer_purpose_requirement_breached",
            "liable_person_duty_breached == product_liability_qualified AND liable_person_choice_breached",
            "work_service_liability_duty_breached == product_liability_qualified AND work_or_service_provider_liability_breached",
            "information_duty_breached == product_liability_qualified AND information_liability_breached",
            "service_life_duty_breached == product_liability_qualified AND service_life_period_rules_breached",
            "service_life_exception_duty_breached == product_liability_qualified AND service_life_absence_exception_disregarded",
            "exculpation_duty_breached == product_liability_qualified AND exculpation_grounds_breached",
            "victim_rules_violation_breached == product_liability_qualified AND exculpation_grounds_breached AND victim_rules_violation_not_applied",
            "requires_human_product_liability_assessment == no_fault_compensation_duty_breached OR consumer_purpose_duty_breached OR liable_person_duty_breached OR work_service_liability_duty_breached OR information_duty_breached OR service_life_duty_breached OR service_life_exception_duty_breached OR exculpation_duty_breached",
        ],
    )


def evaluate_product_liability_constraints(
    constraint_set: ProductLiabilityConstraintSet,
    facts: ProductLiabilityFactSet,
) -> ProductLiabilityEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in ProductLiabilityFactSet.model_fields
    }
    product_liability_qualified = Bool("product_liability_qualified")
    no_fault_compensation_duty_breached = Bool("no_fault_compensation_duty_breached")
    consumer_purpose_duty_breached = Bool("consumer_purpose_duty_breached")
    liable_person_duty_breached = Bool("liable_person_duty_breached")
    work_service_liability_duty_breached = Bool("work_service_liability_duty_breached")
    information_duty_breached = Bool("information_duty_breached")
    service_life_duty_breached = Bool("service_life_duty_breached")
    service_life_exception_duty_breached = Bool("service_life_exception_duty_breached")
    exculpation_duty_breached = Bool("exculpation_duty_breached")
    victim_rules_violation_breached = Bool("victim_rules_violation_breached")
    requires_human_product_liability_assessment = Bool(
        "requires_human_product_liability_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        product_liability_qualified == variables["product_or_service_defect_harm_established"]
    )
    solver.add(
        no_fault_compensation_duty_breached
        == And(product_liability_qualified, variables["compensation_regardless_of_fault_breached"])
    )
    solver.add(
        consumer_purpose_duty_breached
        == And(product_liability_qualified, variables["consumer_purpose_requirement_breached"])
    )
    solver.add(
        liable_person_duty_breached
        == And(product_liability_qualified, variables["liable_person_choice_breached"])
    )
    solver.add(
        work_service_liability_duty_breached
        == And(
            product_liability_qualified, variables["work_or_service_provider_liability_breached"]
        )
    )
    solver.add(
        information_duty_breached
        == And(product_liability_qualified, variables["information_liability_breached"])
    )
    solver.add(
        service_life_duty_breached
        == And(product_liability_qualified, variables["service_life_period_rules_breached"])
    )
    solver.add(
        service_life_exception_duty_breached
        == And(product_liability_qualified, variables["service_life_absence_exception_disregarded"])
    )
    solver.add(
        exculpation_duty_breached
        == And(product_liability_qualified, variables["exculpation_grounds_breached"])
    )
    solver.add(
        victim_rules_violation_breached
        == And(
            product_liability_qualified,
            variables["exculpation_grounds_breached"],
            variables["victim_rules_violation_not_applied"],
        )
    )
    solver.add(
        requires_human_product_liability_assessment
        == Or(
            no_fault_compensation_duty_breached,
            consumer_purpose_duty_breached,
            liable_person_duty_breached,
            work_service_liability_duty_breached,
            information_duty_breached,
            service_life_duty_breached,
            service_life_exception_duty_breached,
            exculpation_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ProductLiabilityEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            product_liability_qualified=False,
            no_fault_compensation_duty_breached=False,
            consumer_purpose_duty_breached=False,
            liable_person_duty_breached=False,
            work_service_liability_duty_breached=False,
            information_duty_breached=False,
            service_life_duty_breached=False,
            service_life_exception_duty_breached=False,
            exculpation_duty_breached=False,
            victim_rules_violation_breached=False,
            requires_human_product_liability_assessment=True,
            reasons_ru=[
                "Набор фактов о вреде вследствие недостатков товаров, работ или услуг противоречив."
            ],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Установлено причинение вреда вследствие конструктивных, рецептурных или иных "
            "недостатков товара, работы или услуги либо вследствие недостоверной или "
            "недостаточной информации о них (статья 1095 ГК РФ)."
            if truth(product_liability_qualified)
            else (
                "Причинение вреда вследствие недостатков товара, работы или услуги не установлено."
            )
        ),
    ]
    if truth(no_fault_compensation_duty_breached):
        reasons_ru.append(
            "Вред, причинённый жизни, здоровью или имуществу гражданина либо имуществу "
            "юридического лица вследствие недостатков товара, работы или услуги, подлежит "
            "возмещению продавцом или изготовителем независимо от их вины и от того, состоял "
            "ли потерпевший с ними в договорных отношениях (статья 1095 ГК РФ)."
        )
    if truth(consumer_purpose_duty_breached):
        reasons_ru.append(
            "Правила о возмещении вреда вследствие недостатков товара, работы или услуги "
            "применяются лишь в случаях приобретения товара, выполнения работы или оказания "
            "услуги в потребительских целях, а не для использования в предпринимательской "
            "деятельности (статья 1095 ГК РФ)."
        )
    if truth(liable_person_duty_breached):
        reasons_ru.append(
            "Вред, причинённый вследствие недостатков товара, подлежит возмещению по выбору "
            "потерпевшего продавцом или изготовителем товара (статья 1096 ГК РФ)."
        )
    if truth(work_service_liability_duty_breached):
        reasons_ru.append(
            "Вред, причинённый вследствие недостатков работы или услуги, подлежит возмещению "
            "лицом, выполнившим работу или оказавшим услугу (исполнителем) "
            "(статья 1096 ГК РФ)."
        )
    if truth(information_duty_breached):
        reasons_ru.append(
            "Вред, причинённый вследствие непредоставления полной или достоверной информации о "
            "товаре, работе или услуге, подлежит возмещению лицами, названными в правилах об "
            "ответственности за недостатки товара, работы или услуги (статья 1096 ГК РФ)."
        )
    if truth(service_life_duty_breached):
        reasons_ru.append(
            "Вред возмещается, если он возник в течение установленного срока годности или срока "
            "службы товара, работы или услуги, а если такой срок не установлен — в течение "
            "десяти лет со дня производства товара, работы или услуги (статья 1097 ГК РФ)."
        )
    if truth(service_life_exception_duty_breached):
        reasons_ru.append(
            "Независимо от времени причинения вред возмещается, если в нарушение закона срок "
            "годности или срок службы не установлен либо потребитель не был предупреждён о "
            "необходимых действиях по истечении такого срока и о возможных последствиях их "
            "невыполнения, а также если он не получил полной и достоверной информации о товаре "
            "(статья 1097 ГК РФ)."
        )
    if truth(exculpation_duty_breached):
        reasons_ru.append(
            "Продавец, изготовитель товара или исполнитель работы либо услуги освобождается от "
            "ответственности только в случае, если докажет, что вред возник вследствие "
            "непреодолимой силы (статья 1098 ГК РФ)."
        )
    if truth(victim_rules_violation_breached):
        reasons_ru.append(
            "Освобождение от ответственности также возможно при доказанности нарушения "
            "потребителем установленных правил пользования товаром, результатами работы или "
            "услуги либо правил их хранения (статья 1098 ГК РФ)."
        )
    return ProductLiabilityEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        product_liability_qualified=truth(product_liability_qualified),
        no_fault_compensation_duty_breached=truth(no_fault_compensation_duty_breached),
        consumer_purpose_duty_breached=truth(consumer_purpose_duty_breached),
        liable_person_duty_breached=truth(liable_person_duty_breached),
        work_service_liability_duty_breached=truth(work_service_liability_duty_breached),
        information_duty_breached=truth(information_duty_breached),
        service_life_duty_breached=truth(service_life_duty_breached),
        service_life_exception_duty_breached=truth(service_life_exception_duty_breached),
        exculpation_duty_breached=truth(exculpation_duty_breached),
        victim_rules_violation_breached=truth(victim_rules_violation_breached),
        requires_human_product_liability_assessment=truth(
            requires_human_product_liability_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о возмещении вреда вследствие "
            "недостатков товаров, работ и услуг и не заменяет судебную оценку.",
            "Наличие недостатка, его причинная связь с вредом, цель приобретения товара и "
            "соблюдение потребителем правил пользования оцениваются экспертом и судом "
            "(статьи 1095, 1097 и 1098 ГК РФ).",
        ],
    )
