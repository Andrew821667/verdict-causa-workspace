"""Формальная модель условного депонирования (эскроу).

Статьи 926.1–926.8 ГК РФ, глава 47.1 целиком.

**Почему институт появился.** Пробел нашёл [обход кодекса](code_coverage.py):
глава вставлена в кодекс между хранением (глава 47) и страхованием (глава 48),
и разбор кодекса по порядку глав её перешагнул. Восемь статей, не заявленных
никем — не изнутри соседнего института, как было со специальными видами
банковских счетов, а полностью, с нуля.

Практика её не показывала: суды на эти статьи в выгрузке кассационных дел не
сослались ни разу. Обход идёт от закона, и отбор дел на него не влияет.

**Чем этот институт отличается от счёта эскроу (статьи 860.7–860.10).** Счёт
эскроу — специальный банковский счёт: эскроу-агентом там всегда банк, а
депонируется всегда безналичная сумма. Договор эскроу этой главы шире: агентом
может быть любое лицо — нотариус, любая организация, гражданин, — а
депонировать можно не только деньги, но и вещи, и бездокументарные ценные
бумаги. Статья 926.6 прямо указывает на стык двух институтов: если
эскроу-агент не банк, депонируемые безналичные деньги идут через его
номинальный счёт (статьи 860.1–860.6), а не через счёт эскроу.

**Три стороны, а не две.** Договор эскроу заключается депонентом, бенефициаром
и эскроу-агентом одновременно (статья 926.1). Агент не сторона основного
обязательства между депонентом и бенефициаром — он посредник, обеспечивающий
сохранность имущества и его передачу при наступлении оговорённых оснований.

**Форма и срок.** Договор эскроу подлежит нотариальному удостоверению, кроме
случая, когда депонируются исключительно безналичные деньги и (или)
бездокументарные ценные бумаги: если в состав депонируемого имущества входят
вещи, нотариальная форма обязательна независимо от того, что депонировано
вместе с ними (статья 926.1). Срок депонирования не может превышать пять лет;
договор, заключённый на больший срок или без указания срока, считается
заключённым на пять лет — это не ничтожность и не пробел воли сторон, а прямая
подстановка кодекса (статья 926.1).

**Что модель не делает.** Она не проверяет наступление оснований передачи по
существу — это оценивает эскроу-агент по условиям договора, а суд и эксперт по
доказательствам. Она не определяет размер и состав депонированного имущества.
Она отвечает об одном договоре эскроу — контракт данных даёт один блок
доказательств на институт.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

ESCROW_DEPOSIT_EVIDENCE_SCHEMA_VERSION = "contracts.escrow-deposit-evidence.v0"
ESCROW_DEPOSIT_MAPPING_VERSION = "contracts-reviewed-escrow-deposit-to-facts-v0"
ESCROW_DEPOSIT_MODEL_VERSION = "contracts-escrow-deposit-articles-926-1-926-8-v0"


class EscrowDepositEvidencePredicate(str, Enum):
    # Квалификация и предмет депонирования (статья 926.1 ГК РФ).
    ESCROW_DEPOSIT_ASSERTED = "escrow_deposit_asserted"
    DEPOSITED_THINGS = "deposited_things"
    DEPOSITED_CASHLESS_MONEY = "deposited_cashless_money"
    DEPOSITED_UNCERTIFICATED_SECURITIES = "deposited_uncertificated_securities"
    DEPOSIT_TERM_MISSING_OR_EXCESSIVE = "deposit_term_missing_or_excessive"
    NOTARIZATION_PERFORMED = "notarization_performed"
    ESCROW_DEPOSIT_GROUNDS_DEFINED = "escrow_deposit_grounds_defined"
    GROUNDS_FOR_TRANSFER_OCCURRED = "grounds_for_transfer_occurred"
    # Вознаграждение эскроу-агента (статья 926.2 ГК РФ).
    REMUNERATION_WAIVED_BY_CONTRACT = "remuneration_waived_by_contract"
    REMUNERATION_LIABILITY_SEVERAL_BY_CONTRACT = "remuneration_liability_several_by_contract"
    AGENT_SETOFF_PERMITTED_BY_CONTRACT = "agent_setoff_permitted_by_contract"
    AGENT_WITHHELD_OR_SETOFF_DEPOSITED_PROPERTY = "agent_withheld_or_setoff_deposited_property"
    # Проверка оснований для передачи (статья 926.3 ГК РФ).
    DOCUMENT_CHECK_REQUIRED_BY_CONTRACT = "document_check_required_by_contract"
    DOCUMENTS_FACIALLY_DOUBTFUL = "documents_facially_doubtful"
    TRANSFER_DESPITE_DOUBT_PERMITTED_BY_CONTRACT = "transfer_despite_doubt_permitted_by_contract"
    AGENT_TRANSFERRED_PROPERTY_DESPITE_DOUBT = "agent_transferred_property_despite_doubt"
    SUBSTANTIVE_CHECK_AGREED_BY_CONTRACT = "substantive_check_agreed_by_contract"
    AGENT_TRANSFERRED_WITHOUT_VERIFYING_GROUNDS = "agent_transferred_without_verifying_grounds"
    # Обособление и распоряжение имуществом (статья 926.4 ГК РФ).
    DEPOSITED_PROPERTY_COMMINGLED_WITH_AGENTS_OWN = (
        "deposited_property_commingled_with_agents_own"
    )
    USE_OR_DISPOSAL_PERMITTED_BY_CONTRACT_OR_NATURE = (
        "use_or_disposal_permitted_by_contract_or_nature"
    )
    AGENT_USED_OR_DISPOSED_DEPOSITED_PROPERTY = "agent_used_or_disposed_deposited_property"
    # Депонирование вещей (статья 926.5 ГК РФ).
    THING_LOST_DAMAGED_OR_SHORT = "thing_lost_damaged_or_short"
    AGENT_PROVED_FORCE_MAJEURE = "agent_proved_force_majeure"
    AGENT_PROVED_INHERENT_DEFECT_UNKNOWN_TO_AGENT = (
        "agent_proved_inherent_defect_unknown_to_agent"
    )
    AGENT_PROVED_DEPOSITOR_FAULT = "agent_proved_depositor_fault"
    # Депонирование ценных бумаг и безналичных денег (статья 926.6 ГК РФ).
    SECURITIES_EXERCISE_PERMITTED_BY_CONTRACT = "securities_exercise_permitted_by_contract"
    AGENT_DISPOSED_OR_EXERCISED_RIGHTS_ON_SECURITIES = (
        "agent_disposed_or_exercised_rights_on_securities"
    )
    ESCROW_AGENT_IS_BANK = "escrow_agent_is_bank"
    # Обращение взыскания (статья 926.7 ГК РФ).
    SEIZURE_OR_DEBIT_FOR_AGENT_OR_DEPOSITOR_DEBT = "seizure_or_debit_for_agent_or_depositor_debt"
    SEIZURE_FOR_BENEFICIARY_DEBT = "seizure_for_beneficiary_debt"
    # Прекращение договора эскроу (статья 926.8 ГК РФ).
    AGENT_PERSONAL_TERMINATION_GROUND = "agent_personal_termination_ground"
    DEPOSIT_TERM_EXPIRED = "deposit_term_expired"
    CONTRACT_TRANSFERRED_UNDER_ARTICLE_392_3 = "contract_transferred_under_article_392_3"


REQUIRED_ESCROW_DEPOSIT_PREDICATES = frozenset(EscrowDepositEvidencePredicate)


class EscrowDepositEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: EscrowDepositEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(default_factory=tuple)


class ReviewedEscrowDepositEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = ESCROW_DEPOSIT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[EscrowDepositEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(default_factory=tuple)
    review_status: BootstrapReviewStatus
    reviewer_id: str | None = None


class EscrowDepositFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    escrow_deposit_asserted: bool
    deposited_things: bool
    deposited_cashless_money: bool
    deposited_uncertificated_securities: bool
    deposit_term_missing_or_excessive: bool
    notarization_performed: bool
    escrow_deposit_grounds_defined: bool
    grounds_for_transfer_occurred: bool
    remuneration_waived_by_contract: bool
    remuneration_liability_several_by_contract: bool
    agent_setoff_permitted_by_contract: bool
    agent_withheld_or_setoff_deposited_property: bool
    document_check_required_by_contract: bool
    documents_facially_doubtful: bool
    transfer_despite_doubt_permitted_by_contract: bool
    agent_transferred_property_despite_doubt: bool
    substantive_check_agreed_by_contract: bool
    agent_transferred_without_verifying_grounds: bool
    deposited_property_commingled_with_agents_own: bool
    use_or_disposal_permitted_by_contract_or_nature: bool
    agent_used_or_disposed_deposited_property: bool
    thing_lost_damaged_or_short: bool
    agent_proved_force_majeure: bool
    agent_proved_inherent_defect_unknown_to_agent: bool
    agent_proved_depositor_fault: bool
    securities_exercise_permitted_by_contract: bool
    agent_disposed_or_exercised_rights_on_securities: bool
    escrow_agent_is_bank: bool
    seizure_or_debit_for_agent_or_depositor_debt: bool
    seizure_for_beneficiary_debt: bool
    agent_personal_termination_ground: bool
    deposit_term_expired: bool
    contract_transferred_under_article_392_3: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "EscrowDepositFactSet":
        if any(
            [
                self.deposited_things,
                self.deposited_cashless_money,
                self.deposited_uncertificated_securities,
            ]
        ) and not self.escrow_deposit_asserted:
            raise ValueError(
                "Предмет депонирования назван, а сам договор эскроу в деле не заявлен."
            )
        if self.grounds_for_transfer_occurred and not self.escrow_deposit_grounds_defined:
            raise ValueError(
                "Основания передачи имущества бенефициару могут наступить только тогда, "
                "когда они определены договором эскроу (статья 926.1 ГК РФ)."
            )
        if self.agent_transferred_property_despite_doubt and not (
            self.document_check_required_by_contract and self.documents_facially_doubtful
        ):
            raise ValueError(
                "Передача имущества вопреки сомнению в документах имеет смысл лишь тогда, "
                "когда договор требовал их проверки и сомнение по внешним признакам "
                "действительно возникло (статья 926.3 ГК РФ)."
            )
        if (
            self.agent_transferred_without_verifying_grounds
            and not self.substantive_check_agreed_by_contract
        ):
            raise ValueError(
                "Упрёк в непроверенном наступлении оснований по существу имеет смысл лишь "
                "тогда, когда договор возложил на агента такую обязанность (статья 926.3 "
                "ГК РФ)."
            )
        if self.thing_lost_damaged_or_short and not self.deposited_things:
            raise ValueError(
                "Утрата, недостача или повреждение депонированного имеют смысл лишь для "
                "депонированных вещей (статья 926.5 ГК РФ)."
            )
        for defence in (
            self.agent_proved_force_majeure,
            self.agent_proved_inherent_defect_unknown_to_agent,
            self.agent_proved_depositor_fault,
        ):
            if defence and not self.thing_lost_damaged_or_short:
                raise ValueError(
                    "Основание освобождения агента от ответственности имеет смысл лишь "
                    "тогда, когда утрата, недостача или повреждение вещи заявлены (статья "
                    "926.5 ГК РФ)."
                )
        if (
            self.agent_disposed_or_exercised_rights_on_securities
            and not self.deposited_uncertificated_securities
        ):
            raise ValueError(
                "Распоряжение ценными бумагами или осуществление прав по ним имеет смысл "
                "лишь для депонированных бездокументарных ценных бумаг (статья 926.6 ГК РФ)."
            )
        return self


class EscrowDepositFactProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fact_name: str
    assertion_id: str
    source_refs: tuple[str, ...] = Field(default_factory=tuple)


class EscrowDepositEvidenceMappingResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: EscrowDepositFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[EscrowDepositFactProvenance] = Field(default_factory=list)


class EscrowDepositConstraintSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class EscrowDepositEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    escrow_deposit_qualified: bool
    escrow_deposit_kind_undetermined: bool
    deposit_term_deemed_five_years: bool
    notarization_required: bool
    notarization_missing_makes_void: bool
    remuneration_owed: bool
    remuneration_liability_joint_and_several: bool
    agent_setoff_breached: bool
    document_check_breach: bool
    substantive_check_breach: bool
    segregation_breach: bool
    use_or_disposal_breach: bool
    depositor_retains_title: bool
    title_passed_to_beneficiary: bool
    agent_liability_for_things_breached: bool
    securities_disposal_breach: bool
    cashless_money_requires_nominal_account: bool
    # Общее последствие: имущество недоступно кредиторам агента и депонента.
    deposited_property_insulated_from_agent_or_depositor_creditors: bool
    insulation_breach: bool
    beneficiary_creditor_may_reach_claim_right: bool
    termination_ground_present: bool
    contract_transferred_to_new_agent: bool
    return_to_depositor_due: bool
    transfer_to_beneficiary_due_on_termination: bool
    requires_human_escrow_deposit_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_escrow_deposit_evidence(
    evidence: ReviewedEscrowDepositEvidence,
) -> EscrowDepositEvidenceMappingResult:
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_ESCROW_DEPOSIT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed escrow-deposit evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_ESCROW_DEPOSIT_PREDICATES
    }
    return EscrowDepositEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=ESCROW_DEPOSIT_MAPPING_VERSION,
        facts=EscrowDepositFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            EscrowDepositFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_ESCROW_DEPOSIT_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_escrow_deposit_constraint_set(
    mapping: EscrowDepositEvidenceMappingResult,
) -> EscrowDepositConstraintSet:
    return EscrowDepositConstraintSet(
        id=f"escrow-deposit-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "escrow_deposit_qualified == escrow_deposit_asserted AND (deposited_things OR deposited_cashless_money OR deposited_uncertificated_securities)",
            "escrow_deposit_kind_undetermined == escrow_deposit_asserted AND NOT deposited_things AND NOT deposited_cashless_money AND NOT deposited_uncertificated_securities",
            "deposit_term_deemed_five_years == escrow_deposit_qualified AND deposit_term_missing_or_excessive",
            "notarization_required == escrow_deposit_qualified AND deposited_things",
            "notarization_missing_makes_void == notarization_required AND NOT notarization_performed",
            "remuneration_owed == escrow_deposit_qualified AND NOT remuneration_waived_by_contract",
            "remuneration_liability_joint_and_several == escrow_deposit_qualified AND NOT remuneration_liability_several_by_contract",
            "agent_setoff_breached == escrow_deposit_qualified AND NOT agent_setoff_permitted_by_contract AND agent_withheld_or_setoff_deposited_property",
            "document_check_breach == escrow_deposit_qualified AND document_check_required_by_contract AND documents_facially_doubtful AND agent_transferred_property_despite_doubt AND NOT transfer_despite_doubt_permitted_by_contract",
            "substantive_check_breach == escrow_deposit_qualified AND substantive_check_agreed_by_contract AND agent_transferred_without_verifying_grounds",
            "segregation_breach == escrow_deposit_qualified AND deposited_property_commingled_with_agents_own",
            "use_or_disposal_breach == escrow_deposit_qualified AND NOT use_or_disposal_permitted_by_contract_or_nature AND agent_used_or_disposed_deposited_property",
            "depositor_retains_title == escrow_deposit_qualified AND deposited_things AND NOT grounds_for_transfer_occurred",
            "title_passed_to_beneficiary == escrow_deposit_qualified AND deposited_things AND grounds_for_transfer_occurred",
            "agent_liability_for_things_breached == escrow_deposit_qualified AND deposited_things AND thing_lost_damaged_or_short AND NOT agent_proved_force_majeure AND NOT agent_proved_inherent_defect_unknown_to_agent AND NOT agent_proved_depositor_fault",
            "securities_disposal_breach == escrow_deposit_qualified AND deposited_uncertificated_securities AND NOT securities_exercise_permitted_by_contract AND agent_disposed_or_exercised_rights_on_securities",
            "cashless_money_requires_nominal_account == escrow_deposit_qualified AND deposited_cashless_money AND NOT escrow_agent_is_bank",
            "deposited_property_insulated_from_agent_or_depositor_creditors == escrow_deposit_qualified",
            "insulation_breach == deposited_property_insulated_from_agent_or_depositor_creditors AND seizure_or_debit_for_agent_or_depositor_debt",
            "beneficiary_creditor_may_reach_claim_right == escrow_deposit_qualified AND seizure_for_beneficiary_debt",
            "termination_ground_present == escrow_deposit_qualified AND (agent_personal_termination_ground OR deposit_term_expired)",
            "contract_transferred_to_new_agent == termination_ground_present AND contract_transferred_under_article_392_3",
            "return_to_depositor_due == termination_ground_present AND NOT contract_transferred_to_new_agent AND NOT grounds_for_transfer_occurred",
            "transfer_to_beneficiary_due_on_termination == termination_ground_present AND NOT contract_transferred_to_new_agent AND grounds_for_transfer_occurred",
            "requires_human_escrow_deposit_assessment == escrow_deposit_kind_undetermined OR notarization_missing_makes_void OR agent_setoff_breached OR document_check_breach OR substantive_check_breach OR segregation_breach OR use_or_disposal_breach OR agent_liability_for_things_breached OR securities_disposal_breach OR insulation_breach OR cashless_money_requires_nominal_account OR termination_ground_present",
        ],
    )


def evaluate_escrow_deposit_constraints(
    constraint_set: EscrowDepositConstraintSet,
    facts: EscrowDepositFactSet,
) -> EscrowDepositEvaluation:
    variables = {field_name: Bool(field_name) for field_name in EscrowDepositFactSet.model_fields}
    escrow_deposit_qualified = Bool("escrow_deposit_qualified")
    escrow_deposit_kind_undetermined = Bool("escrow_deposit_kind_undetermined")
    deposit_term_deemed_five_years = Bool("deposit_term_deemed_five_years")
    notarization_required = Bool("notarization_required")
    notarization_missing_makes_void = Bool("notarization_missing_makes_void")
    remuneration_owed = Bool("remuneration_owed")
    remuneration_liability_joint_and_several = Bool("remuneration_liability_joint_and_several")
    agent_setoff_breached = Bool("agent_setoff_breached")
    document_check_breach = Bool("document_check_breach")
    substantive_check_breach = Bool("substantive_check_breach")
    segregation_breach = Bool("segregation_breach")
    use_or_disposal_breach = Bool("use_or_disposal_breach")
    depositor_retains_title = Bool("depositor_retains_title")
    title_passed_to_beneficiary = Bool("title_passed_to_beneficiary")
    agent_liability_for_things_breached = Bool("agent_liability_for_things_breached")
    securities_disposal_breach = Bool("securities_disposal_breach")
    cashless_money_requires_nominal_account = Bool("cashless_money_requires_nominal_account")
    deposited_property_insulated_from_agent_or_depositor_creditors = Bool(
        "deposited_property_insulated_from_agent_or_depositor_creditors"
    )
    insulation_breach = Bool("insulation_breach")
    beneficiary_creditor_may_reach_claim_right = Bool(
        "beneficiary_creditor_may_reach_claim_right"
    )
    termination_ground_present = Bool("termination_ground_present")
    contract_transferred_to_new_agent = Bool("contract_transferred_to_new_agent")
    return_to_depositor_due = Bool("return_to_depositor_due")
    transfer_to_beneficiary_due_on_termination = Bool(
        "transfer_to_beneficiary_due_on_termination"
    )
    requires_human_escrow_deposit_assessment = Bool("requires_human_escrow_deposit_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        escrow_deposit_qualified
        == And(
            variables["escrow_deposit_asserted"],
            Or(
                variables["deposited_things"],
                variables["deposited_cashless_money"],
                variables["deposited_uncertificated_securities"],
            ),
        )
    )
    solver.add(
        escrow_deposit_kind_undetermined
        == And(
            variables["escrow_deposit_asserted"],
            Not(variables["deposited_things"]),
            Not(variables["deposited_cashless_money"]),
            Not(variables["deposited_uncertificated_securities"]),
        )
    )
    solver.add(
        deposit_term_deemed_five_years
        == And(escrow_deposit_qualified, variables["deposit_term_missing_or_excessive"])
    )
    solver.add(
        notarization_required == And(escrow_deposit_qualified, variables["deposited_things"])
    )
    solver.add(
        notarization_missing_makes_void
        == And(notarization_required, Not(variables["notarization_performed"]))
    )
    solver.add(
        remuneration_owed
        == And(escrow_deposit_qualified, Not(variables["remuneration_waived_by_contract"]))
    )
    solver.add(
        remuneration_liability_joint_and_several
        == And(
            escrow_deposit_qualified,
            Not(variables["remuneration_liability_several_by_contract"]),
        )
    )
    solver.add(
        agent_setoff_breached
        == And(
            escrow_deposit_qualified,
            Not(variables["agent_setoff_permitted_by_contract"]),
            variables["agent_withheld_or_setoff_deposited_property"],
        )
    )
    solver.add(
        document_check_breach
        == And(
            escrow_deposit_qualified,
            variables["document_check_required_by_contract"],
            variables["documents_facially_doubtful"],
            variables["agent_transferred_property_despite_doubt"],
            Not(variables["transfer_despite_doubt_permitted_by_contract"]),
        )
    )
    solver.add(
        substantive_check_breach
        == And(
            escrow_deposit_qualified,
            variables["substantive_check_agreed_by_contract"],
            variables["agent_transferred_without_verifying_grounds"],
        )
    )
    solver.add(
        segregation_breach
        == And(
            escrow_deposit_qualified, variables["deposited_property_commingled_with_agents_own"]
        )
    )
    solver.add(
        use_or_disposal_breach
        == And(
            escrow_deposit_qualified,
            Not(variables["use_or_disposal_permitted_by_contract_or_nature"]),
            variables["agent_used_or_disposed_deposited_property"],
        )
    )
    solver.add(
        depositor_retains_title
        == And(
            escrow_deposit_qualified,
            variables["deposited_things"],
            Not(variables["grounds_for_transfer_occurred"]),
        )
    )
    solver.add(
        title_passed_to_beneficiary
        == And(
            escrow_deposit_qualified,
            variables["deposited_things"],
            variables["grounds_for_transfer_occurred"],
        )
    )
    solver.add(
        agent_liability_for_things_breached
        == And(
            escrow_deposit_qualified,
            variables["deposited_things"],
            variables["thing_lost_damaged_or_short"],
            Not(variables["agent_proved_force_majeure"]),
            Not(variables["agent_proved_inherent_defect_unknown_to_agent"]),
            Not(variables["agent_proved_depositor_fault"]),
        )
    )
    solver.add(
        securities_disposal_breach
        == And(
            escrow_deposit_qualified,
            variables["deposited_uncertificated_securities"],
            Not(variables["securities_exercise_permitted_by_contract"]),
            variables["agent_disposed_or_exercised_rights_on_securities"],
        )
    )
    solver.add(
        cashless_money_requires_nominal_account
        == And(
            escrow_deposit_qualified,
            variables["deposited_cashless_money"],
            Not(variables["escrow_agent_is_bank"]),
        )
    )
    solver.add(
        deposited_property_insulated_from_agent_or_depositor_creditors
        == escrow_deposit_qualified
    )
    solver.add(
        insulation_breach
        == And(
            deposited_property_insulated_from_agent_or_depositor_creditors,
            variables["seizure_or_debit_for_agent_or_depositor_debt"],
        )
    )
    solver.add(
        beneficiary_creditor_may_reach_claim_right
        == And(escrow_deposit_qualified, variables["seizure_for_beneficiary_debt"])
    )
    solver.add(
        termination_ground_present
        == And(
            escrow_deposit_qualified,
            Or(
                variables["agent_personal_termination_ground"],
                variables["deposit_term_expired"],
            ),
        )
    )
    solver.add(
        contract_transferred_to_new_agent
        == And(
            termination_ground_present, variables["contract_transferred_under_article_392_3"]
        )
    )
    solver.add(
        return_to_depositor_due
        == And(
            termination_ground_present,
            Not(contract_transferred_to_new_agent),
            Not(variables["grounds_for_transfer_occurred"]),
        )
    )
    solver.add(
        transfer_to_beneficiary_due_on_termination
        == And(
            termination_ground_present,
            Not(contract_transferred_to_new_agent),
            variables["grounds_for_transfer_occurred"],
        )
    )
    solver.add(
        requires_human_escrow_deposit_assessment
        == Or(
            escrow_deposit_kind_undetermined,
            notarization_missing_makes_void,
            agent_setoff_breached,
            document_check_breach,
            substantive_check_breach,
            segregation_breach,
            use_or_disposal_breach,
            agent_liability_for_things_breached,
            securities_disposal_breach,
            insulation_breach,
            cashless_money_requires_nominal_account,
            termination_ground_present,
        )
    )

    if solver.check() != sat:
        return EscrowDepositEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            escrow_deposit_qualified=False,
            escrow_deposit_kind_undetermined=False,
            deposit_term_deemed_five_years=False,
            notarization_required=False,
            notarization_missing_makes_void=False,
            remuneration_owed=False,
            remuneration_liability_joint_and_several=False,
            agent_setoff_breached=False,
            document_check_breach=False,
            substantive_check_breach=False,
            segregation_breach=False,
            use_or_disposal_breach=False,
            depositor_retains_title=False,
            title_passed_to_beneficiary=False,
            agent_liability_for_things_breached=False,
            securities_disposal_breach=False,
            cashless_money_requires_nominal_account=False,
            deposited_property_insulated_from_agent_or_depositor_creditors=False,
            insulation_breach=False,
            beneficiary_creditor_may_reach_claim_right=False,
            termination_ground_present=False,
            contract_transferred_to_new_agent=False,
            return_to_depositor_due=False,
            transfer_to_beneficiary_due_on_termination=False,
            requires_human_escrow_deposit_assessment=True,
            reasons_ru=["Набор фактов о договоре условного депонирования противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru: list[str] = []
    if truth(escrow_deposit_qualified):
        kinds_ru = []
        if truth(variables["deposited_things"]):
            kinds_ru.append("вещи")
        if truth(variables["deposited_cashless_money"]):
            kinds_ru.append("безналичные деньги")
        if truth(variables["deposited_uncertificated_securities"]):
            kinds_ru.append("бездокументарные ценные бумаги")
        reasons_ru.append(
            "Договор эскроу квалифицирован: депонент передал эскроу-агенту имущество "
            "(" + ", ".join(kinds_ru) + ") для передачи бенефициару при наступлении "
            "предусмотренных договором оснований (пункт 1 статьи 926.1 ГК РФ)."
        )
    elif truth(escrow_deposit_kind_undetermined):
        reasons_ru.append(
            "Договор эскроу в деле заявлен, но предмет депонирования не установлен: "
            "вещи, безналичные деньги и бездокументарные ценные бумаги влекут разные "
            "правила (статьи 926.5 и 926.6 ГК РФ), и без предмета модель их не выводит."
        )
    else:
        reasons_ru.append("Договор условного депонирования в деле не заявлен.")
    if truth(deposit_term_deemed_five_years):
        reasons_ru.append(
            "Срок депонирования не указан либо превышает пять лет: закон подставляет "
            "вместо него срок пять лет, а не признаёт условие о сроке недействительным "
            "(пункт 4 статьи 926.1 ГК РФ)."
        )
    if truth(notarization_required):
        reasons_ru.append(
            "Требуется нотариальное удостоверение договора: в состав депонируемого "
            "имущества входят вещи, а исключение сделано только для депонирования "
            "исключительно безналичных денег и бездокументарных ценных бумаг (пункт 1 "
            "статьи 926.1 ГК РФ)."
        )
    if truth(notarization_missing_makes_void):
        reasons_ru.append(
            "Нотариальное удостоверение не выполнено там, где оно обязательно; "
            "несоблюдение нотариальной формы, когда закон её требует, влечёт "
            "ничтожность сделки (пункт 3 статьи 163 ГК РФ)."
        )
    if truth(remuneration_owed):
        reasons_ru.append(
            "Эскроу-агент вправе требовать вознаграждение за исполнение своих "
            "обязанностей — договор его не исключил (пункт 1 статьи 926.2 ГК РФ)."
        )
    if truth(remuneration_liability_joint_and_several):
        reasons_ru.append(
            "Обязанность депонента и бенефициара уплатить вознаграждение — солидарная: "
            "договор не установил иного (пункт 2 статьи 926.2 ГК РФ)."
        )
    if truth(agent_setoff_breached):
        reasons_ru.append(
            "Эскроу-агент удержал или зачёл депонированное имущество в счёт своего "
            "вознаграждения, хотя договор ему этого не позволял (пункт 3 статьи 926.2 "
            "ГК РФ)."
        )
    if truth(document_check_breach):
        reasons_ru.append(
            "Эскроу-агент передал имущество бенефициару, хотя предъявленные документы "
            "по внешним признакам вызывали разумные сомнения в достоверности, и "
            "договор не разрешал передачу в таком случае (пункт 1 статьи 926.3 ГК РФ)."
        )
    if truth(substantive_check_breach):
        reasons_ru.append(
            "Договор возложил на эскроу-агента обязанность проверить наступление "
            "оснований передачи по существу, но агент передал имущество, не проверив "
            "их (пункт 2 статьи 926.3 ГК РФ)."
        )
    if truth(segregation_breach):
        reasons_ru.append(
            "Депонированное имущество смешано с имуществом эскроу-агента; это нарушает "
            "обязанность обособленного учёта, хотя само по себе не прекращает "
            "обязательства агента перед депонентом и бенефициаром (пункты 1 и 2 статьи "
            "926.4 ГК РФ)."
        )
    if truth(use_or_disposal_breach):
        reasons_ru.append(
            "Эскроу-агент использовал депонированное имущество или распорядился им, "
            "хотя договор этого не допускал и существо обязательства этого не требовало "
            "(пункт 3 статьи 926.4 ГК РФ)."
        )
    if truth(depositor_retains_title):
        reasons_ru.append(
            "Право собственности на депонированные вещи сохраняется за депонентом: "
            "основания для их передачи бенефициару ещё не наступили (пункт 1 статьи "
            "926.5 ГК РФ)."
        )
    if truth(title_passed_to_beneficiary):
        reasons_ru.append(
            "Право собственности на депонированные вещи перешло к бенефициару с даты "
            "наступления оснований передачи (пункт 1 статьи 926.5 ГК РФ)."
        )
    if truth(agent_liability_for_things_breached):
        reasons_ru.append(
            "Эскроу-агент отвечает за утрату, недостачу или повреждение депонированных "
            "вещей: он не доказал непреодолимую силу, неизвестное ему свойство вещей "
            "или умысел либо грубую неосторожность депонента (пункт 2 статьи 926.5 "
            "ГК РФ)."
        )
    if truth(securities_disposal_breach):
        reasons_ru.append(
            "Эскроу-агент распорядился депонированными бездокументарными ценными "
            "бумагами или осуществил права по ним, хотя договор ему этого не разрешал "
            "(пункт 2 статьи 926.6 ГК РФ)."
        )
    if truth(cashless_money_requires_nominal_account):
        reasons_ru.append(
            "Эскроу-агент не банк, поэтому депонируемые безналичные деньги должны "
            "находиться на его номинальном счёте, а не на счёте эскроу (пункт 3 статьи "
            "926.6 ГК РФ). Режим этого номинального счёта отдельно проверяет институт "
            "специальных видов банковских счетов (статьи 860.1–860.6 ГК РФ)."
        )
    if truth(deposited_property_insulated_from_agent_or_depositor_creditors):
        reasons_ru.append(
            "Депонированное имущество недоступно кредиторам эскроу-агента и депонента: "
            "обращение взыскания, арест и обеспечительные меры по их долгам не "
            "допускаются (пункт 1 статьи 926.7 ГК РФ)."
        )
    if truth(insulation_breach):
        reasons_ru.append(
            "Защита нарушена: по долгу эскроу-агента или депонента на депонированное "
            "имущество обращено взыскание или наложен арест, что законом не допускается."
        )
    if truth(beneficiary_creditor_may_reach_claim_right):
        reasons_ru.append(
            "По долгу бенефициара взыскание может быть обращено — но не на само "
            "депонированное имущество, а на его право требования к эскроу-агенту о "
            "передаче этого имущества (пункт 2 статьи 926.7 ГК РФ)."
        )
    if truth(termination_ground_present):
        reasons_ru.append(
            "Договор эскроу прекращён: наступило одно из оснований статьи 926.8 ГК РФ "
            "— обстоятельство на стороне эскроу-агента или истечение срока "
            "депонирования."
        )
        if truth(contract_transferred_to_new_agent):
            reasons_ru.append(
                "Договор до наступления этого обстоятельства передан другому лицу в "
                "порядке статьи 392.3 ГК РФ, поэтому прекращения не происходит."
            )
        elif truth(return_to_depositor_due):
            reasons_ru.append(
                "Депонированное имущество подлежит возврату депоненту: основания для "
                "его передачи бенефициару не наступили (пункт 2 статьи 926.8 ГК РФ)."
            )
        elif truth(transfer_to_beneficiary_due_on_termination):
            reasons_ru.append(
                "Депонированное имущество подлежит передаче бенефициару: основания для "
                "передачи уже наступили к моменту прекращения договора (пункт 2 статьи "
                "926.8 ГК РФ)."
            )
    return EscrowDepositEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        escrow_deposit_qualified=truth(escrow_deposit_qualified),
        escrow_deposit_kind_undetermined=truth(escrow_deposit_kind_undetermined),
        deposit_term_deemed_five_years=truth(deposit_term_deemed_five_years),
        notarization_required=truth(notarization_required),
        notarization_missing_makes_void=truth(notarization_missing_makes_void),
        remuneration_owed=truth(remuneration_owed),
        remuneration_liability_joint_and_several=truth(remuneration_liability_joint_and_several),
        agent_setoff_breached=truth(agent_setoff_breached),
        document_check_breach=truth(document_check_breach),
        substantive_check_breach=truth(substantive_check_breach),
        segregation_breach=truth(segregation_breach),
        use_or_disposal_breach=truth(use_or_disposal_breach),
        depositor_retains_title=truth(depositor_retains_title),
        title_passed_to_beneficiary=truth(title_passed_to_beneficiary),
        agent_liability_for_things_breached=truth(agent_liability_for_things_breached),
        securities_disposal_breach=truth(securities_disposal_breach),
        cashless_money_requires_nominal_account=truth(cashless_money_requires_nominal_account),
        deposited_property_insulated_from_agent_or_depositor_creditors=truth(
            deposited_property_insulated_from_agent_or_depositor_creditors
        ),
        insulation_breach=truth(insulation_breach),
        beneficiary_creditor_may_reach_claim_right=truth(
            beneficiary_creditor_may_reach_claim_right
        ),
        termination_ground_present=truth(termination_ground_present),
        contract_transferred_to_new_agent=truth(contract_transferred_to_new_agent),
        return_to_depositor_due=truth(return_to_depositor_due),
        transfer_to_beneficiary_due_on_termination=truth(
            transfer_to_beneficiary_due_on_termination
        ),
        requires_human_escrow_deposit_assessment=truth(
            requires_human_escrow_deposit_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Наступление оснований передачи имущества бенефициару по существу "
            "оценивает эскроу-агент по условиям договора, а по спору — суд и эксперт: "
            "модель принимает результат этой оценки как установленный факт.",
            "Размер и точный состав депонированного имущества модель не определяет.",
            "Иные основания прекращения договора эскроу, предусмотренные кодексом за "
            "пределами обстоятельств на стороне агента и истечения срока, модель не "
            "перечисляет — это открытый перечень статьи 926.8 ГК РФ.",
            "Модель отвечает об одном договоре эскроу: контракт данных даёт один блок "
            "доказательств на институт.",
        ],
    )
