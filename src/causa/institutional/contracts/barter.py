from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


BARTER_EVIDENCE_SCHEMA_VERSION = "contracts.barter-evidence.v0"
BARTER_MAPPING_VERSION = "contracts-reviewed-barter-to-facts-v0"
BARTER_MODEL_VERSION = "contracts-barter-articles-567-571-v0"


class BarterEvidencePredicate(str, Enum):
    # Понятие договора мены (статья 567 ГК РФ).
    MUTUAL_GOODS_FOR_GOODS_EXCHANGE = "mutual_goods_for_goods_exchange"
    CONTRARY_TO_BARTER_ESSENCE = "contrary_to_barter_essence"
    # Цены и расходы, равноценность (статья 568 ГК РФ).
    GOODS_TREATED_AS_EQUAL_VALUE = "goods_treated_as_equal_value"
    GOODS_UNEQUAL_VALUE = "goods_unequal_value"
    LOWER_PRICE_PARTY_PAID_DIFFERENCE = "lower_price_party_paid_difference"
    # Встречное исполнение обязательства передать товар (статья 569 ГК РФ).
    TRANSFER_DEADLINES_DIFFER = "transfer_deadlines_differ"
    FIRST_PARTY_PERFORMED_ITS_TRANSFER = "first_party_performed_its_transfer"
    # Переход права собственности (статья 570 ГК РФ).
    BOTH_PARTIES_TRANSFERRED_GOODS = "both_parties_transferred_goods"
    # Ответственность за изъятие товара (статья 571 ГК РФ).
    RECEIVED_GOOD_EVICTED_BY_THIRD_PARTY = "received_good_evicted_by_third_party"
    EVICTION_GROUND_AROSE_BEFORE_PERFORMANCE = "eviction_ground_arose_before_performance"


REQUIRED_BARTER_PREDICATES = frozenset(BarterEvidencePredicate)


class BarterEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: BarterEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedBarterEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = BARTER_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[BarterEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedBarterEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Barter evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Barter evidence contains duplicate legal source refs.")
        return self


class BarterFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mutual_goods_for_goods_exchange: bool
    contrary_to_barter_essence: bool
    goods_treated_as_equal_value: bool
    goods_unequal_value: bool
    lower_price_party_paid_difference: bool
    transfer_deadlines_differ: bool
    first_party_performed_its_transfer: bool
    both_parties_transferred_goods: bool
    received_good_evicted_by_third_party: bool
    eviction_ground_arose_before_performance: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "BarterFactSet":
        if self.goods_treated_as_equal_value and self.goods_unequal_value:
            raise ValueError(
                "Товары не могут одновременно признаваться равноценными и неравноценными."
            )
        if self.lower_price_party_paid_difference and not self.goods_unequal_value:
            raise ValueError("Оплата разницы в цене возможна только при неравноценности товаров.")
        if (
            self.eviction_ground_arose_before_performance
            and not self.received_good_evicted_by_third_party
        ):
            raise ValueError("Основание изъятия учитывается только при фактическом изъятии товара.")
        return self


class BarterFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class BarterEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: BarterFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[BarterFactProvenance] = Field(default_factory=list)


class BarterConstraintSet(BaseModel):
    id: str
    model_version: str = BARTER_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class BarterEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    barter_qualified: bool
    sale_rules_apply: bool
    equal_value_presumption_applies: bool
    price_difference_obligation: bool
    counter_performance_rules_apply: bool
    second_party_may_suspend_transfer: bool
    ownership_transfers_simultaneously: bool
    eviction_remedy_available: bool
    requires_human_barter_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_barter_evidence(
    evidence: ReviewedBarterEvidence,
) -> BarterEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Barter evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Barter evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_BARTER_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed barter evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_BARTER_PREDICATES
    }
    return BarterEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=BARTER_MAPPING_VERSION,
        facts=BarterFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            BarterFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_BARTER_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_barter_constraint_set(
    mapping: BarterEvidenceMappingResult,
) -> BarterConstraintSet:
    return BarterConstraintSet(
        id=f"barter-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "barter_qualified == mutual_goods_for_goods_exchange",
            "sale_rules_apply == barter_qualified AND NOT contrary_to_barter_essence",
            "equal_value_presumption_applies == barter_qualified AND goods_treated_as_equal_value",
            "price_difference_obligation == barter_qualified AND goods_unequal_value AND NOT lower_price_party_paid_difference",
            "counter_performance_rules_apply == barter_qualified AND transfer_deadlines_differ",
            "second_party_may_suspend_transfer == barter_qualified AND transfer_deadlines_differ AND NOT first_party_performed_its_transfer",
            "ownership_transfers_simultaneously == barter_qualified AND both_parties_transferred_goods",
            "eviction_remedy_available == barter_qualified AND received_good_evicted_by_third_party AND eviction_ground_arose_before_performance",
            "requires_human_barter_assessment == price_difference_obligation OR second_party_may_suspend_transfer OR eviction_remedy_available OR (barter_qualified AND contrary_to_barter_essence)",
        ],
    )


