"""Формальная модель специальных видов банковских счетов.

Статьи 860.1–860.15 ГК РФ: номинальный счёт (§ 2), счёт эскроу (§ 3) и
публичный депозитный счёт (§ 4).

**Почему институт появился.** Пробел нашёл [обход кодекса](code_coverage.py), и
лежал он не за границей модели, а внутри объявленного института: модель
банковского счёта заявляет статьи 845–860 и останавливается ровно перед
специальными видами счетов той же главы 45. Пятнадцать статей — самый крупный
пробел обхода.

Практика его не показывала: суды на эти статьи в выгрузке не ссылались ни разу.
Обход идёт от закона, и отбор дел на него не влияет.

**Что объединяет три вида счетов.** Все три построены на одном: деньги на счёте
принадлежат не владельцу счёта. У номинального счёта права на них у бенефициара
(статья 860.1), на счёте эскроу депонированная сумма блокируется в пользу
бенефициара (статья 860.7), на публичном депозитном счёте деньги вносятся в
депозит нотариусу, приставу или суду (статья 860.11).

Отсюда общее последствие, ради которого эти счета и существуют: **деньги на них
недоступны кредиторам владельца счёта**. Арест, приостановление операций и
списание по его обязательствам не допускаются (статьи 860.5, 860.8 и 860.14).
Модель выводит эту защиту как один вывод для всех трёх видов и отдельно
отмечает её нарушение.

**Публичный депозитный счёт защищён шире.** По статье 860.14 не допускается
арест и списание не только по обязательствам владельца счёта, но и по
обязательствам бенефициара и депонента. У номинального счёта и счёта эскроу
такой широты нет: статья 860.5 прямо допускает арест по обязательствам
бенефициара номинального счёта.

**Чего модель не делает.** Она не определяет размер депонированной суммы, не
проверяет наступление оснований передачи по существу и не оценивает
достаточность собственных средств банка: требование статьи 860.11 к капиталу
она принимает как установленный факт, а не считает сама.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

SPECIAL_ACCOUNTS_EVIDENCE_SCHEMA_VERSION = "contracts.special-accounts-evidence.v0"
SPECIAL_ACCOUNTS_MAPPING_VERSION = "contracts-reviewed-special-accounts-to-facts-v0"
SPECIAL_ACCOUNTS_MODEL_VERSION = "contracts-special-accounts-articles-860-1-860-15-v0"


class SpecialAccountsEvidencePredicate(str, Enum):
    # Квалификация вида счёта (статья 860 ГК РФ).
    SPECIAL_ACCOUNT_ASSERTED = "special_account_asserted"
    NOMINAL_ACCOUNT = "nominal_account"
    ESCROW_ACCOUNT = "escrow_account"
    PUBLIC_DEPOSIT_ACCOUNT = "public_deposit_account"
    # Номинальный счёт (статьи 860.1–860.6).
    BENEFICIARY_IDENTIFIED_OR_DETERMINABLE = "beneficiary_identified_or_determinable"
    NOMINAL_FORM_SINGLE_SIGNED_DOCUMENT = "nominal_form_single_signed_document"
    BANK_CONTROL_DUTY_AGREED = "bank_control_duty_agreed"
    BANK_CONTROL_DUTY_NOT_PERFORMED = "bank_control_duty_not_performed"
    BENEFICIARY_DENIED_ACCOUNT_INFORMATION = "beneficiary_denied_account_information"
    NOMINAL_CHANGE_WITHOUT_BENEFICIARY_CONSENT = "nominal_change_without_beneficiary_consent"
    # Счёт эскроу (статьи 860.7–860.10).
    ESCROW_GROUNDS_DEFINED = "escrow_grounds_defined"
    ESCROW_GROUNDS_OCCURRED = "escrow_grounds_occurred"
    ESCROW_PAYMENT_TO_BENEFICIARY_DELAYED = "escrow_payment_to_beneficiary_delayed"
    DISPOSAL_ATTEMPTED_BEFORE_GROUNDS = "disposal_attempted_before_grounds"
    EXTRA_FUNDS_CREDITED_TO_ESCROW = "extra_funds_credited_to_escrow"
    ESCROW_TERM_EXPIRED_WITHOUT_GROUNDS = "escrow_term_expired_without_grounds"
    ESCROW_BALANCE_WITHHELD_FROM_DEPOSITOR = "escrow_balance_withheld_from_depositor"
    # Публичный депозитный счёт (статьи 860.11–860.15).
    HOLDER_AUTHORISED_BY_LAW = "holder_authorised_by_law"
    BANK_MEETS_CAPITAL_REQUIREMENT = "bank_meets_capital_requirement"
    OWN_FUNDS_CREDITED_TO_PUBLIC_ACCOUNT = "own_funds_credited_to_public_account"
    INTEREST_WITHHELD_FROM_BENEFICIARY = "interest_withheld_from_beneficiary"
    # Неприкосновенность средств (статьи 860.5, 860.8 и 860.14).
    SEIZURE_OR_DEBIT_FOR_HOLDER_DEBT = "seizure_or_debit_for_holder_debt"
    SEIZURE_PERMITTED_BY_LAW = "seizure_permitted_by_law"
    SEIZURE_FOR_BENEFICIARY_OR_DEPOSITOR_DEBT = "seizure_for_beneficiary_or_depositor_debt"


REQUIRED_SPECIAL_ACCOUNTS_PREDICATES = frozenset(SpecialAccountsEvidencePredicate)


class SpecialAccountsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: SpecialAccountsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedSpecialAccountsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = SPECIAL_ACCOUNTS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[SpecialAccountsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedSpecialAccountsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Special-accounts evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Special-accounts evidence contains duplicate legal source refs.")
        return self


class SpecialAccountsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    special_account_asserted: bool
    nominal_account: bool
    escrow_account: bool
    public_deposit_account: bool
    beneficiary_identified_or_determinable: bool
    nominal_form_single_signed_document: bool
    bank_control_duty_agreed: bool
    bank_control_duty_not_performed: bool
    beneficiary_denied_account_information: bool
    nominal_change_without_beneficiary_consent: bool
    escrow_grounds_defined: bool
    escrow_grounds_occurred: bool
    escrow_payment_to_beneficiary_delayed: bool
    disposal_attempted_before_grounds: bool
    extra_funds_credited_to_escrow: bool
    escrow_term_expired_without_grounds: bool
    escrow_balance_withheld_from_depositor: bool
    holder_authorised_by_law: bool
    bank_meets_capital_requirement: bool
    own_funds_credited_to_public_account: bool
    interest_withheld_from_beneficiary: bool
    seizure_or_debit_for_holder_debt: bool
    seizure_permitted_by_law: bool
    seizure_for_beneficiary_or_depositor_debt: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "SpecialAccountsFactSet":
        kinds = [self.nominal_account, self.escrow_account, self.public_deposit_account]
        if sum(kinds) > 1:
            raise ValueError(
                "Счёт не может быть одновременно номинальным, эскроу и публичным "
                "депозитным: § 2, 3 и 4 главы 45 ГК РФ описывают разные договоры, а не "
                "стороны одного."
            )
        if any(kinds) and not self.special_account_asserted:
            raise ValueError(
                "Вид специального счёта назван, а сам специальный счёт в деле не заявлен."
            )
        if self.escrow_grounds_occurred and not self.escrow_grounds_defined:
            raise ValueError(
                "Основания передачи депонированной суммы могут наступить только тогда, "
                "когда они определены договором счёта эскроу (статья 860.7 ГК РФ)."
            )
        if self.seizure_permitted_by_law and not self.seizure_or_debit_for_holder_debt:
            raise ValueError(
                "Допустимость ареста по закону имеет смысл лишь тогда, когда арест или "
                "списание по обязательствам владельца счёта состоялись."
            )
        return self


class SpecialAccountsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class SpecialAccountsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: SpecialAccountsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[SpecialAccountsFactProvenance] = Field(default_factory=list)


class SpecialAccountsConstraintSet(BaseModel):
    id: str
    model_version: str = SPECIAL_ACCOUNTS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class SpecialAccountsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    special_account_qualified: bool
    account_kind_undetermined: bool
    # Общее последствие всех трёх видов: деньги недоступны кредиторам владельца.
    funds_insulated_from_holder_creditors: bool
    insulation_breached: bool
    public_wider_insulation_breached: bool
    nominal_essential_term_missing: bool
    nominal_form_defect_makes_void: bool
    nominal_control_duty_breached: bool
    nominal_information_duty_breached: bool
    nominal_change_duty_breached: bool
    escrow_payment_duty_arisen: bool
    escrow_payment_duty_breached: bool
    escrow_disposal_restriction_breached: bool
    escrow_extra_funds_breached: bool
    escrow_return_duty_breached: bool
    public_holder_not_authorised: bool
    public_bank_requirement_breached: bool
    public_own_funds_prohibition_breached: bool
    public_interest_duty_breached: bool
    requires_human_special_accounts_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_special_accounts_evidence(
    evidence: ReviewedSpecialAccountsEvidence,
) -> SpecialAccountsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Special-accounts evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Special-accounts evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_SPECIAL_ACCOUNTS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed special-accounts evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_SPECIAL_ACCOUNTS_PREDICATES
    }
    return SpecialAccountsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=SPECIAL_ACCOUNTS_MAPPING_VERSION,
        facts=SpecialAccountsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            SpecialAccountsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_SPECIAL_ACCOUNTS_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_special_accounts_constraint_set(
    mapping: SpecialAccountsEvidenceMappingResult,
) -> SpecialAccountsConstraintSet:
    return SpecialAccountsConstraintSet(
        id=f"special-accounts-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "special_account_qualified == special_account_asserted AND (nominal_account OR escrow_account OR public_deposit_account)",
            "account_kind_undetermined == special_account_asserted AND NOT nominal_account AND NOT escrow_account AND NOT public_deposit_account",
            "funds_insulated_from_holder_creditors == special_account_qualified",
            "insulation_breached == funds_insulated_from_holder_creditors AND seizure_or_debit_for_holder_debt AND NOT seizure_permitted_by_law",
            "public_wider_insulation_breached == special_account_qualified AND public_deposit_account AND seizure_for_beneficiary_or_depositor_debt",
            "nominal_essential_term_missing == special_account_qualified AND nominal_account AND NOT beneficiary_identified_or_determinable",
            "nominal_form_defect_makes_void == special_account_qualified AND nominal_account AND NOT nominal_form_single_signed_document",
            "nominal_control_duty_breached == special_account_qualified AND nominal_account AND bank_control_duty_agreed AND bank_control_duty_not_performed",
            "nominal_information_duty_breached == special_account_qualified AND nominal_account AND beneficiary_denied_account_information",
            "nominal_change_duty_breached == special_account_qualified AND nominal_account AND nominal_change_without_beneficiary_consent",
            "escrow_payment_duty_arisen == special_account_qualified AND escrow_account AND escrow_grounds_defined AND escrow_grounds_occurred",
            "escrow_payment_duty_breached == escrow_payment_duty_arisen AND escrow_payment_to_beneficiary_delayed",
            "escrow_disposal_restriction_breached == special_account_qualified AND escrow_account AND disposal_attempted_before_grounds AND NOT escrow_grounds_occurred",
            "escrow_extra_funds_breached == special_account_qualified AND escrow_account AND extra_funds_credited_to_escrow",
            "escrow_return_duty_breached == special_account_qualified AND escrow_account AND escrow_term_expired_without_grounds AND escrow_balance_withheld_from_depositor",
            "public_holder_not_authorised == special_account_qualified AND public_deposit_account AND NOT holder_authorised_by_law",
            "public_bank_requirement_breached == special_account_qualified AND public_deposit_account AND NOT bank_meets_capital_requirement",
            "public_own_funds_prohibition_breached == special_account_qualified AND public_deposit_account AND own_funds_credited_to_public_account",
            "public_interest_duty_breached == special_account_qualified AND public_deposit_account AND interest_withheld_from_beneficiary",
            "requires_human_special_accounts_assessment == account_kind_undetermined OR insulation_breached OR public_wider_insulation_breached OR nominal_essential_term_missing OR nominal_form_defect_makes_void OR nominal_control_duty_breached OR nominal_information_duty_breached OR nominal_change_duty_breached OR escrow_payment_duty_breached OR escrow_disposal_restriction_breached OR escrow_extra_funds_breached OR escrow_return_duty_breached OR public_holder_not_authorised OR public_bank_requirement_breached OR public_own_funds_prohibition_breached OR public_interest_duty_breached",
        ],
    )


def evaluate_special_accounts_constraints(
    constraint_set: SpecialAccountsConstraintSet,
    facts: SpecialAccountsFactSet,
) -> SpecialAccountsEvaluation:
    variables = {field_name: Bool(field_name) for field_name in SpecialAccountsFactSet.model_fields}
    special_account_qualified = Bool("special_account_qualified")
    account_kind_undetermined = Bool("account_kind_undetermined")
    funds_insulated_from_holder_creditors = Bool("funds_insulated_from_holder_creditors")
    insulation_breached = Bool("insulation_breached")
    public_wider_insulation_breached = Bool("public_wider_insulation_breached")
    nominal_essential_term_missing = Bool("nominal_essential_term_missing")
    nominal_form_defect_makes_void = Bool("nominal_form_defect_makes_void")
    nominal_control_duty_breached = Bool("nominal_control_duty_breached")
    nominal_information_duty_breached = Bool("nominal_information_duty_breached")
    nominal_change_duty_breached = Bool("nominal_change_duty_breached")
    escrow_payment_duty_arisen = Bool("escrow_payment_duty_arisen")
    escrow_payment_duty_breached = Bool("escrow_payment_duty_breached")
    escrow_disposal_restriction_breached = Bool("escrow_disposal_restriction_breached")
    escrow_extra_funds_breached = Bool("escrow_extra_funds_breached")
    escrow_return_duty_breached = Bool("escrow_return_duty_breached")
    public_holder_not_authorised = Bool("public_holder_not_authorised")
    public_bank_requirement_breached = Bool("public_bank_requirement_breached")
    public_own_funds_prohibition_breached = Bool("public_own_funds_prohibition_breached")
    public_interest_duty_breached = Bool("public_interest_duty_breached")
    requires_human_special_accounts_assessment = Bool("requires_human_special_accounts_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        special_account_qualified
        == And(
            variables["special_account_asserted"],
            Or(
                variables["nominal_account"],
                variables["escrow_account"],
                variables["public_deposit_account"],
            ),
        )
    )
    solver.add(
        account_kind_undetermined
        == And(
            variables["special_account_asserted"],
            Not(variables["nominal_account"]),
            Not(variables["escrow_account"]),
            Not(variables["public_deposit_account"]),
        )
    )
    solver.add(funds_insulated_from_holder_creditors == special_account_qualified)
    solver.add(
        insulation_breached
        == And(
            funds_insulated_from_holder_creditors,
            variables["seizure_or_debit_for_holder_debt"],
            Not(variables["seizure_permitted_by_law"]),
        )
    )
    solver.add(
        public_wider_insulation_breached
        == And(
            special_account_qualified,
            variables["public_deposit_account"],
            variables["seizure_for_beneficiary_or_depositor_debt"],
        )
    )
    solver.add(
        nominal_essential_term_missing
        == And(
            special_account_qualified,
            variables["nominal_account"],
            Not(variables["beneficiary_identified_or_determinable"]),
        )
    )
    solver.add(
        nominal_form_defect_makes_void
        == And(
            special_account_qualified,
            variables["nominal_account"],
            Not(variables["nominal_form_single_signed_document"]),
        )
    )
    solver.add(
        nominal_control_duty_breached
        == And(
            special_account_qualified,
            variables["nominal_account"],
            variables["bank_control_duty_agreed"],
            variables["bank_control_duty_not_performed"],
        )
    )
    solver.add(
        nominal_information_duty_breached
        == And(
            special_account_qualified,
            variables["nominal_account"],
            variables["beneficiary_denied_account_information"],
        )
    )
    solver.add(
        nominal_change_duty_breached
        == And(
            special_account_qualified,
            variables["nominal_account"],
            variables["nominal_change_without_beneficiary_consent"],
        )
    )
    solver.add(
        escrow_payment_duty_arisen
        == And(
            special_account_qualified,
            variables["escrow_account"],
            variables["escrow_grounds_defined"],
            variables["escrow_grounds_occurred"],
        )
    )
    solver.add(
        escrow_payment_duty_breached
        == And(
            escrow_payment_duty_arisen,
            variables["escrow_payment_to_beneficiary_delayed"],
        )
    )
    solver.add(
        escrow_disposal_restriction_breached
        == And(
            special_account_qualified,
            variables["escrow_account"],
            variables["disposal_attempted_before_grounds"],
            Not(variables["escrow_grounds_occurred"]),
        )
    )
    solver.add(
        escrow_extra_funds_breached
        == And(
            special_account_qualified,
            variables["escrow_account"],
            variables["extra_funds_credited_to_escrow"],
        )
    )
    solver.add(
        escrow_return_duty_breached
        == And(
            special_account_qualified,
            variables["escrow_account"],
            variables["escrow_term_expired_without_grounds"],
            variables["escrow_balance_withheld_from_depositor"],
        )
    )
    solver.add(
        public_holder_not_authorised
        == And(
            special_account_qualified,
            variables["public_deposit_account"],
            Not(variables["holder_authorised_by_law"]),
        )
    )
    solver.add(
        public_bank_requirement_breached
        == And(
            special_account_qualified,
            variables["public_deposit_account"],
            Not(variables["bank_meets_capital_requirement"]),
        )
    )
    solver.add(
        public_own_funds_prohibition_breached
        == And(
            special_account_qualified,
            variables["public_deposit_account"],
            variables["own_funds_credited_to_public_account"],
        )
    )
    solver.add(
        public_interest_duty_breached
        == And(
            special_account_qualified,
            variables["public_deposit_account"],
            variables["interest_withheld_from_beneficiary"],
        )
    )
    solver.add(
        requires_human_special_accounts_assessment
        == Or(
            account_kind_undetermined,
            insulation_breached,
            public_wider_insulation_breached,
            nominal_essential_term_missing,
            nominal_form_defect_makes_void,
            nominal_control_duty_breached,
            nominal_information_duty_breached,
            nominal_change_duty_breached,
            escrow_payment_duty_breached,
            escrow_disposal_restriction_breached,
            escrow_extra_funds_breached,
            escrow_return_duty_breached,
            public_holder_not_authorised,
            public_bank_requirement_breached,
            public_own_funds_prohibition_breached,
            public_interest_duty_breached,
        )
    )

    if solver.check() != sat:
        return SpecialAccountsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            special_account_qualified=False,
            account_kind_undetermined=False,
            funds_insulated_from_holder_creditors=False,
            insulation_breached=False,
            public_wider_insulation_breached=False,
            nominal_essential_term_missing=False,
            nominal_form_defect_makes_void=False,
            nominal_control_duty_breached=False,
            nominal_information_duty_breached=False,
            nominal_change_duty_breached=False,
            escrow_payment_duty_arisen=False,
            escrow_payment_duty_breached=False,
            escrow_disposal_restriction_breached=False,
            escrow_extra_funds_breached=False,
            escrow_return_duty_breached=False,
            public_holder_not_authorised=False,
            public_bank_requirement_breached=False,
            public_own_funds_prohibition_breached=False,
            public_interest_duty_breached=False,
            requires_human_special_accounts_assessment=True,
            reasons_ru=["Набор фактов о специальном банковском счёте противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru: list[str] = []
    if truth(special_account_qualified):
        if truth(variables["nominal_account"]):
            reasons_ru.append(
                "Счёт квалифицирован как номинальный: он открыт владельцу счёта для "
                "совершения операций с деньгами, права на которые принадлежат другому лицу "
                "— бенефициару (пункт 1 статьи 860.1 ГК РФ)."
            )
        elif truth(variables["escrow_account"]):
            reasons_ru.append(
                "Счёт квалифицирован как счёт эскроу: банк блокирует полученную от "
                "депонента сумму и передаёт её бенефициару при наступлении оснований, "
                "предусмотренных договором (пункт 1 статьи 860.7 ГК РФ)."
            )
        else:
            reasons_ru.append(
                "Счёт квалифицирован как публичный депозитный: он открыт владельцу для "
                "депонирования денег, вносимых в депозит нотариуса, службы судебных "
                "приставов или суда (пункт 1 статьи 860.11 ГК РФ)."
            )
    elif truth(account_kind_undetermined):
        reasons_ru.append(
            "Специальный счёт в деле заявлен, но его вид не установлен. Номинальный счёт, "
            "счёт эскроу и публичный депозитный счёт — разные договоры § 2, 3 и 4 главы 45 "
            "ГК РФ с разными последствиями; без вида счёта модель их не выводит."
        )
    else:
        reasons_ru.append(
            "Специальный вид банковского счёта в деле не заявлен: спор разрешается по "
            "общим правилам о банковском счёте (статьи 845–860 ГК РФ)."
        )
    if truth(funds_insulated_from_holder_creditors):
        reasons_ru.append(
            "Деньги на счёте недоступны кредиторам владельца счёта: арест, "
            "приостановление операций и списание по его собственным обязательствам не "
            "допускаются (статьи 860.5, 860.8 и 860.14 ГК РФ). Это общее последствие всех "
            "трёх видов специальных счетов — деньги на них владельцу счёта не принадлежат."
        )
    if truth(insulation_breached):
        reasons_ru.append(
            "Защита нарушена: по обязательствам владельца счёта произведён арест или "
            "списание, а случая, когда закон это допускает, в деле не установлено."
        )
    if truth(public_wider_insulation_breached):
        reasons_ru.append(
            "Нарушена широкая защита публичного депозитного счёта: по статье 860.14 ГК РФ "
            "арест и списание не допускаются и по обязательствам бенефициара и депонента, "
            "а не только владельца счёта. У номинального счёта такой широты нет — статья "
            "860.5 ГК РФ прямо допускает арест по обязательствам бенефициара."
        )
    if truth(nominal_essential_term_missing):
        reasons_ru.append(
            "В договоре номинального счёта не указан бенефициар и не определён порядок "
            "получения сведений о нём — существенное условие отсутствует (пункт 1 статьи "
            "860.2 ГК РФ)."
        )
    if truth(nominal_form_defect_makes_void):
        reasons_ru.append(
            "Договор номинального счёта заключён не в форме единого документа, "
            "подписанного сторонами; несоблюдение этой формы влечёт ничтожность договора "
            "(пункты 1 и 2 статьи 860.2 ГК РФ)."
        )
    if truth(nominal_control_duty_breached):
        reasons_ru.append(
            "Банк не исполнил принятую на себя договором обязанность контролировать "
            "распоряжение деньгами в интересах бенефициара (статья 860.4 ГК РФ)."
        )
    if truth(nominal_information_duty_breached):
        reasons_ru.append(
            "Бенефициару отказано в сведениях, составляющих банковскую тайну "
            "номинального счёта, хотя он вправе их требовать (статья 860.3 ГК РФ)."
        )
    if truth(nominal_change_duty_breached):
        reasons_ru.append(
            "Договор номинального счёта с участием бенефициара изменён или расторгнут без "
            "его согласия (пункт 1 статьи 860.6 ГК РФ)."
        )
    if truth(escrow_payment_duty_arisen):
        reasons_ru.append(
            "Основания передачи депонированной суммы наступили, поэтому у банка возникла "
            "обязанность передать её бенефициару (пункт 1 статьи 860.7, статья 860.8 ГК РФ)."
        )
    if truth(escrow_payment_duty_breached):
        reasons_ru.append(
            "Обязанность передать депонированную сумму бенефициару нарушена просрочкой."
        )
    if truth(escrow_disposal_restriction_breached):
        reasons_ru.append(
            "Нарушен запрет распоряжения депонированной суммой: до наступления оснований "
            "передачи ни депонент, ни бенефициар распоряжаться деньгами на счёте эскроу не "
            "вправе (пункт 1 статьи 860.8 ГК РФ)."
        )
    if truth(escrow_extra_funds_breached):
        reasons_ru.append(
            "На счёт эскроу зачислены иные деньги помимо депонируемой суммы, что законом "
            "не допускается (пункт 3 статьи 860.8 ГК РФ)."
        )
    if truth(escrow_return_duty_breached):
        reasons_ru.append(
            "Срок действия договора счёта эскроу истёк без наступления оснований передачи, "
            "но остаток не возвращён депоненту (пункт 1 статьи 860.10 ГК РФ)."
        )
    if truth(public_holder_not_authorised):
        reasons_ru.append(
            "Владелец публичного депозитного счёта не относится к лицам, которым закон "
            "разрешает его открывать, — нотариусу, службе судебных приставов, суду или "
            "иному уполномоченному органу (пункт 1 статьи 860.11 ГК РФ)."
        )
    if truth(public_bank_requirement_breached):
        reasons_ru.append(
            "Публичный депозитный счёт открыт в банке, не отвечающем требованию к размеру "
            "собственных средств (пункт 1 статьи 860.11 ГК РФ). Достаточность капитала "
            "модель принимает как установленный факт, а не считает сама."
        )
    if truth(public_own_funds_prohibition_breached):
        reasons_ru.append(
            "На публичный депозитный счёт зачислены собственные деньги владельца счёта, "
            "что прямо запрещено (пункт 3 статьи 860.11 ГК РФ)."
        )
    if truth(public_interest_duty_breached):
        reasons_ru.append(
            "Бенефициару не выплачены проценты, начисленные на депонированную сумму на "
            "публичном депозитном счёте (статья 860.13 ГК РФ)."
        )
    return SpecialAccountsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        special_account_qualified=truth(special_account_qualified),
        account_kind_undetermined=truth(account_kind_undetermined),
        funds_insulated_from_holder_creditors=truth(funds_insulated_from_holder_creditors),
        insulation_breached=truth(insulation_breached),
        public_wider_insulation_breached=truth(public_wider_insulation_breached),
        nominal_essential_term_missing=truth(nominal_essential_term_missing),
        nominal_form_defect_makes_void=truth(nominal_form_defect_makes_void),
        nominal_control_duty_breached=truth(nominal_control_duty_breached),
        nominal_information_duty_breached=truth(nominal_information_duty_breached),
        nominal_change_duty_breached=truth(nominal_change_duty_breached),
        escrow_payment_duty_arisen=truth(escrow_payment_duty_arisen),
        escrow_payment_duty_breached=truth(escrow_payment_duty_breached),
        escrow_disposal_restriction_breached=truth(escrow_disposal_restriction_breached),
        escrow_extra_funds_breached=truth(escrow_extra_funds_breached),
        escrow_return_duty_breached=truth(escrow_return_duty_breached),
        public_holder_not_authorised=truth(public_holder_not_authorised),
        public_bank_requirement_breached=truth(public_bank_requirement_breached),
        public_own_funds_prohibition_breached=truth(public_own_funds_prohibition_breached),
        public_interest_duty_breached=truth(public_interest_duty_breached),
        requires_human_special_accounts_assessment=truth(
            requires_human_special_accounts_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Размер депонированной суммы модель не определяет: она отвечает о режиме "
            "счёта, а не о расчёте задолженности.",
            "Наступление оснований передачи депонированной суммы по существу проверяет "
            "человек: модель принимает его как установленный факт из доказательств.",
            "Достаточность собственных средств банка модель не считает — требование "
            "статьи 860.11 ГК РФ она принимает как проверенный факт.",
            "Модель отвечает об одном специальном счёте: контракт данных даёт один блок "
            "доказательств на институт.",
        ],
    )
