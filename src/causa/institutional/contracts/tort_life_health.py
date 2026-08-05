from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


TORT_LIFE_HEALTH_EVIDENCE_SCHEMA_VERSION = "contracts.tort-life-health-evidence.v0"
TORT_LIFE_HEALTH_MAPPING_VERSION = "contracts-reviewed-tort-life-health-to-facts-v0"
TORT_LIFE_HEALTH_MODEL_VERSION = "contracts-tort-life-health-articles-1084-1094-v0"


class TortLifeHealthEvidencePredicate(str, Enum):
    # Возмещение вреда, причинённого жизни или здоровью гражданина
    # (статьи 1084 и 1085 ГК РФ).
    LIFE_OR_HEALTH_HARM_ESTABLISHED = "life_or_health_harm_established"
    HARM_SCOPE_RULES_BREACHED = "harm_scope_rules_breached"
    # Определение утраченного заработка и учёта дохода (статьи 1086 и 1087 ГК РФ).
    LOST_EARNINGS_CALCULATION_BREACHED = "lost_earnings_calculation_breached"
    MINOR_VICTIM_RULES_BREACHED = "minor_victim_rules_breached"
    # Возмещение вреда лицам, понёсшим ущерб в результате смерти кормильца
    # (статьи 1088 и 1089 ГК РФ).
    DEPENDANTS_ENTITLEMENT_BREACHED = "dependants_entitlement_breached"
    DEPENDANTS_PAYMENT_AMOUNT_BREACHED = "dependants_payment_amount_breached"
    # Изменение размера возмещения и индексация (статьи 1090 и 1091 ГК РФ).
    COMPENSATION_ADJUSTMENT_BREACHED = "compensation_adjustment_breached"
    INDEXATION_NOT_APPLIED = "indexation_not_applied"
    # Платежи по возмещению вреда и последствия прекращения юридического лица
    # (статьи 1092 и 1093 ГК РФ).
    PAYMENT_ORDER_OR_SUCCESSION_BREACHED = "payment_order_or_succession_breached"
    # Возмещение расходов на погребение (статья 1094 ГК РФ).
    FUNERAL_EXPENSES_RULES_BREACHED = "funeral_expenses_rules_breached"


REQUIRED_TORT_LIFE_HEALTH_PREDICATES = frozenset(TortLifeHealthEvidencePredicate)


class TortLifeHealthEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: TortLifeHealthEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedTortLifeHealthEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = TORT_LIFE_HEALTH_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[TortLifeHealthEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedTortLifeHealthEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Tort-life-health evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Tort-life-health evidence contains duplicate legal source refs.")
        return self


class TortLifeHealthFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    life_or_health_harm_established: bool
    harm_scope_rules_breached: bool
    lost_earnings_calculation_breached: bool
    minor_victim_rules_breached: bool
    dependants_entitlement_breached: bool
    dependants_payment_amount_breached: bool
    compensation_adjustment_breached: bool
    indexation_not_applied: bool
    payment_order_or_succession_breached: bool
    funeral_expenses_rules_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "TortLifeHealthFactSet":
        if self.indexation_not_applied and not self.compensation_adjustment_breached:
            raise ValueError(
                "Неприменение индексации размера возмещения относится только к случаю, когда "
                "нарушение правил об изменении размера возмещения установлено."
            )
        if self.harm_scope_rules_breached and not self.life_or_health_harm_established:
            raise ValueError(
                "Нарушение объёма и характера возмещения относится только к случаю, когда "
                "причинение вреда жизни или здоровью гражданина установлено."
            )
        return self


class TortLifeHealthFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class TortLifeHealthEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: TortLifeHealthFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[TortLifeHealthFactProvenance] = Field(default_factory=list)


class TortLifeHealthConstraintSet(BaseModel):
    id: str
    model_version: str = TORT_LIFE_HEALTH_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class TortLifeHealthEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    life_health_harm_qualified: bool
    harm_scope_duty_breached: bool
    lost_earnings_duty_breached: bool
    minor_victim_duty_breached: bool
    dependants_entitlement_duty_breached: bool
    dependants_payment_duty_breached: bool
    compensation_adjustment_duty_breached: bool
    indexation_duty_breached: bool
    payment_order_duty_breached: bool
    funeral_expenses_duty_breached: bool
    requires_human_life_health_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_tort_life_health_evidence(
    evidence: ReviewedTortLifeHealthEvidence,
) -> TortLifeHealthEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Tort-life-health evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Tort-life-health evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_TORT_LIFE_HEALTH_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed tort-life-health evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_TORT_LIFE_HEALTH_PREDICATES
    }
    return TortLifeHealthEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=TORT_LIFE_HEALTH_MAPPING_VERSION,
        facts=TortLifeHealthFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            TortLifeHealthFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_TORT_LIFE_HEALTH_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_tort_life_health_constraint_set(
    mapping: TortLifeHealthEvidenceMappingResult,
) -> TortLifeHealthConstraintSet:
    return TortLifeHealthConstraintSet(
        id=f"tort-life-health-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "life_health_harm_qualified == life_or_health_harm_established",
            "harm_scope_duty_breached == life_health_harm_qualified AND harm_scope_rules_breached",
            "lost_earnings_duty_breached == life_health_harm_qualified AND lost_earnings_calculation_breached",
            "minor_victim_duty_breached == life_health_harm_qualified AND minor_victim_rules_breached",
            "dependants_entitlement_duty_breached == life_health_harm_qualified AND dependants_entitlement_breached",
            "dependants_payment_duty_breached == life_health_harm_qualified AND dependants_payment_amount_breached",
            "compensation_adjustment_duty_breached == life_health_harm_qualified AND compensation_adjustment_breached",
            "indexation_duty_breached == life_health_harm_qualified AND compensation_adjustment_breached AND indexation_not_applied",
            "payment_order_duty_breached == life_health_harm_qualified AND payment_order_or_succession_breached",
            "funeral_expenses_duty_breached == life_health_harm_qualified AND funeral_expenses_rules_breached",
            "requires_human_life_health_assessment == harm_scope_duty_breached OR lost_earnings_duty_breached OR minor_victim_duty_breached OR dependants_entitlement_duty_breached OR dependants_payment_duty_breached OR compensation_adjustment_duty_breached OR payment_order_duty_breached OR funeral_expenses_duty_breached",
        ],
    )


