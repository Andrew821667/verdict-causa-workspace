from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


SETTLEMENTS_EVIDENCE_SCHEMA_VERSION = "contracts.settlements-evidence.v0"
SETTLEMENTS_MAPPING_VERSION = "contracts-reviewed-settlements-to-facts-v0"
SETTLEMENTS_MODEL_VERSION = "contracts-settlements-articles-861-885-v0"


class SettlementsEvidencePredicate(str, Enum):
    # Наличные и безналичные расчёты и их формы (статьи 861 и 862 ГК РФ).
    CASHLESS_SETTLEMENTS_PERFORMED = "cashless_settlements_performed"
    SETTLEMENT_FORM_NOT_PROVIDED_BY_LAW = "settlement_form_not_provided_by_law"
    # Расчёты платёжными поручениями (статьи 863–866 ГК РФ).
    PAYMENT_ORDER_EXECUTION_BREACHED = "payment_order_execution_breached"
    PAYMENT_ORDER_LIABILITY_NOT_APPLIED = "payment_order_liability_not_applied"
    # Расчёты по аккредитиву (статьи 867–873 ГК РФ).
    LETTER_OF_CREDIT_TERMS_BREACHED = "letter_of_credit_terms_breached"
    LETTER_OF_CREDIT_CLOSURE_RULES_BREACHED = "letter_of_credit_closure_rules_breached"
    # Расчёты по инкассо (статьи 874–876 ГК РФ).
    COLLECTION_ORDER_EXECUTION_BREACHED = "collection_order_execution_breached"
    # Расчёты чеками (статьи 877–885 ГК РФ).
    CHEQUE_REQUISITES_BREACHED = "cheque_requisites_breached"
    CHEQUE_PAYMENT_AND_WARRANTY_BREACHED = "cheque_payment_and_warranty_breached"
    CHEQUE_NON_PAYMENT_CERTIFICATION_BREACHED = "cheque_non_payment_certification_breached"


REQUIRED_SETTLEMENTS_PREDICATES = frozenset(SettlementsEvidencePredicate)


class SettlementsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: SettlementsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedSettlementsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = SETTLEMENTS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[SettlementsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedSettlementsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Settlements evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Settlements evidence contains duplicate legal source refs.")
        return self


class SettlementsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cashless_settlements_performed: bool
    settlement_form_not_provided_by_law: bool
    payment_order_execution_breached: bool
    payment_order_liability_not_applied: bool
    letter_of_credit_terms_breached: bool
    letter_of_credit_closure_rules_breached: bool
    collection_order_execution_breached: bool
    cheque_requisites_breached: bool
    cheque_payment_and_warranty_breached: bool
    cheque_non_payment_certification_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "SettlementsFactSet":
        if self.payment_order_liability_not_applied and not self.payment_order_execution_breached:
            raise ValueError(
                "Неприменение ответственности за неисполнение платёжного поручения относится "
                "только к случаю, когда нарушение исполнения поручения установлено."
            )
        if self.settlement_form_not_provided_by_law and not self.cashless_settlements_performed:
            raise ValueError(
                "Использование формы расчётов, не предусмотренной законом, относится только к "
                "безналичным расчётам."
            )
        return self


class SettlementsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class SettlementsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: SettlementsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[SettlementsFactProvenance] = Field(default_factory=list)


class SettlementsConstraintSet(BaseModel):
    id: str
    model_version: str = SETTLEMENTS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class SettlementsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    cashless_settlements_qualified: bool
    settlement_form_legality_breached: bool
    payment_order_execution_duty_breached: bool
    payment_order_liability_breached: bool
    letter_of_credit_duty_breached: bool
    letter_of_credit_closure_duty_breached: bool
    collection_execution_duty_breached: bool
    cheque_requisites_duty_breached: bool
    cheque_payment_duty_breached: bool
    cheque_non_payment_certification_duty_breached: bool
    requires_human_settlements_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_settlements_evidence(
    evidence: ReviewedSettlementsEvidence,
) -> SettlementsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Settlements evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Settlements evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_SETTLEMENTS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed settlements evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_SETTLEMENTS_PREDICATES
    }
    return SettlementsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=SETTLEMENTS_MAPPING_VERSION,
        facts=SettlementsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            SettlementsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_SETTLEMENTS_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_settlements_constraint_set(
    mapping: SettlementsEvidenceMappingResult,
) -> SettlementsConstraintSet:
    return SettlementsConstraintSet(
        id=f"settlements-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "cashless_settlements_qualified == cashless_settlements_performed",
            "settlement_form_legality_breached == cashless_settlements_qualified AND settlement_form_not_provided_by_law",
            "payment_order_execution_duty_breached == cashless_settlements_qualified AND payment_order_execution_breached",
            "payment_order_liability_breached == cashless_settlements_qualified AND payment_order_execution_breached AND payment_order_liability_not_applied",
            "letter_of_credit_duty_breached == cashless_settlements_qualified AND letter_of_credit_terms_breached",
            "letter_of_credit_closure_duty_breached == cashless_settlements_qualified AND letter_of_credit_closure_rules_breached",
            "collection_execution_duty_breached == cashless_settlements_qualified AND collection_order_execution_breached",
            "cheque_requisites_duty_breached == cashless_settlements_qualified AND cheque_requisites_breached",
            "cheque_payment_duty_breached == cashless_settlements_qualified AND cheque_payment_and_warranty_breached",
            "cheque_non_payment_certification_duty_breached == cashless_settlements_qualified AND cheque_non_payment_certification_breached",
            "requires_human_settlements_assessment == settlement_form_legality_breached OR payment_order_execution_duty_breached OR letter_of_credit_duty_breached OR letter_of_credit_closure_duty_breached OR collection_execution_duty_breached OR cheque_requisites_duty_breached OR cheque_payment_duty_breached OR cheque_non_payment_certification_duty_breached",
        ],
    )


