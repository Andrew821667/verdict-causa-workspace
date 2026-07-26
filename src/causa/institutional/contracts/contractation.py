from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


CONTRACTATION_EVIDENCE_SCHEMA_VERSION = "contracts.contractation-evidence.v0"
CONTRACTATION_MAPPING_VERSION = "contracts-reviewed-contractation-to-facts-v0"
CONTRACTATION_MODEL_VERSION = "contracts-contractation-articles-535-538-v0"


class ContractationEvidencePredicate(str, Enum):
    # Понятие договора контрактации (статья 535 ГК РФ).
    AGRICULTURAL_PRODUCER_CONTRACT = "agricultural_producer_contract"
    GOODS_ARE_OWN_GROWN_PRODUCE = "goods_are_own_grown_produce"
    # Обязанности заготовителя (статья 536 ГК РФ).
    PROCURER_TOOK_DELIVERY_AT_PRODUCER_LOCATION = "procurer_took_delivery_at_producer_location"
    GOODS_CONFORM_AND_TIMELY = "goods_conform_and_timely"
    PROCURER_REFUSED_CONFORMING_GOODS = "procurer_refused_conforming_goods"
    PROCESSING_WASTE_RETURN_AGREED = "processing_waste_return_agreed"
    PROCURER_RETURNED_WASTE = "procurer_returned_waste"
    # Обязанности и ответственность производителя (статьи 537 и 538 ГК РФ).
    PRODUCER_DELIVERED_QUANTITY_AND_ASSORTMENT = "producer_delivered_quantity_and_assortment"
    PRODUCER_BREACHED = "producer_breached"
    PRODUCER_AT_FAULT = "producer_at_fault"


REQUIRED_CONTRACTATION_PREDICATES = frozenset(ContractationEvidencePredicate)


class ContractationEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ContractationEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedContractationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CONTRACTATION_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ContractationEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedContractationEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Contractation evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Contractation evidence contains duplicate legal source refs.")
        return self


class ContractationFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    agricultural_producer_contract: bool
    goods_are_own_grown_produce: bool
    procurer_took_delivery_at_producer_location: bool
    goods_conform_and_timely: bool
    procurer_refused_conforming_goods: bool
    processing_waste_return_agreed: bool
    procurer_returned_waste: bool
    producer_delivered_quantity_and_assortment: bool
    producer_breached: bool
    producer_at_fault: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ContractationFactSet":
        if self.producer_at_fault and not self.producer_breached:
            raise ValueError("Вина производителя учитывается только при нарушении обязательства.")
        return self


class ContractationFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ContractationEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ContractationFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ContractationFactProvenance] = Field(default_factory=list)


class ContractationConstraintSet(BaseModel):
    id: str
    model_version: str = CONTRACTATION_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ContractationEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    contractation_qualified: bool
    procurer_acceptance_duty_met: bool
    procurer_refusal_unlawful: bool
    waste_return_obligation: bool
    waste_return_performed: bool
    producer_delivery_duty_met: bool
    producer_liable_only_if_at_fault: bool
    requires_human_contractation_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_contractation_evidence(
    evidence: ReviewedContractationEvidence,
) -> ContractationEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Contractation evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Contractation evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_CONTRACTATION_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed contractation evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_CONTRACTATION_PREDICATES
    }
    return ContractationEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CONTRACTATION_MAPPING_VERSION,
        facts=ContractationFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ContractationFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_CONTRACTATION_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_contractation_constraint_set(
    mapping: ContractationEvidenceMappingResult,
) -> ContractationConstraintSet:
    return ContractationConstraintSet(
        id=f"contractation-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "contractation_qualified == agricultural_producer_contract AND goods_are_own_grown_produce",
            "procurer_acceptance_duty_met == procurer_took_delivery_at_producer_location",
            "procurer_refusal_unlawful == procurer_refused_conforming_goods AND goods_conform_and_timely",
            "waste_return_obligation == processing_waste_return_agreed",
            "waste_return_performed == processing_waste_return_agreed AND procurer_returned_waste",
            "producer_delivery_duty_met == producer_delivered_quantity_and_assortment",
            "producer_liable_only_if_at_fault == producer_breached AND producer_at_fault",
            "requires_human_contractation_assessment == procurer_refused_conforming_goods OR producer_breached OR (processing_waste_return_agreed AND NOT procurer_returned_waste)",
        ],
    )


