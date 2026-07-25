from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


RETAIL_SALE_EVIDENCE_SCHEMA_VERSION = "contracts.retail-sale-evidence.v0"
RETAIL_SALE_MAPPING_VERSION = "contracts-reviewed-retail-sale-to-facts-v0"
RETAIL_SALE_MODEL_VERSION = "contracts-retail-sale-articles-492-505-v0"


class RetailSaleEvidencePredicate(str, Enum):
    # Понятие и заключение розничной купли-продажи (статьи 492–494 ГК РФ).
    RETAIL_CONSUMER_SALE = "retail_consumer_sale"
    PUBLIC_OFFER_MADE = "public_offer_made"
    RECEIPT_OR_CONFIRMATION_ISSUED = "receipt_or_confirmation_issued"
    # Информация о товаре (статья 495 ГК РФ).
    REQUIRED_INFORMATION_PROVIDED = "required_information_provided"
    # Ненадлежащее качество (статья 503 ГК РФ).
    GOODS_DEFECTIVE = "goods_defective"
    BUYER_QUALITY_REMEDY_DEMANDED = "buyer_quality_remedy_demanded"
    # Обмен товара надлежащего качества (статья 502 ГК РФ).
    QUALITY_EXCHANGE_DEMANDED_IN_TERM = "quality_exchange_demanded_in_term"
    GOODS_UNUSED_AND_DOCUMENTED = "goods_unused_and_documented"
    SIMILAR_GOODS_AVAILABLE = "similar_goods_available"
    # Цена (статьи 500 и 504 ГК РФ).
    PRICE_INCREASED_BEFORE_REPLACEMENT = "price_increased_before_replacement"


REQUIRED_RETAIL_SALE_PREDICATES = frozenset(RetailSaleEvidencePredicate)


class RetailSaleEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: RetailSaleEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedRetailSaleEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = RETAIL_SALE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[RetailSaleEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedRetailSaleEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Retail sale evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Retail sale evidence contains duplicate legal source refs.")
        return self


class RetailSaleFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    retail_consumer_sale: bool
    public_offer_made: bool
    receipt_or_confirmation_issued: bool
    required_information_provided: bool
    goods_defective: bool
    buyer_quality_remedy_demanded: bool
    quality_exchange_demanded_in_term: bool
    goods_unused_and_documented: bool
    similar_goods_available: bool
    price_increased_before_replacement: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "RetailSaleFactSet":
        if self.receipt_or_confirmation_issued and not self.retail_consumer_sale:
            raise ValueError("Чек розничной продажи невозможен без розничной купли-продажи.")
        return self


class RetailSaleFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class RetailSaleEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: RetailSaleFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[RetailSaleFactProvenance] = Field(default_factory=list)


class RetailSaleConstraintSet(BaseModel):
    id: str
    model_version: str = RETAIL_SALE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class RetailSaleEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    retail_contract_is_public: bool
    form_confirmed_by_receipt: bool
    information_duty_breached: bool
    quality_remedy_available: bool
    quality_exchange_available: bool
    exchange_refund_available: bool
    price_difference_compensable: bool
    requires_human_retail_sale_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_retail_sale_evidence(
    evidence: ReviewedRetailSaleEvidence,
) -> RetailSaleEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Retail sale evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Retail sale evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_RETAIL_SALE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed retail sale evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_RETAIL_SALE_PREDICATES
    }
    return RetailSaleEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=RETAIL_SALE_MAPPING_VERSION,
        facts=RetailSaleFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            RetailSaleFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_RETAIL_SALE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_retail_sale_constraint_set(
    mapping: RetailSaleEvidenceMappingResult,
) -> RetailSaleConstraintSet:
    return RetailSaleConstraintSet(
        id=f"retail-sale-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "retail_contract_is_public == retail_consumer_sale",
            "form_confirmed_by_receipt == retail_consumer_sale AND receipt_or_confirmation_issued",
            "information_duty_breached == retail_consumer_sale AND NOT required_information_provided",
            "quality_remedy_available == goods_defective AND buyer_quality_remedy_demanded",
            "quality_exchange_available == quality_exchange_demanded_in_term AND goods_unused_and_documented AND similar_goods_available",
            "exchange_refund_available == quality_exchange_demanded_in_term AND goods_unused_and_documented AND NOT similar_goods_available",
            "price_difference_compensable == goods_defective AND buyer_quality_remedy_demanded AND price_increased_before_replacement",
            "requires_human_retail_sale_assessment == (retail_consumer_sale AND NOT required_information_provided) OR (goods_defective AND buyer_quality_remedy_demanded) OR quality_exchange_demanded_in_term OR price_increased_before_replacement",
        ],
    )


