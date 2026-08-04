from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


BANK_DEPOSIT_EVIDENCE_SCHEMA_VERSION = "contracts.bank-deposit-evidence.v0"
BANK_DEPOSIT_MAPPING_VERSION = "contracts-reviewed-bank-deposit-to-facts-v0"
BANK_DEPOSIT_MODEL_VERSION = "contracts-bank-deposit-articles-834-844-v0"


class BankDepositEvidencePredicate(str, Enum):
    # Договор банковского вклада и право привлекать вклады (статьи 834 и 835 ГК РФ).
    DEPOSIT_ACCEPTED_FOR_RETURN_WITH_INTEREST = "deposit_accepted_for_return_with_interest"
    DEPOSIT_TAKEN_BY_UNAUTHORISED_PERSON = "deposit_taken_by_unauthorised_person"
    # Форма договора банковского вклада (статья 836 ГК РФ).
    DEPOSIT_WRITTEN_FORM_NOT_OBSERVED = "deposit_written_form_not_observed"
    # Виды вкладов и возврат вклада гражданина (статья 837 ГК РФ).
    CITIZEN_DEPOSIT_ON_DEMAND_REPAYMENT_BREACHED = "citizen_deposit_on_demand_repayment_breached"
    EARLY_REPAYMENT_INTEREST_MISCALCULATED = "early_repayment_interest_miscalculated"
    # Проценты на вклад и порядок их начисления (статьи 838 и 839 ГК РФ).
    DEPOSIT_INTEREST_NOT_PAID_AS_AGREED = "deposit_interest_not_paid_as_agreed"
    TERM_DEPOSIT_INTEREST_RATE_UNILATERALLY_REDUCED = (
        "term_deposit_interest_rate_unilaterally_reduced"
    )
    # Обеспечение возврата вклада и вклады в пользу третьих лиц (статьи 840–842 ГК РФ).
    DEPOSIT_REPAYMENT_SECURITY_NOT_ENSURED = "deposit_repayment_security_not_ensured"
    THIRD_PARTY_DEPOSIT_RIGHTS_DISREGARDED = "third_party_deposit_rights_disregarded"
    # Сберегательная книжка и сберегательный сертификат (статьи 843 и 844 ГК РФ).
    SAVINGS_DOCUMENT_RULES_BREACHED = "savings_document_rules_breached"


REQUIRED_BANK_DEPOSIT_PREDICATES = frozenset(BankDepositEvidencePredicate)


class BankDepositEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: BankDepositEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedBankDepositEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = BANK_DEPOSIT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[BankDepositEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedBankDepositEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Bank-deposit evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Bank-deposit evidence contains duplicate legal source refs.")
        return self


class BankDepositFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    deposit_accepted_for_return_with_interest: bool
    deposit_taken_by_unauthorised_person: bool
    deposit_written_form_not_observed: bool
    citizen_deposit_on_demand_repayment_breached: bool
    early_repayment_interest_miscalculated: bool
    deposit_interest_not_paid_as_agreed: bool
    term_deposit_interest_rate_unilaterally_reduced: bool
    deposit_repayment_security_not_ensured: bool
    third_party_deposit_rights_disregarded: bool
    savings_document_rules_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "BankDepositFactSet":
        if (
            self.early_repayment_interest_miscalculated
            and not self.citizen_deposit_on_demand_repayment_breached
        ):
            raise ValueError(
                "Неверный перерасчёт процентов при досрочном возврате относится только к случаю, "
                "когда нарушение возврата вклада по первому требованию установлено."
            )
        if (
            self.deposit_written_form_not_observed
            and not self.deposit_accepted_for_return_with_interest
        ):
            raise ValueError(
                "Несоблюдение письменной формы относится только к договору банковского вклада."
            )
        return self


class BankDepositFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class BankDepositEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: BankDepositFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[BankDepositFactProvenance] = Field(default_factory=list)


class BankDepositConstraintSet(BaseModel):
    id: str
    model_version: str = BANK_DEPOSIT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class BankDepositEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    bank_deposit_qualified: bool
    deposit_acceptance_unauthorised: bool
    deposit_form_void: bool
    on_demand_repayment_duty_breached: bool
    early_repayment_interest_breached: bool
    interest_payment_duty_breached: bool
    term_rate_reduction_prohibited: bool
    repayment_security_duty_breached: bool
    third_party_deposit_rights_breached: bool
    savings_document_duty_breached: bool
    requires_human_bank_deposit_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_bank_deposit_evidence(
    evidence: ReviewedBankDepositEvidence,
) -> BankDepositEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Bank-deposit evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Bank-deposit evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_BANK_DEPOSIT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed bank-deposit evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_BANK_DEPOSIT_PREDICATES
    }
    return BankDepositEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=BANK_DEPOSIT_MAPPING_VERSION,
        facts=BankDepositFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            BankDepositFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_BANK_DEPOSIT_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_bank_deposit_constraint_set(
    mapping: BankDepositEvidenceMappingResult,
) -> BankDepositConstraintSet:
    return BankDepositConstraintSet(
        id=f"bank-deposit-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "bank_deposit_qualified == deposit_accepted_for_return_with_interest",
            "deposit_acceptance_unauthorised == bank_deposit_qualified AND deposit_taken_by_unauthorised_person",
            "deposit_form_void == bank_deposit_qualified AND deposit_written_form_not_observed",
            "on_demand_repayment_duty_breached == bank_deposit_qualified AND citizen_deposit_on_demand_repayment_breached",
            "early_repayment_interest_breached == bank_deposit_qualified AND citizen_deposit_on_demand_repayment_breached AND early_repayment_interest_miscalculated",
            "interest_payment_duty_breached == bank_deposit_qualified AND deposit_interest_not_paid_as_agreed",
            "term_rate_reduction_prohibited == bank_deposit_qualified AND term_deposit_interest_rate_unilaterally_reduced",
            "repayment_security_duty_breached == bank_deposit_qualified AND deposit_repayment_security_not_ensured",
            "third_party_deposit_rights_breached == bank_deposit_qualified AND third_party_deposit_rights_disregarded",
            "savings_document_duty_breached == bank_deposit_qualified AND savings_document_rules_breached",
            "requires_human_bank_deposit_assessment == deposit_acceptance_unauthorised OR deposit_form_void OR on_demand_repayment_duty_breached OR interest_payment_duty_breached OR term_rate_reduction_prohibited OR repayment_security_duty_breached OR third_party_deposit_rights_breached OR savings_document_duty_breached",
        ],
    )


