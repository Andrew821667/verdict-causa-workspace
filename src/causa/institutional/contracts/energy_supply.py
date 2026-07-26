from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


ENERGY_SUPPLY_EVIDENCE_SCHEMA_VERSION = "contracts.energy-supply-evidence.v0"
ENERGY_SUPPLY_MAPPING_VERSION = "contracts-reviewed-energy-supply-to-facts-v0"
ENERGY_SUPPLY_MODEL_VERSION = "contracts-energy-supply-articles-539-548-v0"


class EnergySupplyEvidencePredicate(str, Enum):
    # Понятие договора энергоснабжения (статья 539 ГК РФ).
    ENERGY_SUPPLIED_THROUGH_ATTACHED_NETWORK = "energy_supplied_through_attached_network"
    SUBSCRIBER_HAS_COMPLIANT_RECEIVING_DEVICE = "subscriber_has_compliant_receiving_device"
    # Количество и качество энергии (статьи 541 и 542 ГК РФ).
    ENERGY_QUANTITY_CONFORMS_TO_CONTRACT = "energy_quantity_conforms_to_contract"
    ENERGY_QUALITY_DEFECTIVE = "energy_quality_defective"
    # Содержание сетей и оплата (статьи 543 и 544 ГК РФ).
    SUBSCRIBER_IS_HOUSEHOLD_CONSUMER = "subscriber_is_household_consumer"
    SUBSCRIBER_MAINTAINED_NETWORKS_AND_REGIME = "subscriber_maintained_networks_and_regime"
    SUBSCRIBER_PAID_FOR_METERED_ENERGY = "subscriber_paid_for_metered_energy"
    # Перерыв, прекращение и ограничение подачи (статья 546 ГК РФ).
    SUPPLY_INTERRUPTED = "supply_interrupted"
    SUPPLY_INTERRUPTION_AGREED = "supply_interruption_agreed"
    UNAGREED_INTERRUPTION_FOR_EMERGENCY_WITH_NOTICE = (
        "unagreed_interruption_for_emergency_with_notice"
    )


REQUIRED_ENERGY_SUPPLY_PREDICATES = frozenset(EnergySupplyEvidencePredicate)


class EnergySupplyEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: EnergySupplyEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedEnergySupplyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = ENERGY_SUPPLY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[EnergySupplyEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedEnergySupplyEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Energy supply evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Energy supply evidence contains duplicate legal source refs.")
        return self


class EnergySupplyFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    energy_supplied_through_attached_network: bool
    subscriber_has_compliant_receiving_device: bool
    energy_quantity_conforms_to_contract: bool
    energy_quality_defective: bool
    subscriber_is_household_consumer: bool
    subscriber_maintained_networks_and_regime: bool
    subscriber_paid_for_metered_energy: bool
    supply_interrupted: bool
    supply_interruption_agreed: bool
    unagreed_interruption_for_emergency_with_notice: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "EnergySupplyFactSet":
        if (
            self.supply_interruption_agreed or self.unagreed_interruption_for_emergency_with_notice
        ) and not self.supply_interrupted:
            raise ValueError(
                "Согласование или неотложность перерыва учитываются только при фактическом "
                "перерыве подачи энергии."
            )
        return self


class EnergySupplyFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class EnergySupplyEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: EnergySupplyFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[EnergySupplyFactProvenance] = Field(default_factory=list)


class EnergySupplyConstraintSet(BaseModel):
    id: str
    model_version: str = ENERGY_SUPPLY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class EnergySupplyEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    energy_supply_qualified: bool
    energy_conforms_to_contract: bool
    subscriber_may_refuse_defective_payment: bool
    subscriber_network_duty_met: bool
    payment_duty_met: bool
    supply_interruption_lawful: bool
    unlawful_supply_interruption: bool
    requires_human_energy_supply_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_energy_supply_evidence(
    evidence: ReviewedEnergySupplyEvidence,
) -> EnergySupplyEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Energy supply evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Energy supply evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_ENERGY_SUPPLY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed energy supply evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_ENERGY_SUPPLY_PREDICATES
    }
    return EnergySupplyEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=ENERGY_SUPPLY_MAPPING_VERSION,
        facts=EnergySupplyFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            EnergySupplyFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_ENERGY_SUPPLY_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_energy_supply_constraint_set(
    mapping: EnergySupplyEvidenceMappingResult,
) -> EnergySupplyConstraintSet:
    return EnergySupplyConstraintSet(
        id=f"energy-supply-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "energy_supply_qualified == energy_supplied_through_attached_network AND subscriber_has_compliant_receiving_device",
            "energy_conforms_to_contract == energy_supply_qualified AND energy_quantity_conforms_to_contract AND NOT energy_quality_defective",
            "subscriber_may_refuse_defective_payment == energy_supply_qualified AND energy_quality_defective",
            "subscriber_network_duty_met == subscriber_is_household_consumer OR subscriber_maintained_networks_and_regime",
            "payment_duty_met == subscriber_paid_for_metered_energy",
            "supply_interruption_lawful == NOT supply_interrupted OR supply_interruption_agreed OR unagreed_interruption_for_emergency_with_notice",
            "unlawful_supply_interruption == supply_interrupted AND NOT supply_interruption_agreed AND NOT unagreed_interruption_for_emergency_with_notice",
            "requires_human_energy_supply_assessment == (energy_supply_qualified AND energy_quality_defective) OR unlawful_supply_interruption",
        ],
    )


