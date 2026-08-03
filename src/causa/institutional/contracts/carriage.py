from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


CARRIAGE_EVIDENCE_SCHEMA_VERSION = "contracts.carriage-evidence.v0"
CARRIAGE_MAPPING_VERSION = "contracts-reviewed-carriage-to-facts-v0"
CARRIAGE_MODEL_VERSION = "contracts-carriage-articles-784-800-v0"


class CarriageEvidencePredicate(str, Enum):
    # Понятие перевозки и транспортные документы (статьи 784–786 ГК РФ).
    CARRIAGE_OF_GOODS_OR_PASSENGER_FOR_FEE = "carriage_of_goods_or_passenger_for_fee"
    TRANSPORT_DOCUMENT_NOT_ISSUED = "transport_document_not_issued"
    # Транспорт общего пользования и провозная плата (статьи 789 и 790 ГК РФ).
    PUBLIC_CARRIER_REFUSED_WITHOUT_GROUNDS = "public_carrier_refused_without_grounds"
    CARRIAGE_CHARGE_OR_RETENTION_RULES_BREACHED = "carriage_charge_or_retention_rules_breached"
    # Подача транспортных средств и сроки доставки (статьи 791, 792 и 794 ГК РФ).
    VEHICLE_NOT_SUPPLIED_OR_NOT_USED = "vehicle_not_supplied_or_not_used"
    DELIVERY_DEADLINE_MISSED = "delivery_deadline_missed"
    # Задержка отправления пассажира и сохранность груза (статьи 795 и 796 ГК РФ).
    PASSENGER_DEPARTURE_DELAYED = "passenger_departure_delayed"
    CARGO_LOST_SHORT_OR_DAMAGED = "cargo_lost_short_or_damaged"
    CARRIER_FAULT_NOT_DISPROVED_FOR_CARGO_LOSS = "carrier_fault_not_disproved_for_cargo_loss"
    # Соглашения об ограничении ответственности перевозчика (статья 793 ГК РФ).
    LIABILITY_LIMITATION_AGREEMENT_PRESENT = "liability_limitation_agreement_present"


REQUIRED_CARRIAGE_PREDICATES = frozenset(CarriageEvidencePredicate)


class CarriageEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: CarriageEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCarriageEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CARRIAGE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CarriageEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedCarriageEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Carriage evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Carriage evidence contains duplicate legal source refs.")
        return self


class CarriageFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    carriage_of_goods_or_passenger_for_fee: bool
    transport_document_not_issued: bool
    public_carrier_refused_without_grounds: bool
    carriage_charge_or_retention_rules_breached: bool
    vehicle_not_supplied_or_not_used: bool
    delivery_deadline_missed: bool
    passenger_departure_delayed: bool
    cargo_lost_short_or_damaged: bool
    carrier_fault_not_disproved_for_cargo_loss: bool
    liability_limitation_agreement_present: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "CarriageFactSet":
        if self.carrier_fault_not_disproved_for_cargo_loss and not self.cargo_lost_short_or_damaged:
            raise ValueError(
                "Недоказанность отсутствия вины перевозчика относится только к случаю, когда "
                "утрата, недостача или повреждение груза либо багажа установлены."
            )
        if self.transport_document_not_issued and not self.carriage_of_goods_or_passenger_for_fee:
            raise ValueError(
                "Отсутствие транспортной накладной, билета или багажной квитанции относится "
                "только к договору перевозки."
            )
        return self


class CarriageFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class CarriageEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: CarriageFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[CarriageFactProvenance] = Field(default_factory=list)