def evaluate_barter_constraints(
    constraint_set: BarterConstraintSet,
    facts: BarterFactSet,
) -> BarterEvaluation:
    variables = {field_name: Bool(field_name) for field_name in BarterFactSet.model_fields}
    barter_qualified = Bool("barter_qualified")
    sale_rules_apply = Bool("sale_rules_apply")
    equal_value_presumption_applies = Bool("equal_value_presumption_applies")
    price_difference_obligation = Bool("price_difference_obligation")
    counter_performance_rules_apply = Bool("counter_performance_rules_apply")
    second_party_may_suspend_transfer = Bool("second_party_may_suspend_transfer")
    ownership_transfers_simultaneously = Bool("ownership_transfers_simultaneously")
    eviction_remedy_available = Bool("eviction_remedy_available")
    requires_human_barter_assessment = Bool("requires_human_barter_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(barter_qualified == variables["mutual_goods_for_goods_exchange"])
    solver.add(
        sale_rules_apply == And(barter_qualified, Not(variables["contrary_to_barter_essence"]))
    )
    solver.add(
        equal_value_presumption_applies
        == And(barter_qualified, variables["goods_treated_as_equal_value"])
    )
    solver.add(
        price_difference_obligation
        == And(
            barter_qualified,
            variables["goods_unequal_value"],
            Not(variables["lower_price_party_paid_difference"]),
        )
    )
    solver.add(
        counter_performance_rules_apply
        == And(barter_qualified, variables["transfer_deadlines_differ"])
    )
    solver.add(
        second_party_may_suspend_transfer
        == And(
            barter_qualified,
            variables["transfer_deadlines_differ"],
            Not(variables["first_party_performed_its_transfer"]),
        )
    )
    solver.add(
        ownership_transfers_simultaneously
        == And(barter_qualified, variables["both_parties_transferred_goods"])
    )
    solver.add(
        eviction_remedy_available
        == And(
            barter_qualified,
            variables["received_good_evicted_by_third_party"],
            variables["eviction_ground_arose_before_performance"],
        )
    )
    solver.add(
        requires_human_barter_assessment
        == Or(
            price_difference_obligation,
            second_party_may_suspend_transfer,
            eviction_remedy_available,
            And(barter_qualified, variables["contrary_to_barter_essence"]),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return BarterEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            barter_qualified=False,
            sale_rules_apply=False,
            equal_value_presumption_applies=False,
            price_difference_obligation=False,
            counter_performance_rules_apply=False,
            second_party_may_suspend_transfer=False,
            ownership_transfers_simultaneously=False,
            eviction_remedy_available=False,
            requires_human_barter_assessment=True,
            reasons_ru=["Набор фактов о мене противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как мена: каждая сторона обязуется передать в собственность "
            "другой стороны один товар в обмен на другой (статья 567 ГК РФ)."
            if truth(barter_qualified)
            else "Отношения не квалифицированы как договор мены."
        ),
    ]
    if truth(sale_rules_apply):
        reasons_ru.append(
            "К договору мены применяются правила о купле-продаже; каждая сторона признаётся "
            "продавцом передаваемого и покупателем принимаемого товара (статья 567 ГК РФ)."
        )
    if truth(equal_value_presumption_applies):
        reasons_ru.append(
            "Обмениваемые товары признаются равноценными, если из договора не вытекает иное "
            "(статья 568 ГК РФ)."
        )
    if truth(price_difference_obligation):
        reasons_ru.append(
            "При неравноценности товаров сторона, передающая товар меньшей цены, обязана "
            "оплатить разницу в цене (статья 568 ГК РФ)."
        )
    if truth(counter_performance_rules_apply):
        reasons_ru.append(
            "При несовпадении сроков передачи к передаче товара применяются правила о встречном "
            "исполнении обязательств (статья 569 ГК РФ, статья 328 ГК РФ)."
        )
    if truth(second_party_may_suspend_transfer):
        reasons_ru.append(
            "Сторона, обязанная передать товар после другой стороны, вправе приостановить "
            "передачу или отказаться от исполнения, если первая сторона не передала товар "
            "(статья 569 ГК РФ)."
        )
    if truth(ownership_transfers_simultaneously):
        reasons_ru.append(
            "Право собственности на обмениваемые товары переходит к сторонам одновременно после "
            "исполнения обязательств передать товары обеими сторонами (статья 570 ГК РФ)."
        )
    if truth(eviction_remedy_available):
        reasons_ru.append(
            "При изъятии третьим лицом товара по основанию, возникшему до исполнения договора, "
            "сторона вправе требовать возврата полученного в обмен товара и (или) возмещения "
            "убытков (статья 571 ГК РФ)."
        )
    return BarterEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        barter_qualified=truth(barter_qualified),
        sale_rules_apply=truth(sale_rules_apply),
        equal_value_presumption_applies=truth(equal_value_presumption_applies),
        price_difference_obligation=truth(price_difference_obligation),
        counter_performance_rules_apply=truth(counter_performance_rules_apply),
        second_party_may_suspend_transfer=truth(second_party_may_suspend_transfer),
        ownership_transfers_simultaneously=truth(ownership_transfers_simultaneously),
        eviction_remedy_available=truth(eviction_remedy_available),
        requires_human_barter_assessment=truth(requires_human_barter_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о мене и не заменяет судебную оценку.",
            "Равноценность товаров, размер разницы в цене и основания изъятия оцениваются "
            "экспертом и судом.",
        ],
    )