def evaluate_energy_supply_constraints(
    constraint_set: EnergySupplyConstraintSet,
    facts: EnergySupplyFactSet,
) -> EnergySupplyEvaluation:
    variables = {field_name: Bool(field_name) for field_name in EnergySupplyFactSet.model_fields}
    energy_supply_qualified = Bool("energy_supply_qualified")
    energy_conforms_to_contract = Bool("energy_conforms_to_contract")
    subscriber_may_refuse_defective_payment = Bool("subscriber_may_refuse_defective_payment")
    subscriber_network_duty_met = Bool("subscriber_network_duty_met")
    payment_duty_met = Bool("payment_duty_met")
    supply_interruption_lawful = Bool("supply_interruption_lawful")
    unlawful_supply_interruption = Bool("unlawful_supply_interruption")
    requires_human_energy_supply_assessment = Bool("requires_human_energy_supply_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        energy_supply_qualified
        == And(
            variables["energy_supplied_through_attached_network"],
            variables["subscriber_has_compliant_receiving_device"],
        )
    )
    solver.add(
        energy_conforms_to_contract
        == And(
            energy_supply_qualified,
            variables["energy_quantity_conforms_to_contract"],
            Not(variables["energy_quality_defective"]),
        )
    )
    solver.add(
        subscriber_may_refuse_defective_payment
        == And(energy_supply_qualified, variables["energy_quality_defective"])
    )
    solver.add(
        subscriber_network_duty_met
        == Or(
            variables["subscriber_is_household_consumer"],
            variables["subscriber_maintained_networks_and_regime"],
        )
    )
    solver.add(payment_duty_met == variables["subscriber_paid_for_metered_energy"])
    solver.add(
        supply_interruption_lawful
        == Or(
            Not(variables["supply_interrupted"]),
            variables["supply_interruption_agreed"],
            variables["unagreed_interruption_for_emergency_with_notice"],
        )
    )
    solver.add(
        unlawful_supply_interruption
        == And(
            variables["supply_interrupted"],
            Not(variables["supply_interruption_agreed"]),
            Not(variables["unagreed_interruption_for_emergency_with_notice"]),
        )
    )
    solver.add(
        requires_human_energy_supply_assessment
        == Or(
            And(energy_supply_qualified, variables["energy_quality_defective"]),
            unlawful_supply_interruption,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return EnergySupplyEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            energy_supply_qualified=False,
            energy_conforms_to_contract=False,
            subscriber_may_refuse_defective_payment=False,
            subscriber_network_duty_met=False,
            payment_duty_met=False,
            supply_interruption_lawful=False,
            unlawful_supply_interruption=False,
            requires_human_energy_supply_assessment=True,
            reasons_ru=["Набор фактов об энергоснабжении противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как энергоснабжение: энергоснабжающая организация подаёт "
            "энергию через присоединённую сеть, а у абонента имеется отвечающее требованиям "
            "энергопринимающее устройство и обеспечен учёт потребления (статья 539 ГК РФ)."
            if truth(energy_supply_qualified)
            else "Отношения не квалифицированы как договор энергоснабжения."
        ),
    ]
    if truth(energy_conforms_to_contract):
        reasons_ru.append(
            "Поданная энергия соответствует договору по количеству и качеству "
            "(статьи 541 и 542 ГК РФ)."
        )
    if truth(subscriber_may_refuse_defective_payment):
        reasons_ru.append(
            "При нарушении требований к качеству энергии абонент вправе отказаться от оплаты "
            "такой энергии (статья 542 ГК РФ)."
        )
    if truth(subscriber_network_duty_met):
        reasons_ru.append(
            "Обязанность по содержанию сетей и соблюдению режима потребления исполнена; для "
            "гражданина-бытового потребителя она возлагается на энергоснабжающую организацию "
            "(статья 543 ГК РФ)."
        )
    if truth(payment_duty_met):
        reasons_ru.append(
            "Оплата произведена за фактически принятое количество энергии по данным учёта "
            "(статья 544 ГК РФ)."
        )
    if truth(supply_interruption_lawful):
        reasons_ru.append(
            "Перерыв, прекращение или ограничение подачи энергии правомерны: по соглашению "
            "сторон либо как неотложная мера при аварии с немедленным уведомлением абонента "
            "(статья 546 ГК РФ)."
        )
    if truth(unlawful_supply_interruption):
        reasons_ru.append(
            "Перерыв, прекращение или ограничение подачи энергии произведены без согласования "
            "и без неотложной необходимости (статья 546 ГК РФ)."
        )
    return EnergySupplyEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        energy_supply_qualified=truth(energy_supply_qualified),
        energy_conforms_to_contract=truth(energy_conforms_to_contract),
        subscriber_may_refuse_defective_payment=truth(subscriber_may_refuse_defective_payment),
        subscriber_network_duty_met=truth(subscriber_network_duty_met),
        payment_duty_met=truth(payment_duty_met),
        supply_interruption_lawful=truth(supply_interruption_lawful),
        unlawful_supply_interruption=truth(unlawful_supply_interruption),
        requires_human_energy_supply_assessment=truth(requires_human_energy_supply_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила об энергоснабжении и не заменяет "
            "судебную оценку.",
            "По договору энергоснабжения нарушившая сторона возмещает причинённый реальный "
            "ущерб; вина и размер убытков оцениваются экспертом и судом (статья 547 ГК РФ).",
        ],
    )