def evaluate_settlements_constraints(
    constraint_set: SettlementsConstraintSet,
    facts: SettlementsFactSet,
) -> SettlementsEvaluation:
    variables = {field_name: Bool(field_name) for field_name in SettlementsFactSet.model_fields}
    cashless_settlements_qualified = Bool("cashless_settlements_qualified")
    settlement_form_legality_breached = Bool("settlement_form_legality_breached")
    payment_order_execution_duty_breached = Bool("payment_order_execution_duty_breached")
    payment_order_liability_breached = Bool("payment_order_liability_breached")
    letter_of_credit_duty_breached = Bool("letter_of_credit_duty_breached")
    letter_of_credit_closure_duty_breached = Bool("letter_of_credit_closure_duty_breached")
    collection_execution_duty_breached = Bool("collection_execution_duty_breached")
    cheque_requisites_duty_breached = Bool("cheque_requisites_duty_breached")
    cheque_payment_duty_breached = Bool("cheque_payment_duty_breached")
    cheque_non_payment_certification_duty_breached = Bool(
        "cheque_non_payment_certification_duty_breached"
    )
    requires_human_settlements_assessment = Bool("requires_human_settlements_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(cashless_settlements_qualified == variables["cashless_settlements_performed"])
    solver.add(
        settlement_form_legality_breached
        == And(cashless_settlements_qualified, variables["settlement_form_not_provided_by_law"])
    )
    solver.add(
        payment_order_execution_duty_breached
        == And(cashless_settlements_qualified, variables["payment_order_execution_breached"])
    )
    solver.add(
        payment_order_liability_breached
        == And(
            cashless_settlements_qualified,
            variables["payment_order_execution_breached"],
            variables["payment_order_liability_not_applied"],
        )
    )
    solver.add(
        letter_of_credit_duty_breached
        == And(cashless_settlements_qualified, variables["letter_of_credit_terms_breached"])
    )
    solver.add(
        letter_of_credit_closure_duty_breached
        == And(cashless_settlements_qualified, variables["letter_of_credit_closure_rules_breached"])
    )
    solver.add(
        collection_execution_duty_breached
        == And(cashless_settlements_qualified, variables["collection_order_execution_breached"])
    )
    solver.add(
        cheque_requisites_duty_breached
        == And(cashless_settlements_qualified, variables["cheque_requisites_breached"])
    )
    solver.add(
        cheque_payment_duty_breached
        == And(cashless_settlements_qualified, variables["cheque_payment_and_warranty_breached"])
    )
    solver.add(
        cheque_non_payment_certification_duty_breached
        == And(
            cashless_settlements_qualified,
            variables["cheque_non_payment_certification_breached"],
        )
    )
    solver.add(
        requires_human_settlements_assessment
        == Or(
            settlement_form_legality_breached,
            payment_order_execution_duty_breached,
            letter_of_credit_duty_breached,
            letter_of_credit_closure_duty_breached,
            collection_execution_duty_breached,
            cheque_requisites_duty_breached,
            cheque_payment_duty_breached,
            cheque_non_payment_certification_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return SettlementsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            cashless_settlements_qualified=False,
            settlement_form_legality_breached=False,
            payment_order_execution_duty_breached=False,
            payment_order_liability_breached=False,
            letter_of_credit_duty_breached=False,
            letter_of_credit_closure_duty_breached=False,
            collection_execution_duty_breached=False,
            cheque_requisites_duty_breached=False,
            cheque_payment_duty_breached=False,
            cheque_non_payment_certification_duty_breached=False,
            requires_human_settlements_assessment=True,
            reasons_ru=["Набор фактов о расчётах противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Расчёты по обязательству осуществляются в безналичном порядке в формах, "
            "предусмотренных законом, банковскими правилами и применяемыми в банковской практике "
            "обычаями (статьи 861 и 862 ГК РФ)."
            if truth(cashless_settlements_qualified)
            else "Безналичные расчёты по спорному обязательству не установлены."
        ),
    ]
    if truth(settlement_form_legality_breached):
        reasons_ru.append(
            "Безналичные расчёты осуществляются платёжными поручениями, по аккредитиву, чеками, "
            "по инкассо, а также в иных формах, предусмотренных законом, банковскими правилами "
            "или применяемыми в банковской практике обычаями (статья 862 ГК РФ)."
        )
    if truth(payment_order_execution_duty_breached):
        reasons_ru.append(
            "При расчётах платёжным поручением банк обязуется перевести денежные средства "
            "плательщика получателю в срок, предусмотренный законом или договором, а также "
            "информировать плательщика об исполнении поручения (статьи 863–865 ГК РФ)."
        )
    if truth(payment_order_liability_breached):
        reasons_ru.append(
            "За неисполнение или ненадлежащее исполнение платёжного поручения банк несёт "
            "ответственность по основаниям и в размерах, предусмотренных главой 25 ГК РФ, с "
            "учётом правил статьи 866 ГК РФ."
        )
    if truth(letter_of_credit_duty_breached):
        reasons_ru.append(
            "При расчётах по аккредитиву банк-эмитент обязуется произвести платежи получателю "
            "средств при представлении документов, соответствующих условиям аккредитива, а "
            "исполнение производится в порядке, предусмотренном законом и банковскими правилами "
            "(статьи 867–871 ГК РФ)."
        )
    if truth(letter_of_credit_closure_duty_breached):
        reasons_ru.append(
            "Закрытие аккредитива в исполняющем банке производится по основаниям и в порядке, "
            "предусмотренных законом, с уведомлением банка-эмитента (статья 873 ГК РФ)."
        )
    if truth(collection_execution_duty_breached):
        reasons_ru.append(
            "При расчётах по инкассо банк-эмитент обязуется по поручению клиента осуществить "
            "действия по получению платежа от плательщика, а исполняющий банк исполняет "
            "инкассовое поручение в предусмотренном порядке и извещает о неисполнении "
            "(статьи 874–876 ГК РФ)."
        )
    if truth(cheque_requisites_duty_breached):
        reasons_ru.append(
            "Чеком признаётся ценная бумага, содержащая ничем не обусловленное распоряжение "
            "чекодателя банку произвести платёж указанной в нём суммы; отсутствие в документе "
            "какого-либо из обязательных реквизитов лишает его силы чека "
            "(статьи 877 и 878 ГК РФ)."
        )
    if truth(cheque_payment_duty_breached):
        reasons_ru.append(
            "Чек оплачивается за счёт средств чекодателя при условии предъявления его к оплате в "
            "установленный срок; передача прав по чеку и гарантия платежа авалем подчиняются "
            "правилам статей 879–881 ГК РФ."
        )
    if truth(cheque_non_payment_certification_duty_breached):
        reasons_ru.append(
            "Отказ от оплаты чека удостоверяется предусмотренными законом способами, чекодержатель "
            "извещает своего индоссанта и чекодателя, а последствия неоплаты чека определяются "
            "статьями 883–885 ГК РФ."
        )
    return SettlementsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        cashless_settlements_qualified=truth(cashless_settlements_qualified),
        settlement_form_legality_breached=truth(settlement_form_legality_breached),
        payment_order_execution_duty_breached=truth(payment_order_execution_duty_breached),
        payment_order_liability_breached=truth(payment_order_liability_breached),
        letter_of_credit_duty_breached=truth(letter_of_credit_duty_breached),
        letter_of_credit_closure_duty_breached=truth(letter_of_credit_closure_duty_breached),
        collection_execution_duty_breached=truth(collection_execution_duty_breached),
        cheque_requisites_duty_breached=truth(cheque_requisites_duty_breached),
        cheque_payment_duty_breached=truth(cheque_payment_duty_breached),
        cheque_non_payment_certification_duty_breached=truth(
            cheque_non_payment_certification_duty_breached
        ),
        requires_human_settlements_assessment=truth(requires_human_settlements_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о расчётах и не заменяет судебную оценку.",
            "Соответствие представленных документов условиям аккредитива, основания неисполнения "
            "поручений и достаточность средств оцениваются экспертом и судом "
            "(статьи 866, 871 и 879 ГК РФ).",
        ],
    )
