from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


WAREHOUSE_STORAGE_EVIDENCE_SCHEMA_VERSION = "contracts.warehouse-storage-evidence.v0"
WAREHOUSE_STORAGE_MAPPING_VERSION = "contracts-reviewed-warehouse-storage-to-facts-v0"
WAREHOUSE_STORAGE_MODEL_VERSION = "contracts-warehouse-storage-articles-907-918-v0"


class WarehouseStorageEvidencePredicate(str, Enum):
    # Договор складского хранения и склад общего пользования (статьи 907 и 908 ГК РФ).
    GOODS_ACCEPTED_BY_WAREHOUSE_FOR_STORAGE = "goods_accepted_by_warehouse_for_storage"
    GENERAL_WAREHOUSE_PUBLIC_DUTY_BREACHED = "general_warehouse_public_duty_breached"
    # Проверка товаров при приёме на склад (статья 909 ГК РФ).
    GOODS_INSPECTION_ON_ACCEPTANCE_BREACHED = "goods_inspection_on_acceptance_breached"
    ACCEPTANCE_DISCREPANCY_NOT_RECORDED = "acceptance_discrepancy_not_recorded"
    # Осмотр товаров товаровладельцем и изменение условий хранения (статьи 909 и 910 ГК РФ).
    OWNER_INSPECTION_RIGHTS_BREACHED = "owner_inspection_rights_breached"
    STORAGE_CONDITIONS_CHANGE_NOT_NOTIFIED = "storage_conditions_change_not_notified"
    # Проверка товаров при возвращении товаровладельцу (статья 911 ГК РФ).
    RETURN_INSPECTION_AND_REPORT_BREACHED = "return_inspection_and_report_breached"
    # Складские документы и распоряжение товаром (статьи 912–918 ГК РФ).
    WAREHOUSE_DOCUMENT_NOT_ISSUED = "warehouse_document_not_issued"
    DOUBLE_CERTIFICATE_RULES_BREACHED = "double_certificate_rules_breached"
    GOODS_RELEASE_AND_COMMINGLING_RULES_BREACHED = "goods_release_and_commingling_rules_breached"


REQUIRED_WAREHOUSE_STORAGE_PREDICATES = frozenset(WarehouseStorageEvidencePredicate)


class WarehouseStorageEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: WarehouseStorageEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedWarehouseStorageEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = WAREHOUSE_STORAGE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[WarehouseStorageEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedWarehouseStorageEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Warehouse-storage evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Warehouse-storage evidence contains duplicate legal source refs.")
        return self


class WarehouseStorageFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    goods_accepted_by_warehouse_for_storage: bool
    general_warehouse_public_duty_breached: bool
    goods_inspection_on_acceptance_breached: bool
    acceptance_discrepancy_not_recorded: bool
    owner_inspection_rights_breached: bool
    storage_conditions_change_not_notified: bool
    return_inspection_and_report_breached: bool
    warehouse_document_not_issued: bool
    double_certificate_rules_breached: bool
    goods_release_and_commingling_rules_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "WarehouseStorageFactSet":
        if (
            self.acceptance_discrepancy_not_recorded
            and not self.goods_inspection_on_acceptance_breached
        ):
            raise ValueError(
                "Незафиксированные расхождения при приёме товара относятся только к случаю, когда "
                "нарушение проверки товаров при их приёме на склад установлено."
            )
        if self.warehouse_document_not_issued and not self.goods_accepted_by_warehouse_for_storage:
            raise ValueError(
                "Невыдача складского документа относится только к договору складского хранения."
            )
        return self


class WarehouseStorageFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class WarehouseStorageEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: WarehouseStorageFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[WarehouseStorageFactProvenance] = Field(default_factory=list)


class WarehouseStorageConstraintSet(BaseModel):
    id: str
    model_version: str = WAREHOUSE_STORAGE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class WarehouseStorageEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    warehouse_storage_qualified: bool
    general_warehouse_duty_breached: bool
    acceptance_inspection_duty_breached: bool
    acceptance_record_duty_breached: bool
    owner_inspection_duty_breached: bool
    conditions_change_notice_duty_breached: bool
    return_inspection_duty_breached: bool
    warehouse_document_duty_breached: bool
    double_certificate_duty_breached: bool
    goods_release_duty_breached: bool
    requires_human_warehouse_storage_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_warehouse_storage_evidence(
    evidence: ReviewedWarehouseStorageEvidence,
) -> WarehouseStorageEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Warehouse-storage evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Warehouse-storage evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_WAREHOUSE_STORAGE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed warehouse-storage evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_WAREHOUSE_STORAGE_PREDICATES
    }
    return WarehouseStorageEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=WAREHOUSE_STORAGE_MAPPING_VERSION,
        facts=WarehouseStorageFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            WarehouseStorageFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_WAREHOUSE_STORAGE_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_warehouse_storage_constraint_set(
    mapping: WarehouseStorageEvidenceMappingResult,
) -> WarehouseStorageConstraintSet:
    return WarehouseStorageConstraintSet(
        id=f"warehouse-storage-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "warehouse_storage_qualified == goods_accepted_by_warehouse_for_storage",
            "general_warehouse_duty_breached == warehouse_storage_qualified AND general_warehouse_public_duty_breached",
            "acceptance_inspection_duty_breached == warehouse_storage_qualified AND goods_inspection_on_acceptance_breached",
            "acceptance_record_duty_breached == warehouse_storage_qualified AND goods_inspection_on_acceptance_breached AND acceptance_discrepancy_not_recorded",
            "owner_inspection_duty_breached == warehouse_storage_qualified AND owner_inspection_rights_breached",
            "conditions_change_notice_duty_breached == warehouse_storage_qualified AND storage_conditions_change_not_notified",
            "return_inspection_duty_breached == warehouse_storage_qualified AND return_inspection_and_report_breached",
            "warehouse_document_duty_breached == warehouse_storage_qualified AND warehouse_document_not_issued",
            "double_certificate_duty_breached == warehouse_storage_qualified AND double_certificate_rules_breached",
            "goods_release_duty_breached == warehouse_storage_qualified AND goods_release_and_commingling_rules_breached",
            "requires_human_warehouse_storage_assessment == general_warehouse_duty_breached OR acceptance_inspection_duty_breached OR owner_inspection_duty_breached OR conditions_change_notice_duty_breached OR return_inspection_duty_breached OR warehouse_document_duty_breached OR double_certificate_duty_breached OR goods_release_duty_breached",
        ],
    )


