from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


BANK_ACCOUNT_EVIDENCE_SCHEMA_VERSION = "contracts.bank-account-evidence.v0"
BANK_ACCOUNT_MAPPING_VERSION = "contracts-reviewed-bank-account-to-facts-v0"
BANK_ACCOUNT_MODEL_VERSION = "contracts-bank-account-articles-845-860-v0"


class BankAccountEvidencePredicate(str, Enum):
    # Договор банковского счёта и условия его заключения (статьи 845 и 846 ГК РФ).
    BANK_ACCOUNT_OPENED_FOR_CLIENT_FUNDS = "bank_account_opened_for_client_funds"
    ACCOUNT_OPENING_TERMS_BREACHED = "account_opening_terms_breached"
    # Распоряжение счётом и совершение операций (статьи 847–849 ГК РФ).
    DISPOSAL_RIGHTS_CERTIFICATION_BREACHED = "disposal_rights_certification_breached"
    OPERATION_DEADLINES_BREACHED = "operation_deadlines_breached"
    IMPROPER_OPERATION_LIABILITY_NOT_APPLIED = "improper_operation_liability_not_applied"
    # Кредитование счёта и оплата услуг банка (статьи 850–853 ГК РФ).
    ACCOUNT_CREDIT_TERMS_BREACHED = "account_credit_terms_breached"
    ACCOUNT_SERVICE_PAYMENT_TERMS_BREACHED = "account_service_payment_terms_breached"
    # Списание средств, банковская тайна и ограничение распоряжения (статьи 854–858 ГК РФ).
    FUNDS_DEBITED_WITHOUT_CLIENT_ORDER = "funds_debited_without_client_order"
    BANK_SECRECY_OR_RESTRICTION_BREACHED = "bank_secrecy_or_restriction_breached"
    # Расторжение договора и возврат остатка (статьи 859 и 860 ГК РФ).
    ACCOUNT_TERMINATION_AND_BALANCE_RETURN_BREACHED = (
        "account_termination_and_balance_return_breached"
    )


REQUIRED_BANK_ACCOUNT_PREDICATES = frozenset(BankAccountEvidencePredicate)


class BankAccountEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: BankAccountEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedBankAccountEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = BANK_ACCOUNT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[BankAccountEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedBankAccountEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Bank-account evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Bank-account evidence contains duplicate legal source refs.")
        return self


class BankAccountFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    bank_account_opened_for_client_funds: bool
    account_opening_terms_breached: bool
    disposal_rights_certification_breached: bool
    operation_deadlines_breached: bool
    improper_operation_liability_not_applied: bool
    account_credit_terms_breached: bool
    account_service_payment_terms_breached: bool
    funds_debited_without_client_order: bool
    bank_secrecy_or_restriction_breached: bool
    account_termination_and_balance_return_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "BankAccountFactSet":
        if self.improper_operation_liability_not_applied and not self.operation_deadlines_breached:
            raise ValueError(
                "Неприменение ответственности банка за ненадлежащее совершение операций "
                "относится только к случаю, когда нарушение сроков операций по счёту установлено."
            )
        if (
            self.funds_debited_without_client_order
            and not self.bank_account_opened_for_client_funds
        ):
            raise ValueError(
                "Списание денежных средств без распоряжения клиента относится только к договору "
                "банковского счёта."
            )
        return self


class BankAccountFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class BankAccountEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: BankAccountFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[BankAccountFactProvenance] = Field(default_factory=list)


class BankAccountConstraintSet(BaseModel):
    id: str
    model_version: str = BANK_ACCOUNT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class BankAccountEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    bank_account_qualified: bool
    account_opening_terms_duty_breached: bool
    disposal_rights_certification_duty_breached: bool
    operation_deadline_duty_breached: bool
    improper_operation_liability_breached: bool
    account_credit_duty_breached: bool
    account_service_payment_duty_breached: bool
    unauthorised_debiting_established: bool
    bank_secrecy_duty_breached: bool
    account_termination_duty_breached: bool
    requires_human_bank_account_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_bank_account_evidence(
    evidence: ReviewedBankAccountEvidence,
) -> BankAccountEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Bank-account evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Bank-account evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_BANK_ACCOUNT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed bank-account evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_BANK_ACCOUNT_PREDICATES
    }
    return BankAccountEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=BANK_ACCOUNT_MAPPING_VERSION,
        facts=BankAccountFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            BankAccountFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_BANK_ACCOUNT_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_bank_account_constraint_set(
    mapping: BankAccountEvidenceMappingResult,
) -> BankAccountConstraintSet:
    return BankAccountConstraintSet(
        id=f"bank-account-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "bank_account_qualified == bank_account_opened_for_client_funds",
            "account_opening_terms_duty_breached == bank_account_qualified AND account_opening_terms_breached",
            "disposal_rights_certification_duty_breached == bank_account_qualified AND disposal_rights_certification_breached",
            "operation_deadline_duty_breached == bank_account_qualified AND operation_deadlines_breached",
            "improper_operation_liability_breached == bank_account_qualified AND operation_deadlines_breached AND improper_operation_liability_not_applied",
            "account_credit_duty_breached == bank_account_qualified AND account_credit_terms_breached",
            "account_service_payment_duty_breached == bank_account_qualified AND account_service_payment_terms_breached",
            "unauthorised_debiting_established == bank_account_qualified AND funds_debited_without_client_order",
            "bank_secrecy_duty_breached == bank_account_qualified AND bank_secrecy_or_restriction_breached",
            "account_termination_duty_breached == bank_account_qualified AND account_termination_and_balance_return_breached",
            "requires_human_bank_account_assessment == account_opening_terms_duty_breached OR disposal_rights_certification_duty_breached OR operation_deadline_duty_breached OR account_credit_duty_breached OR account_service_payment_duty_breached OR unauthorised_debiting_established OR bank_secrecy_duty_breached OR account_termination_duty_breached",
        ],
    )


