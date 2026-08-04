from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


FACTORING_EVIDENCE_SCHEMA_VERSION = "contracts.factoring-evidence.v0"
FACTORING_MAPPING_VERSION = "contracts-reviewed-factoring-to-facts-v0"
FACTORING_MODEL_VERSION = "contracts-factoring-articles-824-833-v0"


class FactoringEvidencePredicate(str, Enum):
    # Понятие факторинга и предмет уступки (статьи 824 и 826 ГК РФ).
    MONETARY_CLAIM_ASSIGNED_FOR_FINANCING = "monetary_claim_assigned_for_financing"
    ASSIGNED_CLAIM_NOT_IDENTIFIED = "assigned_claim_not_identified"
    # Стороны и действительность уступки (статьи 825 и 828 ГК РФ).
    FACTOR_NOT_ENTITLED_TO_ACT = "factor_not_entitled_to_act"
    CONTRACTUAL_ASSIGNMENT_BAN_INVOKED_AGAINST_FACTOR = (
        "contractual_assignment_ban_invoked_against_factor"
    )
    # Ответственность клиента и последующая уступка (статьи 827 и 829 ГК РФ).
    CLIENT_CLAIM_VALIDITY_WARRANTY_BREACHED = "client_claim_validity_warranty_breached"
    SUBSEQUENT_ASSIGNMENT_MADE_WITHOUT_PERMISSION = "subsequent_assignment_made_without_permission"
    # Исполнение должником и зачёт (статьи 830 и 832 ГК РФ).
    DEBTOR_NOT_NOTIFIED_OF_ASSIGNMENT = "debtor_not_notified_of_assignment"
    DEBTOR_SET_OFF_CLAIMS_DISREGARDED = "debtor_set_off_claims_disregarded"
    # Расчёты сторон и возврат полученного (статьи 831 и 833 ГК РФ).
    FACTOR_SETTLEMENT_WITH_CLIENT_BREACHED = "factor_settlement_with_client_breached"
    DEBTOR_REFUND_CLAIM_MISDIRECTED = "debtor_refund_claim_misdirected"


REQUIRED_FACTORING_PREDICATES = frozenset(FactoringEvidencePredicate)


class FactoringEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: FactoringEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedFactoringEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = FACTORING_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[FactoringEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedFactoringEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Factoring evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Factoring evidence contains duplicate legal source refs.")
        return self


class FactoringFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    monetary_claim_assigned_for_financing: bool
    assigned_claim_not_identified: bool
    factor_not_entitled_to_act: bool
    contractual_assignment_ban_invoked_against_factor: bool
    client_claim_validity_warranty_breached: bool
    subsequent_assignment_made_without_permission: bool
    debtor_not_notified_of_assignment: bool
    debtor_set_off_claims_disregarded: bool
    factor_settlement_with_client_breached: bool
    debtor_refund_claim_misdirected: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "FactoringFactSet":
        if self.debtor_set_off_claims_disregarded and not self.debtor_not_notified_of_assignment:
            raise ValueError(
                "Игнорирование зачётных требований должника относится только к случаю, когда "
                "ненадлежащее уведомление должника об уступке установлено."
            )
        if self.assigned_claim_not_identified and not self.monetary_claim_assigned_for_financing:
            raise ValueError(
                "Неопределённость уступаемого требования относится только к договору "
                "финансирования под уступку денежного требования."
            )
        return self


class FactoringFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class FactoringEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: FactoringFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[FactoringFactProvenance] = Field(default_factory=list)


class FactoringConstraintSet(BaseModel):
    id: str
    model_version: str = FACTORING_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class FactoringEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    factoring_qualified: bool
    claim_identification_breached: bool
    factor_status_invalid: bool
    assignment_ban_ineffective_against_factor: bool
    client_warranty_breached: bool
    subsequent_assignment_unauthorized: bool
    debtor_notice_duty_breached: bool
    debtor_set_off_right_available: bool
    settlement_duty_breached: bool
    refund_claim_direction_breached: bool
    requires_human_factoring_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_factoring_evidence(
    evidence: ReviewedFactoringEvidence,
) -> FactoringEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Factoring evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Factoring evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_FACTORING_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed factoring evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_FACTORING_PREDICATES
    }
    return FactoringEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=FACTORING_MAPPING_VERSION,
        facts=FactoringFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            FactoringFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_FACTORING_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_factoring_constraint_set(
    mapping: FactoringEvidenceMappingResult,
) -> FactoringConstraintSet:
    return FactoringConstraintSet(
        id=f"factoring-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "factoring_qualified == monetary_claim_assigned_for_financing",
            "claim_identification_breached == factoring_qualified AND assigned_claim_not_identified",
            "factor_status_invalid == factoring_qualified AND factor_not_entitled_to_act",
            "assignment_ban_ineffective_against_factor == factoring_qualified AND contractual_assignment_ban_invoked_against_factor",
            "client_warranty_breached == factoring_qualified AND client_claim_validity_warranty_breached",
            "subsequent_assignment_unauthorized == factoring_qualified AND subsequent_assignment_made_without_permission",
            "debtor_notice_duty_breached == factoring_qualified AND debtor_not_notified_of_assignment",
            "debtor_set_off_right_available == factoring_qualified AND debtor_not_notified_of_assignment AND debtor_set_off_claims_disregarded",
            "settlement_duty_breached == factoring_qualified AND factor_settlement_with_client_breached",
            "refund_claim_direction_breached == factoring_qualified AND debtor_refund_claim_misdirected",
            "requires_human_factoring_assessment == claim_identification_breached OR factor_status_invalid OR assignment_ban_ineffective_against_factor OR client_warranty_breached OR subsequent_assignment_unauthorized OR debtor_notice_duty_breached OR settlement_duty_breached OR refund_claim_direction_breached",
        ],
    )


