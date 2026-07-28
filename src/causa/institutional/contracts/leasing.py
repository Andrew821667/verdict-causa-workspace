from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


LEASING_EVIDENCE_SCHEMA_VERSION = "contracts.leasing-evidence.v0"
LEASING_MAPPING_VERSION = "contracts-reviewed-leasing-to-facts-v0"
LEASING_MODEL_VERSION = "contracts-leasing-articles-665-670-v0"


class LeasingEvidencePredicate(str, Enum):
    # Понятие и предмет лизинга (статьи 665 и 666 ГК РФ).
    PROPERTY_ACQUIRED_FOR_LESSEE_AND_LEASED = "property_acquired_for_lessee_and_leased"
    LEASED_OBJECT_IS_NON_CONSUMABLE_THING = "leased_object_is_non_consumable_thing"
    OBJECT_EXCLUDED_FROM_LEASING = "object_excluded_from_leasing"
    # Уведомление продавца и выбор стороны (статьи 667 и 670 ГК РФ).
    SELLER_NOT_NOTIFIED_OF_LEASING_PURPOSE = "seller_not_notified_of_leasing_purpose"
    LESSOR_SELECTED_SELLER = "lessor_selected_seller"
    # Передача предмета лизинга и риски (статьи 668 и 669 ГК РФ).
    OBJECT_NOT_DELIVERED_IN_TIME = "object_not_delivered_in_time"
    DELAY_ATTRIBUTABLE_TO_LESSOR = "delay_attributable_to_lessor"
    RISK_ALLOCATION_DISPUTED_BEFORE_TRANSFER = "risk_allocation_disputed_before_transfer"
    # Требования к продавцу и ответственность (статья 670 ГК РФ).
    LESSEE_DENIED_DIRECT_CLAIM_AGAINST_SELLER = "lessee_denied_direct_claim_against_seller"
    SELLER_BREACHED_OBLIGATIONS = "seller_breached_obligations"


REQUIRED_LEASING_PREDICATES = frozenset(LeasingEvidencePredicate)


class LeasingEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: LeasingEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedLeasingEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = LEASING_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[LeasingEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedLeasingEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Leasing evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Leasing evidence contains duplicate legal source refs.")
        return self


class LeasingFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    property_acquired_for_lessee_and_leased: bool
    leased_object_is_non_consumable_thing: bool
    object_excluded_from_leasing: bool
    seller_not_notified_of_leasing_purpose: bool
    lessor_selected_seller: bool
    object_not_delivered_in_time: bool
    delay_attributable_to_lessor: bool
    risk_allocation_disputed_before_transfer: bool
    lessee_denied_direct_claim_against_seller: bool
    seller_breached_obligations: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "LeasingFactSet":
        if self.delay_attributable_to_lessor and not self.object_not_delivered_in_time:
            raise ValueError(
                "Ответственность лизингодателя за просрочку относится только к случаю "
                "непередачи предмета лизинга в установленный срок."
            )
        if self.leased_object_is_non_consumable_thing and self.object_excluded_from_leasing:
            raise ValueError(
                "Предмет лизинга не может одновременно быть допустимой непотребляемой вещью и "
                "объектом, изъятым из круга предметов лизинга."
            )
        return self


class LeasingFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class LeasingEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: LeasingFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[LeasingFactProvenance] = Field(default_factory=list)


class LeasingConstraintSet(BaseModel):
    id: str
    model_version: str = LEASING_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class LeasingEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    leasing_qualified: bool
    object_not_eligible_for_leasing: bool
    seller_notice_not_given: bool
    delivery_default_attributable_to_lessor: bool
    risk_transfer_rule_applies: bool
    lessee_direct_claim_wrongly_denied: bool
    lessor_solidarily_liable_for_seller: bool
    requires_human_leasing_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_leasing_evidence(
    evidence: ReviewedLeasingEvidence,
) -> LeasingEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Leasing evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Leasing evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_LEASING_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed leasing evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_LEASING_PREDICATES
    }
    return LeasingEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=LEASING_MAPPING_VERSION,
        facts=LeasingFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            LeasingFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_LEASING_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_leasing_constraint_set(
    mapping: LeasingEvidenceMappingResult,
) -> LeasingConstraintSet:
    return LeasingConstraintSet(
        id=f"leasing-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "leasing_qualified == property_acquired_for_lessee_and_leased",
            "object_not_eligible_for_leasing == leasing_qualified AND object_excluded_from_leasing",
            "seller_notice_not_given == leasing_qualified AND seller_not_notified_of_leasing_purpose",
            "delivery_default_attributable_to_lessor == leasing_qualified AND object_not_delivered_in_time AND delay_attributable_to_lessor",
            "risk_transfer_rule_applies == leasing_qualified AND risk_allocation_disputed_before_transfer",
            "lessee_direct_claim_wrongly_denied == leasing_qualified AND lessee_denied_direct_claim_against_seller",
            "lessor_solidarily_liable_for_seller == leasing_qualified AND lessor_selected_seller AND seller_breached_obligations",
            "requires_human_leasing_assessment == object_not_eligible_for_leasing OR seller_notice_not_given OR delivery_default_attributable_to_lessor OR risk_transfer_rule_applies OR lessee_direct_claim_wrongly_denied OR lessor_solidarily_liable_for_seller",
        ],
    )