def evaluate_contractation_constraints(
    constraint_set: ContractationConstraintSet,
    facts: ContractationFactSet,
) -> ContractationEvaluation:
    variables = {field_name: Bool(field_name) for field_name in ContractationFactSet.model_fields}
    contractation_qualified = Bool("contractation_qualified")
    procurer_acceptance_duty_met = Bool("procurer_acceptance_duty_met")
    procurer_refusal_unlawful = Bool("procurer_refusal_unlawful")
    waste_return_obligation = Bool("waste_return_obligation")
    waste_return_performed = Bool("waste_return_performed")
    producer_delivery_duty_met = Bool("producer_delivery_duty_met")
    producer_liable_only_if_at_fault = Bool("producer_liable_only_if_at_fault")
    requires_human_contractation_assessment = Bool("requires_human_contractation_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        contractation_qualified
        == And(
            variables["agricultural_producer_contract"],
            variables["goods_are_own_grown_produce"],
        )
    )
    solver.add(
        procurer_acceptance_duty_met == variables["procurer_took_delivery_at_producer_location"]
    )
    solver.add(
        procurer_refusal_unlawful
        == And(
            variables["procurer_refused_conforming_goods"],
            variables["goods_conform_and_timely"],
        )
    )
    solver.add(waste_return_obligation == variables["processing_waste_return_agreed"])
    solver.add(
        waste_return_performed
        == And(
            variables["processing_waste_return_agreed"],
            variables["procurer_returned_waste"],
        )
    )
    solver.add(
        producer_delivery_duty_met == variables["producer_delivered_quantity_and_assortment"]
    )
    solver.add(
        producer_liable_only_if_at_fault
        == And(variables["producer_breached"], variables["producer_at_fault"])
    )
    solver.add(
        requires_human_contractation_assessment
        == Or(
            variables["procurer_refused_conforming_goods"],
            variables["producer_breached"],
            And(
                variables["processing_waste_return_agreed"],
                Not(variables["procurer_returned_waste"]),
            ),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ContractationEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            contractation_qualified=False,
            procurer_acceptance_duty_met=False,
            procurer_refusal_unlawful=False,
            waste_return_obligation=False,
            waste_return_performed=False,
            producer_delivery_duty_met=False,
            producer_liable_only_if_at_fault=False,
            requires_human_contractation_assessment=True,
            reasons_ru=["Набор фактов о контрактации противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как контрактация: производитель передаёт заготовителю "
            "выращенную (произведённую) им сельскохозяйственную продукцию (статья 535 ГК РФ)."
            if truth(contractation_qualified)
            else "Отношения не квалифицированы как договор контрактации."
        ),
    ]
    if truth(procurer_acceptance_duty_met):
        reasons_ru.append(
            "Заготовитель принял продукцию по месту нахождения производителя и обеспечил "
            "её вывоз (статья 536 ГК РФ)."
        )
    if truth(procurer_refusal_unlawful):
        reasons_ru.append(
            "Заготовитель не вправе отказаться от принятия сельскохозяйственной продукции, "
            "соответствующей условиям договора и переданной в срок (статья 536 ГК РФ)."
        )
    if truth(waste_return_obligation):
        reasons_ru.append(
            "Договором предусмотрена обязанность заготовителя возвращать производителю "
            "отходы переработки с оплатой (статья 536 ГК РФ)."
        )
    if truth(waste_return_performed):
        reasons_ru.append("Отходы переработки возвращены производителю.")
    if truth(producer_delivery_duty_met):
        reasons_ru.append(
            "Производитель передал заготовителю продукцию в количестве и ассортименте, "
            "предусмотренных договором (статья 537 ГК РФ)."
        )
    if truth(producer_liable_only_if_at_fault):
        reasons_ru.append(
            "Производитель, не исполнивший обязательство, несёт ответственность при "
            "наличии его вины (статья 538 ГК РФ)."
        )
    return ContractationEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        contractation_qualified=truth(contractation_qualified),
        procurer_acceptance_duty_met=truth(procurer_acceptance_duty_met),
        procurer_refusal_unlawful=truth(procurer_refusal_unlawful),
        waste_return_obligation=truth(waste_return_obligation),
        waste_return_performed=truth(waste_return_performed),
        producer_delivery_duty_met=truth(producer_delivery_duty_met),
        producer_liable_only_if_at_fault=truth(producer_liable_only_if_at_fault),
        requires_human_contractation_assessment=truth(requires_human_contractation_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о контрактации и не заменяет "
            "судебную оценку.",
            "Соответствие продукции, вина производителя и условия возврата отходов "
            "оцениваются экспертом и судом.",
        ],
    )