def evaluate_tort_life_health_constraints(
    constraint_set: TortLifeHealthConstraintSet,
    facts: TortLifeHealthFactSet,
) -> TortLifeHealthEvaluation:
    variables = {field_name: Bool(field_name) for field_name in TortLifeHealthFactSet.model_fields}
    life_health_harm_qualified = Bool("life_health_harm_qualified")
    harm_scope_duty_breached = Bool("harm_scope_duty_breached")
    lost_earnings_duty_breached = Bool("lost_earnings_duty_breached")
    minor_victim_duty_breached = Bool("minor_victim_duty_breached")
    dependants_entitlement_duty_breached = Bool("dependants_entitlement_duty_breached")
    dependants_payment_duty_breached = Bool("dependants_payment_duty_breached")
    compensation_adjustment_duty_breached = Bool("compensation_adjustment_duty_breached")
    indexation_duty_breached = Bool("indexation_duty_breached")
    payment_order_duty_breached = Bool("payment_order_duty_breached")
    funeral_expenses_duty_breached = Bool("funeral_expenses_duty_breached")
    requires_human_life_health_assessment = Bool("requires_human_life_health_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(life_health_harm_qualified == variables["life_or_health_harm_established"])
    solver.add(
        harm_scope_duty_breached
        == And(life_health_harm_qualified, variables["harm_scope_rules_breached"])
    )
    solver.add(
        lost_earnings_duty_breached
        == And(life_health_harm_qualified, variables["lost_earnings_calculation_breached"])
    )
    solver.add(
        minor_victim_duty_breached
        == And(life_health_harm_qualified, variables["minor_victim_rules_breached"])
    )
    solver.add(
        dependants_entitlement_duty_breached
        == And(life_health_harm_qualified, variables["dependants_entitlement_breached"])
    )
    solver.add(
        dependants_payment_duty_breached
        == And(life_health_harm_qualified, variables["dependants_payment_amount_breached"])
    )
    solver.add(
        compensation_adjustment_duty_breached
        == And(life_health_harm_qualified, variables["compensation_adjustment_breached"])
    )
    solver.add(
        indexation_duty_breached
        == And(
            life_health_harm_qualified,
            variables["compensation_adjustment_breached"],
            variables["indexation_not_applied"],
        )
    )
    solver.add(
        payment_order_duty_breached
        == And(life_health_harm_qualified, variables["payment_order_or_succession_breached"])
    )
    solver.add(
        funeral_expenses_duty_breached
        == And(life_health_harm_qualified, variables["funeral_expenses_rules_breached"])
    )
    solver.add(
        requires_human_life_health_assessment
        == Or(
            harm_scope_duty_breached,
            lost_earnings_duty_breached,
            minor_victim_duty_breached,
            dependants_entitlement_duty_breached,
            dependants_payment_duty_breached,
            compensation_adjustment_duty_breached,
            payment_order_duty_breached,
            funeral_expenses_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return TortLifeHealthEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            life_health_harm_qualified=False,
            harm_scope_duty_breached=False,
            lost_earnings_duty_breached=False,
            minor_victim_duty_breached=False,
            dependants_entitlement_duty_breached=False,
            dependants_payment_duty_breached=False,
            compensation_adjustment_duty_breached=False,
            indexation_duty_breached=False,
            payment_order_duty_breached=False,
            funeral_expenses_duty_breached=False,
            requires_human_life_health_assessment=True,
            reasons_ru=[
                "Набор фактов о возмещении вреда, причинённого жизни или здоровью гражданина, "
                "противоречив."
            ],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Установлено причинение вреда жизни или здоровью гражданина: такой вред "
            "возмещается по правилам главы 59 ГК РФ, если законом или договором не "
            "предусмотрен более высокий размер ответственности (статья 1084 ГК РФ)."
            if truth(life_health_harm_qualified)
            else "Причинение вреда жизни или здоровью гражданина не установлено."
        ),
    ]
    if truth(harm_scope_duty_breached):
        reasons_ru.append(
            "При повреждении здоровья гражданина возмещению подлежат утраченный потерпевшим "
            "заработок (доход), который он имел либо определённо мог иметь, а также "
            "дополнительно понесённые расходы на лечение, дополнительное питание, "
            "приобретение лекарств, протезирование, посторонний уход, санаторно-курортное "
            "лечение и подготовку к другой профессии, если установлено, что потерпевший "
            "нуждается в этих видах помощи и не имеет права на их бесплатное получение "
            "(статья 1085 ГК РФ)."
        )
    if truth(lost_earnings_duty_breached):
        reasons_ru.append(
            "Размер подлежащего возмещению утраченного заработка (дохода) определяется в "
            "процентах к среднему месячному заработку до увечья или утраты трудоспособности "
            "соответственно степени утраты профессиональной трудоспособности, а при её "
            "отсутствии — общей трудоспособности (статья 1086 ГК РФ)."
        )
    if truth(minor_victim_duty_breached):
        reasons_ru.append(
            "При причинении вреда здоровью несовершеннолетнего возмещаются расходы, вызванные "
            "повреждением здоровья, а по достижении установленного возраста и при наличии "
            "заработка — вред, связанный с утратой или уменьшением трудоспособности, исходя из "
            "правил о минимальном размере оплаты труда и величине прожиточного минимума "
            "(статья 1087 ГК РФ)."
        )
    if truth(dependants_entitlement_duty_breached):
        reasons_ru.append(
            "В случае смерти потерпевшего (кормильца) право на возмещение вреда имеют "
            "нетрудоспособные лица, состоявшие на его иждивении или имевшие ко дню его смерти "
            "право на получение от него содержания, ребёнок умершего, родившийся после его "
            "смерти, а также иные лица, названные в законе, с соблюдением установленных сроков "
            "возмещения (статья 1088 ГК РФ)."
        )
    if truth(dependants_payment_duty_breached):
        reasons_ru.append(
            "Лицам, имеющим право на возмещение вреда в связи со смертью кормильца, вред "
            "возмещается в размере той доли заработка (дохода) умершего, которую они получали "
            "или имели право получать на своё содержание при его жизни; установленный каждому "
            "размер возмещения по общему правилу дальнейшему перерасчёту не подлежит "
            "(статья 1089 ГК РФ)."
        )
    if truth(compensation_adjustment_duty_breached):
        reasons_ru.append(
            "Потерпевший и причинитель вправе требовать соответствующего изменения размера "
            "возмещения вреда при изменении трудоспособности потерпевшего или имущественного "
            "положения гражданина-причинителя (статья 1090 ГК РФ)."
        )
    if truth(indexation_duty_breached):
        reasons_ru.append(
            "Суммы выплачиваемого гражданам возмещения вреда, причинённого жизни или здоровью, "
            "подлежат изменению пропорционально повышению установленной в соответствии с "
            "законом величины прожиточного минимума (статья 1091 ГК РФ)."
        )
    if truth(payment_order_duty_breached):
        reasons_ru.append(
            "Возмещение вреда, причинённого жизни или здоровью, производится ежемесячными "
            "платежами, а при наличии уважительных причин суд может присудить платежи "
            "единовременно за период не более трёх лет; при реорганизации или ликвидации "
            "юридического лица соответствующие платежи капитализируются и передаются "
            "правопреемнику либо организации, обязанной выплачивать возмещение "
            "(статьи 1092 и 1093 ГК РФ)."
        )
    if truth(funeral_expenses_duty_breached):
        reasons_ru.append(
            "Лица, ответственные за вред, вызванный смертью потерпевшего, обязаны возместить "
            "необходимые расходы на погребение лицу, понёсшему эти расходы; пособие на "
            "погребение в счёт возмещения вреда не засчитывается (статья 1094 ГК РФ)."
        )
    return TortLifeHealthEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        life_health_harm_qualified=truth(life_health_harm_qualified),
        harm_scope_duty_breached=truth(harm_scope_duty_breached),
        lost_earnings_duty_breached=truth(lost_earnings_duty_breached),
        minor_victim_duty_breached=truth(minor_victim_duty_breached),
        dependants_entitlement_duty_breached=truth(dependants_entitlement_duty_breached),
        dependants_payment_duty_breached=truth(dependants_payment_duty_breached),
        compensation_adjustment_duty_breached=truth(compensation_adjustment_duty_breached),
        indexation_duty_breached=truth(indexation_duty_breached),
        payment_order_duty_breached=truth(payment_order_duty_breached),
        funeral_expenses_duty_breached=truth(funeral_expenses_duty_breached),
        requires_human_life_health_assessment=truth(requires_human_life_health_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о возмещении вреда, причинённого жизни "
            "или здоровью гражданина, и не заменяет судебную оценку.",
            "Степень утраты трудоспособности, нуждаемость в дополнительных видах помощи, состав "
            "иждивенцев и размер заработка потерпевшего оцениваются экспертом и судом "
            "(статьи 1085, 1086 и 1088 ГК РФ).",
        ],
    )