def evaluate_warehouse_storage_constraints(
    constraint_set: WarehouseStorageConstraintSet,
    facts: WarehouseStorageFactSet,
) -> WarehouseStorageEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in WarehouseStorageFactSet.model_fields
    }
    warehouse_storage_qualified = Bool("warehouse_storage_qualified")
    general_warehouse_duty_breached = Bool("general_warehouse_duty_breached")
    acceptance_inspection_duty_breached = Bool("acceptance_inspection_duty_breached")
    acceptance_record_duty_breached = Bool("acceptance_record_duty_breached")
    owner_inspection_duty_breached = Bool("owner_inspection_duty_breached")
    conditions_change_notice_duty_breached = Bool("conditions_change_notice_duty_breached")
    return_inspection_duty_breached = Bool("return_inspection_duty_breached")
    warehouse_document_duty_breached = Bool("warehouse_document_duty_breached")
    double_certificate_duty_breached = Bool("double_certificate_duty_breached")
    goods_release_duty_breached = Bool("goods_release_duty_breached")
    requires_human_warehouse_storage_assessment = Bool(
        "requires_human_warehouse_storage_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(warehouse_storage_qualified == variables["goods_accepted_by_warehouse_for_storage"])
    solver.add(
        general_warehouse_duty_breached
        == And(warehouse_storage_qualified, variables["general_warehouse_public_duty_breached"])
    )
    solver.add(
        acceptance_inspection_duty_breached
        == And(warehouse_storage_qualified, variables["goods_inspection_on_acceptance_breached"])
    )
    solver.add(
        acceptance_record_duty_breached
        == And(
            warehouse_storage_qualified,
            variables["goods_inspection_on_acceptance_breached"],
            variables["acceptance_discrepancy_not_recorded"],
        )
    )
    solver.add(
        owner_inspection_duty_breached
        == And(warehouse_storage_qualified, variables["owner_inspection_rights_breached"])
    )
    solver.add(
        conditions_change_notice_duty_breached
        == And(warehouse_storage_qualified, variables["storage_conditions_change_not_notified"])
    )
    solver.add(
        return_inspection_duty_breached
        == And(warehouse_storage_qualified, variables["return_inspection_and_report_breached"])
    )
    solver.add(
        warehouse_document_duty_breached
        == And(warehouse_storage_qualified, variables["warehouse_document_not_issued"])
    )
    solver.add(
        double_certificate_duty_breached
        == And(warehouse_storage_qualified, variables["double_certificate_rules_breached"])
    )
    solver.add(
        goods_release_duty_breached
        == And(
            warehouse_storage_qualified,
            variables["goods_release_and_commingling_rules_breached"],
        )
    )
    solver.add(
        requires_human_warehouse_storage_assessment
        == Or(
            general_warehouse_duty_breached,
            acceptance_inspection_duty_breached,
            owner_inspection_duty_breached,
            conditions_change_notice_duty_breached,
            return_inspection_duty_breached,
            warehouse_document_duty_breached,
            double_certificate_duty_breached,
            goods_release_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return WarehouseStorageEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            warehouse_storage_qualified=False,
            general_warehouse_duty_breached=False,
            acceptance_inspection_duty_breached=False,
            acceptance_record_duty_breached=False,
            owner_inspection_duty_breached=False,
            conditions_change_notice_duty_breached=False,
            return_inspection_duty_breached=False,
            warehouse_document_duty_breached=False,
            double_certificate_duty_breached=False,
            goods_release_duty_breached=False,
            requires_human_warehouse_storage_assessment=True,
            reasons_ru=["Набор фактов о хранении на товарном складе противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор складского хранения: товарный склад обязуется за "
            "вознаграждение хранить товары, переданные ему товаровладельцем, и возвратить эти "
            "товары в сохранности (статья 907 ГК РФ)."
            if truth(warehouse_storage_qualified)
            else "Отношения не квалифицированы как договор складского хранения."
        ),
    ]
    if truth(general_warehouse_duty_breached):
        reasons_ru.append(
            "Договор складского хранения, заключаемый складом общего пользования, признаётся "
            "публичным договором (статья 908 ГК РФ)."
        )
    if truth(acceptance_inspection_duty_breached):
        reasons_ru.append(
            "Товарный склад обязан при приёме товаров на хранение произвести за свой счёт осмотр "
            "товаров и определить их количество и внешнее состояние, если иное не предусмотрено "
            "договором (статья 909 ГК РФ)."
        )
    if truth(acceptance_record_duty_breached):
        reasons_ru.append(
            "Выявленные при приёме товаров расхождения в количестве и внешнем состоянии подлежат "
            "фиксации, а сведения о товарах предоставляются товаровладельцу в предусмотренном "
            "порядке (статья 909 ГК РФ)."
        )
    if truth(owner_inspection_duty_breached):
        reasons_ru.append(
            "Товаровладелец вправе во время хранения осматривать товары или их образцы, если "
            "товары хранятся с обезличением, брать пробы и принимать меры, необходимые для "
            "обеспечения сохранности товаров (статья 909 ГК РФ)."
        )
    if truth(conditions_change_notice_duty_breached):
        reasons_ru.append(
            "При необходимости изменить условия хранения товаров склад вправе принять требуемые "
            "меры самостоятельно, уведомив товаровладельца о существенном изменении условий, а "
            "об обнаруженных повреждениях товара — незамедлительно составить акт и известить "
            "товаровладельца (статья 910 ГК РФ)."
        )
    if truth(return_inspection_duty_breached):
        reasons_ru.append(
            "Товаровладелец и склад имеют право требовать осмотра товаров и проверки их "
            "количества при возвращении товара; при отсутствии совместного осмотра заявление о "
            "недостаче или повреждении подаётся в установленный срок (статья 911 ГК РФ)."
        )
    if truth(warehouse_document_duty_breached):
        reasons_ru.append(
            "Товарный склад выдаёт в подтверждение принятия товара на хранение двойное складское "
            "свидетельство, простое складское свидетельство либо складскую квитанцию "
            "(статьи 912 и 917 ГК РФ)."
        )
    if truth(double_certificate_duty_breached):
        reasons_ru.append(
            "Двойное складское свидетельство состоит из складского и залогового свидетельств, "
            "содержит обязательные реквизиты, а права его держателей и передача этих свидетельств "
            "подчиняются правилам статей 913–915 ГК РФ."
        )
    if truth(goods_release_duty_breached):
        reasons_ru.append(
            "Товар выдаётся держателю складского и залогового свидетельств в предусмотренном "
            "порядке, а при хранении вещей с обезличением склад возвращает равное или "
            "обусловленное сторонами количество вещей того же рода и качества "
            "(статьи 916 и 918 ГК РФ)."
        )
    return WarehouseStorageEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        warehouse_storage_qualified=truth(warehouse_storage_qualified),
        general_warehouse_duty_breached=truth(general_warehouse_duty_breached),
        acceptance_inspection_duty_breached=truth(acceptance_inspection_duty_breached),
        acceptance_record_duty_breached=truth(acceptance_record_duty_breached),
        owner_inspection_duty_breached=truth(owner_inspection_duty_breached),
        conditions_change_notice_duty_breached=truth(conditions_change_notice_duty_breached),
        return_inspection_duty_breached=truth(return_inspection_duty_breached),
        warehouse_document_duty_breached=truth(warehouse_document_duty_breached),
        double_certificate_duty_breached=truth(double_certificate_duty_breached),
        goods_release_duty_breached=truth(goods_release_duty_breached),
        requires_human_warehouse_storage_assessment=truth(
            requires_human_warehouse_storage_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только правила о хранении на товарном складе и не заменяет судебную "
            "оценку.",
            "Существенность изменения условий хранения, достаточность осмотра товаров и "
            "правомерность выдачи товара по складским документам оцениваются экспертом и судом "
            "(статьи 909, 910 и 916 ГК РФ).",
        ],
    )
