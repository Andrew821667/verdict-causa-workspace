from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


SPECIAL_STORAGE_EVIDENCE_SCHEMA_VERSION = "contracts.special-storage-evidence.v0"
SPECIAL_STORAGE_MAPPING_VERSION = "contracts-reviewed-special-storage-to-facts-v0"
SPECIAL_STORAGE_MODEL_VERSION = "contracts-special-storage-articles-919-926-v0"


class SpecialStorageEvidencePredicate(str, Enum):
    # Специальный вид хранения и хранение в ломбарде (статьи 919 и 920 ГК РФ).
    SPECIAL_STORAGE_SERVICE_PROVIDED = "special_storage_service_provided"
    PAWNSHOP_STORAGE_RULES_BREACHED = "pawnshop_storage_rules_breached"
    # Хранение ценностей в банке и в индивидуальном сейфе (статьи 921 и 922 ГК РФ).
    BANK_VALUABLES_STORAGE_RULES_BREACHED = "bank_valuables_storage_rules_breached"
    SAFE_DEPOSIT_BOX_RULES_BREACHED = "safe_deposit_box_rules_breached"
    # Хранение в камерах хранения транспортных организаций (статья 923 ГК РФ).
    TRANSPORT_LOCKER_STORAGE_RULES_BREACHED = "transport_locker_storage_rules_breached"
    LOCKER_OVERDUE_GOODS_RULES_BREACHED = "locker_overdue_goods_rules_breached"
    # Хранение в гардеробах организаций и в гостинице (статьи 924 и 925 ГК РФ).
    CLOAKROOM_STORAGE_RULES_BREACHED = "cloakroom_storage_rules_breached"
    HOTEL_GUEST_PROPERTY_RULES_BREACHED = "hotel_guest_property_rules_breached"
    # Секвестр и пределы ответственности (статья 926 ГК РФ).
    SEQUESTRATION_RULES_BREACHED = "sequestration_rules_breached"
    SPECIAL_STORAGE_LIABILITY_LIMITS_BREACHED = "special_storage_liability_limits_breached"


REQUIRED_SPECIAL_STORAGE_PREDICATES = frozenset(SpecialStorageEvidencePredicate)


class SpecialStorageEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: SpecialStorageEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedSpecialStorageEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = SPECIAL_STORAGE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[SpecialStorageEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedSpecialStorageEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Special-storage evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Special-storage evidence contains duplicate legal source refs.")
        return self


class SpecialStorageFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    special_storage_service_provided: bool
    pawnshop_storage_rules_breached: bool
    bank_valuables_storage_rules_breached: bool
    safe_deposit_box_rules_breached: bool
    transport_locker_storage_rules_breached: bool
    locker_overdue_goods_rules_breached: bool
    cloakroom_storage_rules_breached: bool
    hotel_guest_property_rules_breached: bool
    sequestration_rules_breached: bool
    special_storage_liability_limits_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "SpecialStorageFactSet":
        if (
            self.locker_overdue_goods_rules_breached
            and not self.transport_locker_storage_rules_breached
        ):
            raise ValueError(
                "Нарушение правил о невостребованных вещах относится только к случаю, когда "
                "нарушение хранения в камере хранения транспортной организации установлено."
            )
        if self.pawnshop_storage_rules_breached and not self.special_storage_service_provided:
            raise ValueError(
                "Нарушение правил хранения в ломбарде относится только к специальным видам "
                "хранения."
            )
        return self


class SpecialStorageFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class SpecialStorageEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: SpecialStorageFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[SpecialStorageFactProvenance] = Field(default_factory=list)


class SpecialStorageConstraintSet(BaseModel):
    id: str
    model_version: str = SPECIAL_STORAGE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class SpecialStorageEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    special_storage_qualified: bool
    pawnshop_duty_breached: bool
    bank_valuables_duty_breached: bool
    safe_deposit_box_duty_breached: bool
    transport_locker_duty_breached: bool
    locker_overdue_goods_duty_breached: bool
    cloakroom_duty_breached: bool
    hotel_guest_property_duty_breached: bool
    sequestration_duty_breached: bool
    liability_limits_duty_breached: bool
    requires_human_special_storage_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_special_storage_evidence(
    evidence: ReviewedSpecialStorageEvidence,
) -> SpecialStorageEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Special-storage evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Special-storage evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_SPECIAL_STORAGE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed special-storage evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_SPECIAL_STORAGE_PREDICATES
    }
    return SpecialStorageEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=SPECIAL_STORAGE_MAPPING_VERSION,
        facts=SpecialStorageFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            SpecialStorageFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_SPECIAL_STORAGE_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_special_storage_constraint_set(
    mapping: SpecialStorageEvidenceMappingResult,
) -> SpecialStorageConstraintSet:
    return SpecialStorageConstraintSet(
        id=f"special-storage-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "special_storage_qualified == special_storage_service_provided",
            "pawnshop_duty_breached == special_storage_qualified AND pawnshop_storage_rules_breached",
            "bank_valuables_duty_breached == special_storage_qualified AND bank_valuables_storage_rules_breached",
            "safe_deposit_box_duty_breached == special_storage_qualified AND safe_deposit_box_rules_breached",
            "transport_locker_duty_breached == special_storage_qualified AND transport_locker_storage_rules_breached",
            "locker_overdue_goods_duty_breached == special_storage_qualified AND transport_locker_storage_rules_breached AND locker_overdue_goods_rules_breached",
            "cloakroom_duty_breached == special_storage_qualified AND cloakroom_storage_rules_breached",
            "hotel_guest_property_duty_breached == special_storage_qualified AND hotel_guest_property_rules_breached",
            "sequestration_duty_breached == special_storage_qualified AND sequestration_rules_breached",
            "liability_limits_duty_breached == special_storage_qualified AND special_storage_liability_limits_breached",
            "requires_human_special_storage_assessment == pawnshop_duty_breached OR bank_valuables_duty_breached OR safe_deposit_box_duty_breached OR transport_locker_duty_breached OR cloakroom_duty_breached OR hotel_guest_property_duty_breached OR sequestration_duty_breached OR liability_limits_duty_breached",
        ],
    )


