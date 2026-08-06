"""Формальная модель объектов гражданских прав по статьям 128–152 ГК РФ.

Модель разделяет перечень объектов гражданских прав, их оборотоспособность,
деление вещей на недвижимые и движимые, неделимые вещи и сложные вещи, главную
вещь и принадлежность, плоды, продукцию и доходы, деньги и ценные бумаги, а
также нематериальные блага и защиту чести, достоинства и деловой репутации.

Ключевой вывод для слоя общих положений — `object_excluded_from_circulation`:
объект изъят из оборота либо его отчуждение ограничено законом. По пункту 2
статьи 168 ГК РФ сделка, нарушающая требования закона и посягающая при этом на
публичные интересы, ничтожна, поэтому слой снимает действие договора.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


OBJECTS_EVIDENCE_SCHEMA_VERSION = "contracts.objects-evidence.v0"
OBJECTS_MAPPING_VERSION = "contracts-reviewed-objects-to-facts-v0"
OBJECTS_MODEL_VERSION = "contracts-objects-articles-128-152-v0"


class ObjectsEvidencePredicate(str, Enum):
    # Объекты гражданских прав и их оборотоспособность (статьи 128–130).
    OBJECT_OF_RIGHTS_ASSERTED = "object_of_rights_asserted"
    OBJECT_CLASSIFICATION_BREACHED = "object_classification_breached"
    OBJECT_NOT_IN_CIVIL_CIRCULATION = "object_not_in_civil_circulation"
    IMMOVABLE_CLASSIFICATION_BREACHED = "immovable_classification_breached"
    # Неделимые и сложные вещи, принадлежность, плоды (статьи 133–136).
    DIVISIBILITY_OR_COMPLEX_THING_BREACHED = "divisibility_or_complex_thing_breached"
    PRINCIPAL_AND_APPURTENANCE_BREACHED = "principal_and_appurtenance_breached"
    FRUITS_PRODUCTS_INCOME_BREACHED = "fruits_products_income_breached"
    # Деньги и ценные бумаги (статьи 140 и 142).
    MONEY_OR_SECURITIES_RULES_BREACHED = "money_or_securities_rules_breached"
    # Нематериальные блага и их защита (статьи 150 и 152).
    INTANGIBLE_BENEFITS_PROTECTION_BREACHED = "intangible_benefits_protection_breached"
    HONOUR_AND_REPUTATION_PROTECTION_BREACHED = "honour_and_reputation_protection_breached"


REQUIRED_OBJECTS_PREDICATES = frozenset(ObjectsEvidencePredicate)


class ObjectsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ObjectsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedObjectsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = OBJECTS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ObjectsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedObjectsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Objects evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Objects evidence contains duplicate legal source refs.")
        return self


class ObjectsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    object_of_rights_asserted: bool
    object_classification_breached: bool
    object_not_in_civil_circulation: bool
    immovable_classification_breached: bool
    divisibility_or_complex_thing_breached: bool
    principal_and_appurtenance_breached: bool
    fruits_products_income_breached: bool
    money_or_securities_rules_breached: bool
    intangible_benefits_protection_breached: bool
    honour_and_reputation_protection_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ObjectsFactSet":
        if (
            self.honour_and_reputation_protection_breached
            and not self.intangible_benefits_protection_breached
        ):
            raise ValueError(
                "Нарушение защиты чести, достоинства и деловой репутации относится только к "
                "случаю, когда затронута защита нематериальных благ."
            )
        if self.object_not_in_civil_circulation and not self.object_of_rights_asserted:
            raise ValueError(
                "Изъятие объекта из оборота относится только к заявленному объекту "
                "гражданских прав."
            )
        return self


class ObjectsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ObjectsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ObjectsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ObjectsFactProvenance] = Field(default_factory=list)


class ObjectsConstraintSet(BaseModel):
    id: str
    model_version: str = OBJECTS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ObjectsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    objects_qualified: bool
    object_classification_duty_breached: bool
    # Ключевой вывод для слоя общих положений: объект изъят из оборота либо его
    # отчуждение ограничено законом (статья 129 ГК РФ).
    object_excluded_from_circulation: bool
    immovable_classification_duty_breached: bool
    divisibility_duty_breached: bool
    principal_and_appurtenance_duty_breached: bool
    fruits_products_income_duty_breached: bool
    money_or_securities_duty_breached: bool
    intangible_benefits_duty_breached: bool
    honour_and_reputation_duty_breached: bool
    requires_human_objects_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_objects_evidence(
    evidence: ReviewedObjectsEvidence,
) -> ObjectsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Objects evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Objects evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_OBJECTS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed objects evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_OBJECTS_PREDICATES
    }
    return ObjectsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=OBJECTS_MAPPING_VERSION,
        facts=ObjectsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ObjectsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_OBJECTS_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_objects_constraint_set(mapping: ObjectsEvidenceMappingResult) -> ObjectsConstraintSet:
    return ObjectsConstraintSet(
        id=f"objects-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "objects_qualified == object_of_rights_asserted",
            "object_classification_duty_breached == objects_qualified AND object_classification_breached",
            "object_excluded_from_circulation == objects_qualified AND object_not_in_civil_circulation",
            "immovable_classification_duty_breached == objects_qualified AND immovable_classification_breached",
            "divisibility_duty_breached == objects_qualified AND divisibility_or_complex_thing_breached",
            "principal_and_appurtenance_duty_breached == objects_qualified AND principal_and_appurtenance_breached",
            "fruits_products_income_duty_breached == objects_qualified AND fruits_products_income_breached",
            "money_or_securities_duty_breached == objects_qualified AND money_or_securities_rules_breached",
            "intangible_benefits_duty_breached == objects_qualified AND intangible_benefits_protection_breached",
            "honour_and_reputation_duty_breached == objects_qualified AND intangible_benefits_protection_breached AND honour_and_reputation_protection_breached",
            "requires_human_objects_assessment == object_classification_duty_breached OR object_excluded_from_circulation OR immovable_classification_duty_breached OR divisibility_duty_breached OR principal_and_appurtenance_duty_breached OR fruits_products_income_duty_breached OR money_or_securities_duty_breached OR intangible_benefits_duty_breached",
        ],
    )


def evaluate_objects_constraints(
    constraint_set: ObjectsConstraintSet,
    facts: ObjectsFactSet,
) -> ObjectsEvaluation:
    variables = {field_name: Bool(field_name) for field_name in ObjectsFactSet.model_fields}
    objects_qualified = Bool("objects_qualified")
    object_classification_duty_breached = Bool("object_classification_duty_breached")
    object_excluded_from_circulation = Bool("object_excluded_from_circulation")
    immovable_classification_duty_breached = Bool("immovable_classification_duty_breached")
    divisibility_duty_breached = Bool("divisibility_duty_breached")
    principal_and_appurtenance_duty_breached = Bool("principal_and_appurtenance_duty_breached")
    fruits_products_income_duty_breached = Bool("fruits_products_income_duty_breached")
    money_or_securities_duty_breached = Bool("money_or_securities_duty_breached")
    intangible_benefits_duty_breached = Bool("intangible_benefits_duty_breached")
    honour_and_reputation_duty_breached = Bool("honour_and_reputation_duty_breached")
    requires_human_objects_assessment = Bool("requires_human_objects_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(objects_qualified == variables["object_of_rights_asserted"])
    solver.add(
        object_classification_duty_breached
        == And(objects_qualified, variables["object_classification_breached"])
    )
    solver.add(
        object_excluded_from_circulation
        == And(objects_qualified, variables["object_not_in_civil_circulation"])
    )
    solver.add(
        immovable_classification_duty_breached
        == And(objects_qualified, variables["immovable_classification_breached"])
    )
    solver.add(
        divisibility_duty_breached
        == And(objects_qualified, variables["divisibility_or_complex_thing_breached"])
    )
    solver.add(
        principal_and_appurtenance_duty_breached
        == And(objects_qualified, variables["principal_and_appurtenance_breached"])
    )
    solver.add(
        fruits_products_income_duty_breached
        == And(objects_qualified, variables["fruits_products_income_breached"])
    )
    solver.add(
        money_or_securities_duty_breached
        == And(objects_qualified, variables["money_or_securities_rules_breached"])
    )
    solver.add(
        intangible_benefits_duty_breached
        == And(objects_qualified, variables["intangible_benefits_protection_breached"])
    )
    solver.add(
        honour_and_reputation_duty_breached
        == And(
            objects_qualified,
            variables["intangible_benefits_protection_breached"],
            variables["honour_and_reputation_protection_breached"],
        )
    )
    solver.add(
        requires_human_objects_assessment
        == Or(
            object_classification_duty_breached,
            object_excluded_from_circulation,
            immovable_classification_duty_breached,
            divisibility_duty_breached,
            principal_and_appurtenance_duty_breached,
            fruits_products_income_duty_breached,
            money_or_securities_duty_breached,
            intangible_benefits_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ObjectsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            objects_qualified=False,
            object_classification_duty_breached=False,
            object_excluded_from_circulation=False,
            immovable_classification_duty_breached=False,
            divisibility_duty_breached=False,
            principal_and_appurtenance_duty_breached=False,
            fruits_products_income_duty_breached=False,
            money_or_securities_duty_breached=False,
            intangible_benefits_duty_breached=False,
            honour_and_reputation_duty_breached=False,
            requires_human_objects_assessment=True,
            reasons_ru=["Набор фактов об объекте гражданских прав противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Заявлен объект гражданских прав: к объектам относятся вещи, включая наличные "
            "деньги и документарные ценные бумаги, иное имущество, имущественные права, "
            "результаты работ и оказание услуг, охраняемые результаты интеллектуальной "
            "деятельности и нематериальные блага (статья 128 ГК РФ)."
            if truth(objects_qualified)
            else "Спор об объекте гражданских прав не заявлен."
        ),
    ]
    if truth(object_classification_duty_breached):
        reasons_ru.append(
            "Объект отнесён к объектам гражданских прав с нарушением их перечня: вещи, "
            "имущественные права, результаты работ и оказание услуг, охраняемые результаты "
            "интеллектуальной деятельности и нематериальные блага различаются "
            "(статья 128 ГК РФ)."
        )
    if truth(object_excluded_from_circulation):
        reasons_ru.append(
            "Объект изъят из оборота либо его отчуждение ограничено законом, тогда как "
            "объекты гражданских прав могут свободно отчуждаться или переходить от одного "
            "лица к другому, если они не ограничены в обороте (статья 129 ГК РФ)."
        )
    if truth(immovable_classification_duty_breached):
        reasons_ru.append(
            "Нарушено деление вещей на недвижимые и движимые: к недвижимым вещам относятся "
            "земельные участки, участки недр и всё, что прочно связано с землёй, а вещи, не "
            "относящиеся к недвижимости, признаются движимым имуществом "
            "(статья 130 ГК РФ)."
        )
    if truth(divisibility_duty_breached):
        reasons_ru.append(
            "Нарушены правила о неделимых и сложных вещах: вещь, раздел которой в натуре "
            "невозможен без разрушения, повреждения или изменения её назначения, признаётся "
            "неделимой, а действие сделки, совершённой по поводу сложной вещи, "
            "распространяется на все входящие в неё вещи (статьи 133 и 134 ГК РФ)."
        )
    if truth(principal_and_appurtenance_duty_breached):
        reasons_ru.append(
            "Нарушено правило о главной вещи и принадлежности: вещь, предназначенная для "
            "обслуживания другой, главной вещи и связанная с ней общим назначением, следует "
            "судьбе главной вещи, если договором не предусмотрено иное "
            "(статья 135 ГК РФ)."
        )
    if truth(fruits_products_income_duty_breached):
        reasons_ru.append(
            "Нарушено правило о плодах, продукции и доходах: полученные в результате "
            "использования вещи, они принадлежат собственнику вещи, если иное не "
            "предусмотрено законом, иными правовыми актами или договором "
            "(статья 136 ГК РФ)."
        )
    if truth(money_or_securities_duty_breached):
        reasons_ru.append(
            "Нарушены правила о деньгах и ценных бумагах: рубль является законным платёжным "
            "средством, обязательным к приёму по нарицательной стоимости на всей территории "
            "Российской Федерации, а ценные бумаги удостоверяют права по правилам, "
            "установленным законом (статьи 140 и 142 ГК РФ)."
        )
    if truth(intangible_benefits_duty_breached):
        reasons_ru.append(
            "Нарушены правила о нематериальных благах: жизнь и здоровье, достоинство "
            "личности, честь и доброе имя, деловая репутация и иные принадлежащие гражданину "
            "от рождения или в силу закона блага неотчуждаемы и непередаваемы иным способом "
            "(статья 150 ГК РФ)."
        )
    if truth(honour_and_reputation_duty_breached):
        reasons_ru.append(
            "Нарушены правила о защите чести, достоинства и деловой репутации: гражданин "
            "вправе требовать по суду опровержения порочащих его сведений, если "
            "распространивший их не докажет, что они соответствуют действительности "
            "(статья 152 ГК РФ)."
        )
    return ObjectsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        objects_qualified=truth(objects_qualified),
        object_classification_duty_breached=truth(object_classification_duty_breached),
        object_excluded_from_circulation=truth(object_excluded_from_circulation),
        immovable_classification_duty_breached=truth(immovable_classification_duty_breached),
        divisibility_duty_breached=truth(divisibility_duty_breached),
        principal_and_appurtenance_duty_breached=truth(principal_and_appurtenance_duty_breached),
        fruits_products_income_duty_breached=truth(fruits_products_income_duty_breached),
        money_or_securities_duty_breached=truth(money_or_securities_duty_breached),
        intangible_benefits_duty_breached=truth(intangible_benefits_duty_breached),
        honour_and_reputation_duty_breached=truth(honour_and_reputation_duty_breached),
        requires_human_objects_assessment=truth(requires_human_objects_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила об объектах гражданских прав и не "
            "заменяет судебную оценку.",
            "Отнесение объекта к изъятым из оборота или ограниченным в обороте, прочность "
            "связи вещи с землёй и порочащий характер распространённых сведений оцениваются "
            "экспертом и судом (статьи 129, 130 и 152 ГК РФ).",
        ],
    )