class CarriageConstraintSet(BaseModel):
    id: str
    model_version: str = CARRIAGE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class CarriageEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    carriage_qualified: bool
    transport_document_duty_breached: bool
    public_carriage_refusal_unlawful: bool
    charge_or_retention_rules_breached: bool
    vehicle_supply_duty_breached: bool
    delivery_deadline_breached: bool
    passenger_delay_liability: bool
    cargo_damage_established: bool
    carrier_liable_for_cargo_loss: bool
    liability_limitation_void: bool
    requires_human_carriage_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_carriage_evidence(
    evidence: ReviewedCarriageEvidence,
) -> CarriageEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Carriage evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Carriage evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_CARRIAGE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed carriage evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_CARRIAGE_PREDICATES
    }
    return CarriageEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CARRIAGE_MAPPING_VERSION,
        facts=CarriageFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            CarriageFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_CARRIAGE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_carriage_constraint_set(
    mapping: CarriageEvidenceMappingResult,
) -> CarriageConstraintSet:
    return CarriageConstraintSet(
        id=f"carriage-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "carriage_qualified == carriage_of_goods_or_passenger_for_fee",
            "transport_document_duty_breached == carriage_qualified AND transport_document_not_issued",
            "public_carriage_refusal_unlawful == carriage_qualified AND public_carrier_refused_without_grounds",
            "charge_or_retention_rules_breached == carriage_qualified AND carriage_charge_or_retention_rules_breached",
            "vehicle_supply_duty_breached == carriage_qualified AND vehicle_not_supplied_or_not_used",
            "delivery_deadline_breached == carriage_qualified AND delivery_deadline_missed",
            "passenger_delay_liability == carriage_qualified AND passenger_departure_delayed",
            "cargo_damage_established == carriage_qualified AND cargo_lost_short_or_damaged",
            "carrier_liable_for_cargo_loss == carriage_qualified AND cargo_lost_short_or_damaged AND carrier_fault_not_disproved_for_cargo_loss",
            "liability_limitation_void == carriage_qualified AND liability_limitation_agreement_present",
            "requires_human_carriage_assessment == transport_document_duty_breached OR public_carriage_refusal_unlawful OR charge_or_retention_rules_breached OR vehicle_supply_duty_breached OR delivery_deadline_breached OR passenger_delay_liability OR cargo_damage_established OR liability_limitation_void",
        ],
    )