def evaluate_retail_sale_constraints(
    constraint_set: RetailSaleConstraintSet,
    facts: RetailSaleFactSet,
) -> RetailSaleEvaluation:
    variables = {field_name: Bool(field_name) for field_name in RetailSaleFactSet.model_fields}
    retail_contract_is_public = Bool("retail_contract_is_public")
    form_confirmed_by_receipt = Bool("form_confirmed_by_receipt")
    information_duty_breached = Bool("information_duty_breached")
    quality_remedy_available = Bool("quality_remedy_available")
    quality_exchange_available = Bool("quality_exchange_available")
    exchange_refund_available = Bool("exchange_refund_available")
    price_difference_compensable = Bool("price_difference_compensable")
    requires_human_retail_sale_assessment = Bool("requires_human_retail_sale_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(retail_contract_is_public == variables["retail_consumer_sale"])
    solver.add(
        form_confirmed_by_receipt
        == And(variables["retail_consumer_sale"], variables["receipt_or_confirmation_issued"])
    )
    solver.add(
        information_duty_breached
        == And(variables["retail_consumer_sale"], Not(variables["required_information_provided"]))
    )
    solver.add(
        quality_remedy_available
        == And(variables["goods_defective"], variables["buyer_quality_remedy_demanded"])
    )
    solver.add(
        quality_exchange_available
        == And(
            variables["quality_exchange_demanded_in_term"],
            variables["goods_unused_and_documented"],
            variables["similar_goods_available"],
        )
    )
    solver.add(
        exchange_refund_available
        == And(
            variables["quality_exchange_demanded_in_term"],
            variables["goods_unused_and_documented"],
            Not(variables["similar_goods_available"]),
        )
    )
    solver.add(
        price_difference_compensable
        == And(
            variables["goods_defective"],
            variables["buyer_quality_remedy_demanded"],
            variables["price_increased_before_replacement"],
        )
    )
    solver.add(
        requires_human_retail_sale_assessment
        == Or(
            And(
                variables["retail_consumer_sale"],
                Not(variables["required_information_provided"]),
            ),
            And(variables["goods_defective"], variables["buyer_quality_remedy_demanded"]),
            variables["quality_exchange_demanded_in_term"],
            variables["price_increased_before_replacement"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return RetailSaleEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            retail_contract_is_public=False,
            form_confirmed_by_receipt=False,
            information_duty_breached=False,
            quality_remedy_available=False,
            quality_exchange_available=False,
            exchange_refund_available=False,
            price_difference_compensable=False,
            requires_human_retail_sale_assessment=True,
            reasons_ru=["Набор фактов о розничной купле-продаже противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор розничной купли-продажи является публичным (статья 492 ГК РФ)."
            if truth(retail_contract_is_public)
            else "Отношения не квалифицированы как розничная купля-продажа."
        ),
    ]
    if truth(form_confirmed_by_receipt):
        reasons_ru.append(
            "Договор подтверждён выдачей кассового или товарного чека (статья 493 ГК РФ)."
        )
    if truth(information_duty_breached):
        reasons_ru.append(
            "Продавец обязан предоставить покупателю необходимую и достоверную информацию "
            "о товаре; её непредоставление влечёт последствия (статья 495 ГК РФ)."
        )
    if truth(quality_remedy_available):
        reasons_ru.append(
            "При продаже товара ненадлежащего качества покупатель вправе требовать замены, "
            "соразмерного уменьшения цены, устранения недостатков или возврата уплаченной "
            "суммы (статья 503 ГК РФ)."
        )
    if truth(quality_exchange_available):
        reasons_ru.append(
            "Покупатель вправе обменять непродовольственный товар надлежащего качества на "
            "аналогичный в установленный срок (статья 502 ГК РФ)."
        )
    if truth(exchange_refund_available):
        reasons_ru.append(
            "При отсутствии аналогичного товара покупатель вправе вернуть товар и получить "
            "уплаченную за него сумму (пункт 2 статьи 502 ГК РФ)."
        )
    if truth(price_difference_compensable):
        reasons_ru.append(
            "При замене или возврате товара ненадлежащего качества возмещается разница между "
            "ценой товара и его ценой на момент замены или возврата (статья 504 ГК РФ)."
        )
    return RetailSaleEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        retail_contract_is_public=truth(retail_contract_is_public),
        form_confirmed_by_receipt=truth(form_confirmed_by_receipt),
        information_duty_breached=truth(information_duty_breached),
        quality_remedy_available=truth(quality_remedy_available),
        quality_exchange_available=truth(quality_exchange_available),
        exchange_refund_available=truth(exchange_refund_available),
        price_difference_compensable=truth(price_difference_compensable),
        requires_human_retail_sale_assessment=truth(requires_human_retail_sale_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о розничной купле-продаже и не "
            "заменяет судебную оценку.",
            "Качество товара, достоверность информации и условия обмена оцениваются "
            "экспертом и судом.",
        ],
    )