def evaluate_leasing_constraints(
    constraint_set: LeasingConstraintSet,
    facts: LeasingFactSet,
) -> LeasingEvaluation:
    variables = {field_name: Bool(field_name) for field_name in LeasingFactSet.model_fields}
    leasing_qualified = Bool("leasing_qualified")
    object_not_eligible_for_leasing = Bool("object_not_eligible_for_leasing")
    seller_notice_not_given = Bool("seller_notice_not_given")
    delivery_default_attributable_to_lessor = Bool("delivery_default_attributable_to_lessor")
    risk_transfer_rule_applies = Bool("risk_transfer_rule_applies")
    lessee_direct_claim_wrongly_denied = Bool("lessee_direct_claim_wrongly_denied")
    lessor_solidarily_liable_for_seller = Bool("lessor_solidarily_liable_for_seller")
    requires_human_leasing_assessment = Bool("requires_human_leasing_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(leasing_qualified == variables["property_acquired_for_lessee_and_leased"])
    solver.add(
        object_not_eligible_for_leasing
        == And(leasing_qualified, variables["object_excluded_from_leasing"])
    )
    solver.add(
        seller_notice_not_given
        == And(leasing_qualified, variables["seller_not_notified_of_leasing_purpose"])
    )
    solver.add(
        delivery_default_attributable_to_lessor
        == And(
            leasing_qualified,
            variables["object_not_delivered_in_time"],
            variables["delay_attributable_to_lessor"],
        )
    )
    solver.add(
        risk_transfer_rule_applies
        == And(leasing_qualified, variables["risk_allocation_disputed_before_transfer"])
    )
    solver.add(
        lessee_direct_claim_wrongly_denied
        == And(leasing_qualified, variables["lessee_denied_direct_claim_against_seller"])
    )
    solver.add(
        lessor_solidarily_liable_for_seller
        == And(
            leasing_qualified,
            variables["lessor_selected_seller"],
            variables["seller_breached_obligations"],
        )
    )
    solver.add(
        requires_human_leasing_assessment
        == Or(
            object_not_eligible_for_leasing,
            seller_notice_not_given,
            delivery_default_attributable_to_lessor,
            risk_transfer_rule_applies,
            lessee_direct_claim_wrongly_denied,
            lessor_solidarily_liable_for_seller,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return LeasingEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            leasing_qualified=False,
            object_not_eligible_for_leasing=False,
            seller_notice_not_given=False,
            delivery_default_attributable_to_lessor=False,
            risk_transfer_rule_applies=False,
            lessee_direct_claim_wrongly_denied=False,
            lessor_solidarily_liable_for_seller=False,
            requires_human_leasing_assessment=True,
            reasons_ru=["Набор фактов о финансовой аренде противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как финансовая аренда (лизинг): арендодатель обязуется "
            "приобрести в собственность указанное арендатором имущество у определённого им "
            "продавца и предоставить его арендатору за плату во временное владение и "
            "пользование (статья 665 ГК РФ)."
            if truth(leasing_qualified)
            else "Отношения не квалифицированы как финансовая аренда (лизинг)."
        ),
    ]
    if truth(object_not_eligible_for_leasing):
        reasons_ru.append(
            "Предметом договора финансовой аренды могут быть любые непотребляемые вещи, кроме "
            "земельных участков и других природных объектов; выбранный объект не может быть "
            "предметом лизинга (статья 666 ГК РФ)."
        )
    if truth(seller_notice_not_given):
        reasons_ru.append(
            "Арендодатель, приобретая имущество для арендатора, должен уведомить продавца о том, "
            "что имущество предназначено для передачи в аренду определённому лицу (статья 667 "
            "ГК РФ)."
        )
    if truth(delivery_default_attributable_to_lessor):
        reasons_ru.append(
            "Имущество не передано арендатору в указанный срок по обстоятельствам, за которые "
            "отвечает арендодатель; арендатор вправе потребовать расторжения договора и "
            "возмещения убытков (статья 668 ГК РФ)."
        )
    if truth(risk_transfer_rule_applies):
        reasons_ru.append(
            "Риск случайной гибели или порчи имущества переходит к арендатору в момент передачи "
            "ему предмета лизинга, если иное не предусмотрено договором (статья 669 ГК РФ)."
        )
    if truth(lessee_direct_claim_wrongly_denied):
        reasons_ru.append(
            "Арендатор вправе предъявлять непосредственно продавцу требования, вытекающие из "
            "договора купли-продажи предмета лизинга, в отношении качества и комплектности "
            "имущества, сроков его поставки и в других случаях ненадлежащего исполнения "
            "(статья 670 ГК РФ)."
        )
    if truth(lessor_solidarily_liable_for_seller):
        reasons_ru.append(
            "Если выбор продавца осуществлялся арендодателем, арендатор вправе предъявить "
            "требования, вытекающие из договора купли-продажи, как продавцу, так и арендодателю, "
            "которые несут солидарную ответственность (статья 670 ГК РФ)."
        )
    return LeasingEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        leasing_qualified=truth(leasing_qualified),
        object_not_eligible_for_leasing=truth(object_not_eligible_for_leasing),
        seller_notice_not_given=truth(seller_notice_not_given),
        delivery_default_attributable_to_lessor=truth(delivery_default_attributable_to_lessor),
        risk_transfer_rule_applies=truth(risk_transfer_rule_applies),
        lessee_direct_claim_wrongly_denied=truth(lessee_direct_claim_wrongly_denied),
        lessor_solidarily_liable_for_seller=truth(lessor_solidarily_liable_for_seller),
        requires_human_leasing_assessment=truth(requires_human_leasing_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о финансовой аренде и не заменяет "
            "судебную оценку.",
            "Размер лизинговых платежей, распределение конкретных рисков и объём требований к "
            "продавцу оцениваются экспертом и судом (статьи 665, 669 и 670 ГК РФ).",
        ],
    )