def evaluate_bank_account_constraints(
    constraint_set: BankAccountConstraintSet,
    facts: BankAccountFactSet,
) -> BankAccountEvaluation:
    variables = {field_name: Bool(field_name) for field_name in BankAccountFactSet.model_fields}
    bank_account_qualified = Bool("bank_account_qualified")
    account_opening_terms_duty_breached = Bool("account_opening_terms_duty_breached")
    disposal_rights_certification_duty_breached = Bool(
        "disposal_rights_certification_duty_breached"
    )
    operation_deadline_duty_breached = Bool("operation_deadline_duty_breached")
    improper_operation_liability_breached = Bool("improper_operation_liability_breached")
    account_credit_duty_breached = Bool("account_credit_duty_breached")
    account_service_payment_duty_breached = Bool("account_service_payment_duty_breached")
    unauthorised_debiting_established = Bool("unauthorised_debiting_established")
    bank_secrecy_duty_breached = Bool("bank_secrecy_duty_breached")
    account_termination_duty_breached = Bool("account_termination_duty_breached")
    requires_human_bank_account_assessment = Bool("requires_human_bank_account_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(bank_account_qualified == variables["bank_account_opened_for_client_funds"])
    solver.add(
        account_opening_terms_duty_breached
        == And(bank_account_qualified, variables["account_opening_terms_breached"])
    )
    solver.add(
        disposal_rights_certification_duty_breached
        == And(bank_account_qualified, variables["disposal_rights_certification_breached"])
    )
    solver.add(
        operation_deadline_duty_breached
        == And(bank_account_qualified, variables["operation_deadlines_breached"])
    )
    solver.add(
        improper_operation_liability_breached
        == And(
            bank_account_qualified,
            variables["operation_deadlines_breached"],
            variables["improper_operation_liability_not_applied"],
        )
    )
    solver.add(
        account_credit_duty_breached
        == And(bank_account_qualified, variables["account_credit_terms_breached"])
    )
    solver.add(
        account_service_payment_duty_breached
        == And(bank_account_qualified, variables["account_service_payment_terms_breached"])
    )
    solver.add(
        unauthorised_debiting_established
        == And(bank_account_qualified, variables["funds_debited_without_client_order"])
    )
    solver.add(
        bank_secrecy_duty_breached
        == And(bank_account_qualified, variables["bank_secrecy_or_restriction_breached"])
    )
    solver.add(
        account_termination_duty_breached
        == And(bank_account_qualified, variables["account_termination_and_balance_return_breached"])
    )
    solver.add(
        requires_human_bank_account_assessment
        == Or(
            account_opening_terms_duty_breached,
            disposal_rights_certification_duty_breached,
            operation_deadline_duty_breached,
            account_credit_duty_breached,
            account_service_payment_duty_breached,
            unauthorised_debiting_established,
            bank_secrecy_duty_breached,
            account_termination_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return BankAccountEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            bank_account_qualified=False,
            account_opening_terms_duty_breached=False,
            disposal_rights_certification_duty_breached=False,
            operation_deadline_duty_breached=False,
            improper_operation_liability_breached=False,
            account_credit_duty_breached=False,
            account_service_payment_duty_breached=False,
            unauthorised_debiting_established=False,
            bank_secrecy_duty_breached=False,
            account_termination_duty_breached=False,
            requires_human_bank_account_assessment=True,
            reasons_ru=["Набор фактов о банковском счёте противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор банковского счёта: банк обязуется принимать и "
            "зачислять поступающие на счёт клиента денежные средства, выполнять распоряжения "
            "клиента о перечислении и выдаче соответствующих сумм со счёта и проводить другие "
            "операции по счёту (статья 845 ГК РФ)."
            if truth(bank_account_qualified)
            else "Отношения не квалифицированы как договор банковского счёта."
        ),
    ]
    if truth(account_opening_terms_duty_breached):
        reasons_ru.append(
            "Банк обязан заключить договор банковского счёта с клиентом, обратившимся с "
            "предложением открыть счёт на объявленных банком условиях, соответствующих закону и "
            "банковским правилам (статья 846 ГК РФ)."
        )
    if truth(disposal_rights_certification_duty_breached):
        reasons_ru.append(
            "Права лиц, осуществляющих от имени клиента распоряжения о перечислении и выдаче "
            "средств со счёта, удостоверяются в порядке, предусмотренном законом и банковскими "
            "правилами, а банк обязан совершать для клиента операции, предусмотренные для счетов "
            "данного вида (статьи 847 и 848 ГК РФ)."
        )
    if truth(operation_deadline_duty_breached):
        reasons_ru.append(
            "Банк обязан зачислять поступившие на счёт клиента денежные средства и выдавать или "
            "перечислять их по распоряжению клиента в сроки, установленные законом или договором "
            "(статья 849 ГК РФ)."
        )
    if truth(improper_operation_liability_breached):
        reasons_ru.append(
            "В случаях несвоевременного зачисления, необоснованного списания либо невыполнения "
            "указаний клиента о перечислении или выдаче средств банк обязан уплатить проценты в "
            "порядке и размере, предусмотренных статьёй 395 ГК РФ (статья 856 ГК РФ)."
        )
    if truth(account_credit_duty_breached):
        reasons_ru.append(
            "При осуществлении платежей при отсутствии средств на счёте банк считается "
            "предоставившим клиенту кредит на соответствующую сумму, а права и обязанности "
            "сторон определяются правилами о займе и кредите, если договором не предусмотрено "
            "иное (статья 850 ГК РФ)."
        )
    if truth(account_service_payment_duty_breached):
        reasons_ru.append(
            "Оплата услуг банка по совершению операций, уплата процентов за пользование "
            "средствами, находящимися на счёте, и зачёт встречных требований банка и клиента "
            "производятся в порядке, предусмотренном договором и законом "
            "(статьи 851–853 ГК РФ)."
        )
    if truth(unauthorised_debiting_established):
        reasons_ru.append(
            "Списание денежных средств со счёта осуществляется банком на основании распоряжения "
            "клиента; без такого распоряжения списание допускается по решению суда и в случаях, "
            "установленных законом или предусмотренных договором, а при недостаточности средств "
            "соблюдается установленная очерёдность (статьи 854 и 855 ГК РФ)."
        )
    if truth(bank_secrecy_duty_breached):
        reasons_ru.append(
            "Банк гарантирует тайну банковского счёта, операций по нему и сведений о клиенте, а "
            "ограничение прав клиента на распоряжение средствами допускается только при наложении "
            "ареста или приостановлении операций в случаях, предусмотренных законом "
            "(статьи 857 и 858 ГК РФ)."
        )
    if truth(account_termination_duty_breached):
        reasons_ru.append(
            "Договор банковского счёта расторгается по заявлению клиента в любое время, а остаток "
            "денежных средств выдаётся клиенту либо перечисляется по его указанию в установленный "
            "законом срок (статьи 859 и 860 ГК РФ)."
        )
    return BankAccountEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        bank_account_qualified=truth(bank_account_qualified),
        account_opening_terms_duty_breached=truth(account_opening_terms_duty_breached),
        disposal_rights_certification_duty_breached=truth(
            disposal_rights_certification_duty_breached
        ),
        operation_deadline_duty_breached=truth(operation_deadline_duty_breached),
        improper_operation_liability_breached=truth(improper_operation_liability_breached),
        account_credit_duty_breached=truth(account_credit_duty_breached),
        account_service_payment_duty_breached=truth(account_service_payment_duty_breached),
        unauthorised_debiting_established=truth(unauthorised_debiting_established),
        bank_secrecy_duty_breached=truth(bank_secrecy_duty_breached),
        account_termination_duty_breached=truth(account_termination_duty_breached),
        requires_human_bank_account_assessment=truth(requires_human_bank_account_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о банковском счёте и не заменяет "
            "судебную оценку.",
            "Основания отказа в заключении договора, законность списания без распоряжения клиента "
            "и наличие оснований для ограничения распоряжения счётом оцениваются экспертом и "
            "судом (статьи 846, 854 и 858 ГК РФ).",
        ],
    )