def evaluate_bank_deposit_constraints(
    constraint_set: BankDepositConstraintSet,
    facts: BankDepositFactSet,
) -> BankDepositEvaluation:
    variables = {field_name: Bool(field_name) for field_name in BankDepositFactSet.model_fields}
    bank_deposit_qualified = Bool("bank_deposit_qualified")
    deposit_acceptance_unauthorised = Bool("deposit_acceptance_unauthorised")
    deposit_form_void = Bool("deposit_form_void")
    on_demand_repayment_duty_breached = Bool("on_demand_repayment_duty_breached")
    early_repayment_interest_breached = Bool("early_repayment_interest_breached")
    interest_payment_duty_breached = Bool("interest_payment_duty_breached")
    term_rate_reduction_prohibited = Bool("term_rate_reduction_prohibited")
    repayment_security_duty_breached = Bool("repayment_security_duty_breached")
    third_party_deposit_rights_breached = Bool("third_party_deposit_rights_breached")
    savings_document_duty_breached = Bool("savings_document_duty_breached")
    requires_human_bank_deposit_assessment = Bool("requires_human_bank_deposit_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(bank_deposit_qualified == variables["deposit_accepted_for_return_with_interest"])
    solver.add(
        deposit_acceptance_unauthorised
        == And(bank_deposit_qualified, variables["deposit_taken_by_unauthorised_person"])
    )
    solver.add(
        deposit_form_void
        == And(bank_deposit_qualified, variables["deposit_written_form_not_observed"])
    )
    solver.add(
        on_demand_repayment_duty_breached
        == And(bank_deposit_qualified, variables["citizen_deposit_on_demand_repayment_breached"])
    )
    solver.add(
        early_repayment_interest_breached
        == And(
            bank_deposit_qualified,
            variables["citizen_deposit_on_demand_repayment_breached"],
            variables["early_repayment_interest_miscalculated"],
        )
    )
    solver.add(
        interest_payment_duty_breached
        == And(bank_deposit_qualified, variables["deposit_interest_not_paid_as_agreed"])
    )
    solver.add(
        term_rate_reduction_prohibited
        == And(bank_deposit_qualified, variables["term_deposit_interest_rate_unilaterally_reduced"])
    )
    solver.add(
        repayment_security_duty_breached
        == And(bank_deposit_qualified, variables["deposit_repayment_security_not_ensured"])
    )
    solver.add(
        third_party_deposit_rights_breached
        == And(bank_deposit_qualified, variables["third_party_deposit_rights_disregarded"])
    )
    solver.add(
        savings_document_duty_breached
        == And(bank_deposit_qualified, variables["savings_document_rules_breached"])
    )
    solver.add(
        requires_human_bank_deposit_assessment
        == Or(
            deposit_acceptance_unauthorised,
            deposit_form_void,
            on_demand_repayment_duty_breached,
            interest_payment_duty_breached,
            term_rate_reduction_prohibited,
            repayment_security_duty_breached,
            third_party_deposit_rights_breached,
            savings_document_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return BankDepositEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            bank_deposit_qualified=False,
            deposit_acceptance_unauthorised=False,
            deposit_form_void=False,
            on_demand_repayment_duty_breached=False,
            early_repayment_interest_breached=False,
            interest_payment_duty_breached=False,
            term_rate_reduction_prohibited=False,
            repayment_security_duty_breached=False,
            third_party_deposit_rights_breached=False,
            savings_document_duty_breached=False,
            requires_human_bank_deposit_assessment=True,
            reasons_ru=["Набор фактов о банковском вкладе противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор банковского вклада: банк, принявший поступившую "
            "от вкладчика или для него денежную сумму, обязуется возвратить сумму вклада и "
            "выплатить проценты на условиях и в порядке, предусмотренных договором "
            "(статья 834 ГК РФ)."
            if truth(bank_deposit_qualified)
            else "Отношения не квалифицированы как договор банковского вклада."
        ),
    ]
    if truth(deposit_acceptance_unauthorised):
        reasons_ru.append(
            "Право на привлечение денежных средств во вклады принадлежит банкам, которым такое "
            "право предоставлено в соответствии с выданным в установленном порядке разрешением "
            "(статья 835 ГК РФ)."
        )
    if truth(deposit_form_void):
        reasons_ru.append(
            "Договор банковского вклада должен быть заключён в письменной форме; несоблюдение "
            "письменной формы влечёт ничтожность договора (статья 836 ГК РФ)."
        )
    if truth(on_demand_repayment_duty_breached):
        reasons_ru.append(
            "Банк обязан выдать сумму вклада или её часть по первому требованию вкладчика; "
            "условие об отказе гражданина от права на получение вклада по первому требованию "
            "ничтожно (статья 837 ГК РФ)."
        )
    if truth(early_repayment_interest_breached):
        reasons_ru.append(
            "При возврате вклада до истечения срока либо до наступления иных предусмотренных "
            "договором обстоятельств проценты выплачиваются в размере, соответствующем размеру "
            "процентов по вкладам до востребования, если договором не предусмотрен иной размер "
            "(статья 837 ГК РФ)."
        )
    if truth(interest_payment_duty_breached):
        reasons_ru.append(
            "Банк выплачивает вкладчику проценты на сумму вклада в размере, определяемом "
            "договором, а проценты начисляются со дня, следующего за днём поступления суммы в "
            "банк, до дня её возврата вкладчику включительно (статьи 838 и 839 ГК РФ)."
        )
    if truth(term_rate_reduction_prohibited):
        reasons_ru.append(
            "По вкладу, внесённому гражданином на условиях выдачи по истечении определённого "
            "срока либо при наступлении предусмотренных договором обстоятельств, банк не вправе "
            "односторонне уменьшать размер процентов, если иное не предусмотрено законом "
            "(статья 838 ГК РФ)."
        )
    if truth(repayment_security_duty_breached):
        reasons_ru.append(
            "Банк обязан обеспечивать возврат вкладов граждан путём обязательного страхования, а "
            "способы обеспечения возврата вкладов юридических лиц определяются договором "
            "(статья 840 ГК РФ)."
        )
    if truth(third_party_deposit_rights_breached):
        reasons_ru.append(
            "Денежные средства, поступившие в банк на имя вкладчика от третьих лиц, зачисляются "
            "на его счёт, а по вкладу в пользу третьего лица такое лицо приобретает права "
            "вкладчика с момента предъявления им первого требования либо иного выражения "
            "намерения воспользоваться правами (статьи 841 и 842 ГК РФ)."
        )
    if truth(savings_document_duty_breached):
        reasons_ru.append(
            "Выдача вклада, выплата процентов и исполнение распоряжений вкладчика о перечислении "
            "денежных средств осуществляются при предъявлении сберегательной книжки, а права "
            "по сберегательному сертификату удостоверяются самим сертификатом на предусмотренных "
            "законом условиях (статьи 843 и 844 ГК РФ)."
        )
    return BankDepositEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        bank_deposit_qualified=truth(bank_deposit_qualified),
        deposit_acceptance_unauthorised=truth(deposit_acceptance_unauthorised),
        deposit_form_void=truth(deposit_form_void),
        on_demand_repayment_duty_breached=truth(on_demand_repayment_duty_breached),
        early_repayment_interest_breached=truth(early_repayment_interest_breached),
        interest_payment_duty_breached=truth(interest_payment_duty_breached),
        term_rate_reduction_prohibited=truth(term_rate_reduction_prohibited),
        repayment_security_duty_breached=truth(repayment_security_duty_breached),
        third_party_deposit_rights_breached=truth(third_party_deposit_rights_breached),
        savings_document_duty_breached=truth(savings_document_duty_breached),
        requires_human_bank_deposit_assessment=truth(requires_human_bank_deposit_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о банковском вкладе и не заменяет "
            "судебную оценку.",
            "Наличие у банка права привлекать вклады, достаточность обеспечения возврата и "
            "содержание условий о процентах оцениваются экспертом и судом "
            "(статьи 835, 838 и 840 ГК РФ).",
        ],
    )