def evaluate_special_storage_constraints(
    constraint_set: SpecialStorageConstraintSet,
    facts: SpecialStorageFactSet,
) -> SpecialStorageEvaluation:
    variables = {field_name: Bool(field_name) for field_name in SpecialStorageFactSet.model_fields}
    special_storage_qualified = Bool("special_storage_qualified")
    pawnshop_duty_breached = Bool("pawnshop_duty_breached")
    bank_valuables_duty_breached = Bool("bank_valuables_duty_breached")
    safe_deposit_box_duty_breached = Bool("safe_deposit_box_duty_breached")
    transport_locker_duty_breached = Bool("transport_locker_duty_breached")
    locker_overdue_goods_duty_breached = Bool("locker_overdue_goods_duty_breached")
    cloakroom_duty_breached = Bool("cloakroom_duty_breached")
    hotel_guest_property_duty_breached = Bool("hotel_guest_property_duty_breached")
    sequestration_duty_breached = Bool("sequestration_duty_breached")
    liability_limits_duty_breached = Bool("liability_limits_duty_breached")
    requires_human_special_storage_assessment = Bool("requires_human_special_storage_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(special_storage_qualified == variables["special_storage_service_provided"])
    solver.add(
        pawnshop_duty_breached
        == And(special_storage_qualified, variables["pawnshop_storage_rules_breached"])
    )
    solver.add(
        bank_valuables_duty_breached
        == And(special_storage_qualified, variables["bank_valuables_storage_rules_breached"])
    )
    solver.add(
        safe_deposit_box_duty_breached
        == And(special_storage_qualified, variables["safe_deposit_box_rules_breached"])
    )
    solver.add(
        transport_locker_duty_breached
        == And(special_storage_qualified, variables["transport_locker_storage_rules_breached"])
    )
    solver.add(
        locker_overdue_goods_duty_breached
        == And(
            special_storage_qualified,
            variables["transport_locker_storage_rules_breached"],
            variables["locker_overdue_goods_rules_breached"],
        )
    )
    solver.add(
        cloakroom_duty_breached
        == And(special_storage_qualified, variables["cloakroom_storage_rules_breached"])
    )
    solver.add(
        hotel_guest_property_duty_breached
        == And(special_storage_qualified, variables["hotel_guest_property_rules_breached"])
    )
    solver.add(
        sequestration_duty_breached
        == And(special_storage_qualified, variables["sequestration_rules_breached"])
    )
    solver.add(
        liability_limits_duty_breached
        == And(special_storage_qualified, variables["special_storage_liability_limits_breached"])
    )
    solver.add(
        requires_human_special_storage_assessment
        == Or(
            pawnshop_duty_breached,
            bank_valuables_duty_breached,
            safe_deposit_box_duty_breached,
            transport_locker_duty_breached,
            cloakroom_duty_breached,
            hotel_guest_property_duty_breached,
            sequestration_duty_breached,
            liability_limits_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return SpecialStorageEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            special_storage_qualified=False,
            pawnshop_duty_breached=False,
            bank_valuables_duty_breached=False,
            safe_deposit_box_duty_breached=False,
            transport_locker_duty_breached=False,
            locker_overdue_goods_duty_breached=False,
            cloakroom_duty_breached=False,
            hotel_guest_property_duty_breached=False,
            sequestration_duty_breached=False,
            liability_limits_duty_breached=False,
            requires_human_special_storage_assessment=True,
            reasons_ru=["Набор фактов о специальных видах хранения противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Отношения квалифицированы как специальный вид хранения: вещь принята на хранение "
            "ломбардом, банком, камерой хранения транспортной организации, гардеробом "
            "организации, гостиницей либо в порядке секвестра (статьи 919–926 ГК РФ)."
            if truth(special_storage_qualified)
            else "Специальный вид хранения не установлен."
        ),
    ]
    if truth(pawnshop_duty_breached):
        reasons_ru.append(
            "Договор хранения вещи в ломбарде удостоверяется именной сохранной квитанцией, вещь "
            "оценивается по соглашению сторон, ломбард обязан страховать её в пользу "
            "поклажедателя за свой счёт, а невостребованная вещь хранится и реализуется в "
            "установленном порядке (статьи 919 и 920 ГК РФ)."
        )
    if truth(bank_valuables_duty_breached):
        reasons_ru.append(
            "Банк может принимать на хранение ценные бумаги, драгоценные металлы и камни, иные "
            "драгоценные вещи и ценности; заключение договора удостоверяется выдачей именного "
            "сохранного документа (статья 921 ГК РФ)."
        )
    if truth(safe_deposit_box_duty_breached):
        reasons_ru.append(
            "Хранение ценностей в индивидуальном банковском сейфе осуществляется с "
            "предоставлением клиенту права самому помещать и изымать ценности либо с их приёмом "
            "банком; ответственность банка за содержимое сейфа определяется правилами статьи 922 "
            "ГК РФ."
        )
    if truth(transport_locker_duty_breached):
        reasons_ru.append(
            "Камеры хранения транспортных организаций общего пользования обязаны принимать на "
            "хранение вещи пассажиров и других граждан независимо от наличия у них проездных "
            "документов; договор признаётся публичным (статья 923 ГК РФ)."
        )
    if truth(locker_overdue_goods_duty_breached):
        reasons_ru.append(
            "Вещи, не востребованные в установленный срок, хранятся камерой хранения в течение "
            "предусмотренного законом дополнительного срока, по истечении которого могут быть "
            "проданы в установленном порядке (статья 923 ГК РФ)."
        )
    if truth(cloakroom_duty_breached):
        reasons_ru.append(
            "Хранение в гардеробах организаций предполагается безвозмездным, а хранитель обязан "
            "принять все необходимые меры для обеспечения сохранности вещи независимо от того, "
            "осуществляется хранение за плату или безвозмездно (статья 924 ГК РФ)."
        )
    if truth(hotel_guest_property_duty_breached):
        reasons_ru.append(
            "Гостиница отвечает как хранитель и без особого о том соглашения за утрату, недостачу "
            "или повреждение вещей постояльца, внесённых в гостиницу, за исключением денег и "
            "драгоценностей, принятых на хранение отдельно (статья 925 ГК РФ)."
        )
    if truth(sequestration_duty_breached):
        reasons_ru.append(
            "По договору о секвестре вещь, являющаяся предметом спора, передаётся на хранение "
            "третьему лицу, которое обязано возвратить её лицу, признанному по решению суда или "
            "по соглашению сторон управомоченным (статья 926 ГК РФ)."
        )
    if truth(liability_limits_duty_breached):
        reasons_ru.append(
            "Пределы ответственности хранителя по специальным видам хранения определяются "
            "правилами о соответствующем виде хранения и общими положениями о хранении "
            "(статьи 919–926 ГК РФ)."
        )
    return SpecialStorageEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        special_storage_qualified=truth(special_storage_qualified),
        pawnshop_duty_breached=truth(pawnshop_duty_breached),
        bank_valuables_duty_breached=truth(bank_valuables_duty_breached),
        safe_deposit_box_duty_breached=truth(safe_deposit_box_duty_breached),
        transport_locker_duty_breached=truth(transport_locker_duty_breached),
        locker_overdue_goods_duty_breached=truth(locker_overdue_goods_duty_breached),
        cloakroom_duty_breached=truth(cloakroom_duty_breached),
        hotel_guest_property_duty_breached=truth(hotel_guest_property_duty_breached),
        sequestration_duty_breached=truth(sequestration_duty_breached),
        liability_limits_duty_breached=truth(liability_limits_duty_breached),
        requires_human_special_storage_assessment=truth(requires_human_special_storage_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только правила о специальных видах хранения и не заменяет судебную "
            "оценку.",
            "Оценка вещи, состав внесённых в гостиницу вещей и управомоченность получателя при "
            "секвестре оцениваются экспертом и судом (статьи 919, 925 и 926 ГК РФ).",
        ],
    )
