from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


STATE_SUPPLY_EVIDENCE_SCHEMA_VERSION = "contracts.state-supply-evidence.v0"
STATE_SUPPLY_MAPPING_VERSION = "contracts-reviewed-state-supply-to-facts-v0"
STATE_SUPPLY_MODEL_VERSION = "contracts-state-supply-articles-525-534-v0"


class StateSupplyEvidencePredicate(str, Enum):
    # Государственный (муниципальный) контракт (статьи 525–528 ГК РФ).
    STATE_CONTRACT_CONCLUDED = "state_contract_concluded"
    ORDER_PLACED_BY_PROCEDURE = "order_placed_by_procedure"
    CONCLUSION_MANDATORY_FOR_SUPPLIER = "conclusion_mandatory_for_supplier"
    CONTRACT_CAUSES_SUPPLIER_LOSS = "contract_causes_supplier_loss"
    SUPPLIER_EVADED_CONCLUSION = "supplier_evaded_conclusion"
    # Прикрепление и договор поставки (статьи 529 и 530 ГК РФ).
    ATTACHMENT_NOTICE_ISSUED = "attachment_notice_issued"
    BUYER_REFUSED_GOODS = "buyer_refused_goods"
    # Исполнение, оплата и убытки (статьи 531–534 ГК РФ).
    GOODS_DELIVERED_TO_BUYER = "goods_delivered_to_buyer"
    BUYER_PAID_AT_CONTRACT_PRICE = "buyer_paid_at_contract_price"
    STATE_CUSTOMER_REFUSED_GOODS = "state_customer_refused_goods"
    SUPPLIER_INCURRED_LOSSES = "supplier_incurred_losses"


REQUIRED_STATE_SUPPLY_PREDICATES = frozenset(StateSupplyEvidencePredicate)


class StateSupplyEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: StateSupplyEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedStateSupplyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = STATE_SUPPLY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[StateSupplyEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedStateSupplyEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("State supply evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("State supply evidence contains duplicate legal source refs.")
        return self


class StateSupplyFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state_contract_concluded: bool
    order_placed_by_procedure: bool
    conclusion_mandatory_for_supplier: bool
    contract_causes_supplier_loss: bool
    supplier_evaded_conclusion: bool
    attachment_notice_issued: bool
    buyer_refused_goods: bool
    goods_delivered_to_buyer: bool
    buyer_paid_at_contract_price: bool
    state_customer_refused_goods: bool
    supplier_incurred_losses: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "StateSupplyFactSet":
        if self.contract_causes_supplier_loss and not self.conclusion_mandatory_for_supplier:
            raise ValueError(
                "Убыточность контракта учитывается только при обязательности его заключения."
            )
        return self


class StateSupplyFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class StateSupplyEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: StateSupplyFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[StateSupplyFactProvenance] = Field(default_factory=list)


class StateSupplyConstraintSet(BaseModel):
    id: str
    model_version: str = STATE_SUPPLY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class StateSupplyEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    supplier_conclusion_compellable: bool
    buyer_attached_to_supplier: bool
    supplier_may_seek_reattachment: bool
    buyer_pays_at_contract_price: bool
    customer_guarantees_buyer_payment: bool
    customer_refusal_compensates_supplier: bool
    supplier_losses_compensable: bool
    requires_human_state_supply_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_state_supply_evidence(
    evidence: ReviewedStateSupplyEvidence,
) -> StateSupplyEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("State supply evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("State supply evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_STATE_SUPPLY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed state supply evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_STATE_SUPPLY_PREDICATES
    }
    return StateSupplyEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=STATE_SUPPLY_MAPPING_VERSION,
        facts=StateSupplyFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            StateSupplyFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_STATE_SUPPLY_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_state_supply_constraint_set(
    mapping: StateSupplyEvidenceMappingResult,
) -> StateSupplyConstraintSet:
    return StateSupplyConstraintSet(
        id=f"state-supply-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "supplier_conclusion_compellable == conclusion_mandatory_for_supplier AND order_placed_by_procedure AND supplier_evaded_conclusion AND NOT contract_causes_supplier_loss",
            "buyer_attached_to_supplier == state_contract_concluded AND attachment_notice_issued",
            "supplier_may_seek_reattachment == attachment_notice_issued AND buyer_refused_goods",
            "buyer_pays_at_contract_price == goods_delivered_to_buyer AND buyer_paid_at_contract_price",
            "customer_guarantees_buyer_payment == state_contract_concluded AND goods_delivered_to_buyer",
            "customer_refusal_compensates_supplier == state_customer_refused_goods AND supplier_incurred_losses",
            "supplier_losses_compensable == state_contract_concluded AND supplier_incurred_losses",
            "requires_human_state_supply_assessment == (conclusion_mandatory_for_supplier AND supplier_evaded_conclusion) OR buyer_refused_goods OR state_customer_refused_goods OR supplier_incurred_losses",
        ],
    )


def evaluate_state_supply_constraints(
    constraint_set: StateSupplyConstraintSet,
    facts: StateSupplyFactSet,
) -> StateSupplyEvaluation:
    variables = {field_name: Bool(field_name) for field_name in StateSupplyFactSet.model_fields}
    supplier_conclusion_compellable = Bool("supplier_conclusion_compellable")
    buyer_attached_to_supplier = Bool("buyer_attached_to_supplier")
    supplier_may_seek_reattachment = Bool("supplier_may_seek_reattachment")
    buyer_pays_at_contract_price = Bool("buyer_pays_at_contract_price")
    customer_guarantees_buyer_payment = Bool("customer_guarantees_buyer_payment")
    customer_refusal_compensates_supplier = Bool("customer_refusal_compensates_supplier")
    supplier_losses_compensable = Bool("supplier_losses_compensable")
    requires_human_state_supply_assessment = Bool("requires_human_state_supply_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        supplier_conclusion_compellable
        == And(
            variables["conclusion_mandatory_for_supplier"],
            variables["order_placed_by_procedure"],
            variables["supplier_evaded_conclusion"],
            Not(variables["contract_causes_supplier_loss"]),
        )
    )
    solver.add(
        buyer_attached_to_supplier
        == And(variables["state_contract_concluded"], variables["attachment_notice_issued"])
    )
    solver.add(
        supplier_may_seek_reattachment
        == And(variables["attachment_notice_issued"], variables["buyer_refused_goods"])
    )
    solver.add(
        buyer_pays_at_contract_price
        == And(variables["goods_delivered_to_buyer"], variables["buyer_paid_at_contract_price"])
    )
    solver.add(
        customer_guarantees_buyer_payment
        == And(variables["state_contract_concluded"], variables["goods_delivered_to_buyer"])
    )
    solver.add(
        customer_refusal_compensates_supplier
        == And(variables["state_customer_refused_goods"], variables["supplier_incurred_losses"])
    )
    solver.add(
        supplier_losses_compensable
        == And(variables["state_contract_concluded"], variables["supplier_incurred_losses"])
    )
    solver.add(
        requires_human_state_supply_assessment
        == Or(
            And(
                variables["conclusion_mandatory_for_supplier"],
                variables["supplier_evaded_conclusion"],
            ),
            variables["buyer_refused_goods"],
            variables["state_customer_refused_goods"],
            variables["supplier_incurred_losses"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return StateSupplyEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            supplier_conclusion_compellable=False,
            buyer_attached_to_supplier=False,
            supplier_may_seek_reattachment=False,
            buyer_pays_at_contract_price=False,
            customer_guarantees_buyer_payment=False,
            customer_refusal_compensates_supplier=False,
            supplier_losses_compensable=False,
            requires_human_state_supply_assessment=True,
            reasons_ru=["Набор фактов о поставке для государственных нужд противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = []
    if truth(supplier_conclusion_compellable):
        reasons_ru.append(
            "Поставщик, для которого заключение государственного или муниципального "
            "контракта обязательно и который уклоняется, может быть понуждён к его "
            "заключению (статьи 527 и 528 ГК РФ)."
        )
    if truth(buyer_attached_to_supplier):
        reasons_ru.append(
            "На основании контракта заказчик направил извещение о прикреплении покупателя "
            "к поставщику (статья 529 ГК РФ)."
        )
    if truth(supplier_may_seek_reattachment):
        reasons_ru.append(
            "При отказе покупателя от товаров поставщик вправе требовать прикрепления к "
            "другому покупателю (статья 530 ГК РФ)."
        )
    if truth(buyer_pays_at_contract_price):
        reasons_ru.append(
            "При поставке покупателю оплата производится по ценам, установленным "
            "контрактом (статья 532 ГК РФ)."
        )
    if truth(customer_guarantees_buyer_payment):
        reasons_ru.append(
            "Государственный заказчик признаётся поручителем по обязательству покупателя "
            "об оплате товаров (статья 532 ГК РФ)."
        )
    if truth(customer_refusal_compensates_supplier):
        reasons_ru.append(
            "При отказе государственного заказчика от товаров заказчик возмещает "
            "поставщику причинённые этим убытки (статья 534 ГК РФ)."
        )
    if truth(supplier_losses_compensable):
        reasons_ru.append(
            "Убытки, причинённые поставщику в связи с выполнением контракта, подлежат "
            "возмещению заказчиком (статья 533 ГК РФ)."
        )
    if not reasons_ru:
        reasons_ru.append(
            "Формальные предпосылки поставки для государственных или муниципальных нужд "
            "не подтверждены."
        )
    return StateSupplyEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        supplier_conclusion_compellable=truth(supplier_conclusion_compellable),
        buyer_attached_to_supplier=truth(buyer_attached_to_supplier),
        supplier_may_seek_reattachment=truth(supplier_may_seek_reattachment),
        buyer_pays_at_contract_price=truth(buyer_pays_at_contract_price),
        customer_guarantees_buyer_payment=truth(customer_guarantees_buyer_payment),
        customer_refusal_compensates_supplier=truth(customer_refusal_compensates_supplier),
        supplier_losses_compensable=truth(supplier_losses_compensable),
        requires_human_state_supply_assessment=truth(requires_human_state_supply_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о поставке для государственных и "
            "муниципальных нужд и не заменяет судебную оценку.",
            "Обязательность заключения контракта, размер убытков и порядок размещения "
            "заказа оцениваются экспертом и судом.",
        ],
    )