def evaluate_factoring_constraints(
    constraint_set: FactoringConstraintSet,
    facts: FactoringFactSet,
) -> FactoringEvaluation:
    variables = {field_name: Bool(field_name) for field_name in FactoringFactSet.model_fields}
    factoring_qualified = Bool("factoring_qualified")
    claim_identification_breached = Bool("claim_identification_breached")
    factor_status_invalid = Bool("factor_status_invalid")
    assignment_ban_ineffective_against_factor = Bool("assignment_ban_ineffective_against_factor")
    client_warranty_breached = Bool("client_warranty_breached")
    subsequent_assignment_unauthorized = Bool("subsequent_assignment_unauthorized")
    debtor_notice_duty_breached = Bool("debtor_notice_duty_breached")
    debtor_set_off_right_available = Bool("debtor_set_off_right_available")
    settlement_duty_breached = Bool("settlement_duty_breached")
    refund_claim_direction_breached = Bool("refund_claim_direction_breached")
    requires_human_factoring_assessment = Bool("requires_human_factoring_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(factoring_qualified == variables["monetary_claim_assigned_for_financing"])
    solver.add(
        claim_identification_breached
        == And(factoring_qualified, variables["assigned_claim_not_identified"])
    )
    solver.add(
        factor_status_invalid == And(factoring_qualified, variables["factor_not_entitled_to_act"])
    )
    solver.add(
        assignment_ban_ineffective_against_factor
        == And(
            factoring_qualified,
            variables["contractual_assignment_ban_invoked_against_factor"],
        )
    )
    solver.add(
        client_warranty_breached
        == And(factoring_qualified, variables["client_claim_validity_warranty_breached"])
    )
    solver.add(
        subsequent_assignment_unauthorized
        == And(factoring_qualified, variables["subsequent_assignment_made_without_permission"])
    )
    solver.add(
        debtor_notice_duty_breached
        == And(factoring_qualified, variables["debtor_not_notified_of_assignment"])
    )
    solver.add(
        debtor_set_off_right_available
        == And(
            factoring_qualified,
            variables["debtor_not_notified_of_assignment"],
            variables["debtor_set_off_claims_disregarded"],
        )
    )
    solver.add(
        settlement_duty_breached
        == And(factoring_qualified, variables["factor_settlement_with_client_breached"])
    )
    solver.add(
        refund_claim_direction_breached
        == And(factoring_qualified, variables["debtor_refund_claim_misdirected"])
    )
    solver.add(
        requires_human_factoring_assessment
        == Or(
            claim_identification_breached,
            factor_status_invalid,
            assignment_ban_ineffective_against_factor,
            client_warranty_breached,
            subsequent_assignment_unauthorized,
            debtor_notice_duty_breached,
            settlement_duty_breached,
            refund_claim_direction_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return FactoringEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            factoring_qualified=False,
            claim_identification_breached=False,
            factor_status_invalid=False,
            assignment_ban_ineffective_against_factor=False,
            client_warranty_breached=False,
            subsequent_assignment_unauthorized=False,
            debtor_notice_duty_breached=False,
            debtor_set_off_right_available=False,
            settlement_duty_breached=False,
            refund_claim_direction_breached=False,
            requires_human_factoring_assessment=True,
            reasons_ru=[
                "Набор фактов о финансировании под уступку денежного требования противоречив."
            ],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как финансирование под уступку денежного требования "
            "(факторинг): клиент уступает или обязуется уступить финансовому агенту денежное "
            "требование к должнику, а финансовый агент передаёт или обязуется передать клиенту "
            "денежные средства либо совершить иные предусмотренные договором действия "
            "(статья 824 ГК РФ)."
            if truth(factoring_qualified)
            else (
                "Отношения не квалифицированы как договор финансирования под уступку денежного "
                "требования."
            )
        ),
    ]
    if truth(claim_identification_breached):
        reasons_ru.append(
            "Уступаемое денежное требование должно быть определено в договоре способом, "
            "позволяющим идентифицировать существующее требование в момент заключения договора, а "
            "будущее требование — не позднее чем в момент его возникновения (статья 826 ГК РФ)."
        )
    if truth(factor_status_invalid):
        reasons_ru.append(
            "Финансовым агентом по договору факторинга выступают коммерческие организации, для "
            "которых такая деятельность допустима (статья 825 ГК РФ)."
        )
    if truth(assignment_ban_ineffective_against_factor):
        reasons_ru.append(
            "Уступка денежного требования финансовому агенту действительна, даже если между "
            "клиентом и должником существует соглашение о её запрете или ограничении; клиент при "
            "этом не освобождается от ответственности перед должником (статья 828 ГК РФ)."
        )
    if truth(client_warranty_breached):
        reasons_ru.append(
            "Клиент несёт ответственность за действительность уступаемого денежного требования, "
            "если договором не предусмотрено иное (статья 827 ГК РФ)."
        )
    if truth(subsequent_assignment_unauthorized):
        reasons_ru.append(
            "Последующая уступка денежного требования финансовым агентом допускается, только если "
            "она прямо предусмотрена договором факторинга (статья 829 ГК РФ)."
        )
    if truth(debtor_notice_duty_breached):
        reasons_ru.append(
            "Должник обязан произвести платёж финансовому агенту при условии письменного "
            "уведомления об уступке с определением подлежащего исполнению требования и указанием "
            "агента (статья 830 ГК РФ)."
        )
    if truth(debtor_set_off_right_available):
        reasons_ru.append(
            "Должник вправе предъявить к зачёту денежные требования к клиенту, основанные на "
            "договоре с ним и имевшиеся у должника ко времени получения уведомления об уступке "
            "(статья 832 ГК РФ)."
        )
    if truth(settlement_duty_breached):
        reasons_ru.append(
            "Расчёты сторон определяются тем, приобретено ли требование в целях покупки или в "
            "целях обеспечения исполнения обязательства клиента: при обеспечительной уступке "
            "агент обязан представить отчёт и передать сумму, превышающую обеспеченный долг "
            "(статья 831 ГК РФ)."
        )
    if truth(refund_claim_direction_breached):
        reasons_ru.append(
            "Должник вправе требовать возврата уплаченных сумм от клиента, а от финансового "
            "агента — только в предусмотренных законом случаях (статья 833 ГК РФ)."
        )
    return FactoringEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        factoring_qualified=truth(factoring_qualified),
        claim_identification_breached=truth(claim_identification_breached),
        factor_status_invalid=truth(factor_status_invalid),
        assignment_ban_ineffective_against_factor=truth(assignment_ban_ineffective_against_factor),
        client_warranty_breached=truth(client_warranty_breached),
        subsequent_assignment_unauthorized=truth(subsequent_assignment_unauthorized),
        debtor_notice_duty_breached=truth(debtor_notice_duty_breached),
        debtor_set_off_right_available=truth(debtor_set_off_right_available),
        settlement_duty_breached=truth(settlement_duty_breached),
        refund_claim_direction_breached=truth(refund_claim_direction_breached),
        requires_human_factoring_assessment=truth(requires_human_factoring_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о финансировании под уступку денежного "
            "требования и не заменяет судебную оценку.",
            "Идентифицируемость требования, действительность уступки и содержание расчётов сторон "
            "оцениваются экспертом и судом (статьи 826, 827 и 831 ГК РФ).",
        ],
    )