def evaluate_carriage_constraints(
    constraint_set: CarriageConstraintSet,
    facts: CarriageFactSet,
) -> CarriageEvaluation:
    variables = {field_name: Bool(field_name) for field_name in CarriageFactSet.model_fields}
    carriage_qualified = Bool("carriage_qualified")
    transport_document_duty_breached = Bool("transport_document_duty_breached")
    public_carriage_refusal_unlawful = Bool("public_carriage_refusal_unlawful")
    charge_or_retention_rules_breached = Bool("charge_or_retention_rules_breached")
    vehicle_supply_duty_breached = Bool("vehicle_supply_duty_breached")
    delivery_deadline_breached = Bool("delivery_deadline_breached")
    passenger_delay_liability = Bool("passenger_delay_liability")
    cargo_damage_established = Bool("cargo_damage_established")
    carrier_liable_for_cargo_loss = Bool("carrier_liable_for_cargo_loss")
    liability_limitation_void = Bool("liability_limitation_void")
    requires_human_carriage_assessment = Bool("requires_human_carriage_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(carriage_qualified == variables["carriage_of_goods_or_passenger_for_fee"])
    solver.add(
        transport_document_duty_breached
        == And(carriage_qualified, variables["transport_document_not_issued"])
    )
    solver.add(
        public_carriage_refusal_unlawful
        == And(carriage_qualified, variables["public_carrier_refused_without_grounds"])
    )
    solver.add(
        charge_or_retention_rules_breached
        == And(carriage_qualified, variables["carriage_charge_or_retention_rules_breached"])
    )
    solver.add(
        vehicle_supply_duty_breached
        == And(carriage_qualified, variables["vehicle_not_supplied_or_not_used"])
    )
    solver.add(
        delivery_deadline_breached == And(carriage_qualified, variables["delivery_deadline_missed"])
    )
    solver.add(
        passenger_delay_liability
        == And(carriage_qualified, variables["passenger_departure_delayed"])
    )
    solver.add(
        cargo_damage_established
        == And(carriage_qualified, variables["cargo_lost_short_or_damaged"])
    )
    solver.add(
        carrier_liable_for_cargo_loss
        == And(
            carriage_qualified,
            variables["cargo_lost_short_or_damaged"],
            variables["carrier_fault_not_disproved_for_cargo_loss"],
        )
    )
    solver.add(
        liability_limitation_void
        == And(carriage_qualified, variables["liability_limitation_agreement_present"])
    )
    solver.add(
        requires_human_carriage_assessment
        == Or(
            transport_document_duty_breached,
            public_carriage_refusal_unlawful,
            charge_or_retention_rules_breached,
            vehicle_supply_duty_breached,
            delivery_deadline_breached,
            passenger_delay_liability,
            cargo_damage_established,
            liability_limitation_void,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return CarriageEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            carriage_qualified=False,
            transport_document_duty_breached=False,
            public_carriage_refusal_unlawful=False,
            charge_or_retention_rules_breached=False,
            vehicle_supply_duty_breached=False,
            delivery_deadline_breached=False,
            passenger_delay_liability=False,
            cargo_damage_established=False,
            carrier_liable_for_cargo_loss=False,
            liability_limitation_void=False,
            requires_human_carriage_assessment=True,
            reasons_ru=["Набор фактов о перевозке противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Отношения квалифицированы как перевозка: перевозчик обязуется доставить вверенный "
            "ему отправителем груз в пункт назначения и выдать его получателю либо перевезти "
            "пассажира и его багаж, а отправитель или пассажир — уплатить установленную плату "
            "(статьи 784–786 ГК РФ)."
            if truth(carriage_qualified)
            else "Отношения не квалифицированы как договор перевозки."
        ),
    ]
    if truth(transport_document_duty_breached):
        reasons_ru.append(
            "Заключение договора перевозки подтверждается составлением транспортной накладной, "
            "коносамента или иного документа, а перевозка пассажира — билетом и багажной "
            "квитанцией (статьи 785 и 786 ГК РФ)."
        )
    if truth(public_carriage_refusal_unlawful):
        reasons_ru.append(
            "Перевозка транспортом общего пользования является публичным договором: перевозчик "
            "обязан осуществлять перевозки по обращению любого гражданина или юридического лица "
            "(статья 789 ГК РФ)."
        )
    if truth(charge_or_retention_rules_breached):
        reasons_ru.append(
            "Провозная плата взимается по соглашению сторон, а для транспорта общего пользования "
            "— по утверждённым тарифам; удержание груза и багажа допускается только в "
            "установленных случаях (статья 790 ГК РФ)."
        )
    if truth(vehicle_supply_duty_breached):
        reasons_ru.append(
            "Перевозчик обязан подать отправителю исправные транспортные средства в срок, а "
            "отправитель — использовать поданные средства; их неподача или неиспользование "
            "влечёт ответственность сторон (статьи 791 и 794 ГК РФ)."
        )
    if truth(delivery_deadline_breached):
        reasons_ru.append(
            "Перевозчик обязан доставить груз, пассажира или багаж в пункт назначения в сроки, "
            "определённые транспортными уставами и кодексами либо договором, а при их отсутствии "
            "— в разумный срок (статья 792 ГК РФ)."
        )
    if truth(passenger_delay_liability):
        reasons_ru.append(
            "За задержку отправления транспортного средства, перевозящего пассажира, перевозчик "
            "уплачивает штраф, если не докажет, что задержка произошла вследствие обстоятельств, "
            "которые он не мог предотвратить (статья 795 ГК РФ)."
        )
    if truth(cargo_damage_established):
        reasons_ru.append(
            "Установлены утрата, недостача или повреждение (порча) груза либо багажа, что влечёт "
            "проверку ответственности перевозчика и размера возмещения (статья 796 ГК РФ)."
        )
    if truth(carrier_liable_for_cargo_loss):
        reasons_ru.append(
            "Перевозчик не доказал, что утрата, недостача или повреждение груза либо багажа "
            "произошли вследствие обстоятельств, которые он не мог предотвратить и устранение "
            "которых от него не зависело, и отвечает за них (статья 796 ГК РФ)."
        )
    if truth(liability_limitation_void):
        reasons_ru.append(
            "Соглашения об ограничении или устранении установленной законом ответственности "
            "перевозчика недействительны, за исключением случаев, прямо предусмотренных "
            "транспортными уставами и кодексами (статья 793 ГК РФ)."
        )
    return CarriageEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        carriage_qualified=truth(carriage_qualified),
        transport_document_duty_breached=truth(transport_document_duty_breached),
        public_carriage_refusal_unlawful=truth(public_carriage_refusal_unlawful),
        charge_or_retention_rules_breached=truth(charge_or_retention_rules_breached),
        vehicle_supply_duty_breached=truth(vehicle_supply_duty_breached),
        delivery_deadline_breached=truth(delivery_deadline_breached),
        passenger_delay_liability=truth(passenger_delay_liability),
        cargo_damage_established=truth(cargo_damage_established),
        carrier_liable_for_cargo_loss=truth(carrier_liable_for_cargo_loss),
        liability_limitation_void=truth(liability_limitation_void),
        requires_human_carriage_assessment=truth(requires_human_carriage_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только общие положения ГК РФ о перевозке и не заменяет судебную "
            "оценку.",
            "Транспортные уставы и кодексы, размер возмещения и обстоятельства, которые "
            "перевозчик не мог предотвратить, оцениваются экспертом и судом (статьи 784, 793 и "
            "796 ГК РФ).",
        ],
    )
